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

## 每個數字的出處：報而不擋

`validate_draft` 拿文件真有的章節去核對 ``sectionsScanned``——理由是
「聲稱掃描過本文件沒有的章節，該聲明不可信」。**而每一項結局自己的
``sourceLocation.section``（那個數字是從哪裡抄來的）沒有任何東西在看。**
🚨 兩者是同一種宣稱，而後者才是把數字追回去的那條線。

**🚫 這裡不擋，只數。** 理由兩條：

- schema 明講「粗座標即可……這是它廉價的原因」——⚠️ 擋下去等於改契約。
- 全語料有 20 個節的標題是字面 ``Untitled``（`n541`：分布 18 篇、7.3% 的字）。
  **🚨 強制「必須是真標題」會讓那些節無法被引用**，而那正是 `n541` 記為
  「未被觸發」的那項限制——⚠️ 擋下去就是親手觸發它。

故收據逐篇記 ``unknownSections``：**指不到任何真章節的出處有幾個。**
⚠️ 今天沒有人讀，這個數必然是替身的；🚨 真的讀起來之後它才有意義。

## 兩套驗收，先前只跑其中一套

`validate_draft` 是**本鏈**的驗收（綁定、lifecycle、完整性聲明）；
`schema/outcome-inventory.schema.json` 是**下游**的驗收，且它是
``additionalProperties: false``。**第 539 輪查明兩者不等價**：一份
`validate_draft` 收得下的 draft，schema 可以整份退回（缺 ``attestedBy.at``、
``harmsScan`` 缺三個必填欄位、``agentClass`` 不在列舉內）。

🚨 而在此之前，鏈上沒有任何一段在看 schema——**於是不合下游規格的清冊會被
照樣判範圍、照樣存檔**，等到下游才退。⚠️ 那時候看起來會像是模型回了壞東西，
🚫 而實際上是我們自己沒驗。故這裡兩處都驗：draft 一次、scoped 一次。

## 契約先驗，再花錢

判範圍是**最後一段**，而 ``ScopeMatcher`` 是在那時候才被造出來的。於是一份
造不出 matcher 的契約（缺欄位、型別不對），要等到 41 篇都讀完才會顯現——
**41 筆全部卡在 ``scope``，錢已經花光，一份清冊都沒有。**

第 535 輪實測：真的那份 ``b11-carbohydrate/scope-contract.json`` 造得出 matcher。
**但那道檢查本身不存在**——而上一輪本室的樁契約正是造不出來的那一種，
說明這不是想像出來的壞法。故 ``run_inventory`` 開跑前先造一次，造不出就**整批拒跑**。

🚫 這裡不是「代替」最後那一段的判定，只是把**契約層面**的失敗挪到花錢之前。

## 跑完要留下收據

n+184 卡在一句「沒有 B.11 的用量紀錄」。那句話當時是真的——**而它之所以是真的，
正是因為跑完之後沒有任何東西被寫下來。** 故給了 ``store`` 就一併寫一份批次紀錄：
逐篇一列，含這一趟送出去與收回來的**字元數**。

**刻意不寫 token 數，也不寫金額**：換算率與牌價這裡都沒有憑據，寫下去會讓一個
猜的數字看起來像量到的。字元是真的量到的，而 n+184 的算式本來就從字元起算。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from ahig.contracts.freeze import content_hash
from ahig.extraction import inventory_draft as bridge
from ahig.extraction.corpus import (AcquiredDocument, CorpusError,
                                    iter_acquired, reading_request_for)
from ahig.scope.matcher import ScopeMatcher
from ahig.search.fulltext import utc_now

Reader = Callable[[bridge.DraftRequest], dict]


class ContractUnusable(Exception):
    """契約造不出 ScopeMatcher。整批拒跑，不是逐筆失敗。

    逐筆失敗的紀錄看起來像「試過了，41 篇都沒成」——而實際上一篇都不該試。
    """

STAGES = ("read-corpus", "call-reader", "validate-draft", "scope", "reused")

# 下游那一份。位置照本 repo 既有慣例（`gates/shacl.py` 亦以 parents[2] 定位）。
_SCHEMA_PATH = (Path(__file__).resolve().parents[2] / "schema"
                / "outcome-inventory.schema.json")
_validator = None


