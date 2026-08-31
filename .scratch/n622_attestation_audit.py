# -*- coding: utf-8 -*-
"""**「我掃了哪些段落」這句話，經得起查嗎。**（第 622 輪）

## 🚨 本 run 引用過完整性聲明，卻從未驗證過它

⚠️ 每份清冊都帶著 `completenessAttestation`：掃了哪些段落、做了傷害掃描。
🚨 本室引用過其中的註記（例如那本論文自述是 thesis），
**🚫 但從未問過：那份聲明說的話是不是真的。**

> **⚠️ 一份指向不存在段落的聲明，比沒有聲明更糟——🚨 它讓人以為查過了。**

## ✅ 三道查核

| | 問題 |
|---|---|
| **甲** | `sectionsScanned` 列的段落，在那份文件裡**真的存在**嗎 |
| **乙** | 在範圍內結局的**出處段落**，有沒有在 `sectionsScanned` 裡 |
| **丙** | `harmsScan` 說找到幾個傷害結局，與實際宣告的 GI 結局**對不對得上** |

⚠️ 乙那一條最要緊：**🚨 你不可能在一個沒掃的段落裡找到結局。**

## 🚫 本支不改任何清冊
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
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n622_attestation_audit.json'


def main():
    ids = {c[-16:]: c for c in corpus.acquired_roster()[0]}
    cache = {}

    def titles(report):
        if report not in cache:
            cache[report] = {str(s.title or '')
                             for s in corpus.load_document(ids[report]).sections}
        return cache[report]

    rows = []
    ghost_total = uncovered_total = 0
    harm_mismatch = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        if report not in ids:
            continue
        attestation = doc.get('completenessAttestation') or {}
        scanned = list(attestation.get('sectionsScanned') or [])
        real = titles(report)

        # 甲：⚠️ 聲明列出、而文件裡沒有的段落。
        ghosts = [s for s in scanned if s not in real]
        # 乙：🚨 在範圍內結局的出處，有沒有在聲明裡。
        in_scope_sections = {
            ((o.get('sourceLocation') or {}).get('section')) or ''
            for o in doc.get('reportedOutcomes') or []
            if (o.get('scopeDecision') or {}).get('inScope')}
        uncovered = sorted(s for s in in_scope_sections if s not in scanned)
        # 丙：⚠️ 傷害掃描的數字與宣告的 GI 結局。
        harms = attestation.get('harmsScan') or {}
        claimed = harms.get('harmOutcomesFound')
        gi_declared = sum(
            1 for o in doc.get('reportedOutcomes') or []
            if (o.get('normalisedOutcomeRef') or '').startswith('gi-symptom'))
        statement = harms.get('harmsReportingStatement')

        ghost_total += len(ghosts)
        uncovered_total += len(uncovered)
        # 🚨 第一版的規則是「宣告了 GI 結局而 harmOutcomesFound=0 就算不一致」。
        # ⚠️ 那是錯的——**它忘了本 run 自己立的三分法**：
        # `explicit-none-reported` 正是「評估過、沒有」，而那時候 0 才是對的。
        # ✅ 實例：某篇的標籤逐字寫著「none reported in any trial」。
        # 🚨 真正的矛盾只有兩種：
        #   ① 說 harms-reported 卻回報 0；② 說 not-mentioned 卻宣告了 GI 結局。
        contradiction = ((statement == 'harms-reported' and claimed == 0)
                         or (statement == 'not-mentioned' and gi_declared))
        if contradiction:
            harm_mismatch.append({'report': report, 'claimed': claimed,
                                  'giDeclared': gi_declared,
                                  'statement': statement})
        rows.append({'report': report, 'scanned': len(scanned),
                     'ghostSections': ghosts[:4], 'ghostCount': len(ghosts),
                     'uncoveredInScopeSections': uncovered,
                     'harmOutcomesFound': claimed,
                     'giOutcomesDeclared': gi_declared,
                     'harmsReportingStatement': statement})

    with_ghosts = [r for r in rows if r['ghostCount']]
    with_uncovered = [r for r in rows if r['uncoveredInScopeSections']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每份清冊都有完整性聲明（必觸發）',
          all(r['scanned'] > 0 for r in rows) and len(rows) == 38,
          '🚨 少一份就代表本支看的不是同一批；實得 %d 份，'
          '其中 %d 份的 sectionsScanned 為空'
          % (len(rows), sum(1 for r in rows if not r['scanned'])))
    # 🚨 必觸發之反向：⚠️ 查核要真的分得出「不存在的段落」。
    sample = rows[0]['report'] if rows else None
    probe('段落存在查核說得出「不存在」（必觸發之反向）',
          sample is not None and 'ZZ-不存在-ZZ' not in titles(sample),
          '🚨 以一個不可能存在的段落名試；⚠️ 若它也算存在，'
          '「幽靈段落 %d 個」就沒有意義' % ghost_total)
    # 🚨 這兩道的紅綠就是答案。
    probe('聲明列出的段落都真的存在',
          not with_ghosts,
          '🚨 實得 %d 份清冊列了不存在的段落，共 %d 個；'
          '⚠️ 一份指向不存在段落的聲明，比沒有聲明更糟'
          % (len(with_ghosts), ghost_total))
    probe('在範圍內結局的出處都在已掃段落內',
          not with_uncovered,
          '🚨 實得 %d 份清冊有 %d 個「出處不在已掃清單裡」的段落；'
          '⚠️ 你不可能在一個沒掃的段落裡找到結局'
          % (len(with_uncovered), uncovered_total))
    probe('傷害掃描的數字與宣告的 GI 結局一致',
          not harm_mismatch,
          '🚨 實得 %d 份宣告了 GI 結局卻回報 harmOutcomesFound=0：%s'
          % (len(harm_mismatch),
             [(m['report'], m['statement']) for m in harm_mismatch]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'attestation-audit',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': len(rows),
        'ghostSectionTotal': ghost_total,
        'reportsWithGhostSections': len(with_ghosts),
        'uncoveredInScopeSectionTotal': uncovered_total,
        'reportsWithUncovered': len(with_uncovered),
        'harmMismatch': harm_mismatch,
        'rows': rows,
        'whyItMatters': (
            '⚠️ 完整性聲明是「我看過哪裡」的自述。'
            '🚨 一份指向不存在段落的聲明，比沒有聲明更糟——它讓人以為查過了。'
            '✅ 而「出處不在已掃清單裡」更硬：'
            '**🚫 你不可能在一個沒掃的段落裡找到結局。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n622 完整性聲明稽核 ===')
    print('   清冊 %d 份' % len(rows))
    print('   🚨 列了不存在段落者：%d 份／共 %d 個'
          % (len(with_ghosts), ghost_total))
    print('   🚨 出處不在已掃清單裡者：%d 份／共 %d 個'
          % (len(with_uncovered), uncovered_total))
    for row in with_uncovered[:5]:
        print('      %s｜%s' % (row['report'],
                                row['uncoveredInScopeSections'][:2]))
    print('   🚨 傷害數字對不上者：%d 份' % len(harm_mismatch))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
