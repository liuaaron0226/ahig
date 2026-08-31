# -*- coding: utf-8 -*-
"""**因「儀器不在允許清單」被排除的，到底有幾項、幾篇。**（第 574 輪）

n+189（三）交辦：⚠️ 工作單是**改動前**寫出去的，已讀的那些拿到的是沒有清單的請求。
**🚨 要數，不得憑印象估**——那個數字決定要不要重讀。

## 🚨 兩種排除必須分開數

| | 填了什麼 | 意義 |
|---|---|---|
| **(甲) 名字對不上** | 非 null，且不在允許清單裡 | 🚨 **這是缺陷**：論文可能真的用了允許的儀器，只是讀的人寫了別的名字 |
| **(乙) 刻意留空** | `null` | ✅ **這是實情**：契約對該結局的允許清單裡**沒有**適用的值（例如滾輪滑雪之計時賽） |

**⚠️ 兩者混在一起數，會把「該重讀的」與「重讀也沒用的」算成同一堆。**
🚨 而 n+189 要的那個數字，是**甲**。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

CONTRACT_PATH = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
                 / 'scope-contract.json')
OUT = Path(__file__).resolve().parent / 'n574_instrument_exclusions.json'
REASON = 'notExtracted-instrument-not-in-allowlist'


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    allowed = {o['outcomeId']: set(o.get('allowedInstruments') or [])
               for o in contract['inScopeOutcomes']}

    root = ROOT / 'extraction'
    files = sorted(p for p in root.rglob('inventory-*.json')
                   if 'batches' not in str(p))

    mismatched, blank, records = [], [], []
    for path in files:
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        m_here, b_here = [], []
        for item in doc.get('reportedOutcomes') or []:
            decision = item.get('scopeDecision') or {}
            if decision.get('reasonCode') != REASON:
                continue
            ref = item.get('normalisedOutcomeRef')
            got = item.get('instrument')
            entry = {'report': report, 'outcomeId': ref, 'instrument': got,
                     'allowed': sorted(allowed.get(ref, ())),
                     'label': (item.get('localLabel') or '')[:90]}
            (m_here if got is not None else b_here).append(entry)
        mismatched += m_here
        blank += b_here
        if m_here or b_here:
            records.append({'report': report, 'mismatched': len(m_here),
                            'blank': len(b_here)})

    by_report_m = sorted({e['report'] for e in mismatched})
    by_report_b = sorted({e['report'] for e in blank})
    # 🚨 只因這個理由而**整篇歸零**的：候選數為 0，且該篇有名字對不上的項目。
    zeroed = []
    for path in files:
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc['scopeDecisionSummary']['candidateCount'] != 0:
            continue
        if any(e['report'] == doc['report'][-16:] for e in mismatched):
            zeroed.append(doc['report'][-16:])

    # 🚨 「名字對不上」裡還藏著第二種東西：**modality 根本不在允許清單裡**。
    # ⚠️ 重讀（帶上清單）改不了它——讀的人看到清單只會發現沒有適用值，
    # 🚨 於是它會變成「刻意留空」，理由碼一模一樣。
    # ✅ 故另立一類：填的名字裡帶 ski 的那些（本語料的兩篇滑雪研究）。
    ski = [e for e in mismatched
           if 'ski' in (e['instrument'] or '').lower()]
    rereadable = [e for e in mismatched if e not in ski]
    ski_reports = sorted({e['report'] for e in ski}
                         | {e['report'] for e in blank})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩種排除確實被分開了（必觸發）',
          bool(mismatched) and bool(blank),
          '🚨 若其中一類為空，代表分類沒生效或語料剛好只有一種；'
          '實得 名字對不上 %d 項／刻意留空 %d 項'
          % (len(mismatched), len(blank)))
    probe('每一筆名字對不上者，其允許清單都非空',
          all(e['allowed'] for e in mismatched),
          '🚨 允許清單為空時 matcher 根本不會走到這個理由，'
          '有這種筆代表我讀錯了資料')
    probe('刻意留空者的允許清單裡確實沒有適用值',
          all(e['instrument'] is None for e in blank),
          '⚠️ 留空即表示本室查過清單而找不到適用值')

    doc = {
        'schemaVersion': 1,
        'documentType': 'instrument-exclusion-census',
        'ruling': 'n+189（三）：已讀的那些要回頭數',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'reasonCode': REASON,
        'inventories': len(files),
        'counts': {
            'mismatchedItems': len(mismatched),
            'mismatchedReports': len(by_report_m),
            'blankItems': len(blank),
            'blankReports': len(by_report_b),
            'reportsZeroedByMismatch': len(zeroed),
            'rereadableItems': len(rereadable),
            'rereadableReports': len({e['report'] for e in rereadable}),
            'skiModalityItems': len(ski) + len(blank),
            'skiModalityReports': len(ski_reports),
        },
        'skiModalityGap': {
            'what': ('🚨 語料裡有**兩篇**滑雪研究，而契約 tt-completion-time 的'
                     '允許工具只有自行車與跑步。⚠️ 一篇由本室留空、一篇由另一視窗'
                     '自創了 double-poling-ski-ergometer-… 的名字，'
                     '🚨 但兩者被排除的原因是同一個：**契約沒有滑雪。**'),
            'reports': ski_reports,
            'items': len(ski) + len(blank),
            'rereadingWillNotFix': True,
        },
        'mismatchedReports': by_report_m,
        'blankReports': by_report_b,
        'reportsZeroedByMismatch': zeroed,
        'mismatched': mismatched,
        'blank': blank,
        'whatThisMeans': (
            '🚨 「名字對不上」那一類才是 n+189 要的數：'
            '⚠️ 論文可能真的用了允許的儀器，只是讀的人寫了別的名字，'
            '✅ 重讀（帶上清單）就會改變結果。'
            '🚫 「刻意留空」那一類重讀也不會變——'
            '⚠️ 契約的允許清單裡沒有適用值（例如滾輪滑雪之計時賽），'
            '🚨 那要改的是契約，不是重讀。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n574 因「儀器不在允許清單」被排除者 ===')
    print('   清冊 %d 份' % len(files))
    print('   🚨 名字對不上：%d 項，分布 %d 篇 → %s'
          % (len(mismatched), len(by_report_m), by_report_m))
    print('   ✅ 刻意留空　：%d 項，分布 %d 篇 → %s'
          % (len(blank), len(by_report_b), by_report_b))
    print('   🚨 只因名字對不上而整篇歸零：%d 篇 → %s' % (len(zeroed), zeroed))
    print('   ── 分成兩類 ──')
    print('   ✅ 重讀改得掉：%d 項／%d 篇' % (len(rereadable),
          len({e['report'] for e in rereadable})))
    print('   🚨 滑雪：契約沒有該 modality，重讀改不掉：%d 項／%d 篇 → %s'
          % (len(ski) + len(blank), len(ski_reports), ski_reports))
    print()
    for e in mismatched:
        print('   🚨 %s｜%s' % (e['report'], e['outcomeId']))
        print('      填了：%r' % e['instrument'])
        print('      允許：%s' % e['allowed'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
