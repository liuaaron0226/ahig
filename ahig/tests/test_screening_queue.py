"""B.11 分層 screening queue：只排序、不自動納排。

任何 deterministic 詞彙規則都只能回答「先看哪一筆／要注意什麼」，不能回答
「納入或排除」。最後一筆低訊號候選也必須存在 queue，且明寫需雙盲人工 screening。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ahig.search import screening


def candidate(cid: str, *, kind="publication", title="", abstract=None,
              doi=None, pmid=None, registry=None, is_preprint=False,
              publication_types=None) -> dict:
    return {
        "candidateId": cid,
        "entityKind": kind,
        "canonicalIdentity": (f"doi:{doi}" if doi else
                              f"registry:{registry}" if registry else f"source:{cid}"),
        "identifiers": {
            "doi": [doi] if doi else [], "pmid": [pmid] if pmid else [],
            "pmcid": [], "registryId": [registry] if registry else [],
        },
        "title": title,
        "normalisedTitle": screening.normalise_for_matching(title),
        "abstract": abstract,
        "authorString": "Smith J",
        "firstAuthor": "Smith J",
        "publicationYear": 2020,
        "publicationDate": "2020-01-01",
        "publicationStatus": "ppublish",
        "publicationTypes": publication_types or ["Journal Article"],
        "isPreprint": is_preprint,
        "isOpenAccess": False,
        "members": [{"sourceId": "test", "sourceNativeId": cid,
                     "sourceRecordIndex": 0}],
    }


def build(items: list[dict], *, conflicts=None, ambiguities=None):
    return screening.build_queue(
        items,
        candidate_pool_hash="sha256:" + "a" * 64,
        search_contract_hash="sha256:" + "b" * 64,
        run_id="test-run",
        identifier_conflicts=conflicts or [],
        title_ambiguities=ambiguities or [],
    )


def by_id(result: dict, cid: str) -> dict:
    return next(e for e in result["queue"] if e["candidateId"] == cid)


# ---------------------------------------------------------------------------
# never auto-exclude
# ---------------------------------------------------------------------------

def test_every_input_candidate_appears_exactly_once():
    items = [candidate("a"), candidate("b"), candidate("c")]
    result = build(items)
    ids = [entry["candidateId"] for entry in result["queue"]]
    assert sorted(ids) == ["a", "b", "c"]
    assert len(ids) == len(set(ids))


def test_even_zero_signal_candidate_requires_human_screening():
    entry = by_id(build([candidate("x", title="Unrelated topic")]), "x")
    assert entry["priorityTier"] == "T5-low-signal"
    assert entry["requiresHumanScreening"] is True
    assert entry["autoDecision"] is None


def test_safety_flag_does_not_exclude_candidate():
    entry = by_id(build([candidate(
        "x", title="Low energy availability and carbohydrate in athletes")]), "x")
    assert entry["screeningLane"] == "safety-review"
    assert "safety-low-energy-availability" in entry["flags"]
    assert entry["autoDecision"] is None


def test_missing_abstract_is_a_flag_not_an_exclusion():
    entry = by_id(build([candidate(
        "x", title="Carbohydrate ingestion during cycling performance",
        abstract=None, doi="10.1000/x")]), "x")
    assert "metadata-missing-abstract" in entry["flags"]
    assert entry["requiresHumanScreening"] is True
    assert entry["priorityTier"] in {"T1-high-signal", "T2-moderate-signal"}


# ---------------------------------------------------------------------------
# explainable concept matching
# ---------------------------------------------------------------------------

def test_direct_endurance_carbohydrate_trial_is_p1():
    entry = by_id(build([candidate(
        "x",
        title="Carbohydrate ingestion during prolonged cycling improves time trial performance",
        abstract="Trained endurance cyclists ingested glucose and fructose during exercise.",
        doi="10.1000/x")]), "x")
    assert entry["priorityTier"] == "T1-high-signal"
    assert set(entry["conceptMatches"]) >= {
        "population", "intervention", "exercise", "timing", "outcomes"}
    assert "tt-completion-time" in entry["outcomeHints"]
    assert entry["scoreBreakdown"]["intervention"] > 0


def test_intervention_plus_exercise_without_b11_outcome_is_probable():
    entry = by_id(build([candidate(
        "x", title="Carbohydrate beverage before exercise",
        abstract="Adults consumed glucose before cycling.")]), "x")
    assert entry["priorityTier"] == "T2-moderate-signal"


def test_exercise_only_record_is_broad_not_direct():
    entry = by_id(build([candidate(
        "x", title="Exercise performance in trained runners",
        abstract="Endurance athletes completed a running protocol.")]), "x")
    assert entry["priorityTier"] == "T4-broad-signal"
    assert entry["scoreBreakdown"]["intervention"] == 0


def test_gi_harms_generates_critical_outcome_hint():
    entry = by_id(build([candidate(
        "x", title="Carbohydrate feeding and gastrointestinal symptoms during running",
        abstract="Nausea, diarrhea and gastrointestinal discomfort were recorded.")]), "x")
    assert "gi-symptom-incidence" in entry["outcomeHints"]
    assert "critical-harms-signal" in entry["flags"]
    assert "S5-gi-harms-primary" in entry["suggestedStrata"]


def test_glycogen_hint_is_supporting_not_used_as_exclusion():
    entry = by_id(build([candidate(
        "x", title="Carbohydrate feeding and muscle glycogen after cycling",
        abstract="Muscle biopsy glycogen concentration was measured post exercise.")]), "x")
    assert "muscle-glycogen-post-exercise" in entry["outcomeHints"]
    assert "S7-glycogen" in entry["suggestedStrata"]
    assert entry["autoDecision"] is None


def test_tte_and_tt_hints_remain_distinct():
    result = build([
        candidate("tt", title="Carbohydrate and cycling time trial performance"),
        candidate("tte", title="Carbohydrate and time to exhaustion during exercise"),
    ])
    assert "tt-completion-time" in by_id(result, "tt")["outcomeHints"]
    assert "time-to-exhaustion" not in by_id(result, "tt")["outcomeHints"]
    assert "time-to-exhaustion" in by_id(result, "tte")["outcomeHints"]


def test_oxidation_hint_recognises_exogenous_tracer_language():
    entry = by_id(build([candidate(
        "x", title="Exogenous carbohydrate oxidation during endurance exercise",
        abstract="13C tracer measured glucose and fructose oxidation rates.")]), "x")
    assert "exogenous-cho-oxidation-peak" in entry["outcomeHints"]
    assert "S4-exogenous-oxidation" in entry["suggestedStrata"]


def test_dose_rate_signals_are_hints_not_final_strata_assignment():
    entry = by_id(build([candidate(
        "x", title="90 g/h carbohydrate during cycling",
        abstract="Athletes ingested 90 g h-1 glucose-fructose.")]), "x")
    assert entry["doseSignals"]
    assert any(signal["bandHint"] == "very-high" for signal in entry["doseSignals"])
    assert entry["strataAssignmentFinal"] is False


# ---------------------------------------------------------------------------
# lanes and source-kind separation
# ---------------------------------------------------------------------------

def test_registry_records_use_separate_lane():
    entry = by_id(build([candidate(
        "r", kind="registry-record", title="Carbohydrate during exercise",
        registry="NCT00000001")]), "r")
    assert entry["screeningLane"] == "registry-review"
    assert entry["requiresHumanScreening"] is True


def test_identifier_conflict_has_priority_lane():
    c = candidate("x", title="Carbohydrate exercise")
    result = build([c], conflicts=[{
        "candidateId": "x", "distinctValues": {"pmid": ["1", "2"]},
        "action": "human-review",
    }])
    entry = by_id(result, "x")
    assert entry["screeningLane"] == "identity-review"
    assert "identifier-conflict" in entry["flags"]


def test_title_ambiguity_is_flagged_but_not_merged():
    items = [candidate("a", title="Same title"), candidate("b", title="Same title")]
    result = build(items, ambiguities=[{
        "normalisedTitle": "same title", "candidateIds": ["a", "b"],
        "entityKinds": ["publication"], "action": "human-review-never-auto-merge",
    }])
    assert len(result["queue"]) == 2
    assert all("title-ambiguity" in by_id(result, cid)["flags"] for cid in ("a", "b"))


def test_review_or_guideline_uses_separate_lane_but_is_not_excluded():
    entry = by_id(build([candidate(
        "r", title="Carbohydrate for endurance athletes: a systematic review",
        publication_types=["Systematic Review", "Review"])]), "r")
    assert entry["screeningLane"] == "review-source-review"
    assert "review-or-guideline" in entry["flags"]
    assert entry["autoDecision"] is None


def test_animal_signal_uses_separate_lane_but_is_not_excluded():
    entry = by_id(build([candidate(
        "a", title="Carbohydrate feeding and muscle glycogen in trained rats")]), "a")
    assert entry["screeningLane"] == "animal-signal-review"
    assert "animal-signal" in entry["flags"]
    assert entry["autoDecision"] is None


def test_postexercise_only_signal_is_flagged():
    entry = by_id(build([candidate(
        "p", title="Post-exercise carbohydrate feeding and glycogen resynthesis",
        abstract="Trained athletes consumed glucose during recovery.")]), "p")
    assert "post-exercise-only-signal" in entry["flags"]
    assert entry["autoDecision"] is None


def test_lane_precedence_is_safety_identity_registry_review_animal_standard():
    items = [
        candidate("standard", title="Carbohydrate cycling"),
        candidate("animal", title="Carbohydrate cycling in rats"),
        candidate("review", title="Carbohydrate cycling review",
                  publication_types=["Review"]),
        candidate("registry", kind="registry-record", registry="NCT00000001",
                  title="Carbohydrate cycling"),
        candidate("identity", title="Carbohydrate cycling"),
        candidate("safety", title="RED-S carbohydrate athlete"),
    ]
    result = build(items, conflicts=[{
        "candidateId": "identity", "distinctValues": {"pmid": ["1", "2"]},
        "action": "human-review",
    }])
    order = [e["candidateId"] for e in result["queue"]]
    assert (order.index("safety") < order.index("identity")
            < order.index("registry") < order.index("review")
            < order.index("animal") < order.index("standard"))


# ---------------------------------------------------------------------------
# deterministic, auditable output
# ---------------------------------------------------------------------------

def test_queue_order_is_input_order_independent():
    items = [
        candidate("a", title="Exercise"),
        candidate("b", title="Carbohydrate during cycling time trial"),
        candidate("c", title="Unrelated"),
    ]
    one = [e["candidateId"] for e in build(items)["queue"]]
    two = [e["candidateId"] for e in build(list(reversed(items)))["queue"]]
    assert one == two


def test_manifest_accounts_for_every_tier_and_lane():
    result = build([
        candidate("a", title="Carbohydrate during cycling time trial"),
        candidate("b", title="Unrelated"),
    ])
    manifest = result["manifest"]
    assert sum(manifest["countByPriorityTier"].values()) == 2
    assert sum(manifest["countByScreeningLane"].values()) == 2
    assert manifest["autoExcludedCount"] == 0
    assert manifest["requiresHumanScreeningCount"] == 2


def test_rule_version_and_input_hash_are_recorded():
    manifest = build([candidate("a")])["manifest"]
    assert manifest["screeningRuleVersion"].startswith("b11-screening/")
    assert manifest["candidatePoolHash"].startswith("sha256:")
    assert manifest["searchContractHash"] == "sha256:" + "b" * 64


def test_queue_entries_have_rule_ids_not_only_scores():
    entry = by_id(build([candidate("x", title="Carbohydrate cycling")]), "x")
    assert entry["matchedRuleIds"]
    assert all(rule.startswith("SCREEN-") for rule in entry["matchedRuleIds"])


# ---------------------------------------------------------------------------
# filesystem integration
# ---------------------------------------------------------------------------

def make_pool(tmp: str) -> Path:
    root = Path(tmp) / "run"
    pool = root / "candidate-pool"
    pool.mkdir(parents=True)
    items = [candidate("a", title="Carbohydrate during cycling time trial"),
             candidate("b", title="Unrelated")]
    (pool / "candidates.json").write_text(json.dumps(items), encoding="utf-8")
    (pool / "identifier-conflicts.json").write_text("[]", encoding="utf-8")
    (pool / "title-ambiguities.json").write_text("[]", encoding="utf-8")
    (pool / "manifest.json").write_text(json.dumps({
        "runId": "r1", "searchContractHash": "sha256:" + "b" * 64,
        "candidateCount": 2, "completeAcrossContractSources": False,
    }), encoding="utf-8")
    return root


def test_build_from_run_root_writes_queue_files_atomically():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_pool(tmp)
        result = screening.build_from_run_root(root)
        out = root / "screening-queue"
        assert result["candidateCount"] == 2
        for name in ("manifest.json", "queue.json", "summary.json"):
            assert (out / name).is_file()
        assert not list(out.glob("*.tmp"))


def test_build_from_run_root_rejects_candidate_count_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_pool(tmp)
        manifest = root / "candidate-pool" / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["candidateCount"] = 99
        manifest.write_text(json.dumps(data), encoding="utf-8")
        try:
            screening.build_from_run_root(root)
        except ValueError as exc:
            assert "count" in str(exc).lower() or "筆數" in str(exc)
            return
    raise AssertionError("candidate pool 筆數漂移必須拒絕")


def test_existing_queue_requires_redo_and_archives_old_output():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_pool(tmp)
        screening.build_from_run_root(root)
        try:
            screening.build_from_run_root(root)
        except FileExistsError:
            pass
        else:
            raise AssertionError("已有 queue 時應要求 --redo")
        screening.build_from_run_root(root, redo=True)
        assert list((root / "previous-screening-queues").iterdir())


def test_dry_run_does_not_write_queue():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_pool(tmp)
        result = screening.build_from_run_root(root, dry_run=True)
        assert result["candidateCount"] == 2
        assert not (root / "screening-queue").exists()
