"""萃取工作單：論文出去、清冊回來。ADR-0009 裁定①那條路的萃取版。"""

import json
import os
import tempfile
from pathlib import Path

from ahig.extraction import worksheet
from ahig.extraction.corpus import reading_request_for
from ahig.search import fulltext

FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"

# 這一檔不判範圍，故契約只要湊得出「已凍結、有結局可對照」即可——
# `reading_request_for` 看的就是這兩樣。要 ScopeMatcher 收得下的那份完整契約
# 在 test_extraction_run.py，那裡才真的走到判定。
AT = "2026-08-31T00:00:00Z"

CONTRACT = {"status": "frozen",
            "scopeContractHash": "sha256:" + "c" * 64,
            "inScopeOutcomes": [{"outcomeId": "o1", "label": "fat-free mass"}]}


def _publish(root, candidate_id="ahig:candidate:publication:0011223344556677889900aa"):
    os.environ["AHIG_PRIVATE_ROOT"] = root
    return fulltext._publish_jats(
        {"candidateId": candidate_id, "identifiers": {"pmcid": "PMC7777777"}},
        raw=(FIXTURES / "sample-jats.xml").read_bytes(), exchange={},
        pmcid="PMC7777777", source_url="https://example.invalid/a.xml")


def _draft_for(request, **over):
    draft = {
        "inventoryId": "inv:sheet",
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
            body(Path(tmp), manifest["candidateId"])
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_pages_are_cut_by_characters_not_by_count():
    # 本語料單篇 13k–356k 字元，差 27 倍：固定篇數的一頁大小不可預測。
    assert worksheet.paginate([40, 40, 40], page_chars=100) == [1, 1, 2]
    # 邊界：剛好裝滿不換頁。
    assert worksheet.paginate([50, 50, 1], page_chars=100) == [1, 1, 2]


def test_an_item_larger_than_the_budget_gets_its_own_page_instead_of_being_split():
    # 切不切、怎麼切會改變讀的人看到什麼——那是契約層的決定，不是分頁的。
    assert worksheet.paginate([10, 500, 10], page_chars=100) == [1, 2, 3]


def test_the_worksheet_carries_the_binding_and_the_pages_carry_the_text():
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        sheet = worksheet.write_worksheet(out, [request], source="test")

        index = json.loads((out / "worksheet.json").read_text(encoding="utf-8"))
        [item] = index["items"]
        assert item["report"] == candidate_id
        assert item["manifestation"] == request.manifestation
        assert item["scopeContractHash"] == CONTRACT["scopeContractHash"]
        # 索引不帶全文——不然逐頁一檔就沒有意義了。
        assert "payload" not in item

        page = json.loads((out / "pages" / "page-001.json")
                          .read_text(encoding="utf-8"))
        assert page["items"][0]["payload"]["content"]
        assert sheet["totalChars"] == item["payloadChars"]

    _in_corpus(body)


def test_the_worksheet_stays_inside_the_private_root():
    # 工作單帶著全文。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        with tempfile.TemporaryDirectory() as outside:
            try:
                worksheet.write_worksheet(Path(outside) / "sheet", [request],
                                          source="test")
            except worksheet.WorksheetError as error:
                assert "AHIG_PRIVATE_ROOT" in str(error)
            else:
                raise AssertionError("全文不得寫到私有根之外")

    _in_corpus(body)


def test_a_draft_bound_to_another_document_is_refused_on_the_way_back():
    # 綁錯了的清冊看起來完全正常，只是它讀的不是這一份。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")

        draft = _draft_for(request)
        draft["manifestation"] = "sha256:" + "f" * 64
        (out / "drafts.json").write_text(json.dumps({
            "documentType": "extraction-drafts", "source": "test",
            "readBy": {"agentClass": "model"}, "entries": [draft]},
            ensure_ascii=False), encoding="utf-8")

        try:
            worksheet.load_drafts(out)
        except worksheet.WorksheetError as error:
            assert "manifestation" in str(error)
        else:
            raise AssertionError("綁到別份文件的清冊不該收")

    _in_corpus(body)


def test_a_complete_set_of_drafts_is_accepted_and_becomes_a_reader():
    # 沒有這一條，上面那條在「什麼清冊都拒絕」時一樣會通過。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        (out / "drafts.json").write_text(json.dumps({
            "documentType": "extraction-drafts", "source": "test",
            "readBy": {"agentClass": "model"},
            "entries": [_draft_for(request)]}, ensure_ascii=False),
            encoding="utf-8")

        loaded = worksheet.load_drafts(out)
        assert loaded["draftedCount"] == 1
        assert loaded["remaining"] == []

        read = worksheet.reader_from(loaded["drafts"])
        assert read(request)["report"] == candidate_id

    _in_corpus(body)


