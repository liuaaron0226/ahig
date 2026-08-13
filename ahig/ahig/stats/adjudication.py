#!/usr/bin/env python3
"""
分歧的確定性自動消解層

吞吐量模型顯示：欄位裁決佔人工工時 82%，且基準情境下要在 3 年內完成，
確定性層必須自動消解約 87% 的模型分歧。本模組實作可達成該目標的規則集。

原則：確定性層只在「有客觀依據可判定勝負」時裁決。無客觀依據時
必須回傳 ESCALATE，絕不猜測、絕不以計票處理數值矛盾。

裁決優先順序（契約 P0-3 第 4 節）：
  1. 確定性驗證器
  2. 第三盲審模型（僅限已校準的非數值型分歧）
  3. 人類裁決者
  4. UNRESOLVED
本模組只實作第 1 層。

v2.1 修正（issue 05）：

* **coverage 與 accuracy 分離。** coverage 是「分歧中由確定性規則處理的比例」，
  是產能指標；accuracy 只能對照 gold answer 量測。沒有 gold set 時，
  本模組不產生任何 accuracy 數字。兩位盲審者犯同一個錯時 agreement 看不到，
  只有 gold 抓得到，因此 NO_CONFLICT 也必須進入 gold 評估。
* **anchor 只能定位，不能替數值背書。** 逐字 anchor 證明「原文某處有這串字」，
  不證明「這個數字是這個 estimand 在這個時間點的值」。數值欄位一律要求重算依據；
  非數值欄位的 anchor 也必須帶 verifiedBinding（source hash ＋
  field/outcome/timepoint/arm/analysisSet）才可作為定位證據。
* **crude 2x2 不得打敗校正估計。** 由事件數重算出的是未校正效果量；
  報告值若來自校正模型、或 estimand／analysisSet 與 2x2 不一致，
  此依據不可採信，必須升級而非誤判。
* **null 有兩種。** 「原文未報告」是實質主張，「我找不到」是能力不足，
  兩者不可混為一談，也不得由未宣告狀態走寬鬆路徑。
* **規則遮蔽修正。** anchor 規則原本排在 null 與 schema 規則之前，
  使後兩者永遠不可達。
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Optional

from ahig.stats import deterministic as ds

AUTO_RESOLVED, ESCALATE, NO_CONFLICT = "AUTO_RESOLVED", "ESCALATE", "NO_CONFLICT"

# --- null 狀態 -------------------------------------------------------------
# 「原文沒有報告這個量」與「我在原文中定位不到」是兩件不同的事。
# 前者是可被 gold 驗證的實質主張，後者是抽取者的能力聲明。
NOT_REPORTED = "NOT_REPORTED"
CANNOT_LOCATE = "CANNOT_LOCATE"
NULL_STATE_UNDECLARED = "NULL_STATE_UNDECLARED"
DECLARED_NULL_STATES = {NOT_REPORTED, CANNOT_LOCATE}

# --- gold 評估的狀態碼 -----------------------------------------------------
CORRECT, WRONG, ESCALATED, NOT_EVALUABLE = (
    "CORRECT", "WRONG", "ESCALATED", "NOT_EVALUABLE")
BOTH_AGREED = "both-agreed"
DISAGREED_AUTO = "disagreed-auto-resolved"
DISAGREED_ESCALATED = "disagreed-escalated"
MAJOR, MINOR = "major", "minor"

# 名稱本身即帶數值語意的欄位。用於嚴重度分級與 anchor 禁用判定，
# 不取代以值型別為準的判斷，兩者取聯集。
NUMERIC_FIELDS = {
    "pointEstimate", "ciLow", "ciHigh", "pValue", "sampleSize", "n",
    "events", "mean", "sd", "se", "median", "iqrLow", "iqrHigh",
    "testStatistic", "df1", "df2", "dose",
}

# verifiedBinding 的必要欄位。缺一即不足以證明「這段文字就是這個欄位」。
REQUIRED_BINDING_KEYS = ("sourceHash", "field", "outcome", "timepoint",
                         "arm", "analysisSet")
_SOURCE_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

COVERAGE_NOTE = (
    "deterministicResolutionCoverage 是產能指標：分歧中由確定性規則處理的比例。"
    "coverage 不是正確率；正確率只能對照 gold answer 量測。"
)


@dataclass
class Adjudication:
    field: str
    outcome: str
    winner: Optional[str]          # 'A' | 'B' | None
    value: Any
    rule_id: str
    rationale: str
    escalate_to: Optional[str] = None   # 'third-model' | 'human-self' | 'human-expert'
    evidence: dict = dc_field(default_factory=dict)

    def to_json(self):
        return {"field": self.field, "outcome": self.outcome, "winner": self.winner,
                "value": self.value, "ruleId": self.rule_id,
                "rationale": self.rationale, "escalateTo": self.escalate_to,
                "evidence": self.evidence}


# ---------------------------------------------------------------------------
# 正規化
# ---------------------------------------------------------------------------

def norm_text(s: Any) -> str:
    """比較用的正規化形式（含小寫化）。不可作為要保留的值。"""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"[\s ]+", " ", s).strip().lower()
    s = re.sub(r"[‐‑‒–—―]", "-", s)
    return s


def norm_surface(s: Any) -> str:
    """保留大小寫的表面正規化：NFKC ＋ 空白摺疊 ＋ 連字號正規化。

    ADJ-001 要提交的是這個形式，不是 norm_text 的小寫結果 ——
    小寫化會破壞專有名詞與量表縮寫（ITT、VO2max、Borg）。
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"[\s ]+", " ", s).strip()
    return re.sub(r"[‐‑‒–—―]", "-", s)


