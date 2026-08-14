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


def build(items: list[dict], *, conflicts=None, ambiguities=None,
          source_coverage=None, complete_across_contract_sources=True):
    return screening.build_queue(
        items,
        candidate_pool_hash="sha256:" + "a" * 64,
        search_contract_hash="sha256:" + "b" * 64,
        run_id="test-run",
        identifier_conflicts=conflicts or [],
        title_ambiguities=ambiguities or [],
        source_coverage=source_coverage or {
            "pubmed": "completed", "europe-pmc": "completed",
            "openalex": "completed", "clinicaltrials-gov": "completed",
        },
        complete_across_contract_sources=complete_across_contract_sources,
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


def test_animal_signal_catches_non_mammalian_and_livestock_species():
    """W1：草魚案例（audit 22f634d2325d 第 35 筆）證實舊詞表只涵蓋哺乳實驗動物。

    魚類／家禽／反芻獸研究會漏進 standard-screening，方向與誤剔風險相反：
    誤剔是少收，漏抓是主池混入非人體研究，直接推高篩選工時。
    """
    cases = {
        "carp": "Transcriptome analysis of grass carp between fast- and slow-growing fish",
        "zebrafish": "Glucose metabolism in zebrafish larvae during swimming",
        "salmon": "Dietary starch and hepatic lipogenesis in Atlantic salmon",
        "trout": "Carbohydrate utilisation in rainbow trout",
        "broiler": "Feed carbohydrate and growth performance in broiler chickens",
        "ovine": "Substrate oxidation during treadmill exercise in ovine models",
        "cattle": "Glycogen repletion in the skeletal muscle of cattle",
        "equine": "Dietary starch and exercise responses in equine athletes",
    }
    for cid, title in cases.items():
        entry = by_id(build([candidate(cid, title=title)]), cid)
        assert "animal-signal" in entry["flags"], f"{cid} 未被標為動物訊號"
        assert entry["screeningLane"] == "animal-signal-review", cid
        assert entry["autoDecision"] is None, cid


def test_animal_signal_does_not_fire_on_human_studies():
    """補詞不得把人體研究誤標成動物——誤標會讓真正該篩的文獻被分流出主池。"""
    human_titles = {
        "h1": "Carbohydrate ingestion during cycling in trained men",
        # 'fish oil'／'fishermen' 含 fish 字串但非動物實驗；\bfish\b 之外的
        # 詞邊界誤觸是本測試要擋的主要回歸。
        "h2": "Fish oil supplementation and endurance performance in humans",
        "h3": "Dietary intake of fishermen in coastal communities",
        # 'catheter' 含 'cat'、'ratio' 含 'rat'：詞邊界必須守住。
        "h4": "Arterial catheter measurements and the respiratory exchange ratio",
        # 以下三筆是真實池子裡實測到的誤標（15,425 筆全掃），加回裸詞
        # chicken／equine／calf 會讓它們被踢出主池：
        "h5": "Effect of preexercise electrolyte ingestion on fluid balance in "
              "men and women",                      # 摘要含 chicken noodle soup
        "h6": "Vitamin D deficiency in fatty liver disease: the chicken or the egg?",
        "h7": "Flaxseed supplement versus hormone replacement therapy in "
              "menopausal women",                   # 摘要含 conjugated equine estrogens
        "h8": "Calf muscle fatigue protocol and exercise-associated muscle cramps",
        # bovine 裸詞同樣不可加回：牛初乳是人體補劑、胎牛血清是體外試劑。
        "h9": "Oral supplementation with bovine colostrum decreases intestinal "
              "permeability in athletes",
    }
    # 觸發詞落在摘要而非標題的兩筆，必須連摘要一起餵進去才測得到。
    human_abstracts = {
        "h5": "Subjects cycled for 90 min after ingesting 355 ml of chicken "
              "noodle soup or a carbohydrate-electrolyte beverage.",
        "h7": "Participants took 0.625 mg of conjugated equine estrogens "
              "alone or combined with micronised progesterone.",
        "h8": "Participants performed a calf-fatiguing protocol to induce "
              "cramps in the calf muscle group.",
    }
    for cid, title in human_titles.items():
        entry = by_id(build([candidate(
            cid, title=title, abstract=human_abstracts.get(cid))]), cid)
        assert "animal-signal" not in entry["flags"], f"{cid} 被誤標為動物訊號"
        assert entry["screeningLane"] == "standard-screening", cid


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


def test_queue_is_never_sampling_ready_before_human_screening():
    manifest = build([candidate("a")])["manifest"]
    assert manifest["eligibleSamplingPoolReady"] is False
    assert manifest["blockingReasons"] == [
        "human-title-abstract-screening-not-completed"]


def test_incomplete_candidate_sources_add_sampling_blocker():
    manifest = build(
        [candidate("a")],
        source_coverage={
            "pubmed": "not-run", "europe-pmc": "completed",
            "openalex": "not-run", "clinicaltrials-gov": "completed",
        },
        complete_across_contract_sources=False,
    )["manifest"]
    assert manifest["candidateSourcesComplete"] is False
    assert manifest["blockingReasons"] == [
        "candidate-sources-incomplete",
        "human-title-abstract-screening-not-completed",
    ]


def test_missing_source_key_cannot_be_inferred_as_complete():
    manifest = build(
        [candidate("a")],
        source_coverage={"europe-pmc": "completed"},
        complete_across_contract_sources=False,
    )["manifest"]
    assert manifest["candidateSourcesComplete"] is False
    assert "candidate-sources-incomplete" in manifest["blockingReasons"]


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
        "candidateCount": 2,
        "sourceCoverage": {
            "pubmed": "not-run", "europe-pmc": "completed",
            "openalex": "not-run", "clinicaltrials-gov": "completed",
        },
        "completeAcrossContractSources": False,
    }), encoding="utf-8")
    return root


def test_build_from_run_root_writes_queue_files_atomically():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_pool(tmp)
        result = screening.build_from_run_root(root)
        out = root / "screening-queue"
        assert result["candidateCount"] == 2
        assert result["candidateSourcesComplete"] is False
        assert result["eligibleSamplingPoolReady"] is False
        assert "candidate-sources-incomplete" in result["blockingReasons"]
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
