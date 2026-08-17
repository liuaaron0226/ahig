import json, os, re
from collections import Counter
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
ent = {e['candidateId']: e for e in d['entries']}
op = {k: v['opinion'] for k, v in ent.items()}
overlaid = set()
rc_path = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc_path):
    rc = json.load(open(rc_path, encoding='utf-8'))
    for e in rc['entries']:
        op[e['candidateId']] = e['effectiveDecision']
        overlaid.add(e['candidateId'])

unc = [c for c, o in op.items() if o == 'unclear']

# Ordered: first matching rule wins (most decisive axis first).
RULES = [
    ('R8 age <18',        r'青少年|小兒|18 歲以下|低於契約下限|adolescent'),
    ('R7 route',          r'靜脈|胃內灌注|漱口|輸注|infusion'),
    ('R4 team-sport',     r'足球|橄欖球|曲棍球|袋棍球|澳式|籃球|手球|間歇性場地|games player'),
    ('R1 immune-outcome', r'免疫|IgA|細胞激素|cytokine|發炎標記|上呼吸道|感染率'),
    ('R2 comparator-gap', r'同劑量|相同 .{0,12}(glucose|CHO|葡萄糖)|皆攝取相同|無 CHO 劑量|無安慰劑臂|對照臂為|等熱量'),
    ('R6 retracted',      r'撤稿|Retracted|勘誤|erratum'),
    ('R3 n+35 outcome',   r'n\+35|結果軸與其他軸同等'),
]
# Rule 5 (keep unclear) markers: information genuinely absent.
R5 = r'未揭露|未報告|未載明|無摘要|比例不明|未給定|不明|未特定|需換算|未說明'

buckets = Counter()
samples = {}
r5_only = 0
for c in unc:
    r = ent[c]['reason']
    hit = None
    for name, pat in RULES:
        if re.search(pat, r):
            hit = name
            break
    if hit is None:
        r5_only += 1
        continue
    # If the reason ALSO cites missing information, rule 5 (fail-closed) may still govern.
    amb = bool(re.search(R5, r))
    key = hit + (' [+info-gap]' if amb else '')
    buckets[key] += 1
    samples.setdefault(key, []).append((c[-8:], r[:110]))

print('effectively-unclear total:', len(unc))
print('no now-ruled axis cited (stays unclear):', r5_only)
print()
for k, v in buckets.most_common():
    print(f'{v:4d}  {k}')
print()
print('clean (no info-gap) = would convert to exclude:',
      sum(v for k, v in buckets.items() if '[+info-gap]' not in k))
print('ambiguous (cites info-gap too, needs per-record call):',
      sum(v for k, v in buckets.items() if '[+info-gap]' in k))
print('already in overlay:', sum(1 for c in unc if c in overlaid))
print()
for k in list(buckets):
    if '[+info-gap]' in k:
        continue
    print('==', k)
    for s in samples[k][:3]:
        print('   ', s[0], s[1])
