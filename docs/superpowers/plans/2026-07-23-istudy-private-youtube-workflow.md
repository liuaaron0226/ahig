# iStudy Private YouTube Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a resumable Windows workflow that discovers all videos in 「115暑電子1」 through 「115暑電子15」, saves authorized non-DRM media, validates each file, and uploads it to `liuaaron0226@gmail.com` YouTube with verified Private visibility.

**Architecture:** A small Python package drives a dedicated headed Chrome profile through Playwright, writes an atomic JSON manifest, captures ordinary MP4/HLS responses, and uses Requests or FFmpeg for direct downloads. A bundled Chrome tab-capture extension provides the normal-speed recording fallback without touching the user's personal Chrome profile. YouTube Studio upload automation fails closed unless the completed video can be read back as Private. The first video in 「115暑電子1」 is a mandatory end-to-end trial gate before batch execution is enabled.

**Tech Stack:** Python 3.11.1, Playwright 1.61.0 using installed Google Chrome, Requests 2.34.2, FFmpeg/ffprobe 8.1.2, Chrome Extension Manifest V3, Python `unittest`.

## Global Constraints

- Process only 「115暑電子1」 through 「115暑電子15」.
- The user has stated that they have explicit authorization to download and privately re-upload these videos.
- Never bypass DRM, Encrypted Media Extensions, encrypted HLS keys, paywalls, CAPTCHA, login controls, or account-security checks.
- Never read, store, guess, or automatically enter passwords.
- Use `istudy-private-backup/data/chrome-profile/`; never launch against an existing personal Chrome user-data directory.
- Use the Google account `liuaaron0226@gmail.com` and stop if the dedicated profile cannot confirm it.
- Upload one video at a time and hard-code YouTube visibility to Private.
- Stop the upload queue if Private visibility cannot be read back after an upload.
- Keep validated local files after upload; no cleanup command may delete them.
- The direct-download path may run at available network speed. The recording fallback must use playback rate `1.0` so the saved video retains original timing and audio.
- Batch mode remains locked until the first video in 「115暑電子1」 completes download or recording, validation, Private upload, visibility readback, and duplicate-free rerun.
- Do not run `git add`, `git commit`, or mix unrelated working-tree changes into this work.

---

## File Map

Create the workflow under a new isolated directory:

```text
istudy-private-backup/
  .gitignore                         Generated profiles, state, downloads, reports
  README.md                          Setup, commands, safety rules, manual checkpoints
  requirements.txt                  Existing Python package versions only
  istudy_backup/
    __init__.py                      Package marker
    __main__.py                      CLI: setup, discover, trial, run, report
    core.py                          Paths, records, normalization, exceptions
    state.py                         Atomic JSON persistence and state transitions
    browser.py                       Dedicated persistent Chrome and login checks
    site.py                          Course/video discovery and player opening
    media.py                         DRM detection, response capture, direct download, ffprobe
    recorder.py                      Chrome tab-capture fallback controller
    youtube.py                       YouTube Studio Private upload and visibility readback
    workflow.py                      Trial gate, retries, sequential orchestration, report
  extension/
    manifest.json                    Tab-capture permission and keyboard command
    service-worker.js                Start/stop capture and offscreen lifecycle
    offscreen.html                   Hidden recording document
    offscreen.js                     MediaRecorder, tab audio monitoring, fixed output download
  tests/
    test_core.py
    test_state.py
    test_site.py
    test_media.py
    test_recorder.py
    test_youtube.py
    test_workflow.py
  tools/
    recording_smoke.py                  Synthetic tab-audio capture gate
```

Runtime-only paths, all excluded by `.gitignore`:

```text
istudy-private-backup/data/chrome-profile/
istudy-private-backup/data/state.json
istudy-private-backup/downloads/
istudy-private-backup/reports/
istudy-private-backup/artifacts/
%USERPROFILE%/Downloads/istudy-backup/current.webm
```

---

### Task 1: Package Foundation and Domain Types

**Files:**
- Create: `istudy-private-backup/.gitignore`
- Create: `istudy-private-backup/requirements.txt`
- Create: `istudy-private-backup/istudy_backup/__init__.py`
- Create: `istudy-private-backup/istudy_backup/core.py`
- Create: `istudy-private-backup/tests/test_core.py`

**Interfaces:**
- Produces: `Paths.from_root(root: Path) -> Paths`
- Produces: `VideoRecord`, `WorkflowData`, `Status`, `ManualActionRequired`, `ProtectedMedia`, `PrivacyViolation`
- Produces: `normalize_course_name(text: str) -> str`, `is_target_course(text: str) -> bool`, `safe_filename(text: str) -> str`, `stable_video_id(course: str, title: str, page_url: str) -> str`

- [ ] **Step 1: Write the failing domain tests**

Create `tests/test_core.py`:

```python
import tempfile
import unittest
from pathlib import Path

from istudy_backup.core import (
    Paths,
    is_target_course,
    normalize_course_name,
    safe_filename,
    stable_video_id,
)


class CoreTests(unittest.TestCase):
    def test_course_range_is_exact(self):
        self.assertTrue(is_target_course(" 115暑電子1 "))
        self.assertTrue(is_target_course("115暑電子15"))
        self.assertFalse(is_target_course("115暑電子0"))
        self.assertFalse(is_target_course("115暑電子16"))
        self.assertFalse(is_target_course("115暑電子1 複習"))

    def test_course_normalization_removes_whitespace_only(self):
        self.assertEqual(normalize_course_name("115 暑 電子 01"), "115暑電子1")

    def test_filename_is_windows_safe(self):
        self.assertEqual(safe_filename('第1講: A/B? <test>.'), "第1講_ A_B_ _test_")
        self.assertEqual(safe_filename("CON"), "_CON")

    def test_stable_id_does_not_change(self):
        first = stable_video_id("115暑電子1", "第一講", "https://example/video/1")
        second = stable_video_id("115暑電子1", "第一講", "https://example/video/1")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)

    def test_paths_create_only_dedicated_runtime_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = Paths.from_root(Path(tmp))
            paths.ensure_runtime_dirs()
            self.assertTrue(paths.profile_dir.is_dir())
            self.assertTrue(paths.downloads_dir.is_dir())
            self.assertTrue(paths.reports_dir.is_dir())
            self.assertTrue(paths.artifacts_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `istudy-private-backup/`:

```bash
python -m unittest tests.test_core -v
```

Expected: `ModuleNotFoundError: No module named 'istudy_backup.core'`.

- [ ] **Step 3: Create the package metadata and minimal implementation**

Create `requirements.txt`:

```text
playwright==1.61.0
requests==2.34.2
```

Create `.gitignore`:

```text
__pycache__/
*.pyc
data/
downloads/
reports/
artifacts/
```

Create an empty `istudy_backup/__init__.py`.

Create `istudy_backup/core.py` with:

```python
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
        self.capture_file.parent.mkdir(parents=True, exist_ok=True)


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
```

- [ ] **Step 4: Run the domain tests**

```bash
python -m unittest tests.test_core -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Review scope without committing**

Run:

```bash
git status --short -- istudy-private-backup
```

Expected: only the new `istudy-private-backup/` tree appears. Do not stage or commit it.

---

### Task 2: Atomic State and Safe Transitions

**Files:**
- Create: `istudy-private-backup/istudy_backup/state.py`
- Create: `istudy-private-backup/tests/test_state.py`

**Interfaces:**
- Consumes: `WorkflowData`, `VideoRecord`, `Status`
- Produces: `StateStore.load() -> WorkflowData`, `StateStore.save(data: WorkflowData) -> None`, `StateStore.upsert(record: VideoRecord) -> None`, `StateStore.transition(video_id: str, status: Status, **changes) -> VideoRecord`

- [ ] **Step 1: Write failing atomic-state tests**

Create `tests/test_state.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from istudy_backup.core import Status, VideoRecord
from istudy_backup.state import StateStore


class StateStoreTests(unittest.TestCase):
    def make_record(self):
        return VideoRecord(
            id="abc123",
            course="115暑電子1",
            title="第一講",
            course_url="https://example/course",
            page_url="https://example/video",
        )

    def test_round_trip_and_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json")
            store.upsert(self.make_record())
            loaded = store.load()
            self.assertEqual(loaded.videos["abc123"].title, "第一講")
            self.assertFalse((Path(tmp) / "state.json.tmp").exists())

    def test_transition_persists_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json")
            store.upsert(self.make_record())
            record = store.transition("abc123", Status.VERIFIED, local_path="x.mp4", method="mp4")
            self.assertEqual(record.status, Status.VERIFIED)
            self.assertEqual(store.load().videos["abc123"].local_path, "x.mp4")

    def test_corrupt_state_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                StateStore(path).load()
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_state -v
```

Expected: import failure for `istudy_backup.state`.

- [ ] **Step 3: Implement atomic JSON persistence**

Create `istudy_backup/state.py`:

```python
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
```

- [ ] **Step 4: Run state tests**

```bash
python -m unittest tests.test_state -v
```

Expected: 3 tests pass.

---

### Task 3: Dedicated Chrome Session and Manual Login Gate

**Files:**
- Create: `istudy-private-backup/istudy_backup/browser.py`
- Create: `istudy-private-backup/tests/test_site.py` initially with browser-safety tests

**Interfaces:**
- Consumes: `Paths`, `ManualActionRequired`
- Produces: `ChromeSession(paths: Paths)` context manager with `.context`
- Produces: `classify_dialog(message: str) -> str`, `google_account_matches(body_text: str, expected_email: str) -> bool`, `istudy_login_is_valid(url: str, body_text: str) -> bool`, `ChromeSession.verify_accounts(expected_email: str) -> None`

- [ ] **Step 1: Write failing safety tests**

Create `tests/test_site.py`:

```python
import unittest

from istudy_backup.browser import classify_dialog, google_account_matches, istudy_login_is_valid


class BrowserSafetyTests(unittest.TestCase):
    def test_login_and_duplicate_dialogs_are_blocking(self):
        self.assertEqual(classify_dialog("系統判斷您的帳號重複登入,將被登出"), "blocking")
        self.assertEqual(classify_dialog("您尚未登入"), "blocking")
        self.assertEqual(classify_dialog("機房維修公告"), "notice")

    def test_google_account_must_be_exact(self):
        body = "Google Account liuaaron0226@gmail.com Home"
        self.assertTrue(google_account_matches(body, "liuaaron0226@gmail.com"))
        self.assertFalse(google_account_matches(body, "other@example.com"))

    def test_login_redirect_is_invalid(self):
        self.assertFalse(istudy_login_is_valid("https://istudy.way-to-win.com/cloud/index_login.php", "登入"))
        self.assertTrue(istudy_login_is_valid("https://istudy.way-to-win.com/cloud/video_main.php", "課程列表"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_site.BrowserSafetyTests -v
```

