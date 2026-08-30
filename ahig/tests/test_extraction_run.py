"""整批跑萃取鏈。每一篇都要有下落。"""

import json
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
AT = "2026-08-31T00:00:00Z"

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
        # 下游 schema 也在看這些欄位（第 539 輪起鏈上會驗）：attestedBy 要 at，
        # harmsScan 有三個必填欄位，agentClass 有列舉。
        # createdBy 不收 at（只有 attestedBy 要）——additionalProperties:false。
        "createdBy": {"agentClass": "model"},
        "completenessAttestation": {
            # sectionsScanned 兩處都是 minItems:1，且外層那個還要是這份文件
            # 真有的章節（validate_draft 在看）——故直接用請求帶來的標題。
            "sectionsScanned": list(request.section_titles),
            "supplementaryScanned": False,
            "harmsScan": {"performed": True,
                          "sectionsScanned": list(request.section_titles),
                          "harmOutcomesFound": 0,
                          "harmsReportingStatement": "not-mentioned"},
            "attestedBy": {"agentClass": "model", "at": AT}},
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


def test_the_batch_record_counts_the_buckets_not_just_the_attempts():
    # 跑完什麼都不留下，下一次「花了多少」就又是一句「不知道」——n+184 卡在
    # 那句話上。收據要逐篇一列，且數字要來自桶子而不是嘗試數。
    from ahig.extraction import store

    def body(candidate_id):
        calls = {"n": 0}

        def sometimes(request):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("模型那端斷線")
            return _draft_for(request)

        run = run_inventory(CONTRACT, reader=sometimes,
                            candidate_ids=[candidate_id, candidate_id],
                            store=store)
        written = json.loads(store.batch_path(run.to_batch_record()["batchId"])
                             .read_text(encoding="utf-8"))

        assert written["documentType"] == "outcome-inventory-batch"
        assert written["candidateCount"] == 2
        # 混合的一趟：只看總數分不出「一成一敗」與「兩篇都成」。
        assert written["readThisRunCount"] == 1
        assert written["failedCount"] == 1
        assert written["reusedCount"] == 0
        assert len(written["results"]) == 2
        assert written["scopeContractHash"] == CONTRACT["scopeContractHash"]

    _in_corpus(body)


def test_the_chars_recorded_are_the_chars_actually_sent():
    # 「送了多少字」是換算成錢的唯一起點。記錯了，後面整條算式都錯。
    from ahig.extraction import store
    from ahig.extraction.corpus import reading_request_for

    def body(candidate_id):
        def boom(_request):
            raise RuntimeError("模型那端斷線")

        run = run_inventory(CONTRACT, reader=boom, candidate_ids=[candidate_id],
                            store=store)
        record = run.to_batch_record()
        truth = len(json.dumps(
            reading_request_for(candidate_id, CONTRACT).prompt_payload(),
            ensure_ascii=False))

        assert truth > 0
        assert record["charsSent"] == truth
        # 模型沒回來，那一筆照樣要記 requestChars——那筆錢已經花了。
        [item] = record["results"]
        assert item["stage"] == "call-reader" and item["ok"] is False
        assert item["requestChars"] == truth
        assert item["draftChars"] == 0
        assert record["charsReturned"] == 0

    _in_corpus(body)


def test_each_successful_row_points_at_a_file_whose_bytes_match():
    # 收據上的指標若指不到東西，收據就只是一段自述。
    from ahig.contracts.freeze import file_hash
    from ahig.extraction import store
    from ahig.search.fulltext import private_root

    def body(candidate_id):
        run = run_inventory(CONTRACT, reader=_draft_for,
                            candidate_ids=[candidate_id], store=store)
        [item] = run.to_batch_record()["results"]

        path = private_root() / item["inventoryPath"]
        assert path.exists()
        assert file_hash(path.read_bytes()) == item["inventorySha256"]
        # 且那個檔真的是這一篇的清冊，不是碰巧存在的別的東西。
        assert json.loads(path.read_text(encoding="utf-8"))["report"] == candidate_id

    _in_corpus(body)


def test_a_reused_record_costs_nothing_on_the_receipt():
    # 「重跑不重付錢」若在收據上看不出來，那句話就沒有憑據。
    from ahig.extraction import store

    def body(candidate_id):
        run_inventory(CONTRACT, reader=_draft_for, candidate_ids=[candidate_id],
                      store=store)
        second = run_inventory(CONTRACT, reader=_draft_for,
                               candidate_ids=[candidate_id], store=store)
        record = second.to_batch_record()

        assert record["reusedCount"] == 1
        assert record["readThisRunCount"] == 0
        assert record["charsSent"] == 0
        assert record["charsReturned"] == 0
        # 重用那一列仍要指得到檔，否則「這一趟交出了什麼」就少了它。
        [item] = record["results"]
        assert item["stage"] == "reused"
        assert item["inventoryPath"]

    _in_corpus(body)


