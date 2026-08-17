import json, io, os, re
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc = json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))
overlaid = {e['candidateId'] for e in rc['entries']}
item = {it['candidateId']: it for it in w['items']}

# Second net, independent of my own wording: effective-unclear entries whose ABSTRACT
# contains NO comparison-signalling token at all. A genuine single-arm study should
# fall in here; a multi-arm one almost never will.
cmp_pat = re.compile(
    r'\bvs\.?\b|versus|placebo|\bcontrol\b|controlled|compared (?:with|to)|comparison|'
    r'crossover|cross-over|randomi[sz]ed|randomly|either .{0,40}\bor\b|'
    r'\bgroups?\b|\btrials?\b|\barms?\b|\bconditions?\b|counter-?balanced|double-?blind',
    re.I)

unc = [e for e in d['entries'] if e['opinion'] == 'unclear' and e['candidateId'] not in overlaid]
buf = []
for e in unc:
    cid = e['candidateId']
    it = item.get(cid, {})
    ab = (it.get('abstract') or '')
    if not ab.strip():
        buf.append(('BLANK-ABS', cid, (it.get('title') or '')[:75]))
    elif not cmp_pat.search(ab):
        buf.append(('NO-CMP-TOKEN', cid, (it.get('title') or '')[:75]))
print('effective-unclear pool:', len(unc))
print('net-B hits:', len(buf))
for t, cid, ti in buf:
    print(' -', t, cid[-8:], ti)
