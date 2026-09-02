# -*- coding: utf-8 -*-
"""**先查過再查——識別字索引（按稀有度排序）。**（第 670 輪）

## 🚨 為什麼要有這個

第 662–668 輪查了七輪，🚨 其中一半是**重新撞到已經裁過的東西**：
`D4`（第 594 輪）早就裁過切片器械那 3 項。
⚠️ 而本室當時完全不知道，因為沒有東西查得動「這個東西之前有人碰過嗎」。

## 🚨 本支的第一版是錯的，先講清楚

第一版用「報告代號 ＋ 契約結局**都要命中**」去查，**查不到 n594**——
**🚨 因為 n594 裡根本沒有報告代號**，只有結局名與儀器名。

> **✅ 真正該當鑰匙的是「儀器名稱」，🚫 不是報告代號——因為它稀有。**

## ✅ 於是改成按**稀有度**加權

- 出現在 180 支憑證裡的識別字（例如 `notExtracted-dose-outside-bands`）→ **幾乎沒有資訊**
- 只出現在 2 支裡的（例如某個儀器名稱）→ **一命中就該去讀**

✅ 用 `log(N / 出現支數)` 當權重，把候選排序，🚫 不做模糊比對。

## ✅ 而它必須先證明「當初真的救得了我」

**🚨 回溯測試：只用第 663 輪之前的憑證**，
查第 663 輪當時手上的那四個識別字——**n594 必須排進前五，且必須連得到 D4。**
⚠️ 排不進去，這支索引就蓋不到真正發生過的失誤，🚫 不值得留。

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
OUT = HERE / 'n670_identifier_index.json'
REGISTER = HERE / 'n669_decision_register_v3.json'

ROUND_RE = re.compile(r'^n(\d+)_')
REPORT_RE = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
REASON_RE = re.compile(r'\b(?:notExtracted|escalated)-[a-z0-9-]+\b')
# 🚨 三段以上的 kebab 記號＝受控詞彙（結局代號、儀器名稱……），
# ⚠️ 這是**結構**樣式，🚫 不是關鍵字清單。
KEBAB_RE = re.compile(r'\b[a-z][a-z0-9]*(?:-[a-z0-9]+){2,}\b')
# 🚨 第 673 輪發現的破口：登記簿的決策代號 D1–D24 本來不在詞彙裡，
# ⚠️ 也就是「這個決策之前討論過嗎」根本查不動。
DECISION_RE = re.compile(r'\bD[1-9][0-9]?\b')

CHAIN = range(662, 670)
RETRO_CUTOFF = 663
# 🚨 第 663 輪當時手上真正有的四個識別字
RETRO_QUERY = ['7a6ac1559c740fd6', 'muscle-glycogen-post-exercise',
               'needle-biopsy-vastus-lateralis',
               'acid-hydrolysis-freeze-dried-biopsy']
RETRO_MUST_FIND = 'n594_a3_first_measurement.json'
RAREST_K = 5
TOP_N = 5


def artefacts():
    for path in sorted(HERE.glob('n*.json')):
        m = ROUND_RE.match(path.name)
        if m:
            yield int(m.group(1)), path


def identifiers(text):
    return (set(REPORT_RE.findall(text)) | set(REASON_RE.findall(text))
            | set(KEBAB_RE.findall(text)) | set(DECISION_RE.findall(text)))


# 🚨 第 708 輪查出的自我污染：索引的 JSON 列著**全部識別字**、
# 登記簿列著**全部決策與報告**，⚠️ 於是它們跟任何查詢都相符、永遠佔住第一名，
# **🚫 把真正該讀的憑證擠下去**（實測：未排除時 10／17 支的第一名是目錄）。
# ✅ 目錄不是發現，故排除在索引之外。
CATALOGUE_TYPES = {'identifier-index', 'pending-decision-register'}


def is_catalogue(path):
    try:
        doc = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    return isinstance(doc, dict) and \
        doc.get('documentType') in CATALOGUE_TYPES


def build(max_round=None):
    index = collections.defaultdict(set)
    per_file = {}
    for round_no, path in artefacts():
        if max_round is not None and round_no >= max_round:
            continue
        if is_catalogue(path):
            continue
        try:
            found = identifiers(path.read_text(encoding='utf-8'))
        except OSError:
            continue
        per_file[path.name] = found
        for ident in found:
            index[ident].add(path.name)
    return index, per_file


def weights(index, corpus_size):
    """稀有度權重。🚨 出現得越普遍，權重越接近 0。"""
    return {ident: math.log(corpus_size / len(files))
            for ident, files in index.items() if files}


def search(query, index, per_file, exclude=()):
    corpus = len(per_file) or 1
    w = weights(index, corpus)
    scores = collections.Counter()
    matched = collections.defaultdict(list)
    for ident in query:
        for name in index.get(ident, ()):
            if name in exclude:
                continue
            scores[name] += w.get(ident, 0.0)
            matched[name].append(ident)
    return scores, matched, w


def decisions_by_file():
    """證據檔 → 決策代號。⚠️ 證據字串可能帶「→ 欄位」後綴，🚨 要切掉。"""
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    mapping = collections.defaultdict(set)
    for item in register['items']:
        for part in str(item['evidence']).replace('；', ';').split(';'):
            name = part.split('→')[0].strip()
            if name:
                mapping[name].add(item['id'])
    return mapping


def main():
    index, per_file = build()
    to_decision = decisions_by_file()

    # ✅ 回溯測試：只用第 663 輪之前的憑證。
    retro_index, retro_files = build(max_round=RETRO_CUTOFF)
    retro_scores, retro_matched, retro_w = search(
        RETRO_QUERY, retro_index, retro_files)
    retro_top = retro_scores.most_common(TOP_N)
    retro_rank = next((i + 1 for i, (name, _) in enumerate(retro_top)
                       if name == RETRO_MUST_FIND), None)
    retro_decisions = sorted({d for name, _ in retro_top
                              for d in to_decision.get(name, set())})

    # ⚠️ 這一串的每一支：它用到的**最稀有**識別字，更早哪一支碰過。
    corpus_w = weights(index, len(per_file) or 1)
    chain = {}
    for round_no, path in artefacts():
        if round_no not in CHAIN:
            continue
        # 🚨 只看**本串開始之前**的憑證——⚠️ 否則會撞到本串自己產生的決策，
        # 那是循環，🚫 不是「早該先讀」。
        older = {p.name for r, p in artefacts() if r < min(CHAIN)}
        # 🚨 用整支的識別字全集去查會被常見識別字稀釋——
        # ⚠️ 回溯測試之所以成功，是因為只查了 4 個**針對性**的識別字。
        # ✅ 故這裡也只用最稀有的幾個，與已證明有效的用法一致。
        mine = sorted(per_file.get(path.name, set()),
                      key=lambda i: -corpus_w.get(i, 0.0))[:RAREST_K]
        scores, matched, _ = search(mine, index, per_file,
                                    exclude={path.name})
        scores = collections.Counter({k: v for k, v in scores.items()
                                      if k in older})
        best = scores.most_common(1)
        rarest = max(per_file.get(path.name, set()),
                     key=lambda i: corpus_w.get(i, 0.0), default=None)
        chain[path.name] = {
            'queriedWith': mine,
            'rarestIdentifier': rarest,
            'rarestWeight': round(corpus_w.get(rarest, 0.0), 2),
            'closestEarlierArtefact': best[0][0] if best else None,
            'closestScore': round(best[0][1], 1) if best else 0.0,
            'itsDecisions': sorted(to_decision.get(best[0][0], set()))
            if best else [],
        }

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('索引真的建起來了（必觸發之正對照）',
          len(index) >= 50 and len(per_file) >= 40,
          '🚨 識別字 %d 個、憑證 %d 支；⚠️ 太少代表樣式沒抓到東西'
          % (len(index), len(per_file)))
    probe('查捏造的識別字必須查無（必觸發之反向）',
          not index.get('ffffffffffffffff')
          and not index.get('outcome-that-cannot-exist-670'),
          '🚨 兩個捏造的識別字都查無；⚠️ 若查得到，索引是在亂比對')

    # ✅ 必觸發之反向：權重要真的分得開，🚫 否則排序只是在數命中次數。
    # ⚠️ 本室第一版寫「最普遍者權重須 < 0.3」——
    # 🚨 那個前提在這個語料裡不成立：最常見的識別字也只出現在 31／185 支。
    most_common_ident = max(index, key=lambda i: len(index[i]))
    rarest_ident = min(index, key=lambda i: len(index[i]))
    spread = (corpus_w.get(rarest_ident, 0.0)
              / max(corpus_w.get(most_common_ident, 1e-9), 1e-9))
    probe('稀有度權重真的分得開（必觸發之反向）',
          spread >= 2.0,
          '🚨 最普遍者 `%s` 出現 %d／%d 支、權重 %.2f；'
          '最稀有者出現 %d 支、權重 %.2f；倍率 %.1f；'
          '⚠️ 倍率接近 1 就代表排序只是在數命中次數'
          % (most_common_ident, len(index[most_common_ident]), len(per_file),
             corpus_w.get(most_common_ident, 0.0),
             len(index[rarest_ident]), corpus_w.get(rarest_ident, 0.0),
             spread))

    # 🚨 這一道是關鍵：它必須救得了當初的本室。
    probe('只用第 663 輪之前的憑證，n594 排得進前 %d 且連得到 D4（必觸發之回溯）'
          % TOP_N,
          retro_rank is not None and 'D4' in retro_decisions,
          '🚨 前 %d 名：%s；n594 名次 %s；連到的決策 %s；'
          '⚠️ 排不進去就代表這支索引蓋不到真正發生過的失誤'
          % (TOP_N, [(n, round(s, 1)) for n, s in retro_top],
             retro_rank or '未進榜', retro_decisions or '無'))

    # 🚨 這一道是答案。
    should_have_read = {n: v for n, v in chain.items() if v['itsDecisions']}
    probe('這一串沒有任何一支「早該先讀某支已掛決策的舊憑證」',
          not should_have_read,
          '🚨 %d／%d 支的最近舊憑證掛著決策：%s；'
          '⚠️ 這正是第 669 輪發現的那件事，現在指得出是哪一支'
          % (len(should_have_read), len(chain),
             {n: '%s → %s' % (v['closestEarlierArtefact'], v['itsDecisions'])
              for n, v in should_have_read.items()}))

    doc = {
        'schemaVersion': 2,
        'documentType': 'identifier-index',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'identifiers': len(index),
        'artefactsIndexed': len(per_file),
        'index': {k: sorted(v) for k, v in sorted(index.items())},
        'evidenceToDecision': {k: sorted(v)
                               for k, v in sorted(to_decision.items())},
        'retroTest': {
            'cutoffRound': RETRO_CUTOFF,
            'query': RETRO_QUERY,
            'queryWeights': {i: round(retro_w.get(i, 0.0), 2)
                             for i in RETRO_QUERY},
            'top': [{'artefact': n, 'score': round(s, 2),
                     'matched': sorted(retro_matched[n])}
                    for n, s in retro_top],
            'rankOfTarget': retro_rank,
            'decisionsReached': retro_decisions,
        },
        'chainLookback': chain,
        'firstVersionWasWrong': (
            '🚨 本支第一版用「報告代號 ＋ 契約結局**都要命中**」查，'
            '**查不到 n594——因為 n594 裡根本沒有報告代號**。'
            '✅ 真正該當鑰匙的是稀有的**儀器名稱**。'
            '⚠️ 那一版的「舊地重遊率」也每一支都是 100%%，'
            '**🚨 全滿的指標沒有鑑別力**，已整支換掉。'),
        'howToUse': (
            '✅ 開一輪之前，把手上的識別字丟進 `search`，'
            '**🚨 看前五名有沒有掛著決策的舊憑證——有就先讀它。**'),
        # 🚨 底下那句 methodLimit 是第 670 輪寫的，**沒驗過而且太滿**。
        # ✅ 原文保留不動（那是本室當時真的講過的話），
        # ⚠️ 更正寫在 n671_retro_suite.json。
        'correctedBy': (
            '🚨 `n671_retro_suite.json`（第 671 輪）驗過底下那句 methodLimit：'
            '**⚠️ 它一半是錯的**。✅ 實測：D6 那次只要查詢帶上**理由碼**'
            '就查得到 n588，並連得到 D5／D6。'
            '**🚨 而 D4 那次若只用報告代號與結局代號，名次是 18／32、連不到任何決策**——'
            '✅ 故真正的規矩是「查詢必須帶爭點的識別字」，'
            '🚫 不是「識別字救不了 D6 那類」。'),
        'methodLimit': (
            '🚨 本支只索引**識別字**，🚫 索引不到「同一件事用不同識別字談」——'
            '⚠️ 第 667 輪的「GI 佔六成」與 D6 沒有共同的稀有識別字，'
            '**故這支救得了 D4 那次，救不了 D6 那次**。'
            '✅ 寫在這裡，🚫 免得下次高估它。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n670 識別字索引（按稀有度排序）===')
    print('   識別字 %d 個｜憑證 %d 支' % (len(index), len(per_file)))
    print('   回溯測試（只用第 %d 輪之前的憑證）：' % RETRO_CUTOFF)
    for ident in RETRO_QUERY:
        print('      查詢字 %-38s 權重 %.2f'
              % (ident, retro_w.get(ident, 0.0)))
    for i, (name, score) in enumerate(retro_top, 1):
        print('      %d. %-42s %.2f  命中 %s'
              % (i, name, score, sorted(retro_matched[name])))
    print('      n594 名次 %s｜連到的決策 %s'
          % (retro_rank or '未進榜', retro_decisions or '無'))
    print('   這一串每一支的「最近舊憑證」：')
    for name in sorted(chain):
        v = chain[name]
        print('      %-42s → %-38s %s'
              % (name, v['closestEarlierArtefact'], v['itsDecisions'] or ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
