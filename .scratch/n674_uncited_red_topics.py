# -*- coding: utf-8 -*-
"""**48 支沒有決策的紅燈裡，哪幾支談的是登記簿沒談過的事。**（第 674 輪）

## 🚨 第 673 輪留下的弱點

64 支憑證亮著紅燈，**只有 16 支有決策引用**；
⚠️ 另外 48 支只靠「有人提過那一輪」撐著——**🚫 那不是決定。**

## 🚫 而本室不打算用散文逐一分類

⚠️ 那 48 支的 `documentType` **48 個全都不一樣**——
🚨 那不是規則，是 48 件個案，硬分類只會變成本室的主觀清單。

## ✅ 改用已驗過的機器

每個決策的「題目指紋」＝它的證據憑證裡的識別字。
對每一支無決策的紅燈，算它與**任一決策指紋**的**稀有度加權重疊**：

- **重疊高** → 這件事登記簿談過了（只是這一支沒被列為證據）
- **🚨 重疊低** → **登記簿可能真的沒談過它** → 本室逐一過目

⚠️ 只算**稀有**的識別字（權重 ≥ 2.0，約等於出現在 13% 以下的憑證裡）——
🚨 否則到處都有的結局代號會讓每一對看起來都很像。

## 🚫 本支不改任何清冊與契約、不送外部請求
"""
import collections
import json
import math
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
OUT = HERE / 'n674_uncited_red_topics.json'
REGISTER = HERE / 'n669_decision_register_v3.json'
ORPHAN = HERE / 'n673_orphan_findings.json'

ROUND_RE = re.compile(r'^n(\d+)_')
REPORT_RE = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
REASON_RE = re.compile(r'\b(?:notExtracted|escalated)-[a-z0-9-]+\b')
KEBAB_RE = re.compile(r'\b[a-z][a-z0-9]*(?:-[a-z0-9]+){2,}\b')
DECISION_RE = re.compile(r'\bD[1-9][0-9]?\b')

RARE_FLOOR = 2.0
LOW_OVERLAP = 6.0


def identifiers(text):
    return (set(REPORT_RE.findall(text)) | set(REASON_RE.findall(text))
            | set(KEBAB_RE.findall(text)) | set(DECISION_RE.findall(text)))


def build():
    index = collections.defaultdict(set)
    per_file = {}
    for path in sorted(HERE.glob('n*.json')):
        if not ROUND_RE.match(path.name):
            continue
        try:
            per_file[path.name] = identifiers(
                path.read_text(encoding='utf-8'))
        except OSError:
            continue
        for ident in per_file[path.name]:
            index[ident].add(path.name)
    return index, per_file


