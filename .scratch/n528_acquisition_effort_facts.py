# -*- coding: utf-8 -*-
"""取得階段實際花了多久：**「不到兩小時」對什麼為真，對什麼不為真。**

## 🚨 為什麼此刻要量這個

`n180` 之工時估算把取得階段記為「**不到兩小時**」，
**⚠️ 而擁有者正要據那份估算決定要不要多開幾條線。**

**✅ 那個數對「抓檔與落盤」為真**——本檔實測後確認。
**🚨 而它對「B.11 的取得階段整體」不為真**，理由是一件可量的事實：
**⚠️ 41 份是由兩條路取得的，而第二條路在第一條跑完時並不存在。**

## ✅ 實測（🚫 不憑印象，取產物之寫入時刻）

| 路徑 | 份數 | sections 檔寫入區間 |
|---|---|---|
| `europe-pmc-jats` | 26 | 2026-08-18 07:43 → 07:57（**14 分**） |
| `grobid-tei` | 15 | 2026-08-29 22:29（**同一秒內**） |

**⚠️ 兩批相隔 11 天。**
**🚨 而第二批之所以能在一秒內落盤，是因為 PDF 下載、GROBID 安裝與驗收
都在那之前分別做完了**——⚠️ 那些不在「不到兩小時」裡面。

> **🚨 換句話說：那兩小時量的是最後一哩，🚫 不是那條路的造價。**

## 🚨 這對 P1 的估算是什麼意思（🚫 本檔不改估算）

- ✅ **下界仍站得住**：兩條路現在都存在，P1 不必重造。
- 🚨 **而估算裡沒有一項對應「來源兩條路都吃不下」**——
  ⚠️ 而 B.11 自己的歷史就是那個項目非假想的證據：
  **🚨 第二條路當初也不在計畫裡，是撞到付費牆與機器人阻擋之後才長出來的。**

**🚫 本檔不給那一項該是多少**——⚠️ 一次樣本估不出分布；
**✅ 只指出它現在是 0，而 B.11 的實際值不是 0。**

## 🚨 控制探針

**⚠️ 一個讀不到時刻的量測，會讓每個區間都變成 0 分——而那看起來像「很快」。**
**✅ 故驗兩件**：兩條路之寫入時刻須**不同**（證明時刻讀得到、且不是常數）；
份數須等於獨立量得之 41。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 量得到：產物落盤之時刻與其區間。
- 🚨 量不到：**人在中間花的時間**——⚠️ 安裝、除錯、等待裁定都不落盤，
  **🚫 故本檔給的是下界，不是工時。**
- ⚠️ 檔案時刻可被複製或搬運改寫；**🚨 本語料未經搬運（第 519 輪查過無不明編輯），
  故此處採用之，🚫 但那是一個前提而非保證。**
"""
import io
import json
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
AD = re.compile(r'-[0-9a-f]{16}$')


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def iso(t):
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t))


