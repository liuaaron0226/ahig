"""**真正跑的時候長什麼樣：工作單 ＋ 存放處 ＋ 逐頁，三者一起。**

各段都有自己的測試，⚠️ 而這一檔測的是**它們合起來的那個模式**——
🚨 那是先前唯一沒被走過的一條：所有演練都 `store=None`（因為替身的清冊是編造的，
不能落進真的私有根），而**真正跑的時候一定會帶 store**，否則重跑要重付錢。

逐頁併回去之後再跑，前幾頁那些應該被記成 ``reused`` 而不是重讀——
**🚨 那正是「重跑不重付錢」這句話在實際流程裡兌現的地方，而它從沒被驗過。**
"""

import json
import os
import tempfile
from pathlib import Path

from ahig.extraction import run_inventory, store, worksheet
from ahig.extraction.corpus import reading_request_for
from ahig.search import fulltext

FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"
AT = "2026-08-31T00:00:00Z"

CONTRACT = {
    "status": "frozen",
    "scopeContractHash": "sha256:" + "d" * 64,
    "scopeContractId": "scope:route",
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
        "maxStudyResultsPerStudy": 12},
}


def _publish(root, n):
    """發佈 n 篇。⚠️ 內容相同故 manifestation 相同，🚨 而 candidateId 不同——
    存放處的鍵含 report，故路徑仍各自分開。"""
    os.environ["AHIG_PRIVATE_ROOT"] = root
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    ids = []
    for i in range(n):
        candidate_id = "ahig:candidate:publication:%024x" % (0xA0 + i)
        fulltext._publish_jats(
            {"candidateId": candidate_id,
             "identifiers": {"pmcid": "PMC900000%d" % i}},
            raw=raw, exchange={}, pmcid="PMC900000%d" % i,
            source_url="https://example.invalid/%d.xml" % i)
        ids.append(candidate_id)
    return ids


def _draft_for(request):
    return {
        "inventoryId": "inv:route",
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
            "sectionsScanned": list(request.section_titles),
            "supplementaryScanned": False,
            "harmsScan": {"performed": True,
                          "sectionsScanned": list(request.section_titles),
                          "harmOutcomesFound": 0,
                          "harmsReportingStatement": "not-mentioned"},
            "attestedBy": {"agentClass": "model", "at": AT}},
    }


def _in_corpus(body, n=4):
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        try:
            body(Path(tmp), _publish(tmp, n))
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_pages_read_in_earlier_rounds_are_reused_not_read_again():
    # 「重跑不重付錢」在實際流程裡兌現的地方：逐頁併回去之後再跑，
    # 前幾頁那些要被記成 reused。
    def body(root, ids):
        requests = [reading_request_for(cid, CONTRACT) for cid in ids]
        out = root / "sheet"
        # 一頁兩篇：把 4 篇切成 2 頁。
        one = len(json.dumps(requests[0].prompt_payload(), ensure_ascii=False))
        sheet = worksheet.write_worksheet(out, requests, source="route",
                                          page_chars=one * 2)
        assert sheet["pageCount"] == 2

        by_report = {r.report: r for r in requests}
        reads = {"n": 0}
        drafted, runs, calls = [], [], []
        for number in (1, 2):
            page = worksheet.page(out, number)
            worksheet.append_drafts(
                out, [_draft_for(by_report[it["report"]])
                      for it in page["items"]],
                read_by={"agentClass": "model"})
            drafted.extend(it["report"] for it in page["items"])
            loaded = worksheet.load_drafts(out, require_complete=False)
            inner = worksheet.reader_from(loaded["drafts"])

            def counting(request, inner=inner):
                # 真的數 reader 被叫了幾次——🚨 光看桶子標籤，是在信 run 自己的
                # 分類；被重用的那幾篇「沒有被讀」要由呼叫次數說了算。
                reads["n"] += 1
                return inner(request)

            runs.append(run_inventory(CONTRACT, reader=counting,
                                      candidate_ids=drafted, store=store))
            calls.append(reads["n"])

        first, second = runs
        assert len(first.read_this_run) == 2
        assert first.reused == []
        # 第二輪：前一頁那兩篇不得再讀一次。
        assert len(second.reused) == 2
        assert len(second.read_this_run) == 2
        assert len(second.succeeded) == 4
        # 累計呼叫 2 → 4，🚫 不是 2 → 6。
        assert calls == [2, 4]

    _in_corpus(body)


