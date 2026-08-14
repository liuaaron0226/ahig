#!/usr/bin/env python3
"""AHIG 吞吐量模型 v2：以 P1–P4 為分母的機器篩選＋擁有者抽查制。

取代 `human_throughput.py` 的規劃基準。舊模型的兩個前提都已失效：

1. **分母**：舊模型算 140 領域全庫；ADR-0011 把路線圖改為需求驅動——
   B.11 只做校準（到 M1 為止），其後是 P1 減脂期蛋白質、P2 睡眠、
   P3 壓力性進食、P4 肌酸/咖啡因，共 4＋1 個領域。
2. **信任模型**：舊模型的五處人工介入（gold set、高風險裁決、anchor
   確認……）在 ADR-0009 之下全部改為「主模型判讀全量＋第二模型盲判
   （harms 道）＋擁有者 find-the-number 抽查」。人時不再是主成本；
   **稀缺資源變成執行室的掛機時數（wall-clock）與擁有者的抽查分鐘**。

舊模型不刪——它是 ADR-0009 之前世界的存檔，verify.py 仍引用其輸出；
本模型另立輸出檔，兩者並存供對照。

所有非實測參數都標在情境假設裡；B.11 實測錨點寫在 `ANCHORS`。
第 154 筆前置樣本判完、影子批次歧異率實測出爐、P1 檢索實跑後，
須依序回填重算（見輸出的 recalibrationTriggers）。
"""

from __future__ import annotations
import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ahig.bootstrap import configure_stdio

configure_stdio()
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# B.11 實測錨點（來源：看板 W5 重建報告 queueHash aad9ddfa…b79331a、
# W8 第 10–11 輪回報）。這些是量測值，不是假設。
# ---------------------------------------------------------------------------
ANCHORS = {
    "queue_total": 15_425,
    "lanes": {                      # W5 重建後的篩選道分布
        "standard-screening": 9_260,
        "safety-review": 2_316,     # ADR-0008 前置：終止前必須全篩；harms 雙模型
        "animal-signal-review": 1_978,
        "review-source-review": 1_700,
        "registry-review": 167,
        "identity-review": 4,
    },
    "judgements_per_round": 25,     # W8 第 11 輪實測：一輪判完一頁 25 筆
    "loop_minutes": 15,             # 執行室 /loop 週期
    "pilot_size": 154,              # ADR-0008 前置抽樣（1%）
    "pilot_judged": 154,            # 第 12 輪判完：2 advance / 149 exclude / 3 unclear
    "pilot_prevalence_low": 2 / 154,    # 實測下界（unclear 全算 exclude）＝1.30%
    "pilot_prevalence_high": 5 / 154,   # 實測上界（unclear 全算 advance）＝3.25%
    "shadow_batch": 300,            # 影子批次（雙模型 → 600 筆判讀）
    "tail_spot_check": 200,         # ADR-0008 終止後尾端抽查
    "calibration_papers": 60,       # M1 校準集全文抽取
}

SECONDARY_LANES = ("animal-signal-review", "review-source-review",
                   "registry-review", "identity-review")


@dataclass
class Scenario:
    label: str
    # --- 篩選 ---
    prevalence: float           # standard 道題摘層 advance 率（回填觸發點 1 已到：
                                #   154/154 實測 1.30–3.25%，LOW/HIGH 取實測界、
                                #   BASE 取點估 ~1.95%；P1–P4 各自的盛行率仍未知，
                                #   沿用 B.11 實測值作為規劃假設）
    termination_fraction: float  # ADR-0008 終止前需篩掉的 standard 道比例（AL 排序＋低盛行率下的推測）
    # --- 執行室產能 ---
    uptime_h_day: float         # 擁有者 PC 開機掛 loop 的時數/日（M1 期主導變數）
    judging_share: float        # loop 輪中實際在判讀的比例（其餘輪做合併、回報、W 包）
    # --- 全文階段 ---
    fulltext_include_rate: float    # 題摘 advance → 全文納入
    extraction_rounds_per_study: float  # 每篇全文抽取＋固化所需 loop 輪
    # --- 擁有者 ---
    owner_spotchecks_per_domain: int    # find-the-number 抽查筆數/領域
    owner_min_per_spotcheck: float
    owner_milestone_h: float            # 里程碑一次性審閱（成果＋抽查債＋契約變更）
    # --- P 領域量體倍率（相對 B.11 queue 15,425；檢索實跑後以實數取代） ---
    mult: dict[str, float] = None  # type: ignore[assignment]


LOW = Scenario("樂觀", prevalence=0.0130, termination_fraction=0.35,
               uptime_h_day=12, judging_share=0.8,
               fulltext_include_rate=0.15, extraction_rounds_per_study=1.5,
               owner_spotchecks_per_domain=8, owner_min_per_spotcheck=3,
               owner_milestone_h=0.5,
               mult={"P1": 0.8, "P2": 0.6, "P3": 0.3, "P4": 1.0})

