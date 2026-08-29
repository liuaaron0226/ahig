#!/usr/bin/env python3
"""W4a 全文取得與結構化解析。"""

import contextlib
import hashlib
import io
import json
import urllib.error
from email.message import Message
import os
import re
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

from ahig.contracts.freeze import content_hash
from ahig.search import fulltext


FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"


def test_jats_sections_have_paths_and_exact_global_character_offsets():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()

    parsed = fulltext.parse_jats(raw)

    assert parsed["sourceType"] == "jats-xml"
    assert parsed["parserVersion"] == "ahig-fulltext/1.0.0"
    assert [section["path"] for section in parsed["sections"]] == [
        ["Methods"],
        ["Methods", "Exercise protocol"],
        ["Results"],
        ["Results", "Table 1"],
    ]
    assert parsed["sections"][0]["text"] == (
        "Ten trained cyclists completed a randomised crossover trial."
    )
    assert parsed["sections"][2]["text"] == "Time-trial performance improved."
    for section in parsed["sections"]:
        assert parsed["content"][section["startOffset"]:section["endOffset"]] == (
            section["text"]
        )


def test_jats_preserves_body_level_paragraphs_tables_and_sections_in_order():
    raw = b"""<article><body>
      <p>Unsectioned introduction.</p>
      <table-wrap><label>Table A</label><table><tr><td>42</td></tr></table></table-wrap>
      <sec><title>Methods</title><p>Sectioned method.</p></sec>
      <p>Unsectioned closing note.</p>
    </body></article>"""

    parsed = fulltext.parse_jats(raw)

    assert [(item["kind"], item["path"], item["text"])
            for item in parsed["sections"]] == [
        ("section", ["Body"], "Unsectioned introduction."),
        ("table", ["Body", "Table A"], "Table A 42"),
        ("section", ["Methods"], "Sectioned method."),
        ("section", ["Body 2"], "Unsectioned closing note."),
    ]


def test_grobid_tei_uses_the_same_section_anchor_contract():
    raw = (FIXTURES / "sample-tei.xml").read_bytes()

    parsed = fulltext.parse_tei(raw)

    assert parsed["sourceType"] == "grobid-tei"
    assert parsed["producer"] == {"ident": "GROBID", "version": "0.9.1"}
    assert parsed["pdfLocatorReady"] is False
    assert parsed["locatorMode"] == "section-character-offset-only"
    assert [section["path"] for section in parsed["sections"]] == [
        ["Methods"],
        ["Methods", "Nutrition protocol"],
        ["Results"],
    ]
    assert parsed["sections"][1]["text"] == (
        "Carbohydrate was provided at 90 g/h during running."
    )
    for section in parsed["sections"]:
        assert parsed["content"][section["startOffset"]:section["endOffset"]] == (
            section["text"]
        )


class _FakeTransport:
    def __init__(self, body: bytes):
        self.body = body
        self.urls: list[str] = []

    def get_bytes(self, *, url: str, headers: dict | None = None) -> dict:
        self.urls.append(url)
        return {
            "body": self.body,
            "status": 200,
            "headers": {"Content-Type": "application/xml"},
            "finalUrl": url,
        }


class _ScriptedTransport:
    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.urls: list[str] = []

    def get_bytes(self, *, url: str, headers: dict | None = None) -> dict:
        self.urls.append(url)
        if not self.responses:
            raise AssertionError(f"沒有為這個 request 準備回應：{url}")
        response = dict(self.responses.pop(0))
        response.setdefault("body", b"")
        response.setdefault("status", 200)
        response.setdefault("headers", {})
        response.setdefault("finalUrl", url)
        response.setdefault("contentType", response["headers"].get("Content-Type"))
        return response


def _json_response(document: dict, *, status: int = 200) -> dict:
    return {
        "body": json.dumps(document).encode("utf-8"),
        "status": status,
        "headers": {"Content-Type": "application/json"},
    }


def test_tei_rejects_wrong_namespace_or_missing_grobid_producer():
    cases = [
        b"<TEI><text><body><div><p>x</p></div></body></text></TEI>",
        (b'<TEI xmlns="http://www.tei-c.org/ns/1.0">'
         b"<text><body><div><p>x</p></div></body></text></TEI>"),
        b"<html><body><div>x</div></body></html>",
        # producer 假陽性：ident 只是「含有」grobid，或放錯位置。
        (b'<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><encodingDesc>'
         b'<appInfo><application ident="not-grobid" version="1"/></appInfo>'
         b"</encodingDesc></teiHeader><text><body><div><head>M</head>"
         b"<p>x</p></div></body></text></TEI>"),
        (b'<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>'
         b'<application ident="GROBID" version="0.9.1"/>'
         b"<head>M</head><p>x</p></div></body></text></TEI>"),
    ]
    for raw in cases:
        try:
            fulltext.parse_tei(raw)
        except fulltext.FulltextError as exc:
            assert "TEI" in str(exc) or "GROBID" in str(exc)
        else:
            raise AssertionError("非 GROBID TEI 不得進解析產物")


