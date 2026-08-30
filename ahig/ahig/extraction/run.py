"""把整批語料跑過萃取鏈：**每一篇都要有下落。**

鏈本身已經成段：讀取層驗過才交、橋負責綁定與驗收、範圍判定回到既有的
``ScopeMatcher``。缺的是走完全程的那一段——一次一篇地讀、驗、判，並且在最後
數得出「幾篇成了、幾篇沒成、沒成的卡在哪一段」。

## 為什麼不讓失敗的那些悄悄消失

一篇讀不了、模型沒回、或回來的 draft 收不下，都可能被寫成「跳過」。跳過之後
產出的 scoped 清冊看起來完全正常，只是小一點——而小一點的語料跟乾淨的語料
長得一樣。所以這裡的規則是：**每一個候選最後都恰好落在一個桶子裡**，
且 ``succeeded + 各類失敗 == attempted`` 由 ``InventoryRun`` 自己斷言。

## 讀論文那一端是注入進來的

``reader`` 預設就是 ``inventory_draft.read_sections``——那一支目前會丟
``ReadingSeamNotImplemented``。**不給 reader 就跑，會大聲失敗而不是安靜地
產出零篇。** 測試用替身注入，正式跑則注入真的那一端；接線本身不必再改。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from ahig.extraction import inventory_draft as bridge
from ahig.extraction.corpus import (AcquiredDocument, CorpusError,
                                    iter_acquired, reading_request_for)

Reader = Callable[[bridge.DraftRequest], dict]

STAGES = ("read-corpus", "call-reader", "validate-draft", "scope")


@dataclass
class RecordOutcome:
    candidate_id: str
    stage: str
    ok: bool
    error: str = ""
    scoped: dict | None = None


@dataclass
class InventoryRun:
    contract_hash: str
    outcomes: list[RecordOutcome] = field(default_factory=list)

    @property
    def attempted(self) -> int:
        return len(self.outcomes)

    @property
    def succeeded(self) -> list[RecordOutcome]:
        return [o for o in self.outcomes if o.ok]

    @property
    def failed(self) -> list[RecordOutcome]:
        return [o for o in self.outcomes if not o.ok]

    def failures_by_stage(self) -> dict[str, int]:
        counts = {stage: 0 for stage in STAGES}
        for outcome in self.failed:
            counts[outcome.stage] = counts.get(outcome.stage, 0) + 1
        return counts

    def check(self) -> None:
        """每一篇都要有下落。桶子加起來對不上就是有人被漏掉了。"""
        if len(self.succeeded) + len(self.failed) != self.attempted:
            raise AssertionError("成功與失敗之和不等於嘗試數——有紀錄不見了")
        for outcome in self.outcomes:
            if outcome.stage not in STAGES:
                raise AssertionError(f"未知階段：{outcome.stage}")
            if outcome.ok and outcome.scoped is None:
                raise AssertionError(
                    f"{outcome.candidate_id}：判為成功卻沒有 scoped 清冊")


def _candidate_ids() -> list[str]:
    """語料裡所有 acquired 的 candidateId。

    讀不了的那些在這裡就要被看見，故走 ``iter_acquired`` 而不是自己走目錄：
    它把失敗也產出來，而目錄走訪只會少幾個資料夾。
    """
    ids = []
    for _name, document, _error in iter_acquired():
        if document is not None:
            ids.append(document.candidate_id)
    return ids


def run_inventory(contract: dict, *, reader: Reader | None = None,
                  candidate_ids: Iterable[str] | None = None,
                  now: str | None = None) -> InventoryRun:
    """對每一篇跑：讀 → 交給讀論文那一端 → 驗收 → 判範圍。

    ``reader`` 不給就用尚未接上的那一支，於是整批會在第一篇就大聲失敗——
    那比安靜地跑出零篇好，零篇看起來像「這批沒有東西可報」。
    """
    read = reader or bridge.read_sections
    run = InventoryRun(contract_hash=contract.get("scopeContractHash", ""))
    ids = list(candidate_ids) if candidate_ids is not None else _candidate_ids()

    for candidate_id in ids:
        try:
            request = reading_request_for(candidate_id, contract)
        except (CorpusError, ValueError) as error:
            run.outcomes.append(RecordOutcome(candidate_id, "read-corpus",
                                              False, str(error)))
            continue
        try:
            draft = read(request)
        except Exception as error:  # noqa: BLE001 — 讀論文那一端可能丟任何東西
            run.outcomes.append(RecordOutcome(
                candidate_id, "call-reader", False,
                f"{type(error).__name__}: {error}"))
            continue
        try:
            bridge.validate_draft(draft, request)
        except bridge.DraftRejected as error:
            run.outcomes.append(RecordOutcome(candidate_id, "validate-draft",
                                              False, str(error)))
            continue
        try:
            scoped = bridge.draft_to_scoped(draft, contract, now=now)
        except Exception as error:  # noqa: BLE001
            run.outcomes.append(RecordOutcome(
                candidate_id, "scope", False,
                f"{type(error).__name__}: {error}"))
            continue
        run.outcomes.append(RecordOutcome(candidate_id, "scope", True,
                                          scoped=scoped))

    run.check()
    return run


__all__ = ["InventoryRun", "RecordOutcome", "Reader", "STAGES", "run_inventory",
           "AcquiredDocument"]
