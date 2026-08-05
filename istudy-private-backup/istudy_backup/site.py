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