def test_europe_pmc_acquisition_writes_raw_sections_and_manifest_to_private_root():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:demo123",
        "identifiers": {"pmcid": ["PMC123456"]},
    }
    transport = _FakeTransport(raw)

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(candidate, transport=transport)
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old

        artifact_dirs = list((Path(tmp) / "fulltext").iterdir())
        assert len(artifact_dirs) == 1
        assert ":" not in artifact_dirs[0].name
        manifest = json.loads(
            (artifact_dirs[0] / "manifest.json").read_text(encoding="utf-8")
        )
        assert (artifact_dirs[0] / manifest["rawFile"]).read_bytes() == raw
        sections_path = artifact_dirs[0] / manifest["sectionsFile"]
        sections = json.loads(sections_path.read_text(encoding="utf-8"))
        expected_sections_sha = (
            "sha256:" + hashlib.sha256(sections_path.read_bytes()).hexdigest()
        )

    expected_url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC123456/fullTextXML"
    )
    assert transport.urls == [expected_url]
    assert result == manifest
    assert sections["sourceSha256"] == (
        "sha256:445788b1a69d076adb2dc6d7894f44da4692b6efc34647afe59a3a5644898369"
    )
    assert manifest["candidateId"] == candidate["candidateId"]
    assert manifest["sourceUrl"] == expected_url
    assert manifest["sha256"] == sections["sourceSha256"]
    assert manifest["sectionsSha256"] == expected_sections_sha
    assert sections["contentSha256"] == (
        "sha256:" + hashlib.sha256(sections["content"].encode("utf-8")).hexdigest()
    )
    assert manifest["licence"] == {
        "href": "https://creativecommons.org/licenses/by/4.0/",
        "text": "Creative Commons Attribution 4.0 International",
    }


def test_acquire_from_run_root_resolves_candidates_and_reports_counts():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:batch-one",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            run_root = Path(tmp) / "search-runs" / "demo"
            pool = run_root / "candidate-pool"
            pool.mkdir(parents=True)
            candidates_path = pool / "candidates.json"
            candidates_path.write_text(
                json.dumps([candidate]), encoding="utf-8"
            )
            (pool / "manifest.json").write_text(json.dumps({
                "runId": "demo-run",
                "searchContractHash": "sha256:" + "a" * 64,
            }), encoding="utf-8")
            expected_pool_hash = (
                "sha256:" + hashlib.sha256(candidates_path.read_bytes()).hexdigest()
            )
            transport = _FakeTransport(raw)
            result = fulltext.acquire_from_run_root(
                run_root,
                [candidate["candidateId"], candidate["candidateId"]],
                transport=transport,
                now=lambda: "2026-08-15T01:02:03Z",
            )
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            manifest_path = artifact_dir / "manifest.json"
            paper_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            paper_manifest_sha = (
                "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            )
            paper_manifest_rel = (
                f"fulltext/{artifact_dir.name}/manifests/manifest-"
                f"{paper_manifest_sha.removeprefix('sha256:')[:16]}.json"
            )
            batch_path = run_root / result["batchManifest"]
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old

    assert result["candidateCount"] == 1
    assert result["acquiredCount"] == 1
    assert result["unavailableCount"] == 0
    assert result["results"][0]["candidateId"] == candidate["candidateId"]
    assert len(transport.urls) == 1
    assert paper_manifest["bindings"] == [{
        "runId": "demo-run",
        "candidatePoolHash": expected_pool_hash,
        "candidateRecordHash": content_hash(candidate),
    }]
    assert batch["runId"] == "demo-run"
    assert batch["candidatePoolHash"] == expected_pool_hash
    assert batch["candidateCount"] == 1
    assert batch["results"] == [{
        "candidateId": candidate["candidateId"],
        "status": "acquired",
        "manifestPath": paper_manifest_rel,
        "manifestSha256": paper_manifest_sha,
    }]
    unhashed = {key: value for key, value in batch.items() if key != "batchHash"}
    assert batch["batchHash"] == content_hash(unhashed)


def test_earlier_batch_keeps_resolvable_immutable_manifest_after_reuse():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:cross-run",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            run_root = Path(tmp) / "search-runs" / "demo"
            pool = run_root / "candidate-pool"
            pool.mkdir(parents=True)
            (pool / "candidates.json").write_text(
                json.dumps([candidate]), encoding="utf-8"
            )
            pool_manifest = pool / "manifest.json"
            pool_manifest.write_text(json.dumps({"runId": "run-a"}),
                                     encoding="utf-8")
            first = fulltext.acquire_from_run_root(
                run_root, [candidate["candidateId"]],
                transport=_FakeTransport(raw),
                now=lambda: "2026-08-15T01:00:00Z")
            first_batch = json.loads(
                (run_root / first["batchManifest"]).read_text(encoding="utf-8")
            )
            first_ref = first_batch["results"][0]

            pool_manifest.write_text(json.dumps({"runId": "run-b"}),
                                     encoding="utf-8")
            fulltext.acquire_from_run_root(
                run_root, [candidate["candidateId"]],
                transport=_FakeTransport(raw),
                now=lambda: "2026-08-15T02:00:00Z")

            generation = Path(tmp) / first_ref["manifestPath"]
            generation_bytes = generation.read_bytes()
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old

    assert ("sha256:" + hashlib.sha256(generation_bytes).hexdigest()
            == first_ref["manifestSha256"])


def test_concurrent_publication_of_one_candidate_is_serialised():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:concurrent",
        "identifiers": {"pmcid": ["PMC123456"]},
    }
    barrier = threading.Barrier(2)
    results: list[dict] = []
    errors: list[BaseException] = []

    def worker():
        try:
            barrier.wait(timeout=10)
            results.append(
                fulltext.acquire_fulltext(
                    candidate, transport=_FakeTransport(raw)))
        except BaseException as exc:       # noqa: BLE001 - 交給主執行緒斷言
            errors.append(exc)

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            manifest = json.loads(
                (artifact_dir / "manifest.json").read_text(encoding="utf-8")
            )
            generations = sorted(
                (artifact_dir / "manifests").glob("manifest-*.json"))
            leftovers = sorted(
                path.name for path in artifact_dir.glob(".publish.lock"))
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old

    assert errors == []
    # 序列化的可觀察結果：兩邊都成功、只提交一份 artifact、鎖檔已釋放，
    # 且沒有互刪造成的多餘 generation。
    assert len(results) == 2
    assert all(item["status"] == "acquired" for item in results)
    assert manifest["status"] == "acquired"
    assert len(manifest["artifacts"]) == 1
    assert len(generations) == 1
    assert leftovers == []


