"""AL 第三排序鍵：只准換順序，不准換去留。

這組測試的重點不是「排得準不準」——那要等真實標籤才驗得了——而是
**排序器不可能偷改 queue 的去留**。因此不變量測試（成員、lane、tier、
requiresHumanScreening、非目標 lane 順序）才是主體；排序行為只驗
「AL 分數確實是第三鍵，且不會蓋過 tier」。標籤全部是合成的。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ahig.search import active_learning as al
from ahig.search import screening

# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

POSITIVE = ("carbohydrate ingestion during prolonged cycling time trial "
            "in trained endurance athletes glucose fructose oxidation")
NEGATIVE = ("architectural survey of medieval cathedral masonry and "
            "stained glass restoration techniques in northern europe")


def entry(cid: str, *, lane="standard-screening", tier="T3-partial-signal",
          title="", score=10) -> dict:
    return {
        "candidateId": cid,
        "entityKind": "publication",
        "canonicalIdentity": f"source:{cid}",
        "title": title,
        "publicationYear": 2020,
        "identifiers": {},
        "screeningLane": lane,
        "priorityTier": tier,
        "priorityScore": score,
        "scoreBreakdown": {},
        "conceptMatches": [],
        "outcomeHints": [],
        "doseSignals": [],
        "suggestedStrata": [],
        "strataAssignmentFinal": False,
        "flags": [],
        "matchedRuleIds": ["SCREEN-000-no-signal"],
        "requiresHumanScreening": True,
        "requiredReviewMode": "human-plus-blinded-llm-title-abstract",
        "autoDecision": None,
    }


def synthetic_labelled(n_pos: int, n_neg: int, *, tier="T3-partial-signal"):
    """產生足以越過冷啟動門檻的合成已標記集。"""
    entries, labels = [], {}
    for i in range(n_pos):
        cid = f"pos-{i:03d}"
        entries.append(entry(cid, tier=tier, title=f"{POSITIVE} trial {i}"))
        labels[cid] = 1
    for i in range(n_neg):
        cid = f"neg-{i:03d}"
        entries.append(entry(cid, tier=tier, title=f"{NEGATIVE} volume {i}"))
        labels[cid] = 0
    return entries, labels


# ---------------------------------------------------------------------------
# 不變量：AL 不得改變任何一筆的去留
# ---------------------------------------------------------------------------

def test_rerank_never_adds_or_removes_candidates():
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i:03d}", title=POSITIVE if i % 2 else NEGATIVE)
                  for i in range(20)]
    result = al.rerank(labelled + unlabelled, labels)
    assert ({e["candidateId"] for e in result["queue"]}
            == {e["candidateId"] for e in labelled + unlabelled})
    assert len(result["queue"]) == 80


def test_rerank_never_changes_lane_tier_or_human_screening():
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i:03d}", title=POSITIVE if i % 2 else NEGATIVE)
                  for i in range(20)]
    queue = labelled + unlabelled
    result = al.rerank(queue, labels)
    before = {e["candidateId"]: e for e in queue}
    for got in result["queue"]:
        was = before[got["candidateId"]]
        assert got["screeningLane"] == was["screeningLane"]
        assert got["priorityTier"] == was["priorityTier"]
        assert got["priorityScore"] == was["priorityScore"]
        assert got["requiresHumanScreening"] is True
        assert got["autoDecision"] is None


def test_other_lanes_keep_their_exact_order():
    labelled, labels = synthetic_labelled(30, 30)
    others = [entry(f"safety-{i}", lane="safety-review", title=POSITIVE)
              for i in range(5)]
    others += [entry(f"animal-{i}", lane="animal-signal-review",
                     title=NEGATIVE) for i in range(5)]
    unlabelled = [entry(f"u-{i:03d}", title=POSITIVE) for i in range(10)]
    queue = others + labelled + unlabelled
    result = al.rerank(queue, labels)
    for lane in ("safety-review", "animal-signal-review"):
        seq_before = [e["candidateId"] for e in queue
                      if e["screeningLane"] == lane]
        seq_after = [e["candidateId"] for e in result["queue"]
                     if e["screeningLane"] == lane]
        assert seq_before == seq_after


def test_standard_lane_slots_do_not_move():
    """AL 重排只能在原本屬於 standard-screening 的位置之間洗牌。"""
    labelled, labels = synthetic_labelled(30, 30)
    queue = ([entry("safety-0", lane="safety-review")] + labelled
             + [entry(f"u-{i}", title=POSITIVE) for i in range(10)]
             + [entry("registry-0", lane="registry-review")])
    result = al.rerank(queue, labels)
    slots_before = [i for i, e in enumerate(queue)
                    if e["screeningLane"] == al.TARGET_LANE]
    slots_after = [i for i, e in enumerate(result["queue"])
                   if e["screeningLane"] == al.TARGET_LANE]
    assert slots_before == slots_after
    assert result["queue"][0]["candidateId"] == "safety-0"
    assert result["queue"][-1]["candidateId"] == "registry-0"


def test_invariant_guard_rejects_tampered_queue():
    """守門本身要會炸——否則不變量測試等於沒測。"""
    before = [entry("a"), entry("b")]
    after = [entry("a"), dict(entry("b"), screeningLane="safety-review")]
    try:
        al._assert_invariants(before, after)
    except al.ActiveLearningError as exc:
        assert "screeningLane" in str(exc)
    else:
        raise AssertionError("改動 lane 竟然沒有被擋下")


def test_invariant_guard_rejects_dropped_candidate():
    try:
        al._assert_invariants([entry("a"), entry("b")], [entry("a")])
    except al.ActiveLearningError as exc:
        assert "長度" in str(exc)
    else:
        raise AssertionError("少一筆竟然沒有被擋下")


# ---------------------------------------------------------------------------
# 冷啟動
# ---------------------------------------------------------------------------

def test_cold_start_keeps_regex_order_untouched():
    labelled, labels = synthetic_labelled(3, 3)
    unlabelled = [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    queue = labelled + unlabelled
    result = al.rerank(queue, labels)
    assert result["provenance"]["alEnabled"] is False
    assert "cold-start" in result["provenance"]["disabledReason"]
    assert ([e["candidateId"] for e in result["queue"]]
            == [e["candidateId"] for e in queue])


def test_no_labels_at_all_is_a_no_op():
    queue = [entry(f"u-{i}", title=POSITIVE) for i in range(10)]
    result = al.rerank(queue, {})
    assert result["provenance"]["alEnabled"] is False
    assert result["provenance"]["labelledCount"] == 0
    assert ([e["candidateId"] for e in result["queue"]]
            == [e["candidateId"] for e in queue])


def test_empty_vocabulary_falls_back_instead_of_crashing():
    """同質語料 ＋ max_df=0.95 會把詞彙表剪空；AL 壞掉不該拖垮篩選管線。"""
    entries, labels = [], {}
    for i in range(60):
        cid = f"same-{i:03d}"
        entries.append(entry(cid, title="identical text"))
        labels[cid] = i % 2
    unlabelled = [entry(f"u-{i}", title="identical text") for i in range(5)]
    result = al.rerank(entries + unlabelled, labels)
    assert result["provenance"]["alEnabled"] is False
    assert "退回 regex tier 順序" in result["provenance"]["disabledReason"]
    assert ([e["candidateId"] for e in result["queue"]]
            == [e["candidateId"] for e in entries + unlabelled])


def test_single_class_labels_fall_back_instead_of_crashing():
    """全部都是 exclude 時 balanced 權重無定義；要退回而不是炸掉整條管線。"""
    labelled, labels = synthetic_labelled(0, 60)
    unlabelled = [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    result = al.rerank(labelled + unlabelled, labels)
    assert result["provenance"]["alEnabled"] is False
    assert "正負兩類" in result["provenance"]["disabledReason"]


# ---------------------------------------------------------------------------
# 排序行為：AL 是第三鍵，不是第一鍵
# ---------------------------------------------------------------------------

def test_tier_still_outranks_al_score():
    """高 tier 的低分候選，仍必須排在低 tier 的高分候選前面。"""
    labelled, labels = synthetic_labelled(30, 30)
    # T1 但文字像負例（AL 分數低）、T4 但文字像正例（AL 分數高）
    weak_high_tier = entry("weak-t1", tier="T1-high-signal", title=NEGATIVE)
    strong_low_tier = entry("strong-t4", tier="T4-broad-signal", title=POSITIVE)
    queue = labelled + [strong_low_tier, weak_high_tier]
    result = al.rerank(queue, labels)
    order = [e["candidateId"] for e in result["queue"]]
    assert order.index("weak-t1") < order.index("strong-t4")


def test_al_orders_within_the_same_tier():
    labelled, labels = synthetic_labelled(30, 30)
    looks_relevant = entry("u-relevant", title=POSITIVE)
    looks_irrelevant = entry("u-irrelevant", title=NEGATIVE)
    # 刻意讓不相關者在前，若 AL 生效就會被換到後面
    queue = labelled + [looks_irrelevant, looks_relevant]
    result = al.rerank(queue, labels)
    assert result["provenance"]["alEnabled"] is True
    order = [e["candidateId"] for e in result["queue"]]
    assert order.index("u-relevant") < order.index("u-irrelevant")


def test_already_labelled_entries_sink_below_unlabelled_in_same_tier():
    """已標記者已經篩過了，不該再佔據人工佇列前段。"""
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    result = al.rerank(labelled + unlabelled, labels)
    lane = [e["candidateId"] for e in result["queue"]
            if e["screeningLane"] == al.TARGET_LANE]
    last_unlabelled = max(lane.index(e["candidateId"]) for e in unlabelled)
    first_labelled = min(lane.index(cid) for cid in labels)
    assert last_unlabelled < first_labelled


def test_rerank_is_deterministic():
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i:03d}", title=POSITIVE if i % 3 else NEGATIVE)
                  for i in range(15)]
    queue = labelled + unlabelled
    first = al.rerank(queue, labels)
    second = al.rerank(queue, labels)
    assert ([e["candidateId"] for e in first["queue"]]
            == [e["candidateId"] for e in second["queue"]])
    assert (first["provenance"]["labelledSetHash"]
            == second["provenance"]["labelledSetHash"])


def test_entry_objects_are_not_mutated():
    """AL 分數不得寫進 entry，否則會污染 screeningQueueHash。"""
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    queue = labelled + unlabelled
    snapshot = json.dumps(queue, sort_keys=True, ensure_ascii=False)
    al.rerank(queue, labels)
    assert json.dumps(queue, sort_keys=True, ensure_ascii=False) == snapshot


# ---------------------------------------------------------------------------
# provenance 落盤
# ---------------------------------------------------------------------------

def test_provenance_records_hyperparameters_and_versions():
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    prov = al.rerank(labelled + unlabelled, labels)["provenance"]
    assert prov["rankerVersion"] == al.RANKER_VERSION
    assert prov["sklearnVersion"]
    assert prov["hyperparameters"]["svm"] == {"loss": "squared_hinge", "C": 0.11}
    assert prov["hyperparameters"]["balancerRatio"] == 9.8
    assert prov["hyperparameters"]["tfidf"]["ngram_range"] == [1, 2]
    assert prov["hyperparameters"]["tfidf"]["sublinear_tf"] is True
    assert prov["hyperparameters"]["tfidf"]["min_df"] == 1
    assert prov["hyperparameters"]["tfidf"]["max_df"] == 0.95
    assert prov["labelledSetHash"].startswith("sha256:")
    assert prov["labelledCount"] == 60


def test_labelled_set_hash_changes_when_a_label_flips():
    labelled, labels = synthetic_labelled(30, 30)
    unlabelled = [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    queue = labelled + unlabelled
    before = al.rerank(queue, labels)["provenance"]["labelledSetHash"]
    flipped = dict(labels)
    flipped["pos-000"] = 0
    after = al.rerank(queue, flipped)["provenance"]["labelledSetHash"]
    assert before != after


# ---------------------------------------------------------------------------
# 超參數與上游一致（照抄的東西不准被順手改掉）
# ---------------------------------------------------------------------------

def test_hyperparameters_match_asreview_elas_u4():
    assert al.SVM_PARAMS == {"loss": "squared_hinge", "C": 0.11}
    assert al.BALANCER_RATIO == 9.8
    assert al.TFIDF_PARAMS == {
        "ngram_range": (1, 2), "sublinear_tf": True,
        "min_df": 1, "max_df": 0.95,
    }


def test_balanced_sample_weight_matches_asreview_formula():
    """逐行對應 ASReview Balanced.compute_sample_weight。"""
    labels = [1] * 4 + [0] * 16
    weights = al._balanced_sample_weight(labels, 9.8)
    expected_neg = 4 / (9.8 * 16)
    raw = [1.0] * 4 + [expected_neg] * 16
    scale = len(labels) / sum(raw)
    assert all(abs(w - r * scale) < 1e-12 for w, r in zip(weights, raw))
    assert abs(sum(weights) - len(labels)) < 1e-9


# ---------------------------------------------------------------------------
# run-root 介面
# ---------------------------------------------------------------------------

def test_rerank_run_root_does_not_touch_screening_queue():
    labelled, labels = synthetic_labelled(30, 30)
    queue = labelled + [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        qdir = root / "screening-queue"
        qdir.mkdir(parents=True)
        (qdir / "queue.json").write_text(json.dumps(queue), encoding="utf-8")
        manifest = {"runId": "test-run",
                    "screeningQueueHash": screening.content_hash(queue),
                    "screeningRuleVersion": screening.RULE_VERSION}
        (qdir / "manifest.json").write_text(json.dumps(manifest),
                                            encoding="utf-8")
        rdir = root / "screening-decisions"
        rdir.mkdir(parents=True)
        (rdir / "reconciliation.json").write_text(json.dumps({
            "resolved": [{"candidateId": cid,
                          "decision": "advance" if v else "exclude"}
                         for cid, v in labels.items()]}), encoding="utf-8")

        before = (qdir / "queue.json").read_bytes()
        prov = al.rerank_run_root(root)

        assert (qdir / "queue.json").read_bytes() == before
        assert prov["screeningQueueHash"] == manifest["screeningQueueHash"]
        assert prov["alEnabled"] is True
        order = json.loads((root / "al-rank" / "ranked-order.json")
                           .read_text(encoding="utf-8"))
        assert sorted(order) == sorted(e["candidateId"] for e in queue)


def test_unclear_decisions_are_not_used_as_labels():
    recon = {"resolved": [
        {"candidateId": "a", "decision": "advance"},
        {"candidateId": "b", "decision": "exclude"},
        {"candidateId": "c", "decision": "unclear"},
    ]}
    assert al._decision_labels(recon) == {"a": 1, "b": 0}


# ---------------------------------------------------------------------------
# W10 追加（第 n+16 輪步驟 1-2）：影子批次的 machine-reconciliation
# 「concordant/opinion」形制也要能餵冷啟動，不只 human 路徑的
# 「resolved/decision」——兩者都是「已解決的標籤」，只是欄位名不同。
# ---------------------------------------------------------------------------

def test_decision_labels_also_reads_machine_reconciliation_concordant():
    recon = {"concordant": [
        {"candidateId": "a", "opinion": "advance"},
        {"candidateId": "b", "opinion": "exclude"},
        {"candidateId": "c", "opinion": "unclear"},
    ]}
    assert al._decision_labels(recon) == {"a": 1, "b": 0}


def test_decision_labels_merges_resolved_and_concordant_when_both_present():
    recon = {
        "resolved": [{"candidateId": "a", "decision": "advance"}],
        "concordant": [{"candidateId": "b", "opinion": "exclude"}],
    }
    assert al._decision_labels(recon) == {"a": 1, "b": 0}


def test_rerank_run_root_reads_machine_reconciliation_shape():
    """screening-decisions/reconciliation.json 可以是 reconcile_machine
    的產物（concordant/opinion），不是只有人類路徑的 resolved/decision。"""
    labelled, labels = synthetic_labelled(30, 30)
    queue = labelled + [entry(f"u-{i}", title=POSITIVE) for i in range(5)]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        qdir = root / "screening-queue"
        qdir.mkdir(parents=True)
        (qdir / "queue.json").write_text(json.dumps(queue), encoding="utf-8")
        manifest = {"runId": "test-run",
                    "screeningQueueHash": screening.content_hash(queue),
                    "screeningRuleVersion": screening.RULE_VERSION}
        (qdir / "manifest.json").write_text(json.dumps(manifest),
                                            encoding="utf-8")
        rdir = root / "screening-decisions"
        rdir.mkdir(parents=True)
        (rdir / "reconciliation.json").write_text(json.dumps({
            "concordant": [{"candidateId": cid,
                           "opinion": "advance" if v else "exclude"}
                          for cid, v in labels.items()]}), encoding="utf-8")

        prov = al.rerank_run_root(root)
        assert prov["alEnabled"] is True
        order = json.loads((root / "al-rank" / "ranked-order.json")
                           .read_text(encoding="utf-8"))
        assert sorted(order) == sorted(e["candidateId"] for e in queue)
