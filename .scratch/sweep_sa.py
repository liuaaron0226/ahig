import json, io, os, re
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc_path = OUT + '/post-ruling-reclassification.json'
overlaid = set()
if os.path.exists(rc_path):
    overlaid = {e['candidateId'] for e in json.load(open(rc_path, encoding='utf-8'))['entries']}

item = {it['candidateId']: it for it in w['items']}

# effective-unclear only: raw unclear and not already overlaid
unc = [e for e in d['entries'] if e['opinion'] == 'unclear' and e['candidateId'] not in overlaid]

# two independent nets:
#  (a) my own reasons mentioning no-control / single-arm wording
#  (b) abstract text carrying explicit single-arm markers
reason_pat = re.compile(r'單一臂|單臂|無對照|無比較臂|無安慰劑|全程單一補給')
abs_pat = re.compile(r'uncontrolled|single[- ]arm|open[- ]label|no control|without a control|all (?:subjects|participants) (?:ingested|consumed|received)', re.I)

hits = []
for e in unc:
    cid = e['candidateId']
    it = item.get(cid, {})
    ab = (it.get('abstract') or '')
    a = bool(reason_pat.search(e['reason']))
    b = bool(abs_pat.search(ab))
    if a or b:
        hits.append((cid, 'reason' if a else '', 'abs' if b else '', (it.get('title') or '')[:80]))

print('effective-unclear pool:', len(unc))
print('candidate hits:', len(hits))
for h in hits:
    print(' -', h[0][-8:], '[%s%s]' % (h[1], h[2]), h[3])