Expected: import failure for `istudy_backup.browser`.

- [ ] **Step 3: Implement the dedicated persistent profile**

Create `istudy_backup/browser.py`:

```python
from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from weakref import WeakKeyDictionary

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from .core import ManualActionRequired, Paths


BLOCKING_DIALOG_MARKERS = ("尚未登入", "重複登入", "成功登出", "驗證碼", "安全驗證")
ISTUDY_HOME = "https://istudy.way-to-win.com/cloud/video_main.php"
GOOGLE_ACCOUNT = "https://myaccount.google.com/"
YOUTUBE_STUDIO = "https://studio.youtube.com/"
_PAGE_MEDIA_USAGE: WeakKeyDictionary[Page, set[str]] = WeakKeyDictionary()


def _mark_page_media_usage(source, kind: str) -> None:
    _PAGE_MEDIA_USAGE.setdefault(source["page"], set()).add(kind)


def page_media_usage(page: Page) -> frozenset[str]:
    return frozenset(_PAGE_MEDIA_USAGE.get(page, ()))


def classify_dialog(message: str) -> str:
    return "blocking" if any(marker in message for marker in BLOCKING_DIALOG_MARKERS) else "notice"


def google_account_matches(body_text: str, expected_email: str) -> bool:
    return expected_email.casefold() in body_text.casefold()


def istudy_login_is_valid(url: str, body_text: str) -> bool:
    lowered = url.casefold()
    return "index_login.php" not in lowered and "尚未登入" not in body_text and "登入" != body_text.strip()


class ChromeSession(AbstractContextManager["ChromeSession"]):
    def __init__(self, paths: Paths):
        self.paths = paths
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.dialogs: list[str] = []

    def __enter__(self) -> "ChromeSession":
        self.paths.ensure_runtime_dirs()
        self.playwright = sync_playwright().start()
        extension = str(self.paths.extension_dir.resolve())
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.paths.profile_dir),
            channel="chrome",
            headless=False,
            accept_downloads=True,
            viewport={"width": 1440, "height": 1000},
            args=[f"--disable-extensions-except={extension}", f"--load-extension={extension}"],
        )
        self.context.expose_binding("__ISTUDY_REPORT_MEDIA_USE__", _mark_page_media_usage)
        self.context.add_init_script(
            """
            (() => {
              window.__ISTUDY_DRM_USED__ = false;
              window.__ISTUDY_MSE_USED__ = false;
              const original = navigator.requestMediaKeySystemAccess?.bind(navigator);
              if (original) {
                navigator.requestMediaKeySystemAccess = (...args) => {
                  window.__ISTUDY_DRM_USED__ = true;
                  void window.__ISTUDY_REPORT_MEDIA_USE__('eme');
                  return original(...args);
                };
              }
              if (window.MediaSource) {
                window.MediaSource = new Proxy(window.MediaSource, {
                  construct(target, args, newTarget) {
                    window.__ISTUDY_MSE_USED__ = true;
                    void window.__ISTUDY_REPORT_MEDIA_USE__('mse');
                    return Reflect.construct(target, args, newTarget);
                  }
                });
              }
            })();
            """
        )
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def new_page(self) -> Page:
        assert self.context is not None
        page = self.context.new_page()

        def handle_dialog(dialog) -> None:
            self.dialogs.append(dialog.message)
            dialog.dismiss()

        page.on("dialog", handle_dialog)
        return page

    def verify_accounts(self, expected_email: str) -> None:
        page = self.new_page()
        page.goto(GOOGLE_ACCOUNT, wait_until="domcontentloaded")
        if not google_account_matches(page.locator("body").inner_text(), expected_email):
            raise ManualActionRequired(f"Dedicated Chrome is not signed in as {expected_email}")
        page.goto(ISTUDY_HOME, wait_until="domcontentloaded")
        body = page.locator("body").inner_text()
        blocking = [message for message in self.dialogs if classify_dialog(message) == "blocking"]
        if blocking or not istudy_login_is_valid(page.url, body):
            raise ManualActionRequired("iStudy login requires manual attention: " + " | ".join(blocking))
        page.goto(YOUTUBE_STUDIO, wait_until="domcontentloaded")
        if "accounts.google.com" in page.url:
            raise ManualActionRequired("YouTube Studio requires manual sign-in")
```

- [ ] **Step 4: Run safety tests**

```bash
python -m unittest tests.test_site.BrowserSafetyTests -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Add a headed setup smoke command later consumed by the CLI**

Do not test against the personal Chrome profile. The later `setup` command must instantiate `ChromeSession(Paths.from_root(project_root))`, open the three login pages, and pause for manual sign-in before calling `verify_accounts`. No password fields are filled by code.

---

### Task 4: Course and Video Discovery Without Downloading

**Files:**
- Create: `istudy-private-backup/istudy_backup/site.py`
- Extend: `istudy-private-backup/tests/test_site.py`

**Interfaces:**
- Consumes: Playwright `BrowserContext`, `Page`; `VideoRecord`; `StateStore`
- Produces: `collect_clickables(page: Page) -> list[Clickable]`
- Produces: `discover_target_courses(page: Page) -> list[Clickable]`
- Produces: `discover_video_candidates(page: Page) -> list[Clickable]`
- Produces: `open_video(context: BrowserContext, record: VideoRecord) -> Page`

- [ ] **Step 1: Add failing pure discovery tests**

Append to `tests/test_site.py`:

```python
from istudy_backup.site import Clickable, select_target_courses, select_video_candidates


class DiscoveryTests(unittest.TestCase):
    def test_only_exact_target_courses_are_selected(self):
        items = [
            Clickable("115暑電子1", "https://x/1", "", "a"),
            Clickable("115暑電子15", "https://x/15", "", "a"),
            Clickable("115暑電子16", "https://x/16", "", "a"),
            Clickable("公告", "https://x/news", "", "a"),
        ]
        self.assertEqual([item.text for item in select_target_courses(items)], ["115暑電子1", "115暑電子15"])

    def test_video_candidates_require_playback_signal(self):
        items = [
            Clickable("第一講", "https://x/video.php?id=1", "", "a"),
            Clickable("第二講", "", "playVideo(2)", "button"),
            Clickable("回首頁", "https://x/index.php", "", "a"),
        ]
        self.assertEqual([item.text for item in select_video_candidates(items)], ["第一講", "第二講"])
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_site.DiscoveryTests -v
```

Expected: import failure for `Clickable`.

- [ ] **Step 3: Implement generic, fail-closed discovery**

Create `istudy_backup/site.py` with these concrete rules:

```python
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from playwright.sync_api import BrowserContext, Page

from .core import ManualActionRequired, VideoRecord, is_target_course, normalize_course_name, stable_video_id


VIDEO_SIGNALS = ("video", "movie", "play", "vod", "lesson", "lecture", "影片", "播放")


@dataclass(frozen=True, slots=True)
class Clickable:
    text: str
    href: str
    onclick: str
    tag: str

    @property
    def signature(self) -> str:
        return " ".join((self.text, self.href, self.onclick, self.tag)).casefold()


def select_target_courses(items: list[Clickable]) -> list[Clickable]:
    found = {normalize_course_name(item.text): item for item in items if is_target_course(item.text)}
    return [found[name] for name in (f"115暑電子{i}" for i in range(1, 16)) if name in found]


def select_video_candidates(items: list[Clickable]) -> list[Clickable]:
    return [item for item in items if item.text and any(signal in item.signature for signal in VIDEO_SIGNALS)]


def collect_clickables(page: Page) -> list[Clickable]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Clickable] = []
    for frame in page.frames:
        locator = frame.locator("a,button,[role=button],[onclick],option")
        for index in range(locator.count()):
            node = locator.nth(index)
            try:
                data = node.evaluate(
                    """
                    el => ({
                      text: (el.innerText || el.textContent || '').trim(),
                      href: el.href || el.value || '',
                      onclick: el.getAttribute('onclick') || '',
                      tag: el.tagName.toLowerCase()
                    })
                    """
                )
            except Exception:
                continue
            key = (data["text"], data["href"], data["onclick"])
            if key in seen:
                continue
            seen.add(key)
            result.append(Clickable(**data))
    return result


def discover_target_courses(page: Page) -> list[Clickable]:
    courses = select_target_courses(collect_clickables(page))
    names = {normalize_course_name(item.text) for item in courses}
    missing = [f"115暑電子{i}" for i in range(1, 16) if f"115暑電子{i}" not in names]
    if missing:
        raise ManualActionRequired("Course discovery is incomplete: " + ", ".join(missing))
    return courses


def discover_video_candidates(page: Page) -> list[Clickable]:
    candidates = select_video_candidates(collect_clickables(page))
    if not candidates:
        raise ManualActionRequired("No unambiguous video candidates were found; inspect artifacts before continuing")
    return candidates


def records_from_candidates(course: Clickable, candidates: list[Clickable], base_url: str) -> list[VideoRecord]:
    course_name = normalize_course_name(course.text)
    course_url = urljoin(base_url, course.href)
    records = []
    for item in candidates:
        page_url = urljoin(course_url, item.href) if item.href else course_url
        video_id = stable_video_id(course_name, item.text, page_url + "\n" + item.onclick)
        records.append(
            VideoRecord(
                id=video_id,
                course=course_name,
                title=item.text,
                course_url=course_url,
                page_url=page_url,
                click_text=item.text if not item.href else None,
            )
        )
    return records


def open_video(context: BrowserContext, record: VideoRecord) -> Page:
    page = context.new_page()
    page.goto(record.page_url, wait_until="domcontentloaded")
    if record.click_text:
        target = page.get_by_text(record.click_text, exact=True)
        if target.count() != 1:
            raise ManualActionRequired(f"Video click target is ambiguous: {record.click_text}")
        target.click()
    return page
```

Discovery remains a separate command. Before saving records, print every course and candidate title and require the user to type exactly `ACCEPT DISCOVERY`; otherwise make no state changes.

- [ ] **Step 4: Run discovery tests**

```bash
python -m unittest tests.test_site -v
```

Expected: all browser-safety and discovery tests pass.

---

### Task 5: DRM Detection, Direct Download, and ffprobe Validation

**Files:**
- Create: `istudy-private-backup/istudy_backup/media.py`
- Create: `istudy-private-backup/tests/test_media.py`

**Interfaces:**
- Consumes: `Page`, `Paths`, `VideoRecord`, `ProtectedMedia`
- Produces: `MediaCandidate(url: str, kind: str, headers: dict[str, str])`
- Produces: `probe_media(page: Page, timeout_ms: int = 15000) -> MediaCandidate | None`
- Produces: `download_direct(candidate: MediaCandidate, destination: Path) -> str`
- Produces: `validate_media(path: Path, require_audio: bool = True) -> MediaInfo`

- [ ] **Step 1: Write failing media tests**

Create `tests/test_media.py`:

```python
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests

