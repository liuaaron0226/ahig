#!/usr/bin/env python3
"""W7：以 SYNERGY 基準資料集重放 ADR-0008 統計終止（參數凍結證據）。

目的：在凍結 α=0.05、target_recall=0.95 之前，用 26+ 個已知真值的系統性
回顧資料集重放 `statistical_termination.p_score` 的停止規則，量測：

1. **違規率**：停止當下 recall < 0.95 的比例（理論上界 α=0.05）；
2. **節省率**：停止時未篩比例（終止機制存在的理由）;
3. **尾端抽驗攔截率**：違規發生時，200 筆尾端抽驗抓到 ≥1 篇相關的機率
   （ADR-0008 條件 4 的第二道防線有多可靠）。

三種篩選順序，對應三個世界：

- ``random``：純隨機順序——超幾何檢定的交換性假設完全成立，這是檢定
  數學保證的直接驗證。
- ``al-proxy``：主動學習代理（score = 2·label + N(0,1)）——相關文獻
  前移，模擬 W6 排序器生效後的實況。**已知理論缺口**：AL 排序讓已篩
  尾段不再是剩餘池的交換性抽樣，檢定在此嚴格說是未涵蓋的。
- ``adversarial``：同 al-proxy，但 5% 相關文獻被打成極低分（模型盲點，
  score = −3 + N(0,1)）——殘餘相關集中在池子最尾端，是 BUSCAR 式檢定
  的已知最壞情境。此順序下的違規率就是「模型系統性盲點」的風險標價。

實作註記：p 值在零尾段內以乘積形式增量計算（O(N)/走訪），候選停點再
呼叫**真正的** `p_score` 覆核——凍結物驗證的是生產程式碼，不是重算版。

用法：python3 analysis/synergy_replay.py [--synergy-root PATH] [--quick]
資料集：https://github.com/asreview/synergy-dataset（CC-BY；本腳本只讀
label_included 欄，不讀任何書目內容）。
"""

from __future__ import annotations
import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scipy import stats

from ahig.bootstrap import configure_stdio
from ahig.search.statistical_termination import (DEFAULT_ALPHA,
                                                 DEFAULT_TARGET_RECALL,
                                                 DEFAULT_TAIL_SPOT_CHECK_N,
                                                 p_score)

configure_stdio()
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

ORDERINGS = ("random", "al-proxy", "adversarial")
ADVERSARIAL_BLINDSPOT = 0.05   # 被模型系統性看走眼的相關文獻比例


def load_labels(synergy_root: Path) -> dict[str, list[int]]:
    """讀每個資料集的 0/1 標籤；空白標籤列剔除並計數（少數集有未標紀錄）。"""
    out: dict[str, list[int]] = {}
    for ids_csv in sorted(synergy_root.glob("datasets/*/*_ids.csv")):
        name = ids_csv.stem.removesuffix("_ids")
        labels, dropped = [], 0
        with ids_csv.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                raw = (row.get("label_included") or "").strip()
                if raw in ("0", "1"):
                    labels.append(int(raw))
                else:
                    dropped += 1
        if dropped:
            print(f"  [{name}] 剔除 {dropped} 筆無標籤紀錄", file=sys.stderr)
        if labels and sum(labels):
            out[name] = labels
    return out


def make_order(labels: list[int], ordering: str, rng: random.Random) -> list[int]:
    n = len(labels)
    if ordering == "random":
        idx = list(range(n))
        rng.shuffle(idx)
        return [labels[i] for i in idx]
    scores = []
    for i, lab in enumerate(labels):
        if ordering == "adversarial" and lab and rng.random() < ADVERSARIAL_BLINDSPOT:
            s = -3.0 + rng.gauss(0, 1)          # 模型盲點：相關卻墊底
        else:
            s = 2.0 * lab + rng.gauss(0, 1)     # AL 代理：相關大致前移
        scores.append((s, rng.random(), i))
    scores.sort(reverse=True)
    return [labels[i] for _, _, i in scores]


def replay_walk(order: list[int], *, alpha: float, target: float,
                look_every: int = 1) -> dict:
    """走一遍篩選順序，回傳首個允許停止的位置（或無）。

    段內增量：同一零尾段內 n_start 與 k_min 固定，p(w) 是遞減乘積。
    候選停點以真 p_score 覆核；不一致（浮點邊界）就繼續走。

    ``look_every``：每篩幾筆才評估一次終止（=1 是逐筆重看的最壞情況；
    生產環境是驅動器每批 100 筆固化後才評估——序貫檢定的膨脹隨重看
    頻率下降，兩種都量測，凍結物記實測差）。
    """
    n = len(order)
    from fractions import Fraction
    tau = Fraction(str(target))
    rho = 0
    n_start, k_min = n, 1          # rho=0 段：k_target=1
    p_prod, w = 1.0, 0
    for i, lab in enumerate(order):
        if lab:
            rho += 1
            k_target = (rho * tau.denominator) // tau.numerator + 1
            k_min = k_target - rho
            n_start = n - (i + 1)
            p_prod, w = 1.0, 0
            continue
        w += 1
        if k_min > n_start:
            p_prod = 0.0
        elif p_prod > 0:
            p_prod *= max(0.0, (n_start - k_min - (w - 1))) / (n_start - (w - 1))
        at_look = (i + 1) % look_every == 0 or i + 1 == n
        if at_look and p_prod < alpha:
            real = p_score(order[:i + 1], n, target_recall=target)
            if real["pScore"] < alpha:
                return {"stopped": True, "stopIndex": i + 1,
                        "found": rho, "pAtStop": real["pScore"]}
            p_prod = real["pScore"]   # 浮點邊界：以真值續走
    return {"stopped": False, "stopIndex": n, "found": rho, "pAtStop": None}


