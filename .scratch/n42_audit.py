import json, os, re
from collections import Counter
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
ent = {e['candidateId']: e for e in d['entries']}
op = {k: v['opinion'] for k, v in ent.items()}
rc_path = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc_path):
    rc = json.load(open(rc_path, encoding='utf-8'))
    for e in rc['entries']:
        op[e['candidateId']] = e['effectiveDecision']

eff = Counter(op.values())
print('effective:', dict(eff))

# n+42 rules 1,2,3,4,6,7,8 -> exclude. Only rule 5 keeps unclear.
# So: every effectively-unclear record must be a rule-5 case (title hits but
# population undisclosed / no abstract fail-closed), NOT one of the other seven.
pat = {
  'imm(1)': r'免疫|IgA|細胞激素|發炎標記|感染',
  'cmp(2)': r'同劑量|allowlist|等熱量安慰劑|對照臂',
  'n35(3)': r'n\+35|結果軸.*同等',
  'team(4)': r'間歇性場地|團隊球類|足球|袋棍球|澳式',
  'retr(6)': r'撤稿|Retracted|勘誤|erratum',
  'route(7)': r'胃內灌注|靜脈|漱口',
  'age(8)': r'低於契約下限|小兒|青少年|歲.*低於',
}
unc = [c for c, o in op.items() if o == 'unclear']
print('effectively-unclear count:', len(unc))
hits = Counter()
flagged = []
for c in unc:
    r = ent[c]['reason']
    tags = [k for k, p in pat.items() if re.search(p, r)]
    if tags:
        hits.update(tags)
        flagged.append((c[-8:], tags, r[:90]))
print('unclear matching a now-ruled category:', dict(hits))
for f in flagged[:25]:
    print(' ', f[0], f[1], f[2])
print('total flagged:', len(flagged))