def test_sweeper_running_beside_publisher_never_destroys_committed_evidence():
    """掃除與發佈是同一份多檔交易的兩端；並行時不得互毀。

    單執行緒測不到這條，所以真的開兩條執行緒對打。
    """
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:sweep-race",
        "identifiers": {"pmcid": ["PMC123456"]},
    }
    staged = threading.Event()
    sweep_attempted = threading.Event()
    errors: list[str] = []
    original_write = fulltext._write_committed_manifest

    def pause_at_staging(artifact_dir, manifest):
        """在 staged 檔已寫、manifest 未提交的視窗停住，讓 sweeper 撞上來。"""
        if manifest.get("status") == "acquired" and not staged.is_set():
            staged.set()
            # 給 sweeper 足夠時間嘗試進入；鎖有效時它會被擋在外面。
            sweep_attempted.wait(timeout=5)
        return original_write(artifact_dir, manifest)

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        root = Path(tmp) / "fulltext"

        def publish():
            try:
                fulltext.acquire_fulltext(
                    candidate, transport=_FakeTransport(raw))
            except Exception as exc:       # noqa: BLE001
                errors.append(f"publish:{type(exc).__name__}")

        def sweep():
            staged.wait(timeout=30)
            sweep_attempted.set()
            try:
                for entry in (root.iterdir() if root.exists() else []):
                    if entry.is_dir():
                        fulltext.sweep_orphans(entry)
            except Exception as exc:       # noqa: BLE001
                errors.append(f"sweep:{type(exc).__name__}")

        try:
            with patch.object(fulltext, "_write_committed_manifest",
                              side_effect=pause_at_staging):
                threads = [threading.Thread(target=publish),
                           threading.Thread(target=sweep)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=60)
            artifact_dir = next(root.iterdir())
            manifest = json.loads(
                (artifact_dir / "manifest.json").read_text(encoding="utf-8"))
            # 鎖若失效，sweeper 會在這個視窗刪掉 staged 檔，
            # 提交後的 manifest 就會指向不存在的 artifact。
            fulltext._verify_committed_artifacts(artifact_dir, manifest)
            assert errors == []
            assert manifest["status"] == "acquired"
            assert list(artifact_dir.glob(".publish.lock")) == []
        finally:
            sweep_attempted.set()
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_artifact_writes_refuse_directories_that_escape_the_private_root():
    """junction／symlink 讓候選目錄指到私密根外時，落盤必須擋下。

    本機不一定有建立連結的權限，所以用「直接把逃逸目錄交給寫入路徑」
    來驗邊界檢查本身——真實 junction 的差別只在誰產生那個路徑。
    """
    manifest = {
        "documentType": "fulltext-acquisition-manifest",
        "candidateId": "ahig:candidate:publication:junction",
        "status": "incomplete",
        "attempts": [],
        "artifacts": [],
    }

    with tempfile.TemporaryDirectory() as tmp:
        outside = Path(tmp) / "outside"
        private = Path(tmp) / "private"
        outside.mkdir()
        private.mkdir()
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = str(private)
        try:
            for call in (
                lambda: fulltext._write_committed_manifest(outside, manifest),
                lambda: fulltext.sweep_orphans(outside),
            ):
                try:
                    call()
                except fulltext.FulltextError as exc:
                    assert "AHIG_PRIVATE_ROOT" in str(exc)
                else:
                    raise AssertionError("逃出私密根的 artifact 目錄必須拒絕")
            assert list(outside.iterdir()) == []
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_corrupted_artifact_does_not_make_sweep_destroy_the_evidence():
    """掃除是回復工具：artifact 內容損毀時不得連 manifest 與 generation 一起清掉。"""
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:corrupted",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            manifest = fulltext.acquire_fulltext(
                candidate, transport=_FakeTransport(raw))
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            sections = artifact_dir / manifest["sectionsFile"]
            sections.write_bytes(sections.read_bytes() + b" ")

            removed = fulltext.sweep_orphans(artifact_dir)

            assert removed == []
            assert (artifact_dir / "manifest.json").exists()
            assert (artifact_dir / manifest["rawFile"]).exists()
            assert list((artifact_dir / "manifests").glob("*.json"))
            assert not (artifact_dir / "invalid-manifests").exists()
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_cached_reuse_never_returns_an_artifact_corrupted_after_the_check():
    """鎖外驗證通過後 artifact 才被破壞時，不得回傳 acquired。

    註：這條不變式目前由 `_publish_jats_locked` 與快取路徑兩處的
    `_verify_committed_artifacts` 共同守住，任一處都足以擋下；因此單獨
    移除快取路徑那行不會讓本測試轉紅（已實測）。保留這個測試是為了釘住
    「破壞後不得回傳 acquired」這個對外行為，而不是釘住某一行實作。
    """
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:reverify",
        "identifiers": {"pmcid": ["PMC123456"]},
    }
    swapped = threading.Event()

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            fulltext.acquire_fulltext(candidate, transport=_FakeTransport(raw))
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            manifest_path = artifact_dir / "manifest.json"
            committed = json.loads(manifest_path.read_bytes())
            raw_file = artifact_dir / committed["artifacts"][0]["rawFile"]
            original_lock = fulltext._candidate_lock

            @contextlib.contextmanager
            def corrupt_after_acquiring(*args, **kwargs):
                """鎖外檢查時 artifact 完好，取得鎖後才被破壞。

                candidateId／status／pmcid 全程不動，所以只有鎖內的
                完整性重驗擋得住這個情境。
                """
                with original_lock(*args, **kwargs):
                    if not swapped.is_set():
                        swapped.set()
                        raw_file.write_bytes(b"<article>tampered</article>")
                    yield

            with patch.object(fulltext, "_candidate_lock",
                              side_effect=corrupt_after_acquiring):
                try:
                    fulltext.acquire_fulltext(
                        candidate, transport=_FakeTransport(raw),
                        binding={"runId": "later"})
                except fulltext.FulltextError:
                    pass
                else:
                    raise AssertionError("鎖內必須重驗，不得回傳失效 acquired")
            assert swapped.is_set()
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_invalid_latest_manifest_never_takes_immutable_generations_with_it():
    """latest manifest 壞掉是指標問題；content-addressed generation 必須存活。

    否則舊 batch 的 manifestPath 會跟著失效，回復工具反而製造失證。
    """
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:generation-survives",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            fulltext.acquire_fulltext(candidate, transport=_FakeTransport(raw))
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            before = {path.name: path.read_bytes()
                      for path in (artifact_dir / "manifests").glob("*.json")}
            assert before

            # 未來新增的 status 值會讓封閉列舉的結構驗證失敗——正是最容易
            # 誤觸的情境。
            manifest_path = artifact_dir / "manifest.json"
            broken = json.loads(manifest_path.read_text(encoding="utf-8"))
            broken["status"] = "acquired-pdf"
            manifest_path.write_text(json.dumps(broken), encoding="utf-8")

            fulltext.sweep_orphans(artifact_dir)

            after = {path.name: path.read_bytes()
                     for path in (artifact_dir / "manifests").glob("*.json")}
            assert after == before
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_batch_manifest_write_refuses_paths_outside_the_private_root():
    """batch 目錄若被換成指向私密根外的連結，寫入必須擋下。

    用 patch 讓 batch 目錄解析到外部，等價於 junction；重點是驗
    `acquire_from_run_root` 這個真正的寫入點有做邊界檢查。
    """
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:batch-escape",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        outside = Path(tmp) / "outside"
        private = Path(tmp) / "private"
        outside.mkdir()
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = str(private)
        try:
            run_root = private / "search-runs" / "demo"
            pool = run_root / "candidate-pool"
            pool.mkdir(parents=True)
            (pool / "candidates.json").write_text(
                json.dumps([candidate]), encoding="utf-8")
            (pool / "manifest.json").write_text(
                json.dumps({"runId": "escape"}), encoding="utf-8")

            real_resolve = Path.resolve

            def fake_resolve(self, *args, **kwargs):
                if self.name == "fulltext-acquisition":
                    return real_resolve(outside, *args, **kwargs)
                return real_resolve(self, *args, **kwargs)

            with patch.object(Path, "resolve", fake_resolve):
                try:
                    fulltext.acquire_from_run_root(
                        run_root, [candidate["candidateId"]],
                        transport=_FakeTransport(raw))
                except fulltext.FulltextError as exc:
                    assert "AHIG_PRIVATE_ROOT" in str(exc)
                else:
                    raise AssertionError("batch 路徑逃逸必須拒絕")
            assert list(outside.iterdir()) == []
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_stale_publish_lock_is_reclaimed_instead_of_deadlocking():
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = str(tmp)
        try:
            artifact_dir = Path(tmp) / "fulltext" / "stale-0000000000000000"
            artifact_dir.mkdir(parents=True)
            lock = artifact_dir / ".publish.lock"
            lock.write_bytes(b"")
            os.utime(lock, (0, 0))          # 模擬被砍行程留下的舊鎖

            with fulltext._candidate_lock(artifact_dir, timeout=1.0,
                                          stale_after=1.0):
                assert lock.exists()
            assert not lock.exists()
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_semantically_invalid_manifest_cannot_protect_orphans():
    cases = [
        b"{ not json",
        b"{}",
        json.dumps({
            "documentType": "fulltext-acquisition-manifest",
            "candidateId": "ahig:candidate:publication:sweep",
            "status": "acquired",
            "attempts": [],
            "artifacts": [{"rawFile": "source-deadbeefdeadbeef.jats.xml",
                           "sectionsFile": "sections-vbogus.json"}],
        }).encode("utf-8"),
    ]
    for index, manifest_bytes in enumerate(cases):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("AHIG_PRIVATE_ROOT")
            os.environ["AHIG_PRIVATE_ROOT"] = tmp
            try:
                artifact_dir = Path(tmp) / "fulltext" / f"sweep-{index}"
                artifact_dir.mkdir(parents=True)
                (artifact_dir / "source-deadbeefdeadbeef.jats.xml").write_bytes(
                    b"<article/>")
                (artifact_dir / "sections-vbogus.json").write_bytes(b"{}")
                (artifact_dir / "manifest.json").write_bytes(manifest_bytes)

                removed = fulltext.sweep_orphans(artifact_dir)

                assert sorted(removed) == [
                    "sections-vbogus.json",
                    "source-deadbeefdeadbeef.jats.xml",
                ]
                assert not (artifact_dir / "manifest.json").exists()
                quarantined = list((artifact_dir / "invalid-manifests").iterdir())
                assert len(quarantined) == 1
                assert quarantined[0].read_bytes() == manifest_bytes
            finally:
                if old is None:
                    os.environ.pop("AHIG_PRIVATE_ROOT", None)
                else:
                    os.environ["AHIG_PRIVATE_ROOT"] = old


