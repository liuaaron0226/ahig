# -*- coding: utf-8 -*-
"""**門口被擋下的那幾筆，到底該怎麼結清。**（第 585 輪，對 n+190 三之 A4）

## 🚨 盤過之後，A4 不是三筆的事

⚠️ 「有 draft 卻沒清冊」的確是 3 篇。**🚨 但把 41 篇的 `instrument` 全部對照契約之後，
名字對不上的是 7 種、26 項、6 篇**——⚠️ 其中一篇根本沒被擋下，
**它只是被判成「全部不在範圍內」，看起來像是一篇沒有結局的論文。**

## ✅ 四類，做的事完全不同——🚫 不可混為一談

| 類 | 意思 | 該做的事 |
|---|---|---|
| **甲 改名即可** | ⚠️ 論文的方法就是允許值，只是讀的人寫了別的名字 | ✅ 改名 |
| **乙 改名但要裁定** | 🚨 部分相符：部位對得上，但論文沒寫允許值裡的那個字 | 📮 裁定 |
| **丙 契約缺口** | ⚠️ 契約的允許清單裡**沒有**適用值 | 🚨 改契約，🚫 不是改讀的人 |
| **丁 撤回** | 🚨 **宣告本身就錯，改名救不了** | 🚫 撤回 |

## 🚨 丁那一類是 5 項，不是 1 項

n+190（三）A4 說「其中一筆是真的對錯結局（把平均功率宣告成完成時間）」。
**⚠️ 實際數過是 5 項**——同一篇的五個條件全部這樣宣告。
✅ **那是第 566 輪立過的第五型**：固定**時間**的計時賽報的是功率，🚫 不是完成時間。

## 🚨 而甲那一類會把一篇「沒有結局」的論文變回有結局——**那正是潛伏的重複**

`7a6ac1559c740fd6` 現在在範圍內 0 項，⚠️ 而它的 9 項宣告全卡在兩個名字上。
✅ 改名之後它會拿回 9 項，**🚨 其中的肌肉肝醣正是 n584 那本博士論文 Study 2 的同一批 8 人。**

> **📮 故甲類的改名不能單獨做**：⚠️ 它與「這兩筆算一個 study」是同一個決定。

## 🚫 本支**只記錄，不修改**

⚠️ 逐頁清冊是別的視窗交回的東西；🚨 本室不逕自改寫另一個視窗讀出來的宣告。
**✅ 本支產出的是一份待裁定的更正表**，🚫 一個位元組都不寫進工作單。
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n585_blocked_drafts_errata.json'
DETAIL = ROOT / 'extraction' / 'n585-errata-labels.json'
SHEET = ROOT / 'extraction-worksheet'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# 🚨 每一條都要說清楚**憑什麼**這樣分類，🚫 不是「看起來像」。
ERRATA = {
    ('time-to-exhaustion', 'cycling-time-to-exhaustion-fixed-power'): {
        'category': 'rename-safe',
        'correctTo': 'cycling-tte-fixed-intensity',
        'why': '✅ 固定功率騎到力竭＝固定強度之力竭時間，⚠️ 只是契約用 intensity 一詞。',
    },
    ('exogenous-cho-oxidation-peak', '13c-tracer-irms-indirect-calorimetry'): {
        'category': 'rename-safe',
        'correctTo': '13c-tracer-indirect-calorimetry',
        'why': '✅ 同一條方法，⚠️ 讀的人多寫了 irms（質譜儀）。'
               '🚨 兩篇各自寫出同一個名字，故這是契約用語不夠明顯，🚫 不是誰粗心。',
    },
    ('tt-completion-time', 'treadmill-time-trial-5km'): {
        'category': 'rename-safe',
        'correctTo': 'running-time-trial-fixed-distance',
        'why': '✅ 跑步機上跑固定的 5 公里＝跑步之固定距離計時賽。',
    },
    ('muscle-glycogen-post-exercise', 'acid-hydrolysis-freeze-dried-biopsy'): {
        'category': 'rename-needs-ruling',
        'correctTo': 'needle-biopsy-vastus-lateralis',
        'why': '⚠️ **部分相符**：論文的取樣部位敘述指的就是股外側肌，✅ 部位對得上'
               '（🚫 原句不逐字寫進 repo）；'
               '🚨 但**全文沒有出現 needle**，而允許值裡有這個字。'
               '⚠️ 讀的人寫的是**化驗方法**（酸水解、冷凍乾燥），🚫 不是取樣方法。'
               '📮 「部位相符即可」還是「必須逐字有 needle」，只有協調者能定。',
    },
    ('tt-completion-time', 'cycling-time-trial-fixed-duration-30min'): {
        'category': 'withdraw',
        'correctTo': None,
        'why': '🚨 這 5 項的標籤全部是「**Mean power output** during the 30 min '
               'self-paced time trial」——⚠️ **平均功率不是完成時間**。'
               '✅ 第 566 輪之第五型：固定**時間**的試驗報的是功率。'
               '🚫 改名救不了；⚠️ 契約也沒有固定時間長度的計時賽工具，'
               '🚨 但那是次要的——**主要問題是宣告本身。**',
    },
    ('tt-completion-time', 'double-poling-ski-ergometer-time-trial-fixed-distance'): {
        'category': 'contract-gap',
        'correctTo': None,
        'why': '🚨 契約的計時賽工具只有自行車與跑步，**沒有滑雪**（第 573 輪已報）。',
    },
    ('tt-completion-time', None): {
        'category': 'contract-gap',
        'correctTo': None,
        'why': '✅ 本室讀第 18 頁時**刻意留空**：⚠️ 同一個滑雪缺口，'
               '🚫 自創一個工具名等於製造假對應。',
    },
}


def entries():
    for path in [SHEET / 'drafts.json'] + sorted((SHEET / 'drafts')
                                                 .glob('page-*.json')):
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            yield entry


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    allowed = {o['outcomeId']: set(o.get('allowedInstruments') or [])
               for o in contract['inScopeOutcomes']}

    seen = defaultdict(lambda: {'items': 0, 'reports': set(), 'labels': []})
    for entry in entries():
        report = entry['report'][-16:]
        for item in entry.get('reportedOutcomes') or []:
            ref = item.get('normalisedOutcomeRef')
            if not ref:
                continue
            ok = allowed.get(ref, set())
            if ok and item.get('instrument') not in ok:
                key = (ref, item.get('instrument'))
                seen[key]['items'] += 1
                seen[key]['reports'].add(report)
                seen[key]['labels'].append(
                    {'report': report, 'label': item.get('localLabel')})

    unknown = [k for k in seen if k not in ERRATA]
    rows, by_category, affected = [], defaultdict(int), defaultdict(int)
    for key, found in sorted(seen.items(), key=lambda kv: -kv[1]['items']):
        ref, instrument = key
        note = ERRATA.get(key, {'category': 'unclassified', 'correctTo': None,
                                'why': '🚨 本支沒有為這一種寫下分類'})
        rows.append({'outcomeId': ref, 'declaredInstrument': instrument,
                     'items': found['items'],
                     'reports': sorted(found['reports']), **note})
        by_category[note['category']] += found['items']
        for report in found['reports']:
            affected[report] += found['items']

    # 🚨 有 draft 卻沒清冊的那三篇（門口被擋下的）。
    inventories = {json.loads(p.read_text(encoding='utf-8'))['report'][-16:]
                   for p in (ROOT / 'extraction').rglob('inventory-*.json')
                   if 'batches' not in str(p)}
    drafted = {e['report'][-16:] for e in entries()}
    blocked = sorted(drafted - inventories)
    # ⚠️ 名字對不上、卻**沒有**被擋在門口的：它們有清冊，只是清冊裡全不在範圍內。
    silent = sorted(set(affected) - set(blocked))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的掃到對不上的名字（必觸發）', bool(seen),
          '🚨 若為零，這份更正表就是空的，⚠️ 而空的更正表看起來像是「沒事」；'
          '實得 %d 種／%d 項／%d 篇'
          % (len(seen), sum(v['items'] for v in seen.values()), len(affected)))
    probe('每一種都分過類（必觸發之反向）', not unknown,
          '🚨 沒分類的會落進 unclassified 而不被看見；實得未分類 %d 種 %s'
          % (len(unknown), unknown))
    # 🚨 四類都要真的用得到，⚠️ 否則某一類只是寫在文件裡沒發生。
    missing = [c for c in ('rename-safe', 'rename-needs-ruling',
                           'contract-gap', 'withdraw')
               if c not in by_category]
    probe('四類都真的出現在資料裡（必觸發之反向）', not missing,
          '⚠️ 沒出現的類別代表那條規則沒被驗證過；實得缺 %s' % (missing or '無'))
    # 🚫 本支不得改到工作單。✅ 用「沒有寫入」這件事本身當探針。
    probe('本支沒有改動任何工作單檔案',
          not any(p.stat().st_mtime > OUT.stat().st_mtime
                  for p in SHEET.rglob('*.json')) if OUT.exists() else True,
          '✅ 本支只讀不寫；🚨 若這裡紅了，代表它動了別的視窗交回的東西')

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'errata-labels-private',
         'labels': {'%s|%s' % k: v['labels'] for k, v in seen.items()}},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'blocked-drafts-errata',
        'ruling': 'n+190（三）A4：門口被擋下的三筆全部結清',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'appliesNothing': ('🚫 本支只記錄，不修改——⚠️ 逐頁清冊是別的視窗交回的，'
                           '🚨 本室不逕自改寫另一個視窗讀出來的宣告。'),
        'blockedReports': blocked,
        'zeroedButNotBlocked': silent,
        'kinds': len(rows),
        'itemsByCategory': dict(by_category),
        'itemsByReport': dict(sorted(affected.items(), key=lambda kv: -kv[1])),
        'rows': rows,
        'linkedToN584': (
            '🚨 rename-safe 會讓 7a6ac1559c740fd6 從「在範圍內 0 項」變回 9 項，'
            '⚠️ 而其中的肌肉肝醣正是 n584 那本博士論文 Study 2 的同一批 8 人。'
            '📮 故改名與「這兩筆算一個 study」是同一個決定，🚫 不可分開做。'),
        'detailKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n585 更正表（🚫 只記錄，不修改）===')
    print('   門口被擋下：%s' % blocked)
    print('   🚨 名字對不上卻沒被擋下（清冊全不在範圍內）：%s' % silent)
    print('   分類統計：%s' % dict(by_category))
    for r in rows:
        print('   [%s] %-30s %-46r %2d 項／%d 篇 → %s'
              % (r['category'], r['outcomeId'], r['declaredInstrument'],
                 r['items'], len(r['reports']), r['correctTo']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
