#!/usr/bin/env python3
"""判讀工作單（ADR-0009 裁定①：session 當判讀器）。

驗的是三件事：

- 工作單只帶題摘層資訊，不洩漏 regex 先驗（盲化）；
- 判讀檔的結構檢查擋得住缺理由、缺 judgedBy、越界 id、重複 id；
- 續判語意正確——判一半不算完成，接上去能補完。
"""

import json
import os
import tempfile
from pathlib import Path

from ahig.search import judgement_worksheet as ws
from ahig.search import screening_driver as drv

POOL = [
    {"candidateId": f"c{i}",
     "title": f"Title {i}",
     "abstract": f"Abstract body {i}" if i % 2 else "",
     "publicationYear": 2020 + i % 3,
     "publicationTypes": ["Journal Article"],
     "priorityTier": "T1-high-signal",
     "matchedRuleIds": ["R-007"]}
    for i in range(1, 11)
]
IDS = [c["candidateId"] for c in POOL]


class _Private:
    """把私有根指到暫存目錄，離開時還原。"""

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = self._tmp.name
        root = Path(self._tmp.name) / "run"
        (root / "candidate-pool").mkdir(parents=True)
        (root / "candidate-pool" / "candidates.json").write_text(
            json.dumps(POOL, ensure_ascii=False), encoding="utf-8")
        return root

    def __exit__(self, *exc):
        if self._old is None:
            os.environ.pop("AHIG_PRIVATE_ROOT", None)
        else:
            os.environ["AHIG_PRIVATE_ROOT"] = self._old
        self._tmp.cleanup()
        return False


def _write_judgements(root: Path, out_name: str, entries: list[dict], *,
                      judged_by: dict | None = None) -> None:
    path = root / out_name / "judgements.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["entries"] = entries
    # 空 dict 是有意義的輸入（測缺 agentClass），不能用 or 折疊掉。
    doc["judgedBy"] = ({"agentClass": "llm", "modelId": "claude-opus-5"}
                       if judged_by is None else judged_by)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _entry(cid: str, opinion: str = "exclude") -> dict:
    return {"candidateId": cid, "opinion": opinion,
            "reason": f"{cid}: 非 RCT，敘述性回顧"}


# --- 工作單產生 ---

def test_worksheet_carries_only_title_abstract_layer():
    """盲化：regex 先驗不得出現在工作單，否則判讀會跟著我們的偏誤走。"""
    sheet = ws.build_worksheet(IDS, {c["candidateId"]: c for c in POOL},
                               source="screening-pilot", page_size=4)
    leaked = {"priorityTier", "matchedRuleIds", "suggestedStrata",
              "screeningLane"}
    for item in sheet["items"]:
        assert not (leaked & set(item)), f"工作單洩漏先驗：{set(item) & leaked}"
    assert sheet["itemCount"] == 10
    assert sheet["pageCount"] == 3          # 4 + 4 + 2
    assert sheet["withAbstract"] == 5       # 奇數號才有摘要


def test_worksheet_preserves_given_order_and_pages_stably():
    """頁碼要穩定——重排會讓「第 3 頁」在兩次產生之間指向不同的東西。"""
    reversed_ids = list(reversed(IDS))
    sheet = ws.build_worksheet(reversed_ids,
                               {c["candidateId"]: c for c in POOL},
                               source="s", page_size=4)
    assert [it["candidateId"] for it in sheet["items"]] == reversed_ids
    assert [it["page"] for it in sheet["items"][:4]] == [1, 1, 1, 1]
    assert sheet["items"][4]["page"] == 2


def test_worksheet_rejects_empty_list_and_missing_records():
    for bad, needle in (([], "空"), (["c1", "nope"], "缺這些紀錄")):
        try:
            ws.build_worksheet(bad, {c["candidateId"]: c for c in POOL},
                               source="s")
        except ws.WorksheetError as exc:
            assert needle in str(exc)
        else:
            raise AssertionError(f"應該要拒絕：{bad}")