def _schema_errors(document: dict) -> str:
    """不合下游 schema 之處，回傳一句話；沒有問題回空字串。

    只報首處與總數：一份文件錯十處時，把十處都塞進 outcome 只會讓報表難讀，
    而**修第一處通常就會連帶改掉其餘**。
    """
    global _validator
    if _validator is None:
        from jsonschema import Draft202012Validator
        _validator = Draft202012Validator(
            json.loads(_SCHEMA_PATH.read_text(encoding="utf-8")))
    errors = sorted(_validator.iter_errors(document),
                    key=lambda e: list(e.path))
    if not errors:
        return ""
    first = errors[0]
    where = "/".join(str(p) for p in first.path) or "(root)"
    return "%d 處不合 outcome-inventory schema，首處 %s：%s" % (
        len(errors), where, first.message)


@dataclass
class RecordOutcome:
    candidate_id: str
    stage: str
    ok: bool
    error: str = ""
    scoped: dict | None = None
    # 送出去與收回來的**字元數**。不是 token，也不是錢——見模組說明。
    request_chars: int = 0
    draft_chars: int = 0
    # 指不到任何真章節的 sourceLocation 有幾個。🚫 不擋，只數。
    unknown_sections: int = 0
    reference: dict | None = None

    def to_json(self) -> dict:
        item = {"candidateId": self.candidate_id, "stage": self.stage,
                "ok": self.ok, "requestChars": self.request_chars,
                "draftChars": self.draft_chars,
                "unknownSections": self.unknown_sections}
        if self.error:
            item["error"] = self.error
        if self.reference:
            item.update(self.reference)
        return item


@dataclass
class InventoryRun:
    contract_hash: str
    outcomes: list[RecordOutcome] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    batch_path: str = ""

    @property
    def attempted(self) -> int:
        return len(self.outcomes)

    @property
    def succeeded(self) -> list[RecordOutcome]:
        return [o for o in self.outcomes if o.ok]

    @property
    def read_this_run(self) -> list[RecordOutcome]:
        """這一次真的讀過的。與 ``succeeded`` 分開報，否則一次什麼都沒讀的
        重跑，會和一次完整的跑長得一樣。"""
        return [o for o in self.outcomes if o.ok and o.stage != "reused"]

    @property
    def reused(self) -> list[RecordOutcome]:
        return [o for o in self.outcomes if o.stage == "reused"]

    @property
    def failed(self) -> list[RecordOutcome]:
        return [o for o in self.outcomes if not o.ok]

    def failures_by_stage(self) -> dict[str, int]:
        counts = {stage: 0 for stage in STAGES}
        for outcome in self.failed:
            counts[outcome.stage] = counts.get(outcome.stage, 0) + 1
        return counts

    def to_batch_record(self) -> dict:
        """這一趟做了什麼。**逐篇一列，不只有總數。**

        n+184 卡在一句「沒有用量紀錄」。那句話當時是真的，而它之所以是真的，
        正是因為跑完之後沒有任何東西被寫下來。這裡寫下來的是**字元數**——
        送出去的與收回來的。

        刻意不寫 token 數，也不寫金額：換算率與牌價這裡都沒有憑據，寫下去
        會讓一個猜的數字看起來像量到的。字元是真的量到的，而 n+184 的算式
        本來就是從字元起算，故拿這個數就推得回去。

        ``batchId`` 由內容導出（取得層的 batch 也是這樣做的），故同一趟跑出來
        的紀錄寫兩次會是同一個檔，而內容不同就是導出方式壞了。
        """
        record = {
            "documentType": "outcome-inventory-batch",
            "scopeContractHash": self.contract_hash,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "candidateCount": self.attempted,
            "readThisRunCount": len(self.read_this_run),
            "reusedCount": len(self.reused),
            "failedCount": len(self.failed),
            "charsSent": sum(o.request_chars for o in self.outcomes),
            "charsReturned": sum(o.draft_chars for o in self.outcomes),
            "unknownSections": sum(o.unknown_sections
                                   for o in self.outcomes),
            "results": [o.to_json() for o in self.outcomes],
        }
        seed = {"scopeContractHash": self.contract_hash,
                "startedAt": self.started_at,
                "candidateIds": [o.candidate_id for o in self.outcomes]}
        record["batchId"] = "inventory-batch-" + content_hash(seed).removeprefix(
            "sha256:")[:16]
        record["batchHash"] = content_hash(record)
        return record

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


