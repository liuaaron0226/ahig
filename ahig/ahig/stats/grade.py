#!/usr/bin/env python3
"""
GRADE 的確定性指標層 (Gap E, v2.1)

## v2 的錯誤

v2 把「可計算」誤當成「可判定」：I² ≥ 75% 直接輸出 very-serious、
總事件數 < 300 直接降級、Egger p < 0.10 直接判 serious。那不是 GRADE。
GRADE 的 domain 評級是需要臨床脈絡的判斷，統計量只是輸入之一。
更嚴重的是 fail-open：k < 10、Egger 失敗、資料不足時 v2 回落
not-serious —— 「算不出來」被靜默翻譯成「沒問題」。

## v2.1 的分層

    確定性指標 (indicators)          ← 本模組計算，永遠不是 final
        ↓
    人類 domain judgement            ← 五個 domain 各一筆，必須留痕
        ↓
    確定性聚合 (aggregate_certainty) ← 純規則，無自由度

三個可計算的 domain（inconsistency、imprecision、publication bias）
回傳 `DomainIndicators`：確定性指標 + suggested judgement +
`human_judgement_required`。suggested judgement 是建議，不是評級。

`aggregate_certainty()` 只接受五個具「生效」`HumanDomainJudgement` 的
domain。任一缺漏、任一由模型作出、任一為 indeterminate、任一未確認
必要旗標 —— 一律 block，不產出 effectiveCertainty。

一般風險主張可由 human-self 判斷；safety-critical 必須 human-expert
（契約 B.4，與 adjudicationLevel 的分層一致）。

模型 override 只寫入 `advisoryOverrides`，不動 effective domain 與
effectiveCertainty。人類 override 才進 `overrides` 並重算。
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

import numpy as np
from scipy import stats

NOT_SERIOUS, SERIOUS, VERY_SERIOUS = "not-serious", "serious", "very-serious"

#: 「指標不足以支撐任何方向的建議」。不是 GRADE 級別，不可進入聚合。
INDETERMINATE = "indeterminate"

DOWNGRADE = {NOT_SERIOUS: 0, SERIOUS: 1, VERY_SERIOUS: 2}
SUGGESTABLE = frozenset({NOT_SERIOUS, SERIOUS, VERY_SERIOUS, INDETERMINATE})

GRADE_DOMAINS = ("risk-of-bias", "inconsistency", "indirectness",
                 "imprecision", "publication-bias")

CERTAINTY_LADDER = ["very-low", "low", "moderate", "high"]

AGENT_CLASSES = frozenset({"human-expert", "human-self", "model"})

#: 各風險層可作出生效 domain judgement 的 agentClass。
RISK_TIER_JUDGEMENT_AGENTS: dict[str, frozenset[str]] = {
    "general-clinical": frozenset({"human-self", "human-expert"}),
    "safety-critical": frozenset({"human-expert"}),
}


# ---------------------------------------------------------------------------
# 資料結構
# ---------------------------------------------------------------------------

@dataclass
class DomainIndicators:
    """一個可計算 domain 的確定性指標。

    這**不是** domain rating。`suggested_judgement` 是給人類看的建議，
    採不採用由 `HumanDomainJudgement` 決定。
    """

    domain: str
    suggested_judgement: str
    rule_id: str
    rationale: str
    indicators: dict = field(default_factory=dict)
    flags: list = field(default_factory=list)
    #: 人類必須明確確認過的旗標，未確認則聚合階段 block。
    requires_acknowledgement: list = field(default_factory=list)
    human_judgement_required: bool = True

    def __post_init__(self):
        if self.suggested_judgement not in SUGGESTABLE:
            raise ValueError(f"未知的 suggested judgement：{self.suggested_judgement}")

    # -- 向後相容的唯讀別名 ------------------------------------------------
    # v2 的呼叫端讀 .proposed / .computed / .requires_human_confirmation。
    # 保留讀取路徑，但語意已改：proposed 是建議而非評級，因此只讀不寫。

    @property
    def proposed(self) -> str:
        return self.suggested_judgement

    @property
    def computed(self) -> dict:
        return self.indicators

    @property
    def requires_human_confirmation(self) -> bool:
        return self.human_judgement_required

    def to_json(self) -> dict:
        return {
            "domain": self.domain,
            "suggestedJudgement": self.suggested_judgement,
            "ruleId": self.rule_id,
            "rationale": self.rationale,
            "indicators": copy.deepcopy(self.indicators),
            "flags": list(self.flags),
            "requiresAcknowledgement": list(self.requires_acknowledgement),
            "humanJudgementRequired": self.human_judgement_required,
            "note": "indicators 不是 domain rating；final rating 由人類判斷產生。",
        }


#: v2 名稱。指向同一個型別，讓既有 isinstance / 型別註記不炸。
DomainRating = DomainIndicators


@dataclass
class HumanDomainJudgement:
    """人類對單一 GRADE domain 作出的評級。

    `acknowledged_flags` 必須涵蓋 indicators 的 `requires_acknowledgement`，
    否則聚合階段 block —— 「算不出來」不得被沉默略過。
    """

    domain: str
    rating: str
    agent_class: str
    rationale: str
    acknowledged_flags: list = field(default_factory=list)
    indicators: Optional[DomainIndicators] = None

    def to_json(self) -> dict:
        return {
            "domain": self.domain,
            "rating": self.rating,
            "agentClass": self.agent_class,
            "rationale": self.rationale,
            "acknowledgedFlags": list(self.acknowledged_flags),
            "hasIndicators": self.indicators is not None,
        }


# ---------------------------------------------------------------------------
# Inconsistency
# ---------------------------------------------------------------------------

def meta_analyse_dl(effects: Sequence[float], variances: Sequence[float]) -> dict:
    """DerSimonian–Laird 隨機效果模型。回傳 pooled estimate、tau2、I2、Q、預測區間。"""
    k = len(effects)
    if k < 2:
        raise ValueError("需要至少兩個研究")
    if len(variances) != k:
        raise ValueError("effects 與 variances 長度不符")
    if any(vi <= 0 for vi in variances):
        raise ValueError("變異數必須為正")
    y = list(effects)
    v = list(variances)
    w = [1 / vi for vi in v]
    fe = sum(wi * yi for wi, yi in zip(w, y)) / sum(w)
    Q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, y))
    df = k - 1
    c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    I2 = max(0.0, (Q - df) / Q) * 100 if Q > 0 else 0.0

    wr = [1 / (vi + tau2) for vi in v]
    pooled = sum(wi * yi for wi, yi in zip(wr, y)) / sum(wr)
    se_pooled = math.sqrt(1 / sum(wr))
    q_p = float(1 - stats.chi2.cdf(Q, df)) if df > 0 else float("nan")

    pi = None
    if k >= 3:
        t = float(stats.t.ppf(0.975, k - 2))
        half = t * math.sqrt(tau2 + se_pooled ** 2)
        pi = [pooled - half, pooled + half]

    return {"k": k, "pooled": pooled, "se_pooled": se_pooled,
            "ci": [pooled - 1.96 * se_pooled, pooled + 1.96 * se_pooled],
            "Q": Q, "Q_df": df, "Q_p": q_p, "tau2": tau2, "I2": I2,
            "prediction_interval": pi}


def rate_inconsistency(effects: Sequence[float], variances: Sequence[float],
                       null_value: float = 0.0,
                       mid: Optional[float] = None) -> DomainIndicators:
    """計算 inconsistency 的確定性指標。

    回傳 indicators + suggested judgement。單一研究時 suggested judgement 是
    `indeterminate`（v2 回 not-serious，那是把「沒有異質性可評」誤讀成
    「沒有異質性問題」）。
    """
    if len(effects) < 2:
        return DomainIndicators(
            "inconsistency", INDETERMINATE, "GRADE-INC-000",
            "只有單一研究，無法評估研究間異質性。"
            "不得據此推論一致性良好；需人工以 single-study-evidence 處理。",
            indicators={"k": len(effects)},
            flags=["single-study-evidence"],
            requires_acknowledgement=["single-study-evidence"])

    ma = meta_analyse_dl(effects, variances)
    flags: list[str] = []
    ack: list[str] = []
    reasons: list[str] = []
    level = NOT_SERIOUS

    if ma["I2"] >= 75:
        level = VERY_SERIOUS
        reasons.append(f"I²={ma['I2']:.0f}% (>=75%)")
    elif ma["I2"] >= 50:
        level = SERIOUS
        reasons.append(f"I²={ma['I2']:.0f}% (50–75%)")
    else:
        reasons.append(f"I²={ma['I2']:.0f}% (<50%)")

    if not math.isnan(ma["Q_p"]) and ma["Q_p"] < 0.10:
        flags.append("cochran-Q-p<0.10")
        if level == NOT_SERIOUS:
            level = SERIOUS
            reasons.append(f"Cochran Q p={ma['Q_p']:.3f} < 0.10")

    # 預測區間只在確實存在研究間異質性 (tau2 > 0) 時才計入 inconsistency。
    # tau2 = 0 時預測區間變寬純粹來自小 k 的 t 乘數，那是 imprecision 的問題，
    # 在此降級會把同一個不確定性重複計算兩次。（v2 已修正，v2.1 保留。）
    pi = ma["prediction_interval"]
    if pi and ma["tau2"] > 0:
        if pi[0] < null_value < pi[1]:
            flags.append("prediction-interval-crosses-null")
            reasons.append("存在異質性且預測區間跨越虛無值：新研究的效果方向不確定")
            if level == NOT_SERIOUS:
                level = SERIOUS
        if mid is not None and pi[0] < -abs(mid) and pi[1] > abs(mid):
            flags.append("prediction-interval-spans-both-MIDs")
            level = VERY_SERIOUS if level == SERIOUS else level
            reasons.append("預測區間同時涵蓋雙向重要差異")
    elif pi:
        flags.append("prediction-interval-not-used-tau2-zero")
        reasons.append("tau²=0，預測區間寬度歸因於 imprecision 而非 inconsistency")

    # k < 3 時 I² 的估計不穩定，指標本身不可信 —— 不能給方向性建議。
    if ma["k"] < 3:
        flags.append("k<3-I2-unstable")
        ack.append("k<3-I2-unstable")
        level = INDETERMINATE
        reasons.append("研究數 <3，I² 估計不穩定，指標不足以支撐建議")

    return DomainIndicators("inconsistency", level, "GRADE-INC-001",
                            "；".join(reasons), ma, flags, ack)


# ---------------------------------------------------------------------------
# Imprecision
# ---------------------------------------------------------------------------

def optimal_information_size_binary(control_risk: float, rrr: float,
                                    alpha: float = 0.05, power: float = 0.80) -> float:
    """二元結果的 OIS（總樣本數，兩組等分）。"""
    p1 = control_risk
    p2 = control_risk * (1 - rrr)
    if not (0 < p1 < 1 and 0 < p2 < 1):
        raise ValueError("風險值須介於 0 與 1")
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    pbar = (p1 + p2) / 2
    n_per_arm = ((za * math.sqrt(2 * pbar * (1 - pbar))
                  + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
                 / (p1 - p2) ** 2)
    return 2 * n_per_arm


def optimal_information_size_continuous(mid: float, sd: float,
                                        alpha: float = 0.05,
                                        power: float = 0.80) -> float:
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    n_per_arm = 2 * ((za + zb) ** 2) * (sd ** 2) / (mid ** 2)
    return 2 * n_per_arm


def rate_imprecision(ci_low: float, ci_high: float, total_n: int,
                     null_value: float = 0.0,
                     mid: Optional[float] = None,
                     mid_status: str = "registered",
                     ois: Optional[float] = None,
                     total_events: Optional[int] = None) -> DomainIndicators:
    """計算 imprecision 的確定性指標。

    mid_status:
      registered  —— 來自 MIDRegistry 的 active 項目，可做 contextualised 判定
      provisional —— project-defined-provisional，可判定但不足以支撐 high
      unavailable —— 無 MID，只能以 OIS 與跨虛無值判定，且不得聲稱
                     contextualised；需人工說明

    `indicators["contextualised"]` 是 aggregate 階段判斷能否給 high 的依據。
    """
    if ci_low > ci_high:
        raise ValueError("ci_low 不得大於 ci_high")

    flags: list[str] = []
    ack: list[str] = []
    reasons: list[str] = []
    level = NOT_SERIOUS
    crosses_null = ci_low <= null_value <= ci_high
    contextualised = not (mid_status == "unavailable" or mid is None)
    indicators: dict[str, Any] = {
        "ci": [ci_low, ci_high], "total_n": total_n,
        "crosses_null": crosses_null, "mid_status": mid_status,
        "mid": mid, "contextualised": contextualised,
    }

    if not contextualised:
        flags.append("midUnavailable")
        ack.append("midUnavailable")
        reasons.append("無登錄 MID，imprecision 僅以 OIS 與虛無值判定，"
                       "不得聲稱已做 contextualised 評級")
        if crosses_null:
            level = SERIOUS
            reasons.append("CI 跨越虛無值")
    else:
        if mid_status == "provisional":
            flags.append("midProvisional")
        lo_imp = ci_low < (null_value - abs(mid))
        hi_imp = ci_high > (null_value + abs(mid))
        indicators["ci_spans_benefit_and_harm"] = bool(lo_imp and hi_imp)
        if lo_imp and hi_imp:
            level = VERY_SERIOUS
            reasons.append("CI 同時涵蓋重要獲益與重要傷害")
        elif crosses_null:
            level = SERIOUS
            reasons.append("CI 跨越虛無值但未同時涵蓋雙向重要差異")
        else:
            reasons.append("CI 未跨越虛無值且未涵蓋雙向重要差異")

    if ois is not None:
        indicators["ois"] = ois
        indicators["meets_ois"] = total_n >= ois
        if total_n < ois:
            reasons.append(f"總樣本數 {total_n} < OIS {ois:.0f}")
            flags.append("below-OIS")
            if level in DOWNGRADE:
                level = {NOT_SERIOUS: SERIOUS, SERIOUS: VERY_SERIOUS,
                         VERY_SERIOUS: VERY_SERIOUS}[level]
    else:
        flags.append("ois-not-computed")
        ack.append("ois-not-computed")
        reasons.append("未提供 OIS，無法完整判定 imprecision")

    # 既無 contextualised MID、也無 OIS —— 兩個判定依據全缺，指標不可信。
    # v2 在此回落 not-serious，那是最典型的 fail-open。
    if not contextualised and ois is None:
        level = INDETERMINATE
        reasons.append("MID 與 OIS 皆不可用，指標不足以支撐任何方向的建議")

    if total_events is not None:
        indicators["total_events"] = total_events
        if total_events < 300:
            flags.append("total-events<300")
            reasons.append(f"總事件數 {total_events} < 300（GRADE 經驗法則，"
                           f"是提示而非判準）")
            if level == NOT_SERIOUS:
                level = SERIOUS

    return DomainIndicators("imprecision", level, "GRADE-IMP-001",
                            "；".join(reasons), indicators, flags, ack)


# ---------------------------------------------------------------------------
# Publication bias
# ---------------------------------------------------------------------------

def eggers_test(effects: Sequence[float], se: Sequence[float]) -> dict:
    """Egger 迴歸截距檢定。以 precision 加權迴歸實作。

    設計上不吞例外：奇異矩陣、非正 SE、df <= 0 一律拋 ValueError，
    由呼叫端轉成 indeterminate。靜默回傳「無不對稱」是 fail-open。
    """
    k = len(effects)
    if len(se) != k:
        raise ValueError("effects 與 se 長度不符")
    if k < 3:
        raise ValueError("Egger 檢定需要至少 3 個研究")
    if any(s <= 0 for s in se):
        raise ValueError("標準誤必須為正")

    y = np.asarray(effects, dtype=float)
    s = np.asarray(se, dtype=float)
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(s))):
        raise ValueError("effects 或 se 含非有限值")

    snd = y / s                 # standard normal deviate
    prec = 1.0 / s              # precision
    if np.ptp(prec) == 0:
        raise ValueError("所有研究的 precision 相同，迴歸設計矩陣奇異")

    X = np.column_stack([np.ones(k), prec])
    if np.linalg.matrix_rank(X) < 2:
        raise ValueError("迴歸設計矩陣未達滿秩")

    beta, *_ = np.linalg.lstsq(X, snd, rcond=None)
    resid = snd - X @ beta
    dof = k - 2
    if dof <= 0:
        raise ValueError("自由度不足")
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.inv(X.T @ X)
    var_intercept = cov[0, 0]
    if not np.isfinite(var_intercept) or var_intercept <= 0:
        raise ValueError("截距變異數非正或非有限，檢定不可用")
    se_intercept = math.sqrt(var_intercept)
    t = beta[0] / se_intercept
    p = float(2 * (1 - stats.t.cdf(abs(t), dof)))
    if not math.isfinite(p):
        raise ValueError("p 值非有限")
    return {"intercept": float(beta[0]), "se_intercept": se_intercept,
            "t": float(t), "df": dof, "p": p, "slope": float(beta[1])}


def rate_publication_bias(effects: Sequence[float], se: Sequence[float],
                          all_registered_trials_reported: Optional[bool] = None,
                          small_study_share: Optional[float] = None
                          ) -> DomainIndicators:
    """計算 publication bias 的確定性指標。

    k < 10、Egger 奇異或失敗 —— 一律 `indeterminate` 並要求人工確認。
    v2 在這些情況回落 not-serious，等同「檢定不出來就當沒問題」。
    """
    k = len(effects)
    if len(se) != k:
        raise ValueError("effects 與 se 長度不符")

    flags: list[str] = []
    ack: list[str] = []
    reasons: list[str] = []
    indicators: dict[str, Any] = {"k": k}

    if all_registered_trials_reported is not None:
        indicators["all_registered_trials_reported"] = all_registered_trials_reported
        if all_registered_trials_reported is False:
            flags.append("known-unreported-registered-trials")
            reasons.append("已知有登錄但未發表的試驗")
    if small_study_share is not None:
        indicators["small_study_share"] = small_study_share
        if small_study_share > 0.5:
            flags.append("majority-small-studies")
            reasons.append("過半為小型研究，small-study effect 風險升高")

    if k < 10:
        flags.append("k<10-egger-not-applicable")
        ack.append("k<10-egger-not-applicable")
        reasons.append(f"研究數 {k} < 10，不執行 Egger 檢定"
                       "（漏斗圖不對稱檢定在小 k 下功效不足且易誤判）；"
                       "無法排除亦無法確認發表偏誤")
        return DomainIndicators("publication-bias", INDETERMINATE,
                                "GRADE-PB-000", "；".join(reasons),
                                indicators, flags, ack)

    try:
        eg = eggers_test(effects, se)
    except Exception as exc:  # noqa: BLE001 —— 任何失敗都不得靜默回落
        flags.append("egger-failed")
        ack.append("egger-failed")
        reasons.append(f"Egger 檢定無法執行：{exc}；統計檢定不可用，"
                       f"不得據此推論無發表偏誤")
        return DomainIndicators("publication-bias", INDETERMINATE,
                                "GRADE-PB-002", "；".join(reasons),
                                indicators, flags, ack)

    indicators["egger"] = eg
    level = NOT_SERIOUS
    if eg["p"] < 0.10:
        level = SERIOUS
        reasons.append(f"Egger 截距檢定 p={eg['p']:.3f} < 0.10，漏斗圖不對稱")
    else:
        reasons.append(f"Egger 截距檢定 p={eg['p']:.3f}，未見明顯不對稱")

    if all_registered_trials_reported is False:
        level = SERIOUS if level == NOT_SERIOUS else VERY_SERIOUS

    return DomainIndicators("publication-bias", level, "GRADE-PB-001",
                            "；".join(reasons), indicators, flags, ack)


# ---------------------------------------------------------------------------
# 聚合
# ---------------------------------------------------------------------------

def _blank_result(reasons: list[str], risk_tier: str) -> dict:
    return {
        "effectiveCertainty": None,
        "advisoryCertainty": None,
        "blocked": True,
        "blockReasons": reasons,
        "riskTier": risk_tier,
        "startingLevel": None,
        "totalDowngrade": None,
        "totalUpgrade": None,
        "perDomain": {},
        "perDomainJudgement": {},
        "contextualisedImprecision": None,
        "capReasons": [],
        "certaintyDerivation": None,
        "overrides": [],
        "advisoryOverrides": [],
        "ruleId": "GRADE-SUM-002",
        "note": "effectiveCertainty 只在五個 domain 都有生效人類判斷時產生。",
    }


def _validate_judgement(domain: str, j: Any, allowed_agents: frozenset[str]
                        ) -> list[str]:
    problems: list[str] = []
    if not isinstance(j, HumanDomainJudgement):
        return [f"{domain}：不是 HumanDomainJudgement（收到 {type(j).__name__}）；"
                f"裸的等級字串不構成人類判斷"]
    if j.domain != domain:
        problems.append(f"{domain}：judgement 的 domain 欄位為 {j.domain}，不相符")
    if j.rating not in DOWNGRADE:
        problems.append(f"{domain}：評級 {j.rating!r} 不是有效的 GRADE domain 等級"
                        f"（indeterminate 不得進入聚合）")
    if j.agent_class not in allowed_agents:
        problems.append(f"{domain}：agentClass={j.agent_class!r} 不足以作出生效判斷，"
                        f"需要 {sorted(allowed_agents)}")
    if not (j.rationale or "").strip():
        problems.append(f"{domain}：judgement 缺少理由")
    if j.indicators is not None:
        missing = [f for f in j.indicators.requires_acknowledgement
                   if f not in set(j.acknowledged_flags)]
        if missing:
            problems.append(f"{domain}：未確認必要旗標 {missing}")
    return problems


def aggregate_certainty(design: str,
                        judgements: Mapping[str, Any],
                        risk_tier: str,
                        upgrades: Optional[Mapping[str, Any]] = None) -> dict:
    """由五個生效的人類 domain judgement 聚合出 effectiveCertainty。

    這是純規則、無自由度的一步。缺任一 domain、任一由模型作出、任一為
    indeterminate、任一未確認必要旗標 —— 一律 block。

    risk_tier:
      general-clinical —— 可由 human-self 判斷
      safety-critical  —— 必須 human-expert
    """
    if risk_tier not in RISK_TIER_JUDGEMENT_AGENTS:
        raise ValueError(f"未知的 riskTier：{risk_tier!r}；"
                         f"可用值 {sorted(RISK_TIER_JUDGEMENT_AGENTS)}")
    allowed_agents = RISK_TIER_JUDGEMENT_AGENTS[risk_tier]

    problems: list[str] = []
    missing = [d for d in GRADE_DOMAINS if d not in judgements]
    if missing:
        problems.append(f"缺少 GRADE domain 的人類判斷：{missing}")
    extra = sorted(set(judgements) - set(GRADE_DOMAINS))
    if extra:
        problems.append(f"非 GRADE domain 的判斷：{extra}")

    for d in GRADE_DOMAINS:
        if d in judgements:
            problems.extend(_validate_judgement(d, judgements[d], allowed_agents))

    if problems:
        return _blank_result(problems, risk_tier)

    per_domain = {d: judgements[d].rating for d in GRADE_DOMAINS}
    total_down = sum(DOWNGRADE[per_domain[d]] for d in GRADE_DOMAINS)

    start = 3 if design.startswith("RCT") else 1     # high / low
    up = 0
    if upgrades and start == 1:
        up = min(sum(1 for v in upgrades.values() if v), 2)

    idx = max(0, min(3, start - total_down + up))

    # MID 狀態的上限：provisional 或 unavailable 都不足以支撐 high，
    # 但不硬鎖 low —— 降級只能來自實際的 domain judgement。
    imp = judgements["imprecision"].indicators
    cap_reasons: list[str] = []
    if imp is None:
        contextualised = None
        cap_reasons.append("imprecision 未附確定性指標，無法確認 MID 狀態，"
                           "不足以支撐 high")
    else:
        contextualised = bool(imp.indicators.get("contextualised"))
        if not contextualised:
            cap_reasons.append("imprecision 未做 contextualised 評級"
                               "（midUnavailable），不足以支撐 high")
        elif imp.indicators.get("mid_status") == "provisional":
            cap_reasons.append("MID 為 provisional（非文獻共識），不足以支撐 high")

    if cap_reasons:
        idx = min(idx, CERTAINTY_LADDER.index("moderate"))

    return {
        "effectiveCertainty": CERTAINTY_LADDER[idx],
        "advisoryCertainty": None,
        "blocked": False,
        "blockReasons": [],
        "riskTier": risk_tier,
        "startingLevel": CERTAINTY_LADDER[start],
        "totalDowngrade": total_down,
        "totalUpgrade": up,
        "perDomain": per_domain,
        "perDomainJudgement": {d: judgements[d].to_json() for d in GRADE_DOMAINS},
        "contextualisedImprecision": contextualised,
        "capReasons": cap_reasons,
        "certaintyDerivation": "deterministic-rule",
        "overrides": [],
        "advisoryOverrides": [],
        "ruleId": "GRADE-SUM-002",
        "note": "effectiveCertainty 由規則聚合生效的人類 domain judgement 得出；"
                "模型不得直接輸出 overall certainty。",
    }


def _recompute(result: dict) -> dict:
    """在 perDomain 改變後重算階梯位置與 MID 上限。"""
    total_down = sum(DOWNGRADE[v] for v in result["perDomain"].values())
    start = CERTAINTY_LADDER.index(result["startingLevel"])
    idx = max(0, min(3, start - total_down + (result["totalUpgrade"] or 0)))
    if result["capReasons"]:
        idx = min(idx, CERTAINTY_LADDER.index("moderate"))
    result["totalDowngrade"] = total_down
    result["effectiveCertainty"] = CERTAINTY_LADDER[idx]
    return result


def apply_override(proposal: dict, domain: str, new_level: str,
                   agent_class: str, rationale: str) -> dict:
    """記錄一筆 domain override。

    模型 override 與風險層不足的人類 override 只寫入 `advisoryOverrides`：
    不動 effective domain、不動 effectiveCertainty、不動 certaintyDerivation。
    合格的人類 override 才進 `overrides` 並重算。

    `proposal` 深拷貝後回傳新物件；原物件與其歷史不受影響。
    """
    if agent_class not in AGENT_CLASSES:
        raise ValueError(f"未知的 agentClass：{agent_class!r}")
    if domain not in GRADE_DOMAINS:
        raise ValueError(f"未知的 GRADE domain：{domain!r}")
    if new_level not in DOWNGRADE:
        raise ValueError(f"override 等級 {new_level!r} 不是有效的 GRADE domain 等級")
    if not (rationale or "").strip():
        raise ValueError("override 必須附理由")

    rec = copy.deepcopy(proposal)
    rec.setdefault("overrides", [])
    rec.setdefault("advisoryOverrides", [])

    entry = {
        "domain": domain,
        "from": (rec.get("perDomain") or {}).get(domain),
        "to": new_level,
        "agentClass": agent_class,
        "rationale": rationale,
    }

    allowed = RISK_TIER_JUDGEMENT_AGENTS.get(rec.get("riskTier"), frozenset())
    effective = (agent_class in allowed
                 and not rec.get("blocked", True)
                 and domain in (rec.get("perDomain") or {}))

    if effective:
        entry["effectiveForApprovedClaim"] = True
        rec["overrides"].append(entry)
        rec["perDomain"][domain] = new_level
        rec["certaintyDerivation"] = "deterministic-rule-with-logged-override"
        _recompute(rec)
        return rec

    # Advisory：計算「假如採納會變成什麼」，但只寫在 override 記錄裡。
    entry["effectiveForApprovedClaim"] = False
    if agent_class == "model":
        entry["reason"] = "模型 override 不生效於 Approved Claim，僅供人類參考"
    elif rec.get("blocked", True):
        entry["reason"] = "proposal 已被阻擋，override 無可生效的基礎"
    elif agent_class not in allowed:
        entry["reason"] = (f"riskTier={rec.get('riskTier')} 需要 {sorted(allowed)} "
                           f"才能作出生效 override")
    else:
        entry["reason"] = "override 的 domain 不在生效的 perDomain 中"

    if not rec.get("blocked", True) and domain in (rec.get("perDomain") or {}):
        hypothetical = copy.deepcopy(rec)
        hypothetical["perDomain"][domain] = new_level
        entry["advisoryCertainty"] = _recompute(hypothetical)["effectiveCertainty"]
    else:
        entry["advisoryCertainty"] = None

    rec["advisoryOverrides"].append(entry)
    return rec


# ---------------------------------------------------------------------------
# 向後相容 wrapper
# ---------------------------------------------------------------------------

def propose_certainty(design: str, domains: Mapping[str, str],
                      upgrades: Optional[Mapping[str, Any]] = None) -> dict:
    """v2 介面的相容 wrapper —— **只產出 advisory，永不產出 effectiveCertainty**。

    v2 的呼叫端傳的是裸的等級字串，沒有 agentClass、沒有理由、沒有旗標確認，
    因此無從判斷這些等級是不是人類作出的。在那個資訊量下唯一安全的行為是
    永遠 blocked：算出 advisoryCertainty 供參考，但不放行。

    要取得 effectiveCertainty 必須改用 `aggregate_certainty()` 並提供
    `HumanDomainJudgement`。
    """
    missing = [d for d in GRADE_DOMAINS if d not in domains]
    reasons = ["propose_certainty 是相容 wrapper：輸入不含 agentClass 與理由，"
               "無法確認為人類判斷，因此不產出 effectiveCertainty；"
               "請改用 aggregate_certainty()"]
    if missing:
        reasons.append(f"缺少 GRADE domain：{missing}")

    result = _blank_result(reasons, "unknown")
    result["ruleId"] = "GRADE-SUM-001-COMPAT"

    if missing or any(domains[d] not in DOWNGRADE for d in GRADE_DOMAINS):
        return result

    start = 3 if design.startswith("RCT") else 1
    total_down = sum(DOWNGRADE[domains[d]] for d in GRADE_DOMAINS)
    up = 0
    if upgrades and start == 1:
        up = min(sum(1 for v in upgrades.values() if v), 2)
    idx = max(0, min(3, start - total_down + up))

    result.update({
        "advisoryCertainty": CERTAINTY_LADDER[idx],
        "startingLevel": CERTAINTY_LADDER[start],
        "totalDowngrade": total_down,
        "totalUpgrade": up,
        "perDomain": {d: domains[d] for d in GRADE_DOMAINS},
    })
    return result
