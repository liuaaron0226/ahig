from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


COURSE_RE = re.compile(r"^115暑電子(?:[1-9]|1[0-5])$")
INVALID_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


class Status(StrEnum):
    DISCOVERED = "discovered"
    PROCESSING = "processing"
    DOWNLOADED = "downloaded"
    VERIFIED = "verified"
    UPLOADING = "uploading"
    UPLOADED_PRIVATE = "uploaded_private"
    SKIPPED_PROTECTED = "skipped_protected"
    FAILED = "failed"


class ManualActionRequired(RuntimeError):
    pass


class ProtectedMedia(RuntimeError):
    pass


class PrivacyViolation(RuntimeError):
    pass


@dataclass(slots=True)
class Paths:
    root: Path
    profile_dir: Path
    data_dir: Path
    downloads_dir: Path
    reports_dir: Path
    artifacts_dir: Path
    extension_dir: Path
    state_file: Path
    capture_file: Path

    @classmethod
    def from_root(cls, root: Path) -> "Paths":
        root = root.resolve()
        data = root / "data"
        return cls(
            root=root,
            profile_dir=data / "chrome-profile",
            data_dir=data,
            downloads_dir=root / "downloads",
            reports_dir=root / "reports",
            artifacts_dir=root / "artifacts",
            extension_dir=root / "extension",
            state_file=data / "state.json",
            capture_file=Path.home() / "Downloads" / "istudy-backup" / "current.webm",
        )

    def ensure_runtime_dirs(self) -> None:
        for path in (self.profile_dir, self.downloads_dir, self.reports_dir, self.artifacts_dir):
            path.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class VideoRecord:
    id: str
    course: str
    title: str
    course_url: str
    page_url: str
    click_text: str | None = None
    status: Status = Status.DISCOVERED
    local_path: str | None = None
    method: str | None = None
    attempts: int = 0
    error: str | None = None
    youtube_id: str | None = None
    youtube_url: str | None = None
    youtube_privacy: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoRecord":
        return cls(**{**data, "status": Status(data["status"])})


@dataclass(slots=True)
class WorkflowData:
    schema_version: int = 1
    trial_passed: bool = False
    recording_smoke_passed: bool = False
    stopped_reason: str | None = None
    videos: dict[str, VideoRecord] = field(default_factory=dict)


def normalize_course_name(text: str) -> str:
    compact = re.sub(r"\s+", "", text)
    match = re.fullmatch(r"115暑電子0*([1-9]|1[0-5])", compact)
    return f"115暑電子{int(match.group(1))}" if match else compact


def is_target_course(text: str) -> bool:
    return bool(COURSE_RE.fullmatch(normalize_course_name(text)))


def safe_filename(text: str) -> str:
    name = INVALID_FILENAME_RE.sub("_", text).strip().rstrip(". ") or "untitled"
    if name.upper() in RESERVED_NAMES:
        name = f"_{name}"
    return name[:180]


def stable_video_id(course: str, title: str, page_url: str) -> str:
    raw = f"{normalize_course_name(course)}\n{title.strip()}\n{page_url.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
