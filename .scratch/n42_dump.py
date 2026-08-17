import json, os, re, sys
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
ent = {e['candidateId']: e for e in d['entries']}
op = {k: v['opinion'] for k, v in ent.items()}
rc_path = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc_path):
    for e in json.load(open(rc_path, encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']
order = [e['candidateId'] for e in d['entries']]
unc = [c for c in order if op[c] == 'unclear']
RULES = [
    ('R8', r'青少年|小兒|18 歲以下|adolescent'),
    ('R7', r'靜脈|胃內灌注|漱口|輸注|infusion'),
    ('R4', r'足球|橄欖球|曲棍球|袋棍球|澳式|籃球|手球|間歇性場地|games player'),
    ('R1', r'免疫|IgA|細胞激素|cytokine|發炎標記|上呼吸道|感染率'),
    ('R2', r'同劑量|相同 .{0,12}(glucose|CHO|葡萄糖)|皆攝取相同|無 CHO 劑量|無安慰劑臂|對照臂為|等熱量'),
    ('R6', r'撤稿|Retracted|勘誤|erratum'),
    ('R3', r'n\+35|結果軸與其他軸同等'),
]
lo, hi = int(sys.argv[1]), int(sys.argv[2])
n = 0
for c in unc:
    r = ent[c]['reason']
    tags = [k for k, p in RULES if re.search(p, r)]
    if not tags:
        continue
    n += 1
    if not (lo <= n <= hi):
        continue
    print(f'--- #{n} {c[-8:]} {tags}')
    print(r)
    print()
