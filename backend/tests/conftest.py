from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("GAIA_ALLOW_FALLBACK", "true")
os.environ.setdefault("GAIA_MODE", "fallback")
os.environ.setdefault("GAIA_LOG_TO_FILE", "false")
# Demo mode so importing app.main does not spin up live connectors that would
# hit the network. Live-mode behavior is unit-tested with its own registry.
os.environ.setdefault("GAIA_DATA_MODE", "demo")

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
