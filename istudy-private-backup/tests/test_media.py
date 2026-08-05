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
