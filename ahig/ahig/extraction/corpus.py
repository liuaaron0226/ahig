"""已取得全文的讀取層：**驗過才交出去。**

萃取要的不是 manifest，是「這一篇的第 N 節寫了什麼」，外加**那個數字將來必須
一起帶著走的那些事**——它出自哪一條取得路徑、是哪一版、授權是什麼。把這些
分開存放，等於讓下游有機會只拿走數字。

## 為什麼讀之前要先驗

`_verify_committed_artifacts` 只在發佈路徑上觸發（第 496 輪查明），而萃取是純
讀取的一端：一筆取得之後未再改寫的紀錄，在萃取讀它的時候沒有任何東西看過它。
第 515 輪的演習又顯示，搬運若只翻譯了來源檔而沒動 sections 檔，TEI 路徑上
manifest 那側全部免疫。故這裡的規則是：**驗不過就不交，不是交出去再附註**。

## 兩件刻意不做的事

- **不推定版本。** manifest 沒有版本欄，版本是另外量出來的（`n489`、`n523`）。
  這裡把它留成 ``None``，由呼叫端明確填入；憑路徑猜「PMC 的大概是刊出版」正是
  這個 run 反覆抓到的那一型。
- **不修補節名。** 有 20 個節的標題是字面 ``Untitled``（解析器在找不到標題時
  寫入的預設值），其中 5 篇的首節就是它。``sections_titled`` 因此永遠不會匹配
  到它們——那是事實，不是要在這裡補掉的缺陷。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from ahig.search.fulltext import (
    FulltextError,
    _artifact_dir,
    _verify_committed_artifacts,
    private_root,
)

UNTITLED = "Untitled"


class CorpusError(Exception):
    """讀取層自己的錯誤。與 ``FulltextError`` 分開，因為呼叫端要分得出
    「這一篇有問題」與「取得層的契約有問題」。"""


@dataclass(frozen=True)
class Section:
    kind: str
    path: tuple[str, ...]
    title: str
    text: str
    start_offset: int
    end_offset: int

    @property
    def is_untitled(self) -> bool:
        """標題是解析器的預設值，不是文件裡真的有這個標題。"""
        return self.title.strip() in ("", UNTITLED)


@dataclass(frozen=True)
class AcquiredDocument:
    candidate_id: str
    route: str
    content: str
    sections: tuple[Section, ...]
    licence: object | None
    licence_provenance: dict | None
    source_host: str
    parser_version: str
    sections_sha256: str
    version: str | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.sections:
            raise CorpusError(f"{self.candidate_id}：sections 為空")


def _document_from(artifact_dir: Path, manifest: dict,
                   artifact: dict) -> AcquiredDocument:
    sections_path = artifact_dir / artifact["sectionsFile"]
    parsed = json.loads(sections_path.read_text(encoding="utf-8"))
    sections = tuple(
        Section(kind=s.get("kind", ""), path=tuple(s.get("path") or ()),
                title=s.get("title", ""), text=s.get("text", ""),
                start_offset=int(s["startOffset"]),
                end_offset=int(s["endOffset"]))
        for s in parsed.get("sections") or ())
    return AcquiredDocument(
        candidate_id=manifest["candidateId"],
        route=artifact.get("sourceType", ""),
        content=parsed.get("content", ""),
        sections=sections,
        licence=artifact.get("licence"),
        licence_provenance=artifact.get("licenceProvenance"),
        source_host=urlparse(artifact.get("sourceUrl") or "").netloc,
        parser_version=parsed.get("parserVersion", ""),
        sections_sha256=artifact.get("sectionsSha256", ""),
    )


def load_document(candidate_id: str) -> AcquiredDocument:
    """讀一篇。驗不過就丟 ``CorpusError``，不回半成品。"""
    artifact_dir = _artifact_dir(candidate_id)
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.exists():
        raise CorpusError(f"{candidate_id}：沒有 manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "acquired":
        raise CorpusError(f"{candidate_id}：status 為 {manifest.get('status')}，"
                          "不是 acquired")
    try:
        _verify_committed_artifacts(artifact_dir, manifest)
    except FulltextError as error:
        raise CorpusError(f"{candidate_id}：未通過取得層驗證——{error}") from error
    artifacts = manifest.get("artifacts") or []
    if len(artifacts) != 1:
        # 目前每一筆都恰有一個 artifact。若哪天不是，這裡要先有人決定
        # 「同一篇的兩份全文誰為準」，而不是讓讀取層默默挑第一個。
        raise CorpusError(f"{candidate_id}：artifacts 有 {len(artifacts)} 個，"
                          "而讀取層只處理恰好一個")
    return _document_from(artifact_dir, manifest, artifacts[0])


def iter_acquired() -> Iterator[tuple[str, AcquiredDocument | None, str]]:
    """走過私有根裡每一個 acquired，逐筆產出 ``(目錄名, 文件或 None, 錯誤)``。

    失敗的那些照樣產出，只是文件是 ``None``——呼叫端因此數得出「幾篇讀不了」。
    直接跳過會讓語料悄悄變小，而變小的語料看起來跟乾淨的語料一樣。
    """
    root = private_root() / "fulltext"
    for entry in sorted(root.iterdir()):
        manifest_path = entry / "manifest.json"
        if not entry.is_dir() or not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            yield entry.name, None, f"manifest 無法解析：{error}"
            continue
        if manifest.get("status") != "acquired":
            continue
        candidate_id = manifest.get("candidateId") or ""
        try:
            yield entry.name, load_document(candidate_id), ""
        except CorpusError as error:
            yield entry.name, None, str(error)


def sections_titled(document: AcquiredDocument, *wanted: str) -> tuple[Section, ...]:
    """依標題取節，大小寫與前後空白不計。

    永遠取不到那些標題是 ``Untitled`` 的節——解析器找不到標題時寫的就是這個字，
    而全語料有 20 節如此。要處理那些節得靠位置或內容，不是靠標題。
    """
    keys = {w.strip().lower() for w in wanted}
    return tuple(s for s in document.sections
                 if not s.is_untitled and s.title.strip().lower() in keys)