def test_urllib_binary_transport_preserves_raw_bytes_and_http_metadata():
    class _Headers(dict):
        def items(self):
            return super().items()

    class _Response:
        status = 200
        headers = _Headers({"Content-Type": "application/xml; charset=utf-8"})

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"<article/>"

        def geturl(self):
            return "https://example.test/final.xml"

    with patch("ahig.search.fulltext.urllib.request.urlopen",
               return_value=_Response()) as opened:
        result = fulltext.UrllibBinaryTransport(attempts=1).get_bytes(
            url="https://example.test/source.xml",
            headers={"Accept": "application/xml"},
        )

    assert result == {
        "body": b"<article/>",
        "status": 200,
        "headers": {"Content-Type": "application/xml; charset=utf-8"},
        "finalUrl": "https://example.test/final.xml",
        "contentType": "application/xml; charset=utf-8",
    }
    request = opened.call_args.args[0]
    assert request.get_header("Accept") == "application/xml"


def test_urllib_transport_returns_permanent_http_miss_for_state_machine():
    headers = Message()
    headers["Content-Type"] = "text/plain"
    error = urllib.error.HTTPError(
        "https://example.test/missing", 404, "Not Found", headers,
        io.BytesIO(b"missing"),
    )

    with patch("ahig.search.fulltext.urllib.request.urlopen",
               side_effect=error):
        result = fulltext.UrllibBinaryTransport(attempts=1).get_bytes(
            url="https://example.test/missing"
        )

    assert result["status"] == 404
    assert result["body"] == b"missing"
    assert result["contentType"] == "text/plain"


