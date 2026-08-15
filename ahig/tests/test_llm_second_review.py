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


# --- W10：session-native 判讀路徑（ADR-0009 裁定①，不硬套 ADR-0007 的
# API prompt 假設；正式 gate 慣例，第 n+15 輪裁定 4） -----------------

PROTOCOL = {
    "scopeContractSha256": "sha256:" + "p" * 64,
    "worksheetSha256": "sha256:" + "w" * 64,
    "boardReference": "COORDINATION.md 第 20-21 輪判讀慣例",
}


def session_batch(model_id, opinions, protocol=None):
    return llm.build_session_opinion_batch(
        MANIFEST, QUEUE, opinions, model_id=model_id,
        model_version="session-native; no dated snapshot exposed; "
                      "judged 2026-08-15",
        judging_protocol=protocol or PROTOCOL)


def test_session_batch_binds_queue_model_and_protocol_hash_not_prompt():
    b = session_batch("model-x", [op("c1", "advance"), op("c2", "exclude")])
    assert b["screeningQueueHash"] == MANIFEST["screeningQueueHash"]
    assert b["model"]["id"] == "model-x"
    assert b["judgeMode"] == "session-native"
    assert b["judgingProtocol"] == PROTOCOL
    assert len(b["judgingProtocolHash"]) > 0
    assert "promptTemplate" not in b
    assert "promptTemplateSha256" not in b
    assert b["opinionCount"] == 2
    assert b["llmReviewHash"]
    assert b["blindedToHumanDecisions"] is True


def test_session_batch_rejects_incomplete_judging_protocol():
    for missing_key in ("scopeContractSha256", "worksheetSha256", "boardReference"):
        bad = {k: v for k, v in PROTOCOL.items() if k != missing_key}
        try:
            session_batch("model-x", [op("c1", "advance")], protocol=bad)
        except llm.LlmReviewError as exc:
            assert missing_key in str(exc)
            continue
        raise AssertionError(f"缺 {missing_key} 的 judging_protocol 必須拒絕")


def test_session_batch_same_blinding_rules_as_api_batch():
    """複用 build_opinion_batch 的驗證：盲化違規/未知 id/詞彙錯誤同樣拒絕。"""
    for bad in (
        {**op("c1", "advance"), "humanDecision": "advance"},
        op("c99", "advance"),
        op("c1", "include"),
    ):
        try:
            session_batch("model-x", [bad])
        except llm.LlmReviewError:
            continue
        raise AssertionError(f"session batch 必須拒絕：{bad}")


def test_machine_gate_accepts_mixed_api_and_session_batches():
    """gate 端不挑批次形制：一邊 API prompt、一邊 session-native 皆可比對。"""
    ops = [op("c1", "advance"), op("c2", "exclude"), op("c3", "exclude")]
    report = llm.machine_shadow_gate(
        batch_of("primary", ops), session_batch("secondary", ops))
    assert report["verdict"] == "pass"
    assert report["opposedCandidateIds"] == []


def test_machine_gate_two_session_batches_different_models():
    ops_p = [op("c1", "advance"), op("c2", "exclude"), op("c3", "exclude")]
    ops_s = [op("c1", "advance"), op("c2", "unclear"), op("c3", "exclude")]
    report = llm.machine_shadow_gate(
        session_batch("claude-opus-5", ops_p), session_batch("claude-sonnet-5", ops_s))
    assert report["disagreementCandidateIds"] == ["c2"]
    assert report["opposedCandidateIds"] == []


# --- W10：ownerAuditQueue 擁有者裁決紀錄（第 n+15 輪裁定 4(b)） -------

def owner_decision(decision="advance", reason="recall 優先，全文再核"):
    return {"decidedBy": "owner", "decision": decision,
            "decidedAt": "2026-08-15", "reasonShort": reason}


