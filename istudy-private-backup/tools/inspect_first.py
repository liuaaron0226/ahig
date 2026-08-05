from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from istudy_backup.browser import ChromeSession, ISTUDY_HOME, istudy_login_is_valid, page_media_usage
from istudy_backup.core import Paths, normalize_course_name
from istudy_backup.site import collect_clickables, select_video_candidates

TARGET_COURSE = "115暑電子1"
LOGIN_TIMEOUT_SECONDS = 15 * 60


def safe_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def wait_for_login(page) -> None:
    deadline = time.monotonic() + LOGIN_TIMEOUT_SECONDS
    announced = False
    while time.monotonic() < deadline:
        body = page.locator("body").inner_text() if page.locator("body").count() else ""
        if istudy_login_is_valid(page.url, body) and "video_main.php" in page.url:
            return
        if not announced:
            print("LOGIN_REQUIRED: 請在剛開啟的專用 Chrome 視窗完成 iStudy 登入。", flush=True)
            announced = True
        page.wait_for_timeout(2000)
        if "istudy.way-to-win.com" not in page.url:
            continue
        if "index_login.php" not in page.url:
            page.goto(ISTUDY_HOME, wait_until="domcontentloaded")
    raise TimeoutError("Timed out waiting for iStudy login")


def click_course(page) -> None:
    for frame in page.frames:
        locator = frame.get_by_text(TARGET_COURSE, exact=True)
        if locator.count() == 1:
            locator.click()
            page.wait_for_timeout(1500)
            return
    items = collect_clickables(page)
    matches = [item for item in items if normalize_course_name(item.text) == TARGET_COURSE]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {TARGET_COURSE} entry, found {len(matches)}")
    item = matches[0]
    if item.href:
        page.goto(urljoin(page.url, item.href), wait_until="domcontentloaded")
        return
    raise RuntimeError(f"{TARGET_COURSE} has no unambiguous link")


def open_first_video(page):
    items = collect_clickables(page)
    candidates = select_video_candidates(items)
    if not candidates:
        raise RuntimeError("No video candidate found; see course-clickables.json")
    item = candidates[0]
    if item.href:
        page.goto(urljoin(page.url, item.href), wait_until="domcontentloaded")
    else:
        locator = page.get_by_text(item.text, exact=True)
        if locator.count() != 1:
            raise RuntimeError(f"First video target is ambiguous: {item.text}")
        locator.click()
    return item, items


def inspect_player(page, media_responses: list[dict[str, str]]) -> dict[str, object]:
    page.wait_for_timeout(12000)
    frames = []
    for frame in page.frames:
        try:
            state = frame.evaluate(
                """
                () => ({
                  url: location.href,
                  eme: Boolean(window.__ISTUDY_DRM_USED__),
                  mse: Boolean(window.__ISTUDY_MSE_USED__),
                  mpd: performance.getEntriesByType('resource')
                    .map(entry => entry.name)
                    .filter(url => url.toLowerCase().includes('.mpd')),
                  videos: Array.from(document.querySelectorAll('video')).map(video => ({
                    currentSrc: video.currentSrc || '',
                    src: video.getAttribute('src') || '',
                    readyState: video.readyState,
                    duration: Number.isFinite(video.duration) ? video.duration : null,
                    mediaKeys: Boolean(video.mediaKeys)
                  }))
                })
                """
            )
        except Exception as error:
            state = {"url": safe_url(frame.url), "error": type(error).__name__}
        if "url" in state:
            state["url"] = safe_url(state["url"])
        for video in state.get("videos", []):
            video["currentSrc"] = safe_url(video.get("currentSrc", ""))
            video["src"] = safe_url(video.get("src", ""))
        state["mpd"] = [safe_url(url) for url in state.get("mpd", [])]
        frames.append(state)

    protected = any(
        frame.get("eme")
        or frame.get("mpd")
        or any(video.get("mediaKeys") for video in frame.get("videos", []))
        for frame in frames
    ) or "eme" in page_media_usage(page)
    kinds = {response["kind"] for response in media_responses}
    if protected or "dash" in kinds:
        classification = "protected_or_drm"
    elif "hls" in kinds:
        classification = "hls"
    elif "mp4" in kinds or any(video.get("currentSrc", "").lower().endswith(".mp4") for frame in frames for video in frame.get("videos", [])):
        classification = "mp4"
    else:
        classification = "unknown"
    return {
        "classification": classification,
        "page": safe_url(page.url),
        "frames": frames,
        "media_responses": media_responses,
        "page_media_usage": sorted(page_media_usage(page)),
    }


def main() -> int:
    paths = Paths.from_root(ROOT)
    paths.ensure_runtime_dirs()
    output = paths.artifacts_dir / "first-video-inspection.json"
    clickables_output = paths.artifacts_dir / "course-clickables.json"

    with ChromeSession(paths) as session:
        page = session.new_page()
        media_responses: list[dict[str, str]] = []

        def on_response(response) -> None:
            url = response.url.lower()
            content_type = response.headers.get("content-type", "").lower()
            kind = None
            if ".mpd" in url or "dash+xml" in content_type:
                kind = "dash"
            elif ".m3u8" in url or "mpegurl" in content_type:
                kind = "hls"
            elif ".mp4" in url or content_type.startswith("video/mp4"):
                kind = "mp4"
            if kind:
                media_responses.append({"kind": kind, "url": safe_url(response.url), "content_type": content_type})

        page.on("response", on_response)
        page.goto(ISTUDY_HOME, wait_until="domcontentloaded")
        wait_for_login(page)
        print("LOGIN_OK", flush=True)
        click_course(page)
        item, items = open_first_video(page)
        clickables_output.write_text(
            json.dumps([item.__dict__ if hasattr(item, "__dict__") else {"text": item.text, "href": safe_url(item.href), "onclick": item.onclick, "tag": item.tag} for item in items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        result = inspect_player(page, media_responses)
        result["course"] = TARGET_COURSE
        result["video_title"] = item.text
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"classification": result["classification"], "video_title": item.text, "report": str(output)}, ensure_ascii=False), flush=True)
        page.wait_for_timeout(5000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
