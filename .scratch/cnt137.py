import json, re, collections
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
ov=json.load(open(RUN+'/post-ruling-reclassification.json',encoding='utf-8'))
jent=j['entries']; items={it['candidateId']:it for it in w['items']}
ovids={e['candidateId'] for e in ov['entries']}
print('judged', len(jent), 'overlay', len(ovids))
# is 8cf98a4e (mixed-nutrient mentioned inline) in overlay?
for k in ['8cf98a4e','6244573a','101b349d']:
    hit=[c for c in ovids if k in c]
    print(k,'in overlay:', bool(hit))
def ct(pat):
    return sum(1 for e in jent if re.search(pat, e['reason']))
print('--- counters (regex over judged reasons) ---')
for name,pat in [('學位論文/博士論文','學位論文|博士論文'),('青少年','青少年'),('預印本','預印本'),
                 ('檢索雜訊','檢索雜訊'),('自選補給','自選補給'),('職業','職業體力|職業'),
                 ('漱口','漱口'),('running 詞族','`running` 詞族'),('cycle 詞族','`cycle` 詞族'),
                 ('carbohydrate 詞族','`carbohydrate` 詞族'),('去重','去重清單|第四型|第 4 型')]:
    print(f'  {name}: {ct(pat)}')
# last explicit numeric counters mentioned
for pat in [r'檢索雜訊累計第 (\d+) 筆', r'自選補給型.{0,6}第 (\d+) 筆', r'青少年排除累計第 (\d+) 筆',
            r'學位論文累計第 (\d+) 筆', r'預印本第 (\d+) 筆', r'漱口研究累計第 (\d+) 筆',
            r'`running` 詞族誤命中第 (\d+) 筆', r'`cycle` 詞族誤命中第 (\d+) 筆',
            r'`carbohydrate` 詞族誤命中第 (\d+) 筆']:
    vals=[int(m.group(1)) for e in jent for m in [re.search(pat,e['reason'])] if m]
    print(f'  MAX {pat} -> {max(vals) if vals else None}  (n={len(vals)})')
