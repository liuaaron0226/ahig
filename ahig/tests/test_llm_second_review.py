"""ADR-0007 盲化 LLM 第二審的測試。

核心不變量：

- 意見批次結構性禁止攜帶人類決策欄位（盲化）。
- 影子門檻：LLM 對任一人類 advance 判 exclude → 一票否決，不得切換。
- 歧異或任一方 unclear → 第二位人類；agreed 也仍是人類簽名的決定。
- 批次綁定 queue hash 與 prompt 雜湊；原始回應必須保留。
"""

from __future__ import annotations

from ahig.search import llm_second_review as llm

MANIFEST = {"screeningQueueHash": "sha256:" + "q" * 64, "runId": "run-1"}
QUEUE = [{"candidateId": f"c{i}"} for i in range(1, 7)]


def op(cid, opinion, response="raw model output"):
    return {"candidateId": cid, "opinion": opinion, "rawResponse": response}


def batch(opinions):
    return llm.build_opinion_batch(
        MANIFEST, QUEUE, opinions, model_id="model-x",
        model_version="2026-08-01", prompt_template="screen: {abstract}")


def test_batch_binds_queue_model_and_prompt_hash():
    b = batch([op("c1", "advance"), op("c2", "exclude")])
    assert b["screeningQueueHash"] == MANIFEST["screeningQueueHash"]
    assert b["model"] == {"id": "model-x", "version": "2026-08-01"}
    assert len(b["promptTemplateSha256"]) == 64
    assert b["opinionCount"] == 2
    assert b["llmReviewHash"]
    assert b["blindedToHumanDecisions"] is True


def test_batch_rejects_human_decision_fields_unknown_ids_and_bad_vocab():
    for bad in (
        {**op("c1", "advance"), "humanDecision": "advance"},   # 盲化違規
        op("c99", "advance"),                                   # 不在 queue
        op("c1", "include"),                                    # 詞彙錯誤
        op("c1", "advance", response="  "),                     # 沒留原始回應
    ):
        try:
            batch([bad])
        except llm.LlmReviewError:
            continue
        raise AssertionError(f"必須拒絕：{bad}")
    try:
        batch([op("c1", "advance"), op("c1", "exclude")])
    except llm.LlmReviewError:
        pass
    else:
        raise AssertionError("重複 candidateId 必須拒絕")


def test_shadow_gate_vetoes_any_missed_include():
    b = batch([op("c1", "exclude"), op("c2", "advance"),
               op("c3", "exclude")])
    human = {"c1": "advance", "c2": "advance", "c3": "exclude"}
    report = llm.shadow_gate(human, b)
    assert report["verdict"] == "fail"
    assert report["missedIncludeCandidateIds"] == ["c1"]
    assert "不得切換" in report["consequence"]


def test_shadow_gate_passes_zero_misses_within_disagreement_budget():
    b = batch([op("c1", "advance"), op("c2", "advance"),
               op("c3", "exclude"), op("c4", "exclude")])
    human = {"c1": "advance", "c2": "advance", "c3": "exclude",
             "c4": "exclude"}
    report = llm.shadow_gate(human, b)
    assert report["verdict"] == "pass"
    assert report["missedIncludeCandidateIds"] == []
    assert report["disagreementRate"] == 0.0


def test_shadow_gate_fails_on_excessive_disagreement_even_without_misses():
    # LLM 把人類的 exclude 全判成 advance：沒有漏報，但歧異率 3/4。
    b = batch([op("c1", "advance"), op("c2", "advance"),
               op("c3", "advance"), op("c4", "advance")])
    human = {"c1": "advance", "c2": "exclude", "c3": "exclude",
             "c4": "exclude"}
    report = llm.shadow_gate(human, b)
    assert report["missedIncludeCandidateIds"] == []
    assert report["disagreementRate"] == 0.75
    assert report["verdict"] == "fail"


def test_shadow_gate_counts_unclear_as_disagreement_not_miss():
    b = batch([op("c1", "unclear"), op("c2", "advance")])
    human = {"c1": "advance", "c2": "advance"}
    report = llm.shadow_gate(human, b, max_disagreement_rate=0.5)
    # unclear 不是漏報（它會進人工裁決），但算歧異。
    assert report["missedIncludeCandidateIds"] == []
    assert report["disagreementCandidateIds"] == ["c1"]
    assert report["verdict"] == "pass"


def test_shadow_gate_requires_full_llm_coverage():
    b = batch([op("c1", "advance")])
    try:
        llm.shadow_gate({"c1": "advance", "c2": "exclude"}, b)
    except llm.LlmReviewError as exc:
        assert "c2" in str(exc)
        return
    raise AssertionError("影子批次 LLM 覆蓋不全必須拒絕")


