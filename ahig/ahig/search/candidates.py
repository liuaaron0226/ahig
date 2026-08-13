#!/usr/bin/env python3
"""把來源 metadata 正規化為候選 publication / registry-record pool。

這不是 StudyFamily resolver。publication 的 DOI/PMID/PMCID exact identity 只用來合併
同一 publication 的多個資料庫 representation；registry record 以 registry ID 合併。
publication 與 registry record 永遠不跨 kind 合併，title-only 永遠只產生 ambiguity。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Iterable

from ahig.state import atomic_write_json

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
_PMID_RE = re.compile(r"^\d+$")
_PMCID_RE = re.compile(r"^PMC\d+$", re.I)
_NCT_RE = re.compile(r"^NCT\d{8}$", re.I)


def normalise_doi(raw: Any) -> str | None:
    if not raw:
        return None
    value = unicodedata.normalize("NFKC", str(raw)).strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value,
                   flags=re.I)
    value = value.rstrip(".,;:")
    return value if _DOI_RE.fullmatch(value) else None


def normalise_pmid(raw: Any) -> str | None:
    if not raw:
        return None
    value = re.sub(r"^PMID:\s*", "", str(raw).strip(), flags=re.I)
    return value if _PMID_RE.fullmatch(value) else None


def normalise_pmcid(raw: Any) -> str | None:
    if not raw:
        return None
    value = str(raw).strip().upper()
    return value if _PMCID_RE.fullmatch(value) else None


def normalise_registry_id(raw: Any) -> str | None:
    if not raw:
        return None
    value = re.sub(r"\s+", "", str(raw)).upper()
    return value if _NCT_RE.fullmatch(value) else None


def normalise_title(raw: Any) -> str:
    value = unicodedata.normalize("NFKC", str(raw or ""))
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value.rstrip(" .,!?:;")


def _first_author(author_string: Any) -> str | None:
    if not author_string:
        return None
    value = str(author_string).split(",", 1)[0].strip()
    return value or None


def _nested(value: dict, *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _publication(record: dict, source_index: int) -> dict:
    source = str(record.get("source") or "UNKNOWN").upper()
    native = str(record.get("id") or record.get("pmid") or record.get("pmcid")
                 or source_index)
    doi = normalise_doi(record.get("doi"))
    pmid = normalise_pmid(record.get("pmid"))
    pmcid = normalise_pmcid(record.get("pmcid"))
    title = str(record.get("title") or "").strip()
    return {
        "entityKind": "publication",
        "sourceId": "europe-pmc",
        "sourceNativeId": f"{source}:{native}",
        "sourceRecordIndex": source_index,
        "identifiers": {"doi": doi, "pmid": pmid, "pmcid": pmcid,
                        "registryId": None},
        "title": title,
        "normalisedTitle": normalise_title(title),
        "abstract": str(record.get("abstractText") or "").strip() or None,
        "authorString": str(record.get("authorString") or "").strip() or None,
        "firstAuthor": _first_author(record.get("authorString")),
        "publicationYear": (int(record["pubYear"])
                            if str(record.get("pubYear") or "").isdigit() else None),
        "publicationDate": record.get("firstPublicationDate"),
        "publicationStatus": record.get("publicationStatus"),
        "publicationTypes": sorted(set(
            (record.get("pubTypeList") or {}).get("pubType") or [])),
        "language": record.get("language"),
        "isOpenAccess": record.get("isOpenAccess"),
        "license": record.get("license"),
        "isPreprint": source == "PPR",
    }


def _registry(record: dict, source_index: int) -> dict:
    nct = normalise_registry_id(
        _nested(record, "protocolSection", "identificationModule", "nctId"))
    ident = _nested(record, "protocolSection", "identificationModule") or {}
    status = _nested(record, "protocolSection", "statusModule") or {}
    design = _nested(record, "protocolSection", "designModule") or {}
    description = _nested(record, "protocolSection", "descriptionModule") or {}
    title = str(ident.get("officialTitle") or ident.get("briefTitle") or "").strip()
    return {
        "entityKind": "registry-record",
        "sourceId": "clinicaltrials-gov",
        "sourceNativeId": nct or f"clinicaltrials-gov:{source_index}",
        "sourceRecordIndex": source_index,
        "identifiers": {"doi": None, "pmid": None, "pmcid": None,
                        "registryId": nct},
        "title": title,
        "normalisedTitle": normalise_title(title),
        "abstract": str(description.get("briefSummary") or "").strip() or None,
        "authorString": None,
        "firstAuthor": None,
        "publicationYear": None,
        "publicationDate": _nested(status, "studyFirstPostDateStruct", "date"),
        "publicationStatus": status.get("overallStatus"),
        "publicationTypes": ["Clinical Trial Registry Record"],
        "language": None,
        "isOpenAccess": None,
        "license": None,
        "isPreprint": False,
        "studyType": design.get("studyType"),
        "enrollmentCount": _nested(design, "enrollmentInfo", "count"),
        "hasResults": bool(record.get("hasResults")),
        "registryVersionHolder": _nested(record, "derivedSection", "miscInfoModule",
                                         "versionHolder"),
    }


def normalise_records(records_by_source: dict[str, list[dict]]) -> list[dict]:
    out: list[dict] = []
    for source_id, records in records_by_source.items():
        if source_id == "europe-pmc":
            out.extend(_publication(record, i) for i, record in enumerate(records))
        elif source_id == "clinicaltrials-gov":
            out.extend(_registry(record, i) for i, record in enumerate(records))
        else:
            raise ValueError(f"尚未支援的候選來源：{source_id}")
    return out


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[self.parent[index]]
            index = self.parent[index]
        return index

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _exact_components(records: list[dict]) -> list[list[dict]]:
    uf = _UnionFind(len(records))
    seen: dict[tuple[str, str, str], int] = {}
    for i, record in enumerate(records):
        kind = record["entityKind"]
        for key in ("doi", "pmid", "pmcid", "registryId"):
            value = record["identifiers"].get(key)
            if not value:
                continue
            # publication 與 registry-record 的 identity 空間分離。
            identity = (kind, key, value)
            if identity in seen:
                uf.union(i, seen[identity])
            else:
                seen[identity] = i
    groups: dict[int, list[dict]] = {}
    for i, record in enumerate(records):
        groups.setdefault(uf.find(i), []).append(record)
    return list(groups.values())


def _choose_text(members: list[dict], key: str) -> Any:
    values = {str(member.get(key)).strip() for member in members
              if member.get(key) not in (None, "")}
    if not values:
        return None
    # 最資訊豐富（長）優先；同長度以字典序確定性解 tie。
    return sorted(values, key=lambda v: (-len(v), v))[0]


def _id_values(members: list[dict], key: str) -> list[str]:
    return sorted({m["identifiers"][key] for m in members
                   if m["identifiers"].get(key)})


def _canonical_identity(kind: str, identifiers: dict[str, list[str]],
                        members: list[dict]) -> str:
    precedence = (("doi", "doi"), ("pmid", "pmid"), ("pmcid", "pmcid"),
                  ("registryId", "registry"))
    for key, label in precedence:
        if identifiers[key]:
            return f"{label}:{identifiers[key][0]}"
    member_keys = sorted(f"{m['sourceId']}:{m['sourceNativeId']}" for m in members)
    digest = hashlib.sha256("\n".join(member_keys).encode("utf-8")).hexdigest()
    return f"source-members-sha256:{digest}"


def _candidate(component: list[dict]) -> dict:
    members = sorted(component, key=lambda m: (m["sourceId"], m["sourceNativeId"],
                                                m["sourceRecordIndex"]))
    kind = members[0]["entityKind"]
    identifiers = {key: _id_values(members, key)
                   for key in ("doi", "pmid", "pmcid", "registryId")}
    identity = _canonical_identity(kind, identifiers, members)
    digest = hashlib.sha256(f"{kind}\n{identity}".encode("utf-8")).hexdigest()[:24]
    return {
        "candidateId": f"ahig:candidate:{kind}:{digest}",
        "entityKind": kind,
        "canonicalIdentity": identity,
        "identifiers": identifiers,
        "title": _choose_text(members, "title"),
        "normalisedTitle": _choose_text(members, "normalisedTitle"),
        "abstract": _choose_text(members, "abstract"),
        "authorString": _choose_text(members, "authorString"),
        "firstAuthor": _choose_text(members, "firstAuthor"),
        "publicationYear": min((m["publicationYear"] for m in members
                                if m.get("publicationYear") is not None), default=None),
        "publicationDate": min((m["publicationDate"] for m in members
                                if m.get("publicationDate")), default=None),
        "publicationStatus": _choose_text(members, "publicationStatus"),
        "publicationTypes": sorted({
            item for member in members for item in (member.get("publicationTypes") or [])}),
        "isPreprint": any(bool(m.get("isPreprint")) for m in members),
        "isOpenAccess": any(m.get("isOpenAccess") == "Y"
                            or m.get("isOpenAccess") is True for m in members),
        "members": [{key: m[key] for key in
                     ("sourceId", "sourceNativeId", "sourceRecordIndex")}
                    for m in members],
    }


def _identifier_conflicts(candidate_list: list[dict]) -> list[dict]:
    conflicts = []
    for candidate in candidate_list:
        distinct = {key: values for key, values in candidate["identifiers"].items()
                    if len(values) > 1}
        if distinct:
            conflicts.append({"candidateId": candidate["candidateId"],
                              "distinctValues": distinct,
                              "memberCount": len(candidate["members"]),
                              "action": "human-review"})
    return conflicts


def _title_ambiguities(candidate_list: list[dict]) -> list[dict]:
    buckets: dict[tuple[str, str], list[dict]] = {}
    for candidate in candidate_list:
        title = candidate.get("normalisedTitle") or ""
        if title:
            buckets.setdefault((candidate["entityKind"], title), []).append(candidate)
    result = []
    for (kind, title), values in buckets.items():
        if len(values) <= 1:
            continue
        result.append({
            "normalisedTitle": title,
            "entityKinds": [kind],
            "candidateIds": sorted(v["candidateId"] for v in values),
            "years": sorted({v["publicationYear"] for v in values
                             if v.get("publicationYear") is not None}),
            "action": "human-review-never-auto-merge",
        })
    return sorted(result, key=lambda b: (b["normalisedTitle"], b["candidateIds"]))


def build_candidate_pool(records_by_source: dict[str, list[dict]], *,
                         search_contract_hash: str, run_id: str) -> dict:
    records = normalise_records(records_by_source)
    components = _exact_components(records)
    candidate_list = sorted((_candidate(component) for component in components),
                            key=lambda c: c["candidateId"])
    conflicts = _identifier_conflicts(candidate_list)
    ambiguities = _title_ambiguities(candidate_list)
    without_global = sum(
        not any(c["identifiers"][key] for key in
                ("doi", "pmid", "pmcid", "registryId"))
        for c in candidate_list)
    manifest = {
        "runId": run_id,
        "searchContractHash": search_contract_hash,
        "inputRecordCount": len(records),
        "inputRecordCountBySource": {
            source: len(rows) for source, rows in sorted(records_by_source.items())},
        "candidateCount": len(candidate_list),
        "candidateCountByKind": {
            kind: sum(c["entityKind"] == kind for c in candidate_list)
            for kind in ("publication", "registry-record")},
        "recordsCollapsedByExactId": len(records) - len(candidate_list),
        "candidatesWithoutGlobalIdentifier": without_global,
        "identifierConflictCount": len(conflicts),
        "titleAmbiguityBucketCount": len(ambiguities),
        "deduplicationRule": "exact-identifiers-only-within-entity-kind",
        "titleOnlyAutoMerge": False,
    }
    return {"manifest": manifest, "candidates": candidate_list,
            "identifierConflicts": conflicts, "titleAmbiguities": ambiguities}


def build_from_run_root(run_root: Path, *, dry_run: bool = False,
                        redo: bool = False) -> dict:
    run_root = Path(run_root).resolve()
    manifest_path = run_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"缺少搜尋 manifest：{manifest_path}")
    search_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records_by_source: dict[str, list[dict]] = {}
    source_coverage = {sid: value.get("status", "unknown")
                       for sid, value in search_manifest.get("sources", {}).items()}

    for sid, status in search_manifest.get("sources", {}).items():
        if status.get("status") != "completed":
            continue
        source_root = run_root / "sources" / sid
        path = source_root / "records.json"
        status_path = source_root / "status.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        source_status = json.loads(status_path.read_text(encoding="utf-8"))
        counts = {"records": len(rows),
                  "sourceStatus": source_status.get("recordCount"),
                  "runManifest": status.get("recordCount")}
        if len(set(counts.values())) != 1:
            raise ValueError(f"{sid} 筆數三方不一致：{counts}")
        if source_status.get("status") != "completed":
            raise ValueError(
                f"run manifest 說 {sid}=completed，但 source status 是 "
                f"{source_status.get('status')}")
        if sid in {"europe-pmc", "clinicaltrials-gov"}:
            records_by_source[sid] = rows

    built = build_candidate_pool(
        records_by_source,
        search_contract_hash=search_manifest["searchContractHash"],
        run_id=search_manifest["runId"])
    built["manifest"]["sourceCoverage"] = source_coverage
    built["manifest"]["completeAcrossContractSources"] = bool(source_coverage) and all(
        status == "completed" for status in source_coverage.values())

    summary = {**built["manifest"], "sourceCoverage": source_coverage,
               "completeAcrossContractSources":
               built["manifest"]["completeAcrossContractSources"]}
    if dry_run:
        return summary

    out = run_root / "candidate-pool"
    if out.exists():
        if not redo:
            raise FileExistsError(f"{out} 已存在；重建請使用 --redo")
        archive = run_root / "previous-candidate-pools"
        archive.mkdir(parents=True, exist_ok=True)
        suffix = hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest()[:12]
        target = archive / suffix
        serial = 1
        while target.exists():
            serial += 1
            target = archive / f"{suffix}-{serial}"
        shutil.move(str(out), str(target))
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "manifest.json", built["manifest"])
    atomic_write_json(out / "candidates.json", built["candidates"])
    atomic_write_json(out / "identifier-conflicts.json", built["identifierConflicts"])
    atomic_write_json(out / "title-ambiguities.json", built["titleAmbiguities"])
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--redo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = build_from_run_root(args.run_root, dry_run=args.dry_run, redo=args.redo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
