# -*- coding: utf-8 -*-
"""疑似重疊樣本／作者之登記簿——**由資料掃出，不靠我臨場察覺**。

🚨 第 353–354 輪連續三輪遇到「同國／同聯賽／同語言之多筆記錄數字高度
一致」。我上上輪把立陶宛前兩筆寫成「跨樣本重現」，**看到第三筆才警覺**
——即我的察覺方式是碰巧的，不是系統性的。

本檔改為**由判讀理由掃出候選群**，讓下一次不必靠運氣。

⚠️ 本檔看得到：判讀理由中同時提及同一國別／聯賽／語言之記錄，
且理由中含數字者。
⚠️ 本檔看不到：**作者、機構與樣本本身**——那些欄位 worksheet 沒有。
🚨 **故本檔產出的是「值得查」的清單，不是「確定重疊」的清單**；
真正的判定只能在全文期做。**不得把本檔輸出當成重疊之證據。**
"""
import io
import json
import re
import collections

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
ti = {it['candidateId']: (it.get('title') or '') for it in w['items']}
yr = {it['candidateId']: it.get('publicationYear') for it in w['items']}
by_short = {e['candidateId'][-8:]: e for e in E}

# 掃描維度：國別／聯賽／語言之具名詞。每一項都是我在判讀理由裡實際寫過的。
DIMS = {
    '立陶宛': r'立陶宛',
    '英超': r'英超|英格蘭超級聯賽|English Premier',
    '斯洛維尼亞文': r'斯洛維尼亞',
    '葡萄牙文': r'葡萄牙文',
    '紐西蘭黑醋栗': r'紐西蘭黑醋栗',
    'NCAA': r'NCAA',
    '波蘭': r'波蘭',
    '土耳其': r'土耳其',
    '克拉科夫': r'克拉科夫',
    'Project EAT': r'Project EAT',
}
print('涵蓋自報：主篩 %d 筆判讀理由' % len(E))
print('⚠️ 掃描維度為我判讀理由中實際寫過的具名詞 %d 個——'
      '**未寫進理由的重疊掃不到**。' % len(DIMS))
print()

# 🚨 第 355 輪：本檔第一版直接對整段理由比對，於是**跨輪引述被算成命中**
#    ——斯洛維尼亞學位論文被歸進「英超」族，只因我在它的理由裡引了英超那筆。
#    **這正是本 lane 已登記之第 4 型缺陷（跨輪引述被吞掉），我自己又犯一次。**
#    故先剝除引述段落再比對；並印出剝除前後之差額，讓誤差可見。
CITATION = re.compile(r'第 \d+ 輪[^；。]{0,120}')

rows = []
for lab, pat in DIMS.items():
    raw = [e for e in E if re.search(pat, e['reason'])]
    hits = [e for e in raw
            if re.search(pat, CITATION.sub('', e['reason']))]
    if len(raw) != len(hits):
        print('⚠️ %s：原始命中 %d，剝除跨輪引述後 %d'
              '（差 %d 筆為引述所致之假命中）'
              % (lab, len(raw), len(hits), len(raw) - len(hits)))
    if len(hits) < 2:
        continue
    rows.append((lab, hits))
print()

for lab, hits in sorted(rows, key=lambda x: -len(x[1])):
    print('== %s：%d 筆 ==' % (lab, len(hits)))
    for e in hits:
        cid = e['candidateId']
        # 抽出理由中的 g/kg 或百分比數字，供人工比對
        nums = re.findall(r'\d+(?:\.\d+)?\s*(?:g/kg|%|g/h)', e['reason'])
        print('   %s %-8s %s  %s'
              % (cid[-8:], e['opinion'], yr.get(cid), ti[cid][:64]))
        if nums:
            print('        數字：%s' % ', '.join(dict.fromkeys(nums))[:110])
    print()

print('🚨 本檔輸出為「值得於全文期查證」之清單，**不是重疊之證據**。')
print('⚠️ 真正的判定需要作者、機構與樣本描述——worksheet 沒有這些欄位。')