from istudy_backup.browser import _mark_page_media_usage
from istudy_backup.core import ManualActionRequired, ProtectedMedia
from istudy_backup.media import (
    MediaCandidate,
    _request_headers,
    assert_clear_hls,
    download_direct,
    playlist_is_protected,
    probe_media,
    response_kind,
    validate_probe_json,
)


class FakeLocator:
    count = lambda self: 0


class FakeFrame:
    def __init__(self, **state):
        self.state = {"eme": False, "media_keys": False, "mse": False, "mpd": False, "videos": [], **state}

    def locator(self, _selector):
        return FakeLocator()

    def evaluate(self, _script):
        return self.state


class FakePage:
    url = "https://x/watch"

    def __init__(self, state=None, events=None):
        self.frame = FakeFrame(**(state or {}))
        self.frames = [self.frame]
        self.context = SimpleNamespace(cookies=lambda _url: [{"name": "sid", "value": "fresh"}])
        self.events = list(events or [])
        self.response_handler = None
        self.clock = 0.0

    def on(self, event, handler):
        if event == "response":
            self.response_handler = handler

    def wait_for_timeout(self, milliseconds):
        self.clock += milliseconds / 1000
        if self.events:
            event = self.events.pop(0)
            self.frame.state.update(event.get("state", {}))
            if event.get("response"):
                self.response_handler(event["response"])


def fake_response(url, content_type="video/mp4", request_url=None, headers=None):
    return SimpleNamespace(url=url, headers={"content-type": content_type}, request=SimpleNamespace(url=request_url or url, headers=headers or {}))


class FakeHttpResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("secret response")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def iter_content(self, _size):
        yield self.text.encode("utf-8") if self.text else b"media"


class FakeSession:
    def __init__(self, pages=None, error=None):
        self.pages = pages or {}
        self.error = error
        self.headers = {}
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self.pages[url]