def test_a_half_filled_set_is_refused_unless_asked_for_progress():
    # 有洞的一批會讓下游的分母悄悄變小。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")

        try:
            worksheet.load_drafts(out)
        except worksheet.WorksheetError as error:
            assert "沒有清冊" in str(error)
        else:
            raise AssertionError("工作單沒讀完不該當成讀完")

        progress = worksheet.load_drafts(out, require_complete=False)
        assert progress["draftedCount"] == 0
        assert progress["remaining"] == [candidate_id]

    _in_corpus(body)


def test_drafts_without_a_named_reader_are_refused():
    # 誰讀的沒記下來，清冊就不可稽核。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        (out / "drafts.json").write_text(json.dumps({
            "documentType": "extraction-drafts", "source": "test",
            "readBy": None, "entries": [_draft_for(request)]},
            ensure_ascii=False), encoding="utf-8")

        try:
            worksheet.load_drafts(out)
        except worksheet.WorksheetError as error:
            assert "agentClass" in str(error)
        else:
            raise AssertionError("沒有 readBy 的清冊不該收")

    _in_corpus(body)


SECOND_ID = "ahig:candidate:publication:00112233445566778899aabb"


def _two_page_sheet(root, candidate_id):
    """兩篇各自成頁的工作單——並行讀的最小情形。"""
    second = _publish(str(root), candidate_id=SECOND_ID)["candidateId"]
    requests = [reading_request_for(candidate_id, CONTRACT),
                reading_request_for(second, CONTRACT)]
    out = root / "extraction-worksheet"
    worksheet.write_worksheet(out, requests, source="test", page_chars=1)
    return out, requests


def test_two_windows_reading_different_pages_do_not_overwrite_each_other():
    """🚨 `append_drafts` 是整份讀回、整份寫回。

    ⚠️ 兩個視窗同時跑，**後寫的會把先寫的整個蓋掉且不出任何錯**——蓋掉之後
    的檔案結構完全正常，只是少了一頁。故並行要走逐頁一檔。
    """
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        for page, request in enumerate(requests, start=1):
            worksheet.write_page_drafts(
                out, page, [_draft_for(request)],
                read_by={"agentClass": "model", "window": page})

        got = worksheet.load_drafts(out)
        assert got["draftedCount"] == 2 and got["remaining"] == []
        # 誰讀的是逐頁記的——18 頁 18 個視窗時，硬塞成一個會記錯 17 個。
        assert sorted(got["readByPages"]) == ["1", "2"]
        assert got["readByPages"]["2"]["window"] == 2

    _in_corpus(body)


def test_writing_a_page_touches_no_shared_file():
    """✅ 並行安全靠的就是這一條：**兩個視窗寫的是不同檔案。**

    🚨 若逐頁那一支仍動到 `drafts.json`，前面那條「兩頁都在」的測試照樣會綠
    ——⚠️ 因為它是循序跑的。**這一條才是真的在測並行的那個性質。**
    """
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        before = (out / "drafts.json").read_bytes()
        for page, request in enumerate(requests, start=1):
            worksheet.write_page_drafts(out, page, [_draft_for(request)],
                                        read_by={"agentClass": "model"})
        assert (out / "drafts.json").read_bytes() == before
        assert sorted(p.name for p in (out / "drafts").glob("*.json")) == [
            "page-001.json", "page-002.json"]

    _in_corpus(body)


