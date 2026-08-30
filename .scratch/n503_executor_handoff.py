# -*- coding: utf-8 -*-
"""執行室交辦三項之答覆，並把 18 格做成協調者接得上的單一檔案。

## 🚨 為什麼要有這一支：值產出來了，但沒有人接得到

`n500` 從第 500 輪起就能算出那 18 格。**⚠️ 而看板連續多輪仍寫「18 格待執行室」**，
n+160 更把本室列為「連續五輪無回應」。

> **🚨 產得出來 ≠ 交得出去。**
> ⚠️ 協調者之 `n154_cell_producer.py` 以 `RESOLVERS` 查值，**查不到就丟 `KeyError`**，
> 報告因而印出「⚠️〔待執行室量測〕」。**而它沒有任何一條路徑會去讀 `n500` 的產物。**

**✅ 故本檔輸出一個固定路徑、扁平、可直接查的檔**：`.scratch/executor_cells.json`。
**🚨 協調者只需加一條泛用 resolver**（讀該檔、取 `cells[name].value`），
**⚠️ 18 格一次全通，🚫 不必逐格寫解析器。**

**🚨 併記一條紀律**：該檔**帶產出時刻與輪次**。
⚠️ n+151（一）要求交付當日現算——**故消費端須把它當「執行室於某時之量測」，
🚫 不得當成永遠有效的常數。** 交付當日重跑本檔即刷新。

## 交辦三項

| 交辦 | 本檔如何答 |
|---|---|
| `9c2cc462` 之序列位次 | 以工作單之 `seq`／`page` 與 `contiguousPagesJudged` 對照 |
| `TAG_ROSTER_COUNT`／`TAG_ROSTER_TOTAL` | 已在 `n500`；本檔把它們送進交接檔 |
| `n450` 門檻值 | **🚨 更正一項前提**——見下 |

### 🚨 `n450` 門檻值：**它有存**，前提須更正

n+156 記「`n450` 自己寫著門檻只用來排序，且**未存門檻值**」。
**⚠️ 前半正確，後半不是**：`n450_landing_survey.json` 之 `criterion` 明載
**「a de-tagged word count with an **8000**-word threshold」**，
**🚨 門檻值就在產物裡。**

**⚠️ 而 `LANDING_WORTH_PARSER ＝ 0` 亦非「因為門檻沒存所以算不出」**：
`fulltext-likely` 之判準是**全文容器標記 ＋ 字數 ≥ 8000 兩者皆須成立**，
**🚨 而 33 筆中有 5 筆字數過門檻卻沒有標記**（歸類為 `pdf-only`）。
**✅ 故 0 是一個真的量測：沒有任何一頁同時具備兩個訊號。**

> **⚠️ 因此「若門檻本就不是決定規則則該格作廢」這條退路不適用**——
> **🚨 門檻確實是分類規則的一半；`thresholdNote` 說的是「這個分類不等於斷言全文存在」，
> 不是「門檻沒有參與決定」。**
> **🚫 是否仍要作廢該格屬裁定，本室只更正事實。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 給得出：三項交辦之答案，及 18 格之單一交接檔。
- 🚨 給不出：**4 格仍產不出**（needs-ruling／needs-extraction／needs-judgement），
  ⚠️ 於交接檔中以 `blocked` 標記並附阻礙，**🚫 不留空白**——空白會被讀成零。
- ⚠️ 交接檔是**快照**：🚨 值隨私有根變動，故帶輪次與時刻，交付當日須重跑。
"""
import io
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, 'ahig')
# 🚨 n+162（九之二）：來源不在就拒絕產出，🚫 不得寫入任何值。
# ⚠️ 原本這裡是 `os.environ.setdefault(...)`——那行在別台機器上會
#    「成功」地把根設成一個不存在的路徑，🚨 於是本支量到零並落盤，
#    而「量到零」與「量不到」在檔案裡長得一模一樣。
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require('search-runs/b11-exogenous-cho-endurance/b11-full-run')
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
RUN = (Path(os.environ['AHIG_PRIVATE_ROOT']) / 'search-runs' /
       'b11-exogenous-cho-endurance' / 'b11-full-run')