BASE = Scenario("基準", prevalence=0.0195, termination_fraction=0.55,
                uptime_h_day=8, judging_share=0.7,
                fulltext_include_rate=0.25, extraction_rounds_per_study=2.0,
                owner_spotchecks_per_domain=12, owner_min_per_spotcheck=4,
                owner_milestone_h=1.0,
                mult={"P1": 1.2, "P2": 1.0, "P3": 0.6, "P4": 1.6})

HIGH = Scenario("保守", prevalence=0.0325, termination_fraction=0.85,
                uptime_h_day=4, judging_share=0.6,
                fulltext_include_rate=0.35, extraction_rounds_per_study=3.0,
                owner_spotchecks_per_domain=20, owner_min_per_spotcheck=6,
                owner_milestone_h=2.0,
                mult={"P1": 1.8, "P2": 1.6, "P3": 1.0, "P4": 2.4})

DOMAIN_NOTES = {
    "P1": "減脂期蛋白質與肌肉保留（文獻量大，RCT 密集）",
    "P2": "睡眠與運動表現/恢復",
    "P3": "壓力性進食（與運動員族群交集較窄）",
    "P4": "肌酸/咖啡因（補劑文獻量極大，但重複度高）",
}


def rounds_per_day(s: Scenario) -> float:
    return s.uptime_h_day * (60 / ANCHORS["loop_minutes"]) * s.judging_share


def screening_judgements(s: Scenario, queue_mult: float, *,
                         include_pilot_shadow: bool = True) -> dict:
    """一個領域的題摘層判讀筆數（機器判讀；單位＝筆）。

    - safety 道全篩 ×2（ADR-0008 前置＋ADR-0009 harms 雙模型）
    - standard 道 × 終止比例 ×1（主模型單審；影子門檻通過後）
    - 次要道（animal/review/registry/identity）單審 ×1，**可延後**：
      不在 ADR-0008 終止前置內，M1 不需要，另列不計入核心
    - pilot＋影子批次＋尾端抽查是每領域的固定開銷
    """
    lanes = {k: v * queue_mult for k, v in ANCHORS["lanes"].items()}
    fixed = (ANCHORS["pilot_size"] * queue_mult
             + ANCHORS["shadow_batch"] * 2
             + ANCHORS["tail_spot_check"]) if include_pilot_shadow else 0
    core = (lanes["safety-review"] * 2
            + lanes["standard-screening"] * s.termination_fraction
            + fixed)
    secondary = sum(lanes[k] for k in SECONDARY_LANES)
    return {"core": core, "secondary_deferrable": secondary,
            "lanes": {k: round(v) for k, v in lanes.items()}}


def extraction_load(s: Scenario, queue_mult: float) -> dict:
    """全文階段：AL＋終止設計的意義就是 advance 幾乎不受終止比例影響
    （recall 目標 0.95 固定），故納入數 = standard×盛行率×0.95×納入率。"""
    standard = ANCHORS["lanes"]["standard-screening"] * queue_mult
    advances = standard * s.prevalence * 0.95
    included = advances * s.fulltext_include_rate
    return {"advances": round(advances), "included_studies": round(included),
            "extraction_rounds": round(included * s.extraction_rounds_per_study)}


def domain_report(s: Scenario, key: str) -> dict:
    m = s.mult[key]
    sj = screening_judgements(s, m)
    ex = extraction_load(s, m)
    rpd = rounds_per_day(s)
    screen_rounds = sj["core"] / ANCHORS["judgements_per_round"]
    days_screen = screen_rounds / rpd
    days_extract = ex["extraction_rounds"] / rpd
    owner_h = (s.owner_spotchecks_per_domain * s.owner_min_per_spotcheck / 60
               + s.owner_milestone_h)
    return {
        "note": DOMAIN_NOTES[key],
        "queue_multiplier_assumed": m,
        "queue_projected": round(ANCHORS["queue_total"] * m),
        "screening_judgements_core": round(sj["core"]),
        "screening_judgements_secondary_deferrable": round(sj["secondary_deferrable"]),
        "screening_days": round(days_screen, 1),
        "included_studies": ex["included_studies"],
        "extraction_days": round(days_extract, 1),
        "total_days": round(days_screen + days_extract, 1),
        "owner_hours": round(owner_h, 1),
    }