class MediaTests(unittest.TestCase):
    def test_encrypted_hls_and_missing_method_are_rejected(self):
        self.assertTrue(playlist_is_protected('#EXT-X-KEY:METHOD=AES-128,URI="key.bin"'))
        self.assertTrue(playlist_is_protected('#EXT-X-SESSION-KEY:METHOD=SAMPLE-AES,URI="key.bin"'))
        self.assertTrue(playlist_is_protected('#EXT-X-KEY:URI="key.bin"'))
        self.assertTrue(playlist_is_protected("#EXT-X-KEY"))
        self.assertFalse(playlist_is_protected("#EXT-X-KEY:METHOD=NONE"))

    def test_dash_wins_over_mp4_substring(self):
        self.assertEqual(response_kind(fake_response("https://x/manifest.mpd?fallback=video.mp4", "application/dash+xml")), "protected_or_unsupported")

    def test_preexisting_protection_signals_are_rejected(self):
        for state in ({"mpd": True}, {"media_keys": True}, {"eme": True}):
            with self.subTest(state=state):
                page = FakePage(state=state)
                with patch("istudy_backup.media.time.monotonic", side_effect=lambda: page.clock), self.assertRaises(ProtectedMedia):
                    probe_media(page, timeout_ms=1000)

    def test_page_lifetime_media_history_survives_clean_document_state(self):
        url = "https://x/video.mp4"
        for usage in ("eme", "mse"):
            with self.subTest(usage=usage):
                page = FakePage(events=[{"state": {"videos": [{"ready": True, "current_src": url}]}, "response": fake_response(url)}])
                _mark_page_media_usage({"page": page}, usage)
                with patch("istudy_backup.media.time.monotonic", side_effect=lambda: page.clock), self.assertRaises(ProtectedMedia):
                    probe_media(page, timeout_ms=2000)

    def test_mse_mp4_is_rejected(self):
        url = "https://x/video.mp4"
        page = FakePage(events=[{"state": {"mse": True, "videos": [{"ready": True, "current_src": url}]}, "response": fake_response(url)}])
        with patch("istudy_backup.media.time.monotonic", side_effect=lambda: page.clock), self.assertRaises(ProtectedMedia):
            probe_media(page, timeout_ms=2000)

    def test_true_progressive_mp4_is_accepted_after_stability(self):
        url = "https://x/video.mp4"
        page = FakePage(events=[{"state": {"videos": [{"ready": True, "current_src": url}]}, "response": fake_response(url)}])
        with patch("istudy_backup.media.time.monotonic", side_effect=lambda: page.clock):
            candidate = probe_media(page, timeout_ms=2000)
        self.assertEqual(candidate.url, url)
        self.assertGreaterEqual(page.clock, 1.0)

    def test_unbound_mp4_fails_closed(self):
        page = FakePage(events=[{"state": {"videos": [{"ready": True, "current_src": "https://x/other.mp4"}]}, "response": fake_response("https://x/video.mp4")}])
        with patch("istudy_backup.media.time.monotonic", side_effect=lambda: page.clock), self.assertRaises(ProtectedMedia):
            probe_media(page, timeout_ms=1000)

    def test_forwarded_headers_are_canonical_and_cookie_is_unique(self):
        page = FakePage()
        headers = _request_headers(page, fake_response("https://x/video.mp4", headers={"cookie": "stale", "authorization": "Bearer token", "USER-AGENT": "agent"}))
        self.assertEqual(headers["Cookie"], "sid=fresh")
        self.assertEqual(set(headers), {"Cookie", "Authorization", "User-Agent", "Referer"})

    def test_complete_hls_graph_rejects_encrypted_alternate_audio(self):
        root = "https://x/master.m3u8"
        pages = {root: FakeHttpResponse('#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,URI="audio.m3u8"\n#EXT-X-STREAM-INF:BANDWIDTH=1\nvideo.m3u8'), "https://x/audio.m3u8": FakeHttpResponse('#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="key"'), "https://x/video.m3u8": FakeHttpResponse("#EXTM3U\nsegment.ts")}
        with patch("istudy_backup.media._session", return_value=FakeSession(pages)), self.assertRaises(ProtectedMedia):
            assert_clear_hls(MediaCandidate(root, "hls", {}))

    def test_hls_graph_has_no_depth_limit(self):
        pages = {
            f"https://x/{i}.m3u8": FakeHttpResponse(
                f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\n{i + 1}.m3u8" if i < 4 else "#EXTM3U\nsegment.ts"
            )
            for i in range(5)
        }
        session = FakeSession(pages)
        with patch("istudy_backup.media._session", return_value=session):
            assert_clear_hls(MediaCandidate("https://x/0.m3u8", "hls", {}))
        self.assertEqual(len(session.calls), 5)

    def test_cross_origin_hls_rendition_and_segment_are_rejected(self):
        for manifest in ('#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,URI="https://evil/audio.m3u8"', "#EXTM3U\nhttps://evil/segment.ts", '#EXTM3U\n#EXT-X-MAP:URI="https://evil/init.mp4"\nsegment.ts'):
            with self.subTest(manifest=manifest), patch("istudy_backup.media._session", return_value=FakeSession({"https://x/master.m3u8": FakeHttpResponse(manifest)})), self.assertRaises(ProtectedMedia):
                assert_clear_hls(MediaCandidate("https://x/master.m3u8", "hls", {}))

    def test_hls_node_limit_fails_closed(self):
        pages = {f"https://x/{i}.m3u8": FakeHttpResponse(f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\n{i + 1}.m3u8") for i in range(101)}
        with patch("istudy_backup.media._session", return_value=FakeSession(pages)), self.assertRaises(ProtectedMedia):
            assert_clear_hls(MediaCandidate("https://x/0.m3u8", "hls", {}))

    def test_sensitive_hls_is_rejected_before_subprocess(self):
        candidates = [MediaCandidate("https://x/master.m3u8?token=querysecret", "hls", {}), MediaCandidate("https://x/master.m3u8", "hls", {"Cookie": "cookiesecret"}), MediaCandidate("https://x/master.m3u8", "hls", {"Authorization": "authsecret"}), MediaCandidate("https://x/master.m3u8", "hls", {"Referer": "https://x/watch?token=refsecret"})]
        with tempfile.TemporaryDirectory() as tmp, patch("istudy_backup.media.subprocess.run") as run:
            for candidate in candidates:
                with self.subTest(candidate=candidate.safe_summary()), self.assertRaises(ManualActionRequired) as raised:
                    download_direct(candidate, Path(tmp) / "out.mp4")
                self.assertNotIn("secret", str(raised.exception))
            run.assert_not_called()

    def test_transport_errors_are_sanitized(self):
        candidate = MediaCandidate("https://x/video.mp4?token=querysecret", "mp4", {"Cookie": "cookiesecret", "Authorization": "authsecret"})
        session = FakeSession(error=requests.ConnectionError("querysecret cookiesecret authsecret"))
        with tempfile.TemporaryDirectory() as tmp, patch("istudy_backup.media._session", return_value=session), self.assertRaises(RuntimeError) as raised:
            download_direct(candidate, Path(tmp) / "out.mp4")
        for secret in ("querysecret", "cookiesecret", "authsecret"):
            self.assertNotIn(secret, str(raised.exception))
        self.assertFalse(session.calls[0][1]["allow_redirects"])

    def test_hls_snapshot_rejects_segment_redirect_before_ffmpeg(self):
        candidate = MediaCandidate("https://x/master.m3u8", "hls", {})
        session = FakeSession({
            candidate.url: FakeHttpResponse("#EXTM3U\nsegment.ts"),
            "https://x/segment.ts": FakeHttpResponse(status_code=302),
        })
        with tempfile.TemporaryDirectory() as tmp, patch("istudy_backup.media._session", return_value=session), patch("istudy_backup.media.subprocess.run") as run, self.assertRaises(RuntimeError):
            download_direct(candidate, Path(tmp) / "out.mp4")
        run.assert_not_called()

    def test_ffmpeg_errors_are_sanitized(self):
        candidate = MediaCandidate("https://x/master.m3u8", "hls", {"User-Agent": "agent"})
        with tempfile.TemporaryDirectory() as tmp, patch("istudy_backup.media._snapshot_clear_hls", return_value=Path(tmp) / "master.m3u8"), patch("istudy_backup.media.subprocess.run", side_effect=subprocess.CalledProcessError(1, ["ffmpeg", "secret"])), self.assertRaises(RuntimeError) as raised:
            download_direct(candidate, Path(tmp) / "out.mp4")
        self.assertNotIn("secret", str(raised.exception))

    def test_probe_requires_finite_duration_video_and_audio(self):
        good = {"format": {"duration": "12.5"}, "streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}
        self.assertEqual(validate_probe_json(good, True).duration, 12.5)
        for duration in ("0", "nan"):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                validate_probe_json({"format": {"duration": duration}, "streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}, True)

    def test_media_candidate_redacts_sensitive_values(self):
        candidate = MediaCandidate("https://x/video.mp4?token=secret", "mp4", {"Cookie": "secret", "Referer": "https://x"})
        self.assertNotIn("secret", str(candidate.safe_summary()))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_media -v
```

Expected: import failure for `istudy_backup.media`.

- [ ] **Step 3: Implement candidate detection and protected-HLS rejection**

Create `istudy_backup/media.py` with:

```python
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from playwright.sync_api import Page, Response

from .browser import page_media_usage
from .core import ManualActionRequired, ProtectedMedia

STABILITY_SECONDS = 1.0
MAX_HLS_PLAYLISTS = 100
MAX_PLAYLIST_BYTES = 5 * 1024 * 1024
CANONICAL_HEADERS = {"cookie": "Cookie", "referer": "Referer", "user-agent": "User-Agent", "authorization": "Authorization"}
FRAME_STATE_SCRIPT = """
() => {
  const videos = Array.from(document.querySelectorAll('video'));
  return {
    eme: Boolean(window.__ISTUDY_DRM_USED__),
    media_keys: videos.some(video => Boolean(video.mediaKeys)),
    mse: Boolean(window.__ISTUDY_MSE_USED__),
    mpd: performance.getEntriesByType('resource').some(entry => entry.name.toLowerCase().includes('.mpd')),
    videos: videos.map(video => ({ready: video.readyState >= 2, current_src: video.currentSrc || ''}))
  };
}
"""
URI_RE = re.compile(r'(?:^|,)URI=(?:"([^"]*)"|([^,]*))', re.IGNORECASE)
URI_VALUE_RE = re.compile(r'URI=(?:"([^"]*)"|([^,]*))', re.IGNORECASE)
METHOD_RE = re.compile(r'(?:^|,)METHOD=([^,]+)', re.IGNORECASE)
PLAYLIST_URI_TAGS = ("#EXT-X-MEDIA:", "#EXT-X-I-FRAME-STREAM-INF:", "#EXT-X-RENDITION-REPORT:")


@dataclass(frozen=True, slots=True)
class MediaCandidate:
    url: str
    kind: str
    headers: dict[str, str]

    def safe_summary(self) -> dict[str, object]:
        parsed = urlsplit(self.url)
        origin = f"{parsed.scheme}://{parsed.hostname or ''}" if parsed.scheme else ""
        return {"url": origin, "kind": self.kind, "headers": sorted(CANONICAL_HEADERS[key.casefold()] for key in self.headers if key.casefold() in CANONICAL_HEADERS)}


@dataclass(frozen=True, slots=True)
class MediaInfo:
    duration: float
    has_video: bool
    has_audio: bool


def response_kind(response: Response) -> str | None:
    url = response.url.casefold()
    content_type = response.headers.get("content-type", "").casefold()
    if ".mpd" in url or "dash+xml" in content_type:
        return "protected_or_unsupported"
    if ".m3u8" in url or "mpegurl" in content_type:
        return "hls"
    if ".mp4" in url or content_type.startswith("video/mp4"):
        return "mp4"
    return None


def playlist_is_protected(text: str) -> bool:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.split(":", 1)[0] in {"#EXT-X-KEY", "#EXT-X-SESSION-KEY"}:
            attributes = line.split(":", 1)[1] if ":" in line else ""
            method = METHOD_RE.search(attributes)
            if not method or method.group(1).strip().upper() != "NONE":
                return True
    return False


def _request_headers(page: Page, response: Response) -> dict[str, str]:
    headers = {CANONICAL_HEADERS[key.casefold()]: value for key, value in response.request.headers.items() if key.casefold() in CANONICAL_HEADERS}
    cookies = page.context.cookies(response.url)
    if cookies:
        headers["Cookie"] = "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in cookies)
    headers.setdefault("Referer", page.url)
    return headers


def _frame_states(page: Page) -> list[dict[str, object]]:
    return [frame.evaluate(FRAME_STATE_SCRIPT) for frame in page.frames]


def _raise_for_page_protection(page: Page, states: list[dict[str, object]]) -> None:
    if "eme" in page_media_usage(page) or any(state.get("eme") or state.get("media_keys") for state in states):
        raise ProtectedMedia("Encrypted Media Extensions were detected")
    if any(state.get("mpd") for state in states):
        raise ProtectedMedia("DASH media was detected")


def probe_media(page: Page, timeout_ms: int = 15000) -> MediaCandidate | None:
    candidate: MediaCandidate | None = None
    candidate_urls: set[str] = set()
    protected_response = False
    stable_since: float | None = None

    def on_response(response: Response) -> None:
        nonlocal candidate, protected_response
        kind = response_kind(response)
        if kind == "protected_or_unsupported":
            protected_response = True
        elif kind and candidate is None:
            candidate = MediaCandidate(response.url, kind, _request_headers(page, response))
            candidate_urls.update({response.url, getattr(response.request, "url", response.url)})

    page.on("response", on_response)
    for frame in page.frames:
        videos = frame.locator("video")
        if videos.count():
            videos.first.evaluate("el => { el.playbackRate = 1; return el.play(); }")
            break

    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        states = _frame_states(page)
        if protected_response:
            raise ProtectedMedia("DASH media was detected")
        _raise_for_page_protection(page, states)
        if candidate:
            mse_used = "mse" in page_media_usage(page) or any(state.get("mse") for state in states)
            if candidate.kind == "mp4" and mse_used:
                raise ProtectedMedia("MediaSource MP4 cannot be treated as progressive media")
            videos = [video for state in states for video in state.get("videos", [])]
            eligible = (
                any(video.get("ready") and video.get("current_src") in candidate_urls for video in videos)
                if candidate.kind == "mp4"
                else len(videos) == 1 and videos[0].get("ready")
            )
            if eligible:
                stable_since = stable_since or time.monotonic()
                if time.monotonic() - stable_since >= STABILITY_SECONDS:
                    final_states = _frame_states(page)
                    if protected_response:
                        raise ProtectedMedia("DASH media was detected")
                    _raise_for_page_protection(page, final_states)
                    final_videos = [video for state in final_states for video in state.get("videos", [])]
                    final_mse = "mse" in page_media_usage(page) or any(state.get("mse") for state in final_states)
                    final_eligible = (
                        any(video.get("ready") and video.get("current_src") in candidate_urls for video in final_videos)
                        if candidate.kind == "mp4"
                        else len(final_videos) == 1 and final_videos[0].get("ready")
                    )
                    if not final_eligible or (candidate.kind == "mp4" and final_mse):
                        raise ProtectedMedia("Media binding could not be verified")
                    return candidate
            else:
                stable_since = None
        page.wait_for_timeout(250)

    states = _frame_states(page)
    if protected_response:
        raise ProtectedMedia("DASH media was detected")
    _raise_for_page_protection(page, states)
    if candidate:
        raise ProtectedMedia("Media safety could not be established")
    return None


def _session(candidate: MediaCandidate) -> requests.Session:
    session = requests.Session()
    session.headers.update(candidate.headers)
    return session


def _origin(url: str) -> tuple[str, str, int]:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ProtectedMedia("Unsafe media origin")
    return parsed.scheme.casefold(), parsed.hostname.casefold(), parsed.port or (443 if parsed.scheme == "https" else 80)


def _same_origin_url(base: str, reference: str, root_origin: tuple[str, str, int]) -> str:
    if not reference.strip():
        raise ProtectedMedia("Invalid HLS resource URI")
    resolved = urljoin(base, reference.strip())
    if _origin(resolved) != root_origin:
        raise ProtectedMedia("Cross-origin HLS resource was rejected")
    return resolved


def _uri_attributes(line: str) -> list[str]:
    if "URI=" not in line.upper():
        return []
    matches = URI_RE.findall(line.split(":", 1)[1] if ":" in line else line)
    values = [(quoted or bare).strip() for quoted, bare in matches]
    if not values or any(not value for value in values):
        raise ProtectedMedia("Invalid HLS URI attribute")
    return values


def _hls_transport_headers(candidate: MediaCandidate) -> dict[str, str]:
    if urlsplit(candidate.url).query:
        raise ManualActionRequired("HLS direct download requires recording fallback")
    normalized = {key.casefold(): value for key, value in candidate.headers.items()}
    if "cookie" in normalized or "authorization" in normalized:
        raise ManualActionRequired("HLS direct download requires recording fallback")
    referer = normalized.get("referer")
    if referer and urlsplit(referer).query:
        raise ManualActionRequired("HLS direct download requires recording fallback")
    headers: dict[str, str] = {}
    if normalized.get("user-agent"):
        headers["User-Agent"] = normalized["user-agent"]
    if referer:
        headers["Referer"] = referer
    return headers


def _playlist_text(session: requests.Session, url: str) -> str:
    try:
        with session.get(url, timeout=30, stream=True, allow_redirects=False) as response:
            if 300 <= response.status_code < 400:
                raise RuntimeError("Media request redirect was rejected")
            response.raise_for_status()
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > MAX_PLAYLIST_BYTES:
                    raise ProtectedMedia("HLS playlist is too large")
                chunks.append(chunk)
            try:
                return b"".join(chunks).decode("utf-8-sig")
            except UnicodeDecodeError:
                raise ProtectedMedia("Invalid HLS playlist encoding") from None
    except requests.RequestException:
        raise RuntimeError("Media request failed") from None


def assert_clear_hls(candidate: MediaCandidate, max_playlists: int = MAX_HLS_PLAYLISTS) -> None:
    safe_headers = _hls_transport_headers(candidate)
    session = _session(MediaCandidate(candidate.url, candidate.kind, safe_headers))
    root_origin = _origin(candidate.url)
    pending = [candidate.url]
    known = {candidate.url}
    visited: set[str] = set()

    def register(url: str, is_playlist: bool) -> None:
        if url in known:
            return
        if len(known) >= max_playlists:
            raise ProtectedMedia("HLS graph limit exceeded")
        known.add(url)
        if is_playlist:
            pending.append(url)

    while pending:
        url = pending.pop()
        if url in visited:
            continue
        if len(visited) >= max_playlists:
            raise ProtectedMedia("HLS playlist graph limit exceeded")
        visited.add(url)
        text = _playlist_text(session, url)
        if next((line.strip() for line in text.splitlines() if line.strip()), "") != "#EXTM3U":
            raise ProtectedMedia("Invalid HLS playlist")
        if playlist_is_protected(text):
            raise ProtectedMedia("HLS playlist uses an encryption key")
        expect_playlist = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#EXT-X-STREAM-INF:"):
                expect_playlist = True
                continue
            if line.startswith("#"):
                for reference in _uri_attributes(line):
                    resolved = _same_origin_url(url, reference, root_origin)
                    register(resolved, line.startswith(PLAYLIST_URI_TAGS))
                continue
            resolved = _same_origin_url(url, line, root_origin)
            register(resolved, expect_playlist)
            if expect_playlist:
                expect_playlist = False
        if expect_playlist:
            raise ProtectedMedia("HLS variant URI is missing")


def _local_hls_name(url: str, playlist: bool) -> str:
    suffix = ".m3u8" if playlist else Path(urlsplit(url).path).suffix
    if not suffix or len(suffix) > 10 or not re.fullmatch(r"\.[A-Za-z0-9]+", suffix):
        suffix = ".bin"
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + suffix


def _snapshot_clear_hls(candidate: MediaCandidate, directory: Path, max_nodes: int = MAX_HLS_PLAYLISTS) -> Path:
    safe_headers = _hls_transport_headers(candidate)
    session = _session(MediaCandidate(candidate.url, candidate.kind, safe_headers))
    root_origin = _origin(candidate.url)
    directory.mkdir(parents=True, exist_ok=True)
    pending = [candidate.url]
    playlists = {candidate.url}
    resources: set[str] = set()

    def register(url: str, playlist: bool) -> str:
        if (playlist and url in resources) or (not playlist and url in playlists):
            raise ProtectedMedia("Ambiguous HLS graph node")
        known = playlists | resources
        if url not in known:
            if len(known) >= max_nodes:
                raise ProtectedMedia("HLS graph limit exceeded")
            (playlists if playlist else resources).add(url)
            if playlist:
                pending.append(url)
        return _local_hls_name(url, playlist)

    while pending:
        url = pending.pop()
        text = _playlist_text(session, url)
        if next((line.strip() for line in text.splitlines() if line.strip()), "") != "#EXTM3U" or playlist_is_protected(text):
            raise ProtectedMedia("Unsafe HLS playlist")
        rewritten: list[str] = []
        expect_playlist = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("#EXT-X-STREAM-INF:"):
                expect_playlist = True
                rewritten.append(raw_line)
                continue
            if line.startswith("#") and "URI=" in line.upper():
                is_playlist = line.startswith(PLAYLIST_URI_TAGS)

                def replace_uri(match: re.Match[str]) -> str:
                    reference = (match.group(1) or match.group(2)).strip()
                    resolved = _same_origin_url(url, reference, root_origin)
                    return f'URI="{register(resolved, is_playlist)}"'

                replaced, count = URI_VALUE_RE.subn(replace_uri, raw_line)
                if count == 0:
                    raise ProtectedMedia("Invalid HLS URI attribute")
                rewritten.append(replaced)
                continue
            if line and not line.startswith("#"):
                resolved = _same_origin_url(url, line, root_origin)
                rewritten.append(register(resolved, expect_playlist))
                expect_playlist = False
                continue
            rewritten.append(raw_line)
        if expect_playlist:
            raise ProtectedMedia("HLS variant URI is missing")
        (directory / _local_hls_name(url, True)).write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    for url in resources:
        try:
            with session.get(url, stream=True, timeout=(30, 120), allow_redirects=False) as response:
                if 300 <= response.status_code < 400:
                    raise RuntimeError("Media request redirect was rejected")
                response.raise_for_status()
                with (directory / _local_hls_name(url, False)).open("wb") as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
        except requests.RequestException:
            raise RuntimeError("Media request failed") from None
    return directory / _local_hls_name(candidate.url, True)


def _ffmpeg_headers(headers: dict[str, str]) -> str:
    return "".join(f"{key}: {value}\r\n" for key, value in headers.items())


def download_direct(candidate: MediaCandidate, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".part.mp4")
    if candidate.kind == "mp4":
        try:
            with _session(candidate).get(candidate.url, stream=True, timeout=(30, 120), allow_redirects=False) as response:
                if 300 <= response.status_code < 400:
                    raise RuntimeError("Media request redirect was rejected")
                response.raise_for_status()
                with partial.open("wb") as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
        except requests.RequestException:
            raise RuntimeError("Media request failed") from None
        os.replace(partial, destination)
        return "mp4"
    if candidate.kind == "hls":
        _hls_transport_headers(candidate)
        local_manifest = _snapshot_clear_hls(candidate, destination.with_suffix(".part.hls"))
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-protocol_whitelist", "file", "-i", str(local_manifest), "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", str(partial)]
        try:
            subprocess.run(command, check=True, capture_output=True)
        except (subprocess.CalledProcessError, OSError):
            raise RuntimeError("Media conversion failed") from None
        os.replace(partial, destination)
        return "hls"
    raise ValueError(f"Unsupported candidate kind: {candidate.kind}")


def validate_probe_json(data: dict[str, object], require_audio: bool) -> MediaInfo:
    streams = data.get("streams", [])
    duration = float(data.get("format", {}).get("duration", 0))
    has_video = any(stream.get("codec_type") == "video" for stream in streams)
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    if not math.isfinite(duration) or duration <= 0 or not has_video or (require_audio and not has_audio):
        raise ValueError(f"Invalid media: duration={duration}, video={has_video}, audio={has_audio}")
    return MediaInfo(duration, has_video, has_audio)


def validate_media(path: Path, require_audio: bool = True) -> MediaInfo:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Media file is missing or empty: {path}")
    command = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    return validate_probe_json(json.loads(result.stdout), require_audio)
```

Do not log raw cookies, signed query strings, authorization headers, or full request dumps.

- [ ] **Step 4: Run media tests**

```bash
python -m unittest tests.test_media -v
```

Expected: 18 tests pass.

- [ ] **Step 5: Run a real ffprobe sanity check**

Generate and validate a two-second local sample:

```bash
ffmpeg -hide_banner -loglevel error -y -f lavfi -i testsrc=size=320x180:rate=30 -f lavfi -i sine=frequency=1000 -t 2 -c:v libx264 -c:a aac artifacts/sample.mp4
python -c "from pathlib import Path; from istudy_backup.media import validate_media; print(validate_media(Path('artifacts/sample.mp4')))"
```

Expected: output contains `duration=2` (allowing minor container variance), `has_video=True`, and `has_audio=True`.

---

### Task 6: Normal-Speed Chrome Tab Recording Fallback

**Files:**
- Create: `istudy-private-backup/extension/manifest.json`
- Create: `istudy-private-backup/extension/service-worker.js`
- Create: `istudy-private-backup/extension/offscreen.html`
- Create: `istudy-private-backup/extension/offscreen.js`
- Create: `istudy-private-backup/istudy_backup/recorder.py`
- Create: `istudy-private-backup/tests/test_recorder.py`
- Create: `istudy-private-backup/tools/recording_smoke.py`

**Interfaces:**
- Consumes: `BrowserContext`, `Page`, `Paths`, `validate_media`
- Produces: `TabRecorder.record(page: Page, destination: Path) -> None`
- Recording contract: current course tab only, video playback rate exactly `1.0`, audio included, output remuxed/transcoded to MP4, protected content rejected before this interface is called.

- [ ] **Step 1: Write the failing recorder helper tests**

Create `tests/test_recorder.py`:

```python
import tempfile
import unittest
from pathlib import Path

from istudy_backup.recorder import capture_output_is_ready, recording_timeout_ms


class RecorderTests(unittest.TestCase):
    def test_timeout_allows_duration_plus_sixty_seconds(self):
        self.assertEqual(recording_timeout_ms(120.2), 181_000)

    def test_capture_requires_nonempty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current.webm"
            self.assertFalse(capture_output_is_ready(path))
            path.write_bytes(b"123")
            self.assertTrue(capture_output_is_ready(path))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_recorder -v
```

Expected: import failure for `istudy_backup.recorder`.

- [ ] **Step 3: Create the Manifest V3 extension**

Create `extension/manifest.json`:

```json
{
  "manifest_version": 3,
  "name": "Authorized iStudy Tab Recorder",
  "version": "1.0.0",
  "permissions": ["tabCapture", "offscreen", "downloads", "storage"],
  "background": {"service_worker": "service-worker.js"},
  "commands": {
    "toggle-recording": {
      "suggested_key": {"default": "Ctrl+Shift+9"},
      "description": "Start or stop authorized tab recording"
    }
  }
}
```

Create `extension/offscreen.html`:

```html
<!doctype html><meta charset="utf-8"><script src="offscreen.js"></script>
```

Create `extension/service-worker.js`:

```javascript
async function ensureOffscreen() {
  if (await chrome.offscreen.hasDocument()) return;
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["USER_MEDIA"],
    justification: "Record an authorized course tab with its audio"
  });
}

chrome.commands.onCommand.addListener(async command => {
  if (command !== "toggle-recording") return;
  const state = await chrome.storage.local.get({recording: false});
  if (state.recording) {
    await chrome.runtime.sendMessage({type: "STOP_CAPTURE"});
    await chrome.storage.local.set({recording: false});
    return;
  }
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  const allowed = tab?.url?.startsWith("https://istudy.way-to-win.com/")
    || tab?.url?.startsWith("http://127.0.0.1:");
  if (!tab?.id || !allowed) return;
  await ensureOffscreen();
  const streamId = await chrome.tabCapture.getMediaStreamId({targetTabId: tab.id});
  await chrome.runtime.sendMessage({type: "START_CAPTURE", streamId});
  await chrome.storage.local.set({recording: true});
});

chrome.runtime.onMessage.addListener(message => {
  if (message?.type === "CAPTURE_STOPPED") {
    chrome.storage.local.set({recording: false});
  }
});
```

Create `extension/offscreen.js`:

```javascript
let recorder;
let stream;
let chunks = [];
let monitor;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "START_CAPTURE") startCapture(message.streamId).then(sendResponse);
  if (message?.type === "STOP_CAPTURE") stopCapture().then(sendResponse);
  return true;
});

