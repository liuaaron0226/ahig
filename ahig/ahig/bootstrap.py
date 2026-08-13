from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def private_root() -> Path:
    raw = os.environ.get("AHIG_PRIVATE_ROOT")
    if not raw:
        raise RuntimeError("AHIG_PRIVATE_ROOT is required for private-data commands")
    return Path(raw).expanduser().resolve()
