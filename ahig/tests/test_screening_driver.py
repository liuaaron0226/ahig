"""W8 篩選驅動器的測試（ADR-0009 信任模型、ADR-0008 前置抽樣）。

核心不變量：

- 判讀器是可注入介面；本測試用假判讀器，不呼叫任何真 API。
- 驅動器不改 queue、不做資格判定；缺 judgedBy 的判讀一律拒收。
- 取批確定性：同 queue ＋ 同已判集合 → 同一批。
- 前置抽樣確定性：同 seed 可完整重放；比例限制在 ADR-0008 的 1–2%。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ahig.search import screening_driver as drv

MANIFEST = {"screeningQueueHash": "sha256:" + "q" * 64, "runId": "run-1"}
PROMPT = "screen: {title}\n{abstract}"


def entry(i, *, title=None):
    return {"candidateId": f"c{i:04d}", "title": title or f"title {i}",
            "priorityTier": "tier-2", "screeningLane": "standard-screening",
            "publicationYear": 2020}


def queue_of(n):
    return [entry(i) for i in range(1, n + 1)]


def fake_judge(opinion="exclude", *, calls=None, judged_by=None):
    """假判讀器：記錄收到什麼、回固定意見。"""
    def judge(payload):
        if calls is not None:
            calls.append(payload)
        return [{"candidateId": item["candidateId"],
                 "opinion": (opinion(item) if callable(opinion) else opinion),
                 "rawResponse": f"model says {item['candidateId']}",
                 "judgedBy": judged_by or {"agentClass": "llm",
                                           "modelId": "fake-1"}}
                for item in payload]
    return judge


def run(queue, batch, judge, **kw):
    return drv.run_batch(MANIFEST, queue, batch, judge, model_id="fake-1",
                         model_version="2026-08-01", prompt_template=PROMPT,
                         **kw)


# --- 取批 -------------------------------------------------------------

def test_take_batch_is_deterministic_and_respects_size():
    q = queue_of(250)
    first = drv.take_batch(q)
    assert len(first) == drv.DEFAULT_BATCH_SIZE == 100
    assert first == drv.take_batch(q)
    assert [e["candidateId"] for e in first] == [f"c{i:04d}"
                                                 for i in range(1, 101)]


def test_take_batch_skips_already_judged_without_reordering():
    q = queue_of(10)
    judged = {"c0001", "c0003", "c0004"}
    got = drv.take_batch(q, already_judged=judged, batch_size=4)
    assert [e["candidateId"] for e in got] == ["c0002", "c0005", "c0006",
                                               "c0007"]


def test_take_batch_follows_al_ranked_order_when_given():
    q = queue_of(4)
    ranked = ["c0003", "c0001", "c0004", "c0002"]
    got = drv.take_batch(q, ranked_order=ranked, batch_size=2)
    assert [e["candidateId"] for e in got] == ["c0003", "c0001"]


def test_take_batch_rejects_partial_or_alien_ranked_order():
    q = queue_of(3)
    for bad in (["c0001", "c0002"], ["c0001", "c0002", "c9999"]):
        try:
            drv.take_batch(q, ranked_order=bad)
        except drv.ScreeningDriverError:
            continue
        raise AssertionError(f"必須拒絕 ranked_order={bad}")


def test_take_batch_rejects_non_positive_size():
    try:
        drv.take_batch(queue_of(3), batch_size=0)
    except drv.ScreeningDriverError:
        return
    raise AssertionError("batch_size=0 必須拒絕")


# --- 判讀器介面與留痕 -------------------------------------------------

def test_judge_receives_only_title_layer_never_our_regex_priors():
    calls = []
    q = queue_of(2)
    run(q, q, fake_judge(calls=calls))
    assert len(calls) == 1
    for item in calls[0]:
        assert set(item) == {"candidateId", "title", "abstract",
                             "publicationYear"}
        # 餵 regex 推論結果會讓模型跟著我們的偏誤走，影子批次就失去意義。
        assert "priorityTier" not in item
        assert "screeningLane" not in item


def test_abstracts_are_passed_through_when_available():
    calls = []
    q = queue_of(1)
    run(q, q, fake_judge(calls=calls), abstracts={"c0001": "carb intake ..."})
    assert calls[0][0]["abstract"] == "carb intake ..."


def test_batch_preserves_full_traces_and_binds_queue_hash():
    q = queue_of(3)
    out = run(q, q, fake_judge("advance"))
    assert out["screeningQueueHash"] == MANIFEST["screeningQueueHash"]
    assert out["promptTemplate"] == PROMPT
    assert len(out["promptTemplateSha256"]) == 64
    assert out["model"] == {"id": "fake-1", "version": "2026-08-01"}
    assert out["opinionCount"] == 3
    for e in out["entries"]:
        assert e["rawResponse"].startswith("model says")
        assert e["respondedAt"]
    assert out["llmReviewHash"]


def test_batch_carries_judged_by_and_evidence_grade():
    """ADR-0009 原則 2：缺 judgedBy 的判讀不得進入任何下游計算。"""
    q = queue_of(2)
    out = run(q, q, fake_judge())
    assert out["judgedBy"]["agentClass"] == "llm"
    assert out["judgedBy"]["modelId"] == "fake-1"
    assert "no human expert review" in out["evidenceGrade"]


def test_batch_candidate_set_hash_is_content_addressed():
    q = queue_of(4)
    a = run(q, q[:2], fake_judge())
    b = run(q, list(reversed(q[:2])), fake_judge())
    c = run(q, q[2:], fake_judge())
    assert a["batchCandidateSetHash"] == b["batchCandidateSetHash"]
    assert a["batchCandidateSetHash"] != c["batchCandidateSetHash"]


# --- 判讀器回應的結構檢查（壞掉要當場炸） -----------------------------

def test_rejects_missing_judged_by():
    q = queue_of(1)

    def judge(payload):
        return [{"candidateId": "c0001", "opinion": "advance",
                 "rawResponse": "ok"}]
    try:
        run(q, q, judge)
    except drv.ScreeningDriverError as exc:
        assert "judgedBy" in str(exc)
        return
    raise AssertionError("缺 judgedBy 必須拒絕")


def test_rejects_bad_vocabulary_empty_response_and_wrong_type():
    q = queue_of(1)
    cases = [
        lambda p: [{"candidateId": "c0001", "opinion": "include",
                    "rawResponse": "x", "judgedBy": {"agentClass": "llm"}}],
        lambda p: [{"candidateId": "c0001", "opinion": "advance",
                    "rawResponse": "   ", "judgedBy": {"agentClass": "llm"}}],
        lambda p: {"candidateId": "c0001"},
        lambda p: ["not a dict"],
    ]
    for judge in cases:
        try:
            run(q, q, judge)
        except drv.ScreeningDriverError:
            continue
        raise AssertionError(f"必須拒絕：{judge}")


def test_rejects_incomplete_or_hallucinated_coverage():
    q = queue_of(3)
    # 少判一筆
    try:
        run(q, q, lambda p: fake_judge()(p[:2]))
    except drv.ScreeningDriverError as exc:
        assert "c0003" in str(exc)
    else:
        raise AssertionError("未覆蓋整批必須拒絕")
    # 判了不在批次裡的 id
    try:
        run(q, q[:1], lambda p: fake_judge()(
            p + [{"candidateId": "c9999", "title": "t", "abstract": None,
                  "publicationYear": 2020}]))
    except drv.ScreeningDriverError as exc:
        assert "c9999" in str(exc)
        return
    raise AssertionError("判讀不在批次內的 id 必須拒絕")


def test_rejects_duplicate_candidate_ids():
    q = queue_of(1)

    def judge(payload):
        one = fake_judge()(payload)
        return one + one
    try:
        run(q, q, judge)
    except drv.ScreeningDriverError as exc:
        assert "重複" in str(exc)
        return
    raise AssertionError("重複 candidateId 必須拒絕")


def test_rejects_empty_batch():
    try:
        run(queue_of(1), [], fake_judge())
    except drv.ScreeningDriverError:
        return
    raise AssertionError("空批次必須拒絕")


def test_driver_does_not_mutate_queue_or_entries():
    q = queue_of(3)
    snapshot = json.dumps(q, sort_keys=True)
    run(q, q, fake_judge("advance"))
    assert json.dumps(q, sort_keys=True) == snapshot


# --- ADR-0008 前置抽樣 ------------------------------------------------

def test_pilot_sample_is_deterministic_and_replayable():
    q = queue_of(1000)
    a = drv.pilot_sample(q, seed="w8-pilot")
    b = drv.pilot_sample(q, seed="w8-pilot")
    assert a["candidateIds"] == b["candidateIds"]
    assert a["sampleHash"] == b["sampleHash"]
    assert a["sampleSize"] == 10           # 1% of 1000
    assert a["poolSize"] == 1000
    assert a["adr"] == "ADR-0008"


def test_pilot_sample_changes_with_seed():
    q = queue_of(1000)
    a = drv.pilot_sample(q, seed="seed-a")
    b = drv.pilot_sample(q, seed="seed-b")
    assert a["candidateIds"] != b["candidateIds"]


def test_pilot_sample_is_spread_not_a_prefix():
    """雜湊排序抽樣不該退化成「取前 N 個」——那是系統性偏誤。"""
    q = queue_of(1000)
    sample = drv.pilot_sample(q, seed="w8-pilot")["candidateIds"]
    prefix = [f"c{i:04d}" for i in range(1, 11)]
    assert sample != prefix
    # 樣本應散佈在整個池子，不是擠在前 10%。
    assert max(int(cid[1:]) for cid in sample) > 100


def test_pilot_fraction_bounds_follow_adr_0008():
    q = queue_of(1000)
    assert drv.pilot_sample(q, seed="s", fraction=0.02)["sampleSize"] == 20
    for bad in (0.005, 0.05, 0.0, 1.0):
        try:
            drv.pilot_sample(q, seed="s", fraction=bad)
        except drv.ScreeningDriverError:
            continue
        raise AssertionError(f"比例 {bad} 超出 ADR-0008 的 1–2%，必須拒絕")


def test_pilot_sample_requires_seed_and_non_empty_pool():
    for kwargs, q in ((dict(seed=""), queue_of(10)),
                      (dict(seed="s"), [])):
        try:
            drv.pilot_sample(q, **kwargs)
        except drv.ScreeningDriverError:
            continue
        raise AssertionError("缺 seed 或空池子必須拒絕")


def test_pilot_sample_never_empty_for_tiny_pool():
    assert drv.pilot_sample(queue_of(3), seed="s")["sampleSize"] == 1


# --- 盛行率估計 -------------------------------------------------------

def test_prevalence_brackets_unclear_instead_of_forcing_a_side():
    q = queue_of(1000)
    sample = drv.pilot_sample(q, seed="w8-pilot")
    ids = sample["candidateIds"]
    judgements = {cid: "exclude" for cid in ids}
    judgements[ids[0]] = "advance"
    judgements[ids[1]] = "unclear"
    est = drv.estimate_prevalence(sample, judgements)
    assert est["sampleSize"] == 10
    assert est["advanceCount"] == 1 and est["unclearCount"] == 1
    assert est["prevalenceLowerBound"] == 0.1
    assert est["prevalenceUpperBound"] == 0.2
    assert est["projectedAdvanceLow"] == 100
    assert est["projectedAdvanceHigh"] == 200
    assert est["sampleHash"] == sample["sampleHash"]


def test_prevalence_rejects_incomplete_or_illegal_judgements():
    sample = drv.pilot_sample(queue_of(1000), seed="w8-pilot")
    ids = sample["candidateIds"]
    partial = {cid: "exclude" for cid in ids[:-1]}
    try:
        drv.estimate_prevalence(sample, partial)
    except drv.ScreeningDriverError as exc:
        assert ids[-1] in str(exc)
    else:
        raise AssertionError("前置樣本未判讀完整必須拒絕")
    illegal = {cid: "exclude" for cid in ids}
    illegal[ids[0]] = "maybe"
    try:
        drv.estimate_prevalence(sample, illegal)
    except drv.ScreeningDriverError:
        return
    raise AssertionError("非法判讀值必須拒絕")


# --- run root 讀寫（不得動 queue） ------------------------------------

def _write_run_root(tmp: Path, n=200):
    qdir = tmp / "screening-queue"
    qdir.mkdir(parents=True)
    (qdir / "queue.json").write_text(
        json.dumps(queue_of(n)), encoding="utf-8")
    (qdir / "manifest.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
    return tmp


def test_write_pilot_sample_writes_only_pilot_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = _write_run_root(Path(tmp))
        before = (root / "screening-queue" / "queue.json").read_bytes()
        sample = drv.write_pilot_sample(root, seed="w8-pilot")
        assert sample["screeningQueueHash"] == MANIFEST["screeningQueueHash"]
        assert sample["runId"] == "run-1"
        assert (root / "screening-pilot" / "sample.json").exists()
        # queue 是凍結契約，驅動器只讀不寫。
        assert (root / "screening-queue" / "queue.json").read_bytes() == before
        on_disk = json.loads((root / "screening-pilot" / "sample.json")
                             .read_text(encoding="utf-8"))
        assert on_disk["candidateIds"] == sample["candidateIds"]


def test_load_run_root_picks_up_al_ranked_order_when_present():
    with tempfile.TemporaryDirectory() as tmp:
        root = _write_run_root(Path(tmp), n=4)
        assert drv.load_run_root(root)["rankedOrder"] is None
        (root / "al-rank").mkdir()
        (root / "al-rank" / "ranked-order.json").write_text(
            json.dumps(["c0003", "c0001", "c0004", "c0002"]), encoding="utf-8")
        loaded = drv.load_run_root(root)
        batch = drv.take_batch(loaded["queue"],
                               ranked_order=loaded["rankedOrder"],
                               batch_size=1)
        assert batch[0]["candidateId"] == "c0003"