def test_the_same_page_read_twice_with_different_results_is_refused():
    """⚠️ 同一頁被兩個視窗都讀到，🚫 不是後寫的自動贏。"""
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        read_by = {"agentClass": "model"}
        worksheet.write_page_drafts(out, 1, [_draft_for(requests[0])],
                                    read_by=read_by)
        # 一模一樣的重寫是無害的，不該擋。
        again = worksheet.write_page_drafts(out, 1, [_draft_for(requests[0])],
                                            read_by=read_by)
        assert again["written"] == 0

        other = _draft_for(requests[0], inventoryId="inv:different")
        try:
            worksheet.write_page_drafts(out, 1, [other], read_by=read_by)
        except worksheet.WorksheetError as error:
            assert "不覆寫" in str(error)
        else:
            raise AssertionError("同一頁兩種結果不該悄悄覆寫")

    _in_corpus(body)


def test_a_draft_written_into_the_wrong_page_is_refused():
    """🚨 寫進別頁，會讓兩個視窗各自登錄同一篇而彼此看不見。"""
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        try:
            worksheet.write_page_drafts(out, 2, [_draft_for(requests[0])],
                                        read_by={"agentClass": "model"})
        except worksheet.WorksheetError as error:
            assert "不在第 2 頁" in str(error)
        else:
            raise AssertionError("寫錯頁不該收")

    _in_corpus(body)


def test_the_same_paper_in_both_the_shared_file_and_a_page_file_is_caught():
    """⚠️ 舊的共用檔與新的逐頁檔並存時，同一篇可能被登錄兩次。"""
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        worksheet.append_drafts(out, [_draft_for(requests[0])],
                                read_by={"agentClass": "model"})
        worksheet.write_page_drafts(out, 1, [_draft_for(requests[0])],
                                    read_by={"agentClass": "model"})
        try:
            worksheet.load_drafts(out, require_complete=False)
        except worksheet.WorksheetError as error:
            assert "重複 report" in str(error)
        else:
            raise AssertionError("同一篇登錄兩次不該通過")

    _in_corpus(body)


def test_a_second_reader_never_reaches_the_record():
    """🚨 這是第二位讀者最要緊的一條。

    ⚠️ 第二位讀者存在的理由是**比對**，🚫 不是補產量。
    若它寫的東西會被 `load_drafts` 收進去，那它就從「對照組」變成「產量」，
    **🚨 而一批半數由 A 讀、半數由 B 讀的清冊，看起來和一批乾淨的一模一樣。**
    """
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        worksheet.write_page_drafts(out, 1, [_draft_for(requests[0])],
                                    read_by={"agentClass": "model"})
        # 第二位讀者讀的是**同一頁**——在正式那一道這會被擋，在別道則否。
        worksheet.write_page_drafts(
            out, 1, [_draft_for(requests[0], inventoryId="inv:second")],
            read_by={"agentClass": "model", "name": "second"}, lane="second")

        got = worksheet.load_drafts(out, require_complete=False)
        assert got["draftedCount"] == 1
        assert got["drafts"][requests[0].report]["inventoryId"] != "inv:second"
        assert worksheet.load_lane(out, "second")["drafts"][
            requests[0].report]["inventoryId"] == "inv:second"

    _in_corpus(body)


