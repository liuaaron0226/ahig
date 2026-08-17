import json, os, re
from collections import Counter
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

# Axes now ruled exclude by n+42 (items 1,2,3,4,6,7,8)
RULED = [
    ('R8-age',   r'青少年|小兒|18 歲以下|adolescent'),
    ('R7-route', r'靜脈|胃內灌注|漱口|輸注'),
    ('R4-team',  r'足球|橄欖球|曲棍球|袋棍球|澳式|籃球|手球|間歇性場地|games player|球類專項'),
    ('R1-imm',   r'免疫|IgA|細胞激素|cytokine|發炎標記|上呼吸道|嗜中性球|淋巴球|自然殺手|NK 細胞'),
    ('R2-cmp',   r'同劑量|皆攝取相同|無 CHO 劑量|無安慰劑|無安慰劑臂|對照臂為|等熱量|兩臂皆|非 allowlist|不給液體|不給任何'),
    ('R6-retr',  r'撤稿|Retracted|勘誤|erratum'),
    ('R3-n35',   r'n\+35|非契約清單|非契約 inScopeOutcomes|非契約六項|不在六項'),
]
# Independent information gaps -> n+42 item 5 preserves unclear (fail-closed)
GAP = (r'裁定 62|無訓練狀態措辭|無訓練措辭|無訓練程度措辭|無訓練程度形容詞|'
       r'未載訓練|訓練狀態未揭露|訓練狀態未報告|不自行擴張|措辭含糊|含糊|'
       r'未揭露|摘要截斷|continues|無摘要|截斷|'
       r'劑量未載|未載劑量|未載飲用量|未載體重|未載濃度|不換算|不寫入推估|'
       r'時序未載|未載給予時點|未載攝取時點|timing 未載|未明確區分|未載明時序|'
       r'未載受試者|人數.{0,6}未|年齡.{0,6}未|未載運動強度|方案未揭露|未載分派|未載隨機|'
       r'題摘層資訊不足|資訊不足|需換算|劑量需換算|未報告客觀指標|未達契約 trained|'
       # uncertainty about the axis fact itself (not merely the send-to-fulltext disposition)
       r'無法確定|無法判定|無從確認|無從判定|無從分離|是否另有|是否可用|是否構成|'
       r'確認是否|是否符合|是否屬|可分離性|解讀受限|需視')

conv, keep_gap, keep_none = [], [], []
for c in unc:
    r = ent[c]['reason']
    ax = [k for k, p in RULED if re.search(p, r)]
    if not ax:
        keep_none.append(c)
    elif re.search(GAP, r):
        keep_gap.append((c, ax))
    else:
        conv.append((c, ax))

print('effectively-unclear total :', len(unc))
print('  A. no ruled axis cited  :', len(keep_none), '-> stays unclear')
print('  B. ruled axis + info gap:', len(keep_gap), '-> stays unclear (n+42 item 5, fail-closed)')
print('  C. ruled axis, NO gap   :', len(conv), '-> would convert to exclude')
print()
print('bucket C by axis:', Counter(a for _, ax in conv for a in ax))
print()
for c, ax in conv:
    print(c[-8:], ax)
    print('   ', ent[c]['reason'][:150].replace('\n', ' '))
