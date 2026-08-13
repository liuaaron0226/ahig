#!/usr/bin/env python3
"""凍結 B.11 SearchContract，並重新綁定下游 ScopeContract 與 strata。

SearchContract 是契約鏈的根：query artifact 改一個字元，SearchContract hash 會變；
ScopeContract 必須重新凍結；strata 必須改釘新的 ScopeContract hash。三份產物要嘛
一起寫出，要嘛一份都不寫，避免中途留下合法但互相不一致的契約。

用法：
    python calibration/b11-carbohydrate/freeze_search_contract.py --dry-run
    python calibration/b11-carbohydrate/freeze_search_contract.py
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator          # noqa: E402

from ahig.bootstrap import configure_stdio           # noqa: E402
from ahig.contracts import freeze                    # noqa: E402
from ahig.scope import matcher as sm                 # noqa: E402
from ahig.state import atomic_write_json             # noqa: E402

HERE = Path(__file__).resolve().parent
SEARCH_DRAFT = HERE / "search-contract.draft.json"
SEARCH_OUT = HERE / "search-contract.json"
SCOPE_DRAFT = HERE / "scope-contract.draft.json"
SCOPE_OUT = HERE / "scope-contract.json"
STRATA_PATH = HERE / "strata.json"
SEARCH_SCHEMA = ROOT / "schema" / "search-contract-version.schema.json"
SCOPE_SCHEMA = ROOT / "schema" / "extraction-scope-contract.schema.json"
DEFAULT_FROZEN_AT = "2026-08-13T00:00:00Z"


def _validate(doc: dict, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(doc),
                    key=lambda e: list(e.path))
    if errors:
        detail = "\n".join(f"  - {list(e.path)}: {e.message[:240]}"
                           for e in errors[:10])
        raise ValueError(f"{label} 未通過 schema：\n{detail}")


def _verify_query_artifacts(search: dict) -> None:
    seen: set[str] = set()
    for source in search["sources"]:
        if source["sourceId"] in seen:
            raise ValueError(f"重複 sourceId：{source['sourceId']}")
        seen.add(source["sourceId"])
        if source["generatesCandidateRecords"] and not source["queryArtifacts"]:
            raise ValueError(f"{source['sourceId']} 會產生候選但沒有 query artifact")
        for artifact in source["queryArtifacts"]:
            path = ROOT / artifact["path"]
            if not path.is_file():
                raise ValueError(f"找不到 query artifact：{path}")
            raw = path.read_bytes()
            raw.decode("utf-8")
            if b"\r\n" in raw:
                raise ValueError(f"query artifact 必須使用 LF：{path}")
            actual = "sha256:" + hashlib.sha256(raw).hexdigest()
            if actual != artifact["sha256"]:
                raise ValueError(
                    f"query artifact hash 過期：{artifact['strategyId']} "
                    f"宣告 {artifact['sha256']}，實際 {actual}")


def build(frozen_at: str) -> tuple[dict, dict, dict]:
    search_draft = json.loads(SEARCH_DRAFT.read_text(encoding="utf-8"))
    _verify_query_artifacts(search_draft)
    search = freeze.freeze_document(search_draft, "contractHash",
                                    frozen_at=frozen_at)
    _validate(search, SEARCH_SCHEMA, "SearchContract")
    if not freeze.verify_frozen(search, "contractHash"):
        raise ValueError("SearchContract hash 自我驗證失敗")

    scope_draft = json.loads(SCOPE_DRAFT.read_text(encoding="utf-8"))
    scope_draft["derivedFromSearchContract"] = {
        "searchContractId": search["searchContractId"],
        "version": search["version"],
        "hash": search["contractHash"],
    }
    problems = freeze.freeze_preflight(scope_draft)
    if problems:
        raise ValueError(f"ScopeContract 凍結前置檢查未通過：{problems}")
    scope = freeze.freeze_document(scope_draft, "scopeContractHash",
                                   frozen_at=frozen_at)
    _validate(scope, SCOPE_SCHEMA, "ScopeContract")
    sm.ScopeMatcher(scope)
    if not freeze.verify_frozen(scope, "scopeContractHash"):
        raise ValueError("ScopeContract hash 自我驗證失敗")

    strata = json.loads(STRATA_PATH.read_text(encoding="utf-8"))
    strata["scopeContractHash"] = scope["scopeContractHash"]
    return search, scope, strata


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-at", default=DEFAULT_FROZEN_AT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        search, scope, strata = build(args.frozen_at)
    except Exception as exc:                           # noqa: BLE001
        print(f"凍結失敗：{exc}")
        return 1

    if args.dry_run:
        print("[dry-run] 契約鏈檢查通過")
    else:
        # 三份輸出各自原子寫入；所有驗證已在寫入前完成。
        atomic_write_json(SEARCH_OUT, search)
        atomic_write_json(SCOPE_OUT, scope)
        atomic_write_json(STRATA_PATH, strata)
        print("已寫出 SearchContract → ScopeContract → strata 契約鏈")

    print(f"  searchContractHash = {search['contractHash']}")
    print(f"  scopeContractHash  = {scope['scopeContractHash']}")
    print(f"  candidate sources  = {sum(s['generatesCandidateRecords'] for s in search['sources'])}")
    print(f"  query artifacts    = {sum(len(s['queryArtifacts']) for s in search['sources'])}")
    print(f"  Approved Claim blocked = {search['governance']['blocksApprovedClaims']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
