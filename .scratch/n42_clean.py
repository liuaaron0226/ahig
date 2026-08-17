import json, os, re
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
ent = {e['candidateId']: e for e in d['entries']}
op = {k: v['opinion'] for k, v in ent.items()}
rc = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc):
    for e in json.load(open(rc, encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']
unc = [e['candidateId'] for e in d['entries'] if op[e['candidateId']] == 'unclear']

# Strictest reading: the reason must state a PASSING population phrasing (so item 5
# fail-closed does not apply) AND cite a now-ruled axis as the blocker.
POP_OK = r'措辭通過|為裁定 62 通過措辭|為通過措辭|`trained`|`elite`|`well-trained`|endurance trained|trained men|trained cyclists|well-trained'
GAP = (r'裁定 62 判|無訓練狀態措辭|無訓練措辭|無訓練程度措辭|無訓練程度形容詞|不自行擴張|'
       r'措辭含糊|未報告客觀指標|未達契約 trained|recreational|moderately trained|'
       r'未揭露|摘要截斷|continues|無摘要|題摘層資訊不足|'
       r'劑量未載|未載劑量|未載飲用量|未載體重|未載濃度|不換算|需換算|'
       r'未載給予時點|未載攝取時點|未載明時序|未載分派|未載隨機|方案未揭露|'
       r'無法確定|無法判定|無從確認|無從判定|無從分離|是否另有|是否可用|是否構成|'
       r'確認是否|是否符合|是否屬|可分離性')
RULED = [('R1', r'免疫|IgA|細胞激素|嗜中性球|淋巴球|自然殺手'),
         ('R2', r'同劑量|皆攝取相同|無安慰劑|無 CHO 劑量|對照臂為|等熱量|兩臂皆|不給液體'),
         ('R3', r'非契約清單|非契約 inScopeOutcomes|不在六項|非契約六項'),
         ('R4', r'足球|橄欖球|曲棍球|籃球|球類專項|間歇性場地|games player'),
         ('R7', r'靜脈|漱口|輸注|胃內灌注'),
         ('R8', r'青少年|adolescent')]
out = []
for c in unc:
    r = ent[c]['reason']
    if re.search(GAP, r):
        continue
    if not re.search(POP_OK, r):
        continue
    ax = [k for k, p in RULED if re.search(p, r)]
    if ax:
        out.append((c, ax, r))
print('CLEAN-CUT: population phrasing passes, no other info gap, blocker is a now-ruled axis')
print('count =', len(out))
print()
for c, ax, r in out:
    print(c[-8:], ax)
    print('   ', r[:190].replace('\n', ' '))
    print()
