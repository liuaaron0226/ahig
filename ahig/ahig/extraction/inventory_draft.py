"""sections 文件 → draft 結局清冊 → scoped 清冊。

## 這個模組刻意不含模型呼叫

schema 把 lifecycle 分成兩態，而那個切分是信任模型的骨幹：

    draft   登錄「這篇論文說了什麼」，**不得含任何範圍判定**
    scoped  由確定性 ScopeMatcher 逐項加上具名規則的判定

模型只能產生 draft。範圍判定若由模型自填，等同繞過範圍契約。

因此本模組把「讀論文」留成一道明確的接縫（``build_reading_request`` 產出
請求、``validate_draft`` 驗收回傳），而**判定一律走既有的確定性層**。
接縫未接上時 ``ReadingSeamNotImplemented``，不回傳空清冊——
空的 reportedOutcomes 無法區分「沒抽到」與「論文沒報告」，
而 schema 的 minItems=1 正是為了擋這件事。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ..scope import inventory as inv
from ..scope.matcher import ScopeMatcher

SHA_PREFIX = "sha256:"


class ReadingSeamNotImplemented(NotImplementedError):
    """尚未接上讀論文的那一段。

    刻意不以「回傳空清冊」代替：空清冊會被下游讀成「這篇沒有報告任何結局」，
    而那是一個關於論文的宣稱，不是關於我們的。
    """


class DraftRejected(ValueError):
    """模型回傳之 draft 不合格。"""


def _sha(data: bytes) -> str:
    return SHA_PREFIX + hashlib.sha256(data).hexdigest()


def _sections_of(doc: dict) -> list[dict]:
    if doc.get("documentType") != "fulltext-sections":
        raise ValueError(
            f"不是 sections 文件（documentType={doc.get('documentType')!r}）")
    sections = doc.get("sections")
    if not sections:
        raise ValueError("sections 為空——無法宣稱掃描過任何章節")
    return sections


@dataclass
class DraftRequest:
    """交給讀論文那一端的請求。本身不含模型，只描述要讀什麼、要交回什麼。"""

    report: str
    manifestation: str
    scope_contract_hash: str
    section_titles: list[str]
    content: str
    outcome_hints: list[dict] = field(default_factory=list)

    def prompt_payload(self) -> dict:
        """要讀什麼、要回傳什麼形狀。

        outcome_hints 是範圍契約裡的結局，供對照用；**不是允許清單**——
        清冊要登錄的是「論文報告了什麼」，含範圍外的，否則
        outcome-switching 偵測與日後的 backfill 都失去依據。
        """
        return {
            "task": "list every outcome this report states it measured",
            "mustIncludeOutOfScope": True,
            "sectionTitles": self.section_titles,
            "content": self.content,
            "contractOutcomesForReference": self.outcome_hints,
            "returnShape": "reportedOutcomes[] per OutcomeInventory schema",
            "mustNotReturn": ["scopeDecision", "scopedAt", "scopeDecisionSummary"],
        }


def build_reading_request(sections_doc: dict, contract: dict, *,
                          report: str) -> DraftRequest:
    """由 sections 文件與範圍契約組出讀論文的請求。

    manifestation 取 sections 文件自記的 contentSha256——那是「被讀的到底是哪一份」
    的憑證；若缺，就地失敗，不改以重算代替：重算得到的是「現在這份」的雜湊，
    而清冊要綁的是產生它的那一份。
    """
    sections = _sections_of(sections_doc)
    manifestation = sections_doc.get("contentSha256")
    if not manifestation or not manifestation.startswith(SHA_PREFIX):
        raise ValueError("sections 文件缺 contentSha256——無法指明被讀的是哪一份")
    # ScopeMatcher 也擋未凍結的契約，但它擋在判定那一步——那時論文已經讀過了。
    # 讀一篇論文是有成本的，且對著一份還會變的契約讀，讀完也不能用。
    if contract.get("status") != "frozen":
        raise ValueError(
            f"範圍契約 status={contract.get('status')!r}，非 frozen——"
            "不得對著還會變的契約讀論文")
    contract_hash = contract.get("scopeContractHash")
    if not contract_hash or not contract_hash.startswith(SHA_PREFIX):
        raise ValueError("範圍契約已宣告 frozen 卻無 scopeContractHash——綁定不完整")

    return DraftRequest(
        report=report,
        manifestation=manifestation,
        scope_contract_hash=contract_hash,
        section_titles=[s.get("title") or "" for s in sections],
        content=sections_doc.get("content", ""),
        outcome_hints=[{"outcomeId": o["outcomeId"], "label": o["label"]}
                       for o in contract.get("inScopeOutcomes", [])],
    )


def validate_draft(draft: dict, request: DraftRequest) -> dict:
    """驗收讀論文那一端交回的 draft。

    三件事分開查，因為它們壞掉的方式不同：
      1. lifecycle 必須是 draft，且不得挾帶任何範圍判定
      2. 綁定必須與請求一致（讀的是不是同一份、對的是不是同一份契約）
      3. 完整性聲明所列章節，必須真的來自這份文件
    """
    if draft.get("lifecycle") != "draft":
        raise DraftRejected(
            f"lifecycle 必須為 draft，得到 {draft.get('lifecycle')!r}——"
            "範圍判定屬確定性層，模型不得自填")

    leaked = [k for k in ("scopedAt", "scopeDecisionSummary") if k in draft]
    leaked += ["reportedOutcomes[].scopeDecision"] if any(
        "scopeDecision" in o for o in draft.get("reportedOutcomes", [])) else []
    if leaked:
        raise DraftRejected(f"draft 挾帶了範圍判定：{leaked}——等同繞過範圍契約")

    if not draft.get("reportedOutcomes"):
        raise DraftRejected(
            "reportedOutcomes 為空——空清冊無法區分「沒抽到」與「論文沒報告」")

    for field_name, want in (("manifestation", request.manifestation),
                             ("scopeContractHash", request.scope_contract_hash),
                             ("report", request.report)):
        got = draft.get(field_name)
        if got != want:
            raise DraftRejected(
                f"{field_name} 與請求不符：請求 {want!r}，回傳 {got!r}"
                "——不確定讀的是同一份時，不得收下")

    att = draft.get("completenessAttestation") or {}
    scanned = set(att.get("sectionsScanned") or [])
    known = set(request.section_titles)
    unknown = sorted(scanned - known)
    if unknown:
        raise DraftRejected(
            f"聲稱掃描過本文件沒有的章節：{unknown}——該聲明不可信")
    return draft


def draft_to_scoped(draft: dict, contract: dict, *, now: str | None = None) -> dict:
    """draft → scoped。判定一律交給既有的確定性 ScopeMatcher。

    先過 assert_scopable（既有的 lifecycle 與契約綁定檢查），再交給 matcher；
    本模組不自行判任何一項是否在範圍內。
    """
    inv.assert_scopable(draft, contract.get("scopeContractHash"))
    return ScopeMatcher(contract).scope_inventory(draft, now=now)


def read_sections(request: DraftRequest) -> dict:
    """接縫：把請求交給會讀論文的那一端，取回 draft 清冊。

    尚未接上。接上之後仍須經 ``validate_draft``——
    「模型回了東西」與「回的東西可以收」是兩件事。
    """
    raise ReadingSeamNotImplemented(
        "讀論文那一端尚未接上；接上後回傳之 draft 仍須經 validate_draft 驗收")
