#!/usr/bin/env python3
import base64, gzip, pathlib
root = pathlib.Path(__file__).resolve().parent
b64 = (root / "payload_a.txt").read_text() + (root / "payload_b.txt").read_text()
out = root / "Jarvis.py"
out.write_bytes(gzip.decompress(base64.b64decode(b64)))
print(f"Wrote {out} ({out.stat().st_size} bytes). Run: python Jarvis.py")
