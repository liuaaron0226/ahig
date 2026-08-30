"""整批跑萃取鏈。每一篇都要有下落。"""

import os
import tempfile
from pathlib import Path

from ahig.extraction import inventory_draft as bridge
from ahig.extraction import run_inventory
from ahig.search import fulltext

FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"
CONTRACT = {"status": "frozen",
            "scopeContractHash": "sha256:" + "a" * 64,
            "scopeContractId": "scope:test",
            "inScopeOutcomes": [{"outcomeId": "o1", "label": "fat-free mass"}]}


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
        assert len(run.succeeded) + len(run.failed) == 2
        run.check()

    _in_corpus(body)
