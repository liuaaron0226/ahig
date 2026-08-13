"""公開 metadata 搜尋 runner：續跑、原始回應、分頁與 fail-closed。

全部使用 fake transport，不碰外網。正式 API 只在單元／整合測試全綠後執行。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ahig.search import runner

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "calibration" / "b11-carbohydrate" / "search-contract.json"


class FakeTransport:
    def __init__(self, responses: list[dict | Exception]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get_json(self, *, url: str, params: dict, headers: dict | None = None) -> dict:
        self.calls.append({"url": url, "params": dict(params), "headers": dict(headers or {})})
        if not self.responses:
            raise AssertionError("fake transport 沒有下一個 response")
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def epmc_page(ids: list[str], next_cursor: str | None = None, hit_count: int | None = None):
    value = {
        "hitCount": hit_count if hit_count is not None else len(ids),
        "resultList": {"result": [{"id": i, "source": "MED", "title": i} for i in ids]},
    }
    if next_cursor is not None:
        value["nextCursorMark"] = next_cursor
    return value


def ct_page(ids: list[str], next_token: str | None = None, total: int | None = None):
    value = {
        "studies": [{"protocolSection": {"identificationModule": {"nctId": i,
                                                                      "briefTitle": i}}}
                    for i in ids],
        "totalCount": total if total is not None else len(ids),
    }
    if next_token is not None:
        value["nextPageToken"] = next_token
    return value


def pubmed_initial(count: int = 2):
    return {"esearchresult": {"count": str(count), "querykey": "1",
                              "webenv": "TEST-WEBENV", "idlist": []}}


def pubmed_summary(ids: list[str]):
    result = {"uids": ids}
    for uid in ids:
        result[uid] = {"uid": uid, "title": uid, "pubdate": "2020"}
    return {"result": result}


def run_with(tmp: str, fake: FakeTransport, *, only: list[str] | None = None,
             dry_run: bool = False, redo: bool = False, run_id: str = "run-001"):
    with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
        return runner.run_search(
            contract_path=CONTRACT, only=only, dry_run=dry_run, redo=redo,
            run_id=run_id, transport=fake)


# ---------------------------------------------------------------------------
# dry-run 與私密根
# ---------------------------------------------------------------------------

def test_dry_run_does_not_require_private_root_or_write_files():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {}, clear=True):
            result = runner.run_search(CONTRACT, only=["europe-pmc"], dry_run=True,
                                       run_id="dry", transport=FakeTransport([]))
        assert result["status"] == "dry-run"
        assert list(Path(tmp).iterdir()) == []


def test_real_run_requires_private_root():
    with patch.dict(os.environ, {}, clear=True):
        try:
            runner.run_search(CONTRACT, only=["europe-pmc"], dry_run=False,
                              run_id="x", transport=FakeTransport([]))
        except RuntimeError as exc:
            assert "AHIG_PRIVATE_ROOT" in str(exc)
            return
    raise AssertionError("實際搜尋未設私密根必須 fail-closed")


def test_outputs_only_under_private_root():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, FakeTransport([epmc_page(["A"])]),
                          only=["europe-pmc"])
        run_root = Path(result["runRoot"])
        assert run_root.is_relative_to(Path(tmp).resolve())
        assert not (ROOT / "jobs").exists()


# ---------------------------------------------------------------------------
# Europe PMC cursor
# ---------------------------------------------------------------------------

def test_europe_pmc_follows_cursor_and_retains_raw_pages():
    fake = FakeTransport([
        epmc_page(["A", "B"], next_cursor="c2", hit_count=3),
        epmc_page(["C"], hit_count=3),
    ])
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, fake, only=["europe-pmc"])
        source = result["sources"]["europe-pmc"]
        assert source["status"] == "completed"
        assert source["recordCount"] == 3
        assert len(fake.calls) == 2
        assert fake.calls[0]["params"]["cursorMark"] == "*"
        assert fake.calls[1]["params"]["cursorMark"] == "c2"
        raw = sorted((Path(result["runRoot"]) / "sources" / "europe-pmc"
                      / "responses").glob("*.json"))
        assert len(raw) == 2
        assert json.loads(raw[0].read_text(encoding="utf-8"))["hitCount"] == 3


def test_europe_pmc_repeated_cursor_is_a_failure_not_infinite_loop():
    fake = FakeTransport([
        epmc_page(["A"], next_cursor="same", hit_count=2),
        epmc_page(["B"], next_cursor="same", hit_count=2),
    ])
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, fake, only=["europe-pmc"])
        source = result["sources"]["europe-pmc"]
        assert source["status"] == "failed"
        assert "cursor" in source["error"].lower()


# ---------------------------------------------------------------------------
# ClinicalTrials.gov page token
# ---------------------------------------------------------------------------

def test_clinical_trials_follows_page_token():
    fake = FakeTransport([
        ct_page(["NCT1"], next_token="p2", total=2),
        ct_page(["NCT2"], total=2),
    ])
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, fake, only=["clinicaltrials-gov"])
        source = result["sources"]["clinicaltrials-gov"]
        assert source["status"] == "completed" and source["recordCount"] == 2
        assert "pageToken" not in fake.calls[0]["params"]
        assert fake.calls[1]["params"]["pageToken"] == "p2"


def test_clinical_trials_does_not_filter_by_recruitment_status():
    fake = FakeTransport([ct_page([])])
    with tempfile.TemporaryDirectory() as tmp:
        run_with(tmp, fake, only=["clinicaltrials-gov"])
    params = fake.calls[0]["params"]
    query = params["query.term"].lower()
    assert "recruit" not in query and "overallstatus" not in query


# ---------------------------------------------------------------------------
# PubMed history + ESummary
# ---------------------------------------------------------------------------

def test_pubmed_requires_contact_email_and_never_uses_git_email():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=True):
            result = runner.run_search(CONTRACT, only=["pubmed"], run_id="run-001",
                                       transport=FakeTransport([]))
        source = result["sources"]["pubmed"]
        assert source["status"] == "blocked"
        assert "AHIG_CONTACT_EMAIL" in source["error"]


def test_pubmed_uses_history_then_pages_esummary():
    fake = FakeTransport([pubmed_initial(2), pubmed_summary(["11", "22"])])
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp,
                                     "AHIG_CONTACT_EMAIL": "owner@example.com"}, clear=True):
            result = runner.run_search(CONTRACT, only=["pubmed"], run_id="run-001",
                                       transport=fake)
        source = result["sources"]["pubmed"]
        assert source["status"] == "completed" and source["recordCount"] == 2
        assert fake.calls[0]["url"].endswith("esearch.fcgi")
        assert fake.calls[0]["params"]["usehistory"] == "y"
        assert fake.calls[1]["url"].endswith("esummary.fcgi")
        assert fake.calls[1]["params"]["WebEnv"] == "TEST-WEBENV"
        assert fake.calls[1]["params"]["query_key"] == "1"
        assert fake.calls[0]["params"]["email"] == "owner@example.com"


# ---------------------------------------------------------------------------
# OpenAlex credential and pagination
# ---------------------------------------------------------------------------

def test_openalex_without_api_key_is_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=True):
            result = runner.run_search(CONTRACT, only=["openalex"], run_id="run-001",
                                       transport=FakeTransport([]))
        assert result["sources"]["openalex"]["status"] == "blocked"
        assert "OPENALEX_API_KEY" in result["sources"]["openalex"]["error"]


def test_openalex_polite_pool_mailto_when_no_api_key():
    """無金鑰時走官方 polite pool：帶 mailto、不帶 api_key、記錄模式。"""
    fake = FakeTransport([
        {"meta": {"next_cursor": None, "count": 1}, "results": [{"id": "W1"}]},
    ])
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp,
                                     "AHIG_CONTACT_EMAIL": "me@example.test"},
                        clear=True):
            result = runner.run_search(CONTRACT, only=["openalex"],
                                       run_id="run-001", transport=fake)
        source = result["sources"]["openalex"]
        assert source["recordCount"] == 1
        assert source["accessMode"] == "polite-pool-mailto"
        assert fake.calls[0]["params"]["mailto"] == "me@example.test"
        assert "api_key" not in fake.calls[0]["params"]


def test_openalex_follows_next_cursor_with_api_key():
    fake = FakeTransport([
        {"meta": {"next_cursor": "c2", "count": 2}, "results": [{"id": "W1"}]},
        {"meta": {"next_cursor": None, "count": 2}, "results": [{"id": "W2"}]},
    ])
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp,
                                     "OPENALEX_API_KEY": "test-key"}, clear=True):
            result = runner.run_search(CONTRACT, only=["openalex"], run_id="run-001",
                                       transport=fake)
        assert result["sources"]["openalex"]["recordCount"] == 2
        assert fake.calls[0]["params"]["api_key"] == "test-key"
        assert fake.calls[1]["params"]["cursor"] == "c2"


# ---------------------------------------------------------------------------
# manifest、續跑與 redo
# ---------------------------------------------------------------------------

def test_manifest_records_contract_hash_source_counts_and_timestamps():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, FakeTransport([epmc_page(["A"])]),
                          only=["europe-pmc"])
        manifest = json.loads((Path(result["runRoot"]) / "manifest.json").read_text(
            encoding="utf-8"))
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        assert manifest["searchContractHash"] == contract["contractHash"]
        assert manifest["sources"]["europe-pmc"]["recordCount"] == 1
        assert manifest["startedAt"] and manifest["finishedAt"]


def test_request_manifest_retains_url_params_and_response_path():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, FakeTransport([epmc_page(["A"])]),
                          only=["europe-pmc"])
        request_manifest = json.loads(
            (Path(result["runRoot"]) / "sources" / "europe-pmc"
             / "requests.json").read_text(encoding="utf-8"))
        assert request_manifest[0]["url"].startswith("https://")
        assert request_manifest[0]["params"]["query"]
        assert request_manifest[0]["requestedAt"]
        assert request_manifest[0]["responsePath"].endswith("000001.json")


def test_completed_source_is_skipped_on_resume():
    with tempfile.TemporaryDirectory() as tmp:
        first = run_with(tmp, FakeTransport([epmc_page(["A"])]),
                         only=["europe-pmc"])
        second_fake = FakeTransport([])
        second = run_with(tmp, second_fake, only=["europe-pmc"])
        assert second["sources"]["europe-pmc"]["status"] == "completed"
        assert second_fake.calls == []
        assert first["runRoot"] == second["runRoot"]


def test_redo_reexecutes_completed_source_and_replaces_old_source_dir():
    with tempfile.TemporaryDirectory() as tmp:
        first = run_with(tmp, FakeTransport([epmc_page(["A"])]),
                         only=["europe-pmc"])
        second_fake = FakeTransport([epmc_page(["B", "C"])])
        second = run_with(tmp, second_fake, only=["europe-pmc"], redo=True)
        assert second["sources"]["europe-pmc"]["recordCount"] == 2
        response_files = list((Path(first["runRoot"]) / "sources" / "europe-pmc"
                               / "responses").glob("*.json"))
        assert len(response_files) == 1


def test_network_failure_marks_source_failed_and_keeps_prior_raw_pages():
    fake = FakeTransport([epmc_page(["A"], next_cursor="c2", hit_count=2),
                          RuntimeError("network down")])
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, fake, only=["europe-pmc"])
        source = result["sources"]["europe-pmc"]
        assert source["status"] == "failed"
        raw = list((Path(result["runRoot"]) / "sources" / "europe-pmc"
                    / "responses").glob("*.json"))
        assert len(raw) == 1


def test_mixed_success_and_blocked_sources_make_run_partial():
    fake = FakeTransport([epmc_page(["A"])])
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=True):
            result = runner.run_search(CONTRACT, only=["europe-pmc", "pubmed"],
                                       run_id="run-001", transport=fake)
        assert result["status"] == "partial"
        assert result["sources"]["europe-pmc"]["status"] == "completed"
        assert result["sources"]["pubmed"]["status"] == "blocked"


def test_single_successful_source_does_not_make_the_whole_run_completed():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, FakeTransport([epmc_page(["A"])]),
                          only=["europe-pmc"])
        assert result["status"] == "partial"
        assert result["sources"]["pubmed"]["status"] == "not-run"
        assert result["sources"]["openalex"]["status"] == "not-run"
        assert result["sources"]["clinicaltrials-gov"]["status"] == "not-run"


def test_unknown_only_source_is_rejected_before_writing():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
            try:
                runner.run_search(CONTRACT, only=["does-not-exist"], run_id="x",
                                  transport=FakeTransport([]))
            except ValueError as exc:
                assert "does-not-exist" in str(exc)
                return
    raise AssertionError("未知 sourceId 應被拒絕")


def test_only_accepts_candidate_sources_not_access_resolvers():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
            try:
                runner.run_search(CONTRACT, only=["unpaywall"], run_id="x",
                                  transport=FakeTransport([]))
            except ValueError as exc:
                assert "candidate" in str(exc).lower() or "候選" in str(exc)
                return
    raise AssertionError("metadata runner 不得執行 access resolver")


def test_runner_never_calls_fulltext_or_access_resolver_endpoints():
    fake = FakeTransport([epmc_page([])])
    with tempfile.TemporaryDirectory() as tmp:
        run_with(tmp, fake, only=["europe-pmc"])
    assert all("unpaywall" not in c["url"] and "oa.fcgi" not in c["url"]
               and "fulltext" not in c["url"].lower() for c in fake.calls)


def test_run_id_rejects_path_traversal_before_writing():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
            for bad in ("../escape", "..", "a/b", "a\\b"):
                try:
                    runner.run_search(CONTRACT, only=["europe-pmc"], run_id=bad,
                                      transport=FakeTransport([]))
                except ValueError:
                    continue
                raise AssertionError(f"不安全的 run-id 未被拒絕：{bad}")
        assert not (Path(tmp).parent / "escape").exists()


def test_separate_only_invocations_preserve_prior_source_in_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        run_with(tmp, FakeTransport([epmc_page(["A"])]), only=["europe-pmc"])
        second = run_with(tmp, FakeTransport([ct_page(["NCT1"])]),
                          only=["clinicaltrials-gov"])
        assert set(second["sources"]) == {
            "pubmed", "europe-pmc", "openalex", "clinicaltrials-gov"}
        assert second["sources"]["europe-pmc"]["recordCount"] == 1
        assert second["sources"]["clinicaltrials-gov"]["recordCount"] == 1
        assert second["sources"]["pubmed"]["status"] == "not-run"


def test_retry_after_failed_attempt_archives_prior_raw_evidence():
    first_fake = FakeTransport([
        epmc_page(["A"], next_cursor="c2", hit_count=2),
        RuntimeError("network down"),
    ])
    with tempfile.TemporaryDirectory() as tmp:
        first = run_with(tmp, first_fake, only=["europe-pmc"])
        assert first["sources"]["europe-pmc"]["status"] == "failed"
        second = run_with(tmp, FakeTransport([epmc_page(["B", "C"])]),
                          only=["europe-pmc"])
        assert second["sources"]["europe-pmc"]["status"] == "completed"
        archived = list((Path(second["runRoot"]) / "previous-attempts").glob(
            "europe-pmc-*"))
        assert len(archived) == 1
        assert list((archived[0] / "responses").glob("*.json")), \
            "失敗嘗試的 raw response 不得被靜默覆蓋"


def test_same_run_id_refuses_a_different_contract_hash():
    with tempfile.TemporaryDirectory() as tmp:
        first = run_with(tmp, FakeTransport([epmc_page([])]), only=["europe-pmc"])
        state_path = Path(first["runRoot"]) / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["searchContractHash"] = "sha256:" + "f" * 64
        state_path.write_text(json.dumps(state), encoding="utf-8")
        try:
            run_with(tmp, FakeTransport([]), only=["europe-pmc"])
        except ValueError as exc:
            assert "contract" in str(exc).lower() or "契約" in str(exc)
            return
    raise AssertionError("同一 run-id 不得混入不同 SearchContract hash")


def test_declared_total_mismatch_marks_source_failed():
    """API 宣告 10 筆但 cursor 提前結束，不得把殘缺集合標 completed。"""
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, FakeTransport([epmc_page(["A"], hit_count=10)]),
                          only=["europe-pmc"])
        source = result["sources"]["europe-pmc"]
        assert source["status"] == "failed"
        assert "incomplete" in source["error"].lower()


def test_raw_exchange_is_written_byte_for_byte_with_checksum_and_headers():
    class RawFake(FakeTransport):
        def __init__(self):
            super().__init__([epmc_page(["A"])])
            self.raw = b'{"hitCount":1,"resultList":{"result":[{"id":"A"}]}}'
            self.last_exchange = None

        def get_json(self, *, url: str, params: dict,
                     headers: dict | None = None) -> dict:
            value = super().get_json(url=url, params=params, headers=headers)
            self.last_exchange = {
                "body": self.raw,
                "status": 200,
                "headers": {"Content-Type": "application/json", "ETag": "abc"},
                "finalUrl": "https://example.test/search?api_key=secret&email=me%40x.test",
                "contentType": "application/json",
            }
            return value

    fake = RawFake()
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, fake, only=["europe-pmc"])
        source_root = Path(result["runRoot"]) / "sources" / "europe-pmc"
        req = json.loads((source_root / "requests.json").read_text(encoding="utf-8"))[0]
        raw_path = source_root / req["responsePath"]
        assert raw_path.read_bytes() == fake.raw
        assert req["responseKind"] == "raw-http-body"
        assert req["httpStatus"] == 200 and req["headers"]["ETag"] == "abc"
        assert req["sha256"] == "sha256:" + __import__("hashlib").sha256(fake.raw).hexdigest()
        assert "secret" not in req["finalUrl"] and "me%40x.test" not in req["finalUrl"]
        assert "%3Credacted%3E" in req["finalUrl"]


def test_api_key_and_email_are_absent_from_request_manifest():
    fake = FakeTransport([pubmed_initial(0)])
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp,
                                     "AHIG_CONTACT_EMAIL": "secret@example.com"}, clear=True):
            result = runner.run_search(CONTRACT, only=["pubmed"], run_id="run-001",
                                       transport=fake)
        req_text = (Path(result["runRoot"]) / "sources" / "pubmed"
                    / "requests.json").read_text(encoding="utf-8")
        assert "secret@example.com" not in req_text
        assert "AHIG_CONTACT_EMAIL" in req_text


def test_boolean_query_params_are_serialised_lowercase():
    fake = FakeTransport([ct_page([])])
    with tempfile.TemporaryDirectory() as tmp:
        run_with(tmp, fake, only=["clinicaltrials-gov"])
    assert fake.calls[0]["params"]["countTotal"] == "true"
    assert all(value not in {True, False} for value in fake.calls[0]["params"].values())


def test_http_error_exchange_is_retained_before_source_fails():
    class ErrorTransport(FakeTransport):
        def __init__(self):
            super().__init__([])
            self.last_exchange = None
            self.raw = b'{"error":"bad query"}'

        def get_json(self, *, url: str, params: dict,
                     headers: dict | None = None) -> dict:
            self.calls.append({"url": url, "params": dict(params),
                               "headers": dict(headers or {})})
            self.last_exchange = {
                "body": self.raw,
                "status": 400,
                "headers": {"Content-Type": "application/json"},
                "finalUrl": "https://example.test?api_key=secret",
                "contentType": "application/json",
            }
            raise RuntimeError("HTTP 400")

    fake = ErrorTransport()
    with tempfile.TemporaryDirectory() as tmp:
        result = run_with(tmp, fake, only=["clinicaltrials-gov"])
        source_root = Path(result["runRoot"]) / "sources" / "clinicaltrials-gov"
        req = json.loads((source_root / "requests.json").read_text(encoding="utf-8"))[0]
        assert result["sources"]["clinicaltrials-gov"]["status"] == "failed"
        assert (source_root / req["responsePath"]).read_bytes() == fake.raw
        assert req["httpStatus"] == 400
        assert "secret" not in req["finalUrl"]