def test_an_unusable_contract_is_refused_before_a_single_paper_is_read():
    # 判範圍是最後一段，故造不出 ScopeMatcher 的契約，本來要等 41 篇都讀完
    # 才會顯現——41 筆全卡在 scope，錢花光而一份清冊都沒有。
    from ahig.extraction import ContractUnusable

    def body(candidate_id):
        calls = {"n": 0}

        def counting(request):
            calls["n"] += 1
            return _draft_for(request)

        # 上一輪本室的樁契約正是這一種：缺 inScopeTimepoints。
        broken = {k: v for k, v in CONTRACT.items() if k != "inScopeTimepoints"}
        try:
            run_inventory(broken, reader=counting, candidate_ids=[candidate_id])
        except ContractUnusable as error:
            assert "ScopeMatcher" in str(error)
        else:
            raise AssertionError("契約造不出 matcher，不該開跑")

        # 這才是重點：一篇都沒讀。逐筆失敗的紀錄看起來像「試過了」。
        assert calls["n"] == 0

    _in_corpus(body)


def test_a_usable_contract_still_gets_through_the_preflight():
    # 沒有這一條，上面那條在「什麼契約都拒絕」時一樣會通過。
    def body(candidate_id):
        calls = {"n": 0}

        def counting(request):
            calls["n"] += 1
            return _draft_for(request)

        run = run_inventory(CONTRACT, reader=counting, candidate_ids=[candidate_id])
        assert calls["n"] == 1
        assert len(run.succeeded) == 1

    _in_corpus(body)


def test_the_real_frozen_contract_passes_the_preflight():
    # 樁契約過得了不代表真的那份過得了。這一條若哪天紅了，代表凍結出去的契約
    # 萃取階段用不了——而那要在花錢之前知道。
    import json as _json
    from pathlib import Path as _Path

    path = (_Path(__file__).resolve().parents[1] / "calibration"
            / "b11-carbohydrate" / "scope-contract.json")
    contract = _json.loads(path.read_text(encoding="utf-8"))
    assert contract["status"] == "frozen"

    # 候選給空的：這一條只驗契約那一關，不碰語料。
    run = run_inventory(contract, candidate_ids=[])
    assert run.attempted == 0
    assert run.contract_hash == contract["scopeContractHash"]


def test_a_draft_the_seam_accepts_but_the_downstream_schema_rejects_is_a_failure():
    # validate_draft 是本鏈的驗收，schema 是下游的，兩者不等價。先前鏈上沒有
    # 任何一段在看 schema——不合下游規格的清冊會被照樣判範圍、照樣存檔，
    # 等到下游才退，而那時候看起來會像模型回了壞東西。
    def body(candidate_id):
        def slightly_off(request):
            draft = _draft_for(request)
            # validate_draft 不看這一欄；schema 要 integer。
            draft["completenessAttestation"]["harmsScan"]["harmOutcomesFound"] = "0"
            return draft

        run = run_inventory(CONTRACT, reader=slightly_off,
                            candidate_ids=[candidate_id])
        assert run.succeeded == []
        assert run.failures_by_stage()["validate-draft"] == 1
        assert "schema" in run.failed[0].error

    _in_corpus(body)


def test_the_schema_check_says_nothing_about_a_document_that_conforms():
    # 沒有這一條，上面那條在「什麼都退」時一樣會通過。
    from ahig.extraction.run import _schema_errors

    def body(candidate_id):
        from ahig.extraction.corpus import reading_request_for
        request = reading_request_for(candidate_id, CONTRACT)
        assert _schema_errors(_draft_for(request)) == ""
        # 而多一個 schema 沒宣告的欄位就該有話說（additionalProperties: false）。
        assert _schema_errors(dict(_draft_for(request), anUnexpectedField=1))

    _in_corpus(body)


def test_a_source_location_naming_no_real_section_is_counted_not_blocked():
    # sectionsScanned 被核對，而每個數字自己的出處沒有——兩者是同一種宣稱，
    # 而後者才是把數字追回去的那條線。這裡數它，不擋它：schema 明講粗座標
    # 即可，且 20 個節的標題是字面 Untitled，擋下去等於讓它們無法被引用。
    def body(candidate_id):
        def elsewhere(request):
            draft = _draft_for(request)
            draft["reportedOutcomes"][0]["sourceLocation"] = {
                "section": "A Section No Paper Has"}
            return draft

        run = run_inventory(CONTRACT, reader=elsewhere,
                            candidate_ids=[candidate_id])
        assert len(run.succeeded) == 1, "指不到的出處不該讓這一篇失敗"
        record = run.to_batch_record()
        assert record["unknownSections"] == 1
        assert record["results"][0]["unknownSections"] == 1

    _in_corpus(body)


def test_a_source_location_naming_a_real_section_counts_zero():
    # 沒有這一條，上面那條在「什麼出處都算指不到」時一樣會通過。
    def body(candidate_id):
        from ahig.extraction.corpus import reading_request_for
        real = reading_request_for(candidate_id, CONTRACT).section_titles[0]

        def cited(request):
            draft = _draft_for(request)
            draft["reportedOutcomes"][0]["sourceLocation"] = {
                # 大小寫與前後空白不計，與 sections_titled 同一規則。
                "section": "  " + real.upper() + "  "}
            return draft

        run = run_inventory(CONTRACT, reader=cited, candidate_ids=[candidate_id])
        assert run.to_batch_record()["unknownSections"] == 0

    _in_corpus(body)
