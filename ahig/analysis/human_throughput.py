#!/usr/bin/env python3
"""
AHIG 人力吞吐量與批次容量模型 (Gap B，並量化 Gap A 的修正效益)

契約中至少五處要求人工介入：
  1. gold set 建立（50 篇 / >=300 critical fields）
  2. 高風險主張 100% 人工裁決
  3. fuzzy OCR anchor 100% 人工確認
  4. 相似度 0.75–0.90 的 manual-required anchor
  5. 數值分歧的第三順位人類裁決

本模型計算：
  A. 校準集的一次性工時（自動化啟用的前置門檻）
  B. 全庫在「無抽取範圍契約」與「有抽取範圍契約」兩種情況下的人工工時
  C. 佇列穩定條件下的最大批次大小（每批領域數）
  D. 到第一條 Approved Claim 的最短前置時間

所有時間參數為明列假設下的規劃估計，非實測值。第一批實跑後必須以實測重新校準。
"""

from __future__ import annotations
import json
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ahig.bootstrap import configure_stdio

configure_stdio()
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)


@dataclass
class Params:
    label: str
    # --- 單位工時（分鐘） ---
    t_read_paper: float           # 為建立 gold answer 而完整閱讀一篇論文
    t_critical_field: float       # 每個 critical field 的 gold answer
    t_adjudicate_field: float     # 每次模型分歧的人工裁決（已有原文+locator+確定性報告）
    t_manual_anchor: float        # 每個 manual-required / fuzzy anchor 的人工確認
    t_highrisk_claim: float       # 每條高風險 SynthesizedClaim 的完整人工裁決
    t_screen_record: float        # 每筆題摘篩選

    # --- 比率 ---
    model_disagreement_rate: float   # 兩模型盲審在 critical field 上的分歧比例
    manual_anchor_rate: float        # 落入 manual/fuzzy 帶的 anchor 比例
    highrisk_claim_share: float      # 高風險主張佔比

    # --- 量體 ---
    n_domains: int = 140
    reports_per_domain_T1: int = 200
    dedup_overlap_factor: float = 0.72   # 跨領域去重後保留比例（重疊係數的倒推）
    t3_share_unscoped: float = 1.00      # 無範圍契約：所有 T2 都全抽
    t3_share_scoped: float = 0.25        # 有範圍契約：只抽實際支援 Claim 的研究
    studyresults_per_study_unscoped: float = 30.0
    studyresults_per_study_scoped: float = 5.0
    critical_fields_per_studyresult: int = 8
    anchors_per_studyresult: float = 2.0
    claims_per_domain: int = 12

    # --- 校準集 ---
    calib_studies: int = 50
    calib_critical_fields: int = 300


LOW = Params("樂觀", t_read_paper=25, t_critical_field=2.0, t_adjudicate_field=4,
             t_manual_anchor=1.5, t_highrisk_claim=20, t_screen_record=0.4,
             model_disagreement_rate=0.08, manual_anchor_rate=0.05,
             highrisk_claim_share=0.15)

BASE = Params("基準", t_read_paper=45, t_critical_field=4.0, t_adjudicate_field=8,
              t_manual_anchor=3.0, t_highrisk_claim=45, t_screen_record=0.75,
              model_disagreement_rate=0.15, manual_anchor_rate=0.12,
              highrisk_claim_share=0.25)

HIGH = Params("保守", t_read_paper=90, t_critical_field=8.0, t_adjudicate_field=15,
              t_manual_anchor=6.0, t_highrisk_claim=90, t_screen_record=1.5,
              model_disagreement_rate=0.25, manual_anchor_rate=0.25,
              highrisk_claim_share=0.40)


def calibration_hours(p: Params) -> dict:
    read = p.calib_studies * p.t_read_paper
    fields = p.calib_critical_fields * p.t_critical_field
    # 盲測結果的比對與歧異分析（gold set 必須逐欄比對兩模型輸出）
    review = p.calib_critical_fields * 2 * p.t_adjudicate_field * 0.35
    total_min = read + fields + review
    return {
        "read_papers_h": round(read / 60, 1),
        "gold_fields_h": round(fields / 60, 1),
        "blinded_comparison_h": round(review / 60, 1),
        "total_h": round(total_min / 60, 1),
    }


