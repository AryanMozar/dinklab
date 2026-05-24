"""
Generate icon.ico (Windows) and icon.icns (macOS) from scratch using Pillow.
Run from the repo root:  python assets/generate_icons.py
"""
import io
import struct
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow required: pip install pillow")

ASSETS = Path(__file__).resolve().parent
ACCENT = (232, 49, 26, 255)   # #E8311A vermillion
WHITE  = (255, 255, 255, 255)


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    pad = round(size * 0.04)
    r   = round(size * 0.1875)   # ~96/512 corner radius
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=r, fill=ACCENT)

    # outer diamond
    cx, cy   = size // 2, size // 2
    outer    = round(size * 0.328)   # ~168/512 from centre to point
    inner    = round(size * 0.172)   # ~88/512 inner diamond (cutout)

    outer_pts = [(cx, cy - outer), (cx + outer, cy), (cx, cy + outer), (cx - outer, cy)]
    inner_pts = [(cx, cy - inner), (cx + inner, cy), (cx, cy + inner), (cx - inner, cy)]

    d.polygon(outer_pts, fill=WHITE)
    d.polygon(inner_pts, fill=ACCENT)   # punch out the centre — frame effect

    return img


# ---------- .ico (Windows) ----------
def build_ico():
    # Pillow resamples a single source image to each requested size.
    # Render at 256 (largest ICO size) and let Pillow downsample.
    src = draw_icon(256).convert("RGBA")
    out = ASSETS / "icon.ico"
    src.save(
        out,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"  wrote {out}  ({out.stat().st_size // 1024} KB)")


# ---------- .icns (macOS) ----------
# Minimal ICNS: just write a valid container with PNG chunks.
# Works on any OS — no macOS toolchain required.
ICNS_TYPES = {
    16:   b"icp4",
    32:   b"icp5",
    64:   b"icp6",
    128:  b"ic07",
    256:  b"ic08",
    512:  b"ic09",
    1024: b"ic10",
}

def build_icns():
    sizes = [16, 32, 64, 128, 256, 512]
    chunks = []
    for s in sizes:
        if s not in ICNS_TYPES:
            continue
        buf = io.BytesIO()
        draw_icon(s).save(buf, format="PNG")
        data = buf.getvalue()
        chunks.append(ICNS_TYPES[s] + struct.pack(">I", 8 + len(data)) + data)

    body  = b"".join(chunks)
    out   = ASSETS / "icon.icns"
    out.write_bytes(b"icns" + struct.pack(">I", 8 + len(body)) + body)
    print(f"  wrote {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    print("Generating DinkLab icons…")
    build_ico()
    build_icns()
    print("Done.")