def test_agreement_counts_labels_and_says_what_it_does_not_measure():
    """✅ 兩邊都有的、只有一邊有的，逐篇列出。

    ⚠️ 同一個結局被叫成不同名字時會算成兩邊各有一個——🚨 那正是為什麼
    「只有一邊有」是待人看的清單，🚫 不是錯誤數。
    """
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        request = requests[0]
        primary = _draft_for(request)
        primary["reportedOutcomes"] = [
            {"localLabel": "fat-free mass",
             "sourceLocation": {"section": "Results"}},
            {"localLabel": "VO2max", "sourceLocation": {"section": "Results"}}]
        second = _draft_for(request, inventoryId="inv:second")
        second["reportedOutcomes"] = [
            {"localLabel": "  Fat-Free   Mass ",   # 只差大小寫與空白 → 算同一個
             "sourceLocation": {"section": "Results"}},
            {"localLabel": "lean body mass",       # 同一件事、不同叫法 → 算兩邊各一
             "sourceLocation": {"section": "Results"}}]
        worksheet.write_page_drafts(out, 1, [primary],
                                    read_by={"agentClass": "model"})
        worksheet.write_page_drafts(out, 1, [second], lane="second",
                                    read_by={"agentClass": "model"})

        got = worksheet.agreement(
            worksheet.load_drafts(out, require_complete=False)["drafts"],
            worksheet.load_lane(out, "second")["drafts"])
        assert got["comparedReports"] == 1
        assert got["labelsBoth"] == 1
        assert got["labelsOnlyPrimary"] == 1 and got["labelsOnlySecond"] == 1
        assert got["rows"][0]["onlyPrimary"] == ["VO2max"]
        assert got["rows"][0]["onlySecond"] == ["lean body mass"]
        assert "不是錯誤數" in got["caveat"]

    _in_corpus(body)


def test_agreement_only_compares_papers_both_readers_read():
    """⚠️ 第二位讀者多半只讀一部分——🚫 沒讀的不得算成不同意。"""
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        for page, request in enumerate(requests, start=1):
            worksheet.write_page_drafts(out, page, [_draft_for(request)],
                                        read_by={"agentClass": "model"})
        worksheet.write_page_drafts(out, 1, [_draft_for(requests[0])],
                                    lane="second",
                                    read_by={"agentClass": "model"})

        got = worksheet.agreement(
            worksheet.load_drafts(out)["drafts"],
            worksheet.load_lane(out, "second")["drafts"])
        assert got["comparedReports"] == 1
        assert got["primaryOnlyReports"] == [requests[1].report]
        assert got["secondOnlyReports"] == []

    _in_corpus(body)


def test_a_reader_who_could_not_have_read_it_is_refused():
    """記下誰讀的還不夠——**有些記載在這個專案裡不可能為真**。

    `human-self` 讀完 41 篇英文全文是假的（ADR-0009：本專案唯一的人讀不了
    英文文獻），`deterministic` 更直接：確定性程式碼讀不出論文報告了什麼，
    那正是這個接縫存在的理由。⚠️ 而錯的來源記載看起來和對的一模一樣。
    """
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        for agent_class in ("human-self", "deterministic"):
            (out / "drafts.json").write_text(json.dumps({
                "documentType": "extraction-drafts", "source": "test",
                "readBy": {"agentClass": agent_class},
                "entries": [_draft_for(request)]},
                ensure_ascii=False), encoding="utf-8")
            try:
                worksheet.load_drafts(out)
            except worksheet.WorksheetError as error:
                assert agent_class in str(error)
            else:
                raise AssertionError(f"{agent_class} 讀的清冊不該收")

        # 正向對照：讀得了的那些照樣收，🚫 本檢查不是把 readBy 一律擋掉。
        for agent_class in ("model", "human-expert"):
            (out / "drafts.json").write_text(json.dumps({
                "documentType": "extraction-drafts", "source": "test",
                "readBy": {"agentClass": agent_class},
                "entries": [_draft_for(request)]},
                ensure_ascii=False), encoding="utf-8")
            assert worksheet.load_drafts(out)["readBy"]["agentClass"] == agent_class

    _in_corpus(body)


