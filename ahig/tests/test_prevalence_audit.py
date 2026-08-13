"""S2 母體比例抽查工具的測試。

核心不變量：

- 抽樣確定性：同 seed 同池必得同樣本，與輸入順序無關。
- 只抽 TT 候選；TTE-only 永不入樣。
- 這不是 screening：不產生任何 include/exclude，queue 與 pool 不被改動。
- estimate 對未回填的稽核表必須拒絕，不得默默略過。
- regex 對照以人工判定為準：人說有、regex 沒抓到 → missed。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ahig.search import candidates, prevalence_audit, screening


def epmc(*, native_id, title, abstract, doi=None, year="2020") -> dict:
    return {
        "source": "MED", "id": native_id, "title": title,
        "authorString": "Smith J", "pubYear": year, "abstractText": abstract,
        "firstPublicationDate": f"{year}-01-01",
        "doi": doi or f"10.1000/{native_id.lower()}",
    }


TT_RECORDS = [
    epmc(native_id="TT90", title="Carbohydrate and cycling time trial",
         abstract="Cyclists ingested carbohydrate at 90 g/h during the "
                  "time trial."),
    epmc(native_id="TTWORDS", title="High carbohydrate dose and time trial",
         abstract="Cyclists ingested sixty grams per hour of carbohydrate "
                  "before the time trial."),
    epmc(native_id="TTNONE", title="Carbohydrate feeding and time trial",
         abstract="Trained cyclists completed a time trial after "
                  "carbohydrate ingestion."),
    epmc(native_id="TT45", title="Moderate carbohydrate and time trial",
         abstract="Runners ingested 45 g/h carbohydrate during a running "
                  "time trial."),
    epmc(native_id="TTA", title="Carbohydrate beverage and time trial A",
         abstract="A cycling time trial with carbohydrate drinks."),
    epmc(native_id="TTB", title="Carbohydrate beverage and time trial B",
         abstract="Another cycling time trial with carbohydrate gels."),
]
TTE_RECORD = epmc(
    native_id="TTE1", title="Carbohydrate and time to exhaustion",
    abstract="Cyclists ingested carbohydrate; time to exhaustion improved.")


def make_run_root(tmp: str) -> Path:
    root = Path(tmp) / "run"
    rows = TT_RECORDS + [TTE_RECORD]
    d = root / "sources" / "europe-pmc"
    d.mkdir(parents=True)
    (d / "records.json").write_text(json.dumps(rows), encoding="utf-8")
    (d / "status.json").write_text(json.dumps({
        "sourceId": "europe-pmc", "status": "completed",
        "recordCount": len(rows)}), encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({
        "runId": "audit-run", "searchContractHash": "sha256:" + "a" * 64,
        "sources": {"europe-pmc": {"status": "completed",
                                   "recordCount": len(rows)}},
    }), encoding="utf-8")
    candidates.build_from_run_root(root)
    screening.build_from_run_root(root)
    return root


def test_sample_is_deterministic_and_order_independent():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        one = prevalence_audit.draw_sample(root, seed=7, n=3)
        two = prevalence_audit.draw_sample(root, seed=7, n=3, redo=True)
        assert [r["candidateId"] for r in one["records"]] == [
            r["candidateId"] for r in two["records"]]
        other = prevalence_audit.draw_sample(root, seed=8, n=3, redo=True)
        assert one["auditId"] != other["auditId"]


def test_sample_covers_only_tt_candidates_and_caps_at_pool_size():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        audit = prevalence_audit.draw_sample(root, seed=1, n=50)
        assert audit["ttCandidateCount"] == len(TT_RECORDS)
        assert audit["sampleSize"] == len(TT_RECORDS)
        queue = json.loads((root / "screening-queue" / "queue.json")
                           .read_text(encoding="utf-8"))
        by_id = {e["candidateId"]: e for e in queue}
        for record in audit["records"]:
            assert prevalence_audit.TT_OUTCOME in (
                by_id[record["candidateId"]]["outcomeHints"])
            assert record["doseMentionedInAbstract"] is None
        tte_ids = {e["candidateId"] for e in queue
                   if "time-to-exhaustion" in e["outcomeHints"]
                   and prevalence_audit.TT_OUTCOME not in e["outcomeHints"]}
        assert tte_ids
        assert tte_ids.isdisjoint(r["candidateId"] for r in audit["records"])


def test_sample_is_not_a_screening_decision_and_mutates_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        queue_before = (root / "screening-queue" / "queue.json").read_bytes()
        pool_before = (root / "candidate-pool" / "candidates.json").read_bytes()
        audit = prevalence_audit.draw_sample(root, seed=1, n=3)
        assert audit["notAScreeningDecision"] is True
        assert audit["requiresHumanScreeningUnchanged"] is True
        assert (root / "screening-queue" / "queue.json").read_bytes() == queue_before
        assert (root / "candidate-pool" / "candidates.json").read_bytes() == pool_before


def test_sample_requires_redo_to_overwrite():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        prevalence_audit.draw_sample(root, seed=1, n=3)
        try:
            prevalence_audit.draw_sample(root, seed=1, n=3)
        except FileExistsError:
            return
    raise AssertionError("同一 audit 目錄已存在時必須要求 --redo")


def test_estimate_rejects_unfilled_tally():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        audit = prevalence_audit.draw_sample(root, seed=1, n=3)
        audit_dir = root / "prevalence-audit" / audit["auditId"]
        try:
            prevalence_audit.estimate(audit_dir)
        except ValueError as exc:
            assert "未回填" in str(exc)
            return
    raise AssertionError("未回填完成的稽核表必須拒絕")


def _fill(audit_dir: Path) -> None:
    """依 fixture 已知內容回填：90→very-high、字面 sixty→high、45→moderate、
    其餘 false。"""
    path = audit_dir / "audit.json"
    audit = json.loads(path.read_text(encoding="utf-8"))
    for record in audit["records"]:
        abstract = record["abstract"] or ""
        if "90 g/h" in abstract:
            record.update(doseMentionedInAbstract=True,
                          maxDoseGramsPerHour=90, judgedBand="very-high")
        elif "sixty grams per hour" in abstract:
            record.update(doseMentionedInAbstract=True,
                          maxDoseGramsPerHour=60, judgedBand="high")
        elif "45 g/h" in abstract:
            record.update(doseMentionedInAbstract=True,
                          maxDoseGramsPerHour=45, judgedBand="moderate")
        else:
            record.update(doseMentionedInAbstract=False)
    path.write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")


def test_estimate_counts_projection_and_regex_audit():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        audit = prevalence_audit.draw_sample(root, seed=1, n=50)
        audit_dir = root / "prevalence-audit" / audit["auditId"]
        _fill(audit_dir)
        result = prevalence_audit.estimate(audit_dir)

        counts = result["counts"]
        assert counts["doseMentioned"] == 3
        assert counts["judgedHighOrVeryHigh"] == 2
        assert counts["judgedUnclear"] == 0
        # 「sixty grams per hour」人判有劑量、現行 regex 抓不到。
        assert counts["humanFoundDoseButRegexMissed"] == 1
        missed = result["regexAudit"]["missedCandidateIds"]
        assert len(missed) == 1

        n = result["sampleSize"]
        est = result["estimates"]["highOrVeryHighDose"]
        assert est["point"] == 2 / n
        lo, hi = est["wilson95"]
        assert 0.0 <= lo < est["point"] < hi <= 1.0
        proj = result["projection"]
        assert proj["point"] == round(result["ttCandidateCount"] * 2 / n)
        assert proj["wilson95"][0] <= proj["point"] <= proj["wilson95"][1]
        assert result["decisionRemainsHuman"] is True
        assert (audit_dir / "estimate.json").is_file()


def test_estimate_requires_redo_to_overwrite():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        audit = prevalence_audit.draw_sample(root, seed=1, n=3)
        audit_dir = root / "prevalence-audit" / audit["auditId"]
        _fill(audit_dir)
        prevalence_audit.estimate(audit_dir)
        try:
            prevalence_audit.estimate(audit_dir)
        except FileExistsError:
            return
    raise AssertionError("estimate.json 已存在時必須要求 --redo")


def test_wilson_interval_known_value_and_edges():
    lo, hi = prevalence_audit.wilson_interval(10, 50)
    assert abs(lo - 0.11244) < 1e-3
    assert abs(hi - 0.33037) < 1e-3
    assert prevalence_audit.wilson_interval(0, 0) == (0.0, 1.0)
    zero_lo, zero_hi = prevalence_audit.wilson_interval(0, 50)
    assert zero_lo == 0.0 and 0.0 < zero_hi < 0.1
    full_lo, full_hi = prevalence_audit.wilson_interval(50, 50)
    assert 0.9 < full_lo < 1.0 and full_hi == 1.0
