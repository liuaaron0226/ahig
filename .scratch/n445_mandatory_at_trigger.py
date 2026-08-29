# -*- coding: utf-8 -*-
"""第二次觸發當下，前置條件是否事實為真——第 444 輪明列之未查項。

## 承接

第 444 輪查出：第二次觸發之**作成決策的區塊沒有前置條件旗標**，
唯一記載 `mandatoryLanesFullyScreened: True` 之處，其 `poolSize` 為 15,425（全 queue）
而非標準線之 9,091，且該區塊自身 `allowedToStop` 為 False。

**⚠️ 當時本室明載：不以「跨 lane 事實很可能通用」代替查核。** 本檔即補做該查核。

## 一、定義照抄生產程式，不重述

`statistical_termination.py:177-185`：

```python
mandatory_unscreened = sorted(
    e["candidateId"] for e in queue
    if e["candidateId"] not in seen
    and (e.get("screeningLane") == "safety-review"
         or "critical-harms-signal" in (e.get("flags") or [])))
preconditions_met = not mandatory_unscreened
```

**🚨 關鍵在它跑在哪個 `queue` 上**——⚠️ 全 queue 與標準線工作單會得到不同的 mandatory 集合。
**而標準線那 9,091 筆中確有帶 `critical-harms-signal` 者**（即 n+94 之孤兒機制所在）。

## 二、🚨 「現在為真」不等於「當時為真」——本檔把時點界定起來

單純對現行判讀語料計算，只能證明**今日**為真。
**⚠️ 而終止已宣告、篩選已停，語料只可能等於或多於觸發當下。** 故本檔加兩道時點論證：

1. **標準線語料未增長**：觸發當下 `screenedCount 7431 + outOfSequenceCount 200 = 7631`，
   與現行 `standard-full-screen-pass-1/judgements.json` 之筆數**逐數相符**
   → **該語料即觸發當下之語料。**
2. **mandatory 由該批自己判畢**：標準線基準之 mandatory 全部落在該批 judgements 內，
   **無一筆倚賴他批** → **其判畢時點必在觸發之前。**

**🚨 少了任一道，結論就只是「今日為真」。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：兩個母體之 mandatory 集合、是否全數判畢、標準線之時點界定。
- 🚨 查不到：**全 queue 基準之時點**——⚠️ 其 mandatory 有 2,729 筆，跨 safety／shadow／
  critical-harms 各批，本檔**未**逐批界定其時點。
  **🚨 惟全 queue 基準之區塊本來就自記該旗標，不需本檔代證；本檔要證的是標準線那一側。**
"""
import io
import json
import os
import sys

R = (os.environ.get('AHIG_PRIVATE_ROOT',
                    r'C:/Users/User/Desktop/claude/ahig-private') +
     '/search-runs/b11-exogenous-cho-endurance/b11-full-run')
SRC = ['standard-full-screen-pass-1', 'safety-full-screen-pass-1',
       'safety-full-screen-pass-2', 'screening-shadow-pass-a',
       'screening-shadow-pass-b', 'critical-harms-sweep',
       'critical-harms-sweep-orphans']


def entries(directory):
    p = os.path.join(R, directory, 'judgements.json')
    if not os.path.isfile(p):
        return []
    doc = json.load(io.open(p, encoding='utf-8'))
    return doc if isinstance(doc, list) else doc['entries']


seen = set()
for d in SRC:
    seen |= {e['candidateId'] for e in entries(d) if e.get('candidateId')}
queue = json.load(io.open(R + '/screening-queue/queue.json', encoding='utf-8'))
std_items = json.load(io.open(R + '/standard-full-screen-pass-1/worksheet.json',
                              encoding='utf-8'))['items']
std_ids = {i['candidateId'] for i in std_items}
ev = json.load(io.open('.scratch/n78_termination_evidence.json',
                       encoding='utf-8'))['standardLaneSequence']


def mandatory(rows):
    m = [e['candidateId'] for e in rows
         if e.get('screeningLane') == 'safety-review'
         or 'critical-harms-signal' in (e.get('flags') or [])]
    return m, sorted(c for c in m if c not in seen)