ROUND = 503


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


print('=== 執行室交辦答覆 ＋ 18 格交接檔（第 %d 輪）===' % ROUND)
print()

# ── 一、`9c2cc462` 之序列位次 ────────────────────────────────────
print('一、`9c2cc462` 之序列位次（n+152 二所留之待裁）')
w = jload(RUN / 'standard-full-screen-pass-1' / 'worksheet.json')
j = jload(RUN / 'standard-full-screen-pass-1' / 'judgements.json')
ev = jload(S + 'n78_termination_evidence.json')
judged = {e['candidateId'] for e in j['entries']}
item = next((i for i in w['items'] if i['candidateId'].endswith('9c2cc462')), None)
cont = ev['standardLaneSequence']['contiguousPagesJudged']
if item is None:
    sys.exit('🚨 工作單內找不到 9c2cc462——🚫 中止，不臆測。')
by_page = {}
for i in w['items']:
    d = by_page.setdefault(i['page'], [0, 0])
    d[0] += 1
    d[1] += i['candidateId'] in judged
# 🚨 控制：最大連續完整頁須自行算出並與 evidence 所載相符，
# ⚠️ 否則「它在連續段之外」這句話是靠一個沒被驗過的數字撐著。
calc = 0
for p in range(1, max(by_page) + 1):
    n, k = by_page.get(p, (0, 0))
    if n and n == k:
        calc = p
    else:
        break
ok = (calc == cont)
print('   %s 控制：自算最大連續完整頁 %d ｜ evidence 所載 contiguousPagesJudged %d'
      % ('✅' if ok else '🚨', calc, cont))
if not ok:
    sys.exit('🚨 兩者不符——🚫 不據以作答。')
tot_after = sum(n for p, (n, _) in by_page.items() if p > cont)
jud_after = sum(k for p, (_, k) in by_page.items() if p > cont)
pn, pk = by_page[item['page']]
unjudged = len(w['items']) - len(judged)
pos = {
    'candidateIdTail': '9c2cc462', 'seq': item['seq'], 'page': item['page'],
    'contiguousPagesJudged': cont, 'pagesBeyondFront': item['page'] - cont,
    'itemsBeyondFront': tot_after, 'judgedBeyondFront': jud_after,
    'ownPageJudged': '%d/%d' % (pk, pn),
    'unjudgedWorksheetItems': unjudged,
    'tailSpotCheckPopulation': ev['tailSpotCheckPopulation']['count'],
}
print('   seq %d｜第 %d 頁——🚨 連續判讀止於第 %d 頁，故它在連續段之外 %d 頁。'
      % (item['seq'], item['page'], cont, item['page'] - cont))
print('   連續段之後共 %d 筆，僅 %d 筆（%.1f%%）有判讀；其所在頁 %s。'
      % (tot_after, jud_after, 100.0 * jud_after / tot_after, pos['ownPageJudged']))
print('   ✅ 工作單未判讀者 %d 筆，與 `tailSpotCheckPopulation` 所載 %d %s。'
      % (unjudged, pos['tailSpotCheckPopulation'],
         '相符' if unjudged == pos['tailSpotCheckPopulation'] else '🚨 不符'))
print('   🚨 結論：它未被判讀，是因為**篩選在抵達它之前即依統計停止**，')
print('      ⚠️ 🚫 不是漏判，🚫 也不是被排除——它是那 %d 筆未判讀之一。' % unjudged)
print('   ⚠️ 本室只給位次事實；🚫 是否補判屬裁定。')
print()

