#!/usr/bin/env python3
"""把 B.11 範圍契約草稿凍結成正式契約。

流程刻意分兩個檔案：``scope-contract.draft.json`` 是可編輯的來源，
``scope-contract.json`` 是產物。凍結時做三件事：

1. 跑 schema 驗證與確定性前置檢查（時窗重疊、劑量帶重疊、重複 ID）。
2. 補 ``frozenAt`` 與 ``status=frozen``。
3. 算出排除雜湊欄位自身的正規化雜湊並寫回。

任何一步失敗就整個中止，不寫出半成品。改契約的正確方式是改草稿後重跑本腳本，
而不是手改產物——手改會讓雜湊失效，且 ``test_contract_is_frozen_and_hash_self_verifies``
會抓到。

用法：
    python calibration/b11-carbohydrate/freeze_contract.py [--frozen-at ISO8601]
"""

from __future__ import annotations

import argparse
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
DRAFT = HERE / "scope-contract.draft.json"
OUT = HERE / "scope-contract.json"
SCHEMA = ROOT / "schema" / "extraction-scope-contract.schema.json"

DEFAULT_FROZEN_AT = "2026-08-13T00:00:00Z"


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frozen-at", default=DEFAULT_FROZEN_AT,
                    help="凍結時戳（ISO 8601）。預設為固定值，讓凍結可重現。")
    ap.add_argument("--dry-run", action="store_true",
                    help="只檢查，不寫出檔案。")
    args = ap.parse_args(argv)

    draft = json.loads(DRAFT.read_text(encoding="utf-8"))

    problems = freeze.freeze_preflight(draft)
    if problems:
        print("凍結前置檢查未通過：")
        for p in problems:
            print(f"  - {p}")
        return 1

    frozen = freeze.freeze_document(draft, "scopeContractHash",
                                    frozen_at=args.frozen_at)

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(frozen),
                    key=lambda e: list(e.path))
    if errors:
        print("凍結後的契約未通過 schema 驗證：")
        for e in errors[:5]:
            print(f"  - {list(e.path)}: {e.message[:200]}")
        return 1

    # matcher 願意接受，才算真的可用——schema 只管形狀，matcher 管語意前提。
    sm.ScopeMatcher(frozen)

    if not freeze.verify_frozen(frozen, "scopeContractHash"):
        print("雜湊自我驗證失敗（不應發生）")
        return 1

    if args.dry_run:
        print(f"[dry-run] 檢查通過；雜湊會是 {frozen['scopeContractHash']}")
        return 0

    atomic_write_json(OUT, frozen)
    print(f"已凍結 → {OUT}")
    print(f"  scopeContractHash = {frozen['scopeContractHash']}")
    print(f"  frozenAt          = {frozen['frozenAt']}")
    print(f"  inScopeOutcomes   = {len(frozen['inScopeOutcomes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