def test_appending_a_page_refuses_a_reader_who_could_not_have_read_it():
    """併入那一支也走同一道——🚫 兩處各寫一份判斷，遲早會分岔。"""
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        try:
            worksheet.append_drafts(out, [_draft_for(request)],
                                    read_by={"agentClass": "human-self"})
        except worksheet.WorksheetError as error:
            assert "human-self" in str(error)
        else:
            raise AssertionError("human-self 讀的清冊不該併入")

    _in_corpus(body)


def test_the_reader_refuses_a_document_that_changed_after_the_draft_was_written():
    # load_drafts 驗的是「清冊 vs 工作單」；這裡驗的是「清冊 vs 這一次的請求」。
    # 兩者之間文件可能又被重新解析過。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        read = worksheet.reader_from({candidate_id: _draft_for(request)})

        class Moved:
            report = candidate_id
            manifestation = "sha256:" + "e" * 64
            scope_contract_hash = CONTRACT["scopeContractHash"]

        try:
            read(Moved())
        except worksheet.WorksheetError as error:
            assert "又變過" in str(error)
        else:
            raise AssertionError("文件變過就不該沿用舊清冊")

    _in_corpus(body)


def test_a_missing_draft_raises_instead_of_returning_an_empty_inventory():
    # 空清冊分不出「沒讀到」與「論文沒報告」。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        read = worksheet.reader_from({})
        try:
            read(request)
        except worksheet.WorksheetError as error:
            assert "沒有這一篇" in str(error)
        else:
            raise AssertionError("找不到清冊不該回空的")

    _in_corpus(body)


def test_pages_are_merged_back_one_at_a_time():
    # 18 頁分 18 輪讀完，所以併檔會發生很多次。整份重寫等於每次都要有全部。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")

        result = worksheet.append_drafts(
            out, [_draft_for(request)], read_by={"agentClass": "model"})
        assert result["added"] == 1
        assert result["draftedCount"] == 1
        assert result["remaining"] == []
        assert worksheet.load_drafts(out)["draftedCount"] == 1

    _in_corpus(body)


def test_merging_the_same_paper_twice_is_refused():
    # 同一篇讀了兩次而兩份不同，是要有人看一眼的事，不是後寫的自動贏。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        worksheet.append_drafts(out, [_draft_for(request)],
                                read_by={"agentClass": "model"})
        try:
            worksheet.append_drafts(out, [_draft_for(request)])
        except worksheet.WorksheetError as error:
            assert "重複" in str(error)
        else:
            raise AssertionError("同一篇不該被併入兩次")

    _in_corpus(body)


def test_a_bad_entry_leaves_the_file_as_it_was():
    # 半套寫入會讓清冊檔停在 load_drafts 讀不回來的狀態，
    # 而那時候前面幾頁讀的東西也一起卡住。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        before = (out / "drafts.json").read_text(encoding="utf-8")

        bad = _draft_for(request)
        bad["manifestation"] = "sha256:" + "f" * 64
        try:
            worksheet.append_drafts(out, [bad], read_by={"agentClass": "model"})
        except worksheet.WorksheetError:
            pass
        else:
            raise AssertionError("綁錯的清冊不該被併入")

        assert (out / "drafts.json").read_text(encoding="utf-8") == before

    _in_corpus(body)


def test_merging_without_naming_the_reader_is_refused():
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        try:
            worksheet.append_drafts(out, [_draft_for(request)])
        except worksheet.WorksheetError as error:
            assert "agentClass" in str(error)
        else:
            raise AssertionError("沒有 readBy 不該併入")

    _in_corpus(body)


def test_a_page_is_fetched_on_its_own():
    # 逐頁一檔的用意：讀第 3 頁的人不必先把 1、2 頁一起載進來。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")

        page = worksheet.page(out, 1)
        assert page["page"] == 1
        assert page["items"][0]["report"] == candidate_id
        try:
            worksheet.page(out, 99)
        except worksheet.WorksheetError as error:
            assert "沒有第 99 頁" in str(error)
        else:
            raise AssertionError("不存在的頁不該回東西")

    _in_corpus(body)


