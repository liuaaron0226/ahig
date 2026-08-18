# -*- coding: utf-8 -*-
"""n+57 第二節【第 1 步】：凍結證據並落盤。

🚨 **觸發事實**：page 279 判畢後實算 `pScore = 0.0460 < 0.05`。
依 n+68（〇）與 n+57 第二節，**已於第 343 輪結束後立即停判**
（page 280 起未動），本檔為停判後之第一個動作。

⚠️ **先落盤再做任何其他事**——事後補記的證據沒有稽核價值（n+57 第 1 步）。
⚠️ 本檔唯讀 `judgements.json` 與 `worksheet.json`，只寫證據檔。

⚠️ **順序證據寫進內容而非檔案時間**（n+67 四）：
本檔產物自帶 `producedAt`，後續各步之產物記錄其所讀入之
前一步檔案雜湊，使順序可由 committed 內容本身覆核。
"""
import io
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import (  # noqa: E402
    content_hash, evaluate_termination)

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))

# ---- 決策序列：與 term.py 同一套覆蓋層邏輯（協調者 b1bc147 認可）----
op = {e['candidateId']: e['opinion'] for e in d['entries']}
raw = Counter(op.values())

n_over = 0
rc_path = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc_path):
    rc = json.load(io.open(rc_path, encoding='utf-8'))
    seen = set()
    for e in rc['entries']:
        cid = e['candidateId']
        assert cid in op, 'reclass id not judged: ' + cid
        assert cid not in seen, 'duplicate in reclass: ' + cid
        assert op[cid] == e['originalOpinion'], 'originalOpinion mismatch'
        seen.add(cid)
        op[cid] = e['effectiveDecision']
        n_over += 1

n_ratchet = 0
rr_path = OUT + '/post-ruling-abstract-rescreen.json'
if os.path.exists(rr_path):
    rr = json.load(io.open(rr_path, encoding='utf-8'))
    for e in rr['entries']:
        cid = e['candidateId']
        assert cid in op, 'rescreen id not judged: ' + cid
        op[cid] = e['effectiveDecision']
        n_ratchet += 1

order = [e['candidateId'] for e in d['entries']]
decisions_in_order = [(cid, op[cid]) for cid in order]

queue = [{'candidateId': it['candidateId']} for it in w['items']]

res = evaluate_termination(queue, decisions_in_order)

judged = {cid for cid, _ in decisions_in_order}
not_screened = [it['candidateId'] for it in w['items']
                if it['candidateId'] not in judged]

# ⚠️ 本 lane 無 queueHash，依 n+51 已核准之等效替代：worksheet SHA-256。
# **產物中明載所用錨定值之來源，不得逕稱 queueHash**（n+57 第 3 步）。
worksheet_hash = content_hash(w)

evidence = {
    'schemaVersion': 1,
    'documentType': 'termination-evidence-freeze',
    'step': 'n+57 section 2 step 1 (freeze evidence)',
    'producedAt': datetime.now(timezone.utc).isoformat(),
    'producedBy': 'claude-opus-5[1m] executor-session round 344',
    'trigger': {
        'atPage': 279,
        'note': ('page 279 判畢後實算 pScore < 0.05；'
                 '依 n+68（〇）立即停判，page 280 起未動'),
    },
    'terminationResult': res,
    'counts': {
        'judgedCount': len(decisions_in_order),
        'poolSize': len(queue),
        'notScreenedCount': len(not_screened),
        'rawOpinions': dict(raw),
        'effectiveDecisions': dict(Counter(op.values())),
        'overlayApplied': n_over,
        'ratchetApplied': n_ratchet,
    },
    'anchors': {
        'worksheetSha256': worksheet_hash,
        'anchorNote': ('本 lane 無 queueHash；依 n+51 核准之等效替代，'
                       '以 worksheet 之 SHA-256 為抽樣種子錨定。'
                       '⚠️ 此值為 worksheet 雜湊，不得稱為 queueHash。'),
        'judgementsSha256': content_hash(d),
    },
}
evidence['terminationEvidenceHash'] = content_hash(evidence)

path = '.scratch/n68_termination_evidence.json'
json.dump(evidence, io.open(path, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('=' * 66)
print('n+57 第二節【第 1 步】證據已凍結並落盤')
print('=' * 66)
print('  產物：%s' % path)
print('  producedAt：%s' % evidence['producedAt'])
print('  terminationEvidenceHash：%s' % evidence['terminationEvidenceHash'])
print()
print('  pScore            %.6f' % res['pScore'])
print('  windowSize        %d' % res['windowSize'])
print('  relevantFound     %d' % res['relevantFound'])
print('  screenedCount     %d' % res['screenedCount'])
print('  poolSize          %d' % res['poolSize'])
print('  notScreenedCount  %d' % len(not_screened))
print('  allowedToStop     %s' % res.get('allowedToStop'))
print()
print('  worksheetSha256   %s' % worksheet_hash)
print('  ⚠️ 上列為 worksheet 雜湊，非 queueHash（n+57 第 3 步所令之明載）')
