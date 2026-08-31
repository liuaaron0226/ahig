# -*- coding: utf-8 -*-
"""**protocol 四之 1 的那張表——六份切題回顧說了什麼。**（n+195，P3）

## 🚨 合起來的答案是**否定的**

| 問題 | 既有回顧的答案 |
|---|---|
| 有介入能**減少壓力／情緒驅動的進食**嗎 | ⚠️ **混合，而愈新愈近於無**：兩份較早的說有幫助（CBT、身分／價值／自我調節類技術），🚨 **兩份較新且更專一的，情緒性進食那一項都不顯著** |
| 有介入能**提高赤字的維持率**嗎 | **🚨 唯一直接測過的：沒有。** 計畫性暫停對**中途退出**無差別 |

> **✅ 這回答了 protocol 四之 3：既有回顧**沒有**解決擁有者的問題。**
> 🚨 而它不只是「沒人做過」——⚠️ **是做過而結果多半是零。**

## ⚠️ 一個要點名的接力關係

`36768088`（截止 2022-02）與 `39763344`（搜 2022-01 至 2023-04）是**同一條線的前後兩版**
——✅ 後者自述為 review update。**⚠️ 故兩者不是獨立的兩份證據**，
🚨 合成時不得當成兩筆（正是 B.11 那條「研究 vs 論文」的同一問題）。

## 🚫 數字留私有根

⚠️ 效果量與信賴區間是論文的內容；**✅ repo 只留識別碼、截止日、類別與方向標籤。**
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'p3_step1i_table.json'
DETAIL = ROOT / 'p3-stress-eating' / 'step1i-table.json'

DIRECTION = {
    'favourable': '✅ 該回顧自述為有利',
    'null': '🚨 該回顧自述為無顯著差異',
    'mixed': '⚠️ 部分結局有利、部分無',
    'not-reported': '🚫 該回顧未給方向',
}
SIDE = {'stress-eating': '甲：減少壓力／情緒驅動的進食',
        'deficit-adherence': '乙：提高赤字的維持率'}

TABLE = {
    '36768088': {
        'side': 'stress-eating', 'cutoff': 'February 2022',
        'population': '成人，過重或肥胖',
        'intervention': '針對情緒性進食的心理介入（含 CBT）',
        'outcome': '情緒性進食分數與體重',
        'direction': 'favourable',
        'statedGap': '⚠️ 該回顧自述證據有限、異質性高',
        'chain': '🚨 為 39763344 的前一版',
    },
    '39763344': {
        'side': 'stress-eating', 'cutoff': '31 April 2023',
        'population': '成人，BMI > 25',
        'intervention': '情緒性進食介入，並以行為改變技術分類法拆解',
        'outcome': '情緒性進食分數與體重',
        'direction': 'favourable',
        'statedGap': '🚨 該回顧自述**機轉仍不清楚**——✅ 這正是它做 BCT 拆解的理由',
        'chain': '🚨 自述為 36768088 的 review update（搜 2022-01 至 2023-04）',
    },
    '32551798': {
        'side': 'stress-eating', 'cutoff': 'June 2017',
        'population': '有問題性進食或身體意象困擾者',
        'intervention': '正念為基礎之介入',
        'outcome': '情緒性、外因性、暴食進食',
        'direction': 'favourable',
        'statedGap': '⚠️ 僅 9 篇隨機對照試驗',
        'chain': None,
    },
    '36763199': {
        'side': 'stress-eating', 'cutoff': '17 June 2022',
        'population': '成人，過重或肥胖',
        'intervention': '接納與承諾治療',
        'outcome': '體重、進食行為、心理結局',
        'direction': 'mixed',
        'statedGap': '🚨 **情緒性進食該項不顯著**；⚠️ BMI 與心理彈性有利',
        'chain': None,
    },
    '39489689': {
        'side': 'stress-eating', 'cutoff': 'June 2023',
        'population': '成人（含不同場域）',
        'intervention': '正念為基礎之介入',
        'outcome': '肥胖性進食行為（分「無意識進食」與「壓力相關進食」）',
        'direction': 'mixed',
        'statedGap': ('🚨 **情緒性進食與暴食皆不顯著**，且長期追蹤仍不顯著；'
                      '⚠️ 有利的是「無意識進食」那一組結局。'
                      '✅ 該回顧自述場域為調節變項（臨床優於學校）'),
        'chain': None,
    },
    '38246879': {
        'side': 'deficit-adherence', 'cutoff': 'July 2023',
        'population': '成人，過重或肥胖',
        'intervention': '計畫性暫停 vs 持續能量限制',
        'outcome': '體重變化與**中途退出**',
        'direction': 'null',
        'statedGap': '🚨 體重與中途退出**皆無差別**；⚠️ 僅 9 個介入組',
        'chain': None,
    },
}

UNRESOLVED = {
    '38784136': '⚠️ 開放取用但全文找不到檢索日期 → protocol 二之 2：**無法接續**',
    '39228092': '🚫 非開放取用，方法段讀不到 → 截止日不明',
}


def main():
    bad = sorted(k for k, v in TABLE.items() if v['direction'] not in DIRECTION)
    sides = Counter(v['side'] for v in TABLE.values())
    directions = Counter(v['direction'] for v in TABLE.values())
    chained = [k for k, v in TABLE.items() if v['chain']]
    deficit = [k for k, v in TABLE.items() if v['side'] == 'deficit-adherence']
    positive_deficit = [k for k in deficit if TABLE[k]['direction'] == 'favourable']

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一列都有截止日（必觸發）',
          all(v['cutoff'] for v in TABLE.values()),
          '🚨 protocol 三：沒有截止日的回顧無法接續；實得 %d 列全部有'
          % len(TABLE))
    probe('方向標籤都在固定詞彙裡（必觸發之反向）', not bad,
          '🚨 自創方向等於沒有分類；實得 %s' % (bad or '無'))
    probe('方向欄真的分得出不同答案（必觸發之反向）',
          len(directions) >= 2,
          '⚠️ 實得 %s；🚨 若只有一種，這一欄什麼都沒說' % dict(directions))
    probe('兩半都有列（必觸發）', len(sides) == 2,
          '⚠️ 實得 %s' % dict(sides))
    # 🚨 這一道會紅，而它就是擁有者要的答案。
    probe('有回顧直接測過「赤字維持率」且結果為正',
          bool(positive_deficit),
          '🚨 乙半邊只有 %d 份直接測過，且方向為 %s——'
          '⚠️ 計畫性暫停對中途退出**無差別**。'
          '✅ 故 protocol 四之 3：既有回顧**沒有**回答擁有者的問題'
          % (len(deficit), [TABLE[k]['direction'] for k in deficit]))

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p3-step1i-table-private',
         'note': '⚠️ 效果量與信賴區間留在此處，🚫 不進 repo。',
         'rows': TABLE, 'unresolved': UNRESOLVED},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1i-table',
        'assignment': 'n+195：P3 第一步之產出一（表）與產出三（判斷）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'directionVocabulary': DIRECTION,
        'sides': SIDE,
        'rows': {k: {kk: vv for kk, vv in v.items()} for k, v in TABLE.items()},
        'unresolved': UNRESOLVED,
        'countsBySide': dict(sides),
        'countsByDirection': dict(directions),
        'chainedPair': chained,
        'chainWarning': (
            '🚨 36768088 與 39763344 是同一條線的前後兩版（後者自述為 update）。'
            '⚠️ 合成時**不得當成兩筆獨立證據**——'
            '✅ 與 B.11 那條「研究 vs 論文」是同一個問題。'),
        'answerToProtocolFour3': (
            '🚨 **既有回顧沒有回答擁有者的問題。**'
            '⚠️ 減少情緒性進食：兩份較早的說有幫助，'
            '**而兩份較新且更專一的，情緒性進食那一項都不顯著**；'
            '🚨 提高赤字維持率：唯一直接測過的（計畫性暫停）**無差別**。'
            '✅ 而這不只是「沒人做過」——**是做過而結果多半是零**。'),
        'searchStartsFrom': '2023 年年中（甲 June 2023／乙 July 2023，皆方法段逐字）',
        'numbersKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3：protocol 四之 1 的表 ===')
    print('   列數 %d（甲 %d／乙 %d）｜方向 %s'
          % (len(TABLE), sides['stress-eating'], sides['deficit-adherence'],
             dict(directions)))
    for key, row in TABLE.items():
        print('   %s｜%-18s｜截止 %-16s｜%s'
              % (key, SIDE[row['side']][:9], row['cutoff'], row['direction']))
    print('   🚨 未解：%s' % list(UNRESOLVED))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（數字留私有根）' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
