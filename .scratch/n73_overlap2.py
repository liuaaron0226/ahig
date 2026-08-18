# -*- coding: utf-8 -*-
"""疑似重疊樣本之候選掃描 v2——**改以標題（資料）為準，不用判讀理由（我寫的）**。

🚨 v1 的錯誤鏈值得完整記下，因為它連錯兩層：
  （一）第一版直接比對整段判讀理由 → **跨輪引述被算成命中**
        （斯洛維尼亞論文被歸進「英超」族，只因我在它的理由裡引了英超那筆）。
        **這是本 lane 已登記之第 4 型缺陷，我自己又犯一次。**
  （二）剝除引述後**仍有假命中**：立陶宛族混進法國、英超與英軍樣本，
        因為那些是我在同一段理由裡「併記」時提到立陶宛，**不是引述格式**，
        剝不掉。
  🚨 兩次都是同一個根因：**我拿「我寫的文字」當「資料」用。**
     判讀理由是敘事，裡面本來就會提到別的研究；
     **要問「這篇研究本身屬於哪個樣本」，該看的是標題與年份。**

本檔看得到：標題中具名之國別／聯賽／機構，加上年份與劑量數字。
本檔看不到：作者、機構、樣本描述——worksheet 無此欄位。
🚨 **輸出是「值得於全文期查證」之清單，不是重疊之證據。**
⚠️ 語言型群組（如斯洛維尼亞文學位論文）標題不含國名，
   **本檔掃不到**——那類仍需人工標記，已於下方另列。
"""
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
info = {it['candidateId']: (it.get('title') or '', it.get('publicationYear'))
        for it in w['items']}
op = {e['candidateId']: e['opinion'] for e in E}
reason = {e['candidateId']: e['reason'] for e in E}

# 標題層之具名詞。每一個都是原文標題會出現的字串，不是我的中文敘述。
DIMS = {
    'Lithuanian': r'\bLithuanian?\b',
    'English Premier League': r'English Premier League',
    'NCAA': r'\bNCAA\b',
    'New Zealand blackcurrant': r'New Zealand [Bb]lack ?currant',
    'Polish': r'\bPolish\b|\bPoland\b',
    'Turkish': r'\bTurkish\b',
    'Project EAT': r'Project EAT|EAT-I{1,3}V?\b',
    'Australian Football': r'Australian [Ff]ootball',
}
print('涵蓋自報：已判 %d 筆，掃描其**標題**' % len(E))
print()

DOSE = re.compile(r'\d+(?:\.\d+)?\s*(?:g/kg|g/h)')
for lab, pat in DIMS.items():
    hits = [cid for cid in op if re.search(pat, info[cid][0])]
    if len(hits) < 2:
        continue
    hits.sort(key=lambda c: (info[c][1] or 0))
    print('== %s：%d 筆 ==' % (lab, len(hits)))
    for cid in hits:
        t, y = info[cid]
        nums = list(dict.fromkeys(DOSE.findall(reason[cid])))
        print('   %s %-8s %s  %s' % (cid[-8:], op[cid], y, t[:66]))
        if nums:
            print('        劑量數字：%s' % ', '.join(nums))
    print()

print('== 語言型群組（標題不含國名，本檔掃不到，人工登記）==')
for lab, ids in [('斯洛維尼亞文學位論文', ['26d9c8ed', '25a4bf7b']),
                 ('葡萄牙文學位論文', ['88dbe2ed', '776e2dc6'])]:
    print('   %s：' % lab)
    for s in ids:
        cid = next((c for c in op if c.endswith(s)), None)
        if not cid:
            print('      %s **查無**' % s)
            continue
        t, y = info[cid]
        print('      %s %-8s %s  %s' % (s, op[cid], y, t[:60]))
print()
print('🚨 本清單為「值得查」，不是「已確定重疊」。')
print('⚠️ 真正判定需要作者、機構與樣本描述，只能於全文期做。')