def test_write_worksheet_creates_empty_judgement_slot_and_is_idempotent():
    with _Private() as root:
        ws.write_worksheet(root, IDS[:4], source="screening-pilot",
                           out_name="screening-pilot", page_size=2)
        path = root / "screening-pilot" / "judgements.json"
        assert json.loads(path.read_text(encoding="utf-8"))["entries"] == []
        _write_judgements(root, "screening-pilot", [_entry("c1")])
        # 重跑工作單不得清掉已填的判讀。
        ws.write_worksheet(root, IDS[:4], source="screening-pilot",
                           out_name="screening-pilot", page_size=2)
        again = json.loads(path.read_text(encoding="utf-8"))
        assert [e["candidateId"] for e in again["entries"]] == ["c1"]


def test_write_worksheet_refuses_outside_private_root():
    with _Private():
        with tempfile.TemporaryDirectory() as outside:
            try:
                ws.write_worksheet(Path(outside), IDS[:2], source="s",
                                   out_name="s")
            except ws.WorksheetError as exc:
                assert "AHIG_PRIVATE_ROOT" in str(exc)
            else:
                raise AssertionError("私有根之外應該要拒絕")


# --- 判讀檔回收 ---

def test_load_judgements_round_trips_opinions():
    with _Private() as root:
        ws.write_worksheet(root, IDS[:3], source="p", out_name="p")
        _write_judgements(root, "p", [_entry("c1", "advance"),
                                      _entry("c2", "exclude"),
                                      _entry("c3", "unclear")])
        loaded = ws.load_judgements(root, out_name="p")
        assert loaded["opinions"] == {"c1": "advance", "c2": "exclude",
                                      "c3": "unclear"}
        assert loaded["remaining"] == []
        assert loaded["judgedBy"]["agentClass"] == "llm"


def test_load_judgements_treats_partial_as_incomplete():
    """判一半就固化會讓下游分母悄悄變小——預設必須擋。"""
    with _Private() as root:
        ws.write_worksheet(root, IDS[:5], source="p", out_name="p")
        _write_judgements(root, "p", [_entry("c1"), _entry("c2")])
        try:
            ws.load_judgements(root, out_name="p")
        except ws.WorksheetError as exc:
            assert "未判讀" in str(exc)
        else:
            raise AssertionError("不完整的判讀檔應該要擋下")
        partial = ws.load_judgements(root, out_name="p",
                                     require_complete=False)
        assert partial["judgedCount"] == 2
        assert partial["remaining"] == ["c3", "c4", "c5"]
        # 續判：補完剩下的就通過。
        _write_judgements(root, "p", [_entry(cid) for cid in IDS[:5]])
        assert ws.load_judgements(root, out_name="p")["judgedCount"] == 5


def test_load_judgements_rejects_missing_reason_alien_and_duplicate():
    cases = [
        ([{"candidateId": "c1", "opinion": "advance", "reason": "  "}],
         "判讀理由"),
        ([{"candidateId": "zz", "opinion": "advance", "reason": "x"}],
         "不在工作單內"),
        ([_entry("c1"), _entry("c1")], "重複"),
        ([{"candidateId": "c1", "opinion": "maybe", "reason": "x"}],
         "opinion 必須是"),
    ]
    for entries, needle in cases:
        with _Private() as root:
            ws.write_worksheet(root, IDS[:3], source="p", out_name="p")
            _write_judgements(root, "p", entries)
            try:
                ws.load_judgements(root, out_name="p",
                                   require_complete=False)
            except ws.WorksheetError as exc:
                assert needle in str(exc), f"{needle} 沒出現在：{exc}"
            else:
                raise AssertionError(f"應該要拒絕：{entries}")


def test_load_judgements_requires_judged_by():
    """ADR-0009 原則 2：缺 judgedBy 的判讀不得進入下游計算。"""
    with _Private() as root:
        ws.write_worksheet(root, IDS[:2], source="p", out_name="p")
        _write_judgements(root, "p", [_entry("c1")], judged_by={})
        try:
            ws.load_judgements(root, out_name="p", require_complete=False)
        except ws.WorksheetError as exc:
            assert "judgedBy" in str(exc)
        else:
            raise AssertionError("缺 judgedBy 應該要擋下")


# --- 分頁併入 ---