def m1_remaining(s: Scenario) -> dict:
    """B.11 從當前狀態（前置樣本已判 25/154）到 M1 的殘餘工作量。"""
    a = ANCHORS
    lanes = a["lanes"]
    judgements = (
        (a["pilot_size"] - a["pilot_judged"])          # 前置樣本殘餘
        + a["shadow_batch"] * 2                        # 影子批次雙模型
        + lanes["safety-review"] * 2                   # harms 雙模型全篩
        + lanes["standard-screening"] * s.termination_fraction
        + a["tail_spot_check"])
    screen_rounds = judgements / a["judgements_per_round"]
    calib_rounds = a["calibration_papers"] * s.extraction_rounds_per_study
    overhead_rounds = 12   # W9 交付＋影子門檻報告＋合併複驗等非判讀輪（粗估）
    total_rounds = screen_rounds + calib_rounds + overhead_rounds
    days = total_rounds / rounds_per_day(s)
    return {
        "judgements_remaining": round(judgements),
        "loop_rounds_total": round(total_rounds),
        "wall_clock_days": round(days, 1),
        "wall_clock_weeks": round(days / 7, 1),
    }


def main():
    report = {
        "note": ("規劃估計。實測錨點僅 B.11 佇列分布與判讀速率；"
                 "盛行率/終止比例/量體倍率為情境假設，須依觸發點回填。"),
        "anchors": ANCHORS,
        "recalibrationTriggers": [
            "✅ 已回填（第 12 輪）：盛行率實測 1.30–3.25%（2 advance/149 exclude/3 unclear）",
            "影子批次歧異率實測 → 以歧異率修 judging 品質假設與二審成本",
            "B.11 正式篩選跑到 ADR-0008 終止 → 以實測終止點取代 termination_fraction",
            "每個 P 領域檢索實跑 → 以實際 queue 數取代 mult",
            "M1 校準集 60 篇抽取完成 → 以實測輪數取代 extraction_rounds_per_study",
        ],
        "scenarios": {},
    }

    print("=" * 78)
    print("吞吐量模型 v2：P1–P4 分母（ADR-0009/0010/0011 制度下）")
    print("=" * 78)

    for s in (LOW, BASE, HIGH):
        m1 = m1_remaining(s)
        doms = {k: domain_report(s, k) for k in ("P1", "P2", "P3", "P4")}
        p_days = sum(d["total_days"] for d in doms.values())
        owner_total = (sum(d["owner_hours"] for d in doms.values())
                       + s.owner_milestone_h  # M1 本身的一次性審閱
                       + 5 * s.owner_min_per_spotcheck / 60)  # 既有抽查債 5 筆
        m2_days = m1["wall_clock_days"] + doms["P1"]["total_days"]
        print(f"\n【{s.label}】掛機 {s.uptime_h_day}h/日，判讀輪占比 "
              f"{s.judging_share:.0%}，盛行率 {s.prevalence:.0%}，"
              f"終止比例 {s.termination_fraction:.0%}")
        print(f"  M1（B.11 校準集就緒）殘餘：{m1['judgements_remaining']:,} 筆判讀 "
              f"≈ {m1['loop_rounds_total']} 輪 ≈ {m1['wall_clock_days']} 天"
              f"（{m1['wall_clock_weeks']} 週）")
        print(f"  M2（M1＋P1 首批結論）：≈ {m2_days:.0f} 天")
        for k, d in doms.items():
            print(f"  {k} {d['note']}：篩 {d['screening_days']} 天 + "
                  f"抽取 {d['extraction_days']} 天（納入 ~{d['included_studies']} 篇）"
                  f" = {d['total_days']} 天")
        print(f"  P1–P4 合計 wall-clock ≈ {p_days:.0f} 天；"
              f"擁有者總投入 ≈ {owner_total:.1f} 小時（抽查＋里程碑）")
        report["scenarios"][s.label] = {
            "params": asdict(s), "m1_remaining": m1, "domains": doms,
            "p1_p4_total_days": round(p_days, 1),
            "m2_days_from_now": round(m2_days, 1),
            "owner_hours_total": round(owner_total, 1),
        }

    # 與舊模型對照：同一份工作在 ADR-0009 之前的人時標價
    old_path = OUT / "human_throughput.json"
    if old_path.exists():
        old = json.loads(old_path.read_text(encoding="utf-8"))
        old_py = old["report"]["headline"]["base_scoped_person_years"]
        new_owner = report["scenarios"]["基準"]["owner_hours_total"]
        print("\n" + "=" * 78)
        print("對照舊模型（140 領域、全人工、有範圍契約、基準情境）")
        print("=" * 78)
        print(f"  舊制人工需求：{old_py} 人年（{old_py * 1800:,.0f} 小時）")
        print(f"  新制擁有者投入（B.11＋P1–P4 全部）：{new_owner} 小時")
        print(f"  代價轉移到：執行室 wall-clock（PC 開機時間）＋"
              f"「AI-graded evidence」標籤（ADR-0009 明示）")
        report["old_model_comparison"] = {
            "old_base_scoped_person_years": old_py,
            "new_owner_hours_total_base": new_owner,
            "cost_shifted_to": "executor wall-clock + AI-graded evidence label",
        }

    (OUT / "throughput_p1p4.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\n寫出 {OUT / 'throughput_p1p4.json'}")


if __name__ == "__main__":
    main()