def _unknown_sections(draft: dict, request) -> int:
    """有幾個 ``sourceLocation.section`` 指不到這份文件真有的章節。

    🚫 不擋，只數——理由見模組說明。⚠️ 比對照 `sections_titled` 的規則：
    去前後空白、不分大小寫。
    """
    known = {title.strip().lower() for title in request.section_titles}
    unknown = 0
    for item in draft.get("reportedOutcomes") or []:
        where = (item.get("sourceLocation") or {}).get("section")
        if isinstance(where, str) and where.strip().lower() not in known:
            unknown += 1
    return unknown


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
                  now: str | None = None, store=None) -> InventoryRun:
    """對每一篇跑：讀 → 交給讀論文那一端 → 驗收 → 判範圍。

    ``reader`` 不給就用尚未接上的那一支，於是整批會在第一篇就大聲失敗——
    那比安靜地跑出零篇好，零篇看起來像「這批沒有東西可報」。

    給了 ``store`` 就會跳過「同一份文件、同一份契約」已經做過的那些，並把它們
    記成 ``reused`` 而不是成功——讀一篇要花錢，而一次什麼都沒讀的重跑不該和
    一次完整的跑長得一樣。
    """
    read = reader or bridge.read_sections
    # 造不出 matcher 的契約，要在讀第一篇之前就擋下來——不然 41 篇讀完
    # 才會全部卡在 scope，錢花光而一份清冊都沒有。
    try:
        ScopeMatcher(contract)
    except Exception as error:  # noqa: BLE001 — 契約可能以任何方式壞掉
        raise ContractUnusable(
            f"範圍契約造不出 ScopeMatcher（{type(error).__name__}: {error}）"
            "——整批拒跑，一篇都不讀") from error
    run = InventoryRun(contract_hash=contract.get("scopeContractHash", ""),
                       started_at=utc_now())
    ids = list(candidate_ids) if candidate_ids is not None else _candidate_ids()

    for candidate_id in ids:
        try:
            request = reading_request_for(candidate_id, contract)
        except (CorpusError, ValueError) as error:
            run.outcomes.append(RecordOutcome(candidate_id, "read-corpus",
                                              False, str(error)))
            continue
        # 送出去的字元數要在真的送之前就量得到——失敗的那些也要有這個數，
        # 否則「這一趟送了多少」會少掉正是最貴的那幾筆。
        sent = len(json.dumps(request.prompt_payload(), ensure_ascii=False))
        if store is not None:
            existing = store.load_if_current(candidate_id, request.manifestation,
                                             request.scope_contract_hash)
            if existing is not None:
                # 重用不記 sent：這一趟並沒有把它送出去。
                path = store.inventory_path(candidate_id, request.manifestation,
                                            request.scope_contract_hash)
                run.outcomes.append(RecordOutcome(
                    candidate_id, "reused", True, scoped=existing,
                    reference=store.reference(path)))
                continue
        try:
            draft = read(request)
        except Exception as error:  # noqa: BLE001 — 讀論文那一端可能丟任何東西
            run.outcomes.append(RecordOutcome(
                candidate_id, "call-reader", False,
                f"{type(error).__name__}: {error}", request_chars=sent))
            continue
        returned = len(json.dumps(draft, ensure_ascii=False, default=str))
        unknown = _unknown_sections(draft, request)
        try:
            bridge.validate_draft(draft, request)
        except bridge.DraftRejected as error:
            run.outcomes.append(RecordOutcome(
                candidate_id, "validate-draft", False, str(error),
                request_chars=sent, draft_chars=returned,
                unknown_sections=unknown))
            continue
        problem = _schema_errors(draft)
        if problem:
            run.outcomes.append(RecordOutcome(
                candidate_id, "validate-draft", False, problem,
                request_chars=sent, draft_chars=returned,
                unknown_sections=unknown))
            continue
        try:
            scoped = bridge.draft_to_scoped(draft, contract, now=now)
        except Exception as error:  # noqa: BLE001
            run.outcomes.append(RecordOutcome(
                candidate_id, "scope", False,
                f"{type(error).__name__}: {error}",
                request_chars=sent, draft_chars=returned))
            continue
        problem = _schema_errors(scoped)
        if problem:
            run.outcomes.append(RecordOutcome(
                candidate_id, "scope", False, problem,
                request_chars=sent, draft_chars=returned))
            continue
        saved = None
        if store is not None:
            try:
                saved = store.reference(store.save(scoped))
            except Exception as error:  # noqa: BLE001
                run.outcomes.append(RecordOutcome(
                    candidate_id, "scope", False,
                    f"{type(error).__name__}: {error}",
                    request_chars=sent, draft_chars=returned))
                continue
        run.outcomes.append(RecordOutcome(
            candidate_id, "scope", True, scoped=scoped,
            request_chars=sent, draft_chars=returned, reference=saved,
            unknown_sections=unknown))

    run.finished_at = utc_now()
    run.check()
    if store is not None:
        run.batch_path = store.save_batch(run.to_batch_record()).name
    return run


__all__ = ["ContractUnusable", "InventoryRun", "RecordOutcome", "Reader",
           "STAGES", "run_inventory", "AcquiredDocument"]