def test_adjudication_plan_routes_disagreement_and_unclear_to_second_human():
    b = batch([op("c1", "advance"), op("c2", "exclude"),
               op("c3", "unclear"), op("c4", "exclude")])
    human = {"c1": "advance", "c2": "advance", "c3": "advance",
             "c4": "exclude"}
    plan = llm.adjudication_plan(human, b)
    by_id = {row["candidateId"]: row for row in plan["needsSecondHuman"]}
    assert set(by_id) == {"c2", "c3"}
    assert by_id["c2"]["reason"] == "disagreement"
    assert by_id["c3"]["reason"] == "either-unclear"
    assert plan["agreedCount"] == 2
    assert {row["candidateId"] for row in plan["agreed"]} == {"c1", "c4"}
    # 一致的也仍是人類決定，不是自動生效。
    assert "人類簽名" in plan["note"]


def test_adjudication_plan_requires_llm_opinion_for_every_screened_record():
    b = batch([op("c1", "advance")])
    try:
        llm.adjudication_plan({"c1": "advance", "c5": "exclude"}, b)
    except llm.LlmReviewError as exc:
        assert "c5" in str(exc)
        return
    raise AssertionError("人類已篩但 LLM 未出意見必須拒絕")


# --- ADR-0009 機-機影子門檻（W8） ---------------------------------------

def batch_of(model_id, opinions):
    return llm.build_opinion_batch(
        MANIFEST, QUEUE, opinions, model_id=model_id,
        model_version="2026-08-01", prompt_template="screen: {abstract}")


def test_machine_gate_passes_when_two_models_agree():
    ops = [op("c1", "advance"), op("c2", "exclude"), op("c3", "exclude")]
    report = llm.machine_shadow_gate(batch_of("primary", ops),
                                     batch_of("secondary", ops))
    assert report["verdict"] == "pass"
    assert report["opposedCandidateIds"] == []
    assert report["disagreementRate"] == 0.0
    assert report["ownerAuditQueue"] == []
    assert report["adr"] == "ADR-0009"
    assert report["amends"] == "ADR-0007"
    assert report["shadowSampleSize"] == 3


def test_machine_gate_opposed_judgement_fails_regardless_of_rate():
    # 只有 1/6 歧異、遠低於 25% 上限，但那一筆是對立判讀 → 一票否決。
    primary = [op(f"c{i}", "exclude") for i in range(1, 7)]
    secondary = list(primary)
    secondary[0] = op("c1", "advance")
    report = llm.machine_shadow_gate(batch_of("primary", primary),
                                     batch_of("secondary", secondary))
    assert report["opposedCandidateIds"] == ["c1"]
    assert report["disagreementRate"] < report["maxDisagreementRate"]
    assert report["verdict"] == "fail"


def test_machine_gate_opposed_is_symmetric():
    """沒有金標準——誰判 advance 誰判 exclude，對立就是對立。"""
    a = [op("c1", "advance"), op("c2", "exclude")]
    b = [op("c1", "exclude"), op("c2", "exclude")]
    forward = llm.machine_shadow_gate(batch_of("p", a), batch_of("s", b))
    reverse = llm.machine_shadow_gate(batch_of("p", b), batch_of("s", a))
    assert forward["opposedCandidateIds"] == reverse["opposedCandidateIds"]


def test_machine_gate_unclear_counts_as_disagreement_but_not_opposed():
    ops_p = [op(f"c{i}", "exclude") for i in range(1, 7)]
    ops_s = list(ops_p)
    ops_s[0] = op("c1", "unclear")
    ops_s[1] = op("c2", "unclear")
    report = llm.machine_shadow_gate(batch_of("p", ops_p), batch_of("s", ops_s))
    assert report["opposedCandidateIds"] == []
    assert report["disagreementCandidateIds"] == ["c1", "c2"]
    # 兩邊都 unclear 也算歧異：它照樣要人看。
    both = [op("c1", "unclear"), op("c2", "exclude")]
    r2 = llm.machine_shadow_gate(batch_of("p", both), batch_of("s", both))
    assert r2["disagreementCandidateIds"] == ["c1"]


def test_machine_gate_fails_on_high_disagreement_rate():
    ops_p = [op(f"c{i}", "exclude") for i in range(1, 7)]
    ops_s = [op("c1", "unclear"), op("c2", "unclear"), op("c3", "unclear"),
             op("c4", "exclude"), op("c5", "exclude"), op("c6", "exclude")]
    report = llm.machine_shadow_gate(batch_of("p", ops_p), batch_of("s", ops_s))
    assert report["disagreementRate"] == 0.5
    assert report["verdict"] == "fail"
    assert report["ownerAuditQueue"] == ["c1", "c2", "c3"]


