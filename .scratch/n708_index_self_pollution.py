# -*- coding: utf-8 -*-
"""**索引污染了自己的查詢——目錄型憑證永遠排第一。**（第 708 輪）

## 🚨 怎麼發現的

第 706 輪的教訓是「工具指了、本室沒讀」。
✅ 於是本輪回頭跑那個查詢，問「第 690–707 輪還有哪些該讀而沒讀的」——
**⚠️ 結果是空的。**

🚨 但把「有沒有掛決策」的條件拿掉之後就看到了：
**第 1 名幾乎永遠是 `n670_identifier_index.json` 或某一版登記簿。**

> **🚨 索引的 JSON 裡**列著全部識別字**，登記簿列著全部決策與報告——
> ⚠️ 它們跟任何查詢都高度相符，於是**永遠佔住第一名**。**

## ✅ 修法：目錄不是發現

把 `documentType` 為 `identifier-index` 或 `pending-decision-register` 的
憑證**排除在索引之外**——🚨 它們是目錄，🚫 不是發現。

## ✅ 而修完必須通過兩題

| 題 | 要求 |
|---|---|
| **回溯測試**（第 670 輪那題） | `n594` 仍要排得進前五、仍要連得到 `D4` |
| **本輪這題** | 排除之後，本串的第一名要換成**真的憑證** |

⚠️ 只過一題不算——🚨 前者防止修過頭，後者證明真的修到。

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
OUT = HERE / 'n708_index_self_pollution.json'
REGISTER = HERE / 'n707_decision_register_v13.json'

ROUND_RE = re.compile(r'^n(\d+)_')
REPORT_RE = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
REASON_RE = re.compile(r'\b(?:notExtracted|escalated)-[a-z0-9-]+\b')
KEBAB_RE = re.compile(r'\b[a-z][a-z0-9]*(?:-[a-z0-9]+){2,}\b')
DECISION_RE = re.compile(r'\bD[1-9][0-9]?\b')

CATALOGUE_TYPES = {'identifier-index', 'pending-decision-register'}
CHAIN = range(690, 708)
RETRO_CUTOFF = 663
RETRO_QUERY = ['7a6ac1559c740fd6', 'muscle-glycogen-post-exercise',
               'needle-biopsy-vastus-lateralis',
               'acid-hydrolysis-freeze-dried-biopsy']
RETRO_TARGET = 'n594_a3_first_measurement.json'
RAREST_K = 5


def identifiers(text):
    return (set(REPORT_RE.findall(text)) | set(REASON_RE.findall(text))
            | set(KEBAB_RE.findall(text)) | set(DECISION_RE.findall(text)))


def catalogue_names():
    out = set()
    for path in sorted(HERE.glob('n*.json')):
        if not ROUND_RE.match(path.name):
            continue
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and \
                doc.get('documentType') in CATALOGUE_TYPES:
            out.add(path.name)
    return out


def build(exclude=frozenset(), max_round=None):
    index = collections.defaultdict(set)
    per_file = {}
    for path in sorted(HERE.glob('n*.json')):
        m = ROUND_RE.match(path.name)
        if not m or path.name in exclude:
            continue
        if max_round is not None and int(m.group(1)) >= max_round:
            continue
        try:
            found = identifiers(path.read_text(encoding='utf-8'))
        except OSError:
            continue
        per_file[path.name] = found
        for ident in found:
            index[ident].add(path.name)
    return index, per_file


def weights(index, size):
    return {i: math.log(size / len(f)) for i, f in index.items() if f}


def top_hit(name, per_file, index, w, older):
    mine = sorted(per_file.get(name, set()),
                  key=lambda i: -w.get(i, 0.0))[:RAREST_K]
    scores = collections.Counter()
    for ident in mine:
        for other in index.get(ident, ()):
            if other in older and other != name:
                scores[other] += w.get(ident, 0.0)
    best = scores.most_common(1)
    return best[0][0] if best else None


def decisions_by_file():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    out = collections.defaultdict(set)
    for item in register['items']:
        for part in str(item['evidence']).replace('；', ';').split(';'):
            name = part.split('→')[0].strip()
            if name:
                out[name].add(item['id'])
    return out


def main():
    catalogues = catalogue_names()
    to_decision = decisions_by_file()

    results = {}
    for label, exclude in (('未排除', frozenset()),
                           ('排除目錄後', frozenset(catalogues))):
        index, per_file = build(exclude=exclude)
        w = weights(index, len(per_file) or 1)
        older = {n for n in per_file
                 if int(ROUND_RE.match(n).group(1)) < min(CHAIN)}
        hits = {}
        for name in per_file:
            r = int(ROUND_RE.match(name).group(1))
            if r not in CHAIN:
                continue
            hit = top_hit(name, per_file, index, w, older)
            hits[name] = {'top': hit,
                          'decisions': sorted(to_decision.get(hit, set()))
                          if hit else []}
        results[label] = hits

    def catalogue_share(hits):
        tops = [v['top'] for v in hits.values() if v['top']]
        return (sum(1 for t in tops if t in catalogues), len(tops))

    before = catalogue_share(results['未排除'])
    after = catalogue_share(results['排除目錄後'])
    with_decisions = sum(1 for v in results['排除目錄後'].values()
                         if v['decisions'])

    # ✅ 回溯測試：修完不能把第 670 輪那題弄壞。
    retro_index, retro_files = build(exclude=frozenset(catalogues),
                                     max_round=RETRO_CUTOFF)
    rw = weights(retro_index, len(retro_files) or 1)
    scores = collections.Counter()
    for ident in RETRO_QUERY:
        for name in retro_index.get(ident, ()):
            scores[name] += rw.get(ident, 0.0)
    ranked = scores.most_common()
    rank = next((i + 1 for i, (n, _) in enumerate(ranked)
                 if n == RETRO_TARGET), None)
    retro_decisions = sorted({d for n, _ in ranked[:5]
                              for d in to_decision.get(n, set())})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('目錄型憑證抓得出來（必觸發之正對照）',
          len(catalogues) >= 5,
          '🚨 目錄型憑證 %d 支（%s 型）；⚠️ 抓不到就無從排除'
          % (len(catalogues), sorted(CATALOGUE_TYPES)))
    # 🚨 這一道是問題本身。
    probe('未排除時，目錄不會霸佔第一名',
          before[0] == 0,
          '🚨 未排除：%d／%d 支的第一名是目錄；'
          '⚠️ 目錄列著全部識別字，跟任何查詢都相符'
          % before)
    probe('排除之後目錄不再佔第一名（必觸發之反向）',
          after[0] == 0 and after[1] > 0,
          '🚨 排除後：%d／%d 支的第一名是目錄；'
          '⚠️ 若仍有，代表排除沒生效' % after)
    probe('排除之後，第 670 輪那題仍過（必觸發之正對照・防止修過頭）',
          rank is not None and rank <= 5 and 'D4' in retro_decisions,
          '🚨 `n594` 名次 %s、前五連到的決策 %s；'
          '⚠️ 弄壞它就代表修過頭了'
          % (rank or '未進榜', retro_decisions or '無'))
    # 🚨 這一道是答案。
    probe('排除之後，本串沒有任何一支指向掛著決策的舊憑證',
          with_decisions == 0,
          '🚨 %d 支的第一名掛著決策：%s；'
          '⚠️ 這些就是「早該先讀」——**而第 706 輪已經證明不讀會出事**'
          % (with_decisions,
             {k: v for k, v in results['排除目錄後'].items()
              if v['decisions']}))

    doc = {
        'schemaVersion': 1,
        'documentType': 'index-self-pollution',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'problem': (
            '🚨 索引的 JSON 列著**全部識別字**，登記簿列著**全部決策與報告**——'
            '⚠️ 它們跟任何查詢都高度相符，於是**永遠佔住第一名**，'
            '**🚫 把真正該讀的憑證擠下去。**'),
        'catalogues': sorted(catalogues),
        'topHitIsCatalogue': {'未排除': before, '排除目錄後': after},
        'chainTopHits': results['排除目錄後'],
        'retroTest': {'target': RETRO_TARGET, 'rank': rank,
                      'decisionsReached': retro_decisions},
        'whyTwoTests': (
            '🚨 只過一題不算：**回溯測試**防止修過頭（把真的線索也排掉），'
            '**本輪這題**證明真的修到（目錄不再霸佔第一名）。'),
        'connectsTo': (
            '⚠️ 第 673 輪曾記下「加上決策代號後，第 670 輪那個 3／8 翻成 0／8，'
            '該指標對詞彙變動不穩」——'
            '**🚨 現在知道原因了：加上決策代號讓目錄型憑證更容易命中，'
            '於是它把真的線索擠掉了。**'),
        'methodLimit': (
            '⚠️ 本支只排除**兩種** `documentType`；'
            '🚨 若日後又出現別的目錄型產物（例如全語料對帳表），'
            '**同樣的污染會再發生**，🚫 而本支不會自動認出它。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n708 索引的自我污染 ===')
    print('   目錄型憑證 %d 支' % len(catalogues))
    print('   第一名是目錄的比例：未排除 %d／%d → 排除後 %d／%d'
          % (before[0], before[1], after[0], after[1]))
    print('   排除後、本串指向掛著決策的舊憑證：')
    for name, info in sorted(results['排除目錄後'].items()):
        if info['decisions']:
            print('      %-42s → %-40s %s'
                  % (name, info['top'], info['decisions']))
    print('   回溯測試：n594 名次 %s｜前五連到 %s'
          % (rank or '未進榜', retro_decisions))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
