import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
for path in (ROOT, ENGINE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