def canonical_surface(*forms: Any) -> str:
    """由多個等價表面形式選出唯一 canonical 值，與 A/B 順序無關。

    偏好保留大小寫資訊的形式；完全同級時取排序第一者。
    """
    uniq = sorted({norm_surface(f) for f in forms if f is not None})
    if not uniq:
        return ""
    informative = [f for f in uniq if f != f.lower()]
    return (informative or uniq)[0]


ENUM_SYNONYMS = {
    "analysisSet": {
        "itt": "ITT", "intention-to-treat": "ITT", "intention to treat": "ITT",
        "full analysis set": "ITT", "fas": "ITT",
        "mitt": "mITT", "modified itt": "mITT", "modified intention-to-treat": "mITT",
        "pp": "PP", "per-protocol": "PP", "per protocol": "PP",
        "at": "AT", "as-treated": "AT", "as treated": "AT",
        "complete case": "complete-case", "completers": "complete-case",
    },
    "effectMeasure": {
        "risk ratio": "RR", "relative risk": "RR", "rr": "RR",
        "odds ratio": "OR", "or": "OR",
        "hazard ratio": "HR", "hr": "HR",
        "risk difference": "RD", "rd": "RD", "absolute risk difference": "RD",
        "mean difference": "MD", "md": "MD",
        "standardised mean difference": "SMD", "standardized mean difference": "SMD",
        "smd": "SMD", "cohen's d": "SMD", "hedges' g": "SMD",
    },
    "studyDesign": {
        "randomised controlled trial": "RCT-parallel",
        "randomized controlled trial": "RCT-parallel",
        "parallel rct": "RCT-parallel", "rct": "RCT-parallel",
        "crossover trial": "RCT-crossover", "cross-over rct": "RCT-crossover",
        "cluster randomised trial": "RCT-cluster",
        "prospective cohort": "cohort-prospective",
        "retrospective cohort": "cohort-retrospective",
    },
}


def canonical_enum(field: str, value: Any) -> Optional[str]:
    table = ENUM_SYNONYMS.get(field)
    if not table:
        return None
    n = norm_text(value)
    if n in table:
        return table[n]
    # 值本身已是 canonical
    if str(value) in set(table.values()):
        return str(value)
    return None


# ---------------------------------------------------------------------------
# 量綱註冊表
# ---------------------------------------------------------------------------

_REGISTRY_DIR = Path(__file__).resolve().parents[2] / "registry"
_REGISTRY_GLOB = "quantity-kinds.*.json"
_REGISTRY_CACHE: Optional[dict] = None


class QuantityKindCollision(ValueError):
    """兩個註冊表檔宣告了同一個 quantityKindId。

    靜默讓後載入者覆蓋前者，會使 blockingConditions 取決於檔名排序——
    那是最難察覺的一種閘門失效，所以這裡直接拋出。
    """


