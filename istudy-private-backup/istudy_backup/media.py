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