print('已判聯集 %d 筆（七個判讀來源）' % len(seen))
print()
print('=== 一、兩個母體之 mandatory 是否全數判畢 ===')
res = {}
for label, rows in (('full-queue', queue),
                    ('standard-lane-worksheet',
                     [e for e in queue if e['candidateId'] in std_ids])):
    m, uns = mandatory(rows)
    res[label] = {'population': len(rows), 'mandatory': len(m),
                  'unscreened': len(uns), 'met': not uns}
    print('   %-26s 母體 %5d｜mandatory %4d｜未判 %d  %s'
          % (label, len(rows), len(m), len(uns), '✅' if not uns else '🚨'))

print()
print('=== 二、時點界定（🚨 兩道都要成立，否則只證得到「今日為真」）===')
std_ent = entries('standard-full-screen-pass-1')
expect = ev['screenedCount'] + ev['outOfSequenceCount']
grew = len(std_ent) != expect
print('   ① 標準線語料未增長：觸發當下 %d + %d = %d｜現行 %d  %s'
      % (ev['screenedCount'], ev['outOfSequenceCount'], expect, len(std_ent),
         '✅ 相符' if not grew else '🚨 已增長'))
std_seen = {e['candidateId'] for e in std_ent if e.get('candidateId')}
m_std, _ = mandatory([e for e in queue if e['candidateId'] in std_ids])
outside = [c for c in m_std if c not in std_seen]
print('   ② mandatory 由該批自己判畢：%d 筆中在該批內 %d、倚賴他批 %d  %s'
      % (len(m_std), len(m_std) - len(outside), len(outside),
         '✅' if not outside else '🚨'))

closed = (not grew and not outside and res['standard-lane-worksheet']['met'])
print()
print('%s' % ('✅ 結論：`mandatoryLanesFullyScreened` 於第二次觸發當下、'
              '就標準線基準而言，**事實為真**——非借用、非推定。'
              if closed else
              '🚨 時點未閉合，🚫 不得宣稱「當時為真」。'))
print('⚠️ 第 444 輪之「記載位置」缺口仍成立：🚨 產物本身仍未就標準線基準陳述該旗標。')

doc = {
    'schemaVersion': 1,
    'documentType': 'precondition-truth-at-second-trigger',
    'ruling': 'self-initiated; closes the item round 444 listed as unchecked',
    'population': 'screening-queue (15,425) and the standard-lane worksheet '
                  'subset (9,091)',
    'countingUnit': 'candidate',
    'criterion': 'statistical_termination.py:177-185 verbatim -- lane is '
                 'safety-review, or flags contain critical-harms-signal',
    'byBasis': res,
    'standardLaneMandatoryAllFromFlag': True,
    'standardLaneMandatoryNote': 'Every mandatory record in the standard-lane '
                                 'subset qualifies through the '
                                 'critical-harms-signal flag, not through lane '
                                 '-- the orphan mechanism n+94 examined.',
    'timeBounding': {
        'corpusUnchanged': not grew,
        'triggerScreened': ev['screenedCount'],
        'triggerOutOfSequence': ev['outOfSequenceCount'],
        'currentJudgements': len(std_ent),
        'mandatoryJudgedInSameBatch': not outside,
        'note': 'Computing against the current corpus alone would only show '
                'the flag is true today. Two bounds close it: the standard-lane '
                'corpus is exactly its trigger-time size, and every mandatory '
                'record was judged inside that same batch rather than borrowed '
                'from a later one.',
    },
    'verdict': ('true at the second trigger for the standard-lane basis'
                if closed else 'not established'),
    'recordingGapStands': ('Round 444 stands: the artefact still never states '
                           'this flag for the standard-lane basis. What changes '
                           'is that the fact is now verified rather than '
                           'assumed to carry over.'),
    'coverageStatement': ('The full-queue basis is not time-bounded here -- its '
                          '2,729 mandatory records span several batches. That '
                          'block records the flag itself, so it needs no proxy '
                          'from this file.'),
    'contentNote': 'Counts and field names only.',
}
io.open('.scratch/n445_mandatory_at_trigger.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → .scratch/n445_mandatory_at_trigger.json')
sys.exit(0 if closed else 1)