def _registry() -> dict:
    """合併 registry/ 下所有量綱註冊表為單一命名空間。

    領域註冊表會持續增加（B.11、之後的 B.14 …），但裁決層必須只有一個
    查表入口；分檔是編輯上的方便，不是語意上的隔離。
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE

    merged: dict[str, dict] = {}
    origin: dict[str, str] = {}
    for path in sorted(_REGISTRY_DIR.glob(_REGISTRY_GLOB)):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for entry in doc.get("entries", []):
            qk_id = entry.get("quantityKindId")
            if not qk_id:
                continue
            if qk_id in merged:
                raise QuantityKindCollision(
                    f"{qk_id} 同時定義於 {origin[qk_id]} 與 {path.name}")
            merged[qk_id] = entry
            origin[qk_id] = path.name
    _REGISTRY_CACHE = merged
    return _REGISTRY_CACHE


def quantity_kind_entry(quantity_kind_id: Optional[str]) -> Optional[dict]:
    """取得註冊表項目。未登錄的量綱回傳 None —— 呼叫端不得自行猜測。"""
    if not quantity_kind_id:
        return None
    return _registry().get(quantity_kind_id)


# ---------------------------------------------------------------------------
# 單位換算（僅限已宣告可換算者）
# ---------------------------------------------------------------------------

DECLARED_CONVERSIONS = {
    ("mg", "g"): 0.001, ("g", "mg"): 1000.0,
    ("kg", "g"): 1000.0, ("g", "kg"): 0.001,
    ("min", "s"): 60.0, ("s", "min"): 1 / 60.0,
    ("h", "min"): 60.0, ("min", "h"): 1 / 60.0,
    ("wk", "d"): 7.0, ("d", "wk"): 1 / 7.0,
    ("cm", "m"): 0.01, ("m", "cm"): 100.0,
    ("mm", "cm"): 0.1, ("cm", "mm"): 10.0,
}

# 每個已宣告換算族的 canonical 單位。用於讓 ADJ-003 的輸出與 A/B 順序無關。
FAMILY_CANONICAL_UNIT = {
    "mg": "g", "g": "g", "kg": "g",
    "s": "min", "min": "min", "h": "min",
    "d": "d", "wk": "d",
    "mm": "cm", "cm": "cm", "m": "cm",
}

# 出現這些字元即視為複合／導出單位。複合換算牽涉多個量綱的對齊
# （例如 mg/(kg.d) 需要體重與時間基準一致），不得由單位字串推導。
_COMPOSITE_UNIT_CHARS = set("/().*^·")


def is_composite_unit(unit: Optional[str]) -> bool:
    return bool(unit) and any(ch in _COMPOSITE_UNIT_CHARS for ch in str(unit))


def same_after_conversion(v1: float, u1: str, v2: float, u2: str,
                          rel_tol: float = 1e-6) -> bool:
    if u1 == u2:
        return math.isclose(v1, v2, rel_tol=rel_tol)
    f = DECLARED_CONVERSIONS.get((u1, u2))
    if f is None:
        return False
    return math.isclose(v1 * f, v2, rel_tol=rel_tol)


def convert_to(value: float, unit: str, target: str) -> Optional[float]:
    if unit == target:
        return float(value)
    f = DECLARED_CONVERSIONS.get((unit, target))
    return None if f is None else float(value) * f


def _canonical_unit(unit_a: str, unit_b: str, qk_entry: Optional[dict]
                    ) -> Optional[str]:
    """canonical 單位優先取註冊表宣告的 UCUM code，其次取換算族的代表單位。"""
    if qk_entry:
        rep = qk_entry.get("representation", {})
        code = rep.get("ucumCode")
        if code and (code == unit_a or code == unit_b
                     or (unit_a, code) in DECLARED_CONVERSIONS
                     or (unit_b, code) in DECLARED_CONVERSIONS):
            return code
    fam_a = FAMILY_CANONICAL_UNIT.get(unit_a)
    fam_b = FAMILY_CANONICAL_UNIT.get(unit_b)
    return fam_a if fam_a and fam_a == fam_b else None


# ---------------------------------------------------------------------------
# verifiedBinding：anchor 之所以能定位的條件
# ---------------------------------------------------------------------------

def _binding_rejections(anchor: Optional[dict], field: str, ctx: dict) -> list:
    """回傳 anchor 不足以作為定位證據的理由清單；空清單代表合格。"""
    if not anchor:
        return ["anchor-absent"]
    b = anchor.get("verifiedBinding")
    if not b:
        return ["verified-binding-absent"]
    reasons = [f"binding-missing-{k}" for k in REQUIRED_BINDING_KEYS
               if b.get(k) in (None, "")]
    if reasons:
        return reasons
    if not _SOURCE_HASH_RE.match(str(b["sourceHash"])):
        return ["binding-source-hash-malformed"]
    if b["field"] != field:
        return ["binding-field-mismatch"]
    for key in ("outcome", "timepoint", "arm", "analysisSet"):
        expected = ctx.get(key)
        if expected is not None and b.get(key) != expected:
            reasons.append(f"binding-{key}-mismatch")
    return reasons


def _anchor_strength(anchor: Optional[dict]) -> int:
    """0 無 anchor / 1 fuzzy 或多重命中 / 2 normalized-exact 唯一 / 3 exact 唯一"""
    if not anchor:
        return 0
    method = anchor.get("anchorMethod")
    unique = anchor.get("uniqueMatch", False)
    if not unique:
        return 1 if method else 0
    return {"exact": 3, "normalized-exact": 2, "fuzzy-accepted": 1,
            "manual-required": 1, "unresolved-anchor": 0}.get(method, 0)


def _verified_strength(payload: dict, field: str, ctx: dict) -> tuple:
    """(有效強度, 拒絕理由)。binding 不合格者強度一律歸零。"""
    anchor = payload.get("anchor")
    reasons = _binding_rejections(anchor, field, ctx)
    return (0 if reasons else _anchor_strength(anchor)), reasons


# ---------------------------------------------------------------------------
# null 狀態
# ---------------------------------------------------------------------------

def null_state(payload: dict) -> Optional[str]:
    """有值時回傳 None；無值時回傳宣告的 null 狀態或 NULL_STATE_UNDECLARED。"""
    if payload.get("value") is not None:
        return None
    state = payload.get("nullState")
    return state if state in DECLARED_NULL_STATES else NULL_STATE_UNDECLARED


def _is_numeric(*values) -> bool:
    return any(isinstance(v, (int, float)) and not isinstance(v, bool)
               for v in values)


def _numeric_field(field: str, va: Any, vb: Any) -> bool:
    return field in NUMERIC_FIELDS or _is_numeric(va, vb)


# ---------------------------------------------------------------------------
# 規則
# ---------------------------------------------------------------------------

def adjudicate_field(field: str, a: dict, b: dict, context: dict) -> Adjudication:
    """a / b 為兩位盲審者的輸出：{'value':..., 'unit':..., 'anchor':...}

    context 提供可用於客觀判定的事實，例如 2x2 表、CI、樣本數等。
    """
    ctx = context or {}
    va, vb = a.get("value"), b.get("value")
    na, nb = null_state(a), null_state(b)
    numeric_field = _numeric_field(field, va, vb)

    # R0 —— 無分歧。兩方皆缺值時，null 狀態相同才算一致。
    if va is None and vb is None:
        if na == nb:
            return Adjudication(field, NO_CONFLICT, None, None,
                                "ADJ-000-identical",
                                f"兩方皆無值且 null 狀態相同（{na}）",
                                evidence={"nullState": na})
        return Adjudication(
            field, ESCALATE, None, None, "ADJ-006c-null-state-contradiction",
            f"兩方皆無值但狀態不同：A={na}、B={nb}。"
            "『原文未報告』與『定位不到』不可互相抵銷",
            escalate_to=("human-expert" if numeric_field else "human-self"),
            evidence={"nullState": {"A": na, "B": nb}})
    if va == vb:
        return Adjudication(field, NO_CONFLICT, None, va, "ADJ-000-identical",
                            "兩方相同")

    # R-null —— 恰有一方缺值。必須先於 anchor 規則，否則永遠不可達。
    if (va is None) != (vb is None):
        return _resolve_null_vs_value(field, a, b, ctx, na, nb, numeric_field)

    # R1 —— 文字正規化後相同。提交保留大小寫的 canonical 表面形式。
    if isinstance(va, str) and isinstance(vb, str) and norm_text(va) == norm_text(vb):
        return Adjudication(field, AUTO_RESOLVED, None, canonical_surface(va, vb),
                            "ADJ-001-text-normalisation",
                            "NFKC + 空白摺疊 + 連字號正規化後相同；"
                            "提交保留大小寫的 canonical 形式")

    # R2 —— 列舉同義詞映射後相同
    ca, cb = canonical_enum(field, va), canonical_enum(field, vb)
    if ca and cb and ca == cb:
        return Adjudication(field, AUTO_RESOLVED, None, ca,
                            "ADJ-002-enum-synonym", f"兩方映射到同一 canonical 值 {ca}")

    # R3 —— 單位換算
    if a.get("unit") and b.get("unit") and _is_numeric(va) and _is_numeric(vb) \
            and a["unit"] != b["unit"]:
        res = _resolve_by_unit_conversion(field, a, b, ctx)
        if res:
            return res

    # R4 —— 數值分歧：以確定性統計檢查判勝負
    if field in {"pointEstimate", "ciLow", "ciHigh", "pValue"} and ctx:
        res = _resolve_numeric_by_recomputation(field, a, b, ctx)
        if res:
            return res

    # R7 —— schema 違規：一方的值不在允許列舉內。
    # 必須先於 anchor 規則：schema 是硬事實，anchor 只是定位證據。
    allowed = ctx.get("allowedValues", {}).get(field)
    if allowed:
        ok_a, ok_b = va in allowed, vb in allowed
        if ok_a != ok_b:
            winner, val = ("A", va) if ok_a else ("B", vb)
            return Adjudication(field, AUTO_RESOLVED, winner, val,
                                "ADJ-007-schema-violation",
                                "敗方的值不在 schema 允許列舉內")

    # R5 —— anchor 可驗證性。只用於非數值欄位的定位，且必須有 verifiedBinding。
    sa, rej_a = _verified_strength(a, field, ctx)
    sb, rej_b = _verified_strength(b, field, ctx)
    anchor_evidence = {"anchorStrength": {"A": sa, "B": sb},
                       "anchorRejections": {"A": rej_a, "B": rej_b}}
    if not numeric_field and sa != sb and max(sa, sb) >= 2:
        winner, val = ("A", va) if sa > sb else ("B", vb)
        return Adjudication(field, AUTO_RESOLVED, winner, val,
                            "ADJ-005-anchor-strength",
                            f"勝方 anchor 等級 {max(sa, sb)}（binding 已驗證），"
                            f"敗方 {min(sa, sb)}",
                            evidence=anchor_evidence)

    # 無客觀依據 —— 升級。數值分歧不得送第三模型，也不得以任何形式計票。
    if numeric_field:
        anchor_evidence["anchorAdmissible"] = False
        anchor_evidence["anchorNote"] = (
            "數值欄位不得由 anchor 強度單獨裁決：逐字命中只證明原文出現該字串，"
            "不證明它就是這個 estimand 在這個時間點的值")
    return Adjudication(field, ESCALATE, None, None, "ADJ-999-no-deterministic-basis",
                        "無客觀依據可判定，禁止以計票方式決定",
                        escalate_to=("human-expert" if numeric_field
                                     else "third-model"),
                        evidence=anchor_evidence)


# ---------------------------------------------------------------------------
# null 對有值
# ---------------------------------------------------------------------------

def _resolve_null_vs_value(field: str, a: dict, b: dict, ctx: dict,
                           na: Optional[str], nb: Optional[str],
                           numeric_field: bool) -> Adjudication:
    present_side = "A" if b.get("value") is None else "B"
    present = a if present_side == "A" else b
    state = nb if present_side == "A" else na

    if state == NOT_REPORTED:
        return Adjudication(
            field, ESCALATE, None, None, "ADJ-006c-null-state-contradiction",
            f"一方主張原文未報告（{NOT_REPORTED}），另一方卻提交了值。"
            "這是對原文內容的實質矛盾，不是定位能力差異",
            escalate_to=("human-expert" if numeric_field else "human-self"),
            evidence={"nullState": state, "presentSide": present_side})

    if state == NULL_STATE_UNDECLARED:
        return Adjudication(
            field, ESCALATE, None, None, "ADJ-006b-null-unanchored",
            f"一方缺值但未宣告 null 狀態（{NULL_STATE_UNDECLARED}），"
            "無法區分『原文未報告』與『定位不到』",
            escalate_to="human-self",
            evidence={"nullState": state, "presentSide": present_side})

    # CANNOT_LOCATE：對方只是找不到，有值的一方若能被獨立佐證即可採用。
    if numeric_field:
        corroborated, detail = _recomputation_corroborates(field, present, ctx)
        if corroborated:
            return Adjudication(
                field, AUTO_RESOLVED, present_side, present.get("value"),
                "ADJ-006-null-vs-anchored",
                f"一方宣告 {CANNOT_LOCATE}，另一方的數值通過獨立重算 {detail}",
                evidence={"nullState": state, "recomputation": detail})
        return Adjudication(
            field, ESCALATE, None, None, "ADJ-006b-null-unanchored",
            f"一方宣告 {CANNOT_LOCATE}，但另一方的數值沒有重算依據可佐證；"
            "數值不得僅憑 anchor 採用",
            escalate_to="human-self",
            evidence={"nullState": state, "recomputation": detail})

    strength, rejections = _verified_strength(present, field, ctx)
    if strength >= 2:
        return Adjudication(
            field, AUTO_RESOLVED, present_side, present.get("value"),
            "ADJ-006-null-vs-anchored",
            f"一方宣告 {CANNOT_LOCATE}，另一方有 binding 已驗證的逐字 anchor",
            evidence={"nullState": state, "anchorStrength": strength})
    return Adjudication(
        field, ESCALATE, None, None, "ADJ-006b-null-unanchored",
        f"一方宣告 {CANNOT_LOCATE}，但另一方 anchor 不足以佐證",
        escalate_to="human-self",
        evidence={"nullState": state, "anchorRejections": rejections})


# ---------------------------------------------------------------------------
# 單位換算裁決
# ---------------------------------------------------------------------------

def _resolve_by_unit_conversion(field: str, a: dict, b: dict,
                                ctx: dict) -> Optional[Adjudication]:
    ua, ub = a["unit"], b["unit"]
    qk_id = (ctx.get("quantityKinds") or {}).get(field)
    entry = quantity_kind_entry(qk_id)

    blocked = _comparability_block(entry, a, b, ctx)
    if blocked:
        return Adjudication(
            field, ESCALATE, None, None, "ADJ-003b-comparability-blocked",
            f"量綱 {qk_id} 的可比性條件不成立：{blocked}",
            escalate_to="human-expert",
            evidence={"quantityKindId": qk_id, "blockedBy": blocked})

    if is_composite_unit(ua) or is_composite_unit(ub):
        if (ua, ub) not in DECLARED_CONVERSIONS:
            return Adjudication(
                field, ESCALATE, None, None,
                "ADJ-003c-undeclared-composite-conversion",
                f"{ua} 與 {ub} 是複合／導出單位且無已宣告的換算規則；"
                "複合換算需對齊各分量的基準，不得由單位字串推導",
                escalate_to="human-expert",
                evidence={"units": [ua, ub]})

    if not same_after_conversion(a["value"], ua, b["value"], ub):
        return None

    canon = _canonical_unit(ua, ub, entry)
    if canon is None:
        return None
    converted = convert_to(a["value"], ua, canon)
    if converted is None:
        converted = convert_to(b["value"], ub, canon)
    if converted is None:
        return None
    return Adjudication(
        field, AUTO_RESOLVED, None, {"value": round(converted, 12), "unit": canon},
        "ADJ-003-unit-conversion",
        f"{a['value']}{ua} 與 {b['value']}{ub} 依已宣告換算表同值；"
        f"提交 canonical 單位 {canon}",
        evidence={"quantityKindId": qk_id, "canonicalUnit": canon,
                  "reported": {"A": [a["value"], ua], "B": [b["value"], ub]}})


def _comparability_block(entry: Optional[dict], a: dict, b: dict,
                         ctx: dict) -> Optional[str]:
    if not entry:
        return None
    comp = entry.get("crossStudyComparability", {})
    level = comp.get("level")
    if level in {"not-comparable", "comparable-only-as-SMD"}:
        return f"crossStudyComparability level = {level}"
    declared = set(ctx.get("declaredConditions") or [])
    hit = sorted(declared & set(comp.get("blockingConditions") or []))
    if hit:
        return f"blockingConditions 命中 {hit}"
    if entry.get("requiresInstrumentMatch"):
        for key in ("instrument", "method"):
            xa, xb = a.get(key), b.get(key)
            if xa is not None and xb is not None and norm_text(xa) != norm_text(xb):
                return f"requiresInstrumentMatch 但 {key} 不同（{xa} vs {xb}）"
    return None


# ---------------------------------------------------------------------------
# 數值重算裁決
# ---------------------------------------------------------------------------

def _crude_2x2_admissible(ctx: dict) -> tuple:
    """由事件數重算得到的是 **未校正** 效果量。

    只有在報告值本身也是未校正、且 estimand / analysisSet / 模型與 2x2 一致時，
    這個依據才可用來判定勝負。否則校正估計會被 crude 值誤判為錯誤。
    """
    table = ctx.get("twoByTwo") or {}
    model = ctx.get("statisticalModel")
    if model is not None and norm_text(model) not in {"unadjusted", "crude",
                                                      "unadjusted-primary"}:
        return False, f"報告值來自 {model} 模型，crude 2x2 只重算未校正效果量"
    for key in ("analysisSet", "estimand", "statisticalModel"):
        declared, in_table = ctx.get(key), table.get(key)
        if declared is not None and in_table is not None \
                and norm_text(declared) != norm_text(in_table):
            return False, f"{key} 與 2x2 不一致（{declared} vs {in_table}）"
    return True, None


def _side_checks(field: str, payload: dict, ctx: dict, use_2x2: bool) -> dict:
    measure = ctx.get("effectMeasure")
    cand = {**(ctx.get("baseStudyResult") or {}), field: payload.get("value")}
    checks = []

    if use_2x2 and ctx.get("twoByTwo") and measure in {"RR", "OR", "RD"} \
            and cand.get("pointEstimate") is not None:
        t = ctx["twoByTwo"]
        checks.append(ds.check_effect_vs_2x2(measure, cand["pointEstimate"],
                                             t["a"], t["n1"], t["c"], t["n2"]))
    if all(cand.get(k) is not None for k in ("pointEstimate", "ciLow", "ciHigh")) \
            and measure:
        checks.append(ds.check_ci_symmetry(cand["pointEstimate"], cand["ciLow"],
                                           cand["ciHigh"], measure))
        if cand.get("pValue") is not None:
            checks.append(ds.check_p_vs_ci(cand["pointEstimate"], cand["ciLow"],
                                           cand["ciHigh"], measure, cand["pValue"]))
            checks.append(ds.check_significance_coherence(
                cand["ciLow"], cand["ciHigh"], measure, cand["pValue"]))
    if ctx.get("testStatistic") and cand.get("pValue") is not None:
        t = ctx["testStatistic"]
        checks.append(ds.check_test_statistic_p(t["type"], t["value"],
                                                cand["pValue"], t.get("df1"),
                                                t.get("df2")))
    return {"fails": [c.rule_id for c in checks if c.verdict == ds.FAIL],
            "passes": [c.rule_id for c in checks if c.verdict == ds.PASS]}


def _decide_by_checks(field: str, a: dict, b: dict, ctx: dict,
                      use_2x2: bool) -> Optional[Adjudication]:
    results = {"A": _side_checks(field, a, ctx, use_2x2),
               "B": _side_checks(field, b, ctx, use_2x2)}
    fa, fb = len(results["A"]["fails"]), len(results["B"]["fails"])
    pa, pb = len(results["A"]["passes"]), len(results["B"]["passes"])
    if not (pa or pb or fa or fb):
        return None
    if fa == 0 and fb > 0 and pa > 0:
        return Adjudication(field, AUTO_RESOLVED, "A", a.get("value"),
                            "ADJ-004-numeric-recomputation",
                            f"B 的值違反 {results['B']['fails']}，"
                            f"A 通過 {results['A']['passes']}",
                            evidence={"checks": results, "crude2x2Used": use_2x2})
    if fb == 0 and fa > 0 and pb > 0:
        return Adjudication(field, AUTO_RESOLVED, "B", b.get("value"),
                            "ADJ-004-numeric-recomputation",
                            f"A 的值違反 {results['A']['fails']}，"
                            f"B 通過 {results['B']['passes']}",
                            evidence={"checks": results, "crude2x2Used": use_2x2})
    if fa > 0 and fb > 0:
        return Adjudication(field, ESCALATE, None, None,
                            "ADJ-004b-both-fail-recomputation",
                            f"兩方皆有數學矛盾（A:{results['A']['fails']}, "
                            f"B:{results['B']['fails']}）—— 可能是原文本身有誤",
                            escalate_to="human-expert",
                            evidence={"checks": results})
    return None


def _resolve_numeric_by_recomputation(field: str, a: dict, b: dict,
                                      ctx: dict) -> Optional[Adjudication]:
    """以獨立可算的事實判定哪一方的數值自洽。

    只有當一方通過而另一方失敗時才自動裁決；兩方皆通過或皆失敗一律升級。
    crude 2x2 不可採信時先排除該依據，若排除後仍可由 CI/p 判定就照常裁決；
    唯有「非靠 2x2 不可」時才因不可採信而升級。
    """
    admissible, reason = _crude_2x2_admissible(ctx)
    res = _decide_by_checks(field, a, b, ctx, use_2x2=admissible)
    if res:
        return res
    if not admissible and ctx.get("twoByTwo"):
        hypothetical = _decide_by_checks(field, a, b, ctx, use_2x2=True)
        if hypothetical:
            return Adjudication(
                field, ESCALATE, None, None, "ADJ-004c-crude-2x2-inadmissible",
                f"唯一可判定的依據是由事件數重算的未校正效果量，但{reason}；"
                "校正估計不得被 crude 2x2 打敗",
                escalate_to="human-expert",
                evidence={"inadmissibleReason": reason,
                          "wouldHaveDecided": hypothetical.rule_id})
    return None


def _recomputation_corroborates(field: str, payload: dict, ctx: dict) -> tuple:
    """單側佐證：該值在可算的檢查下無矛盾且至少通過一項。"""
    admissible, reason = _crude_2x2_admissible(ctx)
    res = _side_checks(field, payload, ctx, use_2x2=admissible)
    ok = bool(res["passes"]) and not res["fails"]
    detail = {"passes": res["passes"], "fails": res["fails"],
              "crude2x2Used": admissible}
    if not admissible:
        detail["crude2x2Excluded"] = reason
    return ok, detail


# ---------------------------------------------------------------------------
# 記錄層：coverage / gold accuracy / major-error 分離
# ---------------------------------------------------------------------------

def _gold_matches(committed: Any, expected: Any) -> bool:
    if isinstance(committed, dict) and "value" in committed:
        if isinstance(expected, dict) and "value" in expected:
            return (_gold_matches(committed["value"], expected["value"])
                    and committed.get("unit") == expected.get("unit"))
        return _gold_matches(committed["value"], expected)
    if committed is None or expected is None:
        return committed is expected
    if _is_numeric(committed) and _is_numeric(expected):
        return math.isclose(float(committed), float(expected), rel_tol=1e-9,
                            abs_tol=1e-12)
    return norm_text(committed) == norm_text(expected)


def _severity(field: str, committed: Any, gold_entry: dict) -> str:
    declared = gold_entry.get("severity")
    if declared in {MAJOR, MINOR}:
        return declared
    expected = gold_entry.get("value")
    inner = committed.get("value") if isinstance(committed, dict) else committed
    return MAJOR if _numeric_field(field, inner, expected) else MINOR


def evaluate_against_gold(adjudications: list, gold: Optional[dict]) -> Optional[dict]:
    """對照 gold answer 量測正確率。沒有 gold 就回傳 None —— 不得憑空生出數字。

    共同錯誤（兩位盲審者一致但都錯）在 agreement 指標上完全不可見，
    因此 NO_CONFLICT 也必須進入評估。
    """
    if not gold:
        return None

    by_field, major_errors = {}, []
    n_correct = n_wrong = n_escalated = n_not_evaluable = 0
    shared_errors = 0
    auto_correct = auto_wrong = 0

    for adj_json in adjudications:
        f = adj_json["field"]
        outcome = adj_json["outcome"]
        agreement = (BOTH_AGREED if outcome == NO_CONFLICT else
                     DISAGREED_AUTO if outcome == AUTO_RESOLVED else
                     DISAGREED_ESCALATED)
        entry = gold.get(f)
        if entry is None:
            n_not_evaluable += 1
            by_field[f] = {"status": NOT_EVALUABLE, "agreementClass": agreement,
                           "note": "gold set 未涵蓋此欄位"}
            continue
        if not isinstance(entry, dict):
            entry = {"value": entry}
        if outcome == ESCALATE:
            n_escalated += 1
            by_field[f] = {"status": ESCALATED, "agreementClass": agreement,
                           "note": "升級處理，未提交值，不計入正確率"}
            continue

        committed = adj_json["value"]
        ok = _gold_matches(committed, entry.get("value"))
        sev = None if ok else _severity(f, committed, entry)
        if ok:
            n_correct += 1
        else:
            n_wrong += 1
            if agreement == BOTH_AGREED:
                shared_errors += 1
            if sev == MAJOR:
                major_errors.append({"field": f, "committedValue": committed,
                                     "goldValue": entry.get("value"),
                                     "agreementClass": agreement})
        if outcome == AUTO_RESOLVED:
            auto_correct += 1 if ok else 0
            auto_wrong += 0 if ok else 1
        by_field[f] = {"status": CORRECT if ok else WRONG,
                       "agreementClass": agreement, "severity": sev,
                       "committedValue": committed, "goldValue": entry.get("value")}

    n_committed = n_correct + n_wrong
    n_auto = auto_correct + auto_wrong
    minor_errors = n_wrong - len(major_errors)
    return {
        "deterministicResolutionAccuracy": (auto_correct / n_auto) if n_auto else None,
        "committedValueAccuracy": (n_correct / n_committed) if n_committed else None,
        "nAdjudicatedWithGold": n_auto,
        "nCommitted": n_committed,
        "nCorrect": n_correct,
        "nWrong": n_wrong,
        "nEscalated": n_escalated,
        "nNotEvaluable": n_not_evaluable,
        "sharedErrorCount": shared_errors,
        "majorErrorCount": len(major_errors),
        "minorErrorCount": minor_errors,
        "majorErrors": major_errors,
        "byField": by_field,
        "note": "共同錯誤只有 gold 抓得到；agreement 對它完全盲目。",
    }


def adjudicate_record(fields: dict, context: Optional[dict] = None,
                      gold: Optional[dict] = None) -> dict:
    """fields: {fieldName: {'A': {...}, 'B': {...}}}

    gold: {fieldName: {'value': ..., 'severity': 'major'|'minor'}}，可省略。
    省略時輸出中不會出現任何 accuracy 數字。
    """
    context = context or {}
    out = [adjudicate_field(f, pair["A"], pair["B"], context).to_json()
           for f, pair in fields.items()]
    conflicts = [o for o in out if o["outcome"] != NO_CONFLICT]
    auto = [o for o in conflicts if o["outcome"] == AUTO_RESOLVED]
    esc = [o for o in conflicts if o["outcome"] == ESCALATE]
    coverage = (len(auto) / len(conflicts)) if conflicts else None

    return {
        "adjudications": out,
        "nFields": len(out),
        "nConflicts": len(conflicts),
        "nAutoResolved": len(auto),
        "nEscalated": len(esc),
        "autoResolutionRate": coverage,
        "escalatedToHuman": [o for o in esc if (o["escalateTo"] or "").startswith("human")],
        "escalatedToThirdModel": [o for o in esc if o["escalateTo"] == "third-model"],
        "metrics": {
            "coverage": {
                "nFields": len(out),
                "nConflicts": len(conflicts),
                "nAutoResolved": len(auto),
                "nEscalated": len(esc),
                "nNoConflict": len(out) - len(conflicts),
                "deterministicResolutionCoverage": coverage,
                "note": COVERAGE_NOTE,
            },
            "goldEvaluation": evaluate_against_gold(out, gold),
        },
    }
