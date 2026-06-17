from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("GAIA_ALLOW_FALLBACK", "true")
os.environ.setdefault("GAIA_MODE", "fallback")
os.environ.setdefault("GAIA_LOG_TO_FILE", "false")

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
