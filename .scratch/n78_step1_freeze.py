# -*- coding: utf-8 -*-
"""n+57 第 1 步：凍結終止證據（第二次觸發）。

🚨 依 n+78，凍結證據須新增 `triggerCause` 欄位，明載本次跨越 α 係由
`3d617443` 之改判所致，並附改判前後之 pScore／windowSize。

⚠️ 本檔另記錄一件我在執行中查到、且會影響「觸發是否成立」的事：
`term.py` 與 `term2.py` 給出不同判定，成因有二（labels 序列組成、n_total
取哪個池）。**兩者皆已量測並寫入證據**，由協調者裁示以何者為準——
執行室不自行選定（n+57 第 6 步：只回報、不宣告）。

第 1 步之要求：先落盤，再做任何其他事。
"""
import hashlib
import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import (  # noqa: E402
    evaluate_termination, p_score)

ROOT = Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
            r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT / 'standard-full-screen-pass-1'
queue = json.loads((ROOT / 'screening-queue' / 'queue.json')
                   .read_text(encoding='utf-8'))
w_raw = (OUT / 'worksheet.json').read_text(encoding='utf-8')
w = json.loads(w_raw)

op = {e['candidateId']: e['opinion'] for e in
      json.loads((OUT / 'judgements.json').read_text(encoding='utf-8'))['entries']}
