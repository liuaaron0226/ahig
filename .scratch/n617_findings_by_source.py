# -*- coding: utf-8 -*-
"""**先前那些發現，是不是都擠在那 15 篇上。**（第 617 輪）

## 🚨 這一支在檢驗本室自己的推論

第 616 輪說「覆蓋率最低的三篇，都是先前被記為有問題的論文」。
**⚠️ 三篇是軼事，🚫 不是證據。**

> **✅ 若那些發現真的由酬載品質造成，它們應該集中在 GROBID 那 15 篇；**
> **🚨 若平均分布，那本室的推論就站不住——而那也要照報。**

⚠️ 基準率：**GROBID 15／41 ＝ 37%**。
🚨 任何發現若在 GROBID 的占比接近 37%，就**不算集中**。

## 🚨 而答案是：**推論不成立**

| 發現 | 涉及篇數 | GROBID 占比 | 判讀 |
|---|---|---|---|
| 零貢獻論文（n586） | 13 | **38%** | ⚠️ **等於基準率**——🚫 不集中 |
| 劑量留空（n589） | 6 | **33%** | ⚠️ **等於基準率**——🚫 不集中 |
| 其餘三項 | **各 1 篇** | 100% | 🚨 n＝1，🚫 撐不起模式 |

> **🚨 唯二有足夠篇數可談的兩項，都落在基準率上。**
> **⚠️ 故第 616 輪那句「他們手上少了兩成」是軼事，🚫 分布不支持它。**
> ✅ 酬載品質仍是**真的缺陷**（第 611／615／616 輪的數字沒有變），
> **🚫 但它不是那些發現的成因。**

## ⚠️ 而本支自己差點犯同一個錯

🚨 第一版把基準率算成 **15%**（讀了全部 315 份 manifest 而非那 41 篇）——
**⚠️ 用偏低的基準率去比，會把「剛好等於基準」誤讀成「不成比例地集中」。**
✅ 已修：只算取得的 41 篇。

## 🚫 本支不改任何東西，也不重新判定任何一項
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n617_findings_by_source.json'


def source_map():
    """🚨 只算**取得的那 41 篇**。

    ⚠️ 第一版讀了全部 315 份 manifest，得出基準率 15%——**而正確是 37%**。
    🚨 用一個偏低的基準率去比，會把「剛好等於基準」誤讀成「不成比例地集中」。
    ✅ 那正是本支要檢驗的東西，🚫 而它差點自己犯了。
    """
    sys.path.insert(0, str(REPO / 'ahig'))
    from ahig.extraction import corpus  # noqa: E402
    acquired = {c[-16:] for c in corpus.acquired_roster()[0]}
    out = {}
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        key = doc.get('candidateId', '')[-16:]
        if doc.get('sourceType') and key in acquired:
            out[key] = doc['sourceType']
    return out


def reports_from(name, key, path=()):
    """從既有憑證取出涉及的報告代碼。🚫 不重新判定。"""
    target = HERE / (name + '.json')
    if not target.exists():
        return set()
    doc = json.loads(target.read_text(encoding='utf-8'))
    for step in path:
        doc = doc.get(step) or {}
    if isinstance(doc, dict):
        items = doc.get(key) or []
    else:
        items = doc
    out = set()
    for item in items:
        if isinstance(item, str):
            out.add(item[-16:])
        elif isinstance(item, dict):
            for field in ('report', 'reportId'):
                if item.get(field):
                    out.add(item[field][-16:])
    return out


def main():
    sources = source_map()
    tei = {k for k, v in sources.items() if v == 'grobid-tei'}
    base = round(100 * len(tei) / len(sources)) if sources else 0

    findings = {}

    census = HERE / 'n586_zero_contribution_census.json'
    if census.exists():
        rows = json.loads(census.read_text(encoding='utf-8')).get('zeroRows', [])
        findings['零貢獻論文（n586）'] = {r['report'] for r in rows}

    dose = HERE / 'n589_dose_not_reported_audit.json'
    if dose.exists():
        rows = json.loads(dose.read_text(encoding='utf-8')).get('rows', [])
        findings['劑量留空（n589）'] = {r['report'] for r in rows}

    unsupported = HERE / 'n597_numeric_result_unsupported.json'
    if unsupported.exists():
        doc = json.loads(unsupported.read_text(encoding='utf-8'))
        findings['宣稱有數值而無數字（n597）'] = {doc['report'][-16:]}

    methods = HERE / 'n598_source_section_no_result.json'
    if methods.exists():
        rows = json.loads(methods.read_text(encoding='utf-8')).get('flagged', [])
        findings['出處無結果標記（n598）'] = {r['report'] for r in rows}

    discussion = HERE / 'n590_source_location_audit.json'
    if discussion.exists():
        rows = json.loads(discussion.read_text(encoding='utf-8')).get(
            'citedContextWithContractOutcome', [])
        findings['出處為討論段（n590）'] = {r['report'] for r in rows}

    table = []
    for name, reports in findings.items():
        known = {r for r in reports if r in sources}
        hit = {r for r in known if r in tei}
        table.append({'finding': name, 'reports': len(known),
                      'grobidReports': len(hit),
                      'grobidShare': round(100 * len(hit) / len(known))
                      if known else 0})

    concentrated = [t for t in table if t['grobidShare'] > base + 20]
    at_base = [t for t in table if abs(t['grobidShare'] - base) <= 20]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('取到了多個既有發現（必觸發）',
          len(table) >= 4,
          '🚨 太少就談不上分布；實得 %d 項發現' % len(table))
    probe('基準率算得出來（必觸發）', 0 < base < 100,
          '⚠️ GROBID 佔全語料 %d%%——🚨 任何發現的占比若接近它，就不算集中'
          % base)
    # 🚨 必觸發之反向：⚠️ 不是每一項都該集中，否則這個比較沒有分辨力。
    probe('並非每一項發現都集中在 GROBID（必觸發之反向）',
          len(concentrated) < len(table),
          '⚠️ 集中者 %d／%d；🚨 若全部都集中，代表本支只是在複述來源分布'
          % (len(concentrated), len(table)))
    # 🚨 這一道會紅：⚠️ 有發現確實擠在那 15 篇上。
    probe('沒有任何發現不成比例地集中在 GROBID',
          not concentrated,
          '🚨 實得 %d 項超出基準率 20 個百分點以上：%s；'
          '⚠️ 基準率 %d%%——✅ 那支持「酬載品質是成因之一」，'
          '🚫 但不證明每一項都是'
          % (len(concentrated),
             [(t['finding'], '%d%%' % t['grobidShare']) for t in concentrated],
             base))

    doc = {
        'schemaVersion': 1,
        'documentType': 'findings-by-source',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'baseRatePct': base,
        'corpus': {'total': len(sources), 'grobid': len(tei)},
        'findings': table,
        'concentrated': [t['finding'] for t in concentrated],
        'atBaseRate': [t['finding'] for t in at_base],
        'whatThisDoesNotShow': (
            '🚫 本支不證明那些發現「是酬載造成的」——'
            '⚠️ 集中只是相容於那個解釋。'
            '🚨 而若某一項落在基準率附近，那一項就**不能**用酬載解釋。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n617 發現落在哪一種來源 ===')
    print('   基準率：GROBID %d／%d ＝ %d%%' % (len(tei), len(sources), base))
    for row in sorted(table, key=lambda t: -t['grobidShare']):
        mark = '🚨' if row['grobidShare'] > base + 20 else '  '
        print('   %s %-28s 涉及 %2d 篇｜GROBID %2d 篇（%d%%）'
              % (mark, row['finding'], row['reports'], row['grobidReports'],
                 row['grobidShare']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
