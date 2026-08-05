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
        args = (
            [f"--disable-extensions-except={extension}", f"--load-extension={extension}"]
            if self.paths.extension_dir.is_dir()
            else []
        )
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.paths.profile_dir),
            channel="chrome",
            headless=False,
            accept_downloads=True,
            viewport={"width": 1440, "height": 1000},
            args=args,
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
        blocking = [message for message in self.dialogs if classify_dialog(message) == "blocking"]
        if blocking:
            raise ManualActionRequired("YouTube Studio requires manual attention: " + " | ".join(blocking))
        if "accounts.google.com" in page.url:
            raise ManualActionRequired("YouTube Studio requires manual sign-in")
