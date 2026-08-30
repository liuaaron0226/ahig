"""萃取讀取層。M1 第四步的第一塊。"""

import json
import os
import tempfile
from pathlib import Path

from ahig.extraction import (CorpusError, iter_acquired, load_document,
                             sections_titled)
from ahig.search import fulltext

FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"


def _publish(root, candidate_id="ahig:candidate:publication:aabbccddeeff001122334455"):
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {"candidateId": candidate_id,
                 "identifiers": {"pmcid": "PMC1234567"}}
    os.environ["AHIG_PRIVATE_ROOT"] = root
    manifest = fulltext._publish_jats(
        candidate, raw=raw, exchange={}, pmcid="PMC1234567",
        source_url="https://example.invalid/a.xml")
    return candidate_id, manifest


def test_a_verified_document_loads_with_its_provenance():
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        try:
            candidate_id, manifest = _publish(tmp)
            document = load_document(candidate_id)

            assert document.candidate_id == candidate_id
            assert document.route == "europe-pmc-jats"
            assert document.sections
            assert document.source_host == "example.invalid"
            assert document.sections_sha256 == manifest["artifacts"][0]["sectionsSha256"]
            # 版本不在 manifest 裡，讀取層不猜——由呼叫端明確填。
            assert document.version is None
            # 節的偏移必須真的指到 content 的那一段，否則下游兩種取法會拿到不同的字。
            first = document.sections[0]
            assert document.content[first.start_offset:first.end_offset] == first.text
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_a_document_that_fails_verification_is_not_handed_over():
    # 萃取是純讀取的一端：一筆取得後未再改寫的紀錄，在萃取讀它時沒有任何
    # 東西看過它。所以驗不過就不交，而不是交出去再附註。
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        try:
            candidate_id, manifest = _publish(tmp)
            artifact_dir = fulltext._artifact_dir(candidate_id)
            source = artifact_dir / manifest["artifacts"][0]["rawFile"]
            source.write_bytes(source.read_bytes() + b"<!-- moved -->")

            try:
                load_document(candidate_id)
            except CorpusError as error:
                assert "未通過取得層驗證" in str(error)
            else:
                raise AssertionError("來源被動過，讀取層不該交出這一篇")
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_iter_reports_unreadable_records_instead_of_skipping_them():
    # 直接跳過會讓語料悄悄變小，而變小的語料看起來跟乾淨的語料一樣。
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        try:
            candidate_id, manifest = _publish(tmp)
            artifact_dir = fulltext._artifact_dir(candidate_id)
            sections = artifact_dir / manifest["artifacts"][0]["sectionsFile"]
            body = json.loads(sections.read_text(encoding="utf-8"))
            digest = body["sourceSha256"]
            body["sourceSha256"] = digest[:-1] + ("0" if digest[-1] != "0" else "1")
            sections.write_text(json.dumps(body, ensure_ascii=False),
                                encoding="utf-8")

            results = list(iter_acquired())
            assert len(results) == 1
            _, document, error = results[0]
            assert document is None
            assert error
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_untitled_sections_are_never_matched_by_title():
    # 解析器找不到標題時寫入字面 "Untitled"，全語料有 20 節如此，其中 5 篇的
    # 首節就是它。用標題找它們永遠找不到，而那是事實不是缺陷。
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        try:
            candidate_id, _ = _publish(tmp)
            document = load_document(candidate_id)
            titles = {s.title for s in document.sections}

            assert sections_titled(document, "Untitled") == ()
            # 而有標題的節照樣取得到，否則上面那個空 tuple 沒有意義。
            real = next(t for t in titles if t.strip() and t != "Untitled")
            assert sections_titled(document, real.lower())
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old
