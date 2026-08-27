# Jarvis V1.2.0

## Fixes in this release
- API key stored in keyring + encrypted fallback + settings mirror (no more "key not found")
- Wake-word listening waits for real speech (min ~2.5s) before ending on silence
- Face match thresholds tuned; models download on enrollment
- Chrome path finder improved
- **Auto-update**: on startup checks `VERSION` on this repo and replaces `Jarvis.py` if newer

## Install

1. Download `Jarvis.py` from the release artifact / chat download
2. Place in this folder as `Jarvis.py`
3. Run `python Jarvis.py` (or `python3 Jarvis.py`)

Optional assemble path if `payload_*.txt` present:
```bash
python assemble_jarvis.py
```

Skip update check: `python Jarvis.py --no-update`

Repo: https://github.com/robopup33/Jarvis-V1
