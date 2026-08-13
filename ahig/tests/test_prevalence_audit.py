"""劑量可讀性 prevalence audit 的測試。

核心不變量：

- 來源不齊（candidateSourcesComplete ≠ True）→ 直接擋，與 make_assignment 一致。
- 產出只能落在 AHIG_PRIVATE_ROOT 之下。
- 主抽樣框扣除動物／綜述／registry／安全四類；誤剔抽查只從這四類抽。
- 抽樣確定性：同 seed 同池必得同樣本；queue 與 pool 絕不被改動。
- estimate 對源頭重放驗證：改抽樣區段（即使重算 samplingLockHash）也會被拒。
- 每次 sample 都在 draws.jsonl 留痕；多次抽樣時 estimate 明示警告。
- 母體外推以有限母體夾定：普查塌縮為精確計數，下界不低於已觀察數。
- 測試只用虛構 fixture（含 strata），不碰真實校準資料。
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from ahig.search import candidates, prevalence_audit, screening


@contextmanager
def private_tmp():
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            yield Path(tmp)
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def epmc(*, native_id, title, abstract, publication_types=None,
         year="2020") -> dict:
    value = {
        "source": "MED", "id": native_id, "title": title,
        "authorString": "Smith J", "pubYear": year, "abstractText": abstract,
        "firstPublicationDate": f"{year}-01-01",
        "doi": f"10.1000/{native_id.lower()}",
    }
    if publication_types is not None:
        value["pubTypeList"] = {"pubType": publication_types}
    return value


def ct(*, nct="NCT00000001") -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct,
                                     "briefTitle": "Carbohydrate trial"},
            "statusModule": {"overallStatus": "COMPLETED",
                             "studyFirstPostDateStruct": {"date": "2020-01-01"}},
            "descriptionModule": {"briefSummary": "Registry summary"},
            "designModule": {"studyType": "INTERVENTIONAL",
                             "enrollmentInfo": {"count": 20}},
            "conditionsModule": {"conditions": ["Exercise"]},
        },
        "derivedSection": {"miscInfoModule": {"versionHolder": "2026-08-13"}},
        "hasResults": False,
    }


# 主抽樣框（standard-screening lane）
FRAME_RECORDS = [
    epmc(native_id="TT90", title="Carbohydrate and cycling time trial",
         abstract="Cyclists ingested carbohydrate at 90 g/h during the "
                  "time trial."),
    epmc(native_id="TTWORDS", title="Worded dose and time trial",
         abstract="Cyclists ingested sixty grams per hour of carbohydrate "
                  "during the time trial."),
    epmc(native_id="TTNONE", title="Carbohydrate feeding and time trial",
         abstract="Trained cyclists completed a time trial after "
                  "carbohydrate ingestion."),
    epmc(native_id="TTE45", title="Carbohydrate and time to exhaustion",
         abstract="Runners ingested 45 g/h carbohydrate; time to exhaustion "
                  "was measured."),
    epmc(native_id="GLY120", title="Carbohydrate and muscle glycogen",
         abstract="Cyclists ingested 120 g/h carbohydrate; muscle glycogen "
                  "was assessed."),
    epmc(native_id="OX60", title="Exogenous carbohydrate oxidation study",
         abstract="Exogenous carbohydrate oxidation was measured while "
                  "cyclists ingested 60 g/h."),
    epmc(native_id="HIGHWORD", title="High carbohydrate dose and time trial",
         abstract="Cyclists ingested a high carbohydrate dose during the "
                  "time trial."),
]
# 四類分流（誤剔抽查母體）
EXCLUDED_RECORDS = [
    epmc(native_id="ANIMAL", title="Carbohydrate feeding in rats",
         abstract="Rats ingested carbohydrate during treadmill running "
                  "time trial."),
    epmc(native_id="REVIEW", title="Carbohydrate and time trial: a review",
         abstract="A review of carbohydrate ingestion and time trial "
                  "performance.", publication_types=["Review"]),
    epmc(native_id="SAFETY", title="Carbohydrate and low energy availability",
         abstract="Athletes with low energy availability ingested "
                  "carbohydrate during a time trial."),
]

STRATA_FIXTURE = {
    "samplingFrameId": "fixture:strata",
    "version": "fixture-1.0.0",
    "status": "frozen",
    "strata": [
        {"stratumId": "S1-tt-moderate-dose", "quota": 12,
         "primaryOutcomes": ["tt-completion-time"],
         "doseBands": ["moderate"]},
        {"stratumId": "S2-tt-high-and-very-high-dose", "quota": 10,
         "primaryOutcomes": ["tt-completion-time"],
         "doseBands": ["high", "very-high"]},
        {"stratumId": "S5-gi-primary", "quota": 8,
         "primaryOutcomes": ["gi-symptom-incidence", "gi-symptom-severity"],
         "doseBands": ["moderate", "high", "very-high"]},
        {"stratumId": "S6-gi-secondary", "quota": 7,
         "primaryOutcomes": ["gi-symptom-incidence"],
         "doseBands": ["low", "moderate", "high", "very-high"]},
        {"stratumId": "S7-glycogen", "quota": 5,
         "primaryOutcomes": ["muscle-glycogen-post-exercise"],
         "doseBands": ["moderate", "high"]},
    ],
}


def make_strata(tmp: Path) -> Path:
    path = tmp / "strata-fixture.json"
    path.write_text(json.dumps(STRATA_FIXTURE, ensure_ascii=False),
                    encoding="utf-8")
    return path


def make_run_root(base: Path, *, complete: bool = True) -> Path:
    root = base / "run"
    rows_by_source = {
        "europe-pmc": FRAME_RECORDS + EXCLUDED_RECORDS,
        "clinicaltrials-gov": [ct()],
    }
    if complete:
        rows_by_source["pubmed"] = []
        rows_by_source["openalex"] = []
    for sid, rows in rows_by_source.items():
        d = root / "sources" / sid
        d.mkdir(parents=True)
        (d / "records.json").write_text(json.dumps(rows), encoding="utf-8")
        (d / "status.json").write_text(json.dumps({
            "sourceId": sid, "status": "completed",
            "recordCount": len(rows)}), encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({
        "runId": "audit-run", "searchContractHash": "sha256:" + "a" * 64,
        "sources": {sid: {"status": "completed", "recordCount": len(rows)}
                    for sid, rows in rows_by_source.items()},
    }), encoding="utf-8")
    candidates.build_from_run_root(root)
    screening.build_from_run_root(root)
    return root


def _fill(audit_dir: Path, *, unjustified_exclusions: int = 0) -> None:
    """依 fixture 已知內容回填。TT90 額外確認 outcomeHints。"""
    path = audit_dir / "audit.json"
    audit = json.loads(path.read_text(encoding="utf-8"))
    for record in audit["records"]:
        abstract = record["abstract"] or ""
        if "90 g/h" in abstract:
            record.update(doseReadability="exact-value",
                          maxDose={"value": 90, "unit": "g/h"},
                          doseBands=["very-high"], outcomeConfirmed=True)
        elif "sixty grams per hour" in abstract:
            record.update(doseReadability="exact-value",
                          maxDose={"value": 60, "unit": "g/h"},
                          doseBands=["high"])
        elif "45 g/h" in abstract:
            record.update(doseReadability="exact-value",
                          maxDose={"value": 45, "unit": "g/h"},
                          doseBands=["moderate"])
        elif "120 g/h" in abstract:
            record.update(doseReadability="exact-value",
                          maxDose={"value": 120, "unit": "g/h"},
                          doseBands=["very-high"])
        elif "60 g/h" in abstract:
            record.update(doseReadability="exact-value",
                          maxDose={"value": 60, "unit": "g/h"},
                          doseBands=["high"])
        elif "a high carbohydrate dose" in abstract:
            record.update(doseReadability="intensity-only",
                          doseBands=["high"])
        else:
            record.update(doseReadability="not-reported")
    for i, record in enumerate(audit["exclusionAudit"]):
        record["exclusionJustified"] = i >= unjustified_exclusions
    path.write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")


def _draw(root: Path, **kwargs):
    kwargs.setdefault("seed", 1)
    kwargs.setdefault("n", 50)
    return prevalence_audit.draw_sample(root, **kwargs)


def _estimate(root: Path, audit: dict, tmp: Path, **kwargs):
    audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
    return prevalence_audit.estimate(audit_dir,
                                     strata_path=make_strata(tmp), **kwargs)


def test_sample_blocked_when_candidate_sources_incomplete():
    with private_tmp() as tmp:
        root = make_run_root(tmp, complete=False)
        try:
            _draw(root)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "complete" in str(exc)
            return
    raise AssertionError("來源不齊必須直接擋，與 make_assignment 一致")


def test_sample_refuses_paths_outside_private_root():
    with private_tmp() as tmp:
        priv = tmp / "priv"
        priv.mkdir()
        os.environ["AHIG_PRIVATE_ROOT"] = str(priv)
        root = make_run_root(tmp)  # 在 private root 之外
        try:
            _draw(root)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "AHIG_PRIVATE_ROOT" in str(exc)
            return
    raise AssertionError("private root 之外必須拒絕")


def test_sample_is_deterministic_and_seed_changes_audit_id():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        one = _draw(root, seed=7)
        two = _draw(root, seed=7, redo=True)
        assert ([r["candidateId"] for r in one["records"]]
                == [r["candidateId"] for r in two["records"]])
        assert one["samplingLockHash"] == two["samplingLockHash"]
        other = _draw(root, seed=8)
        assert other["auditId"] != one["auditId"]


def test_frame_excludes_four_lanes_and_exclusion_audit_draws_from_them():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        assert audit["frameSize"] == len(FRAME_RECORDS)
        # registry + 動物 + 綜述 + 安全
        assert audit["excludedPoolSize"] == len(EXCLUDED_RECORDS) + 1
        assert set(audit["exclusionCountsByLane"]) == {
            "animal-signal-review", "review-source-review",
            "registry-review", "safety-review"}
        for record in audit["records"]:
            assert record["screeningLane"] not in prevalence_audit.EXCLUDED_LANES
            assert record["doseReadability"] is None
            assert record["outcomeConfirmed"] is None
        for record in audit["exclusionAudit"]:
            assert record["screeningLane"] in prevalence_audit.EXCLUDED_LANES
            assert record["exclusionJustified"] is None


def test_sample_is_not_a_screening_decision_and_mutates_nothing():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        queue_before = (root / "screening-queue" / "queue.json").read_bytes()
        pool_before = (root / "candidate-pool" / "candidates.json").read_bytes()
        audit = _draw(root)
        assert audit["notAScreeningDecision"] is True
        assert audit["requiresHumanScreeningUnchanged"] is True
        assert (root / "screening-queue" / "queue.json").read_bytes() == queue_before
        assert (root / "candidate-pool" / "candidates.json").read_bytes() == pool_before


def test_reading_sheet_contains_records_sections_and_instructions():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        sheet = (root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
                 / "reading-sheet.md").read_text(encoding="utf-8")
        assert "第一節" in sheet and "第二節" in sheet
        assert "outcomeConfirmed" in sheet
        for record in audit["records"]:
            assert record["candidateId"] in sheet


def test_redo_archives_previous_audit_and_draw_log_is_append_only():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root, seed=1)
        try:
            _draw(root, seed=1)
        except FileExistsError:
            pass
        else:
            raise AssertionError("同 audit 目錄已存在時必須要求 --redo")
        _draw(root, seed=1, redo=True)
        archive = root / prevalence_audit.ARCHIVE_DIRNAME
        assert (archive / audit["auditId"]).is_dir()
        log = (root / prevalence_audit.AUDIT_DIRNAME / prevalence_audit.DRAW_LOG)
        lines = [json.loads(line) for line in
                 log.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == 2
        assert all(line["frameHash"] == audit["frameHash"] for line in lines)


def test_estimate_reports_draw_count_and_multiplicity_warning():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        _draw(root, seed=1)
        audit = _draw(root, seed=99)  # seed shopping 會被看見
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        assert result["drawsForSameFrame"] == 2
        assert result["multiplicityWarning"] is not None


def test_single_draw_has_no_multiplicity_warning():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        assert result["drawsForSameFrame"] == 1
        assert result["multiplicityWarning"] is None
        assert result["sourceReplayVerified"] is True


def test_estimate_rejects_unfilled_tally():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        try:
            _estimate(root, audit, tmp)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "未回填" in str(exc)
            return
    raise AssertionError("未回填的稽核表必須拒絕")


def test_estimate_rejects_tampered_sampling_section():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        path = audit_dir / "audit.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["records"][0]["abstract"] = "tampered abstract"
        path.write_text(json.dumps(data), encoding="utf-8")
        try:
            _estimate(root, audit, tmp)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "samplingLockHash" in str(exc)
            return
    raise AssertionError("抽樣區段被動過必須拒絕")


def test_estimate_rejects_adversary_who_recomputes_the_lock():
    """lock 不是信任來源：重算 lock 的竄改也要被源頭重放攔下。"""
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        path = audit_dir / "audit.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["records"][0]["abstract"] = (
            "Fabricated: cyclists ingested 95 g/h in a time trial.")
        data["samplingLockHash"] = prevalence_audit._sampling_lock(data)
        path.write_text(json.dumps(data), encoding="utf-8")
        try:
            _estimate(root, audit, tmp)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "源頭" in str(exc)
            return
    raise AssertionError("重算 lock 的竄改必須被源頭重放攔下")


def test_estimate_rejects_frame_size_inflation_with_recomputed_lock():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        path = audit_dir / "audit.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["frameSize"] = 10000  # 膨脹母體 → 膨脹所有外推
        data["samplingLockHash"] = prevalence_audit._sampling_lock(data)
        path.write_text(json.dumps(data), encoding="utf-8")
        try:
            _estimate(root, audit, tmp)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "不符" in str(exc)
            return
    raise AssertionError("frameSize 竄改必須被攔下")


def test_validation_rejects_contradictory_tallies():
    cases = [
        # not-reported 卻填 band
        {"doseReadability": "not-reported", "doseBands": ["high"],
         "maxDose": {"value": None, "unit": None}},
        # not-reported 卻殘留 unit
        {"doseReadability": "not-reported", "doseBands": None,
         "maxDose": {"value": None, "unit": "g/h"}},
        # exact-value 缺 maxDose
        {"doseReadability": "exact-value", "doseBands": ["high"],
         "maxDose": {"value": None, "unit": None}},
        # intensity-only 卻有數值
        {"doseReadability": "intensity-only", "doseBands": ["high"],
         "maxDose": {"value": 60, "unit": "g/h"}},
        # intensity-only 殘留 unit
        {"doseReadability": "intensity-only", "doseBands": ["high"],
         "maxDose": {"value": None, "unit": "g/h"}},
        # 不合法 band 名
        {"doseReadability": "exact-value", "doseBands": ["mega"],
         "maxDose": {"value": 60, "unit": "g/h"}},
        # outcomeConfirmed 型別錯誤
        {"doseReadability": "not-reported", "doseBands": None,
         "maxDose": {"value": None, "unit": None}, "outcomeConfirmed": "yes"},
    ]
    for bad in cases:
        with private_tmp() as tmp:
            root = make_run_root(tmp)
            audit = _draw(root)
            audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
            _fill(audit_dir)
            path = audit_dir / "audit.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["records"][0].update(bad)
            path.write_text(json.dumps(data), encoding="utf-8")
            try:
                _estimate(root, audit, tmp)
            except prevalence_audit.PrevalenceAuditError:
                continue
            raise AssertionError(f"矛盾判讀必須拒絕：{bad}")


def test_band_estimates_census_collapses_to_exact_counts():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)  # n=50 > frame 7 → 普查
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        assert result["isCensus"] is True
        high = result["bandEstimates"]["high"]
        # exact-value 的 high：TTWORDS(60) + OX60；HIGHWORD 只算進 lenient。
        assert high["strict"]["count"] == 2
        assert high["lenient"]["count"] == 3
        # 普查：母體計數已知，外推塌縮為精確值。
        assert high["strict"]["projectedInFrame"] == [2, 2]
        assert high["lenient"]["projectedInFrame"] == [3, 3]
        counts = result["readabilityCounts"]
        assert counts["exact-value"] == 5
        assert counts["intensity-only"] == 1
        assert counts["not-reported"] == 1


def test_project_clamps_to_finite_population_facts():
    # 下界不得低於樣本已觀察到的 k
    assert prevalence_audit._project(100, 0.001, 0.30,
                                     successes=2, n=50) == [2, 30]
    # 上界不得高於 frame_size - (n - k)
    assert prevalence_audit._project(60, 0.5, 0.99,
                                     successes=30, n=50) == [30, 40]
    # 普查塌縮
    assert prevalence_audit._project(40, 0.1, 0.5,
                                     successes=10, n=40) == [10, 10]


def test_stratum_feasibility_joins_outcome_and_band():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        by_id = {row["stratumId"]: row for row in result["stratumFeasibility"]}
        s2 = by_id["S2-tt-high-and-very-high-dose"]
        # S2 = TT × {high, very-high}：TT90(very-high) + TTWORDS(high)。
        # HIGHWORD 是 intensity-only，只進 lenient。
        assert s2["strict"]["count"] == 2
        assert s2["lenient"]["count"] == 3
        # 普查且 2 < quota 10 → 確定不足。
        assert s2["strict"]["verdictAtBound"] == "likely-insufficient"
        # TT90 有人工確認 outcome，TTWORDS 沒有 → strict 未確認占比 1/2。
        assert abs(s2["strict"]["hintUnconfirmedShare"] - 0.5) < 1e-12
        assert "S1-tt-moderate-dose" in s2["overlappingStrata"]
        # S5/S6 outcome 集合相交 → 互相標注。
        assert "S6-gi-secondary" in by_id["S5-gi-primary"]["overlappingStrata"]
        # S7 glycogen：樣本裡只有一筆 → 證據太薄要明說。
        s7 = by_id["S7-glycogen"]
        assert s7["outcomeGroupSampleCount"] == 1
        assert s7["insufficientAuditData"] is True
        assert result["strataVersion"] == "fixture-1.0.0"
        assert result["strataOverride"] is True


def test_outcome_filtered_topup_skips_exclusion_audit_and_other_strata():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root,
                      outcome_filter=["muscle-glycogen-post-exercise"])
        assert audit["frameSize"] == 1
        assert audit["exclusionAuditSize"] == 0  # 補抽不重複背誤剔判讀
        assert all("muscle-glycogen-post-exercise" in r["outcomeHints"]
                   for r in audit["records"])
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        assert result["outcomeFilter"] == ["muscle-glycogen-post-exercise"]
        assert "outcomeFilterCaveat" in result["interpretation"]
        by_id = {row["stratumId"]: row for row in result["stratumFeasibility"]}
        # 與過濾無交集的層不得產生判定
        assert by_id["S2-tt-high-and-very-high-dose"][
            "skippedReason"] == "outcome-filtered-draw"
        assert "verdictAtBound" in by_id["S7-glycogen"]["strict"]


def test_regex_audit_flags_worded_dose_as_missed():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        missed = set(result["regexAudit"]["missedCandidateIds"])
        worded = {r["candidateId"] for r in audit["records"]
                  if "sixty grams" in (r["abstract"] or "")}
        intensity = {r["candidateId"] for r in audit["records"]
                     if "a high carbohydrate dose" in (r["abstract"] or "")}
        assert worded | intensity == missed
        assert result["regexAudit"]["falsePositiveCandidateIds"] == []


def test_exclusion_audit_upper_bound_matches_closed_form():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        result = _estimate(root, audit, tmp)
        m = result["exclusionAudit"]["sampleSize"]
        assert m == 4
        assert result["exclusionAudit"]["unjustifiedCount"] == 0
        # 零誤剔的單側 95% 上界閉式解：1 - 0.05^(1/m)
        expected = 1 - 0.05 ** (1 / m)
        assert abs(result["exclusionAudit"]["falseExclusionRateUpper95"]
                   - expected) < 1e-9

        _fill(audit_dir, unjustified_exclusions=1)
        worse = _estimate(root, audit, tmp, redo=True)
        assert worse["exclusionAudit"]["unjustifiedCount"] == 1
        assert (worse["exclusionAudit"]["falseExclusionRateUpper95"]
                > expected)
        # --redo 不覆蓋：舊 estimate 改名保留
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        assert (audit_dir / "estimate-superseded-1.json").is_file()


def test_estimate_rejects_non_frozen_or_broken_strata():
    with private_tmp() as tmp:
        root = make_run_root(tmp)
        audit = _draw(root)
        audit_dir = root / prevalence_audit.AUDIT_DIRNAME / audit["auditId"]
        _fill(audit_dir)
        thawed = dict(STRATA_FIXTURE, status="draft")
        path = tmp / "thawed.json"
        path.write_text(json.dumps(thawed), encoding="utf-8")
        try:
            prevalence_audit.estimate(audit_dir, strata_path=path)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "frozen" in str(exc)
        else:
            raise AssertionError("非 frozen 的 strata 檔必須拒絕")
        broken = dict(STRATA_FIXTURE)
        broken["strata"] = [dict(STRATA_FIXTURE["strata"][0], quota=None)]
        path2 = tmp / "broken.json"
        path2.write_text(json.dumps(broken), encoding="utf-8")
        try:
            prevalence_audit.estimate(audit_dir, strata_path=path2)
        except prevalence_audit.PrevalenceAuditError as exc:
            assert "quota" in str(exc)
            return
    raise AssertionError("quota 非正整數必須以 domain error 拒絕")


def test_clopper_pearson_matches_closed_forms():
    n = 50
    lo, hi = prevalence_audit.clopper_pearson(0, n)
    assert lo == 0.0
    assert abs(hi - (1 - 0.025 ** (1 / n))) < 1e-9
    lo, hi = prevalence_audit.clopper_pearson(n, n)
    assert hi == 1.0
    assert abs(lo - 0.025 ** (1 / n)) < 1e-9
    assert prevalence_audit.clopper_pearson(0, 0) == (0.0, 1.0)
    assert prevalence_audit.clopper_pearson_upper(0, 12) == 1 - 0.05 ** (1 / 12)
