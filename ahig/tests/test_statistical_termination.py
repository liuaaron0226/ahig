"""ADR-0008 統計終止的測試。

核心不變量：

- p 值與閉式解一致；證據不足（p ≥ α）預設繼續篩。
- unclear 一律當相關計算（往「更難停」的方向）。
- safety-review 與 critical-harms-signal 未篩畢 → 不得終止。
- 尾端是 not-screened 不是 excluded；抽驗出現 advance/unclear 即恢復。
- 抽驗種子從 queue hash 導出，確定性、無從挑選。
"""

from __future__ import annotations

import math

from ahig.search import statistical_termination as st


def queue(n, *, safety=(), harms=()):
    entries = []
    for i in range(1, n + 1):
        cid = f"c{i}"
        entries.append({
            "candidateId": cid,
            "screeningLane": ("safety-review" if cid in safety
                              else "standard-screening"),
            "flags": ["critical-harms-signal"] if cid in harms else [],
        })
    return entries


def test_p_score_matches_closed_form_for_zero_relevant():
    # rho=0 → k_target=1；篩 50/100 全不相關：
    # p = C(99,50)/C(100,50) = (100-50)/100 = 0.5
    score = st.p_score([0] * 50, 100)
    assert abs(score["pScore"] - 0.5) < 1e-12
    assert score["h0MinTotalRelevant"] == 1
    assert score["windowSize"] == 50


def test_p_score_matches_closed_form_for_trailing_zero_run():
    # rho=1（第一篇），之後 49 篇 0；τ=0.95 → k_target=2 → 視窗起點剩餘
    # 池 99 篇至少 1 篇相關：p = Π_{i=0..48} (98-i)/(99-i) = 50/99
    labels = [1] + [0] * 49
    score = st.p_score(labels, 100)
    assert abs(score["pScore"] - 50 / 99) < 1e-12
    assert score["windowSize"] == 49


def test_p_score_uses_exact_integer_boundary_arithmetic():
    # rho=18、τ=0.9：18/20 = 0.9 不小於 0.9，所以 k_target 必須是 21。
    # 浮點除法（int(18/0.9)+1 = 20）會在這裡反保守。
    labels = [1] * 18 + [0] * 10
    score = st.p_score(labels, 200, target_recall=0.9)
    assert score["h0MinTotalRelevant"] == 21


def test_p_score_monotone_decreasing_in_tail_length():
    prev = 1.0
    for tail in (10, 30, 60):
        p = st.p_score([1] + [0] * tail, 200)["pScore"]
        assert p < prev
        prev = p


def test_p_score_edges():
    assert st.p_score([], 100)["pScore"] == 1.0
    # 最後一篇就是相關 → 對尾段乾涸毫無證據
    assert st.p_score([0, 1], 100)["pScore"] == 1.0
    # H0 需要的相關數超過剩餘池 → H0 不可能
    labels = [1] * 90 + [0] * 9
    score = st.p_score(labels, 99, target_recall=0.5)
    assert score["pScore"] == 0.0


def test_unclear_counts_as_relevant_making_stopping_harder():
    q = queue(100)
    base = [(f"c{i}", "exclude") for i in range(1, 51)]
    with_unclear = base[:-1] + [("c50", "unclear")] + [
        (f"c{i}", "exclude") for i in range(51, 56)]
    p_base = st.evaluate_termination(q, base)["pScore"]
    p_unclear = st.evaluate_termination(q, with_unclear)["pScore"]
    # unclear 重置了尾段視窗，p 必須變大（更難停）。
    assert p_unclear > p_base


def test_termination_blocked_until_safety_and_harms_screened():
    q = queue(100, safety={"c99"}, harms={"c98"})
    decisions = [(f"c{i}", "exclude") for i in range(1, 91)]
    result = st.evaluate_termination(q, decisions)
    assert result["mandatoryLanesFullyScreened"] is False
    assert set(result["mandatoryUnscreenedCandidateIds"]) == {"c98", "c99"}
    assert result["allowedToStop"] is False
    assert "不得終止" in result["reason"]


def test_termination_allowed_when_p_below_alpha_and_preconditions_met():
    q = queue(400)
    # 篩 300 篇全不相關：p = C(399,300)/C(400,300) = 100/400 = 0.25 → 不停
    some = [(f"c{i}", "exclude") for i in range(1, 301)]
    mid = st.evaluate_termination(q, some)
    assert abs(mid["pScore"] - 0.25) < 1e-12
    assert mid["allowedToStop"] is False
    assert "繼續篩" in mid["reason"]
    # 篩 390 篇全不相關：p = 10/400 = 0.025 < 0.05 → 允許終止
    more = [(f"c{i}", "exclude") for i in range(1, 391)]
    done = st.evaluate_termination(q, more)
    assert abs(done["pScore"] - 10 / 400) < 1e-12
    assert done["allowedToStop"] is True
    assert done["notScreenedCount"] == 10
    assert done["notScreenedIsNotExcluded"] is True
    assert done["terminationEvidenceHash"]