raw_n = len(op)
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    for e in json.loads((OUT / f).read_text(encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']

by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
cont = 0
while all(c in op for c in by_page.get(cont + 1, [None])):
    cont += 1

exc = json.loads((OUT / 'p-score-sequence-exclusions.json')
                 .read_text(encoding='utf-8'))
out_perm = {e['candidateId'] for e in exc['entries']
            if e.get('state') == 'out-of-sequence-permanent'}
pending = {e['candidateId'] for e in exc['entries']
           if e.get('state') != 'out-of-sequence-permanent'
           and e['page'] > cont}
skip = out_perm | pending

seq_items = [it for it in w['items']
             if it['candidateId'] in op and it['candidateId'] not in skip]
labels = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
          for it in seq_items]

std = p_score(labels, w['itemCount'])

# 全 lane 版本（term2 之問法），一併落盤供協調者裁示
other = []
for d in ('safety-full-screen-pass-1', 'critical-harms-sweep',
          'critical-harms-sweep-orphans'):
    p = ROOT / d / 'judgements.json'
    if p.exists():
        for e in json.loads(p.read_text(encoding='utf-8'))['entries']:
            if e['candidateId'] not in op:
                other.append((e['candidateId'], e['opinion']))
alllane = evaluate_termination(
    queue,
    [(it['candidateId'], op[it['candidateId']]) for it in w['items']
     if it['candidateId'] in op] + other,
    out_of_sequence=out_perm)

# 標準線版本之 evaluate_termination：其他 lane 併入第三態（已篩畢、不入序列）
std_eval = evaluate_termination(
    queue,
    [(it['candidateId'], op[it['candidateId']]) for it in w['items']
     if it['candidateId'] in op] + other,
    p_score_excluded=pending,
    out_of_sequence=out_perm | {c for c, _ in other})

from ahig.contracts.freeze import content_hash  # noqa: E402
# 🚨 種子錨定須用 content_hash(worksheet)，與第一次抽樣所用者相同。
# 本檔第一版寫的是 hashlib.sha256(檔案位元組)，那是另一個值——
# 若照它抽樣，種子會與第一次不同，兩次抽樣就無從比較重疊。
worksheet_sha = content_hash(w)
worksheet_file_sha = hashlib.sha256(w_raw.encode('utf-8')).hexdigest()

# 抽樣母體＝主篩工作單內尚未判讀者。
# 🚨 第一版我寫成「queue 中 lane==standard-screening 且未判者」，量到 1629，
# 比心跳一路報的 1460 多 169。查證：那 169 筆全在 screening-shadow-pass-a/b
# 之工作單內且兩份皆已判讀（ADR-0007 盲化雙篩驗證樣本），
# **不在主篩工作單內是設計使然，不是漏篩**。母體須為 1460。
ws_ids = {it['candidateId'] for it in w['items']}
not_screened = sorted(cid for cid in ws_ids if cid not in op)

doc = {
    'documentType': 'termination-evidence-freeze',
    'schemaVersion': '1.0',
    'adr': 'ADR-0008',
    'lane': 'b11-exogenous-cho-endurance / standard-full-screen-pass-1',
    'occurrence': 2,
    'previousOccurrence': {
        'atPage': 279,
        'pScore': 0.046023,
        'windowSize': 177,
        'outcome': 'termination-void (tail spot check returned 2 hits)',
        'ruling': 'n+72',
    },
    'triggerCause': {
        'kind': 'reclassification',
        'candidateId': [c for c in op if c.endswith('3d617443')][0],
        'change': 'unclear -> exclude',
        'ruling': 'n+77 (五) criterion; n+78 (二) authorisation',
        'reason': ('The record sat at p294 with 86 excludes after it, i.e. it '
                   'was the last hit in the sequence; excluding it merges the '
                   'window from 115 to 201.'),
        'before': {'pScore': 0.076292, 'windowSize': 115,
                   'relevantFound': 719},
        'after': {'pScore': 0.012405, 'windowSize': 201,
                  'relevantFound': 718},
        'note': ('Criterion preceded measurement and is checkable: n+77 ruled '
                 'the publication-type exclusion a round before the sequence '
                 'position was known. Executor measured only after the ruling, '
                 'then halted per n+62 for explicit authorisation, which n+78 '
                 'granted after independently recomputing both figures.'),
    },
    'standardLaneSequence': {
        'note': ('The authoritative construction used throughout this lane: '
                 'standard-screening worksheet order only, n_total = worksheet '
                 'itemCount. Verified against the first trigger: reproducing '
                 'pScore 0.046023 at window 177 requires n_total 9091, not '
                 '15425.'),
        'nTotal': w['itemCount'],
        'contiguousPagesJudged': cont,
        **std,
        'pScoreExcludedCount': len(pending),
        'outOfSequenceCount': len(out_perm),
        'crossesAlpha': std['pScore'] < 0.05,
    },
    'allLaneSequenceForComparison': {
        'note': ('term2.py construction: every lane concatenated into one '
                 'label stream, n_total = len(queue). Recorded for the '
                 'coordinator, NOT used as the trigger determination. Its '
                 'windowSize collapses to 1 because unclear records sit near '
                 'the end of the appended non-standard judgements -- the '
                 'semantic breakage n+70 (二) already identified.'),
        'nTotal': len(queue),
        'pScore': alllane['pScore'],
        'windowSize': alllane['windowSize'],
        'allowedToStop': alllane['allowedToStop'],
    },
    'evaluateTerminationStandardBasis': {
        'note': ('evaluate_termination with non-standard lanes placed in the '
                 'third state (screened, permanently out of sequence) so the '
                 'label stream is the standard lane alone. n_total is still '
                 'len(queue) = 15425 by construction, which is why its pScore '
                 'differs from the standard-lane figure above. Both are '
                 'recorded rather than one being chosen here.'),
        'pScore': std_eval['pScore'],
        'windowSize': std_eval['windowSize'],
        'relevantFound': std_eval['relevantFound'],
        'screenedCount': std_eval['screenedCount'],
        'poolSize': std_eval['poolSize'],
        'notScreenedCount': std_eval['notScreenedCount'],
        'mandatoryLanesFullyScreened': std_eval['mandatoryLanesFullyScreened'],
        'pScoreExcludedCount': std_eval['pScoreExcludedCount'],
        'outOfSequenceCount': std_eval['outOfSequenceCount'],
        'allowedToStop': std_eval['allowedToStop'],
        'terminationEvidenceHash': std_eval['terminationEvidenceHash'],
    },
    'openQuestionForCoordinator': (
        'Which n_total does ADR-0008 intend for this lane -- the standard '
        'screening worksheet (9091) or the full queue across all lanes '
        '(15425)? Every figure reported in this lane to date, including the '
        'first trigger the coordinator verified digit by digit, used 9091. '
        'The executor does not select between them here (n+57 step 6: report, '
        'do not declare).'),
    'tailSpotCheckPopulation': {
        'count': len(not_screened),
        'definition': 'standard-full-screen-pass-1 worksheet items not yet judged',
        'note': ('A first draft of this script used queue lane == '
                 'standard-screening instead, giving 1629. The extra 169 are '
                 'the ADR-0007 blinded shadow-pass sample: they sit in '
                 'screening-shadow-pass-a and -b worksheets and are judged in '
                 'both, so their absence from the main worksheet is by design '
                 'rather than a screening gap. Sampling from 1629 would have '
                 'drawn records outside the not-screened tail of this lane.'),
    },
    'seedAnchorValue': worksheet_sha,
    'worksheetFileSha256': worksheet_file_sha,
    'seedAnchorNote': ('Tail spot check seed anchors on seedAnchorValue '
                       'above; this lane has no queueHash (n+51 approved '
                       'equivalent). Do not call it queueHash.'),
    'judgementsEntryCount': raw_n,
}

dest = Path('.scratch/n78_termination_evidence.json')
io.open(dest, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 第 1 步：證據已落盤 → %s' % dest)
print()
print('標準線序列（本 lane 歷來之權威建構）')
print('  n_total %d  window %d  pScore %.6f  跨越 α：%s'
      % (w['itemCount'], std['windowSize'], std['pScore'],
         std['pScore'] < 0.05))
print('  relevantFound %d  screenedCount %d'
      % (std['relevantFound'], std['screenedCount']))
print()
print('⚠️ 並陳（不由執行室選定）')
print('  term2 全 lane 串接      window %d  pScore %.6f  allowedToStop %s'
      % (alllane['windowSize'], alllane['pScore'], alllane['allowedToStop']))
print('  第三態版（僅標準線入序列）window %d  pScore %.6f  allowedToStop %s'
      % (std_eval['windowSize'], std_eval['pScore'],
         std_eval['allowedToStop']))
print('  terminationEvidenceHash %s'
      % std_eval['terminationEvidenceHash'][:32])
print()
print('未篩（標準線）%d 筆；worksheet SHA-256 %s'
      % (len(not_screened), worksheet_sha[:32]))
