#!/usr/bin/env python3
"""判讀工作單：session 當判讀器時，題摘出去、判讀回來（ADR-0009 裁定①）。

裁定①把正式判讀器定為**執行室 session 本身**：每輪取批、自行判讀、產出
判讀檔餵驅動器固化。repo 內不放任何 API 呼叫程式或金鑰。這個模組就是那
條路徑的兩端：

- :func:`write_worksheet` 把一份候選清單（前置樣本或影子批次）展開成
  **只含題摘**的工作單，外加一份空的判讀槽。
- :func:`load_judgements` 把填好的判讀檔收回來，做結構檢查後轉成
  :func:`screening_driver.run_batch` 要的 judge 回傳形狀。

為什麼要落盤成檔、而不是 session 直接在記憶體裡判完接上驅動器：

- **可中斷**。154 筆約 57k tokens，一輪 loop 吞不完；工作單分頁、判讀檔
  逐頁累積，下一輪從第一筆未判的接著做。與 ``prevalence_audit`` 的 fill
  模式同一個道理（存檔即續填）。
- **可稽核**。判讀檔是判讀行為的原始紀錄，和固化後的批次分開存；重跑
  固化不會動到判讀本身，判讀出錯也能只重判那幾筆。
- **盲化**。工作單刻意不帶 ``priorityTier``／``matchedRuleIds``——與
  ``screening_driver._entry_payload`` 同一條規則，理由見該處。

本模組不做資格判定，也不呼叫任何模型。它只管「給出去的長什麼樣、收回來
的合不合法」。
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ahig.bootstrap import private_root
from ahig.search.llm_second_review import OPINIONS
from ahig.state import atomic_write_json

# 一頁的筆數。判讀是逐篇讀題摘，頁太大會在單輪 loop 裡讀爆 context；
# 太小則固化次數變多。25 筆約 9k tokens，一輪讀得完還有餘裕做別的事。
DEFAULT_PAGE_SIZE = 25


class WorksheetError(ValueError):
    """工作單輸入缺漏，或判讀檔違反結構規則。"""


def _require_private(path: Path) -> Path:
    """判讀工作單帶著題摘全文，只能待在私有根底下。"""
    root = private_root()
    resolved = Path(path).expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise WorksheetError(f"判讀工作單只能在 AHIG_PRIVATE_ROOT 之下：{root}")
    return resolved


def build_worksheet(candidate_ids: Sequence[str], records: dict[str, dict], *,
                    source: str, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    """把候選清單展開成分頁工作單。

    ``records``：candidateId → 候選紀錄（至少要有 title／abstract）。
    順序照 ``candidate_ids`` 給定的順序，不重排——重排會讓「第 3 頁」在
    兩次產生之間指向不同的東西。
    """
    if page_size <= 0:
        raise WorksheetError("page_size 必須為正整數")
    if not candidate_ids:
        raise WorksheetError("候選清單是空的")
    missing = [cid for cid in candidate_ids if cid not in records]
    if missing:
        raise WorksheetError(
            f"候選池缺這些紀錄：{missing[:3]}（共 {len(missing)} 筆）")
    items = []
    for i, cid in enumerate(candidate_ids):
        rec = records[cid]
        items.append({
            "seq": i + 1,
            "page": i // page_size + 1,
            "candidateId": cid,
            "title": rec.get("title") or None,
            "abstract": (rec.get("abstract") or "").strip() or None,
            "publicationYear": rec.get("publicationYear"),
            "publicationTypes": rec.get("publicationTypes"),
        })
    pages = items[-1]["page"] if items else 0
    return {
        "documentType": "screening-judgement-worksheet",
        "adr": "ADR-0009",
        "source": source,
        "itemCount": len(items),
        "pageSize": page_size,
        "pageCount": pages,
        "withAbstract": sum(1 for it in items if it["abstract"]),
        "items": items,
        "note": ("工作單只帶題摘層資訊，不帶 priorityTier／matchedRuleIds"
                 "等 regex 先驗——那些是我們自己的偏誤，餵進判讀會讓判讀"
                 "跟著 regex 走。"),
    }


def write_worksheet(run_root: Path, candidate_ids: Sequence[str], *,
                    source: str, out_name: str,
                    page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    """產生工作單並落盤（同時建立空判讀檔，若還不存在）。"""
    run_root = _require_private(run_root)
    pool_path = run_root / "candidate-pool" / "candidates.json"
    if not pool_path.exists():
        raise WorksheetError(f"找不到候選池：{pool_path}")
    records = {c["candidateId"]: c
               for c in json.loads(pool_path.read_text(encoding="utf-8"))}
    sheet = build_worksheet(candidate_ids, records, source=source,
                            page_size=page_size)
    out_dir = run_root / out_name
    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out_dir / "worksheet.json", sheet)
    judgements_path = out_dir / "judgements.json"
    if not judgements_path.exists():
        atomic_write_json(judgements_path, {
            "documentType": "screening-judgements",
            "adr": "ADR-0009",
            "source": source,
            "judgedBy": None,
            "entries": [],
        })
    return sheet


def _validate_entry(i: int, item: object, allowed: set[str],
                    seen: set[str]) -> dict:
    if not isinstance(item, dict):
        raise WorksheetError(f"判讀[{i}] 必須是物件")
    cid = item.get("candidateId")
    if cid not in allowed:
        raise WorksheetError(f"判讀[{i}] 的 candidateId 不在工作單內：{cid}")
    if cid in seen:
        raise WorksheetError(f"判讀[{i}] 重複 candidateId：{cid}")
    seen.add(cid)
    opinion = item.get("opinion")
    if opinion not in OPINIONS:
        raise WorksheetError(
            f"判讀[{i}] {cid}: opinion 必須是 {OPINIONS}，得到 {opinion!r}")
    reason = item.get("reason")
    if not (isinstance(reason, str) and reason.strip()):
        raise WorksheetError(
            f"判讀[{i}] {cid}: 必須寫判讀理由——理由就是 rawResponse，"
            "缺了就不可稽核（ADR-0009 原則 3）")
    return {"candidateId": cid, "opinion": opinion, "reason": reason.strip()}


def load_judgements(run_root: Path, *, out_name: str,
                    require_complete: bool = True) -> dict:
    """讀回判讀檔並檢查結構，回傳可餵給驅動器的形狀。

    ``require_complete``：預設要求工作單每筆都判過——固化一個有洞的批次
    會讓下游的分母悄悄變小。續判途中想看進度就傳 ``False``。
    """
    run_root = _require_private(run_root)
    out_dir = run_root / out_name
    sheet = json.loads(
        (out_dir / "worksheet.json").read_text(encoding="utf-8"))
    doc = json.loads(
        (out_dir / "judgements.json").read_text(encoding="utf-8"))
    allowed = {it["candidateId"] for it in sheet["items"]}
    raw = doc.get("entries")
    if not isinstance(raw, list):
        raise WorksheetError("judgements.json 的 entries 必須是陣列")
    seen: set[str] = set()
    entries = [_validate_entry(i, item, allowed, seen)
               for i, item in enumerate(raw)]
    judged_by = doc.get("judgedBy")
    if entries and not (isinstance(judged_by, dict)
                        and judged_by.get("agentClass")):
        raise WorksheetError(
            "judgedBy 缺 agentClass——ADR-0009 原則 2 規定缺此欄位的判讀"
            "不得進入任何下游計算")
    remaining = sorted(allowed - seen)
    if require_complete and remaining:
        raise WorksheetError(
            f"工作單還有 {len(remaining)} 筆未判讀：{remaining[:3]}")
    return {
        "source": sheet["source"],
        "itemCount": sheet["itemCount"],
        "judgedCount": len(entries),
        "remaining": remaining,
        "judgedBy": judged_by,
        "entries": entries,
        "opinions": {e["candidateId"]: e["opinion"] for e in entries},
    }


def file_judge(loaded: dict):
    """把讀回的判讀檔包成 ``screening_driver.run_batch`` 要的 judge。

    驅動器的 judge 介面是 ``(list[dict]) -> list[dict]``，本來預期是模型
    呼叫層。裁定①之後判讀在 session 裡發生、結果先落盤，所以這裡的
    "judge" 只是把已判好的結果照批次順序取出——介面不必改。
    """
    by_id = {e["candidateId"]: e for e in loaded["entries"]}
    judged_by = loaded["judgedBy"]

    def judge(payload: list[dict]) -> list[dict]:
        out = []
        for entry in payload:
            cid = entry["candidateId"]
            got = by_id.get(cid)
            if got is None:
                raise WorksheetError(f"批次含未判讀的 candidateId：{cid}")
            out.append({"candidateId": cid, "opinion": got["opinion"],
                        "rawResponse": got["reason"], "judgedBy": judged_by})
        return out

    return judge


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sheet = sub.add_parser("worksheet", help="由樣本／批次清單產生判讀工作單")
    sheet.add_argument("run_root", type=Path)
    sheet.add_argument("--from-file", required=True, type=Path,
                       help="含 candidateIds 的 JSON（sample.json/batch.json）")
    sheet.add_argument("--out-name", required=True,
                       help="產出子目錄名，如 screening-pilot")
    sheet.add_argument("--field", default="candidateIds",
                       help="要讀的清單欄位，預設 candidateIds")
    sheet.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    page = sub.add_parser("page", help="印出某一頁待判讀的題摘")
    page.add_argument("run_root", type=Path)
    page.add_argument("--out-name", required=True)
    page.add_argument("--page", type=int, default=None,
                      help="頁碼；不給則自動取第一頁尚未判完的")
    status = sub.add_parser("status", help="看判讀進度")
    status.add_argument("run_root", type=Path)
    status.add_argument("--out-name", required=True)
    return parser


def _next_unjudged_page(sheet: dict, judged: set[str]) -> int | None:
    for item in sheet["items"]:
        if item["candidateId"] not in judged:
            return item["page"]
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "worksheet":
        source = json.loads(args.from_file.read_text(encoding="utf-8"))
        ids = source[args.field]
        sheet = write_worksheet(args.run_root, ids, source=args.out_name,
                                out_name=args.out_name,
                                page_size=args.page_size)
        result = {k: v for k, v in sheet.items() if k != "items"}
    else:
        run_root = _require_private(args.run_root)
        out_dir = run_root / args.out_name
        sheet = json.loads(
            (out_dir / "worksheet.json").read_text(encoding="utf-8"))
        loaded = load_judgements(args.run_root, out_name=args.out_name,
                                 require_complete=False)
        judged = set(loaded["opinions"])
        if args.command == "status":
            result = {"itemCount": sheet["itemCount"],
                      "judgedCount": loaded["judgedCount"],
                      "remaining": len(loaded["remaining"]),
                      "pageCount": sheet["pageCount"],
                      "nextPage": _next_unjudged_page(sheet, judged)}
        else:
            page = args.page or _next_unjudged_page(sheet, judged)
            if page is None:
                result = {"done": True, "note": "全部判讀完畢"}
            else:
                result = {"page": page, "pageCount": sheet["pageCount"],
                          "items": [it for it in sheet["items"]
                                    if it["page"] == page
                                    and it["candidateId"] not in judged]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