def test_acquisition_refuses_to_replace_a_different_existing_source():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    changed = raw.replace(b"Ten trained cyclists", b"Nine trained cyclists")
    candidate = {
        "candidateId": "ahig:candidate:publication:immutable",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            fulltext.acquire_fulltext(candidate, transport=_FakeTransport(raw))
            try:
                fulltext.acquire_fulltext(
                    candidate, transport=_FakeTransport(changed)
                )
            except fulltext.FulltextError as exc:
                assert "既有原始全文" in str(exc)
            else:
                raise AssertionError("不同的遠端全文不得覆寫既有證據")
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_reacquisition_detects_tampered_sections_instead_of_overwriting_them():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:tampered-sections",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            manifest = fulltext.acquire_fulltext(
                candidate, transport=_FakeTransport(raw)
            )
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            (artifact_dir / manifest["sectionsFile"]).write_text(
                "{}\n", encoding="utf-8"
            )
            try:
                fulltext.acquire_fulltext(
                    candidate, transport=_FakeTransport(raw)
                )
            except fulltext.FulltextError as exc:
                assert "sectionsSha256" in str(exc)
            else:
                raise AssertionError("竄改的 sections 不得被重新取得掩蓋")
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_jats_rejects_html_error_pages_even_when_they_contain_a_body():
    raw = b"<html><body><p>Service unavailable</p></body></html>"

    try:
        fulltext.parse_jats(raw)
    except fulltext.FulltextError as exc:
        assert "JATS article" in str(exc)
    else:
        raise AssertionError("HTML 錯誤頁不得被標為 JATS 全文")


