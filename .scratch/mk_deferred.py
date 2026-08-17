import json, os, re, sys
os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score

RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
ent = {e['candidateId']: e for e in d['entries']}
op = {k: v['opinion'] for k, v in ent.items()}
for e in json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))['entries']:
    op[e['candidateId']] = e['effectiveDecision']

RULED = [('R1', 'immune-outcome', r'免疫|IgA|細胞激素|嗜中性球|淋巴球|自然殺手'),
         ('R2', 'comparator-gap', r'同劑量|皆攝取相同|無安慰劑|無 CHO 劑量|對照臂為|等熱量|兩臂皆|不給液體'),
         ('R3', 'outcome-adjacent', r'非契約清單|非契約 inScopeOutcomes|不在六項|非契約六項'),
         ('R4', 'intermittent-team-sport', r'足球|橄欖球|曲棍球|籃球|球類專項|間歇性場地|games player'),
         ('R7', 'route', r'靜脈|漱口|輸注|胃內灌注'),
         ('R8', 'age', r'青少年|adolescent')]
# Reuse the EXACT gap definition that produced the 28 reported in round 228,
# rather than retyping it (a retyped variant silently yielded 39).
GAP = (r'裁定 62|無訓練狀態措辭|無訓練措辭|無訓練程度措辭|無訓練程度形容詞|'
       r'未載訓練|訓練狀態未揭露|訓練狀態未報告|不自行擴張|措辭含糊|含糊|'
       r'未揭露|摘要截斷|continues|無摘要|截斷|'
       r'劑量未載|未載劑量|未載飲用量|未載體重|未載濃度|不換算|不寫入推估|'
       r'時序未載|未載給予時點|未載攝取時點|timing 未載|未明確區分|未載明時序|'
       r'未載受試者|人數.{0,6}未|年齡.{0,6}未|未載運動強度|方案未揭露|未載分派|未載隨機|'
       r'題摘層資訊不足|資訊不足|需換算|劑量需換算|未報告客觀指標|未達契約 trained|'
       r'無法確定|無法判定|無從確認|無從判定|無從分離|是否另有|是否可用|是否構成|'
       r'確認是否|是否符合|是否屬|可分離性|解讀受限|需視')

order = [e['candidateId'] for e in d['entries']]
unc = [c for c in order if op[c] == 'unclear']
bucketC, bucketB, bucketA = [], [], []
for c in unc:
    r = ent[c]['reason']
    ax = [(k, t) for k, t, p in RULED if re.search(p, r)]
    if not ax:
        bucketA.append(c)
    elif re.search(GAP, r):
        bucketB.append((c, ax))
    else:
        bucketC.append((c, ax))

# Guardrail check: these records must NOT change the sequence at all.
by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(x in op for x in by_page.get(contiguous + 1, [None])):
    contiguous += 1
excl = {e['candidateId'] for e in json.load(open(OUT + '/p-score-sequence-exclusions.json', encoding='utf-8'))['entries'] if e['page'] > contiguous}
seq = [it['candidateId'] for it in w['items'] if it['candidateId'] in op and it['candidateId'] not in excl]
before = p_score([1 if op[c] in ('advance', 'unclear') else 0 for c in seq], w['itemCount'])

doc = {
    'schemaVersion': 1,
    'source': 'standard-full-screen-pass-1',
    'ruling': 'n+43',
    'producedBy': 'B.11 execution room',
    'semantics': ('Holding tags only. These records keep their original judgement '
                  '(unclear) and their p-score sequence label is UNCHANGED. Per ruling '
                  'n+43 case (b), rulings are not retroactive: the blocker cited in each '
                  'reason was ruled exclude by n+42 AFTER the judgement was made, so the '
                  'judgement stands and the record is resolved at full-text instead. '
                  'This file must never be read by the termination statistic.'),
    'affectsTerminationStatistic': False,
    'pScoreBefore': before['pScore'],
    'pScoreAfter': before['pScore'],
    'windowSizeBefore': before['windowSize'],
    'windowSizeAfter': before['windowSize'],
    'producedAtJudgedCount': len(op),
    'bucketCounts': {'A_noRuledAxis': len(bucketA),
                     'B_ruledAxisPlusInfoGap': len(bucketB),
                     'C_ruledAxisOnly': len(bucketC)},
    'entries': [{'candidateId': c, 'opinion': 'unclear', 'holdingTag': 'post-ruling-deferred',
                 'ruledAxes': [t for _, t in ax], 'rulingThatRemovedBlocker': 'n+42'}
                for c, ax in bucketC],
}
path = OUT + '/post-ruling-deferred-tags.json'
json.dump(doc, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('wrote', path)
print('bucket A/B/C =', len(bucketA), len(bucketB), len(bucketC))
print('pScore before/after =', before['pScore'], '/', before['pScore'], '(sequence untouched by design)')

# bucket B ids for the w4b full-text priority list
json.dump({'bucketB': [c for c, _ in bucketB], 'bucketC': [c for c, _ in bucketC]},
          open('.scratch/w4b_buckets.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('bucket ids saved for w4b-design-inputs')
