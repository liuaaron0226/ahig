# -*- coding: utf-8 -*-
"""**抽哪一欄，會讓哪幾道把關活過來。**（第 719 輪）

## ✅ 把第 718 輪那件事一般化

n718 查出：`STAT-012`（交叉設計誤用獨立樣本公式）**對每一項都不適用**，
因為清冊裡沒有 `studyDesign`。

> **🚨 那就要問：`run_all` 裡還有多少道，在現有欄位下是死的？**

## ✅ 做法：逐階把欄位加回去，看判定怎麼變

- **第 0 階**：只有清冊真的有的（`analysisSet`／`effectMeasure`，第 676 輪）
- **第 1 階**：＋第 676 輪證過的最小集（點估計、區間、樣本數）
- **第 2 階**：＋設計與分析方式（第 718 輪那道）
- **第 3 階**：＋檢定統計量與 p 值
- **第 4 階**：＋事件數與各臂人數
- **第 5 階**：＋各臂描述統計
- **第 6 階**：＋逐項描述統計（GRIM／GRIMMER）

⚠️ 每一階都是**前一階的超集**，🚨 故「新亮起來的規則」就是那一階換到的東西。

## 🚫 本支不改產品程式、不改任何清冊、不送外部請求

✅ 資料全是本支現造的合成值，🚫 不含任何文獻內容。
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.stats import deterministic as det  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n719_field_to_check_map.json'

STAGES = [
    ('第 0 階・清冊現有', {
        'analysisSet': 'complete-case', 'effectMeasure': 'mean'}),
    ('第 1 階・＋最小數值集', {
        'pointEstimate': 2.0, 'ciLow': 0.5, 'ciHigh': 3.5,
        'nSubjects': 12}),
    ('第 2 階・＋設計與分析方式', {
        'studyDesign': 'RCT-crossover', 'analysisReported': 'paired t-test'}),
    ('第 3 階・＋檢定統計量與 p 值', {
        'testStatistic': {'type': 't', 'value': 2.6, 'df1': 11},
        'pValue': 0.024}),
    ('第 4 階・＋事件數與各臂人數', {
        'events': [4, 9], 'armN': [12, 12]}),
    ('第 5 階・＋各臂描述統計', {
        'armDescriptives': {'m1': 10.0, 'sd1': 2.0, 'n1': 12,
                            'm2': 8.0, 'sd2': 2.2, 'n2': 12},
        'smdType': 'hedges_g'}),
    ('第 6 階・＋逐項描述統計', {
        'descriptives': [{'mean': '10.0', 'sd': '2.0', 'n': 12}]}),
]


def summarise(sr):
    result = det.run_all(dict(sr))
    by_verdict = collections.Counter(c.verdict for c in result['checks'])
    live = {c.rule_id for c in result['checks']
            if c.verdict != 'NOT_APPLICABLE'}
    return {'checks': result['n_checks'],
            'byVerdict': dict(by_verdict.most_common()),
            'liveRules': sorted(live)}


def main():
    sr = {}
    rows = []
    previous_live = set()
    for label, fields in STAGES:
        sr.update(fields)
        info = summarise(sr)
        live = set(info['liveRules'])
        rows.append({
            'stage': label,
            'fieldsAdded': sorted(fields),
            'checksRun': info['checks'],
            'byVerdict': info['byVerdict'],
            'liveRules': info['liveRules'],
            'newlyLive': sorted(live - previous_live),
            'liveCount': len(live),
        })
        previous_live = live

    stage0 = rows[0]
    final = rows[-1]
    stat012 = 'STAT-012-paired-vs-independent'

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一階都跑得出檢查（必觸發之正對照）',
          all(r['checksRun'] > 0 for r in rows),
          '🚨 逐階的檢查數：%s；⚠️ 有 0 就代表那一階根本沒跑'
          % [(r['stage'], r['checksRun']) for r in rows])
    # 🚨 與第 718 輪對得起來：第 0 階不得讓 STAT-012 活著。
    probe('第 0 階時 `%s` 不是活的（必觸發之反向・與第 718 輪一致）' % stat012,
          stat012 not in stage0['liveRules'],
          '🚨 第 0 階活著的規則：%s；'
          '⚠️ 若它已經活著，就與第 718 輪的實測矛盾' % stage0['liveRules'])
    probe('加回設計欄之後它會活過來（必觸發之正對照）',
          any(stat012 in r['newlyLive'] for r in rows),
          '🚨 `%s` 在哪一階活過來：%s；'
          '⚠️ 若一直沒活，代表本支的合成值沒觸發它'
          % (stat012,
             [r['stage'] for r in rows if stat012 in r['newlyLive']] or '無'))
    # 🚨 這一道是答案。
    probe('清冊現有的欄位已經讓所有把關活著',
          stage0['liveCount'] == final['liveCount'],
          '🚨 第 0 階活著 %d 道，全部欄位到齊時活著 %d 道——'
          '**⚠️ 現況下有 %d 道把關是死的**；'
          '🚫 而那不是它們壞了，是**沒有資料經過它們**'
          % (stage0['liveCount'], final['liveCount'],
             final['liveCount'] - stage0['liveCount']))

    doc = {
        'schemaVersion': 1,
        'documentType': 'field-to-check-map',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'generalises': 'n718（STAT-012 對每一項都不適用）',
        'stages': rows,
        'liveAtStage0': stage0['liveCount'],
        'liveWhenComplete': final['liveCount'],
        'dormantToday': final['liveCount'] - stage0['liveCount'],
        'whatThisGivesD25': (
            '✅ 一張**欄位 → 把關**的對照：'
            '🚨 抽哪一階，就換到哪幾道確定性檢查。'
            '⚠️ 第 676 輪的兩層（合併得動／驗得動）是粗的；'
            '**✅ 這裡把「驗得動」拆成有順序的階梯，'
            '每一階都寫明它讓哪幾道規則活過來。**'),
        'contentDiscipline': (
            '✅ 資料全是本支現造的合成值，🚫 不含任何文獻內容（n+195 一）。'),
        'methodLimit': (
            '🚨 「活著」＝該道檢查回傳的判定**不是** `NOT_APPLICABLE`——'
            '⚠️ 它**不保證**那道檢查在真實資料上會抓到東西。'
            '🚫 又：本支用的是**一組**合成值，'
            '**若換一組值，某些階的活躍規則會不同。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n719 欄位 → 把關 的階梯 ===')
    for row in rows:
        print('   %-24s 跑 %2d 道｜活 %2d 道｜%s'
              % (row['stage'], row['checksRun'], row['liveCount'],
                 row['byVerdict']))
        if row['newlyLive']:
            print('      新亮起來：%s' % row['newlyLive'])
    print('   🚨 現況（第 0 階）活著 %d 道；欄位到齊時 %d 道——'
          '故現在有 %d 道把關是死的'
          % (stage0['liveCount'], final['liveCount'],
             final['liveCount'] - stage0['liveCount']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
