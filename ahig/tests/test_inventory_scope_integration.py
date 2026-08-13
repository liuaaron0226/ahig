"""OutcomeInventory draft/scoped lifecycle 與 ScopeMatcher 的整合測試。

三個層次：

1. **Schema 層**：draft 與 scoped 各自的必填、禁止與條件式（registry compared、
   outcome switching 強制雙審、harms 掃描可稽核）。
2. **整合層**：ScopeMatcher 把 draft 升級為 scoped，輸出必須「直接」通過 schema，
   不容許測試端補欄位。這是本檔的主張：介面漂移會在此爆炸。
3. **漂移層**：以 AST 解析 matcher.py，比對它實際讀取的軸鍵、發出的 reasonCode
   與 ruleId 是否與 schema 宣告完全一致。schema 與實作各自演化時必然亮紅燈。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ahig.scope import inventory as inv_mod
from ahig.scope import matcher as sm

try:                                            # run_tests.py 把 tests/ 放進 sys.path
    from test_scope_and_family import base_contract
except ImportError:                             # pytest 以 package 方式匯入
    from tests.test_scope_and_family import base_contract

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "outcome-inventory.schema.json"
MATCHER_PATH = ROOT / "ahig" / "scope" / "matcher.py"

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


# ===========================================================================
# fixtures
# ===========================================================================

def errors(doc: dict) -> list:
    return sorted(VALIDATOR.iter_errors(doc), key=lambda e: list(e.path))


def assert_valid(doc: dict, label: str = "") -> None:
    errs = errors(doc)
    assert not errs, f"{label} 應通過驗證，但：{list(errs[0].path)} — {errs[0].message}"


def assert_invalid(doc: dict, label: str = "") -> None:
    assert errors(doc), f"{label} 應被拒絕，但通過了驗證"


def outcome(**over) -> dict:
    """一個完整的 draft reportedOutcome（含 ScopeMatcher 需要的全部軸）。"""
    o = {
        "localLabel": "1RM back squat",
        "normalisedOutcomeRef": "1rm-squat",
        "instrument": "barbell-back-squat",
        "unitAsReported": "kg",
        "reportedTimepoints": ["4 weeks"],
        "reportedAnalysisSets": ["ITT"],
        "outcomeRoleAsStated": "primary",
        "hasNumericResult": True,
        "sourceLocation": {"section": "Results", "pageIndex": 5,
                           "tableOrFigure": "Table 2"},
        "timepointDays": 28,
        "analysisSet": "ITT",
        "effectMeasure": "MD",
        "statisticalModel": "unadjusted",
        "dose": 5,
        "doseUnit": "g",
    }
    o.update(over)
    return o


def attestation(**over) -> dict:
    a = {
        "sectionsScanned": ["Methods", "Results", "Tables", "Supplement"],
        "supplementaryScanned": True,
        "harmsScan": {
            "performed": True,
            "sectionsScanned": ["Results", "Adverse events"],
            "harmOutcomesFound": 0,
            "harmsReportingStatement": "explicit-none-reported",
        },
        "attestedBy": {"agentClass": "model", "at": "2026-08-13T00:00:00Z"},
    }
    a.update(over)
    return a


def draft(**over) -> dict:
    d = {
        "inventoryId": "inv-1",
        "report": "expr-1",
        "manifestation": "sha256:" + "a" * 64,
        "scopeContractHash": "sha256:" + "0" * 64,
        "lifecycle": "draft",
        "reportedOutcomes": [outcome()],
        "registryComparison": {
            "status": "compared",
            "registryId": "NCT01234567",
            "registryRetrievedAt": "2026-08-13T00:00:00Z",
            "registryPrimaryOutcomes": ["1RM squat at 4 weeks"],
            "outcomeSwitchingFlags": [],
        },
        "createdBy": {"agentClass": "model", "modelVersion": "x",
                      "dualExtracted": False},
        "completenessAttestation": attestation(),
    }
    d.update(over)
    return d


# ===========================================================================
# 1. lifecycle：draft
# ===========================================================================

def test_valid_draft_passes():
    assert_valid(draft(), "完整 draft")


def test_lifecycle_is_required():
    d = draft()
    del d["lifecycle"]
    assert_invalid(d, "缺少 lifecycle 的清單")


def test_unknown_lifecycle_rejected():
    assert_invalid(draft(lifecycle="scopedish"), "未列舉的 lifecycle")


def test_draft_must_not_carry_scope_decisions():
    """draft 帶著 scopeDecision 等同讓模型自行判定範圍 —— 契約禁止。"""
    d = draft()
    d["reportedOutcomes"][0]["scopeDecision"] = {
        "inScope": True, "reasonCode": "in-scope", "ruleId": "SCOPE-999-in-scope",
        "matchedScopeElements": {"outcomeId": "1rm-squat", "timepointId": "wk4",
                                 "analysisSet": "ITT", "effectMeasure": "MD",
                                 "doseBandId": "maintenance"},
        "decidedBy": {"agentClass": "deterministic",
                      "matcherVersion": inv_mod.MATCHER_VERSION},
    }
    assert_invalid(d, "帶 scopeDecision 的 draft")


def test_draft_must_not_carry_scope_summary():
    assert_invalid(draft(scopedAt="2026-08-13T00:00:00Z"), "帶 scopedAt 的 draft")


def test_reported_outcomes_must_not_be_empty():
    """空清單無法支撐任何 notExtracted 標記。"""
    assert_invalid(draft(reportedOutcomes=[]), "空的 reportedOutcomes")


def test_all_matcher_axes_are_accepted_by_schema():
    """ScopeMatcher 讀得到的每一個軸都必須能寫進 draft，否則抽取端無法被驗證。"""
    d = draft()
    d["reportedOutcomes"] = [outcome(
        timepointSessions=12, multipleMeasurementsInWindow=True,
        isSubgroup=True, subgroupId="female", subgroupPrespecified=True,
        isSensitivityAnalysis=True, primaryAnalysisFailedRoB=False)]
    assert_valid(d, "含全部軸的 draft")


def test_unknown_axis_still_rejected():
    d = draft()
    d["reportedOutcomes"][0]["someUndeclaredAxis"] = 1
    assert_invalid(d, "未宣告的軸")


# ===========================================================================
# 2. completenessAttestation 與 harms 掃描可稽核
# ===========================================================================

def test_completeness_attestation_is_required():
    d = draft()
    del d["completenessAttestation"]
    assert_invalid(d, "缺少 completenessAttestation")


def test_harms_scan_is_required():
    a = attestation()
    del a["harmsScan"]
    assert_invalid(draft(completenessAttestation=a), "缺少 harmsScan")


def test_harms_scan_cannot_be_declared_not_performed():
    a = attestation()
    a["harmsScan"]["performed"] = False
    assert_invalid(draft(completenessAttestation=a), "performed=false 的 harmsScan")


def test_harms_scan_must_record_which_sections_were_scanned():
    a = attestation()
    a["harmsScan"]["sectionsScanned"] = []
    assert_invalid(draft(completenessAttestation=a), "未記錄掃描章節的 harmsScan")


def test_harms_found_requires_a_safety_outcome_in_the_inventory():
    """宣稱找到 harm 卻沒有任何 safety outcome 登錄 —— 不可稽核，必須擋下。"""
    a = attestation()
    a["harmsScan"]["harmOutcomesFound"] = 1
    a["harmsScan"]["harmsReportingStatement"] = "harms-reported"
    assert_invalid(draft(completenessAttestation=a), "找到 harm 但無 safety 條目")


def test_harms_found_with_safety_outcome_passes():
    a = attestation()
    a["harmsScan"]["harmOutcomesFound"] = 1
    a["harmsScan"]["harmsReportingStatement"] = "harms-reported"
    d = draft(completenessAttestation=a)
    d["reportedOutcomes"].append(outcome(
        localLabel="muscle cramps", normalisedOutcomeRef=None,
        outcomeRoleAsStated="safety", instrument=None))
    assert_valid(d, "harm 與 safety 條目相符")


def test_harms_reported_statement_must_match_count():
    a = attestation()
    a["harmsScan"]["harmsReportingStatement"] = "harms-reported"
    a["harmsScan"]["harmOutcomesFound"] = 0
    assert_invalid(draft(completenessAttestation=a), "宣稱有 harm 卻計數為 0")


def test_audit_harms_scan_detects_count_mismatch():
    """程式層的稽核：宣告數與實際 safety 條目數不符時必須有具名發現。"""
    d = draft()
    d["completenessAttestation"]["harmsScan"]["harmOutcomesFound"] = 2
    d["reportedOutcomes"].append(outcome(localLabel="nausea",
                                         outcomeRoleAsStated="safety"))
    findings = inv_mod.audit_harms_scan(d)
    assert any(f["code"] == "harms-count-mismatch" for f in findings), findings


def test_audit_harms_scan_clean_when_consistent():
    assert inv_mod.audit_harms_scan(draft()) == []


# ===========================================================================
# 3. registryComparison 條件與 outcome switching 強制雙審
# ===========================================================================

def test_compared_status_requires_registry_id():
    d = draft()
    d["registryComparison"]["registryId"] = None
    assert_invalid(d, "status=compared 但 registryId 為 null")


def test_compared_status_requires_retrieved_at():
    d = draft()
    del d["registryComparison"]["registryRetrievedAt"]
    assert_invalid(d, "status=compared 但缺 registryRetrievedAt")


def test_compared_status_requires_explicit_switching_flags():
    """比對過就必須明說有沒有 flag；欄位缺席不等於沒有 flag。"""
    d = draft()
    del d["registryComparison"]["outcomeSwitchingFlags"]
    assert_invalid(d, "status=compared 但未列出 outcomeSwitchingFlags")


def test_no_registration_found_does_not_require_registry_id():
    d = draft()
    d["registryComparison"] = {"status": "no-registration-found"}
    assert_valid(d, "no-registration-found")


def test_switching_flag_forces_dual_extraction():
    d = draft()
    d["registryComparison"]["outcomeSwitchingFlags"] = ["registry-primary-not-reported"]
    d["createdBy"]["dualExtracted"] = False
    assert_invalid(d, "有 switching flag 卻單模型抽取")


def test_switching_flag_with_dual_extraction_passes():
    d = draft()
    d["registryComparison"]["outcomeSwitchingFlags"] = ["registry-primary-not-reported"]
    d["createdBy"]["dualExtracted"] = True
    assert_valid(d, "有 switching flag 且雙審")


def test_switching_flag_absent_dual_extraction_field_rejected():
    """flag 存在時 dualExtracted 不得省略（預設 false 是 fail-open）。"""
    d = draft()
    d["registryComparison"]["outcomeSwitchingFlags"] = ["new-primary-not-in-registry"]
    del d["createdBy"]["dualExtracted"]
    assert_invalid(d, "有 switching flag 但未宣告 dualExtracted")


# ===========================================================================
# 4. 整合：matcher 把 draft 升級為 scoped，輸出直接通過 schema
# ===========================================================================

def matcher() -> sm.ScopeMatcher:
    return sm.ScopeMatcher(base_contract())


def test_scoped_output_validates_without_touch_up():
    """本檔的核心主張：matcher 的輸出不需測試端補欄位即可通過 schema。"""
    scoped = matcher().scope_inventory(draft())
    assert scoped["lifecycle"] == "scoped"
    assert_valid(scoped, "matcher 產出的 scoped 清單")


def test_scoped_output_carries_rule_id_and_deterministic_decided_by():
    scoped = matcher().scope_inventory(draft())
    dec = scoped["reportedOutcomes"][0]["scopeDecision"]
    assert dec["inScope"] and dec["reasonCode"] == "in-scope"
    assert dec["ruleId"] == "SCOPE-999-in-scope"
    assert dec["decidedBy"]["agentClass"] == "deterministic"
    assert dec["decidedBy"]["matcherVersion"] == inv_mod.MATCHER_VERSION


def test_scoped_preserves_every_reported_outcome():
    """out-of-scope 者只是被標記，不得從清單消失。"""
    d = draft()
    d["reportedOutcomes"] = [outcome(), outcome(normalisedOutcomeRef="vo2max",
                                                instrument=None,
                                                localLabel="VO2max")]
    scoped = matcher().scope_inventory(d)
    assert len(scoped["reportedOutcomes"]) == 2
    codes = [o["scopeDecision"]["reasonCode"] for o in scoped["reportedOutcomes"]]
    assert codes == ["in-scope", "notExtracted-outcome-not-in-scope"]
    assert_valid(scoped, "含 out-of-scope 條目的 scoped 清單")


def test_scoped_summary_matches_decisions():
    d = draft()
    d["reportedOutcomes"] = [outcome(), outcome(normalisedOutcomeRef="vo2max",
                                                instrument=None)]
    scoped = matcher().scope_inventory(d)
    s = scoped["scopeDecisionSummary"]
    assert s["candidateCount"] == 1 and s["inScopeCount"] == 1
    assert s["escalated"] is False and s["escalationReason"] is None


def test_scoped_escalation_zeroes_in_scope_count_and_still_validates():
    c = base_contract()
    c["extractionPolicy"]["maxStudyResultsPerStudy"] = 1
    m = sm.ScopeMatcher(c)
    d = draft()
    d["reportedOutcomes"] = [outcome(), outcome(timepointDays=84)]  # wk4 + wk12
    scoped = m.scope_inventory(d)
    s = scoped["scopeDecisionSummary"]
    assert s["escalated"] is True
    assert s["inScopeCount"] == 0 and s["candidateCount"] == 2
    assert isinstance(s["escalationReason"], str) and s["escalationReason"]
    assert all(o["scopeDecision"]["ruleId"] == "SCOPE-100-exceeds-max"
               for o in scoped["reportedOutcomes"])
    assert_valid(scoped, "escalate 後的 scoped 清單")


def test_escalated_summary_cannot_claim_in_scope_results():
    scoped = matcher().scope_inventory(draft())
    scoped["scopeDecisionSummary"]["escalated"] = True
    assert_invalid(scoped, "escalated 為真但 inScopeCount 非 0")


def test_escalated_summary_requires_reason():
    c = base_contract()
    c["extractionPolicy"]["maxStudyResultsPerStudy"] = 1
    d = draft()
    d["reportedOutcomes"] = [outcome(), outcome(timepointDays=84)]
    scoped = sm.ScopeMatcher(c).scope_inventory(d)
    scoped["scopeDecisionSummary"]["escalationReason"] = None
    assert_invalid(scoped, "escalated 為真但無 escalationReason")


def test_scoping_a_scoped_inventory_is_refused():
    scoped = matcher().scope_inventory(draft())
    try:
        matcher().scope_inventory(scoped)
        raise AssertionError("已 scoped 的清單不得再次升級")
    except ValueError:
        pass


def test_scoping_refuses_draft_from_a_different_contract():
    d = draft(scopeContractHash="sha256:" + "b" * 64)
    try:
        matcher().scope_inventory(d)
        raise AssertionError("契約 hash 不符時不得升級")
    except ValueError:
        pass


def test_scoping_refuses_draft_carrying_model_decisions():
    d = draft()
    d["reportedOutcomes"][0]["scopeDecision"] = {"inScope": True,
                                                 "reasonCode": "in-scope"}
    try:
        matcher().scope_inventory(d)
        raise AssertionError("draft 帶著 scopeDecision 時不得升級")
    except ValueError:
        pass


def test_scoping_refuses_empty_inventory():
    try:
        matcher().scope_inventory(draft(reportedOutcomes=[]))
        raise AssertionError("空清單不得升級")
    except ValueError:
        pass


# ===========================================================================
# 5. scoped 的 schema 硬性條件
# ===========================================================================

def test_scoped_requires_scope_decision_on_every_outcome():
    scoped = matcher().scope_inventory(draft())
    scoped["reportedOutcomes"].append(outcome(localLabel="untouched"))
    assert_invalid(scoped, "有條目缺 scopeDecision 的 scoped 清單")


def test_scoped_requires_rule_id():
    scoped = matcher().scope_inventory(draft())
    del scoped["reportedOutcomes"][0]["scopeDecision"]["ruleId"]
    assert_invalid(scoped, "缺 ruleId 的 scopeDecision")


def test_scoped_rejects_unlisted_rule_id():
    scoped = matcher().scope_inventory(draft())
    scoped["reportedOutcomes"][0]["scopeDecision"]["ruleId"] = "SCOPE-042-vibes"
    assert_invalid(scoped, "未列舉的 ruleId")


def test_scope_decision_must_be_made_by_deterministic_agent():
    scoped = matcher().scope_inventory(draft())
    scoped["reportedOutcomes"][0]["scopeDecision"]["decidedBy"]["agentClass"] = "model"
    assert_invalid(scoped, "由模型做出的 scopeDecision")


def test_scope_decision_requires_matched_scope_elements():
    scoped = matcher().scope_inventory(draft())
    del scoped["reportedOutcomes"][0]["scopeDecision"]["matchedScopeElements"]
    assert_invalid(scoped, "缺 matchedScopeElements 的 scopeDecision")


def test_scoped_requires_summary_and_timestamp():
    scoped = matcher().scope_inventory(draft())
    del scoped["scopeDecisionSummary"]
    assert_invalid(scoped, "缺 scopeDecisionSummary 的 scoped 清單")

    scoped2 = matcher().scope_inventory(draft())
    del scoped2["scopedAt"]
    assert_invalid(scoped2, "缺 scopedAt 的 scoped 清單")


def test_scoped_still_enforces_registry_and_harms_conditions():
    d = draft()
    d["registryComparison"]["outcomeSwitchingFlags"] = ["primary-timepoint-changed"]
    d["createdBy"]["dualExtracted"] = True
    scoped = matcher().scope_inventory(d)
    assert_valid(scoped, "scoped 且雙審")
    scoped["createdBy"]["dualExtracted"] = False
    assert_invalid(scoped, "scoped 但 switching flag 未雙審")


# ===========================================================================
# 6. backfill 仍以 draft 為依據
# ===========================================================================

def test_backfill_operates_on_draft_axes():
    old = matcher()
    c2 = base_contract()
    c2["version"] = "1.1.0"
    c2["inScopeAnalysisSets"] = ["ITT", "PP"]
    d = draft()
    d["reportedOutcomes"] = [outcome(analysisSet="ITT"), outcome(analysisSet="PP")]
    assert_valid(d, "backfill 用 draft")
    cand = sm.backfill_candidates(d, old, sm.ScopeMatcher(c2))
    assert len(cand) == 1
    assert cand[0]["previousReason"] == "notExtracted-analysis-set-not-in-scope"


# ===========================================================================
# 7. AST × schema 漂移偵測
# ===========================================================================

MATCHER_SRC = MATCHER_PATH.read_text(encoding="utf-8")
MATCHER_AST = ast.parse(MATCHER_SRC)


def _string_constants(tree: ast.AST) -> set[str]:
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def _keys_read_from(tree: ast.AST, var: str) -> set[str]:
    """var 這個名字在 tree 內被讀取的字串鍵（``x.get("k")`` 與 ``x["k"]``）。"""
    keys: set[str] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == var
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            keys.add(node.args[0].value)
        if (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == var
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)):
            keys.add(node.slice.value)
    return keys


def matcher_axis_keys() -> set[str]:
    """matcher.py 實際從「單筆 reportedOutcome」讀出的鍵。

    兩個來源，都由 AST 認定而非寫死變數名：
    1. 參數名為 ``reported`` 的函式 —— 其整個函式體。
    2. ``for X in ...["reportedOutcomes"]`` 迴圈 —— 只算該迴圈體內的 X。

    刻意不掃全檔：``decide_inventory`` 內另有 ``for r in results`` 重用同名變數
    走訪判定結果，全檔掃描會把 inScope/reasonCode 誤認成論文登錄軸。
    """
    keys: set[str] = set()

    for node in ast.walk(MATCHER_AST):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = {a.arg for a in node.args.args}
            if "reported" in names:
                keys |= _keys_read_from(node, "reported")

        if (isinstance(node, ast.For)
                and isinstance(node.target, ast.Name)
                and isinstance(node.iter, ast.Subscript)
                and isinstance(node.iter.slice, ast.Constant)
                and node.iter.slice.value == "reportedOutcomes"):
            for stmt in node.body:
                keys |= _keys_read_from(stmt, node.target.id)

    return keys


def schema_outcome_properties() -> set[str]:
    return set(SCHEMA["$defs"]["reportedOutcome"]["properties"])


def schema_reason_codes() -> set[str]:
    return set(SCHEMA["$defs"]["scopeDecision"]["properties"]["reasonCode"]["enum"])


def schema_rule_ids() -> set[str]:
    return set(SCHEMA["$defs"]["scopeDecision"]["properties"]["ruleId"]["enum"])


def test_every_axis_matcher_reads_is_declared_in_schema():
    keys = matcher_axis_keys()
    assert len(keys) >= 15, f"AST 只抓到 {len(keys)} 個鍵，解析器可能失效：{sorted(keys)}"
    missing = keys - schema_outcome_properties()
    assert not missing, f"matcher 讀取但 schema 未宣告的軸：{sorted(missing)}"


def test_schema_declares_no_axis_the_matcher_cannot_use():
    """反向漂移：schema 宣告了 matcher 不讀、也不屬於登錄描述的軸。"""
    descriptive = {"localLabel", "normalisedOutcomeRef", "instrument",
                   "unitAsReported", "reportedTimepoints", "reportedAnalysisSets",
                   "outcomeRoleAsStated", "sourceLocation", "scopeDecision"}
    orphan = schema_outcome_properties() - descriptive - matcher_axis_keys()
    assert not orphan, f"schema 宣告但無人使用的軸：{sorted(orphan)}"


def test_reason_codes_match_schema_exactly():
    emitted = {s for s in _string_constants(MATCHER_AST)
               if s == "in-scope" or s.startswith(("notExtracted-", "escalated-"))}
    assert len(emitted) == 13, f"預期 13 個理由碼，實得 {len(emitted)}：{sorted(emitted)}"
    assert emitted == schema_reason_codes(), (
        f"僅 matcher 有：{sorted(emitted - schema_reason_codes())}；"
        f"僅 schema 有：{sorted(schema_reason_codes() - emitted)}")


def test_rule_ids_match_schema_exactly():
    emitted = {s for s in _string_constants(MATCHER_AST) if s.startswith("SCOPE-")}
    assert len(emitted) >= 15, f"AST 只抓到 {len(emitted)} 個 ruleId：{sorted(emitted)}"
    assert emitted == schema_rule_ids(), (
        f"僅 matcher 有：{sorted(emitted - schema_rule_ids())}；"
        f"僅 schema 有：{sorted(schema_rule_ids() - emitted)}")


def test_every_rule_id_is_reachable_and_unique_per_reason():
    """每個 ruleId 只能出現在一種 reasonCode 底下，否則稽核時無法回溯。"""
    pairs = set()
    for node in ast.walk(MATCHER_AST):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "ScopeDecision" and len(node.args) == 4
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[3], ast.Constant)):
            pairs.add((node.args[3].value, node.args[1].value))
    assert len(pairs) >= 14, f"只解析到 {len(pairs)} 組 (ruleId, reasonCode)"
    seen: dict[str, str] = {}
    for rule, reason in pairs:
        assert seen.setdefault(rule, reason) == reason, f"{rule} 對應多個理由碼"


def test_matcher_never_writes_scope_decisions_into_a_draft():
    """升級必須產生新文件，不得就地改寫 draft —— 否則 draft 不可複驗。"""
    d = draft()
    before = json.dumps(d, sort_keys=True, ensure_ascii=False)
    matcher().scope_inventory(d)
    assert json.dumps(d, sort_keys=True, ensure_ascii=False) == before


def test_schema_id_is_versioned_for_the_lifecycle_change():
    assert SCHEMA["$id"].endswith("/2.0.0"), SCHEMA["$id"]
    Draft202012Validator.check_schema(SCHEMA)


if __name__ == "__main__":
    from run_tests import main
    raise SystemExit(main([__file__]))
