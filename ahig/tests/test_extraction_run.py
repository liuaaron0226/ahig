"""整批跑萃取鏈。每一篇都要有下落。"""

import os
import tempfile
from pathlib import Path

from ahig.extraction import inventory_draft as bridge
from ahig.extraction import run_inventory
from ahig.search import fulltext

FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"
# 契約要完整到 ``ScopeMatcher`` 真的收得下。第 533 輪查明：先前這裡是個殘缺的
# 樁，於是每一筆都在 scope 階段丟 KeyError——而下面那個「混合結果」的測試，
# 兩筆其實都失敗，卻因為只數了 succeeded + failed 而照樣通過。
CONTRACT = {
    "status": "frozen",
    "scopeContractHash": "sha256:" + "c" * 64,
    "scopeContractId": "scope:test",
    "inScopeOutcomes": [
        {"outcomeId": "ffm-change", "label": "去脂體重變化", "role": "critical",
         "quantityKind": "qk:ffm",
         "comparabilityClass": "body-composition-multi-compartment"}],
    "inScopeTimepoints": [
        {"timepointId": "end", "label": "介入結束", "windowStart": 4,
         "windowEnd": 104, "unit": "week"}],
    "researchQuestion": {
        "questionType": "efficacy",
        "population": {"label": "赤字期成人"},
        "interventionOrExposure": {"label": "較高蛋白質", "doseBands": [
            {"bandId": "high", "min": 1.6, "max": 2.39, "unit": "g/kg/day"}]},
        "comparator": {"types": ["dose-comparison"]}},
    "inScopeAnalysisSets": ["ITT"],
    "inScopeEffectMeasures": ["MD"],
    "extractionPolicy": {
        "subgroupPolicy": "prespecified-only",
        "sensitivityAnalysisPolicy": "exclude",
        "adjustedModelPolicy": "primary-model-only",
        "onOutOfScope": "record-in-outcome-inventory-only",
        "maxStudyResultsPerStudy": 16},
}


def _publish(root, candidate_id="ahig:candidate:publication:0011223344556677889900aa"):
    os.environ["AHIG_PRIVATE_ROOT"] = root
    return fulltext._publish_jats(
        {"candidateId": candidate_id, "identifiers": {"pmcid": "PMC7777777"}},
        raw=(FIXTURES / "sample-jats.xml").read_bytes(), exchange={},
        pmcid="PMC7777777", source_url="https://example.invalid/a.xml")


def _draft_for(request, **over):
    draft = {
        "inventoryId": "inv:run",
        "report": request.report,
        "manifestation": request.manifestation,
        "scopeContractHash": request.scope_contract_hash,
        "lifecycle": "draft",
        "reportedOutcomes": [
            {"localLabel": "fat-free mass",
             "sourceLocation": {"section": "Results"}}],
        "registryComparison": {"status": "pending"},
        "createdBy": {"agentClass": "model"},
        "completenessAttestation": {
            "sectionsScanned": [], "supplementaryScanned": False,
            "harmsScan": {"performed": True},
            "attestedBy": {"agentClass": "model"}},
    }
    draft.update(over)
    return draft


def _in_corpus(body):
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        try:
            manifest = _publish(tmp)
            body(manifest["candidateId"])
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_without_a_reader_the_run_fails_loudly_rather_than_reporting_nothing():
    # 安靜地跑出零篇，看起來像「這批沒有東西可報」。
    def body(candidate_id):
        run = run_inventory(CONTRACT, candidate_ids=[candidate_id])
        assert run.attempted == 1
        assert run.succeeded == []
        assert run.failures_by_stage()["call-reader"] == 1
        assert "ReadingSeamNotImplemented" in run.failed[0].error

    _in_corpus(body)


def test_a_reader_that_raises_leaves_the_record_listed_not_dropped():
    # 跳過之後產出的清冊看起來完全正常，只是小一點。
    def body(candidate_id):
        def boom(_request):
            raise RuntimeError("模型那端斷線")

        run = run_inventory(CONTRACT, reader=boom, candidate_ids=[candidate_id])
        assert run.attempted == 1
        assert [o.candidate_id for o in run.failed] == [candidate_id]
        assert "斷線" in run.failed[0].error

    _in_corpus(body)