def test_the_receipt_charges_only_for_what_this_round_read():
    # 收據若把重用的也算進送出字元，帳會隨重跑次數線性膨脹。
    def body(root, ids):
        requests = [reading_request_for(cid, CONTRACT) for cid in ids]
        out = root / "sheet"
        one = len(json.dumps(requests[0].prompt_payload(), ensure_ascii=False))
        worksheet.write_worksheet(out, requests, source="route",
                                  page_chars=one * 2)
        by_report = {r.report: r for r in requests}

        drafted, records = [], []
        for number in (1, 2):
            page = worksheet.page(out, number)
            worksheet.append_drafts(
                out, [_draft_for(by_report[it["report"]])
                      for it in page["items"]],
                read_by={"agentClass": "model"})
            drafted.extend(it["report"] for it in page["items"])
            loaded = worksheet.load_drafts(out, require_complete=False)
            run = run_inventory(
                CONTRACT, reader=worksheet.reader_from(loaded["drafts"]),
                candidate_ids=drafted, store=store)
            records.append(run.to_batch_record())

        first, second = records
        assert first["readThisRunCount"] == 2 and first["reusedCount"] == 0
        assert second["readThisRunCount"] == 2 and second["reusedCount"] == 2
        # 兩輪各只送出兩篇的量——🚫 第二輪不得因為總數是 4 就收 4 篇的錢。
        assert second["charsSent"] == first["charsSent"]

    _in_corpus(body)


def test_every_saved_inventory_is_reachable_from_its_receipt():
    # 收據上的指標指不到東西，收據就只是一段自述。
    from ahig.contracts.freeze import file_hash

    def body(root, ids):
        requests = [reading_request_for(cid, CONTRACT) for cid in ids]
        out = root / "sheet"
        worksheet.write_worksheet(out, requests, source="route")
        worksheet.append_drafts(out, [_draft_for(r) for r in requests],
                                read_by={"agentClass": "model"})
        loaded = worksheet.load_drafts(out)
        run = run_inventory(CONTRACT,
                            reader=worksheet.reader_from(loaded["drafts"]),
                            candidate_ids=ids, store=store)
        record = run.to_batch_record()

        assert len(record["results"]) == len(ids)
        seen = set()
        for item in record["results"]:
            path = fulltext.private_root() / item["inventoryPath"]
            assert path.exists()
            assert file_hash(path.read_bytes()) == item["inventorySha256"]
            seen.add(item["inventoryPath"])
        # 四篇內容相同，但每一篇要有自己的檔——否則就是彼此覆蓋了。
        assert len(seen) == len(ids)

    _in_corpus(body)


def test_a_second_pass_over_a_finished_batch_reads_nothing_at_all():
    # 一次什麼都沒讀的重跑，不該和一次完整的跑長得一樣。
    def body(root, ids):
        requests = [reading_request_for(cid, CONTRACT) for cid in ids]
        out = root / "sheet"
        worksheet.write_worksheet(out, requests, source="route")
        worksheet.append_drafts(out, [_draft_for(r) for r in requests],
                                read_by={"agentClass": "model"})
        loaded = worksheet.load_drafts(out)

        reads = {"n": 0}

        def counting(request):
            reads["n"] += 1
            return loaded["drafts"][request.report]

        run_inventory(CONTRACT, reader=counting, candidate_ids=ids, store=store)
        assert reads["n"] == len(ids)

        again = run_inventory(CONTRACT, reader=counting, candidate_ids=ids,
                              store=store)
        assert reads["n"] == len(ids), "第二趟不該再讀任何一篇"
        assert len(again.reused) == len(ids)
        assert again.read_this_run == []
        record = again.to_batch_record()
        assert record["charsSent"] == 0
        assert record["readThisRunCount"] == 0

    _in_corpus(body)
