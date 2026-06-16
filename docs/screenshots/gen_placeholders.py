"""Generate placeholder screenshots for documentation."""
import struct, zlib, os

SCREENSHOTS = [
    ("coach.png", "Coach — AI Reply Suggestions"),
    ("translate.png", "Translate — Context-Aware Translation"),
    ("history.png", "History — Filterable Task Log"),
    ("review.png", "Review Book — Saved Cards"),
    ("vocab.png", "Vocab Bank — Personal Phrase Collection"),
    ("report.png", "Learning Report — Progress Metrics"),
]

WIDTH, HEIGHT = 800, 500

def _make_png(path: str, label: str):
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        for x in range(WIDTH):
            # Gradient background: dark blue top-left, teal bottom-right
            r = int(15 + (x / WIDTH) * 20)
            g = int(23 + (y / HEIGHT) * 30)
            b_val = int(42 + ((x + y) / (WIDTH + HEIGHT)) * 80)
            raw.extend([r, g, b_val, 255])

    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(png)
    print(f"  Created {path} ({WIDTH}x{HEIGHT}) — placeholder for: {label}")

def main():
    out_dir = os.path.dirname(__file__)
    for filename, label in SCREENSHOTS:
        path = os.path.join(out_dir, filename)
        _make_png(path, label)
    print(f"\nDone. {len(SCREENSHOTS)} placeholders created.")
    print("Replace with actual browser screenshots before production use.")

if __name__ == "__main__":
    main()
