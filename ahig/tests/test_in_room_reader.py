"""不花錢那條讀論文路線。

每一條測的是一種**會安靜過去**的壞法：骨架沒填卻算讀過、還沒讀被記成讀壞了、
清冊寫進版控、來源記成人讀的。
"""
from __future__ import annotations

import json
import pytest

from ahig.extraction import DraftRequest, validate_draft
from ahig.extraction.in_room_reader import (DropReader, DropReaderError,
                                            NotDrafted, draft_skeleton)
from ahig.extraction.inventory_draft import DraftRejected

SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64


def _req(report="rep1", manifestation=SHA_A):
    return DraftRequest(report=report, manifestation=manifestation,
                        scope_contract_hash=SHA_C,
                        section_titles=["Methods", "Results"],
                        content="Methods ... Results ...")


def test_drop_directory_inside_version_control_refused(tmp_path):
    """清冊含論文抄出來的字。**擋在寫進去之前，不是之後才發現。**"""
    (tmp_path / ".git").mkdir()
    with pytest.raises(DropReaderError, match="版控樹"):
        DropReader(tmp_path / "drafts")


def test_unfilled_skeleton_does_not_count_as_read(tmp_path):
    """骨架寫出去、原封不動收回來，**必須過不了驗收**。

    否則一批「全部發過骨架」的跑會得到 41 篇成功，而一個字都沒有人讀。
    """
    reader = DropReader(tmp_path)
    request = _req()
    reader.write_skeleton(request)
    draft = reader(request)
    with pytest.raises(DraftRejected, match="reportedOutcomes 為空"):
        validate_draft(draft, request)


def test_filled_skeleton_passes_validation(tmp_path):
    """骨架填上內容之後要收得下——**綁定是骨架填的，不是讀的人填的。**"""
    reader = DropReader(tmp_path)
    request = _req()
    path = reader.write_skeleton(request)
    draft = json.loads(path.read_text(encoding="utf-8"))
    draft["reportedOutcomes"] = [
        {"localLabel": "fat-free mass", "sourceLocation": {"section": "Results"}}]
    draft["completenessAttestation"]["sectionsScanned"] = ["Methods", "Results"]
    path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
    assert validate_draft(reader(request), request) is not None


def test_not_yet_read_is_distinct_from_read_badly(tmp_path):
    """「還沒讀」有自己的例外型別。

    兩者要做的事不同：一個是去讀，一個是去看讀出來的東西哪裡不對。
    都記成同一種失敗，看起來會一樣。
    """
    reader = DropReader(tmp_path)
    with pytest.raises(NotDrafted):
        reader(_req())
    bad = reader.path_for("rep1", SHA_A)
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(DropReaderError, match="讀不出來"):
        reader(_req())


def test_draft_claiming_a_human_read_it_refused(tmp_path):
    """本專案唯一的人讀不了英文文獻（ADR-0009）——那個來源記載不可能為真。"""
    reader = DropReader(tmp_path)
    request = _req()
    draft = draft_skeleton(request)
    draft["createdBy"] = {"agentClass": "human-self"}
    reader.path_for("rep1", SHA_A).write_text(
        json.dumps(draft, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(DropReaderError, match="createdBy"):
        reader(request)


def test_status_names_which_ones_are_missing(tmp_path):
    """要補的是**哪幾篇**，不是還差幾篇。"""
    reader = DropReader(tmp_path)
    reader.write_skeleton(_req("rep1", SHA_A))
    drafted, pending = reader.status(["rep1", "rep2"], [SHA_A, SHA_B])
    assert drafted == ["rep1"] and pending == ["rep2"]


def test_same_document_different_content_is_not_already_read(tmp_path):
    """同一篇換了一份 content 就不算讀過——檔名帶 manifestation 正是為此。"""
    reader = DropReader(tmp_path)
    reader.write_skeleton(_req("rep1", SHA_A))
    _drafted, pending = reader.status(["rep1"], [SHA_B])
    assert pending == ["rep1"]


def test_skeleton_is_stable_across_reissues(tmp_path):
    """重發骨架必須是同一份，否則存放處會看到兩份「內容不同」的清冊。"""
    assert draft_skeleton(_req()) == draft_skeleton(_req())
    reader = DropReader(tmp_path)
    path = reader.write_skeleton(_req())
    path.write_text('{"lifecycle": "draft", "filled": true}', encoding="utf-8")
    reader.write_skeleton(_req())
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "lifecycle": "draft", "filled": True}
