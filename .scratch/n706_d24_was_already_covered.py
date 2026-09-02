# -*- coding: utf-8 -*-
"""**`D24` 是本室重複登記的——而且它的前提是錯的。**（第 706 輪）

## 🚨 怎麼發現的

第 705 輪剩下 29 對候選連鎖，本室挑了 `D2`／`D24`（兩者都卡 A4、主題相鄰）來逐對算。
✅ 一讀 `D2` 的證據 `n585_blocked_drafts_errata.json`，就看到：

> 那份更正表**早就有那一條改名**：
> `cycling-time-to-exhaustion-fixed-power` → `cycling-tte-fixed-intensity`
> （`rename-safe`、6 項、涵蓋 `7a6ac1559c740fd6` 與 `f6a82302d7fe9adf`）。

**🚨 而本室在第 669 輪把同一件事新增成 `D24`。**

## 🚨 更糟的是，`D24` 的**前提**也不對

本室當時是從**機械性突變**推出「這是同義字問題」：
第 665 輪把儀器欄換成同結局的合格值，那 7 項就進得了範圍。

**⚠️ 但「換成一個合格的值會進來」🚫 不等於「那篇論文用的就是那個工具」。**

✅ 而 `n585` 是**讀過論文**之後分類的：

| 篇 | `n585` 的分類 | 意思 |
|---|---|---|
| `7a6ac`（力竭時間） | `rename-safe` | ✅ 真的只是用詞不同 |
| `7a6ac`（肌肝醣） | `rename-needs-ruling` | 🚨 而 `D4` 已裁**不改** |
| `298c` | **`contract-gap`** | 🚨 契約**沒有滑雪類**工具 |
| `9a3b` | **`contract-gap`** | 🚨 同上 |

> **🚨 那兩篇不是同義字問題，是契約缺口——🚫 而 `D24` 把它們當成同一件事問。**

## ✅ 而第 670 輪的索引其實指出過

第 670 輪的「早該先讀」欄位就寫著 `n663 → n585 [D2]`。
**⚠️ 本室當時只把它當成一個統計數字，🚫 沒有真的去讀 n585。**

## 🚫 本支不刪除任何決定（登記簿的處置另出一版）、不送外部請求
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n706_d24_was_already_covered.json'
N585 = HERE / 'n585_blocked_drafts_errata.json'
N665 = HERE / 'n665_blocked_gate_depth.json'


def main():
    errata = json.loads(N585.read_text(encoding='utf-8'))
    gate = json.loads(N665.read_text(encoding='utf-8'))

    # ✅ D24 的範圍＝第 665 輪「單欄換儀器即可進範圍」的那些。
    d24_items = [r for r in gate['rows']
                 if r.get('singleFieldFixes') == ['儀器']]
    by_report = collections.Counter(r['report'] for r in d24_items)

    # ✅ n585 把每一篇怎麼分類。
    category_of = {}
    for row in errata['rows']:
        for report in row['reports']:
            category_of.setdefault(report, set()).add(row['category'])

    coverage = []
    for report, count in sorted(by_report.items()):
        cats = sorted(category_of.get(report, []))
        coverage.append({'report': report, 'itemsInD24': count,
                         'n585Categories': cats,
                         'coveredByErrata': bool(cats)})

    uncovered = [c for c in coverage if not c['coveredByErrata']]
    contract_gap = [c for c in coverage
                    if 'contract-gap' in c['n585Categories']]
    rename_safe = [c for c in coverage
                   if 'rename-safe' in c['n585Categories']]

    renames = {row['declaredInstrument']: row['correctTo']
               for row in errata['rows'] if row.get('correctTo')}

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('抓得到 `D24` 的範圍（必觸發之正對照）',
          len(d24_items) > 0,
          '🚨 第 665 輪「單欄換儀器即可進範圍」共 %d 項，分佈 %s；'
          '⚠️ 若是 0，本支沒有可比的對象'
          % (len(d24_items), dict(by_report)))
    probe('更正表裡真的有那一條改名（必觸發之正對照）',
          renames.get('cycling-time-to-exhaustion-fixed-power')
          == 'cycling-tte-fixed-intensity',
          '🚨 更正表的改名對照：%s；'
          '⚠️ 若沒有那一條，本支的「重複登記」指控就不成立' % renames)
    probe('捏造的工具名不在更正表裡（必觸發之反向）',
          'instrument-that-cannot-exist-706' not in renames,
          '🚨 捏造工具名不在表裡；⚠️ 若在，代表比對是在亂配')
    # 🚨 這一道是答案。
    probe('`D24` 涵蓋的篇，更正表都沒有處理過',
          not coverage or all(not c['coveredByErrata'] for c in coverage),
          '🚨 %d 篇裡有 %d 篇更正表**早就分類過**：%s；'
          '⚠️ 而其中 %d 篇被分為 `contract-gap`（契約沒有那類工具）——'
          '**🚨 那不是同義字問題，🚫 D24 問錯了**'
          % (len(coverage), len(coverage) - len(uncovered),
             [(c['report'], c['n585Categories']) for c in coverage],
             len(contract_gap)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd24-duplicate-and-wrong-premise',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'howFound': ('✅ 第 705 輪剩下的 29 對候選裡，挑了 `D2`／`D24` 逐對算——'
                     '🚨 一讀 `D2` 的證據就看到那條改名早就在表裡。'),
        'd24Items': len(d24_items),
        'd24ByReport': dict(by_report),
        'errataCoverage': coverage,
        'erratraRenameTable': renames,
        'contractGapReports': [c['report'] for c in contract_gap],
        'renameSafeReports': [c['report'] for c in rename_safe],
        'twoProblemsWithD24': {
            '一・重複登記': (
                '🚨 `n585`（`D2` 的證據）**早就有**'
                '`cycling-time-to-exhaustion-fixed-power` → '
                '`cycling-tte-fixed-intensity` 這條改名，'
                '⚠️ 而本室在第 669 輪把它新增成 `D24`。'),
            '二・前提錯誤': (
                '🚨 本室當時是從**機械性突變**推出「這是同義字問題」——'
                '⚠️ 但「換成一個合格的值會進來」🚫 不等於'
                '「那篇論文用的就是那個工具」。'
                '**✅ 而 `n585` 是讀過論文之後分類的：'
                '`298c` 與 `9a3b` 是 `contract-gap`（契約沒有滑雪類工具），'
                '🚫 不是同義字。**'),
        },
        'theToolDidWarnMe': (
            '⚠️ 第 670 輪的「早該先讀」欄位就寫著 `n663 → n585 [D2]`。'
            '**🚨 本室當時只把它當成一個統計數字，🚫 沒有真的去讀那一支。**'
            '✅ 工具有效，⚠️ 而使用者（本室）沒有照它的指示做。'),
        'proposedDisposition': (
            '📮 建議把 `D24` 標為**併入 `D2`**（🚫 不刪除），'
            '並把 `298c`／`9a3b` 那兩篇改掛到**契約缺口**那一線'
            '（第 573 輪已報「契約的計時賽工具只有自行車與跑步，沒有滑雪」）。'
            '⚠️ 本支只提建議，**📮 併不併是裁定**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n706 D24 早就被更正表涵蓋 ===')
    print('   D24 的範圍：%d 項，分佈 %s' % (len(d24_items), dict(by_report)))
    print('   更正表的分類：')
    for row in coverage:
        print('      %s｜D24 有 %d 項｜n585 分類 %s'
              % (row['report'], row['itemsInD24'], row['n585Categories']))
    print('   更正表的改名對照：')
    for old, new in renames.items():
        print('      %s → %s' % (old, new))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
