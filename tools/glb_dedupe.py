"""Gộp các ảnh trùng nhau trong file .glb do Godot xuất ra.

Exporter của Godot ghi lại texture cho từng material (normal map, ORM đã pack), nên một
texture dùng chung bị lưu nhiều lần và file phình to. Script này giữ một bản cho mỗi ảnh
giống hệt nhau, trỏ lại các texture vào đó và đóng gói lại phần binary.

    python3 tools/glb_dedupe.py exports/*.glb
"""
import hashlib
import json
import struct
import sys

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def read_glb(path):
    data = open(path, "rb").read()
    magic, version, _ = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67 and version == 2, f"{path} is not a glTF 2.0 binary"
    offset, gltf, binary = 12, None, b""
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8 : offset + 8 + length]
        if kind == JSON_CHUNK:
            gltf = json.loads(chunk)
        elif kind == BIN_CHUNK:
            binary = chunk
        offset += 8 + length
    return gltf, binary


def write_glb(path, gltf, binary):
    text = json.dumps(gltf, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(text), JSON_CHUNK) + text)
        f.write(struct.pack("<II", len(binary), BIN_CHUNK) + binary)


def view_bytes(gltf, binary, index):
    view = gltf["bufferViews"][index]
    start = view.get("byteOffset", 0)
    return binary[start : start + view["byteLength"]]


def dedupe(path):
    gltf, binary = read_glb(path)
    images = gltf.get("images", [])
    keep, image_map, by_hash = [], {}, {}
    for i, image in enumerate(images):
        digest = hashlib.sha1(view_bytes(gltf, binary, image["bufferView"])).hexdigest()
        if digest not in by_hash:
            by_hash[digest] = len(keep)
            keep.append(image)
        image_map[i] = by_hash[digest]
    for texture in gltf.get("textures", []):
        if "source" in texture:
            texture["source"] = image_map[texture["source"]]
    gltf["images"] = keep

    # Repack the binary with only the buffer views still referenced.
    used = {a["bufferView"] for a in gltf.get("accessors", []) if "bufferView" in a}
    used |= {img["bufferView"] for img in keep}
    view_map, views, packed = {}, [], bytearray()
    for i, view in enumerate(gltf["bufferViews"]):
        if i not in used:
            continue
        chunk = view_bytes(gltf, binary, i)
        packed += b"\0" * (-len(packed) % 4)
        view = dict(view, byteOffset=len(packed))
        packed += chunk
        view_map[i] = len(views)
        views.append(view)
    for accessor in gltf.get("accessors", []):
        if "bufferView" in accessor:
            accessor["bufferView"] = view_map[accessor["bufferView"]]
    for image in keep:
        image["bufferView"] = view_map[image["bufferView"]]
    gltf["bufferViews"] = views
    gltf["buffers"] = [{"byteLength": len(packed)}]
    write_glb(path, gltf, bytes(packed))
    print(f"{path}: images {len(images)} -> {len(keep)}, {len(binary)} -> {len(packed)} bytes")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        dedupe(arg)
