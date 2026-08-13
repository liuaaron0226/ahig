from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from ahig.state import StateStore


def test_state_store_round_trip_uses_utf8():
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "狀態.json"
        store = StateStore(path)
        store.save({"schema_version": 1, "message": "肝醣"})
        assert store.load()["message"] == "肝醣"


def test_state_store_atomic_write_preserves_previous_file_on_replace_failure():
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "state.json"
        store = StateStore(path)
        store.save({"schema_version": 1, "value": "old"})

        with patch("ahig.state.os.replace", side_effect=OSError("injected replace failure")):
            try:
                store.save({"schema_version": 1, "value": "new"})
            except OSError:
                pass
            else:
                raise AssertionError("expected injected failure")

        assert json.loads(path.read_text(encoding="utf-8"))["value"] == "old"
        assert not path.with_suffix(".json.tmp").exists()
