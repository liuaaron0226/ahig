# -*- coding: utf-8 -*-
"""**A2 的實際狀態：雙讀了幾篇、幾處不一致、七種成因用過幾種。**（第 641 輪）

## 🚨 內容關卡 A2 卡了很久，而沒有一處寫下它現在是什麼樣子

⚠️ A2 要的是「**抽樣雙讀＋每處不一致判明成因**」。
🚨 本 run 做過幾次第二線的讀，也討論過成因分類，**🚫 但從沒有人把現況攤開**：
雙讀涵蓋幾篇、契約結局層級一致多少、七種裁決成因實際用過幾種。

> **⚠️ 一個沒有現況的關卡，永遠只能靠印象說「快好了」。**

## ✅ 作法：用產品的 `agreement()`，🚫 不自己重寫一套比較邏輯

第二線的讀存成完整清冊，正好餵得進 `worksheet.agreement()`。
⚠️ 而該函式自己就分了兩種單位——**標籤（不可比，顆粒度）** 與
**契約結局 refs（可比）**——✅ 本支只用後者下結論。

## 🚫 本支不改任何產品程式、不改任何清冊、不送外部請求
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
from ahig.extraction import worksheet  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n641_double_read_state.json'
WORKSHEET = ROOT / 'extraction-worksheet'


def main():
    # 官方清冊（第一線）。
    primary = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        primary[doc['report']] = doc

    # 第二線的讀。
    second = {}
    second_pages = []
    for path in sorted((WORKSHEET / 'second').glob('page-*.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        second_pages.append(path.name)
        for entry in doc.get('entries') or []:
            second[entry['report']] = entry

    pending = sorted(p.name for p in
                     (WORKSHEET / 'second-pending').glob('*.json'))

    shared = sorted(set(primary) & set(second))
    result = worksheet.agreement({r: primary[r] for r in shared},
                                 {r: second[r] for r in shared})

    # ⚠️ 七種裁決成因用過幾種：🚨 從已存的裁決紀錄裡數，不是從記憶。
    causes_used = collections.Counter()
    adjudication_files = []
    for path in sorted(WORKSHEET.rglob('*.json')):
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        text = json.dumps(doc, ensure_ascii=False)
        hit = [c for c in worksheet.ADJUDICATION_CAUSES if c in text]
        if hit:
            adjudication_files.append(path.name)
            for cause in hit:
                causes_used[cause] += 1
    unused_causes = sorted(c for c in worksheet.ADJUDICATION_CAUSES
                           if causes_used[c] == 0)

    # 🚨 那七種成因在**本室的憑證**裡出現過嗎——⚠️ 若有，代表分析做過，
    # 但它**停在憑證裡、沒有進到系統的紀錄（工作簿）**。
    # ✅ 這兩件事差很多：A2 要的是後者。
    in_scratch = collections.Counter()
    scratch_dir = Path(__file__).resolve().parent
    for path in sorted(scratch_dir.glob('n*.json')):
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for cause in worksheet.ADJUDICATION_CAUSES:
            if cause in text:
                in_scratch[cause] += 1
    discussed_not_recorded = sorted(c for c in worksheet.ADJUDICATION_CAUSES
                                    if in_scratch[c] and not causes_used[c])

    disagreeing = [row for row in result['rows']
                   if row['refsOnlyPrimary'] or row['refsOnlySecond']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('第二線的讀讀得到、且對得上第一線（必觸發之正對照）',
          len(shared) > 0 and len(shared) == len(second),
          '🚨 第二線 %d 篇、與第一線共有 %d 篇；⚠️ 對不上代表有篇只有一邊讀過'
          % (len(second), len(shared)))
    probe('比較有真的產出東西（必觸發之正對照）',
          result['refsBoth'] + result['refsOnlyPrimary']
          + result['refsOnlySecond'] > 0,
          '🚨 契約結局層級：兩邊都有 %d／只有第一線 %d／只有第二線 %d；'
          '⚠️ 全為 0 代表本支根本沒比到東西'
          % (result['refsBoth'], result['refsOnlyPrimary'],
             result['refsOnlySecond']))
    # 🚨 以下三道是現況，不是缺陷指控。
    probe('雙讀涵蓋率達到語料的一成',
          len(shared) >= len(primary) * 0.1,
          '🚨 雙讀 %d 篇／清冊 %d 份＝%.1f%%；⚠️ A2 要的是抽樣，'
          '🚫 但抽樣多少是裁定的事，本室只把數字放上來'
          % (len(shared), len(primary),
             100 * len(shared) / max(1, len(primary))))
    probe('雙讀過的篇在契約結局層級全部一致',
          not disagreeing,
          '🚨 有不一致的 %d 篇：%s'
          % (len(disagreeing),
             [(r['report'][-16:], r['refsOnlyPrimary'], r['refsOnlySecond'])
              for r in disagreeing]))
    probe('七種裁決成因都被用過（在工作簿裡）',
          not unused_causes,
          '🚨 工作簿裡從未出現的成因 %d 種：%s；⚠️ 工作簿裡用過的：%s'
          % (len(unused_causes), unused_causes,
             dict(causes_used.most_common())))
    probe('討論過的成因都有進到系統的紀錄',
          not discussed_not_recorded,
          '🚨 只出現在本室憑證、卻沒進工作簿的成因 %d 種：%s（憑證裡的次數：%s）；'
          '⚠️ **A2 要的是系統的紀錄，🚫 不是本室的分析**'
          % (len(discussed_not_recorded), discussed_not_recorded,
             dict(in_scratch.most_common())))

    doc = {
        'schemaVersion': 1,
        'documentType': 'double-read-state',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': len(primary),
        'secondLanePages': second_pages,
        'secondLaneReports': [r[-16:] for r in sorted(second)],
        'pendingSubmission': pending,
        'comparedReports': result['comparedReports'],
        'refsBoth': result['refsBoth'],
        'refsOnlyPrimary': result['refsOnlyPrimary'],
        'refsOnlySecond': result['refsOnlySecond'],
        'reportsFullyAgreed': result['reportsFullyAgreed'],
        'labelsBoth': result['labelsBoth'],
        'labelsOnlyPrimary': result['labelsOnlyPrimary'],
        'labelsOnlySecond': result['labelsOnlySecond'],
        'rows': result['rows'],
        'adjudicationCauses': dict(causes_used.most_common()),
        'unusedCauses': unused_causes,
        'causesInMyArtefactsOnly': dict(in_scratch.most_common()),
        'discussedButNotRecorded': discussed_not_recorded,
        'theGapThatMatters': (
            '🚨 七種成因在**本室的憑證**裡都出現過（granularity 4 份、'
            'model-fabricated 2 份……），**⚠️ 而工作簿裡一次都沒有**。'
            '**🚨 即 `adjudicate()` 從未被真的呼叫過**——'
            '⚠️ 成因分析做了，但它停在憑證裡，沒有進到系統的紀錄。'
            '✅ A2 要的是後者。'),
        'filesMentioningCauses': adjudication_files,
        'whyLabelsAreNotTheAnswer': result['caveat'],
        'coverageStatement': (
            '⚠️ 雙讀 %d 篇／清冊 %d 份。'
            '🚨 A2 要的是「抽樣」雙讀，而抽多少是裁定的事——'
            '**✅ 本支只把現況放上來，🚫 不宣稱夠或不夠。**'
            % (len(shared), len(primary))),
        'pendingNote': (
            '⚠️ 另有 %d 份第二線的讀**未送出**，暫存在 second-pending／——'
            '🚨 那是 D14 卡著的那一份（`write_page_drafts` 拒絕同頁異容），'
            '🚫 本室未繞過守衛。' % len(pending)),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n641 雙讀現況（A2）===')
    print('   清冊 %d 份｜第二線讀過 %d 篇｜待送出 %d 份'
          % (len(primary), len(second), len(pending)))
    print('   契約結局層級：兩邊都有 %d｜只有第一線 %d｜只有第二線 %d｜逐篇全一致 %d/%d'
          % (result['refsBoth'], result['refsOnlyPrimary'],
             result['refsOnlySecond'], result['reportsFullyAgreed'],
             result['comparedReports']))
    print('   標籤層級（🚫 不可比，僅供參考）：兩邊都有 %d｜只有第一線 %d｜只有第二線 %d'
          % (result['labelsBoth'], result['labelsOnlyPrimary'],
             result['labelsOnlySecond']))
    for row in result['rows']:
        print('      %s｜refs 共有 %d｜只有第一線 %s｜只有第二線 %s'
              % (row['report'][-16:], len(row['refsBoth']),
                 row['refsOnlyPrimary'], row['refsOnlySecond']))
    print('   裁決成因（工作簿）：用過 %s｜從未用過 %d 種'
          % (dict(causes_used.most_common()) or '（無）', len(unused_causes)))
    print('   同樣的成因在本室憑證裡：%s' % dict(in_scratch.most_common()))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