# ── 守衛：第 552 輪查出這兩道 raise 從未被執行過 ──────────────────────────

def test_an_empty_worksheet_is_refused():
    # 空工作單與「這批沒有論文」在檔案裡分不出來。
    try:
        worksheet.build_worksheet([], source="test")
    except worksheet.WorksheetError as error:
        assert "空工作單" in str(error)
    else:
        raise AssertionError("沒有要讀的東西就不該產出工作單")


def test_a_draft_for_a_paper_not_on_the_worksheet_is_refused():
    # 收回一份工作單上沒有的清冊，代表兩邊對的不是同一批。
    def body(root, candidate_id):
        request = reading_request_for(candidate_id, CONTRACT)
        out = root / "extraction-worksheet"
        worksheet.write_worksheet(out, [request], source="test")
        stray = dict(_draft_for(request), report="ahig:candidate:publication:" + "f" * 24)
        try:
            worksheet.append_drafts(out, [stray],
                                    read_by={"agentClass": "model"})
        except worksheet.WorksheetError as error:
            assert "不在工作單內" in str(error)
        else:
            raise AssertionError("工作單上沒有的那一篇不該被收")

    _in_corpus(body)


def test_agreement_on_contract_outcomes_is_immune_to_granularity():
    """🚨 實測：兩位讀者的標籤零逐字重疊（41 對 18），而兩邊都不算錯。

    ⚠️ 差在顆粒度——一邊拆十筆、一邊記一筆。**故標籤不可比。**
    ✅ 契約結局清單是固定的，「這篇有沒有報告結局 X」與顆粒度無關。
    """
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        request = requests[0]
        fine = _draft_for(request)
        fine["reportedOutcomes"] = [
            {"localLabel": "plasma glucose", "normalisedOutcomeRef": "o1",
             "sourceLocation": {"section": "Results"}},
            {"localLabel": "plasma lactate", "normalisedOutcomeRef": "o1",
             "sourceLocation": {"section": "Results"}}]
        coarse = _draft_for(request, inventoryId="inv:second")
        coarse["reportedOutcomes"] = [
            {"localLabel": "plasma metabolites", "normalisedOutcomeRef": "o1",
             "sourceLocation": {"section": "Results"}}]
        worksheet.write_page_drafts(out, 1, [fine],
                                    read_by={"agentClass": "model"})
        worksheet.write_page_drafts(out, 1, [coarse], lane="second",
                                    read_by={"agentClass": "model"})

        got = worksheet.agreement(
            worksheet.load_drafts(out, require_complete=False)["drafts"],
            worksheet.load_lane(out, "second")["drafts"])
        # 標籤那一組：完全不重疊——而那個 0 說的是顆粒度，不是不同意。
        assert got["labelsBoth"] == 0
        # 契約結局那一組：完全一致。
        assert got["refsBoth"] == 1
        assert got["refsOnlyPrimary"] == 0 and got["refsOnlySecond"] == 0
        assert got["reportsFullyAgreed"] == 1

    _in_corpus(body)


def test_a_real_disagreement_on_contract_outcomes_still_shows():
    """✅ 反向：顆粒度免疫**不等於**什麼都算一致。"""
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        request = requests[0]
        a = _draft_for(request)
        a["reportedOutcomes"] = [
            {"localLabel": "x", "normalisedOutcomeRef": "o1",
             "sourceLocation": {"section": "Results"}}]
        b = _draft_for(request, inventoryId="inv:second")
        b["reportedOutcomes"] = [
            {"localLabel": "x", "normalisedOutcomeRef": None,
             "sourceLocation": {"section": "Results"}}]
        worksheet.write_page_drafts(out, 1, [a], read_by={"agentClass": "model"})
        worksheet.write_page_drafts(out, 1, [b], lane="second",
                                    read_by={"agentClass": "model"})

        got = worksheet.agreement(
            worksheet.load_drafts(out, require_complete=False)["drafts"],
            worksheet.load_lane(out, "second")["drafts"])
        assert got["refsOnlyPrimary"] == 1 and got["refsBoth"] == 0
        assert got["reportsFullyAgreed"] == 0

    _in_corpus(body)


