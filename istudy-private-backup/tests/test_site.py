import tempfile
import unittest
from pathlib import Path

from istudy_backup.browser import ChromeSession, classify_dialog, google_account_matches, istudy_login_is_valid
from istudy_backup.core import ManualActionRequired, Paths
from istudy_backup.site import Clickable, select_target_courses, select_video_candidates


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

    def test_youtube_blocking_dialog_requires_manual_action(self):
        class FakePage:
            def __init__(self, session):
                self.session = session
                self.url = ""
                self.body = ""

            def goto(self, url, wait_until):
                self.url = url
                if "myaccount.google.com" in url:
                    self.body = "Google Account expected@example.com Home"
                elif "video_main.php" in url:
                    self.body = "課程列表"
                elif "studio.youtube.com" in url:
                    self.session.dialogs.append("安全驗證")

            def locator(self, selector):
                return self

            def inner_text(self):
                return self.body

        class FakeSession(ChromeSession):
            def new_page(self):
                return FakePage(self)

        with tempfile.TemporaryDirectory() as tmp:
            session = FakeSession(Paths.from_root(Path(tmp)))
            with self.assertRaises(ManualActionRequired):
                session.verify_accounts("expected@example.com")


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


if __name__ == "__main__":
    unittest.main()