def test_inline_xml_markup_does_not_insert_spaces_inside_terms_or_units():
    raw = (
        b"<article><body><sec><title>Methods</title><p>"
        b"CHO<sub>ex</sub> oxidation reached 1.5 g h<sup>-1</sup>."
        b"</p></sec></body></article>"
    )

    parsed = fulltext.parse_jats(raw)

    assert parsed["sections"][0]["text"] == (
        "CHOex oxidation reached 1.5 g h-1."
    )


def test_unavailable_lookup_cannot_downgrade_an_acquired_artifact():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    acquired = {
        "candidateId": "ahig:candidate:publication:no-downgrade",
        "identifiers": {"pmcid": ["PMC123456"]},
    }
    rediscovered_without_oa = {
        "candidateId": acquired["candidateId"],
        "identifiers": {"pmcid": [], "pmid": ["2335168"]},
    }
    lookup = json.dumps({
        "resultList": {"result": [{
            "pmid": "2335168", "isOpenAccess": "N",
        }]}
    }).encode("utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            fulltext.acquire_fulltext(
                acquired, transport=_FakeTransport(raw)
            )
            try:
                fulltext.acquire_fulltext(
                    rediscovered_without_oa,
                    transport=_FakeTransport(lookup),
                )
            except fulltext.FulltextError as exc:
                assert "PMCID" in str(exc) or "acquired" in str(exc)
            else:
                raise AssertionError("acquired artifact 不得降級為 unavailable")
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_artifact_directories_use_digest_to_avoid_windows_slug_collisions():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidates = [
        {"candidateId": "ahig:candidate:publication:x?y",
         "identifiers": {"pmcid": ["PMC111"]}},
        {"candidateId": "ahig:candidate:publication:x*y",
         "identifiers": {"pmcid": ["PMC222"]}},
    ]

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            results = [fulltext.acquire_fulltext(
                candidate, transport=_FakeTransport(raw))
                for candidate in candidates]
            directories = sorted((Path(tmp) / "fulltext").iterdir())
            stored_ids = {
                json.loads((path / "manifest.json").read_text(
                    encoding="utf-8"))["candidateId"]
                for path in directories
            }
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old

    assert len(directories) == 2
    assert directories[0].name != directories[1].name
    assert all(re.search(r"-[0-9a-f]{16}$", path.name) for path in directories)
    assert stored_ids == {candidate["candidateId"] for candidate in candidates}
    assert {result["candidateId"] for result in results} == stored_ids