def _one_disagreement(root, candidate_id):
    """造出恰好一處契約結局層級的不一致，供裁決用。"""
    out, requests = _two_page_sheet(root, candidate_id)
    request = requests[0]
    a = _draft_for(request)
    a["reportedOutcomes"] = [{"localLabel": "x", "normalisedOutcomeRef": "o1",
                              "sourceLocation": {"section": "Results"}}]
    b = _draft_for(request, inventoryId="inv:second")
    b["reportedOutcomes"] = [{"localLabel": "x", "normalisedOutcomeRef": None,
                              "sourceLocation": {"section": "Results"}}]
    worksheet.write_page_drafts(out, 1, [a], read_by={"agentClass": "model"})
    worksheet.write_page_drafts(out, 1, [b], lane="second",
                                read_by={"agentClass": "model"})
    got = worksheet.agreement(
        worksheet.load_drafts(out, require_complete=False)["drafts"],
        worksheet.load_lane(out, "second")["drafts"])
    return got, request.report


def test_every_disagreement_must_be_given_a_cause():
    """🚫 沒判完就不算裁決過——⚠️ 那份分類比任何一致性分數有價值。"""
    def body(root, candidate_id):
        got, report = _one_disagreement(root, candidate_id)
        try:
            worksheet.adjudicate(got, {})
        except worksheet.WorksheetError as error:
            assert "未判成因" in str(error)
        else:
            raise AssertionError("沒判成因不該算裁決過")

        done = worksheet.adjudicate(got, {report: {"o1": "contract-ambiguous"}})
        assert done["byCause"] == {"contract-ambiguous": 1}
        # 🚨 它量的是可靠度，🚫 不是正確性。
        assert done["measures"] == "可靠度"
        assert "正確性" in done["doesNotMeasure"]

    _in_corpus(body)


def test_an_invented_cause_and_a_phantom_disagreement_are_both_refused():
    """⚠️ 成因要在清單內；🚨 判了不存在的不一致也要擋——那表示有人在對錯東西。"""
    def body(root, candidate_id):
        got, report = _one_disagreement(root, candidate_id)
        try:
            worksheet.adjudicate(got, {report: {"o1": "看起來還好"}})
        except worksheet.WorksheetError as error:
            assert "不在清單內" in str(error)
        else:
            raise AssertionError("自創成因不該收")

        try:
            worksheet.adjudicate(got, {report: {"o1": "granularity",
                                                "o9": "granularity"}})
        except worksheet.WorksheetError as error:
            assert "不存在的不一致" in str(error)
        else:
            raise AssertionError("判了不存在的不一致不該收")

    _in_corpus(body)


def test_the_same_paper_twice_in_one_submission_is_refused_at_write_time():
    """同一批次裡重複的 report，要在寫入時就擋，不是等到 load 才發現。

    每筆給一個新的 set() 時它會通過寫入，落盤之後才在 load_drafts 被抓到——
    錯誤出現得比必要的晚，而且檔案已經寫出去了。
    """
    def body(root, candidate_id):
        out, requests = _two_page_sheet(root, candidate_id)
        dup = [_draft_for(requests[0]), _draft_for(requests[0])]
        try:
            worksheet.write_page_drafts(out, 1, dup,
                                        read_by={"agentClass": "model"})
        except worksheet.WorksheetError as error:
            assert "重複 report" in str(error)
        else:
            raise AssertionError("同一批次裡重複的 report 不該寫得進去")
        assert not (out / "drafts" / "page-001.json").exists()

    _in_corpus(body)
