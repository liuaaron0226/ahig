"""契約凍結：正規化雜湊與凍結前置檢查。

本檔的主張有兩條：

1. **雜湊必須自我驗證**——排除雜湊欄位自身、與鍵順序無關、與空白無關，
   且任何實質內容變更都必須改變雜湊。
2. **契約自身的無解狀態必須在凍結前被擋下**——時窗重疊、劑量分帶重疊、
   重複 ID。這些不是資料品質問題，而是契約作者的錯誤；放行的代價是
   跑完整批文獻後才發現大量結果卡在人工佇列。
"""

from __future__ import annotations

import json

from ahig.contracts import freeze

try:
    from test_scope_and_family import base_contract
except ImportError:                              # pytest 以 package 方式匯入
    from tests.test_scope_and_family import base_contract


# ===========================================================================
# 1. 正規化雜湊
# ===========================================================================

def test_hash_is_stable_across_key_order():
    a = {"z": 1, "a": {"y": 2, "b": [3, 4]}}
    b = json.loads('{"a": {"b": [3, 4], "y": 2}, "z": 1}')
    assert freeze.content_hash(a) == freeze.content_hash(b)


def test_hash_changes_when_content_changes():
    a = {"a": 1}
    assert freeze.content_hash(a) != freeze.content_hash({"a": 2})


def test_array_order_is_significant():
    """陣列是有序的；靜默把 [a, b] 與 [b, a] 視為同一份契約會遮蔽真實差異。"""
    assert freeze.content_hash({"x": [1, 2]}) != freeze.content_hash({"x": [2, 1]})


def test_document_hash_excludes_the_hash_field_itself():
    doc = {"scopeContractId": "ahig:scope:x", "status": "frozen"}
    h = freeze.document_hash(doc, "scopeContractHash")
    with_hash = dict(doc, scopeContractHash=h)
    assert freeze.document_hash(with_hash, "scopeContractHash") == h


def test_freeze_document_round_trips():
    frozen = freeze.freeze_document(base_contract(status="draft"),
                                    "scopeContractHash",
                                    frozen_at="2026-08-13T00:00:00Z")
    assert frozen["status"] == "frozen"
    assert frozen["frozenAt"] == "2026-08-13T00:00:00Z"
    assert freeze.verify_frozen(frozen, "scopeContractHash")


def test_freeze_document_does_not_mutate_input():
    src = base_contract(status="draft")
    src.pop("scopeContractHash", None)
    snapshot = json.loads(json.dumps(src))
    freeze.freeze_document(src, "scopeContractHash", frozen_at="2026-08-13T00:00:00Z")
    assert src == snapshot


def test_tampered_frozen_document_fails_verification():
    frozen = freeze.freeze_document(base_contract(status="draft"),
                                    "scopeContractHash",
                                    frozen_at="2026-08-13T00:00:00Z")
    frozen["inScopeAnalysisSets"] = ["ITT", "PP"]
    assert not freeze.verify_frozen(frozen, "scopeContractHash")


def test_missing_hash_is_not_verified():
    assert not freeze.verify_frozen({"a": 1}, "scopeContractHash")


# ===========================================================================
# 2. 時窗重疊
# ===========================================================================

def test_disjoint_windows_have_no_conflict():
    assert freeze.timepoint_window_conflicts(base_contract()) == []


def test_overlapping_windows_are_detected():
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "wk4", "label": "4 wk", "windowStart": 3,
         "windowEnd": 6, "unit": "week"},
        {"timepointId": "wk5", "label": "5 wk", "windowStart": 5,
         "windowEnd": 8, "unit": "week"},
    ])
    conflicts = freeze.timepoint_window_conflicts(c)
    assert len(conflicts) == 1
    assert conflicts[0]["kind"] == "overlapping-window"
    assert conflicts[0]["timepoints"] == ["wk4", "wk5"]


def test_touching_windows_count_as_overlap():
    """matcher 用閉區間比對，邊界值會同時命中兩個窗。"""
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "a", "label": "a", "windowStart": 1,
         "windowEnd": 4, "unit": "week"},
        {"timepointId": "b", "label": "b", "windowStart": 4,
         "windowEnd": 8, "unit": "week"},
    ])
    assert freeze.timepoint_window_conflicts(c)


