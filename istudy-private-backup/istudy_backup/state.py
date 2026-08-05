from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .core import Status, VideoRecord, WorkflowData


class StateStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> WorkflowData:
        if not self.path.exists():
            return WorkflowData()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return WorkflowData(
            schema_version=raw["schema_version"],
            trial_passed=raw.get("trial_passed", False),
            recording_smoke_passed=raw.get("recording_smoke_passed", False),
            stopped_reason=raw.get("stopped_reason"),
            videos={key: VideoRecord.from_dict(value) for key, value in raw.get("videos", {}).items()},
        )

    def save(self, data: WorkflowData) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": data.schema_version,
            "trial_passed": data.trial_passed,
            "recording_smoke_passed": data.recording_smoke_passed,
            "stopped_reason": data.stopped_reason,
            "videos": {key: value.to_dict() for key, value in sorted(data.videos.items())},
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)

    def upsert(self, record: VideoRecord) -> None:
        data = self.load()
        data.videos[record.id] = record
        self.save(data)

    def transition(self, video_id: str, status: Status, **changes: Any) -> VideoRecord:
        data = self.load()
        record = data.videos[video_id]
        record.status = status
        for name, value in changes.items():
            if not hasattr(record, name):
                raise AttributeError(name)
            setattr(record, name, value)
        data.videos[video_id] = record
        self.save(data)
        return record