def tail_catch_probability(n_tail: int, missed: int,
                           sample_n: int = DEFAULT_TAIL_SPOT_CHECK_N) -> float:
    """尾端抽驗抓到 ≥1 篇相關的機率（超幾何精確值）。"""
    if missed <= 0 or n_tail <= 0:
        return 0.0
    s = min(sample_n, n_tail)
    return float(1.0 - stats.hypergeom.pmf(0, n_tail, missed, s))


def seeds_for(n: int, quick: bool) -> int:
    if quick:
        return 5
    if n <= 5_000:
        return 60
    if n <= 15_000:
        return 30
    return 10


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synergy-root", type=Path,
                    default=Path("/workspace/asreview/synergy-dataset"))
    ap.add_argument("--quick", action="store_true", help="每集 5 seeds 快跑")
    args = ap.parse_args()

    datasets = load_labels(args.synergy_root)
    if not datasets:
        raise SystemExit(f"找不到資料集：{args.synergy_root}")
    alpha, target = DEFAULT_ALPHA, DEFAULT_TARGET_RECALL

    look_regimes = (1, 100)   # 逐筆重看（最壞）vs 生產批次制（每 100 筆評一次）
    report = {
        "documentType": "adr-0008-parameter-freeze-evidence",
        "adr": "ADR-0008",
        "alpha": alpha, "targetRecall": target,
        "tailSpotCheckN": DEFAULT_TAIL_SPOT_CHECK_N,
        "adversarialBlindspotShare": ADVERSARIAL_BLINDSPOT,
        "lookRegimes": look_regimes,
        "datasetSource": "https://github.com/asreview/synergy-dataset",
        "datasets": {}, "aggregate": {},
    }

    print(f"SYNERGY 重放：{len(datasets)} 個資料集，α={alpha}, "
          f"target recall={target}, 重看頻率 {look_regimes}")
    configs = [(o, lk) for o in ORDERINGS for lk in look_regimes]
    agg = {c: {"walks": 0, "stops": 0, "violations": 0, "savings_sum": 0.0,
               "recall_sum": 0.0, "viol_recall_sum": 0.0, "catch_sum": 0.0}
           for c in configs}

    for name, labels in datasets.items():
        n, r = len(labels), sum(labels)
        n_seeds = seeds_for(n, args.quick)
        row: dict = {"n": n, "relevant": r, "seeds": n_seeds}
        for ordering, look in configs:
            stops = violations = 0
            savings_sum = recall_sum = viol_recall_sum = catch_sum = 0.0
            for seed in range(n_seeds):
                # 順序的 rng 只依 (name, ordering, seed)——兩種重看頻率
                # 走的是同一批順序，差異純粹來自重看頻率本身。
                rng = random.Random(f"w7:{name}:{ordering}:{seed}")
                order = make_order(labels, ordering, rng)
                res = replay_walk(order, alpha=alpha, target=target,
                                  look_every=look)
                a = agg[(ordering, look)]
                a["walks"] += 1
                if not res["stopped"]:
                    continue
                stops += 1
                a["stops"] += 1
                recall = res["found"] / r
                recall_sum += recall
                a["recall_sum"] += recall
                saving = 1 - res["stopIndex"] / n
                savings_sum += saving
                a["savings_sum"] += saving
                if recall < target:
                    violations += 1
                    a["violations"] += 1
                    viol_recall_sum += recall
                    a["viol_recall_sum"] += recall
                    catch = tail_catch_probability(
                        n - res["stopIndex"], r - res["found"])
                    catch_sum += catch
                    a["catch_sum"] += catch
            row[f"{ordering}@look{look}"] = {
                "stops": stops, "violations": violations,
                "violationRate": round(violations / n_seeds, 4),
                "meanRecallAtStop": round(recall_sum / stops, 4) if stops else None,
                "meanSavings": round(savings_sum / stops, 4) if stops else None,
                "meanRecallOnViolation":
                    round(viol_recall_sum / violations, 4) if violations else None,
                "meanTailCatchOnViolation":
                    round(catch_sum / violations, 4) if violations else None,
            }
        report["datasets"][name] = row
        print(f"  {name:34s} N={n:6d} R={r:4d}  " + "  ".join(
            f"{o}@{lk}: {row[f'{o}@look{lk}']['violations']}/{n_seeds}"
            for o, lk in configs))

    print()
    for ordering, look in configs:
        a = agg[(ordering, look)]
        key = f"{ordering}@look{look}"
        vr = a["violations"] / a["walks"] if a["walks"] else 0.0
        report["aggregate"][key] = {
            "walks": a["walks"], "stops": a["stops"],
            "violations": a["violations"],
            "violationRate": round(vr, 4),
            "meanRecallAtStop":
                round(a["recall_sum"] / a["stops"], 4) if a["stops"] else None,
            "meanSavings":
                round(a["savings_sum"] / a["stops"], 4) if a["stops"] else None,
            "meanRecallOnViolation":
                round(a["viol_recall_sum"] / a["violations"], 4)
                if a["violations"] else None,
            "meanTailCatchOnViolation":
                round(a["catch_sum"] / a["violations"], 4)
                if a["violations"] else None,
        }
        print(f"[{key}] 走訪 {a['walks']}, 停止 {a['stops']}, "
              f"違規率 {vr:.2%} (α={alpha:.0%}), "
              f"平均節省 {report['aggregate'][key]['meanSavings']}, "
              f"違規時平均 recall {report['aggregate'][key]['meanRecallOnViolation']}")

    out = OUT / "synergy_replay.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8", newline="\n")
    print(f"\n寫出 {out}")


if __name__ == "__main__":
    main()