def test_append_accumulates_pages_and_records_judged_by_once():
    """判一頁併一頁，判讀者只在第一次併入時記下。"""
    with _Private() as root:
        ws.write_worksheet(root, IDS[:5], source="p", out_name="p",
                           page_size=2)
        who = {"agentClass": "llm", "modelId": "claude-opus-5"}
        first = ws.append_judgements(root, [_entry("c1"), _entry("c2")],
                                     out_name="p", judged_by=who)
        assert first == {"added": 2, "judgedCount": 2, "remaining": 3}
        # 第二頁不再傳 judged_by，既有的要留著。
        second = ws.append_judgements(root, [_entry("c3"), _entry("c4"),
                                             _entry("c5", "advance")],
                                      out_name="p")
        assert second == {"added": 3, "judgedCount": 5, "remaining": 0}
        loaded = ws.load_judgements(root, out_name="p")
        assert loaded["judgedBy"] == who
        assert loaded["opinions"]["c5"] == "advance"


def test_append_rejects_duplicate_against_existing_and_writes_nothing():
    """重判同一筆代表判讀有誤，且半套寫入會讓判讀檔讀不回來。"""
    with _Private() as root:
        ws.write_worksheet(root, IDS[:4], source="p", out_name="p")
        who = {"agentClass": "llm", "modelId": "claude-opus-5"}
        ws.append_judgements(root, [_entry("c1")], out_name="p",
                             judged_by=who)
        try:
            ws.append_judgements(root, [_entry("c2"), _entry("c1")],
                                 out_name="p")
        except ws.WorksheetError as exc:
            assert "重複" in str(exc)
        else:
            raise AssertionError("與既有判讀重複應該要擋下")
        after = ws.load_judgements(root, out_name="p",
                                   require_complete=False)
        assert after["judgedCount"] == 1, "被拒的整批都不該落盤"


def test_append_requires_judged_by_before_first_write():
    """ADR-0009 原則 2：沒記下判讀者就不准開始累積判讀。"""
    with _Private() as root:
        ws.write_worksheet(root, IDS[:3], source="p", out_name="p")
        try:
            ws.append_judgements(root, [_entry("c1")], out_name="p")
        except ws.WorksheetError as exc:
            assert "agentClass" in str(exc)
        else:
            raise AssertionError("缺 judgedBy 應該要擋下")
        assert ws.load_judgements(root, out_name="p",
                                  require_complete=False)["judgedCount"] == 0


# --- 接上驅動器 ---

def test_file_judge_feeds_the_driver_unchanged():
    """判讀檔包成 judge 後，驅動器介面不必改。"""
    with _Private() as root:
        ws.write_worksheet(root, IDS[:3], source="p", out_name="p")
        _write_judgements(root, "p", [_entry("c1", "advance"),
                                      _entry("c2"), _entry("c3")])
        loaded = ws.load_judgements(root, out_name="p")
        queue = [{"candidateId": cid} for cid in IDS[:3]]
        manifest = {"screeningQueueHash": "sha256:deadbeef",
                    "runId": "test-run"}
        fixed = drv.run_batch(
            manifest, queue, queue, ws.file_judge(loaded),
            model_id="claude-opus-5", model_version="2026-08",
            prompt_template="判讀範本 v1")
        assert fixed["opinionCount"] == 3
        assert fixed["judgedBy"]["agentClass"] == "llm"
        by_id = {e["candidateId"]: e for e in fixed["entries"]}
        assert by_id["c1"]["opinion"] == "advance"
        assert by_id["c1"]["rawResponse"].startswith("c1:")


def test_file_judge_raises_on_unjudged_record():
    with _Private() as root:
        ws.write_worksheet(root, IDS[:3], source="p", out_name="p")
        _write_judgements(root, "p", [_entry("c1")])
        loaded = ws.load_judgements(root, out_name="p",
                                    require_complete=False)
        judge = ws.file_judge(loaded)
        try:
            judge([{"candidateId": "c2"}])
        except ws.WorksheetError as exc:
            assert "未判讀" in str(exc)
        else:
            raise AssertionError("未判讀的紀錄不該悄悄通過")