async function startCapture(streamId) {
  chunks = [];
  stream = await navigator.mediaDevices.getUserMedia({
    audio: {mandatory: {chromeMediaSource: "tab", chromeMediaSourceId: streamId}},
    video: {mandatory: {chromeMediaSource: "tab", chromeMediaSourceId: streamId}}
  });
  monitor = new AudioContext();
  monitor.createMediaStreamSource(stream).connect(monitor.destination);
  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
    ? "video/webm;codecs=vp9,opus"
    : "video/webm";
  recorder = new MediaRecorder(stream, {mimeType});
  recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
  recorder.start(1000);
}

async function stopCapture() {
  if (!recorder || recorder.state === "inactive") return;
  await new Promise(resolve => {
    recorder.onstop = resolve;
    recorder.stop();
  });
  const blob = new Blob(chunks, {type: recorder.mimeType});
  await chrome.downloads.download({
    url: URL.createObjectURL(blob),
    filename: "istudy-backup/current.webm",
    conflictAction: "overwrite",
    saveAs: false
  });
  stream.getTracks().forEach(track => track.stop());
  await monitor?.close();
  await chrome.runtime.sendMessage({type: "CAPTURE_STOPPED"});
}
```

- [ ] **Step 4: Implement the Python recorder controller**

Create `istudy_backup/recorder.py`:

```python
from __future__ import annotations

