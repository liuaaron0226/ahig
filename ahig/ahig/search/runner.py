#!/usr/bin/env python3
"""依凍結 SearchContract 執行公開 metadata 搜尋。

這個模組刻意不處理全文：不呼叫 Unpaywall、PMC OA、Europe PMC fulltext，也不建立
NotebookLM。它只建立候選 metadata pool，並把每一個 request、raw response、
cursor/pageToken、逐來源計數與失敗狀態留在 ``AHIG_PRIVATE_ROOT`` 下。

CLI：
    python -m ahig.search.runner --only europe-pmc
    python -m ahig.search.runner --only europe-pmc --only clinicaltrials-gov
    python -m ahig.search.runner --redo --run-id b11-20260813
    python -m ahig.search.runner --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from ahig.bootstrap import configure_stdio, private_root
from ahig.contracts import freeze
from ahig.state import StateStore, atomic_write_bytes, atomic_write_json

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = (ROOT / "calibration" / "b11-carbohydrate"
                    / "search-contract.json")


class JsonTransport(Protocol):
    def get_json(self, *, url: str, params: dict,
                 headers: dict | None = None) -> dict: ...


class UrllibTransport:
    """標準函式庫 HTTP transport；不為幾行網路碼新增 requests/httpx 依賴。

    ``last_exchange`` 保留最近一次成功回應的原始 bytes 與 HTTP metadata。
    runner 先把它寫到磁碟，再使用解析後的 dict；因此「raw response retention」
    不是把 dict 重新 dump 後冒充原始回應。
    """

    def __init__(self, *, attempts: int = 4, timeout: int = 120,
                 base_delay: float = 1.0):
        self.attempts = attempts
        self.timeout = timeout
        self.base_delay = base_delay
        self.last_exchange: dict[str, Any] | None = None

    def get_json(self, *, url: str, params: dict,
                 headers: dict | None = None) -> dict:
        self.last_exchange = None
        query = urllib.parse.urlencode(params, doseq=True)
        full_url = url + ("&" if "?" in url else "?") + query
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "AHIG/0.2.1 metadata-calibration",
            **(headers or {}),
        }
        last: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                req = urllib.request.Request(full_url, headers=request_headers,
                                             method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw = response.read()
                    charset = response.headers.get_content_charset() or "utf-8"
                    self.last_exchange = {
                        "body": raw,
                        "status": getattr(response, "status", 200),
                        "headers": dict(response.headers.items()),
                        "finalUrl": response.geturl(),
                        "contentType": response.headers.get("Content-Type"),
                    }
                    return json.loads(raw.decode(charset))
            except urllib.error.HTTPError as exc:
                raw = exc.read()
                self.last_exchange = {
                    "body": raw,
                    "status": exc.code,
                    "headers": dict(exc.headers.items()) if exc.headers else {},
                    "finalUrl": exc.geturl(),
                    "contentType": (exc.headers.get("Content-Type")
                                    if exc.headers else None),
                }
                last = exc
                # 語法／認證等永久錯誤不得重試；429 與 5xx 才重試。
                if exc.code != 429 and not 500 <= exc.code < 600:
                    snippet = raw.decode("utf-8", errors="replace")[:300]
                    raise RuntimeError(
                        f"HTTP {exc.code} {_redacted_url(full_url)} — {snippet}") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last = exc
            if attempt < self.attempts:
                time.sleep(self.base_delay * (2 ** (attempt - 1)))
        raise RuntimeError(f"HTTP request failed after {self.attempts} attempts: {last}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_contract(path: Path) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("status") != "frozen":
        raise ValueError("SearchContract 必須 status=frozen")
    if not freeze.verify_frozen(contract, "contractHash"):
        raise ValueError("SearchContract hash 自我驗證失敗")
    return contract


def candidate_sources(contract: dict) -> dict[str, dict]:
    return {s["sourceId"]: s for s in contract["sources"]
            if s["generatesCandidateRecords"]}


def _query_artifact(source: dict) -> tuple[Path, str]:
    if len(source["queryArtifacts"]) != 1:
        raise ValueError(f"{source['sourceId']} 目前必須恰有一個 query artifact")
    artifact = source["queryArtifacts"][0]
    path = ROOT / artifact["path"]
    raw = path.read_bytes()
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != artifact["sha256"]:
        raise ValueError(f"query artifact hash 過期：{artifact['strategyId']}")
    return path, raw.decode("utf-8").strip()


def _json_artifact(source: dict) -> dict:
    path, text = _query_artifact(source)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"query artifact 不是合法 JSON：{path}") from exc


def _redacted_params(params: dict) -> dict:
    """Manifest 不保存 API key；email 也只記錄其環境變數來源。"""
    result = dict(params)
    if "api_key" in result:
        result["api_key"] = "<from OPENALEX_API_KEY>"
    if "email" in result:
        result["email"] = "<from AHIG_CONTACT_EMAIL>"
    if "mailto" in result:
        result["mailto"] = "<from AHIG_CONTACT_EMAIL>"
    return result


def _wire_params(params: dict) -> dict:
    """把 JSON 型別轉成 API wire 值；Python 的 True 不得送成字串 `True`。"""
    def convert(value: Any) -> Any:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            return [convert(v) for v in value]
        return value
    return {key: convert(value) for key, value in params.items()}


def _redacted_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    redacted = []
    for key, value in pairs:
        lower = key.lower()
        if lower in {"api_key", "apikey", "key", "token", "access_token"}:
            value = "<redacted>"
        elif lower in {"email", "mailto"}:
            value = "<from-environment>"
        redacted.append((key, value))
    query = urllib.parse.urlencode(redacted)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path,
                                    query, parts.fragment))


def _save_page(source_root: Path, index: int, payload: dict,
               transport: JsonTransport) -> tuple[str, dict]:
    """保存 response；真 transport 留原始 bytes，fake transport 留語意 JSON。"""
    exchange = getattr(transport, "last_exchange", None)
    if exchange and isinstance(exchange.get("body"), bytes):
        relative = Path("responses") / f"{index:06d}.raw"
        path = source_root / relative
        raw = exchange["body"]
        atomic_write_bytes(path, raw)
        meta = {
            "responseKind": "raw-http-body",
            "httpStatus": exchange.get("status"),
            "headers": exchange.get("headers", {}),
            "finalUrl": (_redacted_url(exchange["finalUrl"])
                         if exchange.get("finalUrl") else None),
            "contentType": exchange.get("contentType"),
            "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "byteCount": len(raw),
        }
    else:
        relative = Path("responses") / f"{index:06d}.json"
        atomic_write_json(source_root / relative, payload)
        raw = (source_root / relative).read_bytes()
        meta = {
            "responseKind": "semantic-json-test-double",
            "httpStatus": None,
            "headers": {},
            "finalUrl": None,
            "contentType": "application/json",
            "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "byteCount": len(raw),
        }
    return relative.as_posix(), meta


def _append_request(requests: list[dict], *, source_root: Path, url: str,
                    params: dict, response_path: str | None, requested_at: str,
                    response_meta: dict) -> None:
    requests.append({
        "sequence": len(requests) + 1,
        "method": "GET",
        "url": url,
        "params": _redacted_params(params),
        "requestedAt": requested_at,
        "responsePath": response_path,
        **response_meta,
    })
    atomic_write_json(source_root / "requests.json", requests)


def _request_json(*, transport: JsonTransport, source_root: Path,
                  requests: list[dict], url: str, params: dict,
                  page_index: int) -> dict:
    """送出一個 GET，成功與失敗的 HTTP exchange 都寫入稽核軌。"""
    requested_at = utc_now()
    wire = _wire_params(params)
    try:
        payload = transport.get_json(url=url, params=wire)
    except Exception:
        exchange = getattr(transport, "last_exchange", None)
        if exchange and isinstance(exchange.get("body"), bytes):
            response_path, response_meta = _save_page(
                source_root, page_index, {}, transport)
        else:
            response_path = None
            response_meta = {
                "responseKind": "no-http-response",
                "httpStatus": None,
                "headers": {},
                "finalUrl": None,
                "contentType": None,
                "sha256": None,
                "byteCount": 0,
            }
        _append_request(requests, source_root=source_root, url=url, params=wire,
                        response_path=response_path, requested_at=requested_at,
                        response_meta=response_meta)
        raise
    response_path, response_meta = _save_page(
        source_root, page_index, payload, transport)
    _append_request(requests, source_root=source_root, url=url, params=wire,
                    response_path=response_path, requested_at=requested_at,
                    response_meta=response_meta)
    return payload


def _base_source_result(source: dict) -> dict:
    return {
        "sourceId": source["sourceId"],
        "status": "pending",
        "startedAt": None,
        "finishedAt": None,
        "recordCount": 0,
        "pageCount": 0,
        "error": None,
    }


def _run_europe_pmc(source: dict, source_root: Path,
                    transport: JsonTransport) -> dict:
    _, query = _query_artifact(source)
    fixed = source.get("fixedParameters", {})
    cursor = str(fixed.get("cursorMark", "*"))
    seen: set[str] = set()
    records: list[dict] = []
    requests: list[dict] = []
    page = 0
    declared_total: int | None = None

    while True:
        if cursor in seen:
            raise RuntimeError(f"cursor loop detected: {cursor}")
        seen.add(cursor)
        params = {"query": query,
                  "format": fixed.get("format", "json"),
                  "resultType": fixed.get("resultType", "core"),
                  "pageSize": source["pagination"]["pageSize"],
                  "cursorMark": cursor}
        page += 1
        payload = _request_json(
            transport=transport, source_root=source_root, requests=requests,
            url=source["endpoint"], params=params, page_index=page)
        if declared_total is None and payload.get("hitCount") is not None:
            declared_total = int(payload["hitCount"])
        batch = payload.get("resultList", {}).get("result") or []
        records.extend(batch)
        next_cursor = payload.get("nextCursorMark")
        if not next_cursor or not batch:
            break
        cursor = str(next_cursor)

    if declared_total is not None and len(records) != declared_total:
        raise RuntimeError(
            f"Europe PMC pagination incomplete: retained {len(records)} of {declared_total}")
    atomic_write_json(source_root / "records.json", records)
    return {"recordCount": len(records), "pageCount": page,
            "declaredTotal": declared_total}


def _run_clinical_trials(source: dict, source_root: Path,
                         transport: JsonTransport) -> dict:
    artifact = _json_artifact(source)
    params_base = dict(artifact["params"])
    params_base["pageSize"] = source["pagination"]["pageSize"]
    token: str | None = None
    seen: set[str] = set()
    records: list[dict] = []
    requests: list[dict] = []
    page = 0
    declared_total: int | None = None

    while True:
        if token is not None:
            if token in seen:
                raise RuntimeError(f"pageToken loop detected: {token}")
            seen.add(token)
        params = dict(params_base)
        if token is not None:
            params["pageToken"] = token
        page += 1
        payload = _request_json(
            transport=transport, source_root=source_root, requests=requests,
            url=source["endpoint"], params=params, page_index=page)
        if declared_total is None and payload.get("totalCount") is not None:
            declared_total = int(payload["totalCount"])
        batch = payload.get("studies") or []
        records.extend(batch)
        token = payload.get("nextPageToken")
        if not token:
            break

    if declared_total is not None and len(records) != declared_total:
        raise RuntimeError(
            f"ClinicalTrials.gov pagination incomplete: retained {len(records)} "
            f"of {declared_total}")
    atomic_write_json(source_root / "records.json", records)
    return {"recordCount": len(records), "pageCount": page,
            "declaredTotal": declared_total}


def _run_openalex(source: dict, source_root: Path,
                   transport: JsonTransport) -> dict:
    # 有金鑰用金鑰；沒有則退回 OpenAlex 官方支援的無金鑰 polite pool
    # （mailto 參數）。兩者皆無才擋。存取模式記錄於來源結果。
    api_key = os.environ.get("OPENALEX_API_KEY")
    email = os.environ.get("AHIG_CONTACT_EMAIL")
    if not api_key and not email:
        raise PermissionError(
            "OpenAlex 需要 OPENALEX_API_KEY，或以 AHIG_CONTACT_EMAIL "
            "走無金鑰 polite pool 模式")
    artifact = _json_artifact(source)
    params_base = dict(artifact["params"])
    params_base["per_page"] = source["pagination"]["pageSize"]
    if api_key:
        params_base["api_key"] = api_key
    else:
        params_base["mailto"] = email
    cursor = str(params_base.get("cursor", "*"))
    seen: set[str] = set()
    records: list[dict] = []
    requests: list[dict] = []
    page = 0
    declared_total: int | None = None

    while True:
        if cursor in seen:
            raise RuntimeError(f"cursor loop detected: {cursor}")
        seen.add(cursor)
        params = dict(params_base, cursor=cursor)
        page += 1
        payload = _request_json(
            transport=transport, source_root=source_root, requests=requests,
            url=source["endpoint"], params=params, page_index=page)
        if declared_total is None and payload.get("meta", {}).get("count") is not None:
            declared_total = int(payload["meta"]["count"])
        batch = payload.get("results") or []
        records.extend(batch)
        next_cursor = payload.get("meta", {}).get("next_cursor")
        if not next_cursor or not batch:
            break
        cursor = str(next_cursor)

    if declared_total is not None and len(records) != declared_total:
        raise RuntimeError(
            f"OpenAlex pagination incomplete: retained {len(records)} of {declared_total}")
    atomic_write_json(source_root / "records.json", records)
    return {"recordCount": len(records), "pageCount": page,
            "declaredTotal": declared_total,
            "accessMode": "api-key" if api_key else "polite-pool-mailto"}


def _run_pubmed(source: dict, source_root: Path,
                 transport: JsonTransport) -> dict:
    email = os.environ.get("AHIG_CONTACT_EMAIL")
    if not email:
        raise PermissionError("AHIG_CONTACT_EMAIL is required for PubMed")
    _, query = _query_artifact(source)
    fixed = source.get("fixedParameters", {})
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    esearch_params = {
        "db": "pubmed", "term": query, "retmode": "json", "usehistory": "y",
        "retmax": 0, "tool": "ahig", "email": email,
    }
    requests: list[dict] = []
    initial = _request_json(
        transport=transport, source_root=source_root, requests=requests,
        url=base + "esearch.fcgi", params=esearch_params, page_index=1)
    result = initial.get("esearchresult", {})
    count = int(result.get("count", 0))
    query_key, webenv = result.get("querykey"), result.get("webenv")
    if count and (not query_key or not webenv):
        raise RuntimeError("PubMed usehistory response missing querykey/WebEnv")

    records: list[dict] = []
    page_size = source["pagination"]["pageSize"]
    page = 1
    for start in range(0, count, page_size):
        params = {
            "db": "pubmed", "query_key": query_key, "WebEnv": webenv,
            "retstart": start, "retmax": page_size, "retmode": "json",
            "tool": "ahig", "email": email,
        }
        page += 1
        payload = _request_json(
            transport=transport, source_root=source_root, requests=requests,
            url=base + "esummary.fcgi", params=params, page_index=page)
        summary = payload.get("result", {})
        for uid in summary.get("uids") or []:
            if str(uid) in summary:
                records.append(summary[str(uid)])

    if len(records) != count:
        raise RuntimeError(
            f"PubMed pagination incomplete: retained {len(records)} of {count}")
    atomic_write_json(source_root / "records.json", records)
    return {"recordCount": len(records), "pageCount": page,
            "declaredTotal": count}


RUNNERS = {
    "pubmed": _run_pubmed,
    "europe-pmc": _run_europe_pmc,
    "openalex": _run_openalex,
    "clinicaltrials-gov": _run_clinical_trials,
}


_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def _run_root(private: Path, contract: dict, run_id: str) -> Path:
    if not _SAFE_RUN_ID.fullmatch(run_id) or run_id in {".", ".."}:
        raise ValueError(
            "run-id 只能含英數、點、底線、連字號，長度 1–80，且不得是 . 或 ..")
    return (private / "search-runs" / contract["searchContractId"].split(":")[-1]
            / run_id)


def _source_status(run_root: Path, source_id: str) -> dict | None:
    path = run_root / "sources" / source_id / "status.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _status_for_run(sources: dict[str, dict]) -> str:
    statuses = [v["status"] for v in sources.values()]
    if statuses and all(s == "completed" for s in statuses):
        return "completed"
    attempted = [s for s in statuses if s != "not-run"]
    if attempted and all(s in {"blocked", "failed"} for s in attempted):
        return "failed"
    return "partial"


def run_search(contract_path: Path = DEFAULT_CONTRACT, *,
               only: list[str] | None = None, dry_run: bool = False,
               redo: bool = False, run_id: str | None = None,
               transport: JsonTransport | None = None) -> dict:
    contract_path = Path(contract_path).resolve()
    contract = load_contract(contract_path)
    available = candidate_sources(contract)
    selected = list(only or available.keys())
    unknown = [s for s in selected if s not in available]
    if unknown:
        all_ids = {s["sourceId"] for s in contract["sources"]}
        access_only = [s for s in unknown if s in all_ids]
        if access_only:
            raise ValueError(f"metadata runner 只接受 candidate sources：{access_only}")
        raise ValueError(f"未知 sourceId：{unknown}")

    if dry_run:
        return {
            "status": "dry-run",
            "searchContractHash": contract["contractHash"],
            "selectedSources": selected,
            "requirements": {
                sid: {
                    "AHIG_CONTACT_EMAIL": sid == "pubmed",
                    "OPENALEX_API_KEY": sid == "openalex",
                } for sid in selected
            },
        }

    private = private_root()
    rid = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = _run_root(private, contract, rid)
    run_root.mkdir(parents=True, exist_ok=True)
    state_store = StateStore(run_root / "state.json")
    state = state_store.load()
    existing_hash = state.get("searchContractHash")
    if existing_hash and existing_hash != contract["contractHash"]:
        raise ValueError(
            f"同一 run-id 已綁定不同 SearchContract：{existing_hash}；"
            f"現行 {contract['contractHash']}")
    state.update({"schema_version": 1, "runId": rid,
                  "searchContractHash": contract["contractHash"]})
    state.setdefault("sources", {})
    state_store.save(state)

    transport = transport or UrllibTransport()
    started_at = state.get("startedAt") or utc_now()
    state["startedAt"] = started_at
    state_store.save(state)
    # Manifest 是整個 run 的累積狀態，不是這次 --only 的暫時視圖。
    outputs: dict[str, dict] = {}
    for source_id, source in available.items():
        previous = _source_status(run_root, source_id)
        if previous:
            outputs[source_id] = previous
        else:
            not_run = _base_source_result(source)
            not_run["status"] = "not-run"
            outputs[source_id] = not_run

    for source_id in selected:
        source = available[source_id]
        previous = _source_status(run_root, source_id)
        if previous and previous.get("status") == "completed" and not redo:
            outputs[source_id] = previous
            continue

        source_root = run_root / "sources" / source_id
        if source_root.exists():
            # 無論是明確 redo 或失敗重試，舊 evidence 都先封存，不靜默覆蓋。
            attempts_root = run_root / "previous-attempts"
            attempts_root.mkdir(parents=True, exist_ok=True)
            suffix = (previous or {}).get("finishedAt") or utc_now()
            safe_suffix = re.sub(r"[^A-Za-z0-9._-]", "-", suffix)
            archive = attempts_root / f"{source_id}-{safe_suffix}"
            serial = 1
            while archive.exists():
                serial += 1
                archive = attempts_root / f"{source_id}-{safe_suffix}-{serial}"
            shutil.move(str(source_root), str(archive))
        source_root.mkdir(parents=True, exist_ok=True)
        status = _base_source_result(source)
        status["startedAt"] = utc_now()
        atomic_write_json(source_root / "status.json", status)

        try:
            counts = RUNNERS[source_id](source, source_root, transport)
            status.update(counts)
            status["status"] = "completed"
        except PermissionError as exc:
            status["status"] = "blocked"
            status["error"] = str(exc)
        except Exception as exc:                         # noqa: BLE001
            status["status"] = "failed"
            status["error"] = f"{type(exc).__name__}: {exc}"
        status["finishedAt"] = utc_now()
        atomic_write_json(source_root / "status.json", status)
        outputs[source_id] = status
        state["sources"][source_id] = status
        state_store.save(state)

    manifest = {
        "runId": rid,
        "status": _status_for_run(outputs),
        "searchContractId": contract["searchContractId"],
        "searchContractVersion": contract["version"],
        "searchContractHash": contract["contractHash"],
        "contractPath": contract_path.as_posix(),
        "startedAt": started_at,
        "finishedAt": utc_now(),
        "selectedSources": selected,
        "sources": outputs,
        "approvedClaimBlocked": True,
        "blockedReasons": list(contract["governance"]["unblockConditions"]),
    }
    atomic_write_json(run_root / "manifest.json", manifest)
    state.update({"status": manifest["status"], "finishedAt": manifest["finishedAt"]})
    state_store.save(state)
    return {**manifest, "runRoot": str(run_root.resolve())}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--only", action="append", help="可重複：pubmed/europe-pmc/openalex/clinicaltrials-gov")
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--redo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    result = run_search(args.contract, only=args.only, dry_run=args.dry_run,
                        redo=args.redo, run_id=args.run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"completed", "dry-run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