def test_machine_gate_rejects_same_model_same_hash_and_hash_mismatch():
    ops = [op("c1", "advance"), op("c2", "exclude")]
    same = batch_of("model-x", ops)
    # 同模型同內容 → llmReviewHash 相同，盲判前提不成立。
    for bad in (lambda: llm.machine_shadow_gate(same, same),
                lambda: llm.machine_shadow_gate(
                    batch_of("model-x", ops),
                    batch_of("model-x", [op("c1", "advance")]))):
        try:
            bad()
        except llm.LlmReviewError:
            continue
        raise AssertionError("同模型／同雜湊的兩批必須拒絕")


def test_machine_gate_rejects_different_queue_hash():
    ops = [op("c1", "advance")]
    other_manifest = {"screeningQueueHash": "sha256:" + "z" * 64,
                      "runId": "run-1"}
    other = llm.build_opinion_batch(
        other_manifest, QUEUE, ops, model_id="secondary",
        model_version="2026-08-01", prompt_template="screen: {abstract}")
    try:
        llm.machine_shadow_gate(batch_of("primary", ops), other)
    except llm.LlmReviewError as exc:
        assert "screeningQueueHash" in str(exc)
        return
    raise AssertionError("兩批綁定不同 queue hash 必須拒絕")


def test_machine_gate_rejects_coverage_mismatch_and_empty():
    try:
        llm.machine_shadow_gate(
            batch_of("primary", [op("c1", "advance"), op("c2", "exclude")]),
            batch_of("secondary", [op("c1", "advance")]))
    except llm.LlmReviewError as exc:
        assert "c2" in str(exc)
        return
    raise AssertionError("兩批覆蓋範圍不同必須拒絕")


def test_machine_gate_never_auto_adjudicates():
    """ADR-0009 原則 5：歧異一律進擁有者抽查，不自動裁決。"""
    ops_p = [op("c1", "advance"), op("c2", "exclude")]
    ops_s = [op("c1", "unclear"), op("c2", "exclude")]
    report = llm.machine_shadow_gate(batch_of("p", ops_p), batch_of("s", ops_s))
    assert report["ownerAuditQueue"] == report["disagreementCandidateIds"]
    assert "resolved" not in report and "decision" not in report


# --- 分層影子批次：歧異率分母限定純隨機子集 --------------------------

def test_machine_gate_rate_uses_only_the_random_subset():
    """補位段刻意過度取樣稀有分層，算進分母會讓歧異率偏離母體。"""
    ops_p = [op(f"c{i}", "exclude") for i in range(1, 7)]
    ops_s = list(ops_p)
    # c5、c6 是補位段，兩筆都歧異；主體 c1–c4 全同意。
    ops_s[4] = op("c5", "unclear")
    ops_s[5] = op("c6", "unclear")
    rate_ids = [f"c{i}" for i in range(1, 5)]
    report = llm.machine_shadow_gate(
        batch_of("p", ops_p), batch_of("s", ops_s), rate_candidate_ids=rate_ids)
    assert report["disagreementRate"] == 0.0
    assert report["disagreementRateDenominator"] == 4
    assert report["disagreementRateBasis"] == "random-subset"
    # 但歧異本身沒被吞掉：補位段照樣要進擁有者抽查。
    assert report["disagreementCandidateIds"] == ["c5", "c6"]
    assert report["ownerAuditQueue"] == ["c5", "c6"]
    full = llm.machine_shadow_gate(batch_of("p", ops_p), batch_of("s", ops_s))
    assert full["disagreementRate"] == 2 / 6
    assert full["disagreementRateDenominator"] == 6
    assert full["disagreementRateBasis"] == "full-batch"


def test_machine_gate_opposed_veto_still_scans_the_whole_batch():
    """對立是一票否決，覆蓋越大越好——不因為不在分母就漏掉。"""
    ops_p = [op(f"c{i}", "exclude") for i in range(1, 7)]
    ops_s = list(ops_p)
    ops_s[5] = op("c6", "advance")          # 對立筆落在補位段
    report = llm.machine_shadow_gate(
        batch_of("p", ops_p), batch_of("s", ops_s),
        rate_candidate_ids=[f"c{i}" for i in range(1, 6)])
    assert report["disagreementRate"] == 0.0
    assert report["opposedCandidateIds"] == ["c6"]
    assert report["verdict"] == "fail"


def test_machine_gate_rejects_alien_or_empty_rate_subset():
    ops = [op(f"c{i}", "exclude") for i in range(1, 7)]
    for bad in (["c1", "c99"], []):
        try:
            llm.machine_shadow_gate(batch_of("p", ops), batch_of("s", ops),
                                    rate_candidate_ids=bad)
        except llm.LlmReviewError:
            continue
        raise AssertionError(f"歧異率子集 {bad} 必須拒絕")
