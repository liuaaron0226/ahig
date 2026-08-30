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
    content_sha256: str = ""
    # sections 文件自報的型別。照抄而不寫死：橋用它擋「這不是 sections 文件」，
    # 而寫死等於讓那道檢查對本讀取層永遠成立。
    document_type: str = ""
    version: str | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.sections:
            raise CorpusError(f"{self.candidate_id}：sections 為空")

    def as_sections_document(self) -> dict:
        """還原成 ``inventory_draft`` 那一端收得下的形狀。

        兩個房間各自造了半條鏈：讀取層要私有根，橋不要。接起來的地方就是這裡。
        ``contentSha256`` 必須是 sections 文件自記的那一個——橋拿它當「被讀的是
        哪一份」的憑證，重算會得到「現在這份」的雜湊，那是另一件事。
        """
        return {
            "documentType": self.document_type,
            "contentSha256": self.content_sha256,
            "content": self.content,
            "parserVersion": self.parser_version,
            "sections": [{"kind": s.kind, "path": list(s.path), "title": s.title,
                          "text": s.text, "startOffset": s.start_offset,
                          "endOffset": s.end_offset} for s in self.sections],
        }


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
        content_sha256=parsed.get("contentSha256", ""),
        document_type=parsed.get("documentType", ""),
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


def _acquired_manifests() -> Iterator[tuple[str, dict | None, str]]:
    """走過私有根裡每一個 acquired，產出 ``(目錄名, manifest 或 None, 錯誤)``。

    ``iter_acquired`` 與 ``acquired_roster`` 共用這一段——⚠️ 兩份走訪遲早會分岔，
    而分岔之後「幾篇」這個問題就有兩個答案。
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
        yield entry.name, manifest, ""


def iter_acquired() -> Iterator[tuple[str, AcquiredDocument | None, str]]:
    """走過私有根裡每一個 acquired，逐筆產出 ``(目錄名, 文件或 None, 錯誤)``。

    失敗的那些照樣產出，只是文件是 ``None``——呼叫端因此數得出「幾篇讀不了」。
    直接跳過會讓語料悄悄變小，而變小的語料看起來跟乾淨的語料一樣。
    """
    for name, manifest, error in _acquired_manifests():
        if manifest is None:
            yield name, None, error
            continue
        try:
            yield name, load_document(manifest.get("candidateId") or ""), ""
        except CorpusError as error:
            yield name, None, str(error)


def acquired_roster() -> tuple[list[str], list[tuple[str, str]]]:
    """**這批到底有幾篇**：``(candidateId 名冊, 連名字都沒有的那些)``。

    🚨 這裡刻意**不**過濾讀不出來的那些。第 551 輪查明 ``run.py`` 的預設名冊
    做了相反的事——它走 ``iter_acquired`` 之後把 ``document is None`` 濾掉，
    **⚠️ 於是一筆驗不過的紀錄根本不會進入批次**：收據會顯示「嘗試 41、成功 41」，
    而磁碟上其實有 42 筆、其中一筆是壞的。

    **🚨 那正是 ``iter_acquired`` 這支函式存在要防的事**——
    ⚠️ 而濾掉它的那一行，就寫在一段說「讀不了的那些在這裡就要被看見」的說明底下。

    第二個回傳值是 **manifest 連 candidateId 都讀不出來** 的那些：
    🚫 它們沒有 id 可以進批次，故另外列出——⚠️ 混進名冊會變成一個假的 id。
    """
    ids: list[str] = []
    unnameable: list[tuple[str, str]] = []
    for name, manifest, error in _acquired_manifests():
        if manifest is None:
            unnameable.append((name, error))
            continue
        candidate_id = manifest.get("candidateId") or ""
        if candidate_id:
            ids.append(candidate_id)
        else:
            unnameable.append((name, "manifest 無 candidateId"))
    return ids, unnameable


def reading_request_for(candidate_id: str, contract: dict):
    """從私有根一路接到讀論文的請求：**讀 → 驗 → 交出請求。**

    在此之前這兩段接不起來：讀取層交出 ``AcquiredDocument``，橋收的是 dict，
    中間得有人手工拼一個。手工拼的那一步沒有任何東西在看，而它要拼的正是
    ``contentSha256``——清冊靠它綁住「被讀的是哪一份」。

    ``build_reading_request`` 目前把**整份 content** 放進請求。本語料的內容量為
    最小 12,526、中位 39,095、最大 348,621 字元（那一篇有 160 節）。這裡不改那個
    行為——要不要分段、怎麼分，會改變模型看到什麼，屬契約層的決定——但把數字
    寫在這裡，好讓「授權之後直接跑」不是在不知道規模的情況下說的。
    """
    from ahig.extraction.inventory_draft import build_reading_request

    document = load_document(candidate_id)
    if not document.content_sha256:
        raise CorpusError(f"{candidate_id}：sections 文件無 contentSha256，"
                          "無從指明被讀的是哪一份")
    return build_reading_request(document.as_sections_document(), contract,
                                 report=candidate_id)


def sections_titled(document: AcquiredDocument, *wanted: str) -> tuple[Section, ...]:
    """依標題取節，大小寫與前後空白不計。

    永遠取不到那些標題是 ``Untitled`` 的節——解析器找不到標題時寫的就是這個字，
    而全語料有 20 節如此。要處理那些節得靠位置或內容，不是靠標題。
    """
    keys = {w.strip().lower() for w in wanted}
    return tuple(s for s in document.sections
                 if not s.is_untitled and s.title.strip().lower() in keys)