def test_owner_decision_resolves_opposed_case_and_flips_verdict():
    # 6 筆中只有 c1 對立、其餘全同意 → 歧異率 1/6 本來就在門檻內，
    # 這樣才能單獨測出「解掉對立否決」對 verdict 的效果，不被歧異率蓋過。
    primary = [op(f"c{i}", "exclude") for i in range(1, 7)]
    secondary = list(primary)
    secondary[0] = op("c1", "advance")
    without = llm.machine_shadow_gate(batch_of("p", primary), batch_of("s", secondary))
    assert without["verdict"] == "fail"
    assert without["unresolvedOpposedCandidateIds"] == ["c1"]

    with_decision = llm.machine_shadow_gate(
        batch_of("p", primary), batch_of("s", secondary),
        owner_decisions={"c1": owner_decision()})
    assert with_decision["opposedCandidateIds"] == ["c1"]
    assert with_decision["unresolvedOpposedCandidateIds"] == []
    assert with_decision["ownerDecisions"] == {"c1": owner_decision()}
    assert with_decision["verdict"] == "pass"
    # 裁決不改變歧異清單／擁有者抽查佇列本身——只標記它已被處理。
    assert with_decision["ownerAuditQueue"] == with_decision["disagreementCandidateIds"]


def test_owner_decision_rejects_candidate_not_in_disagreements():
    ops = [op("c1", "exclude"), op("c2", "exclude")]
    try:
        llm.machine_shadow_gate(
            batch_of("p", ops), batch_of("s", ops),
            owner_decisions={"c1": owner_decision()})
    except llm.LlmReviewError as exc:
        assert "c1" in str(exc)
        return
    raise AssertionError("對沒有歧異的紀錄記裁決必須拒絕")


def test_owner_decision_rejects_non_owner_decider_and_missing_fields():
    primary = [op("c1", "exclude")]
    secondary = [op("c1", "advance")]
    bad_records = (
        {**owner_decision(), "decidedBy": "executor-session"},
        {k: v for k, v in owner_decision().items() if k != "decidedAt"},
        {k: v for k, v in owner_decision().items() if k != "reasonShort"},
        {**owner_decision(), "decision": "include"},
    )
    for bad in bad_records:
        try:
            llm.machine_shadow_gate(
                batch_of("p", primary), batch_of("s", secondary),
                owner_decisions={"c1": bad})
        except llm.LlmReviewError:
            continue
        raise AssertionError(f"擁有者裁決紀錄必須拒絕：{bad}")


def test_owner_decision_does_not_lower_disagreement_rate_or_auto_resolve_others():
    """裁決只解對立否決，不影響歧異率統計，也不連帶處理其他歧異筆。"""
    primary = [op("c1", "exclude"), op("c2", "exclude"), op("c3", "exclude")]
    secondary = [op("c1", "advance"), op("c2", "unclear"), op("c3", "exclude")]
    report = llm.machine_shadow_gate(
        batch_of("p", primary), batch_of("s", secondary),
        owner_decisions={"c1": owner_decision()})
    assert report["disagreementRate"] == 2 / 3
    assert report["disagreementCandidateIds"] == ["c1", "c2"]
    # c1 對立已裁決，但 c2 仍是未裁決歧異——rate 依然統計兩筆。
    assert report["verdict"] == "fail"  # 歧異率超過預設 0.25 門檻


def test_owner_decisions_default_empty_preserves_prior_behaviour():
    """不傳 owner_decisions（或傳空字典）與舊行為完全相同，向下相容。"""
    ops_p = [op("c1", "advance"), op("c2", "exclude")]
    ops_s = [op("c1", "unclear"), op("c2", "exclude")]
    no_arg = llm.machine_shadow_gate(batch_of("p", ops_p), batch_of("s", ops_s))
    empty_arg = llm.machine_shadow_gate(batch_of("p", ops_p), batch_of("s", ops_s),
                                        owner_decisions={})
    assert no_arg == empty_arg
    assert "ownerDecisions" in no_arg and no_arg["ownerDecisions"] == {}
