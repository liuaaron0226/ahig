"""候選池正規化與確定性去重。

核心安全邊界：

- DOI / PMID / PMCID 只在 publication 內作 exact merge。
- registry ID 只在 registry-record 內作 exact merge。
- 相同標題、作者、年份只能建立 ambiguity bucket，絕不自動 merge。
- registry record 與 publication 即使提到同一 NCT，也屬不同 report/entity；關係留給
  StudyFamily，不在 dedup 階段消失。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ahig.search import candidates


def epmc(*, source="MED", native_id="1", doi=None, pmid=None, pmcid=None,
         title="Carbohydrate and exercise.", author="Smith J", year="2020",
         abstract="Abstract", publication_types=None) -> dict:
    value = {
        "source": source, "id": native_id, "title": title,
        "authorString": author, "pubYear": year, "abstractText": abstract,
        "firstPublicationDate": f"{year}-01-01",
    }
    if publication_types is not None:
        value["pubTypeList"] = {"pubType": publication_types}
    for key, item in (("doi", doi), ("pmid", pmid), ("pmcid", pmcid)):
        if item is not None:
            value[key] = item
    return value


def ct(*, nct="NCT00000001", title="Carbohydrate and exercise",
       official=None, status="COMPLETED") -> dict:
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": nct, "briefTitle": title,
                "officialTitle": official or title,
            },
            "statusModule": {"overallStatus": status,
                             "studyFirstPostDateStruct": {"date": "2020-01-01"}},
            "descriptionModule": {"briefSummary": "Trial summary"},
            "designModule": {"studyType": "INTERVENTIONAL",
                             "enrollmentInfo": {"count": 20}},
            "conditionsModule": {"conditions": ["Exercise"]},
        },
        "derivedSection": {"miscInfoModule": {"versionHolder": "2026-08-13"}},
        "hasResults": False,
    }


def build(records_by_source: dict[str, list[dict]]):
    return candidates.build_candidate_pool(records_by_source,
                                           search_contract_hash="sha256:" + "a" * 64,
                                           run_id="test-run")


# ---------------------------------------------------------------------------
# normalisers
# ---------------------------------------------------------------------------

def test_normalise_doi_strips_resolver_prefix_and_terminal_punctuation():
    assert candidates.normalise_doi(" HTTPS://doi.org/10.1000/ABC.1. ") == "10.1000/abc.1"
    assert candidates.normalise_doi("doi:10.1000/X(Y)") == "10.1000/x(y)"
    assert candidates.normalise_doi("not-a-doi") is None


def test_normalise_pmid_and_pmcid_are_strict():
    assert candidates.normalise_pmid(" 12345 ") == "12345"
    assert candidates.normalise_pmid("PMID:12345") == "12345"
    assert candidates.normalise_pmid("12x") is None
    assert candidates.normalise_pmcid("pmc12345") == "PMC12345"
    assert candidates.normalise_pmcid("12345") is None


def test_title_normalisation_is_conservative():
    assert (candidates.normalise_title("  Carbohydrate—Exercise!  ")
            == "carbohydrate—exercise")
    # 中間標點保留，避免過度正規化把不同標題揉在一起。
    assert candidates.normalise_title("A: B") != candidates.normalise_title("A B")


# ---------------------------------------------------------------------------
# exact merge
# ---------------------------------------------------------------------------

def test_same_doi_merges_publication_representations():
    pool = build({"europe-pmc": [
        epmc(native_id="MED1", doi="10.1000/X", pmid="1"),
        epmc(source="PMC", native_id="PMC1", doi="https://doi.org/10.1000/x",
             pmcid="PMC1"),
    ]})
    assert pool["manifest"]["inputRecordCount"] == 2
    assert pool["manifest"]["candidateCount"] == 1
    c = pool["candidates"][0]
    assert len(c["members"]) == 2
    assert c["identifiers"] == {"doi": ["10.1000/x"], "pmid": ["1"],
                                "pmcid": ["PMC1"], "registryId": []}


def test_same_pmid_merges_even_when_one_record_lacks_doi():
    pool = build({"europe-pmc": [
        epmc(native_id="A", pmid="123", doi="10.1000/x"),
        epmc(native_id="B", pmid="123"),
    ]})
    assert pool["manifest"]["candidateCount"] == 1


def test_same_pmcid_merges_publication_records():
    pool = build({"europe-pmc": [
        epmc(source="PMC", native_id="A", pmcid="PMC123"),
        epmc(source="MED", native_id="B", pmcid="pmc123"),
    ]})
    assert pool["manifest"]["candidateCount"] == 1


def test_same_registry_id_merges_registry_records():
    pool = build({"clinicaltrials-gov": [ct(), ct()]})
    assert pool["manifest"]["candidateCount"] == 1
    assert pool["candidates"][0]["entityKind"] == "registry-record"


def test_transitive_exact_ids_merge_and_identifier_conflict_is_exposed():
    """A/B 同 DOI，B/C 同 PMID；C 的另一 DOI 不能被靜默藏起來。"""
    pool = build({"europe-pmc": [
        epmc(native_id="A", doi="10.1000/x", pmid="1"),
        epmc(native_id="B", doi="10.1000/x", pmid="2"),
        epmc(native_id="C", doi="10.1000/y", pmid="2"),
    ]})
    assert pool["manifest"]["candidateCount"] == 1
    assert len(pool["identifierConflicts"]) == 1
    conflict = pool["identifierConflicts"][0]
    assert conflict["distinctValues"]["doi"] == ["10.1000/x", "10.1000/y"]
    assert conflict["distinctValues"]["pmid"] == ["1", "2"]


# ---------------------------------------------------------------------------
# never merge on title / family signal
# ---------------------------------------------------------------------------

def test_same_title_without_exact_id_does_not_merge():
    pool = build({"europe-pmc": [
        epmc(native_id="A", title="Same title", author="Smith J", year="2020"),
        epmc(native_id="B", title="Same title.", author="Smith J", year="2020"),
    ]})
    assert pool["manifest"]["candidateCount"] == 2
    assert len(pool["titleAmbiguities"]) == 1
    assert len(pool["titleAmbiguities"][0]["candidateIds"]) == 2


def test_same_title_with_different_year_is_still_only_ambiguity():
    pool = build({"europe-pmc": [
        epmc(native_id="A", title="Same title", year="2020"),
        epmc(native_id="B", title="Same title", year="2021"),
    ]})
    assert pool["manifest"]["candidateCount"] == 2
    assert pool["titleAmbiguities"]


def test_registry_and_publication_never_merge_on_shared_title_or_nct_text():
    pool = build({
        "europe-pmc": [epmc(native_id="P", title="Shared trial",
                            abstract="Registered as NCT00000001")],
        "clinicaltrials-gov": [ct(nct="NCT00000001", title="Shared trial")],
    })
    assert pool["manifest"]["candidateCount"] == 2
    assert {c["entityKind"] for c in pool["candidates"]} == {
        "publication", "registry-record"}
    # Registry/publication linkage is StudyFamily work, not title dedup.
    assert all(len(b["entityKinds"]) == 1 for b in pool["titleAmbiguities"])


# ---------------------------------------------------------------------------
# stable output and provenance
# ---------------------------------------------------------------------------

def test_candidate_ids_are_order_independent():
    a = epmc(native_id="A", doi="10.1000/x", pmid="1")
    b = epmc(native_id="B", doi="10.1000/x", pmcid="PMC1")
    one = build({"europe-pmc": [a, b]})["candidates"][0]["candidateId"]
    two = build({"europe-pmc": [b, a]})["candidates"][0]["candidateId"]
    assert one == two


def test_candidate_id_uses_entity_kind_and_canonical_identity():
    pool = build({"europe-pmc": [epmc(doi="10.1000/x")]})
    c = pool["candidates"][0]
    assert c["candidateId"].startswith("ahig:candidate:publication:")
    assert c["canonicalIdentity"] == "doi:10.1000/x"


def test_member_provenance_includes_source_native_id_and_index():
    pool = build({"europe-pmc": [epmc(native_id="A", doi="10.1000/x")]})
    m = pool["candidates"][0]["members"][0]
    assert m["sourceId"] == "europe-pmc"
    assert m["sourceNativeId"] == "MED:A"
    assert m["sourceRecordIndex"] == 0


def test_manifest_counts_exact_collapses_and_missing_global_ids():
    pool = build({"europe-pmc": [
        epmc(native_id="A", doi="10.1000/x"),
        epmc(native_id="B", doi="10.1000/x"),
        epmc(native_id="C"),
    ]})
    m = pool["manifest"]
    assert m["inputRecordCount"] == 3
    assert m["candidateCount"] == 2
    assert m["recordsCollapsedByExactId"] == 1
    assert m["candidatesWithoutGlobalIdentifier"] == 1


def test_preferred_publication_metadata_uses_nonempty_values_deterministically():
    pool = build({"europe-pmc": [
        epmc(native_id="B", doi="10.1000/x", title="Short", abstract=""),
        epmc(native_id="A", doi="10.1000/x", title="Longer title", abstract="Full abstract"),
    ]})
    c = pool["candidates"][0]
    assert c["title"] == "Longer title"
    assert c["abstract"] == "Full abstract"


def test_publication_types_are_preserved_and_merged_deterministically():
    pool = build({"europe-pmc": [
        epmc(native_id="B", doi="10.1000/x", publication_types=["Review"]),
        epmc(native_id="A", doi="10.1000/x",
             publication_types=["Journal Article", "Review"]),
    ]})
    assert pool["candidates"][0]["publicationTypes"] == ["Journal Article", "Review"]


def test_registry_record_has_explicit_publication_type():
    pool = build({"clinicaltrials-gov": [ct()]})
    assert pool["candidates"][0]["publicationTypes"] == [
        "Clinical Trial Registry Record"]


# ---------------------------------------------------------------------------
# live-run filesystem integration (synthetic files)
# ---------------------------------------------------------------------------

def make_run_root(tmp: str) -> Path:
    root = Path(tmp) / "run"
    for sid, rows in {
        "europe-pmc": [epmc(native_id="A", doi="10.1000/x")],
        "clinicaltrials-gov": [ct()],
    }.items():
        d = root / "sources" / sid
        d.mkdir(parents=True)
        (d / "records.json").write_text(json.dumps(rows), encoding="utf-8")
        (d / "status.json").write_text(json.dumps({
            "sourceId": sid, "status": "completed", "recordCount": len(rows),
        }), encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({
        "runId": "r1", "searchContractHash": "sha256:" + "a" * 64,
        "sources": {
            "europe-pmc": {"status": "completed", "recordCount": 1},
            "clinicaltrials-gov": {"status": "completed", "recordCount": 1},
        },
    }), encoding="utf-8")
    return root


def test_build_from_run_root_writes_atomic_private_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        result = candidates.build_from_run_root(root)
        out = root / "candidate-pool"
        assert result["candidateCount"] == 2
        for name in ("manifest.json", "candidates.json", "title-ambiguities.json",
                     "identifier-conflicts.json"):
            assert (out / name).is_file(), name
        assert not list(out.glob("*.tmp"))


def test_build_from_run_root_rejects_source_count_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        status = root / "sources" / "europe-pmc" / "status.json"
        data = json.loads(status.read_text(encoding="utf-8"))
        data["recordCount"] = 99
        status.write_text(json.dumps(data), encoding="utf-8")
        try:
            candidates.build_from_run_root(root)
        except ValueError as exc:
            assert "count" in str(exc).lower() or "筆數" in str(exc)
            return
    raise AssertionError("來源 status 與 records 筆數不符必須拒絕")


def test_failed_or_not_run_sources_are_declared_not_silently_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        manifest = root / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["sources"]["pubmed"] = {"status": "not-run", "recordCount": 0}
        manifest.write_text(json.dumps(data), encoding="utf-8")
        result = candidates.build_from_run_root(root)
        assert result["sourceCoverage"]["pubmed"] == "not-run"
        assert result["completeAcrossContractSources"] is False


def test_dry_run_computes_counts_without_writing_candidate_pool():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        result = candidates.build_from_run_root(root, dry_run=True)
        assert result["candidateCount"] == 2
        assert not (root / "candidate-pool").exists()


def test_existing_pool_requires_redo():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_run_root(tmp)
        candidates.build_from_run_root(root)
        try:
            candidates.build_from_run_root(root)
        except FileExistsError:
            pass
        else:
            raise AssertionError("已有 candidate-pool 時必須要求 --redo")
        candidates.build_from_run_root(root, redo=True)
