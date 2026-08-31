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