def main():
    index, per_file = build()
    corpus = len(per_file) or 1
    weight = {i: math.log(corpus / len(f)) for i, f in index.items() if f}
    rare = {i for i, w in weight.items() if w >= RARE_FLOOR}

    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    fingerprints = {}
    evidence_of = {}
    for item in register['items']:
        names = [p.split('→')[0].strip()
                 for p in str(item['evidence']).replace('；', ';').split(';')]
        names = [n for n in names if n in per_file]
        evidence_of[item['id']] = names
        marks = set()
        for name in names:
            marks |= (per_file[name] & rare)
        if marks:
            fingerprints[item['id']] = marks

    orphan = json.loads(ORPHAN.read_text(encoding='utf-8'))
    uncited = [r for r in orphan['rows'] if not r['citedByDecisions']]
    cited = [r for r in orphan['rows'] if r['citedByDecisions']]

    def best_match(name, skip=()):
        mine = per_file.get(name, set()) & rare
        best, best_score, best_shared = None, 0.0, []
        for did, marks in fingerprints.items():
            if did in skip:
                continue
            shared = mine & marks
            score = sum(weight[i] for i in shared)
            if score > best_score:
                best, best_score, best_shared = did, score, sorted(shared)
        return best, round(best_score, 2), best_shared

    rows = []
    for entry in uncited:
        did, score, shared = best_match(entry['artefact'])
        rows.append({'artefact': entry['artefact'], 'round': entry['round'],
                     'firstFailed': entry['firstFailed'],
                     'closestDecision': did, 'overlapScore': score,
                     'sharedRareIdentifiers': shared[:6]})
    rows.sort(key=lambda r: r['overlapScore'])
    low = [r for r in rows if r['overlapScore'] < LOW_OVERLAP]

    # ✅ 必觸發之反向：**被某決策引用的**憑證，對「那個決策」必須高分。
    sanity = []
    for entry in cited:
        did = entry['citedByDecisions'][0]
        mine = per_file.get(entry['artefact'], set()) & rare
        shared = mine & fingerprints.get(did, set())
        sanity.append({'artefact': entry['artefact'], 'decision': did,
                       'selfScore': round(sum(weight[i] for i in shared), 2)})
    sanity_bad = [s for s in sanity if s['selfScore'] < LOW_OVERLAP]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('決策的題目指紋抽得出來（必觸發之正對照）',
          len(fingerprints) >= 15,
          '🚨 %d／%d 個決策有指紋（其餘的證據檔不在 .scratch 或無稀有識別字）；'
          '⚠️ 太少的話「重疊低」只是因為沒有東西可比'
          % (len(fingerprints), len(register['items'])))
    probe('稀有度門檻真的篩掉了到處都有的識別字（必觸發之反向）',
          len(rare) < len(weight),
          '🚨 識別字 %d 個，權重 ≥ %.1f 的只有 %d 個；'
          '⚠️ 若全部都留下，每一對看起來都會很像'
          % (len(weight), RARE_FLOOR, len(rare)))
    probe('被決策引用的憑證，對「引用它的那個決策」必須高分（必觸發之反向）',
          not sanity_bad,
          '🚨 %d 支已被引用，其中對自己那個決策低於 %.1f 分的有 %d 支：%s；'
          '⚠️ 若自己都比不高，這個相似度沒有意義'
          % (len(sanity), LOW_OVERLAP, len(sanity_bad),
             [s['artefact'] for s in sanity_bad] or '無'))
    # 🚨 這一道是答案。
    probe('每一支無決策的紅燈都與某個決策高度重疊',
          not low,
          '🚨 重疊低於 %.1f 分的有 %d／%d 支：%s；'
          '⚠️ 這是**要本室逐一過目的候選**，🚫 不是「漏掉的決策」'
          % (LOW_OVERLAP, len(low), len(rows),
             [r['artefact'] for r in low] or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'uncited-red-topic-overlap',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'uncitedReds': len(rows),
        'lowOverlapThreshold': LOW_OVERLAP,
        'lowOverlap': low,
        'rows': rows,
        'decisionsWithFingerprint': sorted(fingerprints),
        'sanityCheck': sanity,
        'whyNotProse': (
            '⚠️ 那 48 支的 `documentType` **48 個全都不一樣**——'
            '🚨 硬分類只會變成本室的主觀清單。'
            '✅ 故改用第 670／671 輪驗過的稀有度重疊。'),
        'methodLimit': (
            '🚨 重疊高只代表**談的東西重疊**，🚫 不代表那個決策涵蓋了這支的發現；'
            '⚠️ 重疊低也可能只是因為那支憑證談的是**本室自己的工具**'
            '（索引、掃描器、重跑對帳），**那本來就不需要裁定**。'
            '✅ 故本支的產出是**待過目清單**，🚫 不是缺漏清單。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n674 無決策紅燈的題目重疊 ===')
    print('   無決策紅燈 %d 支｜有指紋的決策 %d 個｜稀有識別字 %d／%d'
          % (len(rows), len(fingerprints), len(rare), len(weight)))
    print('   重疊最低的 12 支（分數低＝登記簿可能沒談過）：')
    for row in rows[:12]:
        print('      %5.2f  %-42s → %-4s %s'
              % (row['overlapScore'], row['artefact'],
                 row['closestDecision'] or '—',
                 (row['firstFailed'] or '')[:34]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