def corpus_volumes(p: Params, scoped: bool) -> dict:
    t1_raw = p.n_domains * p.reports_per_domain_T1
    t1_unique = t1_raw * p.dedup_overlap_factor
    t3_share = p.t3_share_scoped if scoped else p.t3_share_unscoped
    t3_studies = t1_unique * t3_share
    sr_per = (p.studyresults_per_study_scoped if scoped
              else p.studyresults_per_study_unscoped)
    studyresults = t3_studies * sr_per
    critical_fields = studyresults * p.critical_fields_per_studyresult
    anchors = studyresults * p.anchors_per_studyresult
    claims = p.n_domains * p.claims_per_domain
    return {
        "T1_records_raw": int(t1_raw),
        "T1_records_deduped": int(t1_unique),
        "T3_studies": int(t3_studies),
        "study_results": int(studyresults),
        "critical_fields": int(critical_fields),
        "anchors": int(anchors),
        "synthesized_claims": int(claims),
    }


def corpus_hours(p: Params, scoped: bool) -> dict:
    v = corpus_volumes(p, scoped)
    screen = v["T1_records_deduped"] * p.t_screen_record
    adjud = v["critical_fields"] * p.model_disagreement_rate * p.t_adjudicate_field
    anchors = v["anchors"] * p.manual_anchor_rate * p.t_manual_anchor
    highrisk = v["synthesized_claims"] * p.highrisk_claim_share * p.t_highrisk_claim
    total = screen + adjud + anchors + highrisk
    return {
        "volumes": v,
        "screening_h": round(screen / 60),
        "field_adjudication_h": round(adjud / 60),
        "manual_anchor_h": round(anchors / 60),
        "highrisk_claim_h": round(highrisk / 60),
        "total_h": round(total / 60),
        "total_person_years_at_1800h": round(total / 60 / 1800, 1),
    }


def max_batch_size(p: Params, scoped: bool, weekly_capacity_h: float,
                   batch_weeks: int = 4) -> float:
    """佇列穩定條件：每批產生的人工需求 <= 該批期間的人工產能。
    回傳每批可容納的領域數（可為小數，實務上向下取整）。"""
    h = corpus_hours(p, scoped)
    per_domain_h = h["total_h"] / p.n_domains
    capacity = weekly_capacity_h * batch_weeks
    return capacity / per_domain_h if per_domain_h > 0 else float("inf")


def time_to_first_claim(p: Params, weekly_capacity_h: float) -> dict:
    """校準集 + 第一批（假設 1 個領域的最小可行切片）"""
    calib = calibration_hours(p)["total_h"]
    h = corpus_hours(p, scoped=True)
    one_domain = h["total_h"] / p.n_domains
    return {
        "calibration_weeks": round(calib / weekly_capacity_h, 1),
        "first_domain_weeks": round(one_domain / weekly_capacity_h, 1),
        "total_weeks_to_first_approved_claim": round(
            (calib + one_domain) / weekly_capacity_h, 1),
    }