def test_an_empty_inventory_is_a_failure_not_a_result():
    # 空清冊分不出「沒抽到」與「論文沒報告」，故不得當成跑完。
    def body(candidate_id):
        def empty(request):
            return _draft_for(request, reportedOutcomes=[])

        run = run_inventory(CONTRACT, reader=empty, candidate_ids=[candidate_id])
        assert run.succeeded == []
        assert run.failures_by_stage()["validate-draft"] == 1

    _in_corpus(body)


def test_every_record_lands_in_exactly_one_bucket():
    # check() 自己斷言這件事；這裡驗它在混合結果下仍成立。
    def body(candidate_id):
        calls = {"n": 0}

        def sometimes(request):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("第一次失敗")
            return _draft_for(request)

        run = run_inventory(CONTRACT, reader=sometimes,
                            candidate_ids=[candidate_id, candidate_id])
        assert run.attempted == 2
        # 先證明真的是混合的。只數 succeeded + failed == 2，在「兩筆都失敗」時
        # 一樣會過——那正是這個測試本來要排除的情況。
        assert len(run.succeeded) == 1
        assert len(run.failed) == 1
        run.check()

    _in_corpus(body)


def test_a_stored_inventory_is_reused_and_counted_apart_from_a_fresh_read():
    # 讀一篇要花錢。重跑不該重讀，而重用也不該被算成「這次讀到的」——
    # 否則一次什麼都沒讀的重跑，會和一次完整的跑長得一樣。
    from ahig.extraction import store

    def body(candidate_id):
        reads = {"n": 0}

        def counting(request):
            reads["n"] += 1
            return _draft_for(request)

        first = run_inventory(CONTRACT, reader=counting,
                              candidate_ids=[candidate_id], store=store)
        assert len(first.read_this_run) == 1
        assert first.reused == []
        assert reads["n"] == 1

        second = run_inventory(CONTRACT, reader=counting,
                               candidate_ids=[candidate_id], store=store)
        assert reads["n"] == 1, "同一份文件同一份契約不該再讀一次"
        assert len(second.reused) == 1
        assert second.read_this_run == []
        assert len(second.succeeded) == 1

    _in_corpus(body)


def test_a_different_contract_is_not_treated_as_already_done():
    # 判準變了，先前那份清冊回答的是別的問題。
    from ahig.extraction import store

    def body(candidate_id):
        reads = {"n": 0}

        def counting(request):
            reads["n"] += 1
            return _draft_for(request)

        first = run_inventory(CONTRACT, reader=counting,
                              candidate_ids=[candidate_id], store=store)
        other = dict(CONTRACT, scopeContractHash="sha256:" + "b" * 64)
        second = run_inventory(other, reader=counting,
                               candidate_ids=[candidate_id], store=store)

        assert reads["n"] == 2
        # 「讀了兩次」也可能是因為兩次都在存的時候壞掉。要兩次都真的走完，
        # 這個數字才代表「換了契約就重讀」。
        assert len(first.read_this_run) == 1
        assert len(second.read_this_run) == 1
        assert second.reused == []

    _in_corpus(body)


def test_the_store_refuses_to_overwrite_a_different_inventory():
    # 同一份文件對同一份契約產生兩份不同的清冊，是要有人看一眼的事，
    # 不是後寫的自動贏。
    from ahig.extraction import store

    def body(candidate_id):
        def reader(request):
            return _draft_for(request)

        run_inventory(CONTRACT, reader=reader, candidate_ids=[candidate_id],
                      store=store)
        # 直接改寫存下的那一份，再存回去
        from ahig.extraction.corpus import reading_request_for
        request = reading_request_for(candidate_id, CONTRACT)
        saved = store.load_if_current(candidate_id, request.manifestation,
                                      request.scope_contract_hash)
        assert saved is not None
        tampered = dict(saved, inventoryId="inv:other")
        try:
            store.save(tampered)
        except store.StoreError as error:
            assert "內容不同" in str(error)
        else:
            raise AssertionError("同鍵不同內容不該被靜靜覆寫")

    _in_corpus(body)