def test_termination_rejects_unknown_duplicate_or_bad_decisions():
    q = queue(10)
    for bad in ([("c99", "exclude")],
                [("c1", "exclude"), ("c1", "exclude")],
                [("c1", "include")]):
        try:
            st.evaluate_termination(q, bad)
        except st.TerminationError:
            continue
        raise AssertionError(f"必須拒絕：{bad}")


def test_tail_spot_check_is_deterministic_and_seed_derived():
    ids = [f"c{i}" for i in range(1, 500)]
    one = st.draw_tail_spot_check(ids, queue_hash="sha256:" + "q" * 64)
    two = st.draw_tail_spot_check(ids, queue_hash="sha256:" + "q" * 64)
    assert one["candidateIds"] == two["candidateIds"]
    assert one["sampleSize"] == st.DEFAULT_TAIL_SPOT_CHECK_N
    assert one["seedDerivation"] == "derived-from-queue-hash"
    other = st.draw_tail_spot_check(ids, queue_hash="sha256:" + "r" * 64)
    assert other["candidateIds"] != one["candidateIds"]


def test_tail_spot_check_resumes_on_any_advance_or_unclear():
    ids = [f"c{i}" for i in range(1, 50)]
    sample = st.draw_tail_spot_check(ids, queue_hash="sha256:" + "q" * 64,
                                     n=10)
    clean = {cid: "exclude" for cid in sample["candidateIds"]}
    ok = st.evaluate_tail_spot_check(sample, clean)
    assert ok["resumeScreening"] is False

    dirty = dict(clean)
    dirty[sample["candidateIds"][3]] = "advance"
    hit = st.evaluate_tail_spot_check(sample, dirty)
    assert hit["resumeScreening"] is True

    unclear = dict(clean)
    unclear[sample["candidateIds"][5]] = "unclear"
    assert st.evaluate_tail_spot_check(sample, unclear)[
        "resumeScreening"] is True

    incomplete = dict(clean)
    incomplete.pop(sample["candidateIds"][0])
    try:
        st.evaluate_tail_spot_check(sample, incomplete)
    except st.TerminationError:
        pass
    else:
        raise AssertionError("抽驗未完成必須拒絕")


def test_review_mode_follows_adr_0007():
    """queue 端的審查模式：安全/critical-harms 雙人，其餘 human+LLM。"""
    from ahig.search import screening
    candidates = [
        {"candidateId": "std", "entityKind": "publication",
         "canonicalIdentity": "doi:10.1/std",
         "title": "Carbohydrate and time trial",
         "abstract": "Cyclists ingested carbohydrate in a time trial.",
         "identifiers": {}, "publicationTypes": [], "isPreprint": False},
        {"candidateId": "safety", "entityKind": "publication",
         "canonicalIdentity": "doi:10.1/safety",
         "title": "Low energy availability in athletes",
         "abstract": "Athletes with low energy availability were studied.",
         "identifiers": {}, "publicationTypes": [], "isPreprint": False},
        {"candidateId": "harms", "entityKind": "publication",
         "canonicalIdentity": "doi:10.1/harms",
         "title": "Gastrointestinal symptoms during exercise",
         "abstract": "GI distress and nausea during cycling were recorded.",
         "identifiers": {}, "publicationTypes": [], "isPreprint": False},
    ]
    built = screening.build_queue(
        candidates, candidate_pool_hash="sha256:" + "p" * 64,
        search_contract_hash="sha256:" + "s" * 64, run_id="r1",
        identifier_conflicts=[], title_ambiguities=[],
        source_coverage={}, complete_across_contract_sources=True)
    modes = {e["candidateId"]: e["requiredReviewMode"]
             for e in built["queue"]}
    assert modes["std"] == "human-plus-blinded-llm-title-abstract"
    assert modes["safety"] == "dual-blind-title-abstract"
    assert modes["harms"] == "dual-blind-title-abstract"
    assert screening.RULE_VERSION == "b11-screening/1.3.0"
    assert all(e["requiresHumanScreening"] is True for e in built["queue"])
    assert all(e["autoDecision"] is None for e in built["queue"])