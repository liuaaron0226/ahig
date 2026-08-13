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
