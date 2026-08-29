#!/usr/bin/env python3
"""OA 全文取得與結構化解析（W4a）。"""

from __future__ import annotations

import contextlib
import hashlib
import http.client
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from ahig.bootstrap import private_root
from ahig.contracts.freeze import content_hash
from ahig.state import atomic_write_bytes, atomic_write_json

PARSER_VERSION = "ahig-fulltext/1.0.0"
_BLOCK_TAGS = {
    "p", "list", "list-item", "def-list", "def-item", "caption",
    "table-wrap", "table", "thead", "tbody", "tfoot", "tr", "th", "td",
    "disp-quote", "boxed-text", "statement", "fig", "label",
}
EUROPE_PMC_FULLTEXT_URL = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
)
EUROPE_PMC_SEARCH_URL = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
)
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
UNPAYWALL_URL = "https://api.unpaywall.org/v2/{doi}"


class FulltextError(ValueError):
    """全文來源或解析產物不符合 W4a 契約。"""


class TransportError(FulltextError):
    """網路傳輸在重試後仍失敗；不含契約／解析／identity 錯誤。"""


class BinaryTransport(Protocol):
    def get_bytes(self, *, url: str,
                  headers: dict | None = None) -> dict: ...


class UrllibBinaryTransport:
    """保留原始 bytes 的標準函式庫 transport。"""

    def __init__(self, *, attempts: int = 4, timeout: int = 120,
                 base_delay: float = 1.0):
        self.attempts = attempts
        self.timeout = timeout
        self.base_delay = base_delay

    def get_bytes(self, *, url: str,
                  headers: dict | None = None) -> dict:
        request = urllib.request.Request(url, headers=headers or {}, method="GET")
        last: Exception | None = None
        last_exchange: dict | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    return {
                        "body": raw,
                        "status": getattr(response, "status", 200),
                        "headers": dict(response.headers.items()),
                        "finalUrl": response.geturl(),
                        "contentType": response.headers.get("Content-Type"),
                    }
            except urllib.error.HTTPError as exc:
                raw = exc.read()
                last = exc
                last_exchange = {
                    "body": raw,
                    "status": exc.code,
                    "headers": dict(exc.headers.items()) if exc.headers else {},
                    "finalUrl": exc.geturl(),
                    "contentType": (exc.headers.get("Content-Type")
                                    if exc.headers else None),
                }
                if exc.code != 429 and not 500 <= exc.code < 600:
                    return last_exchange
            except (urllib.error.URLError, TimeoutError,
                    http.client.HTTPException, ConnectionError) as exc:
                last = exc
            if attempt < self.attempts:
                time.sleep(self.base_delay * (2 ** (attempt - 1)))
        if last_exchange is not None:
            return last_exchange
        raise TransportError(
            f"HTTP request failed after {self.attempts} attempts") from last


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _json_bytes(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _element_text(element: ET.Element) -> str:
    return _normalise_text("".join(element.itertext()))


def _own_text(element: ET.Element, *, nested_section_tag: str,
              excluded_tags: set[str] | None = None) -> str:
    parts: list[str] = []
    excluded = {"title", "head", nested_section_tag, *(excluded_tags or set())}

    def visit(node: ET.Element) -> None:
        if node.text:
            parts.append(node.text)
        for child in node:
            name = _local_name(child.tag)
            if name not in excluded:
                is_block = name in _BLOCK_TAGS
                if is_block:
                    parts.append(" ")
                visit(child)
                if is_block:
                    parts.append(" ")
            if child.tail:
                parts.append(child.tail)

    visit(element)
    return _normalise_text("".join(parts))


def _descendants_outside_nested_sections(element: ET.Element, *,
                                           wanted_tag: str,
                                           nested_section_tag: str):
    for child in element:
        name = _local_name(child.tag)
        if name == nested_section_tag:
            continue
        if name == wanted_tag:
            yield child
        else:
            yield from _descendants_outside_nested_sections(
                child, wanted_tag=wanted_tag,
                nested_section_tag=nested_section_tag)


def _with_offsets(sections: list[dict]) -> tuple[str, list[dict]]:
    content_parts: list[str] = []
    positioned: list[dict] = []
    cursor = 0
    for section in sections:
        if content_parts:
            content_parts.append("\n\n")
            cursor += 2
        text = section["text"]
        positioned.append({**section, "startOffset": cursor,
                           "endOffset": cursor + len(text)})
        content_parts.append(text)
        cursor += len(text)
    return "".join(content_parts), positioned


def _jats_licence(root: ET.Element) -> dict | None:
    licence = next((node for node in root.iter()
                    if _local_name(node.tag) == "license"), None)
    if licence is None:
        return None
    href = (licence.attrib.get("{http://www.w3.org/1999/xlink}href")
            or licence.attrib.get("href"))
    text = _element_text(licence) or None
    if not href and not text:
        return None
    return {"href": href, "text": text}


def parse_jats(raw: bytes) -> dict:
    """把 JATS XML 切成可錨定的段落，偏移以合併後 ``content`` 為準。"""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FulltextError(f"JATS XML 無法解析：{exc}") from exc
    if _local_name(root.tag) != "article":
        raise FulltextError("JATS article 根元素缺失")

    body = next((node for node in root.iter()
                 if _local_name(node.tag) == "body"), None)
    if body is None:
        raise FulltextError("JATS XML 缺少 body")

    sections: list[dict] = []

    def append_table(table: ET.Element, parent_path: list[str], index: int) -> None:
        label_node = next((child for child in table
                           if _local_name(child.tag) == "label"), None)
        table_title = (_element_text(label_node) if label_node is not None
                       else f"Table {index}")
        table_text = _own_text(table, nested_section_tag="__none__")
        if table_text:
            sections.append({"kind": "table",
                             "path": [*parent_path, table_title],
                             "title": table_title, "text": table_text})

    def visit(sec: ET.Element, parent_path: list[str]) -> None:
        title_node = next((child for child in sec
                           if _local_name(child.tag) == "title"), None)
        title = _element_text(title_node) if title_node is not None else "Untitled"
        path = [*parent_path, title]
        text = _own_text(sec, nested_section_tag="sec",
                         excluded_tags={"table-wrap"})
        if text:
            sections.append({"kind": "section", "path": path,
                             "title": title, "text": text})
        for index, table in enumerate(_descendants_outside_nested_sections(
                sec, wanted_tag="table-wrap", nested_section_tag="sec"), 1):
            append_table(table, path, index)
        for child in sec:
            if _local_name(child.tag) == "sec":
                visit(child, path)

    pending_body: list[str] = []
    body_chunk = 0

    def flush_body() -> None:
        nonlocal body_chunk
        text = _normalise_text(" ".join(pending_body))
        pending_body.clear()
        if not text:
            return
        body_chunk += 1
        title = "Body" if body_chunk == 1 else f"Body {body_chunk}"
        sections.append({"kind": "section", "path": [title],
                         "title": title, "text": text})

    if body.text and body.text.strip():
        pending_body.append(body.text)
    body_table_index = 0
    for child in body:
        name = _local_name(child.tag)
        if name == "sec":
            flush_body()
            visit(child, [])
        elif name == "table-wrap":
            flush_body()
            body_table_index += 1
            append_table(child, ["Body"], body_table_index)
        else:
            text = _own_text(child, nested_section_tag="sec",
                             excluded_tags={"table-wrap"})
            if text:
                pending_body.append(text)
            for table in _descendants_outside_nested_sections(
                    child, wanted_tag="table-wrap", nested_section_tag="sec"):
                flush_body()
                body_table_index += 1
                append_table(table, ["Body"], body_table_index)
        if child.tail and child.tail.strip():
            pending_body.append(child.tail)
    flush_body()
    if not sections:
        raise FulltextError("JATS body 沒有可解析文字")

    content, positioned = _with_offsets(sections)
    return {
        "documentType": "fulltext-sections",
        "sourceType": "jats-xml",
        "parserVersion": PARSER_VERSION,
        "sourceSha256": _sha256(raw),
        "contentSha256": _sha256(content.encode("utf-8")),
        "licence": _jats_licence(root),
        "content": content,
        "sections": positioned,
    }


def parse_tei(raw: bytes) -> dict:
    """把 GROBID TEI 切成與 JATS 相同的節名與字元偏移契約。"""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FulltextError(f"TEI XML 無法解析：{exc}") from exc
    namespace = (root.tag[1:].split("}", 1)[0]
                 if root.tag.startswith("{") else None)
    if _local_name(root.tag) != "TEI" or namespace != "http://www.tei-c.org/ns/1.0":
        raise FulltextError("TEI root 或 namespace 不符")
    # producer 只認 teiHeader/encodingDesc/appInfo/application 這條正規路徑，
    # 且 ident 必須恰好是 GROBID——「任意位置、ident 含 grobid」會讓
    # not-grobid 與正文裡的假 metadata 通過。
    application = None
    for header in (node for node in root if _local_name(node.tag) == "teiHeader"):
        for encoding in (n for n in header if _local_name(n.tag) == "encodingDesc"):
            for app_info in (n for n in encoding if _local_name(n.tag) == "appInfo"):
                for node in (n for n in app_info
                             if _local_name(n.tag) == "application"):
                    if str(node.get("ident") or "").casefold() == "grobid":
                        application = node
                        break
    if application is None:
        raise FulltextError("TEI 缺 GROBID producer metadata")
    text_node = next((node for node in root.iter()
                      if _local_name(node.tag) == "text"), None)
    body = (next((node for node in text_node.iter()
                  if _local_name(node.tag) == "body"), None)
            if text_node is not None else None)
    if body is None:
        raise FulltextError("TEI 缺少 text/body")

    sections: list[dict] = []

    def visit(div: ET.Element, parent_path: list[str]) -> None:
        head = next((child for child in div
                     if _local_name(child.tag) == "head"), None)
        title = _element_text(head) if head is not None else "Untitled"
        path = [*parent_path, title]
        text = _own_text(div, nested_section_tag="div")
        if text:
            sections.append({"path": path, "title": title, "text": text})
        for child in div:
            if _local_name(child.tag) == "div":
                visit(child, path)

    for div in (child for child in body if _local_name(child.tag) == "div"):
        visit(div, [])
    if not sections:
        text = _element_text(body)
        if text:
            sections.append({"path": ["Body"], "title": "Body", "text": text})
    if not sections:
        raise FulltextError("TEI body 沒有可解析文字")

    content, positioned = _with_offsets(sections)
    return {
        "documentType": "fulltext-sections",
        "sourceType": "grobid-tei",
        "parserVersion": PARSER_VERSION,
        "sourceSha256": _sha256(raw),
        "contentSha256": _sha256(content.encode("utf-8")),
        "producer": {"ident": application.get("ident"),
                     "version": application.get("version")},
        "pdfLocatorReady": False,
        "locatorMode": "section-character-offset-only",
        "content": content,
        "sections": positioned,
    }


def _candidate_directory_name(candidate_id: str) -> str:
    digest = hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[:16]
    human = candidate_id.rsplit(":", 1)[-1]
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", human).strip("-.").lower()
    slug = (slug[:32].rstrip("-.") or "candidate")
    return f"{slug}-{digest}"


def _identifier(candidate: dict, key: str) -> str | None:
    raw = (candidate.get("identifiers") or {}).get(key)
    values = raw if isinstance(raw, list) else [raw]
    values = [str(value).strip() for value in values if value]
    if key == "pmcid":
        values = [value.upper() for value in values]
    unique = list(dict.fromkeys(values))
    if len(unique) > 1:
        raise FulltextError(f"{key} 有多個不同識別碼，拒絕自動綁定：{unique}")
    return unique[0] if unique else None


def _pmcid(candidate: dict) -> str | None:
    value = _identifier(candidate, "pmcid")
    if value is None:
        return None
    value = value.upper()
    if not re.fullmatch(r"PMC\d+", value):
        raise FulltextError(f"無效 PMCID：{value}")
    return value


def _pmid(candidate: dict) -> str | None:
    value = _identifier(candidate, "pmid")
    if value is not None and not re.fullmatch(r"\d+", value):
        raise FulltextError(f"無效 PMID：{value}")
    return value


def _doi(candidate: dict) -> str | None:
    value = _identifier(candidate, "doi")
    if value is None:
        return None
    value = value.lower().removeprefix("https://doi.org/").removeprefix("doi:")
    return value or None


def _require_private(path: Path) -> Path:
    root = private_root()
    resolved = path.expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise FulltextError(f"全文命令只能使用 AHIG_PRIVATE_ROOT 之下的路徑：{root}")
    return resolved


def _artifact_dir(candidate_id: str) -> Path:
    """候選 artifact 目錄；解析後強制仍落在私密根內（防 junction 逃逸）。"""
    path = private_root() / "fulltext" / _candidate_directory_name(candidate_id)
    if path.exists():
        return _require_private(path)
    return path


def _version_token(version: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "-", version).strip("-.")
    if not token:
        raise FulltextError("parserVersion 無法轉成安全檔名")
    return token


# 原始檔之副檔名依來源型別而定。n+123（五）裁定 PDF 路徑須同時記下
# 抓回的 PDF 與 GROBID 產出的 TEI，兩者都會經過本函式；副檔名若寫死成
# .jats.xml，產物名稱就會與內容不符（n+111 四已因標籤名實不符出過問題）。
_SOURCE_SUFFIX = {
    "jats": "jats.xml",
    "tei": "tei.xml",
    "pdf": "pdf",
}


def _artifact_files(source_sha256: str, parser_version: str,
                    sections_sha256: str,
                    source_kind: str = "jats") -> tuple[str, str]:
    if source_kind not in _SOURCE_SUFFIX:
        raise FulltextError(f"未知的來源型別：{source_kind}")
    source_token = source_sha256.removeprefix("sha256:")[:16]
    sections_token = sections_sha256.removeprefix("sha256:")[:16]
    raw_file = f"source-{source_token}.{_SOURCE_SUFFIX[source_kind]}"
    sections_file = (
        f"sections-v{_version_token(parser_version)}-"
        f"{source_token}-{sections_token}.json")
    return raw_file, sections_file


@contextlib.contextmanager
def _candidate_lock(artifact_dir: Path, *, timeout: float = 30.0,
                    poll: float = 0.01, stale_after: float = 300.0):
    """候選層級的跨行程互斥鎖。

    manifest-last 只保證單檔原子性；read → sweep → write 這串多檔交易若兩個
    寫入者交錯，會互刪 staged 檔或蓋掉對方的 binding。用 ``O_CREAT|O_EXCL``
    當鎖是因為它在 Windows 與 POSIX 上語意一致，且不需要新依賴。
    """
    artifact_dir.mkdir(parents=True, exist_ok=True)
    lock_path = artifact_dir / ".publish.lock"
    deadline = time.monotonic() + timeout
    handle = None
    heartbeat = threading.Event()
    while handle is None:
        try:
            handle = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # 持鎖行程被砍會留下 stale lock，沒有回收機制該候選就永久卡死。
            # 但直接 unlink 別人的鎖在 POSIX 上會成功（開啟中的檔案照刪），
            # 造成兩個持有者並存。改為先 os.replace 搬成唯一暫名：只有搬成功
            # 的那個等待者能回收，輸家會在下一輪看到鎖已消失而重試。
            try:
                age = time.time() - lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > stale_after:
                claim = lock_path.with_name(
                    f".publish.stale.{os.getpid()}.{id(heartbeat):x}")
                try:
                    os.replace(lock_path, claim)
                except (FileNotFoundError, PermissionError, OSError):
                    pass                      # 別人先回收或平台不允許，重試
                else:
                    claim.unlink(missing_ok=True)
                continue
            if time.monotonic() >= deadline:
                raise FulltextError(
                    f"取得候選發佈鎖逾時：{artifact_dir.name}") from None
            time.sleep(poll)

    def keep_alive() -> None:
        # 合法但耗時的交易不該被判成 stale，所以持鎖期間持續續期。
        while not heartbeat.wait(stale_after / 3):
            try:
                os.utime(lock_path, None)
            except OSError:
                return

    ticker = threading.Thread(target=keep_alive, daemon=True)
    ticker.start()
    try:
        yield
    finally:
        heartbeat.set()
        os.close(handle)
        lock_path.unlink(missing_ok=True)


def _write_committed_manifest(artifact_dir: Path, manifest: dict) -> tuple[str, str]:
    """先保存 immutable generation，最後原子更新 latest manifest。"""
    artifact_dir = _require_private(artifact_dir)
    raw = _json_bytes(manifest)
    manifest_sha256 = _sha256(raw)
    token = manifest_sha256.removeprefix("sha256:")[:16]
    generation = artifact_dir / "manifests" / f"manifest-{token}.json"
    if generation.exists() and generation.read_bytes() != raw:
        raise FulltextError("content-addressed manifest generation 內容不符")
    if not generation.exists():
        atomic_write_bytes(generation, raw)
    atomic_write_json(artifact_dir / "manifest.json", manifest)
    relative = generation.relative_to(private_root()).as_posix()
    return relative, manifest_sha256


def _merge_binding(manifest: dict | None, binding: dict | None) -> list[dict]:
    bindings = list((manifest or {}).get("bindings") or [])
    if binding is not None and binding not in bindings:
        bindings.append(dict(binding))
    return bindings


def _manifest_references(manifest: dict) -> set[str]:
    references: set[str] = set()
    for artifact in manifest.get("artifacts") or []:
        for key in ("rawFile", "sectionsFile"):
            value = artifact.get(key)
            if isinstance(value, str):
                references.add(value)
    for key in ("rawFile", "sectionsFile"):
        value = manifest.get(key)
        if isinstance(value, str):
            references.add(value)
    return references


def _validate_latest_manifest(artifact_dir: Path, manifest: dict) -> None:
    if manifest.get("documentType") != "fulltext-acquisition-manifest":
        raise FulltextError("manifest documentType 不符")
    candidate_id = manifest.get("candidateId")
    if not (isinstance(candidate_id, str) and candidate_id):
        raise FulltextError("manifest 缺 candidateId")
    if _candidate_directory_name(candidate_id) != artifact_dir.name:
        raise FulltextError("manifest candidateId 與 artifact 目錄不符")
    status = manifest.get("status")
    if status not in {"acquired", "available-pdf", "available-landing-page",
                      "no-oa-fulltext", "incomplete", "error"}:
        raise FulltextError("manifest status 不合法")
    if not isinstance(manifest.get("attempts"), list):
        raise FulltextError("manifest attempts 必須是陣列")
    if status == "acquired":
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise FulltextError("acquired manifest 缺 artifacts")
        required = {"rawFile", "sectionsFile", "sourceSha256",
                    "sectionsSha256", "parserVersion", "pmcid", "sourceUrl"}
        if any(not required <= set(item) for item in artifacts
               if isinstance(item, dict)):
            raise FulltextError("artifact 必填欄位不完整")
        if any(not isinstance(item, dict) for item in artifacts):
            raise FulltextError("artifact 必須是物件")
    # 這裡刻意只做結構驗證，不驗 artifact 內容 hash。掃除是回復工具，
    # 若拿 hash 不符當「manifest 無效」，一個被竄改的 sections 就會讓
    # 整份證據（含 immutable generation）被當垃圾清掉——那正是要防的失證。
    # 內容完整性交由 _verify_committed_artifacts 在發佈路徑上 fail-closed。


def _quarantine_invalid_manifest(artifact_dir: Path, raw: bytes) -> None:
    token = _sha256(raw).removeprefix("sha256:")[:16]
    target = artifact_dir / "invalid-manifests" / f"manifest-{token}.json"
    if not target.exists():
        atomic_write_bytes(target, raw)
    (artifact_dir / "manifest.json").unlink(missing_ok=True)


def sweep_orphans(artifact_dir: Path) -> list[str]:
    """清除沒有被有效 manifest 引用的 manifest-last 殘檔。

    對外入口一律持候選鎖：掃除與發佈是同一份多檔交易的兩端，不持鎖會刪掉
    另一個寫入者正在 staging 的檔案。
    """
    artifact_dir = _require_private(artifact_dir)
    with _candidate_lock(artifact_dir):
        return _sweep_orphans_locked(artifact_dir)


def _sweep_orphans_locked(artifact_dir: Path) -> list[str]:
    manifest_path = artifact_dir / "manifest.json"
    references: set[str] = set()
    if manifest_path.exists():
        raw = manifest_path.read_bytes()
        try:
            manifest = json.loads(raw)
            _validate_latest_manifest(artifact_dir, manifest)
        except (json.JSONDecodeError, FulltextError):
            _quarantine_invalid_manifest(artifact_dir, raw)
        else:
            references = _manifest_references(manifest)
    removed: list[str] = []
    # 鎖檔與隔離目錄不是 artifact，掃除不得動它們。
    for pattern in ("source-*.jats.xml", "sections-v*.json"):
        for path in sorted(artifact_dir.glob(pattern)):
            if path.name not in references:
                path.unlink()
                removed.append(path.name)
    # immutable generation 一律保留，即使 latest manifest 無效。它們是
    # content-addressed（檔名即內容雜湊）故能自證，且舊 batch 以
    # manifestPath＋manifestSha256 直接引用；跟著壞掉的指標一起刪，
    # 等於讓回復工具製造出它要防的失證。
    return removed


def _verify_committed_artifacts(artifact_dir: Path, manifest: dict) -> None:
    for artifact in manifest.get("artifacts") or []:
        raw_path = artifact_dir / artifact["rawFile"]
        sections_path = artifact_dir / artifact["sectionsFile"]
        if not raw_path.exists() or not sections_path.exists():
            raise FulltextError("已提交 artifact 缺 raw 或 sections")
        if _sha256(raw_path.read_bytes()) != artifact.get("sourceSha256"):
            raise FulltextError("已提交 artifact 的 raw sha256 不符")
        if _sha256(sections_path.read_bytes()) != artifact.get("sectionsSha256"):
            raise FulltextError("已提交 artifact 的 sectionsSha256 不符")


def _publish_jats(candidate: dict, *, raw: bytes, exchange: dict,
                  pmcid: str, source_url: str,
                  attempts: list[dict] | None = None,
                  binding: dict | None = None) -> dict:
    candidate_id = candidate["candidateId"]
    artifact_dir = _artifact_dir(candidate_id)
    with _candidate_lock(artifact_dir):
        return _publish_jats_locked(
            candidate, raw=raw, exchange=exchange, pmcid=pmcid,
            source_url=source_url, attempts=attempts, binding=binding)


def _publish_jats_locked(candidate: dict, *, raw: bytes, exchange: dict,
                         pmcid: str, source_url: str,
                         attempts: list[dict] | None = None,
                         binding: dict | None = None) -> dict:
    candidate_id = candidate["candidateId"]
    artifact_dir = _artifact_dir(candidate_id)
    manifest_path = artifact_dir / "manifest.json"
    existing: dict | None = None
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise FulltextError(f"既有 manifest 無法解析：{candidate_id}") from exc
        if existing.get("candidateId") != candidate_id:
            raise FulltextError("既有 manifest candidateId 與請求不符")
        _verify_committed_artifacts(artifact_dir, existing)
    _sweep_orphans_locked(artifact_dir)      # 已在鎖內，不可重入取鎖

    source_sha256 = _sha256(raw)
    if existing and existing.get("status") == "acquired":
        matching = [item for item in existing.get("artifacts") or []
                    if item.get("sourceSha256") == source_sha256]
        if not matching:
            raise FulltextError(
                f"既有原始全文與本次回應不同，拒絕覆寫：{candidate_id}")
        for item in matching:
            if item.get("pmcid") != pmcid:
                raise FulltextError("reuse 的 PMCID 與已提交 artifact 不符")
            if item.get("sourceUrl") != source_url:
                raise FulltextError("reuse 的 source URL 與已提交 artifact 不符")
        current = next((item for item in matching
                        if item.get("parserVersion") == PARSER_VERSION), None)
        if current is not None:
            bindings = _merge_binding(existing, binding)
            if bindings != list(existing.get("bindings") or []):
                existing["bindings"] = bindings
                _write_committed_manifest(artifact_dir, existing)
            return existing

    sections = parse_jats(raw)
    sections_raw = _json_bytes(sections)
    sections_sha256 = _sha256(sections_raw)
    raw_file, sections_file = _artifact_files(
        source_sha256, PARSER_VERSION, sections_sha256)
    source_path = artifact_dir / raw_file
    sections_path = artifact_dir / sections_file
    if source_path.exists() and source_path.read_bytes() != raw:
        raise FulltextError(f"content-addressed raw 檔內容不符：{candidate_id}")
    if sections_path.exists() and sections_path.read_bytes() != sections_raw:
        raise FulltextError(f"versioned sections 檔內容不符：{candidate_id}")
    if not source_path.exists():
        atomic_write_bytes(source_path, raw)
    if not sections_path.exists():
        atomic_write_bytes(sections_path, sections_raw)

    artifact = {
        "sourceType": "europe-pmc-jats",
        "sourceUrl": source_url,
        "finalUrl": exchange.get("finalUrl") or source_url,
        "pmcid": pmcid,
        "licence": sections.get("licence"),
        "sourceSha256": source_sha256,
        "sectionsSha256": sections_sha256,
        "contentLength": len(raw),
        "parserVersion": PARSER_VERSION,
        "rawFile": raw_file,
        "sectionsFile": sections_file,
    }
    artifacts = list((existing or {}).get("artifacts") or [])
    artifacts.append(artifact)
    manifest = {
        "documentType": "fulltext-acquisition-manifest",
        "candidateId": candidate_id,
        "pmcid": pmcid,
        "status": "acquired",
        "sourceType": artifact["sourceType"],
        "sourceUrl": artifact["sourceUrl"],
        "finalUrl": artifact["finalUrl"],
        "licence": artifact["licence"],
        "sha256": source_sha256,
        "sectionsSha256": sections_sha256,
        "contentLength": len(raw),
        "parserVersion": PARSER_VERSION,
        "rawFile": raw_file,
        "sectionsFile": sections_file,
        "artifacts": artifacts,
        "attempts": (list(attempts) if attempts is not None
                     else list((existing or {}).get("attempts") or [])),
        "bindings": _merge_binding(existing, binding),
    }
    _write_committed_manifest(artifact_dir, manifest)
    return manifest


def _attempt(source_id: str, attempted_at: str, *, url: str | None,
             http_status: int | None, conclusion: str, **extra) -> dict:
    return {"sourceId": source_id, "attemptedAt": attempted_at,
            "url": url, "httpStatus": http_status,
            "conclusion": conclusion, **extra}


def _json_document(exchange: dict, source_id: str) -> dict:
    body = exchange.get("body")
    if not isinstance(body, bytes):
        raise FulltextError(f"{source_id} 必須回傳 bytes body")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FulltextError(f"{source_id} 回應不是合法 UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise FulltextError(f"{source_id} JSON 根必須是物件")
    return document


def _status_conclusion(status: int) -> str:
    if status in {404, 410}:
        return "miss"
    return "transient-error" if status == 429 or status >= 500 else "error"


def _attempt_europe_pmc(candidate: dict, *, transport: BinaryTransport,
                        attempted_at: str,
                        binding: dict | None = None) -> tuple[dict, dict | None]:
    pmcid = _pmcid(candidate)
    pmid = _pmid(candidate)
    doi = _doi(candidate)
    if pmcid is None:
        if pmid:
            query_text = f"EXT_ID:{pmid} AND SRC:MED"
        elif doi:
            query_text = f'DOI:"{doi}"'
        else:
            return (_attempt("europe-pmc", attempted_at, url=None,
                             http_status=None, conclusion="not-applicable"), None)
        query = urllib.parse.urlencode({"query": query_text, "format": "json"})
        discovery_url = f"{EUROPE_PMC_SEARCH_URL}?{query}"
        lookup = transport.get_bytes(
            url=discovery_url,
            headers={"Accept": "application/json",
                     "User-Agent": "AHIG/0.2.1 fulltext-calibration"})
        status = int(lookup.get("status") or 0)
        if not 200 <= status < 300:
            return (_attempt("europe-pmc", attempted_at, url=discovery_url,
                             http_status=status,
                             conclusion=_status_conclusion(status)), None)
        payload = _json_document(lookup, "europe-pmc")
        results = ((payload.get("resultList") or {}).get("result") or [])
        result = results[0] if results else None
        discovered = result.get("pmcid") if isinstance(result, dict) else None
        if not discovered:
            return (_attempt("europe-pmc", attempted_at, url=discovery_url,
                             http_status=status, conclusion="miss"), None)
        pmcid = str(discovered).strip().upper()
        if not re.fullmatch(r"PMC\d+", pmcid):
            raise FulltextError(f"Europe PMC 回傳無效 PMCID：{pmcid}")

    source_url = EUROPE_PMC_FULLTEXT_URL.format(pmcid=pmcid)
    exchange = transport.get_bytes(
        url=source_url,
        headers={"Accept": "application/xml",
                 "User-Agent": "AHIG/0.2.1 fulltext-calibration"})
    status = int(exchange.get("status") or 0)
    if not 200 <= status < 300:
        return (_attempt("europe-pmc", attempted_at, url=source_url,
                         http_status=status,
                         conclusion=_status_conclusion(status)), None)
    raw = exchange.get("body")
    if not isinstance(raw, bytes):
        raise FulltextError("Europe PMC 全文必須回傳 bytes body")
    attempt = _attempt("europe-pmc", attempted_at, url=source_url,
                       http_status=status, conclusion="acquired-jats")
    manifest = _publish_jats(candidate, raw=raw, exchange=exchange,
                             pmcid=pmcid, source_url=source_url,
                             attempts=[attempt], binding=binding)
    return attempt, manifest


def _attempt_openalex(candidate: dict, *, transport: BinaryTransport,
                      attempted_at: str, contact_email: str | None) -> tuple[dict, dict | None]:
    doi = _doi(candidate)
    if doi is None:
        return (_attempt("openalex", attempted_at, url=None,
                         http_status=None, conclusion="not-applicable"), None)
    params = {"filter": f"doi:{doi}"}
    if contact_email:
        params["mailto"] = contact_email
    request_url = f"{OPENALEX_WORKS_URL}?{urllib.parse.urlencode(params)}"
    exchange = transport.get_bytes(
        url=request_url,
        headers={"Accept": "application/json",
                 "User-Agent": "AHIG/0.2.1 fulltext-calibration"})
    status = int(exchange.get("status") or 0)
    recorded_url = request_url.replace(urllib.parse.quote_plus(contact_email or ""),
                                       "<from AHIG_CONTACT_EMAIL>") if contact_email else request_url
    if not 200 <= status < 300:
        return (_attempt("openalex", attempted_at, url=recorded_url,
                         http_status=status,
                         conclusion=_status_conclusion(status)), None)
    payload = _json_document(exchange, "openalex")
    work = ((payload.get("results") or [None])[0]
            if "results" in payload else payload)
    location = (work or {}).get("best_oa_location") or {}
    pdf_url = location.get("pdf_url")
    available_url = pdf_url or location.get("landing_page_url")
    if not available_url:
        return (_attempt("openalex", attempted_at, url=recorded_url,
                         http_status=status, conclusion="miss"), None)
    conclusion = "available-pdf" if pdf_url else "available-landing-page"
    result = {"availableUrl": available_url,
              "licence": location.get("license"),
              "sourceType": "openalex-oa",
              "status": conclusion}
    return (_attempt("openalex", attempted_at, url=recorded_url,
                     http_status=status, conclusion=conclusion,
                     availableUrl=available_url), result)


def _attempt_unpaywall(candidate: dict, *, transport: BinaryTransport,
                       attempted_at: str, contact_email: str | None) -> tuple[dict, dict | None]:
    doi = _doi(candidate)
    if doi is None:
        return (_attempt("unpaywall", attempted_at, url=None,
                         http_status=None, conclusion="not-applicable"), None)
    if not contact_email:
        return (_attempt("unpaywall", attempted_at, url=None,
                         http_status=None, conclusion="blocked",
                         reason="missing-contact-email"), None)
    source_url = UNPAYWALL_URL.format(doi=urllib.parse.quote(doi, safe=""))
    request_url = f"{source_url}?{urllib.parse.urlencode({'email': contact_email})}"
    recorded_url = f"{source_url}?email=<from AHIG_CONTACT_EMAIL>"
    exchange = transport.get_bytes(
        url=request_url,
        headers={"Accept": "application/json",
                 "User-Agent": "AHIG/0.2.1 fulltext-calibration"})
    status = int(exchange.get("status") or 0)
    if not 200 <= status < 300:
        return (_attempt("unpaywall", attempted_at, url=recorded_url,
                         http_status=status,
                         conclusion=_status_conclusion(status)), None)
    payload = _json_document(exchange, "unpaywall")
    location = payload.get("best_oa_location") or {}
    pdf_url = location.get("url_for_pdf")
    available_url = pdf_url or location.get("url")
    if not payload.get("is_oa") or not available_url:
        return (_attempt("unpaywall", attempted_at, url=recorded_url,
                         http_status=status, conclusion="miss"), None)
    conclusion = "available-pdf" if pdf_url else "available-landing-page"
    result = {"availableUrl": available_url,
              "licence": location.get("license"),
              "sourceType": "unpaywall-oa",
              "status": conclusion}
    return (_attempt("unpaywall", attempted_at, url=recorded_url,
                     http_status=status, conclusion=conclusion,
                     availableUrl=available_url), result)


def _write_chain_manifest(candidate: dict, *, status: str,
                          attempts: list[dict], available: dict | None = None,
                          binding: dict | None = None) -> dict:
    artifact_dir = _artifact_dir(candidate["candidateId"])
    with _candidate_lock(artifact_dir):
        return _write_chain_manifest_locked(
            candidate, status=status, attempts=attempts,
            available=available, binding=binding)


def _write_chain_manifest_locked(candidate: dict, *, status: str,
                                 attempts: list[dict],
                                 available: dict | None = None,
                                 binding: dict | None = None) -> dict:
    artifact_dir = _artifact_dir(candidate["candidateId"])
    manifest_path = artifact_dir / "manifest.json"
    existing = None
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("candidateId") != candidate["candidateId"]:
            raise FulltextError("既有 manifest candidateId 與請求不符")
        if existing.get("status") == "acquired":
            _verify_committed_artifacts(artifact_dir, existing)
            return existing
    manifest = {
        "documentType": "fulltext-acquisition-manifest",
        "candidateId": candidate["candidateId"],
        "status": status,
        "attempts": attempts,
        "artifacts": list((existing or {}).get("artifacts") or []),
        "availableUrl": (available or {}).get("availableUrl"),
        "sourceType": (available or {}).get("sourceType"),
        "licence": (available or {}).get("licence"),
        "bindings": _merge_binding(existing, binding),
    }
    _write_committed_manifest(artifact_dir, manifest)
    return manifest


def acquire_fulltext(candidate: dict, *, transport: BinaryTransport,
                     contact_email: str | None = None,
                     now: Callable[[], str] = utc_now,
                     binding: dict | None = None) -> dict:
    """依 Europe PMC → OpenAlex → Unpaywall 順序解析 OA 可得性。"""
    candidate_id = candidate.get("candidateId")
    if not (isinstance(candidate_id, str) and candidate_id.strip()):
        raise FulltextError("candidateId 必須是非空字串")
    cached: dict | None = None
    cached_path = _artifact_dir(candidate_id) / "manifest.json"
    if cached_path.exists():
        cached = json.loads(cached_path.read_text(encoding="utf-8"))
        if cached.get("candidateId") != candidate_id:
            raise FulltextError("既有 manifest candidateId 與請求不符")
        if cached.get("status") == "acquired":
            _verify_committed_artifacts(cached_path.parent, cached)
            if cached.get("pmcid") != _pmcid(candidate):
                raise FulltextError("reuse 的 PMCID 與請求紀錄不符")
    attempts: list[dict] = []
    try:
        epmc_attempt, acquired = _attempt_europe_pmc(
            candidate, transport=transport, attempted_at=now(),
            binding=binding)
    except TransportError:
        epmc_attempt = _attempt("europe-pmc", now(), url=None,
                                http_status=None, conclusion="transient-error",
                                reason="transport-error")
        acquired = None
    attempts.append(epmc_attempt)
    if acquired is not None:
        return acquired
    if cached is not None and cached.get("status") == "acquired":
        # 追加本 run 的 binding 也是對同一份 manifest 的多檔交易，必須持鎖，
        # 否則可能與另一行程的 sweep／publish 交錯。
        with _candidate_lock(cached_path.parent):
            # 取鎖前那次驗證是鎖外看到的舊狀態；鎖內必須對重讀的內容再驗
            # 一次，否則兩次讀之間被換掉的 manifest 會被當成有效證據回傳。
            current = json.loads(cached_path.read_text(encoding="utf-8"))
            if current.get("candidateId") != candidate_id:
                raise FulltextError("既有 manifest candidateId 與請求不符")
            if current.get("status") != "acquired":
                raise FulltextError("既有 acquired manifest 在鎖內已變更狀態")
            if current.get("pmcid") != _pmcid(candidate):
                raise FulltextError("reuse 的 PMCID 與請求紀錄不符")
            _verify_committed_artifacts(cached_path.parent, current)
            bindings = _merge_binding(current, binding)
            if bindings != list(current.get("bindings") or []):
                current["bindings"] = bindings
                _write_committed_manifest(cached_path.parent, current)
            cached = current
        return cached

    try:
        openalex_attempt, available = _attempt_openalex(
            candidate, transport=transport, attempted_at=now(),
            contact_email=contact_email)
    except TransportError:
        openalex_attempt = _attempt("openalex", now(), url=None,
                                    http_status=None, conclusion="transient-error",
                                    reason="transport-error")
        available = None
    attempts.append(openalex_attempt)
    if available is not None:
        return _write_chain_manifest(
            candidate, status=available.get("status", "available-pdf"),
            attempts=attempts, available=available, binding=binding)

    try:
        unpaywall_attempt, available = _attempt_unpaywall(
            candidate, transport=transport, attempted_at=now(),
            contact_email=contact_email)
    except TransportError:
        unpaywall_attempt = _attempt("unpaywall", now(), url=None,
                                     http_status=None, conclusion="transient-error",
                                     reason="transport-error")
        available = None
    attempts.append(unpaywall_attempt)
    if available is not None:
        return _write_chain_manifest(
            candidate, status=available.get("status", "available-pdf"),
            attempts=attempts, available=available, binding=binding)
    # 只有三個來源都「實際查過且沒有」才是終局；not-applicable（缺識別碼）
    # 與 blocked 都代表沒查成，宣稱 no-oa-fulltext 會過度宣稱證據。
    terminal = all(item["conclusion"] == "miss" for item in attempts)
    return _write_chain_manifest(
        candidate, status="no-oa-fulltext" if terminal else "incomplete",
        attempts=attempts, binding=binding)


def acquire_from_run_root(run_root: Path, candidate_ids: Sequence[str], *,
                          transport: BinaryTransport,
                          contact_email: str | None = None,
                          now: Callable[[], str] = utc_now) -> dict:
    """從凍結候選池批次執行 OA 來源鏈，並產生 run-scoped manifest。"""
    run_root = _require_private(run_root)
    pool_root = run_root / "candidate-pool"
    pool_path = pool_root / "candidates.json"
    pool_manifest_path = pool_root / "manifest.json"
    if not pool_path.exists() or not pool_manifest_path.exists():
        raise FulltextError("找不到 candidate-pool candidates.json／manifest.json")
    candidates_raw = pool_path.read_bytes()
    pool_manifest = json.loads(pool_manifest_path.read_text(encoding="utf-8"))
    run_id = pool_manifest.get("runId")
    if not (isinstance(run_id, str) and run_id):
        raise FulltextError("candidate-pool manifest 缺 runId")
    candidate_pool_hash = _sha256(candidates_raw)
    records = {
        item["candidateId"]: item
        for item in json.loads(candidates_raw)
    }
    unique_ids = list(dict.fromkeys(candidate_ids))
    missing = [candidate_id for candidate_id in unique_ids
               if candidate_id not in records]
    if missing:
        raise FulltextError(f"候選池缺少 ID：{missing[:3]}")

    started_at = now()
    results: list[dict] = []
    batch_results: list[dict] = []
    for candidate_id in unique_ids:
        candidate = records[candidate_id]
        binding = {
            "runId": run_id,
            "candidatePoolHash": candidate_pool_hash,
            "candidateRecordHash": content_hash(candidate),
        }
        try:
            result = acquire_fulltext(
                candidate, transport=transport, contact_email=contact_email,
                now=now, binding=binding)
        except TransportError:
            result = _write_chain_manifest(
                candidate, status="error", binding=binding,
                attempts=[_attempt("batch", now(), url=None,
                                   http_status=None, conclusion="error",
                                   reason="transport-error")])
        results.append(result)
        artifact_dir = _artifact_dir(candidate_id)
        manifest_path = artifact_dir / "manifest.json"
        manifest_raw = manifest_path.read_bytes()
        manifest_sha256 = _sha256(manifest_raw)
        token = manifest_sha256.removeprefix("sha256:")[:16]
        generation = artifact_dir / "manifests" / f"manifest-{token}.json"
        if not generation.exists() or generation.read_bytes() != manifest_raw:
            raise FulltextError("batch 找不到相符的 immutable manifest generation")
        batch_results.append({
            "candidateId": candidate_id,
            "status": result["status"],
            "manifestPath": generation.relative_to(private_root()).as_posix(),
            "manifestSha256": manifest_sha256,
        })

    finished_at = now()
    batch_seed = {"runId": run_id, "startedAt": started_at,
                  "candidateIds": unique_ids}
    batch_id = "fulltext-batch-" + content_hash(batch_seed).removeprefix(
        "sha256:")[:16]
    batch = {
        "documentType": "fulltext-acquisition-batch",
        "batchId": batch_id,
        "runId": run_id,
        "candidatePoolHash": candidate_pool_hash,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "candidateCount": len(results),
        "results": batch_results,
    }
    batch["batchHash"] = content_hash(batch)
    batch_relative = Path("fulltext-acquisition") / f"{batch_id}.json"
    batch_path = run_root / batch_relative
    # 目錄可能是指向私密根外的 junction；寫入前重新解析父目錄。
    batch_path.parent.mkdir(parents=True, exist_ok=True)
    _require_private(batch_path.parent)
    atomic_write_json(batch_path, batch)
    return {
        "candidateCount": len(results),
        "acquiredCount": sum(result["status"] == "acquired"
                             for result in results),
        "availablePdfCount": sum(result["status"] == "available-pdf"
                                 for result in results),
        "unavailableCount": sum(result["status"] == "no-oa-fulltext"
                                for result in results),
        "incompleteCount": sum(result["status"] in {"incomplete", "error"}
                               for result in results),
        "batchManifest": batch_relative.as_posix(),
        "results": results,
    }