import math
import os
import subprocess
import time
from pathlib import Path

from playwright.sync_api import BrowserContext, Page

from .core import ManualActionRequired, Paths
from .media import validate_media


def recording_timeout_ms(duration_seconds: float) -> int:
    return int(duration_seconds + 60.999) * 1000


def capture_output_is_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def wait_for_stable_capture(path: Path, timeout_seconds: float = 60) -> bool:
    deadline = time.monotonic() + timeout_seconds
    previous_size = -1
    stable_since: float | None = None
    while time.monotonic() < deadline:
        size = path.stat().st_size if path.is_file() else 0
        if size > 0 and size == previous_size:
            stable_since = stable_since or time.monotonic()
            if time.monotonic() - stable_since >= 2:
                return True
        else:
            stable_since = None
        previous_size = size
        time.sleep(0.5)
    return False


class TabRecorder:
    def __init__(self, context: BrowserContext, paths: Paths):
        self.context = context
        self.paths = paths

    def _extension_worker(self):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            workers = [worker for worker in self.context.service_workers if worker.url.startswith("chrome-extension://")]
            if workers:
                return workers[0]
            time.sleep(0.25)
        raise ManualActionRequired("Recorder extension service worker is unavailable")

    def _recording_active(self) -> bool:
        return bool(
            self._extension_worker().evaluate(
                "async () => (await chrome.storage.local.get({recording: false})).recording"
            )
        )

    def _wait_recording_state(self, expected: bool, timeout_seconds: float = 5) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._recording_active() is expected:
                return
            time.sleep(0.25)
        raise ManualActionRequired("Chrome did not confirm the recorder shortcut; use the extension shortcut manually and rerun")

    def _toggle(self, page: Page, expected: bool) -> None:
        page.bring_to_front()
        page.keyboard.press("Control+Shift+9")
        self._wait_recording_state(expected)

    def _video_frame(self, page: Page):
        for frame in page.frames:
            if frame.locator("video").count():
                return frame
        raise ManualActionRequired("No HTML video element is available for recording")

    def record(self, page: Page, destination: Path) -> None:
        frame = self._video_frame(page)
        drm_used = any(item.evaluate("() => Boolean(window.__ISTUDY_DRM_USED__)") for item in page.frames)
        if drm_used:
            raise ManualActionRequired("Recording is disabled because EME was requested")
        video = frame.locator("video").first
        duration = float(video.evaluate("el => el.duration"))
        if not math.isfinite(duration) or duration <= 0:
            raise ManualActionRequired("Video duration is unavailable")
        self.paths.capture_file.unlink(missing_ok=True)
        video.evaluate("el => { el.pause(); el.currentTime = 0; el.playbackRate = 1; }")
        self._toggle(page, True)
        video.evaluate("el => el.play()")
        frame.wait_for_function("() => document.querySelector('video')?.ended === true", timeout=recording_timeout_ms(duration))
        self._toggle(page, False)
        if not wait_for_stable_capture(self.paths.capture_file):
            raise ManualActionRequired("Tab recording did not finish writing a stable file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(".part.mp4")
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(self.paths.capture_file),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-movflags", "+faststart", str(partial),
        ]
        subprocess.run(command, check=True)
        validate_media(partial)
        os.replace(partial, destination)
```

- [ ] **Step 5: Run recorder unit tests**

```bash
python -m unittest tests.test_recorder -v
```

Expected: 2 tests pass.

- [ ] **Step 6: Add and run the synthetic tab-capture gate**

Create `tools/recording_smoke.py`:

```python
from __future__ import annotations

import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from istudy_backup.browser import ChromeSession
from istudy_backup.core import Paths
from istudy_backup.media import validate_media
from istudy_backup.recorder import TabRecorder
from istudy_backup.state import StateStore


paths = Paths.from_root(ROOT)
paths.ensure_runtime_dirs()
source = paths.artifacts_dir / "smoke-source.mp4"
html = paths.artifacts_dir / "smoke.html"
destination = paths.artifacts_dir / "smoke-recorded.mp4"
subprocess.run(
    [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000",
        "-t", "3", "-c:v", "libx264", "-c:a", "aac", str(source),
    ],
    check=True,
)
html.write_text('<video controls src="/smoke-source.mp4"></video>', encoding="utf-8")
handler = partial(SimpleHTTPRequestHandler, directory=str(paths.artifacts_dir))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with ChromeSession(paths) as session:
        assert session.context is not None
        page = session.new_page()
        page.goto(f"http://127.0.0.1:{server.server_port}/smoke.html", wait_until="domcontentloaded")
        TabRecorder(session.context, paths).record(page, destination)
    info = validate_media(destination)
    data = StateStore(paths.state_file).load()
    data.recording_smoke_passed = True
    StateStore(paths.state_file).save(data)
    print(f"recording smoke passed: duration={info.duration}, audio={info.has_audio}")
finally:
    server.shutdown()
    server.server_close()
```

Run:

```bash
python tools/recording_smoke.py
```

Expected: `recording smoke passed` with `audio=True`, and `data/state.json` contains `"recording_smoke_passed": true`. If the command fails, leave the flag false and do not attempt fallback recording on course content; direct non-DRM download remains available.

---

### Task 7: YouTube Studio Private Upload With Readback

**Files:**
- Create: `istudy-private-backup/istudy_backup/youtube.py`
- Create: `istudy-private-backup/tests/test_youtube.py`

**Interfaces:**
- Consumes: Playwright `Page`, validated `VideoRecord`, `PrivacyViolation`
- Produces: `youtube_title(record: VideoRecord) -> str`
- Produces: `privacy_is_private(text: str) -> bool`
- Produces: `YouTubeStudioUploader.upload_private(page: Page, record: VideoRecord) -> UploadResult`
- Produces: `YouTubeStudioUploader.verify_private(page: Page, video_id: str) -> bool`

- [ ] **Step 1: Write failing fail-closed tests**

Create `tests/test_youtube.py`:

```python
import unittest

from istudy_backup.core import VideoRecord
from istudy_backup.youtube import privacy_is_private, youtube_title


