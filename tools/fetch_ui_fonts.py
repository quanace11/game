"""Tải font cho giao diện giấy tờ (chữ viết tay, chữ in, chữ dấu mộc).

Nguồn: gói @fontsource trên registry.npmjs.org (bản build của Google Fonts,
giấy phép SIL OFL 1.1). Mỗi font tách thành ba tệp con latin / latin-ext /
vietnamese; PaperFonts.gd ghép lại bằng fallback nên chữ Việt đủ dấu.

Chạy: python3 tools/fetch_ui_fonts.py
"""
import io
import json
import os
import tarfile
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
SUBSETS = ["latin", "latin-ext", "vietnamese"]
# gói fontsource -> các độ đậm cần lấy
FONTS = {
    "charm": ["400", "700"],          # chữ viết tay nghiêng nét bút máy (nhật ký, thầy cúng)
    "mynerve": ["400"],               # chữ bút bi người lớn (sổ phụ xe, chú Bảy, bà Năm)
    "grape-nuts": ["400"],            # nét bút chì run, ghi vội
    "mali": ["400", "500"],           # chữ học trò (vở của Hùng)
    "tinos": ["400", "700"],          # chữ in giấy tờ nhà nước
    "xanh-mono": ["400"],             # chữ máy chữ điền vào mẫu
    "oswald": ["500", "700"],         # chữ dấu mộc, nhãn dán
}


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def main():
    for pkg, weights in FONTS.items():
        meta = json.loads(fetch(f"https://registry.npmjs.org/@fontsource/{pkg}/latest"))
        tar = tarfile.open(fileobj=io.BytesIO(fetch(meta["dist"]["tarball"])), mode="r:gz")
        out = os.path.join(ROOT, pkg)
        os.makedirs(out, exist_ok=True)
        names = tar.getnames()
        for w in weights:
            for sub in SUBSETS:
                name = f"package/files/{pkg}-{sub}-{w}-normal.woff2"
                if name not in names:
                    print("  thiếu", name)
                    continue
                with open(os.path.join(out, f"{pkg}-{sub}-{w}.woff2"), "wb") as f:
                    f.write(tar.extractfile(name).read())
        with open(os.path.join(out, "OFL.txt"), "wb") as f:
            f.write(tar.extractfile("package/LICENSE").read())
        print(pkg, meta["version"])


if __name__ == "__main__":
    main()