def test_reuse_rejects_pmcid_or_source_url_binding_drift():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    first = {"candidateId": "ahig:candidate:publication:binding",
             "identifiers": {"pmcid": ["PMC111"]}}
    drifted = {"candidateId": first["candidateId"],
               "identifiers": {"pmcid": ["PMC222"]}}

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            fulltext.acquire_fulltext(first, transport=_FakeTransport(raw))
            try:
                fulltext.acquire_fulltext(
                    drifted, transport=_FakeTransport(raw))
            except fulltext.FulltextError as exc:
                assert "PMCID" in str(exc) or "source URL" in str(exc)
            else:
                raise AssertionError("reuse 不得接受 PMCID/source URL 漂移")
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_acquisition_rejects_conflicting_pmcid_or_pmid_before_network_access():
    cases = [
        ({"pmcid": ["PMC111", "PMC222"]}, b"<article/>"),
        ({"pmcid": [], "pmid": ["111", "222"]}, b"{}"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            for index, (identifiers, body) in enumerate(cases):
                candidate = {
                    "candidateId": f"ahig:candidate:publication:conflict-{index}",
                    "identifiers": identifiers,
                }
                transport = _FakeTransport(body)
                try:
                    fulltext.acquire_fulltext(candidate, transport=transport)
                except fulltext.FulltextError as exc:
                    assert "多個不同" in str(exc)
                    assert transport.urls == []
                else:
                    raise AssertionError("identifier conflict 必須 fail-closed")
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old


def test_jats_tables_are_separate_anchored_sections():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()

    parsed = fulltext.parse_jats(raw)
    tables = [item for item in parsed["sections"] if item.get("kind") == "table"]

    assert len(tables) == 1
    assert tables[0]["path"] == ["Results", "Table 1"]
    assert tables[0]["title"] == "Table 1"
    assert "Reported outcomes" in tables[0]["text"]
    assert "GI symptoms 2" in tables[0]["text"]
    assert parsed["content"][tables[0]["startOffset"]:tables[0]["endOffset"]] == (
        tables[0]["text"]
    )


def test_source_chain_continues_from_europe_pmc_miss_to_openalex_pdf():
    candidate = {
        "candidateId": "ahig:candidate:publication:oa-chain",
        "identifiers": {"pmcid": [], "pmid": ["2335168"],
                        "doi": ["10.1007/example"]},
    }
    transport = _ScriptedTransport([
        _json_response({"resultList": {"result": [{
            "pmid": "2335168", "isOpenAccess": "N",
        }]}}),
        _json_response({
            "id": "https://openalex.org/W1",
            "best_oa_location": {
                "pdf_url": "https://example.org/paper.pdf",
                "landing_page_url": "https://example.org/article",
                "license": "cc-by",
            },
        }),
    ])

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(
                candidate, transport=transport,
                contact_email="owner@example.com",
                now=lambda: "2026-08-15T00:00:00Z",
            )
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root

    assert result["status"] == "available-pdf"
    assert [attempt["sourceId"] for attempt in result["attempts"]] == [
        "europe-pmc", "openalex",
    ]
    assert [attempt["conclusion"] for attempt in result["attempts"]] == [
        "miss", "available-pdf",
    ]
    assert result["availableUrl"] == "https://example.org/paper.pdf"
    assert all(attempt["attemptedAt"] == "2026-08-15T00:00:00Z"
               for attempt in result["attempts"])


def test_no_oa_fulltext_requires_all_three_sources_to_miss():
    candidate = {
        "candidateId": "ahig:candidate:publication:no-oa-chain",
        "identifiers": {"pmcid": [], "pmid": ["2335168"],
                        "doi": ["10.1007/example"]},
    }
    transport = _ScriptedTransport([
        _json_response({"resultList": {"result": []}}),
        {"status": 404, "body": b"not found"},
        {"status": 404, "body": b"not found"},
    ])

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(
                candidate, transport=transport,
                contact_email="owner@example.com",
                now=lambda: "2026-08-15T00:00:00Z",
            )
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root

    assert result["status"] == "no-oa-fulltext"
    assert [attempt["conclusion"] for attempt in result["attempts"]] == [
        "miss", "miss", "miss",
    ]
    assert [attempt["httpStatus"] for attempt in result["attempts"]] == [
        200, 404, 404,
    ]


def test_non_2xx_fulltext_response_is_never_parsed_as_evidence():
    """404 的 body 就算長得像 JATS 也不得成為 acquired 證據。"""
    candidate = {
        "candidateId": "ahig:candidate:publication:not-found",
        "identifiers": {"pmcid": ["PMC777777"]},
    }
    jats_shaped_error_page = (FIXTURES / "sample-jats.xml").read_bytes()
    transport = _ScriptedTransport([
        {"status": 404, "body": jats_shaped_error_page},
        _json_response({"results": []}),
        _json_response({"is_oa": False}),
    ])

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(
                candidate, transport=transport,
                contact_email="owner@example.com",
                now=lambda: "2026-08-15T00:00:00Z")
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            staged = sorted(path.name for path in artifact_dir.glob("source-*"))
        finally:
            if old is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old

    assert result["status"] != "acquired"
    assert result["attempts"][0]["conclusion"] == "miss"
    assert result["attempts"][0]["httpStatus"] == 404
    assert result["artifacts"] == []
    assert staged == []


def test_candidate_without_identifiers_is_blocked_not_terminal_no_oa():
    candidate = {
        "candidateId": "ahig:candidate:publication:no-identifiers",
        "identifiers": {"pmcid": [], "pmid": [], "doi": []},
    }
    transport = _ScriptedTransport([])

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(
                candidate, transport=transport,
                contact_email="owner@example.com",
                now=lambda: "2026-08-15T00:00:00Z",
            )
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root

    assert transport.urls == []
    assert [attempt["conclusion"] for attempt in result["attempts"]] == [
        "not-applicable", "not-applicable", "not-applicable",
    ]
    assert result["status"] == "incomplete"


def test_landing_page_only_oa_is_not_reported_as_available_pdf():
    candidate = {
        "candidateId": "ahig:candidate:publication:landing-only",
        "identifiers": {"pmcid": [], "pmid": [], "doi": ["10.1007/example"]},
    }
    transport = _ScriptedTransport([
        _json_response({"resultList": {"result": []}}),
        _json_response({
            "id": "https://openalex.org/W2",
            "best_oa_location": {
                "landing_page_url": "https://example.org/article",
                "license": "cc-by",
            },
        }),
    ])

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(
                candidate, transport=transport,
                contact_email="owner@example.com",
                now=lambda: "2026-08-15T00:00:00Z",
            )
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root

    assert result["status"] == "available-landing-page"
    assert result["attempts"][-1]["conclusion"] == "available-landing-page"
    assert result["availableUrl"] == "https://example.org/article"


def test_missing_unpaywall_email_keeps_chain_incomplete_not_no_oa():
    candidate = {
        "candidateId": "ahig:candidate:publication:blocked-unpaywall",
        "identifiers": {"pmcid": [], "pmid": ["2335168"],
                        "doi": ["10.1007/example"]},
    }
    transport = _ScriptedTransport([
        _json_response({"resultList": {"result": []}}),
        {"status": 404, "body": b"not found"},
    ])

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            result = fulltext.acquire_fulltext(
                candidate, transport=transport, contact_email=None,
                now=lambda: "2026-08-15T00:00:00Z",
            )
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root

    assert result["status"] == "incomplete"
    assert result["attempts"][-1]["sourceId"] == "unpaywall"
    assert result["attempts"][-1]["conclusion"] == "blocked"
    assert result["attempts"][-1]["httpStatus"] is None


def test_parser_upgrade_adds_versioned_sections_without_overwriting_old_version():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:versioned",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            first = fulltext.acquire_fulltext(
                candidate, transport=_FakeTransport(raw)
            )
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            first_sections = artifact_dir / first["sectionsFile"]
            first_bytes = first_sections.read_bytes()
            with patch.object(fulltext, "PARSER_VERSION", "ahig-fulltext/2.0.0"):
                second = fulltext.acquire_fulltext(
                    candidate, transport=_FakeTransport(raw)
                )
            stored = json.loads(
                (artifact_dir / "manifest.json").read_text(encoding="utf-8")
            )
            assert first_sections.read_bytes() == first_bytes
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root

    assert second["sectionsFile"] != first["sectionsFile"]
    assert len(stored["artifacts"]) == 2
    assert {item["parserVersion"] for item in stored["artifacts"]} == {
        "ahig-fulltext/1.0.0", "ahig-fulltext/2.0.0",
    }


def test_manifest_failure_leaves_sweepable_orphans_not_committed_evidence():
    raw = (FIXTURES / "sample-jats.xml").read_bytes()
    candidate = {
        "candidateId": "ahig:candidate:publication:interrupted",
        "identifiers": {"pmcid": ["PMC123456"]},
    }

    with tempfile.TemporaryDirectory() as tmp:
        old_root = os.environ.get("AHIG_PRIVATE_ROOT")
        os.environ["AHIG_PRIVATE_ROOT"] = tmp
        try:
            with patch("ahig.search.fulltext.atomic_write_json",
                       side_effect=OSError("simulated manifest failure")):
                try:
                    fulltext.acquire_fulltext(
                        candidate, transport=_FakeTransport(raw)
                    )
                except OSError as exc:
                    assert "simulated manifest failure" in str(exc)
                else:
                    raise AssertionError("manifest 寫入失敗必須向上拋出")
            artifact_dir = next((Path(tmp) / "fulltext").iterdir())
            assert not (artifact_dir / "manifest.json").exists()
            staged = sorted(path.name for path in artifact_dir.iterdir())
            assert len(staged) == 3          # raw + sections + generation dir

            removed = fulltext.sweep_orphans(artifact_dir)

            # staged 的 raw/sections 是孤兒可清；但 content-addressed 的
            # generation 一律保留——它能自證，且可能被既有 batch 引用。
            assert len(removed) == 2
            assert sorted(path.name for path in artifact_dir.iterdir()) == [
                "manifests"
            ]
        finally:
            if old_root is None:
                os.environ.pop("AHIG_PRIVATE_ROOT", None)
            else:
                os.environ["AHIG_PRIVATE_ROOT"] = old_root


def test_artifact_files_names_the_raw_file_after_its_source_kind():
    # n+123(5) 要求 PDF 路徑同時記下抓回的 PDF 與 GROBID 產出的 TEI。
    # 兩者都會經過 _artifact_files，所以副檔名不能寫死成 jats。
    source = "sha256:" + "a" * 64
    sections = "sha256:" + "b" * 64

    jats_raw, jats_sections = fulltext._artifact_files(source, "v/1.0.0", sections)
    tei_raw, tei_sections = fulltext._artifact_files(
        source, "v/1.0.0", sections, source_kind="tei")
    pdf_raw, _ = fulltext._artifact_files(
        source, "v/1.0.0", sections, source_kind="pdf")

    assert jats_raw.endswith(".jats.xml")
    assert tei_raw.endswith(".tei.xml")
    assert pdf_raw.endswith(".pdf")
    # sections 檔名不隨來源型別改變——它記的是 parser 與兩個雜湊，不是容器格式。
    assert jats_sections == tei_sections

    # 該檔未匯入 pytest，沿用其既有之 try/except/else 寫法。
    try:
        fulltext._artifact_files(source, "v/1.0.0", sections, source_kind="docx")
    except fulltext.FulltextError as exc:
        assert "docx" in str(exc)
    else:
        raise AssertionError("未知來源型別必須被拒絕")
