from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """以 tmp → flush → fsync → os.replace 原子寫入任意 bytes。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, data: Any) -> None:
    """原子寫入 UTF-8/LF JSON。

    中途失敗時原檔完整保留，且不留下半寫入的暫存檔。凡是會被後續步驟
    當成事實讀取的產物（凍結契約、抽樣框、狀態檔）都走這條路徑。
    """
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    atomic_write_bytes(path, payload)


class StateStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        if "schema_version" not in data:
            raise ValueError("state requires schema_version")
        atomic_write_json(self.path, data)
