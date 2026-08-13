#!/usr/bin/env python3
"""
StudyFamily 分層判定 (Gap G)

設計目標：讓「同一研究的多篇報告」不會被當成多份獨立證據，同時不把成本
壓在人工上。三層：

  tier1  確定性訊號 —— 自動合併，無需人工
  tier2  強啟發式   —— 建立 suspectedFamily，不自動合併
  tier3  弱啟發式   —— 同上，優先度較低
  none   無關聯

關鍵設計：tier2/tier3 的解析 **延後** 到該研究實際要支撐 Claim 時才發生。
絕大多數文獻停在 T1/T2，永遠不需要人工解析。這是把人工成本從
「全庫 O(n²)」降到「僅 Claim 支撐集」的機制。

模型不得判定 family。模型產生的候選只寫入 advisory 命名空間。
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

REGISTRY_PATTERNS = {
    "ClinicalTrials.gov": re.compile(r"^NCT\d{8}$", re.I),
    "ISRCTN": re.compile(r"^ISRCTN\d{8}$", re.I),
    "ANZCTR": re.compile(r"^ACTRN\d{14}$", re.I),
    "ChiCTR": re.compile(r"^ChiCTR[-A-Z0-9]{4,}$", re.I),
    "UMIN-CTR": re.compile(r"^UMIN\d{9}$", re.I),
    "EudraCT": re.compile(r"^\d{4}-\d{6}-\d{2}$"),
}


def normalise_registry_id(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip().upper().replace(" ", "")
    for pat in REGISTRY_PATTERNS.values():
        if pat.match(s):
            return s
    return None


def normalise_author(name: str) -> str:
    """姓 + 名首字母。刻意保守：不做同名合併，只做格式正規化。"""
    s = re.sub(r"[^\w\s,.-]", "", name.strip())
    if "," in s:
        surname, rest = s.split(",", 1)
    else:
        parts = s.split()
        surname, rest = (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else (s, "")
    initial = rest.strip()[:1].upper() if rest.strip() else ""
    return f"{surname.strip().lower()}|{initial}"


@dataclass
class Report:
    work_id: str
    registry_id: Optional[str] = None
    doi: Optional[str] = None
    authors: Sequence[str] = field(default_factory=list)
    sample_size: Optional[int] = None
    recruitment_start: Optional[str] = None      # ISO date
    recruitment_end: Optional[str] = None
    country_or_site: Optional[str] = None
    population_descriptor: Optional[str] = None
    trial_acronym: Optional[str] = None
    publication_year: Optional[int] = None

    @property
    def norm_registry(self) -> Optional[str]:
        return normalise_registry_id(self.registry_id)

    @property
    def norm_authors(self) -> list[str]:
        return [normalise_author(a) for a in self.authors]

    @property
    def first_author(self) -> Optional[str]:
        return self.norm_authors[0] if self.norm_authors else None

    @property
    def last_author(self) -> Optional[str]:
        return self.norm_authors[-1] if len(self.norm_authors) > 1 else None

    @property
    def recruitment_window(self) -> Optional[tuple]:
        if self.recruitment_start and self.recruitment_end:
            return (self.recruitment_start, self.recruitment_end)
        return None


def pairwise_signals(a: Report, b: Report) -> dict:
    sig = {
        "sameRegistryId": (a.norm_registry
                           if a.norm_registry and a.norm_registry == b.norm_registry
                           else None),
        "sameDOI": bool(a.doi and b.doi and a.doi.lower() == b.doi.lower()),
        "sameSampleSize": (None if None in (a.sample_size, b.sample_size)
                           else a.sample_size == b.sample_size),
        "sampleSizeValues": [x for x in (a.sample_size, b.sample_size) if x is not None],
        "sameRecruitmentWindow": (None if not (a.recruitment_window and b.recruitment_window)
                                  else a.recruitment_window == b.recruitment_window),
        "recruitmentWindows": [str(w) for w in (a.recruitment_window, b.recruitment_window) if w],
        "sameSiteOrCountry": (None if None in (a.country_or_site, b.country_or_site)
                              else a.country_or_site.strip().lower()
                              == b.country_or_site.strip().lower()),
        "authorOverlapCount": len(set(a.norm_authors) & set(b.norm_authors)),
        "sharedFirstOrLastAuthor": bool(
            (a.first_author and a.first_author == b.first_author)
            or (a.last_author and a.last_author == b.last_author)),
        "publicationYearSpan": (None if None in (a.publication_year, b.publication_year)
                                else abs(a.publication_year - b.publication_year)),
        "samePopulationDescriptor": (
            None if None in (a.population_descriptor, b.population_descriptor)
            else a.population_descriptor.strip().lower()
            == b.population_descriptor.strip().lower()),
        "sameTrialAcronym": (None if None in (a.trial_acronym, b.trial_acronym)
                             else a.trial_acronym.strip().upper()
                             == b.trial_acronym.strip().upper()),
    }
    return sig


def classify_pair(a: Report, b: Report) -> dict:
    """回傳 {tier, ruleId, signals}。tier 為 tier1/tier2/tier3/none。"""
    s = pairwise_signals(a, b)

    if s["sameDOI"]:
        return {"tier": "tier1-deterministic", "ruleId": "FAM-T1-001-same-doi",
                "signals": s}
    if s["sameRegistryId"]:
        return {"tier": "tier1-deterministic",
                "ruleId": "FAM-T1-002-same-registry-id", "signals": s}
    if s["sameTrialAcronym"] and s["sharedFirstOrLastAuthor"]:
        return {"tier": "tier1-deterministic",
                "ruleId": "FAM-T1-003-acronym-plus-shared-key-author", "signals": s}

    strong = (s["sameSampleSize"] is True
              and s["sameRecruitmentWindow"] is True
              and s["sameSiteOrCountry"] is True)
    if strong:
        return {"tier": "tier2-strong-heuristic",
                "ruleId": "FAM-T2-001-n-window-site", "signals": s}
    if (s["sameSampleSize"] is True and s["sharedFirstOrLastAuthor"]
            and s["samePopulationDescriptor"] is True):
        return {"tier": "tier2-strong-heuristic",
                "ruleId": "FAM-T2-002-n-author-population", "signals": s}

    weak = (s["authorOverlapCount"] >= 2
            and s["samePopulationDescriptor"] is True
            and (s["publicationYearSpan"] is not None and s["publicationYearSpan"] <= 4))
    if weak:
        return {"tier": "tier3-weak-heuristic",
                "ruleId": "FAM-T3-001-authors-population-years", "signals": s}

    return {"tier": "none", "ruleId": "FAM-T0-000-no-signal", "signals": s}


def build_families(reports: Sequence[Report],
                   claim_supporting: Optional[set] = None) -> dict:
    """以 tier1 邊建立自動合併的 family（連通分量）；
    tier2/tier3 邊只登錄為 suspected，不合併。

    claim_supporting：實際支撐 Claim 的 work_id 集合。suspected 配對中
    只要有任一端屬於此集合，就進人工佇列；否則標記 deferred。
    """
    claim_supporting = claim_supporting or set()
    idx = {r.work_id: r for r in reports}
    parent = {r.work_id: r.work_id for r in reports}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    tier1_edges, suspected = [], []
    for a, b in itertools.combinations(reports, 2):
        res = classify_pair(a, b)
        t = res["tier"]
        if t == "tier1-deterministic":
            union(a.work_id, b.work_id)
            tier1_edges.append({"pair": [a.work_id, b.work_id], **res})
        elif t in ("tier2-strong-heuristic", "tier3-weak-heuristic"):
            needs_human = bool({a.work_id, b.work_id} & claim_supporting)
            suspected.append({
                "pair": [a.work_id, b.work_id], **res,
                "status": ("suspected-unresolved" if needs_human
                           else "deferred-not-claim-supporting"),
                "resolvedBy": {"agentClass": "deterministic", "at": None,
                               "rationale": None},
            })

    groups: dict = {}
    for wid in parent:
        groups.setdefault(find(wid), []).append(wid)

    families = []
    for root, members in sorted(groups.items()):
        if len(members) == 1:
            continue
        families.append({
            "familyId": f"ahig:family:{root}",
            "members": [{"work": m,
                         "role": "primary-report" if m == root else "secondary-publication",
                         "contributesEvidence": m == root}
                        for m in sorted(members)],
            "resolution": {"tier": "tier1-deterministic", "status": "auto-merged",
                           "signals": {}, "ruleId": "FAM-T1-union",
                           "resolvedBy": {"agentClass": "deterministic"}},
            "evidenceWeightPolicy": {"countAs": "one-study", "flagOnUnresolved": True},
        })

    unresolved_pairs = [s for s in suspected if s["status"] == "suspected-unresolved"]
    return {
        "families": families,
        "tier1Edges": tier1_edges,
        "suspectedPairs": suspected,
        "humanQueueSize": len(unresolved_pairs),
        "deferredCount": len(suspected) - len(unresolved_pairs),
        "note": ("suspectedPairs 未解析時，若其成員同時計入同一 SynthesizedClaim，"
                 "該 Claim 必須帶 possibleDuplicateEvidence 標記，"
                 "且不得評為 high certainty。"),
    }


def claim_duplicate_flag(evidence_work_ids: Sequence[str], family_report: dict) -> dict:
    """給定一條 Claim 的證據集，判斷是否需要 possibleDuplicateEvidence 標記。"""
    ids = set(evidence_work_ids)
    hits = [s for s in family_report["suspectedPairs"]
            if set(s["pair"]) <= ids]
    merged_conflicts = []
    for fam in family_report["families"]:
        members = {m["work"] for m in fam["members"]}
        overlap = members & ids
        if len(overlap) > 1:
            merged_conflicts.append({"familyId": fam["familyId"],
                                     "overlappingMembers": sorted(overlap)})
    return {
        "possibleDuplicateEvidence": bool(hits) or bool(merged_conflicts),
        "unresolvedSuspectedPairs": [h["pair"] for h in hits],
        "sameFamilyCountedMultipleTimes": merged_conflicts,
        "certaintyCeiling": ("moderate" if (hits or merged_conflicts) else None),
    }
