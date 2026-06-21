"""Generate PNG icons from the SVG source (requires Pillow or cairosvg).

Run:  python pwa/gen_icons.py

If Pillow is not installed, the app will use SVG icons only,
which is supported by all modern browsers.
"""

import os

SVG_PATH = os.path.join(os.path.dirname(__file__), "icon.svg")
OUTPUT_DIR = os.path.dirname(__file__)

SIZES = [192, 512]


def gen_with_pillow():
    """Convert SVG to PNG using Pillow + cairosvg or svglib."""
    try:
        import io

        from PIL import Image
    except ImportError:
        return False

    # Try cairosvg first
    try:
        import cairosvg

        for size in SIZES:
            output_path = os.path.join(OUTPUT_DIR, f"icon-{size}.png")
            cairosvg.svg2png(
                url=SVG_PATH,
                write_to=output_path,
                output_width=size,
                output_height=size,
            )
            print(f"  ✓ icon-{size}.png ({size}x{size})")
        return True
    except ImportError:
        pass

    # Try svglib + reportlab as fallback
    try:
        import svglib.svglib as svglib
        from reportlab.graphics import renderPM

        for size in SIZES:
            drawing = svglib.svg2rlg(SVG_PATH)
            output_path = os.path.join(OUTPUT_DIR, f"icon-{size}.png")
            renderPM.drawToFile(drawing, output_path, fmt="PNG", dpi=size * 2)
            print(f"  [OK] icon-{size}.png ({size}x{size})")
        return True
    except ImportError:
        pass

    return False


def gen_with_base64_svg():
    """Create minimal placeholder PNGs using built-in modules only."""
    import struct
    import zlib

    def _make_png(size: int) -> bytes:
        """Build a minimal valid PNG with a solid blue background + white TL text."""
        # Create raw pixel data (RGBA)
        raw = bytearray()
        for y in range(size):
            raw.extend([0])  # filter byte
            for x in range(size):
                # Round blue icon area
                cx, cy = size / 2, size / 2
                r = size / 2 - 2
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist < r:
                    # Blue gradient area
                    raw.extend([37, 99, 235, 255])  # #2563eb
                elif dist < r + 4:
                    raw.extend([15, 23, 42, 255])  # border #0f172a
                else:
                    raw.extend([245, 247, 251, 0])  # transparent

        def _chunk(chunk_type: bytes, data: bytes) -> bytes:
            chunk = chunk_type + data
            return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

        # PNG signature
        sig = b"\x89PNG\r\n\x1a\n"
        # IHDR
        ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        # IDAT
        compressed = zlib.compress(bytes(raw))
        idat = _chunk(b"IDAT", compressed)
        # IEND
        iend = _chunk(b"IEND", b"")

        return sig + ihdr + idat + iend

    for size in SIZES:
        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}.png")
        with open(output_path, "wb") as f:
            f.write(_make_png(size))
        ok = "OK"
        print(f"  [{ok}] icon-{size}.png ({size}x{size}) — placeholder")


def main():
    print("Generating PWA icons...")

    if gen_with_pillow():
        print("Done (Pillow).")
        return

    print("  Pillow/cairosvg not installed. Generating placeholder PNGs...")
    gen_with_base64_svg()
    print("Done (placeholder). Install Pillow + cairosvg for crisp SVG rendering:")
    print("  pip install Pillow cairosvg")


if __name__ == "__main__":
    main()