by_route = defaultdict(list)
total = 0
for d in sorted(p for p in (PRIVATE_ROOT / 'fulltext').iterdir()
                if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') != 'acquired':
        continue
    for a in (m.get('artifacts') or []):
        total += 1
        sf = d / (a.get('sectionsFile') or '')
        if sf.name and sf.exists():
            by_route[a.get('sourceType')].append(sf.stat().st_mtime)

print('=== 取得階段之實測時刻（🚫 唯讀）===')
print()
print('一、控制探針——🚨 未過即不報區間')
routes = sorted(by_route)
starts = {r: min(by_route[r]) for r in routes}
distinct = len({round(v) for v in starts.values()}) == len(routes)
n496 = jload(S + 'n496_corpus_verify.json')
count_ok = total == n496.get('acquired')
print('   %s 兩條路之起始時刻不同 ＝ %s（🚨 否則時刻可能根本沒讀到）'
      % ('✅' if distinct else '🚨', distinct))
print('   %s 份數 %d ＝ `n496` 獨立量得之 %s'
      % ('✅' if count_ok else '🚨', total, n496.get('acquired')))
if not (distinct and count_ok):
    sys.exit('🚨 控制探針未過——🚫 不報區間。')
print('   ✅ 兩道皆過。')
print()

print('二、逐路徑')
rows = []
for r in routes:
    v = sorted(by_route[r])
    span = (v[-1] - v[0]) / 60.0
    rows.append({'route': r, 'records': len(v), 'firstWritten': iso(v[0]),
                 'lastWritten': iso(v[-1]), 'spanMinutes': round(span, 1)})
    print('   %-18s %2d 筆｜%s → %s｜跨 %.0f 分'
          % (r, len(v), iso(v[0]), iso(v[-1]), span))
gap = (min(by_route[routes[-1]]) - max(by_route[routes[0]])) / 86400.0
print('   ' + '-' * 62)
print('   🚨 兩批相隔 %.1f 天' % abs(gap))
print()

print('三、🚨 「不到兩小時」對什麼為真')
print('   ✅ 對**抓檔與落盤**為真：兩批各自 14 分與同一秒內。')
print('   🚨 對**取得階段整體**不為真——⚠️ 41 份由兩條路取得，')
print('      而第二條路在第一條跑完時**並不存在**（相隔 %.0f 天）。' % abs(gap))
print('   ⚠️ 第二批能在一秒內落盤，是因為 PDF 下載、GROBID 安裝與驗收')
print('      都在那之前分別做完了——🚨 那些不在那兩小時裡面。')
print()
print('四、⚠️ 對 P1 估算的意思（🚫 本檔不改估算）')
print('   ✅ 下界仍站得住：兩條路現在都在，P1 不必重造。')
print('   🚨 而估算裡沒有一項對應「來源兩條路都吃不下」——')
print('      ⚠️ 而 B.11 自己就是那一項非假想的證據：')
print('      🚨 第二條路當初也不在計畫裡，是撞到付費牆與機器人阻擋之後才長出來的。')
print('   🚫 本檔不給那一項該是多少——⚠️ 一次樣本估不出分布。')

doc = {
    'schemaVersion': 1,
    'documentType': 'acquisition-effort-facts',
    'ruling': 'n+179(4) records acquisition as "under two hours" in an estimate '
              'the owner is about to use to decide whether to open more lines; '
              'this measures what that figure covers',
    'population': 'artifacts of acquired manifests under the private root',
    'countingUnit': 'artifact',
    'criterion': 'filesystem write time of each sections document, grouped by '
                 'acquisition route',
    'controlProbes': {'routeStartsDiffer': distinct, 'countMatchesN496': count_ok,
                      'why': 'A measurement that cannot read times reports every '
                             'span as zero, which reads as "fast".'},
    'routes': rows,
    'daysBetweenBatches': round(abs(gap), 1),
    'trueOf': 'fetching and writing -- 14 minutes for one batch, within one '
              'second for the other',
    'notTrueOf': 'the acquisition phase as a whole: 41 records came through two '
                 'routes, and the second did not exist when the first ran. The '
                 'second batch landed in a second because the PDF downloads, the '
                 'GROBID install and its acceptance had all been done separately '
                 'beforehand, and none of that is inside the two hours.',
    'forTheP1Estimate': 'The lower bound holds -- both routes exist now. What the '
                        'estimate has no term for is a source neither route '
                        'handles, and B.11 is the evidence that such a term is '
                        'not hypothetical: the second route was itself unplanned, '
                        'built after hitting paywalls and bot blocking. This does '
                        'not propose a value for that term; one sample cannot '
                        'give a distribution.',
    'coverageStatement': 'Write times are a lower bound on effort: installing, '
                         'debugging and waiting for rulings leave no artefact. '
                         'File times can be rewritten by copying, and this corpus '
                         'is taken as unmoved on the evidence of round 519 -- a '
                         'premise, not a guarantee.',
    'contentNote': 'Route names, counts and timestamps only.',
}
doc['effortHash'] = content_hash({r['route']: r['spanMinutes'] for r in rows})
io.open(S + 'n528_acquisition_effort_facts.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn528_acquisition_effort_facts.json' % S)