class YouTubeTests(unittest.TestCase):
    def test_title_has_course_prefix_and_limit(self):
        record = VideoRecord("id", "115暑電子1", "第一講" * 50, "c", "p")
        title = youtube_title(record)
        self.assertTrue(title.startswith("[115暑電子1] "))
        self.assertLessEqual(len(title), 100)

    def test_only_explicit_private_text_passes(self):
        self.assertTrue(privacy_is_private("Private"))
        self.assertTrue(privacy_is_private("私人"))
        self.assertFalse(privacy_is_private("Unlisted"))
        self.assertFalse(privacy_is_private("不公開"))
        self.assertFalse(privacy_is_private("Public"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_youtube -v
```

Expected: import failure for `istudy_backup.youtube`.

- [ ] **Step 3: Implement stable selectors and privacy readback**

Create `istudy_backup/youtube.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page

from .core import PrivacyViolation, VideoRecord


STUDIO_URL = "https://studio.youtube.com/"


@dataclass(frozen=True, slots=True)
class UploadResult:
    video_id: str
    video_url: str
    privacy: str


def youtube_title(record: VideoRecord) -> str:
    prefix = f"[{record.course}] "
    return (prefix + record.title.strip())[:100]


def privacy_is_private(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip().casefold()
    return normalized in {"private", "私人"}


class YouTubeStudioUploader:
    def upload_private(self, page: Page, record: VideoRecord) -> UploadResult:
        if not record.local_path:
            raise ValueError("Validated local_path is required")
        page.goto(STUDIO_URL, wait_until="domcontentloaded")
        page.locator("ytcp-button#create-icon").click()
        page.locator('tp-yt-paper-item[test-id="upload-beta"]').click()
        page.locator('input[type="file"]').set_input_files(str(Path(record.local_path).resolve()))
        title_box = page.locator("ytcp-social-suggestions-textbox#title-textarea #textbox")
        title_box.wait_for(state="visible")
        title_box.fill(youtube_title(record))
        for _ in range(3):
            page.locator("ytcp-button#next-button").click()
        private_radio = page.locator('tp-yt-paper-radio-button[name="PRIVATE"]')
        private_radio.wait_for(state="visible")
        private_radio.click()
        if private_radio.get_attribute("aria-checked") != "true":
            raise PrivacyViolation("Private radio button is not selected")
        done = page.locator("ytcp-button#done-button")
        done.wait_for(state="visible", timeout=30 * 60 * 1000)
        if done.get_attribute("disabled") is not None:
            page.wait_for_function("() => !document.querySelector('ytcp-button#done-button')?.hasAttribute('disabled')", timeout=30 * 60 * 1000)
        done.click()
        share = page.locator("a#share-url")
        share.wait_for(state="visible")
        video_url = share.get_attribute("href") or share.inner_text()
        match = re.search(r"(?:youtu\.be/|v=)([A-Za-z0-9_-]{6,})", video_url)
        if not match:
            raise RuntimeError(f"Could not extract YouTube video id from {video_url}")
        video_id = match.group(1)
        privacy = self.read_privacy(page, video_id)
        if not privacy_is_private(privacy):
            raise PrivacyViolation(f"YouTube readback was not Private: {privacy}")
        return UploadResult(video_id, f"https://youtu.be/{video_id}", privacy)

    def read_privacy(self, page: Page, video_id: str) -> str:
        page.goto(f"https://studio.youtube.com/video/{video_id}/edit", wait_until="domcontentloaded")
        control = page.locator("ytcp-video-visibility-select")
        control.wait_for(state="visible")
        selected = control.locator("#selected-item")
        if selected.count() == 1:
            value = selected.inner_text().strip()
        else:
            value = control.evaluate(
                "el => el.selectedVisibility || el.getAttribute('selected-visibility') || ''"
            ).strip()
        if not value:
            raise PrivacyViolation("YouTube visibility control did not expose a selected value")
        return value

    def verify_private(self, page: Page, video_id: str) -> bool:
        return privacy_is_private(self.read_privacy(page, video_id))
```

The live trial is the UI contract test. If any selector is absent or YouTube changes its DOM, stop and update only `youtube.py`; never fall back to clicking by coordinates or assuming the default visibility.

- [ ] **Step 4: Run YouTube unit tests**

```bash
python -m unittest tests.test_youtube -v
```

Expected: 2 tests pass.

---

### Task 8: Sequential Workflow, Trial Gate, Retry Policy, and Report

**Files:**
- Create: `istudy-private-backup/istudy_backup/workflow.py`
- Create: `istudy-private-backup/tests/test_workflow.py`

**Interfaces:**
- Consumes: `StateStore`, `ChromeSession`, `open_video`, `probe_media`, `download_direct`, `TabRecorder`, `validate_media`, `YouTubeStudioUploader`
- Produces: `run_one(record, services) -> VideoRecord`
- Produces: `run_trial(data) -> None`, `run_batch(data) -> None`, `write_report(data, path) -> None`

- [ ] **Step 1: Write failing orchestration tests with fakes**

Create `tests/test_workflow.py`:

```python
import tempfile
import unittest
from pathlib import Path

from istudy_backup.core import PrivacyViolation, Status, VideoRecord, WorkflowData
from istudy_backup.workflow import batch_is_allowed, mark_trial_passed, should_skip


class WorkflowTests(unittest.TestCase):
    def record(self, status=Status.DISCOVERED):
        return VideoRecord("id", "115暑電子1", "第一講", "c", "p", status=status)

    def test_batch_is_locked_before_trial(self):
        self.assertFalse(batch_is_allowed(WorkflowData(trial_passed=False)))
        self.assertTrue(batch_is_allowed(WorkflowData(trial_passed=True)))

    def test_trial_requires_private_upload(self):
        data = WorkflowData(videos={"id": self.record(Status.UPLOADED_PRIVATE)})
        data.videos["id"].youtube_privacy = "Private"
        mark_trial_passed(data, "id")
        self.assertTrue(data.trial_passed)

    def test_completed_private_item_is_skipped_on_rerun(self):
        record = self.record(Status.UPLOADED_PRIVATE)
        record.youtube_id = "abc123"
        record.youtube_privacy = "私人"
        self.assertTrue(should_skip(record))

    def test_unlisted_item_is_not_treated_as_complete(self):
        record = self.record(Status.UPLOADED_PRIVATE)
        record.youtube_id = "abc123"
        record.youtube_privacy = "不公開"
        self.assertFalse(should_skip(record))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify failure**

```bash
python -m unittest tests.test_workflow -v
```

Expected: import failure for `istudy_backup.workflow`.

- [ ] **Step 3: Implement the fail-closed orchestration helpers**

Create `istudy_backup/workflow.py` with these exact policies:

```python
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Callable

from .core import ManualActionRequired, PrivacyViolation, ProtectedMedia, Status, VideoRecord, WorkflowData
from .youtube import privacy_is_private


RETRY_DELAYS = (2, 5, 15)


def batch_is_allowed(data: WorkflowData) -> bool:
    return data.trial_passed


def should_skip(record: VideoRecord) -> bool:
    return (
        record.status == Status.UPLOADED_PRIVATE
        and bool(record.youtube_id)
        and bool(record.youtube_privacy)
        and privacy_is_private(record.youtube_privacy)
    )


def mark_trial_passed(data: WorkflowData, video_id: str) -> None:
    record = data.videos[video_id]
    if not should_skip(record):
        raise PrivacyViolation("Trial cannot pass without verified Private upload")
    data.trial_passed = True
    data.stopped_reason = None


def retry(operation: Callable[[], object]) -> object:
    last_error: Exception | None = None
    for attempt, delay in enumerate((0, *RETRY_DELAYS), start=1):
        if delay:
            time.sleep(delay)
        try:
            return operation()
        except (ProtectedMedia, PrivacyViolation, ManualActionRequired):
            raise
        except Exception as error:
            last_error = error
            if attempt == 4:
                raise
    raise last_error or RuntimeError("retry exhausted")


def write_report(data: WorkflowData, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_course: dict[str, Counter] = {}
    for record in data.videos.values():
        by_course.setdefault(record.course, Counter())[record.status.value] += 1
    lines = ["# iStudy Backup Report", "", f"Trial passed: {data.trial_passed}", ""]
    for course in sorted(by_course, key=lambda name: int(name.removeprefix("115暑電子"))):
        counts = by_course[course]
        lines.append(f"## {course}")
        lines.append("")
        for status, count in sorted(counts.items()):
            lines.append(f"- {status}: {count}")
        lines.append("")
    failures = [record for record in data.videos.values() if record.error]
    if failures:
        lines += ["## Failures", ""]
        lines += [f"- {record.course} / {record.title}: {record.error}" for record in failures]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

Append this concrete dependency-injected state machine to `workflow.py`:

```python
from dataclasses import dataclass
from typing import Any

from .core import Paths, safe_filename
from .media import MediaCandidate, MediaInfo
from .state import StateStore
from .youtube import UploadResult


@dataclass(slots=True)
class Services:
    store: StateStore
    paths: Paths
    open_video: Callable[[VideoRecord], Any]
    probe_media: Callable[[Any], MediaCandidate | None]
    download_direct: Callable[[MediaCandidate, Path], str]
    record_tab: Callable[[Any, Path], None]
    validate_media: Callable[[Path], MediaInfo]
    upload_private: Callable[[VideoRecord], UploadResult]
    verify_private: Callable[[str], bool]


def _destination(paths: Paths, record: VideoRecord) -> Path:
    number = int(record.course.removeprefix("115暑電子"))
    folder = paths.downloads_dir / f"115暑電子{number:02d}"
    return folder / f"{safe_filename(record.title)}-{record.id}.mp4"


def _stop(store: StateStore, reason: str) -> None:
    data = store.load()
    data.stopped_reason = reason
    store.save(data)


def run_one(video_id: str, services: Services) -> VideoRecord:
    current = services.store.load().videos[video_id]
    if should_skip(current):
        if not services.verify_private(current.youtube_id or ""):
            _stop(services.store, f"Remote privacy readback failed for {video_id}")
            raise PrivacyViolation("Previously completed video is no longer confirmed Private")
        return current

    def attempt() -> VideoRecord:
        record = services.store.load().videos[video_id]
        record = services.store.transition(
            video_id,
            Status.PROCESSING,
            attempts=record.attempts + 1,
            error=None,
        )
        destination = Path(record.local_path) if record.local_path else _destination(services.paths, record)
        local_is_valid = False
        if destination.is_file():
            try:
                services.validate_media(destination)
                local_is_valid = True
            except Exception:
                local_is_valid = False
        if not local_is_valid:
            page = services.open_video(record)
            try:
                candidate = services.probe_media(page)
                if candidate is None:
                    services.record_tab(page, destination)
                    method = "tab-recording"
                else:
                    method = services.download_direct(candidate, destination)
            finally:
                page.close()
            services.validate_media(destination)
        else:
            method = record.method or "existing-validated-file"
        record = services.store.transition(
            video_id,
            Status.VERIFIED,
            local_path=str(destination),
            method=method,
        )
        record = services.store.transition(video_id, Status.UPLOADING)
        result = services.upload_private(record)
        if not privacy_is_private(result.privacy):
            raise PrivacyViolation(f"Upload result was not Private: {result.privacy}")
        return services.store.transition(
            video_id,
            Status.UPLOADED_PRIVATE,
            youtube_id=result.video_id,
            youtube_url=result.video_url,
            youtube_privacy=result.privacy,
            error=None,
        )

    try:
        return retry(attempt)
    except ProtectedMedia as error:
        return services.store.transition(
            video_id,
            Status.SKIPPED_PROTECTED,
            error=f"{type(error).__name__}: {error}",
        )
    except PrivacyViolation as error:
        services.store.transition(
            video_id,
            Status.FAILED,
            error=f"{type(error).__name__}: {error}",
        )
        _stop(services.store, str(error))
        raise
    except ManualActionRequired as error:
        services.store.transition(
            video_id,
            Status.FAILED,
            error=f"{type(error).__name__}: {error}",
        )
        _stop(services.store, str(error))
        raise
    except Exception as error:
        return services.store.transition(
            video_id,
            Status.FAILED,
            error=f"{type(error).__name__}: {error}",
        )
```

The fake-service tests call this exact interface, so they can prove duplicate-free reruns and queue-stopping privacy behavior without opening Chrome.

- [ ] **Step 4: Run workflow tests**

```bash
python -m unittest tests.test_workflow -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Add a duplicate-free fake end-to-end test**

Extend `tests/test_workflow.py` with fakes that count download and upload calls. Execute the same `VideoRecord` twice; after the first run sets `UPLOADED_PRIVATE`, the second run must leave both call counters at one. The fake uploader must return `privacy="Private"`; changing it to `Unlisted` must raise `PrivacyViolation` and prevent the next record from starting.

---

### Task 9: CLI Commands and Mandatory Trial Gate

**Files:**
- Create: `istudy-private-backup/istudy_backup/__main__.py`
- Create: `istudy-private-backup/README.md`

**Interfaces:**
- Produces commands:
  - `python -m istudy_backup setup`
  - `python -m istudy_backup discover`
  - `python -m istudy_backup trial`
  - `python -m istudy_backup run`
  - `python -m istudy_backup report`

- [ ] **Step 1: Implement the CLI parser with no destructive commands**

Create `istudy_backup/__main__.py` with this complete parser and dispatch code. It exposes only the five commands above; there is no `clean`, `delete`, `publish`, `public`, or `unlisted` option.

```python
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from urllib.parse import urljoin

from .browser import ChromeSession, GOOGLE_ACCOUNT, ISTUDY_HOME, YOUTUBE_STUDIO
from .core import ManualActionRequired, Paths, Status, WorkflowData
from .media import download_direct, probe_media, validate_media
from .recorder import TabRecorder
from .site import discover_target_courses, discover_video_candidates, open_video, records_from_candidates
from .state import StateStore
from .workflow import Services, batch_is_allowed, mark_trial_passed, run_one, write_report
from .youtube import YouTubeStudioUploader


EXPECTED_ACCOUNT = "liuaaron0226@gmail.com"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths.from_root(PROJECT_ROOT)
STORE = StateStore(PATHS.state_file)
MIN_FREE_BYTES = 10 * 1024**3


def sort_key(record):
    return (int(record.course.removeprefix("115暑電子")), record.title.casefold(), record.id)


def make_services(session: ChromeSession) -> Services:
    assert session.context is not None
    recorder = TabRecorder(session.context, PATHS)
    uploader = YouTubeStudioUploader()
    upload_page = session.new_page()

    def record_tab(page, destination):
        if not STORE.load().recording_smoke_passed:
            raise ManualActionRequired("Recording fallback is locked until tools/recording_smoke.py passes")
        recorder.record(page, destination)

    return Services(
        store=STORE,
        paths=PATHS,
        open_video=lambda record: open_video(session.context, record),
        probe_media=probe_media,
        download_direct=download_direct,
        record_tab=record_tab,
        validate_media=validate_media,
        upload_private=lambda record: uploader.upload_private(upload_page, record),
        verify_private=lambda video_id: uploader.verify_private(upload_page, video_id),
    )


def cmd_setup() -> int:
    with ChromeSession(PATHS) as session:
        for url in (GOOGLE_ACCOUNT, ISTUDY_HOME, YOUTUBE_STUDIO):
            session.new_page().goto(url, wait_until="domcontentloaded")
        print("Use only this dedicated Chrome window. Enter passwords manually; the program does not read them.")
        input("Press Enter after Google, iStudy, and YouTube Studio are signed in: ")
        session.verify_accounts(EXPECTED_ACCOUNT)
    print("dedicated profile verified")
    return 0


def cmd_discover() -> int:
    with ChromeSession(PATHS) as session:
        session.verify_accounts(EXPECTED_ACCOUNT)
        home = session.new_page()
        home.goto(ISTUDY_HOME, wait_until="domcontentloaded")
        courses = discover_target_courses(home)
        records = []
        for course in courses:
            course_url = urljoin(home.url, course.href)
            course_page = session.new_page()
            course_page.goto(course_url, wait_until="domcontentloaded")
            candidates = discover_video_candidates(course_page)
            records.extend(records_from_candidates(course, candidates, home.url))
            course_page.close()
    for record in sorted(records, key=sort_key):
        print(f"{record.course}\t{record.title}\t{record.page_url}")
    if input("Type ACCEPT DISCOVERY to save this manifest: ").strip() != "ACCEPT DISCOVERY":
        print("discovery discarded")
        return 2
    data = STORE.load()
    for record in records:
        data.videos.setdefault(record.id, record)
    STORE.save(data)
    print(f"saved {len(records)} discovered videos")
    return 0


def cmd_trial() -> int:
    data = STORE.load()
    candidates = sorted(
        (record for record in data.videos.values() if record.course == "115暑電子1"),
        key=sort_key,
    )
    if not candidates:
        raise ManualActionRequired("Run discover before trial")
    trial_id = candidates[0].id
    with ChromeSession(PATHS) as session:
        session.verify_accounts(EXPECTED_ACCOUNT)
        services = make_services(session)
        first = run_one(trial_id, services)
        attempts_before = first.attempts
        youtube_id_before = first.youtube_id
        second = run_one(trial_id, services)
        if second.attempts != attempts_before or second.youtube_id != youtube_id_before:
            raise RuntimeError("Trial rerun was not duplicate-free")
        data = STORE.load()
        mark_trial_passed(data, trial_id)
        STORE.save(data)
    print(f"trial passed: {second.youtube_url}")
    return 0


def cmd_run() -> int:
    data = STORE.load()
    if not batch_is_allowed(data):
        raise ManualActionRequired("Batch is locked until trial passes")
    pending = [record for record in sorted(data.videos.values(), key=sort_key) if record.status != Status.SKIPPED_PROTECTED]
    print(f"batch manifest contains {len(pending)} records")
    if input("Type RUN 115暑電子1-15 to continue: ").strip() != "RUN 115暑電子1-15":
        print("batch cancelled")
        return 2
    with ChromeSession(PATHS) as session:
        session.verify_accounts(EXPECTED_ACCOUNT)
        services = make_services(session)
        for record in pending:
            free = shutil.disk_usage(PATHS.downloads_dir).free
            if free < MIN_FREE_BYTES:
                data = STORE.load()
                data.stopped_reason = f"Insufficient disk space: {free} bytes free"
                STORE.save(data)
                raise RuntimeError(data.stopped_reason)
            run_one(record.id, services)
    return 0


def cmd_report() -> int:
    write_report(STORE.load(), PATHS.reports_dir / "latest.md")
    print(PATHS.reports_dir / "latest.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m istudy_backup")
    parser.add_argument("command", choices=("setup", "discover", "trial", "run", "report"))
    command = parser.parse_args().command
    return {
        "setup": cmd_setup,
        "discover": cmd_discover,
        "trial": cmd_trial,
        "run": cmd_run,
        "report": cmd_report,
    }[command]()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Add disk-space preflight**

Before each new video, call `shutil.disk_usage(PATHS.downloads_dir)`. Require at least 10 GiB free. If less, set `stopped_reason` to the exact free-byte count, save state, and stop before opening the next video. This is a conservative guard, not an estimate of total course size.

- [ ] **Step 3: Write README with exact operator sequence**

Create `README.md` with:

````markdown
# iStudy Private Backup

This tool processes only authorized, non-DRM course media and uploads validated files to YouTube as Private.

## Safety

- Use only the dedicated Chrome window opened by this tool.
- Sign in manually as `liuaaron0226@gmail.com`.
- Do not run personal Chrome against `data/chrome-profile`.
- CAPTCHA, duplicate-login, DRM, encrypted HLS, and account-security prompts stop the workflow.
- Local validated videos are never deleted automatically.

## Run order

```bash
python -m unittest discover -s tests -v
python -m istudy_backup setup
python -m istudy_backup discover
python -m istudy_backup trial
python -m istudy_backup report
python -m istudy_backup run
python -m istudy_backup report
```

`trial` handles only the first video in `115暑電子1`. `run` remains locked until trial upload is read back as Private and a second trial invocation proves the item is skipped rather than uploaded again.
````

- [ ] **Step 4: Run the complete local test suite**

```bash
python -m unittest discover -s tests -v
```

Expected: every unit test passes; no Chrome window opens during unit tests.

---

### Task 10: Live Synthetic Recording Test and Single-Video End-to-End Trial

**Files:**
- Runtime only: `istudy-private-backup/artifacts/`, `data/`, `downloads/`, `reports/`
- Modify source only if a live selector contract differs from the tested site UI; keep such changes confined to `site.py` or `youtube.py` and add a regression test.

**Interfaces:**
- Consumes all preceding tasks.
- Produces: one validated local trial file, one YouTube video confirmed Private, `trial_passed=true`, and a rerun proving no duplicate upload.

- [ ] **Step 1: Verify installed binaries and dependencies**

```bash
python --version
python -m pip check
ffmpeg -version
ffprobe -version
```

Expected: Python 3.11.x, no broken Python requirements, FFmpeg and ffprobe available.

- [ ] **Step 2: Run all local tests**

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Complete dedicated-profile login**

```bash
python -m istudy_backup setup
```

In the dedicated Chrome window only, manually sign into Google as `liuaaron0226@gmail.com`, iStudy, and YouTube Studio. Close or log out other iStudy sessions if the site reports duplicate login. The command must finish with a verified-account success message.

- [ ] **Step 4: Discover and review the full course manifest**

```bash
python -m istudy_backup discover
```

Expected before confirmation:

- Exactly 15 courses, numbered 1 through 15.
- At least one video candidate in each course, or a fail-closed diagnostic report naming the course.
- No downloads and no YouTube activity.

Review every printed title, then enter `ACCEPT DISCOVERY`.

- [ ] **Step 5: Test tab recording on synthetic media**

```bash
python tools/recording_smoke.py
```

Expected: `recording smoke passed` with `audio=True`. If it fails, keep `recording_smoke_passed` false; the workflow may continue with direct non-DRM downloads but must mark any item requiring recording as failed with `ManualActionRequired`.

- [ ] **Step 6: Run the first-video trial**

```bash
python -m istudy_backup trial
```

Expected:

- Only the first sorted video in `115暑電子1` is processed.
- Direct MP4/HLS is preferred; recording is used only when no ordinary media candidate exists and the recording smoke test passed.
- The local file passes ffprobe validation.
- YouTube Studio selects Private before completion.
- The resulting video is reopened in Studio and read back as Private.
- State records `uploaded_private`, the YouTube ID, and `youtube_privacy` as `Private` or `私人`.

- [ ] **Step 7: Verify duplicate-free rerun**

Run the same command again:

```bash
python -m istudy_backup trial
```

Expected: no media transfer and no new YouTube upload. State remains unchanged except for harmless report timestamps if implemented.

- [ ] **Step 8: Independently inspect YouTube Studio**

Open the trial video's edit page in the dedicated Chrome window and visually confirm its visibility is Private. Do not rely solely on terminal output for this first outward-facing operation.

- [ ] **Step 9: Generate the trial report**

```bash
python -m istudy_backup report
```

Expected: `reports/latest.md` lists one `uploaded_private` trial item and no public or unlisted item.

---

### Task 11: Batch Execution and Final Reconciliation

**Files:**
- Runtime only unless a verified defect requires a focused source fix with a regression test.

**Interfaces:**
- Consumes: `trial_passed=true` state and the reviewed discovery manifest.
- Produces: sequential processing results for all remaining authorized non-DRM videos and a final reconciliation report.

- [ ] **Step 1: Confirm the trial gate**

Read `data/state.json` through the application, not by manually editing it. Confirm `trial_passed` is true and the trial record has a YouTube ID plus explicit Private readback.

- [ ] **Step 2: Start batch mode**

```bash
python -m istudy_backup run
```

Review the printed item count and enter exactly:

```text
RUN 115暑電子1-15
```

Expected: one item at a time; already completed trial item skipped.

- [ ] **Step 3: Handle only legitimate manual checkpoints**

If the process stops for login expiry, duplicate login, CAPTCHA, account-security confirmation, unavailable recording, protected media, insufficient disk space, or privacy readback failure, resolve only the stated condition and rerun the same command. Never edit state to pretend an item succeeded.

- [ ] **Step 4: Generate final report**

```bash
python -m istudy_backup report
```

Expected per course:

- discovered count equals the reviewed manifest count;
- every item is `uploaded_private`, `skipped_protected`, or `failed` with a reason;
- every `uploaded_private` item has a local validated file, YouTube ID, URL, and explicit Private readback;
- no local validated file was deleted.

- [ ] **Step 5: Run final checks and review**

```bash
python -m unittest discover -s tests -v
git status --short -- istudy-private-backup docs/superpowers/specs/2026-07-23-istudy-private-youtube-workflow-design.md docs/superpowers/plans/2026-07-23-istudy-private-youtube-workflow.md
```

Expected: tests pass; status shows only this workflow, its spec, and its plan. Do not stage or commit.
