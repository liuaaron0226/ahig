"""端到端貫穿：從凍結契約走到 GRADE 聚合，用完全虛構的資料。

每一層都有自己的單元測試，本檔測的是**接縫**——上一層的輸出能不能直接餵給
下一層，不需要測試端手動補欄位或改形狀。介面漂移在單元測試裡看不見，因為每一
層都對著自己的 fixture 綠燈。

流程：

    frozen contract
      → OutcomeInventoryDraft            （模型登錄論文報告了什麼）
      → ScopeMatcher                     （確定性判定哪些該抽）
      → ScopedOutcomeInventory
      → StudyResult                      （只從 in-scope 者建立）
      → 13 項確定性檢查
      → 雙盲審分歧
      → 確定性裁決（coverage / accuracy 分離）
      → 品質閘門（Clopper–Pearson）
      → GRADE indicators → 人類判斷 → 聚合

貫穿用的是 B.11 的真實凍結契約，不是另一份 fixture——契約若改壞，本檔會亮紅燈。

資料全部虛構。這裡沒有任何一個數字來自真實文獻，也不得被當成證據使用。
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ahig.contracts import freeze
from ahig.gates.quality_gate import evaluate_batch_quality
from ahig.scope import matcher as sm
from ahig.stats import adjudication as adj
from ahig.stats import deterministic as ds
from ahig.stats import grade

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "calibration" / "b11-carbohydrate" / "scope-contract.json"
INVENTORY_SCHEMA = Draft202012Validator(json.loads(
    (ROOT / "schema" / "outcome-inventory.schema.json").read_text(encoding="utf-8")))

CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


# ===========================================================================
# 虛構資料
# ===========================================================================

def synthetic_draft() -> dict:
    """一份虛構論文的 OutcomeInventory draft。

    刻意混入三種會被排除的東西，好證明它們是被**標記**而不是被丟棄：
      - 一個 out-of-scope outcome（血乳酸，不在 B.11 契約內）
      - 一個沒有數值結果的 outcome（只有文字敘述）
      - 一個落在時窗外的測量點
    """
    def outcome(**over):
        o = {
            "localLabel": "40 km cycling time trial",
            "normalisedOutcomeRef": "tt-completion-time",
            "instrument": "cycling-time-trial-fixed-distance",
            "unitAsReported": "s",
            "reportedTimepoints": ["end of exercise"],
            "reportedAnalysisSets": ["ITT"],
            "outcomeRoleAsStated": "primary",
            "hasNumericResult": True,
            "sourceLocation": {"section": "Results", "pageIndex": 4,
                               "tableOrFigure": "Table 2"},
            "timepointDays": 0.02,
            "analysisSet": "ITT",
            "effectMeasure": "MD",
            "statisticalModel": "unadjusted",
            "dose": 65,
            "doseUnit": "g/h",
        }
        o.update(over)
        return o

    return {
        "inventoryId": "synthetic-inv-1",
        "report": "synthetic-expr-1",
        "manifestation": "sha256:" + "b" * 64,
        "scopeContractHash": CONTRACT["scopeContractHash"],
        "lifecycle": "draft",
        "reportedOutcomes": [
            outcome(),
            outcome(localLabel="GI symptom incidence",
                    normalisedOutcomeRef="gi-symptom-incidence",
                    instrument=None, unitAsReported=None,
                    outcomeRoleAsStated="safety", effectMeasure="RR"),
            # out-of-scope：血乳酸不在 B.11 契約的 inScopeOutcomes 內
            outcome(localLabel="Blood lactate", normalisedOutcomeRef="blood-lactate",
                    instrument=None, unitAsReported="mmol/L",
                    outcomeRoleAsStated="exploratory"),
            # 無數值結果：只有文字敘述
            outcome(localLabel="Perceived palatability",
                    normalisedOutcomeRef="tt-completion-time",
                    hasNumericResult=False, outcomeRoleAsStated="exploratory"),
            # 時窗外：契約最遠的窗是運動後 30 小時
            outcome(localLabel="TT at 7 days", timepointDays=7,
                    outcomeRoleAsStated="secondary"),
        ],
        "registryComparison": {
            "status": "compared",
            "registryId": "NCT00000000",
            "registryRetrievedAt": "2026-08-13T00:00:00Z",
            "registryPrimaryOutcomes": ["40 km TT completion time"],
            "outcomeSwitchingFlags": [],
        },
        "createdBy": {"agentClass": "model", "modelVersion": "synthetic",
                      "dualExtracted": False},
        "completenessAttestation": {
            "sectionsScanned": ["Methods", "Results", "Tables", "Supplement"],
            "supplementaryScanned": True,
            "harmsScan": {
                "performed": True,
                "sectionsScanned": ["Results", "Adverse events"],
                "harmOutcomesFound": 1,
                "harmsReportingStatement": "harms-reported",
            },
            "attestedBy": {"agentClass": "model", "at": "2026-08-13T00:00:00Z"},
        },
    }


def synthetic_study_result(scoped: dict) -> dict:
    """由 in-scope 項目建立的虛構 StudyResult（連續型：計時賽時間）。
    數值刻意內部一致，好讓確定性檢查的失敗必然來自程式而非資料。"""
    in_scope = [o for o in scoped["reportedOutcomes"]
                if o["scopeDecision"]["inScope"]]
    assert in_scope, "貫穿測試需要至少一個 in-scope 項目"
    return {
        "effectMeasure": "MD",
        "pointEstimate": -60.0,
        "ciLow": -110.0,
        "ciHigh": -10.0,
        "pValue": 0.019,
        "analysisSet": "ITT",
        "studyDesign": "RCT-crossover",
        "analysisReported": "paired",
        "nSubjects": 20,
        "testStatistic": {"type": "t", "value": 2.556, "df1": 19},
        "scopeContractHash": scoped["scopeContractHash"],
        "scopeRuleId": in_scope[0]["scopeDecision"]["ruleId"],
        "inferenceFramework": "frequentist",
        "hasConventionalStatistics": True,
    }


def synthetic_harms_result(scoped: dict) -> dict:
    """GI harms 的 StudyResult（二分型）。

    critical harms 走的是與表現結果不同的檢查分支：事件數合理性與
    crude 2×2 重算。只測連續型會讓整條 harms 路徑從未被貫穿過。
    12/30 vs 4/30 → RR = 3.0。
    """
    gi = [o for o in scoped["reportedOutcomes"]
          if o["normalisedOutcomeRef"] == "gi-symptom-incidence"
          and o["scopeDecision"]["inScope"]]
    assert gi, "貫穿測試需要 GI harms 是 in-scope"
    return {
        "effectMeasure": "RR",
        "pointEstimate": 3.0,
        "ciLow": 1.07,
        "ciHigh": 8.43,
        "pValue": 0.037,
        "events": [12, 4],
        "armN": [30, 30],
        "analysisSet": "ITT",
        "studyDesign": "RCT-parallel",
        "analysisReported": "independent",
        "nSubjects": 60,
        "armAccounting": [
            {"randomised": 30, "analysed": 30, "lostToFollowUp": 0, "excluded": 0},
            {"randomised": 30, "analysed": 30, "lostToFollowUp": 0, "excluded": 0},
        ],
        "scopeContractHash": scoped["scopeContractHash"],
        "scopeRuleId": gi[0]["scopeDecision"]["ruleId"],
        "inferenceFramework": "frequentist",
        "hasConventionalStatistics": True,
    }


# ===========================================================================
# 1. 契約 → scoped inventory
# ===========================================================================

def test_frozen_contract_is_the_starting_point():
    assert CONTRACT["status"] == "frozen"
    assert freeze.verify_frozen(CONTRACT, "scopeContractHash")
    assert freeze.freeze_preflight(CONTRACT) == []


def test_draft_validates_before_scoping():
    errs = sorted(INVENTORY_SCHEMA.iter_errors(synthetic_draft()),
                  key=lambda e: list(e.path))
    assert not errs, f"{list(errs[0].path)} — {errs[0].message}"


def test_scoped_output_validates_without_touch_up():
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    assert scoped["lifecycle"] == "scoped"
    errs = sorted(INVENTORY_SCHEMA.iter_errors(scoped), key=lambda e: list(e.path))
    assert not errs, f"{list(errs[0].path)} — {errs[0].message}"


def test_nothing_is_discarded_by_scoping():
    draft = synthetic_draft()
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(draft)
    assert len(scoped["reportedOutcomes"]) == len(draft["reportedOutcomes"])


def test_each_exclusion_carries_a_named_rule():
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    excluded = [o for o in scoped["reportedOutcomes"]
                if not o["scopeDecision"]["inScope"]]
    assert len(excluded) == 3, "三個刻意排除項應全部被標記"
    for o in excluded:
        assert o["scopeDecision"]["ruleId"].startswith("SCOPE-")
        assert o["scopeDecision"]["decidedBy"]["agentClass"] == "deterministic"


def test_the_three_exclusions_hit_the_expected_rules():
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    rules = {o["localLabel"]: o["scopeDecision"]["ruleId"]
             for o in scoped["reportedOutcomes"]
             if not o["scopeDecision"]["inScope"]}
    assert rules["Blood lactate"] == "SCOPE-001-outcome"
    assert rules["Perceived palatability"] == "SCOPE-000-no-numeric-result"
    assert rules["TT at 7 days"] == "SCOPE-002-timepoint"


def test_harms_survive_scoping():
    """GI harms 是 critical outcome；被 scoping 濾掉就等於契約白寫。"""
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    gi = [o for o in scoped["reportedOutcomes"]
          if o["normalisedOutcomeRef"] == "gi-symptom-incidence"]
    assert gi and gi[0]["scopeDecision"]["inScope"]


# ===========================================================================
# 2. StudyResult → 確定性檢查
# ===========================================================================

def test_study_result_passes_deterministic_checks():
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    report = ds.run_all(synthetic_study_result(scoped))
    assert report["n_checks"] > 0
    assert not report["blocking"], f"虛構資料不該觸發 FAIL：{report['failed_rules']}"
    assert report["n_inconclusive"] == 0, \
        [c.rule_id for c in report["checks"] if c.verdict == ds.INCONCLUSIVE]


def test_a_corrupted_study_result_is_blocked():
    """把點估計移出信賴區間——內部矛盾必須被擋下，否則檢查層形同虛設。"""
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    sr = synthetic_study_result(scoped)
    sr["pointEstimate"] = 999.0
    assert ds.run_all(sr)["blocking"]


def test_study_result_carries_the_scope_provenance():
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    sr = synthetic_study_result(scoped)
    assert sr["scopeContractHash"] == CONTRACT["scopeContractHash"]
    assert sr["scopeRuleId"].startswith("SCOPE-")


def test_harms_result_exercises_the_binary_branch():
    """critical harms 走的是事件數與 2×2 重算，與連續型完全不同的檢查。"""
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    report = ds.run_all(synthetic_harms_result(scoped))
    rules = {c.rule_id for c in report["checks"]}
    assert {"STAT-004-event-le-n", "STAT-006-effect-vs-2x2"} <= rules, \
        f"harms 路徑未觸發二分型檢查：{sorted(rules)}"
    assert not report["blocking"], report["failed_rules"]


def test_harms_result_is_fully_conclusive():
    """INCONCLUSIVE 不是失敗，但貫穿用的虛構資料應該內部完全一致——
    否則『沒有 FAIL』可能只是因為檢查根本算不下去。"""
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    report = ds.run_all(synthetic_harms_result(scoped))
    assert report["n_inconclusive"] == 0, \
        [c.rule_id for c in report["checks"] if c.verdict == ds.INCONCLUSIVE]
    assert report["verdict"] == ds.PASS


def test_a_harms_result_inconsistent_with_its_2x2_is_blocked():
    """12/30 vs 4/30 的 RR 是 3.0；報 1.2 必須被重算擋下。"""
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    sr = synthetic_harms_result(scoped)
    sr["pointEstimate"] = 1.2
    assert ds.run_all(sr)["blocking"]


def test_impossible_event_counts_are_blocked():
    """事件數超過該臂人數是不可能的；這是最基本的一道。"""
    scoped = sm.ScopeMatcher(CONTRACT).scope_inventory(synthetic_draft())
    sr = synthetic_harms_result(scoped)
    sr["events"] = [40, 4]
    assert ds.run_all(sr)["blocking"]


# ===========================================================================
# 3. 雙盲審分歧 → 裁決
# ===========================================================================

def dual_review_fields() -> dict:
    """兩位盲審者的抽取結果。刻意涵蓋四種情境：
    完全一致、大小寫差異、單位差異，以及真正需要人工的數值分歧。"""
    return {
        "analysisSet": {"A": {"value": "ITT"}, "B": {"value": "ITT"}},
        "effectMeasure": {"A": {"value": "MD"}, "B": {"value": "md"}},
        "dose": {"A": {"value": 65, "unit": "g/h"},
                 "B": {"value": 65, "unit": "g/h"}},
        "pointEstimate": {"A": {"value": -60.0}, "B": {"value": -42.0}},
    }


def test_adjudication_separates_coverage_from_accuracy():
    result = adj.adjudicate_record(dual_review_fields())
    coverage = result["metrics"]["coverage"]
    assert coverage["deterministicResolutionCoverage"] is not None
    assert result["metrics"]["goldEvaluation"] is None, \
        "沒有 gold 就不得出現任何 accuracy 數字"


def test_unverifiable_numeric_disagreement_escalates_to_a_human():
    """兩個數值都沒有可驗證依據時，必須升級人工而不是挑一個。"""
    result = adj.adjudicate_record(dual_review_fields())
    escalated = {a["field"] for a in result["adjudications"]
                 if a["outcome"] == adj.ESCALATE}
    assert "pointEstimate" in escalated
    assert result["escalatedToHuman"]


def test_case_difference_is_resolved_without_human_time():
    result = adj.adjudicate_record(dual_review_fields())
    em = [a for a in result["adjudications"] if a["field"] == "effectMeasure"][0]
    assert em["outcome"] == adj.AUTO_RESOLVED
    assert em["value"] == "MD", "canonical 形式不得被小寫化"


def test_gold_enables_accuracy_and_major_error_counts():
    gold = {"effectMeasure": {"value": "MD", "severity": "minor"},
            "analysisSet": {"value": "ITT", "severity": "minor"}}
    evaluation = adj.adjudicate_record(dual_review_fields(),
                                       gold=gold)["metrics"]["goldEvaluation"]
    assert evaluation is not None
    assert evaluation["majorErrorCount"] == 0


# ===========================================================================
# 4. 品質閘門
# ===========================================================================

def test_a_sixty_paper_batch_cannot_pass_the_one_percent_ceiling():
    """校準集規模的誠實後果：零錯誤也不足以宣稱 1% 上界。"""
    result = evaluate_batch_quality(
        sample_size=60, error_count=0,
        conflict_count=40, auto_resolved_count=36,
        auto_resolved_correct_count=36, major_error_count=0,
        common_wrong_agreement_count=0,
        agreement={"gwetAC1": 0.90, "ciLower95": 0.80,
                   "modelAssumptions": {"prevalence": "observed", "n": 60}})
    assert result["decision"] == "fail"
    assert result["errorRateUpper95"] > 0.01


def test_missing_gold_yields_insufficient_evidence_not_pass():
    result = evaluate_batch_quality(
        sample_size=299, error_count=0,
        conflict_count=40, auto_resolved_count=36,
        auto_resolved_correct_count=None, major_error_count=None,
        common_wrong_agreement_count=None, agreement=None)
    assert result["decision"] == "insufficient-evidence"


def test_a_fully_evidenced_batch_can_pass():
    result = evaluate_batch_quality(
        sample_size=299, error_count=0,
        conflict_count=40, auto_resolved_count=36,
        auto_resolved_correct_count=36, major_error_count=0,
        common_wrong_agreement_count=0,
        agreement={"gwetAC1": 0.90, "ciLower95": 0.80,
                   "modelAssumptions": {"prevalence": "observed", "n": 299}})
    assert result["decision"] == "pass"


# ===========================================================================
# 5. GRADE
# ===========================================================================

def domain_judgements(agent_class: str = "human-self") -> dict:
    return {d: grade.HumanDomainJudgement(
        domain=d, rating="not-serious", agent_class=agent_class,
        rationale="虛構貫穿資料") for d in grade.GRADE_DOMAINS}


def test_certainty_is_blocked_without_human_judgements():
    result = grade.aggregate_certainty("RCT", {}, "general-clinical")
    assert result["effectiveCertainty"] is None


def test_certainty_aggregates_once_all_five_domains_are_judged():
    result = grade.aggregate_certainty("RCT", domain_judgements(), "general-clinical")
    assert result["effectiveCertainty"] in {"high", "moderate", "low", "very-low"}


def test_safety_critical_refuses_self_judgement():
    """GI harms 是 critical outcome；safety-critical 分級不得由 human-self 拍板。"""
    result = grade.aggregate_certainty("RCT", domain_judgements("human-self"),
                                       "safety-critical")
    assert result["effectiveCertainty"] is None


def test_model_cannot_stand_in_for_a_human_judgement():
    result = grade.aggregate_certainty("RCT", domain_judgements("model"),
                                       "general-clinical")
    assert result["effectiveCertainty"] is None


def test_mid_unavailable_blocks_contextualised_imprecision():
    """B.11 所有 midRef 皆為 null——GRADE 必須顯性承認未做 contextualised 判定，
    而不是靜默當作做過。"""
    indicators = grade.rate_imprecision(ci_low=-110.0, ci_high=-10.0, total_n=20,
                                        mid=None, mid_status="unavailable")
    assert indicators.indicators["contextualised"] is False


def test_contract_declares_no_mid_so_the_calibration_cannot_claim_high():
    assert all(o.get("midRef") is None for o in CONTRACT["inScopeOutcomes"]), \
        "B.11 本階段不得登錄任何文獻型 MID"