def test_overlap_is_detected_across_different_units():
    """7 day 與 1 week 是同一個時間點；單位不同不代表沒有重疊。"""
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "d5", "label": "5 d", "windowStart": 5,
         "windowEnd": 9, "unit": "day"},
        {"timepointId": "wk1", "label": "1 wk", "windowStart": 1,
         "windowEnd": 2, "unit": "week"},
    ])
    conflicts = freeze.timepoint_window_conflicts(c)
    assert conflicts and conflicts[0]["timepoints"] == ["d5", "wk1"]


def test_session_and_time_windows_do_not_conflict_with_each_other():
    """matcher 對 session 走獨立分支——數值巧合不構成重疊。"""
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "s6", "label": "6 sessions", "windowStart": 4,
         "windowEnd": 8, "unit": "session"},
        {"timepointId": "d6", "label": "6 days", "windowStart": 4,
         "windowEnd": 8, "unit": "day"},
    ])
    assert freeze.timepoint_window_conflicts(c) == []


def test_overlapping_session_windows_are_detected():
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "s1", "label": "s1", "windowStart": 4,
         "windowEnd": 8, "unit": "session"},
        {"timepointId": "s2", "label": "s2", "windowStart": 7,
         "windowEnd": 10, "unit": "session"},
    ])
    assert freeze.timepoint_window_conflicts(c)


def test_inverted_window_is_flagged():
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "bad", "label": "bad", "windowStart": 9,
         "windowEnd": 3, "unit": "week"},
    ])
    conflicts = freeze.timepoint_window_conflicts(c)
    assert conflicts and conflicts[0]["kind"] == "inverted-window"


def test_three_overlapping_windows_report_each_pair():
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "a", "label": "a", "windowStart": 1,
         "windowEnd": 9, "unit": "week"},
        {"timepointId": "b", "label": "b", "windowStart": 2,
         "windowEnd": 8, "unit": "week"},
        {"timepointId": "c", "label": "c", "windowStart": 3,
         "windowEnd": 7, "unit": "week"},
    ])
    assert len(freeze.timepoint_window_conflicts(c)) == 3


# ===========================================================================
# 3. 劑量分帶與重複 ID
# ===========================================================================

def test_disjoint_dose_bands_have_no_conflict():
    assert freeze.dose_band_conflicts(base_contract()) == []


def test_overlapping_dose_bands_are_detected():
    c = base_contract()
    c["researchQuestion"]["interventionOrExposure"]["doseBands"] = [
        {"bandId": "low", "min": 1, "max": 5, "unit": "g"},
        {"bandId": "mid", "min": 4, "max": 9, "unit": "g"},
    ]
    conflicts = freeze.dose_band_conflicts(c)
    assert conflicts and conflicts[0]["bands"] == ["low", "mid"]


def test_dose_bands_in_different_units_are_not_compared():
    """g 與 g/kg 是不同的量；數值區間重疊不構成契約衝突。"""
    c = base_contract()
    c["researchQuestion"]["interventionOrExposure"]["doseBands"] = [
        {"bandId": "abs", "min": 1, "max": 5, "unit": "g"},
        {"bandId": "rel", "min": 1, "max": 5, "unit": "g/(kg.h)"},
    ]
    assert freeze.dose_band_conflicts(c) == []


def test_duplicate_outcome_ids_are_detected():
    c = base_contract()
    c["inScopeOutcomes"] = c["inScopeOutcomes"] + [dict(c["inScopeOutcomes"][0])]
    dupes = freeze.duplicate_ids(c)
    assert dupes and dupes[0]["ids"] == ["1rm-squat"]


def test_duplicate_timepoint_ids_are_detected():
    c = base_contract()
    c["inScopeTimepoints"] = c["inScopeTimepoints"] + [dict(c["inScopeTimepoints"][0])]
    assert freeze.duplicate_ids(c)


# ===========================================================================
# 4. assert_freezable
# ===========================================================================

def test_clean_contract_is_freezable():
    freeze.assert_freezable(base_contract())        # 不得拋出


def test_conflicting_contract_refuses_to_freeze():
    c = base_contract(inScopeTimepoints=[
        {"timepointId": "a", "label": "a", "windowStart": 1,
         "windowEnd": 9, "unit": "week"},
        {"timepointId": "b", "label": "b", "windowStart": 2,
         "windowEnd": 8, "unit": "week"},
    ])
    try:
        freeze.assert_freezable(c)
    except freeze.ContractFreezeError:
        return
    raise AssertionError("重疊時窗的契約不得通過 assert_freezable")
