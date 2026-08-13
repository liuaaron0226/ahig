#!/usr/bin/env python3
"""第六輪：上市＋上櫃全台股（~1900 檔）重跑核心結論。"""
import json, os, collections
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, "expost_cache.json"), encoding="utf-8"))
B = json.load(open(os.path.join(HERE, "otc_cache.json"), encoding="utf-8"))
START = "2024-12"
rows = []
for tag, D in (("上市", A), ("上櫃", B)):
    META, PX = D["meta"], D["px"]
    for code, bars in PX.items():
        mm = [x[0] for x in bars]
        if START not in mm or bars[-1][0] < "2026-07":
            continue
        i0 = mm.index(START)
        px0, adj0 = bars[i0][1], bars[i0][2]
        if not px0 or not adj0:
            continue
        hist = [x[1] for x in bars[max(0, i0-36):i0+1] if x[1]]
        vols = [x[3] for x in bars[max(0, i0-11):i0+1] if x[3]]
        sh = META.get(code, {}).get("shares") or 0
        rows.append(dict(mkt=tag, code=code, name=META.get(code, {}).get("name", ""),
                         ind=META.get(code, {}).get("industry", "?"),
                         ret=bars[-1][2]/adj0-1, px0=px0,
                         mcap=px0*sh/1e8 if sh else None,
                         dd=1-px0/max(hist), off_low=px0/min(hist)-1,
                         r12=adj0/bars[i0-12][2]-1 if i0 >= 12 and bars[i0-12][2] else None,
                         vol=float(np.median(vols))/1000 if vols else None))
win = [r for r in rows if r["ret"] > 1]
lose = [r for r in rows if r["ret"] < 0]
R = np.array([r["ret"] for r in rows])
print(f"全台股樣本 {len(rows)} 檔（上市 {sum(1 for r in rows if r['mkt']=='上市')} ＋ "
      f"上櫃 {sum(1 for r in rows if r['mkt']=='上櫃')}）")
print(f"  中位 {np.median(R)*100:+.1f}%  平均 {R.mean()*100:+.1f}%  "
      f"翻倍 {len(win)} 檔 ({len(win)/len(rows)*100:.1f}%)  下跌 {len(lose)/len(rows)*100:.1f}%")
print(f"  贏過加權指數(+91.0%) 的比例：{sum(1 for x in R if x>0.910)/len(R)*100:.1f}%")
print(f"  上市翻倍率 {sum(1 for r in rows if r['mkt']=='上市' and r['ret']>1)/sum(1 for r in rows if r['mkt']=='上市')*100:.1f}%"
      f"，上櫃翻倍率 {sum(1 for r in rows if r['mkt']=='上櫃' and r['ret']>1)/sum(1 for r in rows if r['mkt']=='上櫃')*100:.1f}%")


def auc(a, b):
    a = np.asarray([x for x in a if x is not None], float)
    b = np.asarray([x for x in b if x is not None], float)
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    return u.statistic/(len(a)*len(b)), u.pvalue, np.median(a), np.median(b)


print(f"\n{'特徵':<16}{'贏家中位':>11}{'輸家中位':>11}{'AUC':>8}{'p':>10}")
print("-" * 58)
for lab, k in (("起點股價", "px0"), ("市值(億,僅上市)", "mcap"), ("距36M高點回撤", "dd"),
               ("距36M低點漲幅", "off_low"), ("前12M報酬", "r12"), ("成交量(張)", "vol")):
    a, p, mw, ml = auc([r[k] for r in win], [r[k] for r in lose])
    print(f"{lab:<16}{mw:>11.2f}{ml:>11.2f}{a:>8.3f}{p:>10.4f}")

print("\n─ 產業（全台股，翻倍股數前 12）─")
by = collections.defaultdict(list)
for r in rows:
    by[r["ind"]].append(r)
t = [(i, len(v), sum(1 for x in v if x["ret"] > 1), np.median([x["ret"] for x in v])*100)
     for i, v in by.items()]
for i, n, w, m in sorted(t, key=lambda x: -x[2])[:12]:
    print(f"  {i:<16}{n:>5} 檔  翻倍 {w:>3} ({w/n*100:5.1f}%)  中位 {m:+6.1f}%  "
          f"佔全部翻倍股 {w/len(win)*100:4.1f}%")
top = sorted(t, key=lambda x: -x[2])
print(f"  前 3 大產業佔翻倍股 {sum(x[2] for x in top[:3])/len(win)*100:.1f}%，"
      f"佔家數 {sum(x[1] for x in top[:3])/len(rows)*100:.1f}%")
TECH = {"半導體業", "電子零組件業", "其他電子業", "光電業", "電腦及週邊設備業",
        "通信網路業", "電子通路業", "電機機械", "資訊服務業", "數位雲端"}
tw = sum(1 for r in win if r["ind"] in TECH)
tn = sum(1 for r in rows if r["ind"] in TECH)
print(f"  電子相關佔翻倍股 {tw/len(win)*100:.1f}%（佔全樣本家數 {tn/len(rows)*100:.1f}%）；"
      f"電子翻倍率 {tw/tn*100:.1f}% vs 非電子 {(len(win)-tw)/(len(rows)-tn)*100:.1f}%")

print("\n─ 五分位翻倍率（全台股）─")
base = len(win)/len(rows)*100
for lab, k in (("起點股價", "px0"), ("距36M高點回撤", "dd"), ("成交量", "vol"),
               ("前12M報酬", "r12"), ("距36M低點漲幅", "off_low")):
    v = sorted([r for r in rows if r[k] is not None], key=lambda r: r[k])
    q = len(v)//5
    cs = []
    for i in range(5):
        s = v[i*q:(i+1)*q] if i < 4 else v[4*q:]
        cs.append(sum(1 for x in s if x["ret"] > 1)/len(s)*100)
    print(f"  {lab:<14} " + "  ".join(f"{c:5.1f}%" for c in cs) + f"   (基準 {base:.1f}%)")

print("\n─ 全台股前 20 名 ─")
for r in sorted(rows, key=lambda r: -r["ret"])[:20]:
    print(f"  {r['code']:<6}{r['name']:<10}{r['mkt']}  {r['ind']:<12}"
          f"起價{r['px0']:>8.1f}  {r['ret']*100:>7.0f}%  回撤{r['dd']*100:>3.0f}%")