def main():
    report = {"note": "規劃估計，非實測。第一批實跑後須以實測重新校準本模型。",
              "scenarios": {}}

    print("=" * 78)
    print("A. 校準集一次性工時（自動化啟用前必須完成）")
    print("=" * 78)
    for p in (LOW, BASE, HIGH):
        c = calibration_hours(p)
        print(f"  {p.label}: 閱讀 {c['read_papers_h']}h + gold 欄位 {c['gold_fields_h']}h "
              f"+ 盲測比對 {c['blinded_comparison_h']}h = 合計 {c['total_h']}h")
        report["scenarios"].setdefault(p.label, {})["calibration"] = c

    print()
    print("=" * 78)
    print("B. 全庫人工工時：無抽取範圍契約 vs 有抽取範圍契約")
    print("=" * 78)
    for p in (LOW, BASE, HIGH):
        u = corpus_hours(p, scoped=False)
        s = corpus_hours(p, scoped=True)
        print(f"\n  【{p.label}】")
        print(f"    無範圍契約: StudyResult {u['volumes']['study_results']:>9,} 個, "
              f"人工 {u['total_h']:>7,}h ({u['total_person_years_at_1800h']} 人年)")
        print(f"    有範圍契約: StudyResult {s['volumes']['study_results']:>9,} 個, "
              f"人工 {s['total_h']:>7,}h ({s['total_person_years_at_1800h']} 人年)")
        print(f"    降幅: {(1 - s['total_h']/u['total_h'])*100:.1f}%")
        print(f"    有範圍契約的工時組成: 篩選 {s['screening_h']:,}h / "
              f"欄位裁決 {s['field_adjudication_h']:,}h / "
              f"anchor {s['manual_anchor_h']:,}h / 高風險主張 {s['highrisk_claim_h']:,}h")
        report["scenarios"][p.label]["corpus_unscoped"] = u
        report["scenarios"][p.label]["corpus_scoped"] = s

    print()
    print("=" * 78)
    print("C. 佇列穩定條件下的最大批次大小（領域數 / 批，批期 4 週）")
    print("=" * 78)
    print(f"  {'情境':<6} {'週產能':>8} {'無範圍契約':>14} {'有範圍契約':>14}")
    for p in (LOW, BASE, HIGH):
        rows = []
        for cap in (5, 10, 20, 40):
            u = max_batch_size(p, False, cap)
            s = max_batch_size(p, True, cap)
            rows.append({"weekly_capacity_h": cap,
                         "max_domains_per_batch_unscoped": round(u, 2),
                         "max_domains_per_batch_scoped": round(s, 2)})
            print(f"  {p.label:<6} {cap:>6}h/週 {u:>14.2f} {s:>14.2f}")
        report["scenarios"][p.label]["batch_capacity"] = rows

    print()
    print("=" * 78)
    print("D. 到第一條 Approved Claim 的前置時間（有範圍契約）")
    print("=" * 78)
    for p in (LOW, BASE, HIGH):
        rows = []
        for cap in (5, 10, 20):
            t = time_to_first_claim(p, cap)
            rows.append({"weekly_capacity_h": cap, **t})
            print(f"  {p.label:<6} {cap:>3}h/週: 校準 {t['calibration_weeks']:>5} 週 "
                  f"+ 首個領域 {t['first_domain_weeks']:>5} 週 "
                  f"= {t['total_weeks_to_first_approved_claim']:>5} 週")
        report["scenarios"][p.label]["time_to_first_claim"] = rows

    print()
    print("=" * 78)
    print("結論（基準情境，10h/週）")
    print("=" * 78)
    b = corpus_hours(BASE, True)
    bu = corpus_hours(BASE, False)
    print(f"  現行契約（無範圍限制器）需要 {bu['total_person_years_at_1800h']} 人年人工")
    print(f"  加入抽取範圍契約後需要 {b['total_person_years_at_1800h']} 人年人工")
    print(f"  基準情境下 8–12 領域/批 在 10h/週 是否可行: "
          f"{'否' if max_batch_size(BASE, True, 10) < 8 else '是'} "
          f"（實際上限 {max_batch_size(BASE, True, 10):.2f} 領域/批）")
    print(f"  要支撐 8 領域/批 需要週產能 "
          f"{10 * 8 / max_batch_size(BASE, True, 10):.0f} h/週")

    report["headline"] = {
        "base_scoped_person_years": corpus_hours(BASE, True)["total_person_years_at_1800h"],
        "base_unscoped_person_years": corpus_hours(BASE, False)["total_person_years_at_1800h"],
        "base_max_domains_per_batch_at_10h_week": round(max_batch_size(BASE, True, 10), 2),
        "weekly_hours_needed_for_8_domain_batch_base": round(
            10 * 8 / max_batch_size(BASE, True, 10)),
    }
    (OUT / "human_throughput.json").write_text(
        json.dumps({"params": {p.label: asdict(p) for p in (LOW, BASE, HIGH)},
                    "report": report}, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\n寫出 {OUT / 'human_throughput.json'}")


if __name__ == "__main__":
    main()