# ── 二、`n450` 門檻值：更正前提 ──────────────────────────────────
print('二、`n450` 門檻值（n+156 交辦）')
sv = jload(S + 'n450_landing_survey.json')
rows = sv['records']
words = sorted(r['textWords'] for r in rows if isinstance(r.get('textWords'), int))
over = [r for r in rows if isinstance(r.get('textWords'), int)
        and r['textWords'] >= 8000]
likely = [r for r in rows if r.get('survey') == 'fulltext-likely']
print('   🚨 更正：門檻值**有存**——`criterion` 明載 8000。')
print('   ⚠️ 原文：%s' % sv['criterion'][-58:])
print('   ✅ `LANDING_WORTH_PARSER ＝ %d` 是真量測：判準要**標記＋字數**兩者，'
      % len(likely))
print('      🚨 而 %d／%d 筆字數過門檻卻無標記（歸 `pdf-only`）。' % (len(over), len(rows)))
print('   ✅ 字數三格（最小／中位／最大）：%d ／ %d ／ %d'
      % (words[0], words[len(words) // 2], words[-1]))
n450 = {'thresholdWords': 8000, 'thresholdIsStored': True,
        'thresholdSource': 'n450_landing_survey.json criterion',
        'fulltextLikely': len(likely), 'overThresholdWithoutMarker': len(over),
        'wordsMin': words[0], 'wordsMedian': words[len(words) // 2],
        'wordsMax': words[-1], 'surveyed': len(rows)}
print()

# ── 三、18 格交接檔 ─────────────────────────────────────────────
print('三、18 格交接檔')
n500 = jload(S + 'n500_inaccessible_cells.json')
if n500.get('listDrift'):
    sys.exit('🚨 `n500` 自報清單漂移——🚫 先修 n500 再產交接檔。')
cells = {}
for name, e in n500['cells'].items():
    if e.get('producible'):
        cells[name] = {'value': e['value'], 'kind': 'measured',
                       'population': e.get('population', ''),
                       'note': e.get('note', '')}
    else:
        cells[name] = {'value': None, 'kind': 'blocked',
                       'blocker': e.get('blocker', ''),
                       'blockerKind': e.get('blockerKind', '')}
measured = sum(1 for v in cells.values() if v['kind'] == 'measured')
print('   可量測 %d 格｜受阻 %d 格（🚫 受阻者留 `blocked` 標記，不留空白——'
      '⚠️ 空白會被讀成零）' % (measured, len(cells) - measured))
print('   🚨 消費方式：讀 `.scratch/executor_cells.json` → `cells[<格名>].value`；')
print('      ⚠️ `kind == "blocked"` 者請印其 `blocker`，🚫 不要印空字串。')

stamp = time.strftime('%Y-%m-%dT%H:%M:%S%z')
hand = {
    'schemaVersion': 1,
    'documentType': 'executor-cell-handoff',
    'ruling': 'n+151(1) assigns these cells to the executor room; n+160 recorded '
              'them as stalled. They were producible from round 500 but nothing '
              'on the coordinator side reads that artefact, so this is the file '
              'a single generic resolver can read.',
    'producedAtRound': ROUND,
    'producedAt': stamp,
    'isSnapshot': True,
    'snapshotNote': 'Values are measurements taken at producedAt against the '
                    'private root. n+151(1) requires delivery-day figures, so '
                    're-run n500 then this file on the day; do not treat these '
                    'as constants.',
    'howToConsume': 'cells[<name>].value for kind == "measured"; for kind == '
                    '"blocked" print blocker rather than an empty string, since '
                    'an empty cell reads as zero.',
    'cellCount': len(cells),
    'measured': measured,
    'cells': cells,
    'terminationPosition': pos,
    'n450Threshold': n450,
    'contentNote': 'Cell names, counts and positions only. No literature content.',
}
hand['handoffHash'] = content_hash({k: v.get('value') for k, v in cells.items()})
io.open(S + 'executor_cells.json', 'w', encoding='utf-8').write(
    json.dumps(hand, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sexecutor_cells.json（%d 格，產出時刻 %s）'
      % (S, len(cells), stamp))
