import json, io, os, re
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc = json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))
overlaid = {e['candidateId']: e['effectiveDecision'] for e in rc['entries']}
item = {it['candidateId']: it for it in w['items']}

cmp_pat = re.compile(
    r'\bvs\.?\b|versus|placebo|\bcontrol\b|controlled|compared (?:with|to)|comparison|'
    r'crossover|cross-over|randomi[sz]ed|randomly|either .{0,40}\bor\b|'
    r'\bgroups?\b|\btrials?\b|\barms?\b|\bconditions?\b|counter-?balanced|double-?blind|'
    r'\bwith and without\b|\bwithout\b',
    re.I)
reason_pat = re.compile(r'單一臂|單臂|無對照|無比較臂')

# sweep the ADVANCE pool (effective advance)
adv = [e for e in d['entries']
       if overlaid.get(e['candidateId'], e['opinion']) == 'advance']
hits = []
for e in adv:
    cid = e['candidateId']
    ab = (item.get(cid, {}).get('abstract') or '')
    if not ab.strip():
        hits.append(('BLANK', cid, (item.get(cid, {}).get('title') or '')[:70]))
    elif not cmp_pat.search(ab):
        hits.append(('NO-CMP', cid, (item.get(cid, {}).get('title') or '')[:70]))
    elif reason_pat.search(e['reason']):
        hits.append(('REASON', cid, (item.get(cid, {}).get('title') or '')[:70]))
print('effective-advance pool:', len(adv))
print('single-arm suspects in ADVANCE:', len(hits))
for t, cid, ti in hits:
    print(' -', t, cid[-8:], ti)
