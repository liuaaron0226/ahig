#!/usr/bin/env python3
"""
契約凍結：正規化雜湊、自我一致性檢查，以及凍結前的確定性前置檢查。

凍結一份契約代表兩件事：

1. **內容不可再改**——由 ``scopeContractHash`` 綁定。雜湊必須排除雜湊欄位
   本身，否則無法自我驗證（寫入雜湊會改變被雜湊的內容）。
2. **契約本身不會讓確定性層陷入無解**——例如兩個 in-scope 時窗重疊時，
   任何落在交集的測量點都會被 ``SCOPE-002b`` 升級為人工裁決。這不是資料
   品質問題，是契約作者的錯誤，必須在凍結前擋下來，而不是等到跑了 60 篇
   論文才發現一半的結果卡在人工佇列。

前置檢查刻意只做「契約自身可判定」的事實檢查，不做任何知識判斷。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

# 與 ahig.scope.matcher 共用同一組換算係數；session 不可換算為時間。
UNIT_TO_DAYS = {"hour": 1 / 24, "day": 1.0, "week": 7.0,
                "month": 30.4375, "year": 365.25}


class ContractFreezeError(ValueError):
    """契約在凍結前未通過確定性前置檢查。"""


# ---------------------------------------------------------------------------
# 正規化雜湊
# ---------------------------------------------------------------------------

def canonical_bytes(obj: Any) -> bytes:
    """JCS 風格的正規化序列化：鍵排序、無多餘空白、UTF-8。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def content_hash(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(obj)).hexdigest()


def file_hash(data: bytes) -> str:
    """位元組層級的雜湊，供非 JSON 的附件（例如檢索策略 markdown）使用。"""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def document_hash(doc: dict, hash_field: str) -> str:
    """排除雜湊欄位自身後的正規化雜湊。

    若把 ``hash_field`` 一起算進去，寫回雜湊就會改變文件內容，
    導致沒有任何一份已凍結的文件能通過自我驗證。
    """
    return content_hash({k: v for k, v in doc.items() if k != hash_field})


def freeze_document(doc: dict, hash_field: str, *, frozen_at: str | None = None,
                    status_field: str = "status") -> dict:
    """回傳帶有正確雜湊的副本。不就地修改輸入。"""
    out = dict(doc)
    out.pop(hash_field, None)
    if frozen_at is not None:
        out["frozenAt"] = frozen_at
    if status_field in out:
        out[status_field] = "frozen"
    out[hash_field] = document_hash(out, hash_field)
    return out


def verify_frozen(doc: dict, hash_field: str) -> bool:
    recorded = doc.get(hash_field)
    return bool(recorded) and recorded == document_hash(doc, hash_field)


# ---------------------------------------------------------------------------
# 凍結前的確定性前置檢查
# ---------------------------------------------------------------------------

def _window_in_days(tp: dict) -> tuple[float, float] | None:
    factor = UNIT_TO_DAYS.get(tp["unit"])
    if factor is None:                       # session：不可換算為時間
        return None
    return tp["windowStart"] * factor, tp["windowEnd"] * factor


def timepoint_window_conflicts(contract: dict) -> list[dict]:
    """回傳所有會導致 SCOPE-002b 的時窗重疊。

    session 與時間單位分開比較——matcher 對兩者走不同分支，
    一個只帶 ``timepointDays`` 的測量點永遠不會命中 session 窗。
    """
    conflicts: list[dict] = []
    tps = contract.get("inScopeTimepoints") or []

    for label, items in (("session", [t for t in tps if t["unit"] == "session"]),
                         ("time", [t for t in tps if t["unit"] != "session"])):
        spans = []
        for tp in items:
            if label == "session":
                span: tuple[float, float] = (tp["windowStart"], tp["windowEnd"])
            else:
                converted = _window_in_days(tp)
                if converted is None:        # 不該發生；防禦性略過
                    continue
                span = converted
            if span[0] > span[1]:
                conflicts.append({"kind": "inverted-window",
                                  "axis": label,
                                  "timepoints": [tp["timepointId"]],
                                  "spans": [list(span)]})
                continue
            spans.append((tp["timepointId"], span))

        for i in range(len(spans)):
            for j in range(i + 1, len(spans)):
                (id_a, a), (id_b, b) = spans[i], spans[j]
                # 邊界相接即算重疊：matcher 的比對是閉區間。
                if a[0] <= b[1] and b[0] <= a[1]:
                    conflicts.append({"kind": "overlapping-window",
                                      "axis": label,
                                      "timepoints": sorted([id_a, id_b]),
                                      "spans": [list(a), list(b)]})
    return conflicts


def dose_band_conflicts(contract: dict) -> list[dict]:
    """劑量分帶重疊會讓 ``_match_dose`` 的結果取決於清單順序。"""
    bands = ((contract.get("researchQuestion", {})
              .get("interventionOrExposure", {}).get("doseBands")) or [])
    conflicts: list[dict] = []
    by_unit: dict[str, list[dict]] = {}
    for b in bands:
        if b["min"] > b["max"]:
            conflicts.append({"kind": "inverted-band", "bands": [b["bandId"]]})
            continue
        by_unit.setdefault(b["unit"], []).append(b)

    for unit, items in by_unit.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a["min"] <= b["max"] and b["min"] <= a["max"]:
                    conflicts.append({"kind": "overlapping-band", "unit": unit,
                                      "bands": sorted([a["bandId"], b["bandId"]])})
    return conflicts


def duplicate_ids(contract: dict) -> list[dict]:
    """同一軸上的重複 ID 會讓 matched 元素無法回指唯一定義。"""
    bands = ((contract.get("researchQuestion", {})
              .get("interventionOrExposure", {}).get("doseBands")) or [])
    checks: Iterable[tuple[str, list[dict], str]] = (
        ("inScopeOutcomes", contract.get("inScopeOutcomes") or [], "outcomeId"),
        ("inScopeTimepoints", contract.get("inScopeTimepoints") or [], "timepointId"),
        ("doseBands", bands, "bandId"),
    )
    out: list[dict] = []
    for axis, items, key in checks:
        counts: dict[str, int] = {}
        for it in items:
            counts[it[key]] = counts.get(it[key], 0) + 1
        dupes = sorted(k for k, n in counts.items() if n > 1)
        if dupes:
            out.append({"kind": "duplicate-id", "axis": axis, "ids": dupes})
    return out


def freeze_preflight(contract: dict) -> list[dict]:
    """所有凍結阻擋項。空清單代表可凍結。"""
    return (timepoint_window_conflicts(contract)
            + dose_band_conflicts(contract)
            + duplicate_ids(contract))


def assert_freezable(contract: dict) -> None:
    problems = freeze_preflight(contract)
    if problems:
        raise ContractFreezeError(
            f"契約未通過凍結前置檢查（{len(problems)} 項）：{problems}")
