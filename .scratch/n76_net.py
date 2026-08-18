# -*- coding: utf-8 -*-
"""n+76（三）工作包：`allowedInstruments` 擴充之**淨回收量**。

🚨 n+66（四）禁「只給總筆數」。154 是標題層命中之**毛數**；
擁有者要知道的是：**若擴充工具清單，實際能回收幾筆？**
——即那 154 筆中，有多少**另有獨立於工具軸之出局理由**。

⚠️ **本檔之判定依據為我寫的判讀理由**——**那正是第九型（以自己
產生的敘述作為資料）的形狀。** 為何此處仍屬正當：
  **問題本身就是「我當初以什麼理由排除它」**——對象即我的判讀，
  不是研究的性質。**🚨 但這使結果只反映我寫下的理由，不反映
  研究的全部事實**：若某筆我只寫了一個軸而它其實還有別的軸出局，
  本檔會低估淨回收量（即高估可回收數）。**此限制寫入輸出。**

分層：
  甲 **已 advance／unclear** ——本就在名單內，擴充與否不影響其去留
  乙 **exclude 且理由中僅工具／結局軸** ——**真正的淨回收候選**
  丙 **exclude 且另有獨立出局軸** ——擴充也回收不了
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
op = {e['candidateId']: e['opinion'] for e in E}
reason = {e['candidateId']: e['reason'] for e in E}

SPORTS = {'游泳': r'\bswim|swimmer',
          '鐵人三項': r'triathl',
          '划船': r'\brow(ing|er)',
          '越野滑雪': r'cross-country ski|xc ski'}

# 獨立於「工具／結局」之出局軸。每一條都是我判讀理由中實際用過的措辭。
# 🚨 第 365 輪修正：第一版樣式太窄，把 22 筆判成「僅工具軸」，
#    逐筆讀回後發現多數另有出局軸，只是措辭沒被抓到——
#    例：「介入對照軸不符」「無 CHO 劑量或型態對照」「安慰劑載體是 CHO」
#    「自選攝取」「漱口」「無摘要」。**樣式訂太窄會高估淨回收量。**
INDEP = [
    ('族群-年齡', r'年齡.{0,8}(?:低於|遠低於|超過|逾).{0,6}契約|'
                  r'兒童|青少年|學童|幼兒|年長者|停經後|低於 ?18'),
    ('族群-臨床', r'屬臨床族群|患者|病患|受贈者|術後'),
    ('族群-非受訓', r'非受訓耐力運動員|未載訓練狀態|無訓練措辭|'
                    r'未載訓練程度|未載.{0,6}客觀指標'),
    ('介入-非碳水', r'非外源性碳水|非外源碳水|非碳水給予|無營養給予|'
                    r'非研究者給予|安慰劑載體是 CHO|placebo-cho-vehicle|'
                    r'配對載體|漱口'),
    ('介入-無對照', r'介入對照軸不符|非契約 comparator|無 CHO 劑量|'
                    r'無受控介入|自選攝取|自選飲食|操弄自變項為'),
    ('時序', r'非運動中補給|運動前|運動後|恢復期|\[chronic-strategy\]|'
             r'每日攝取|多日補充|每日補充'),
    ('設計', r'無隨機分派|個案報告|個案研究|橫斷面|綜述|計畫書|'
             r'單臂|無對照臂|問卷調查|Patent|專利|觀察研究|觀察性|'
             r'無摘要|自陳'),
    ('結局-清單外', r'不在(?:契約)?六項結局|非契約清單|outcome-adjacent|'
                    r'無契約清單內結局|結局軸違反|結果軸：❌'),
    ('非人類', r'受試對象為(?:大鼠|小鼠|細胞|細菌|魚|馬|牛|豬|輪蟲|'
               r'酵母|微生物|水螅|鱘)|無人類受試者|非人類研究'),
]

print('n+76（三）：`allowedInstruments` 擴充之淨回收量')
print('=' * 66)
allhit = {}
for lab, pat in SPORTS.items():
    rx = re.compile(pat, re.I)
    for cid in ti:
        if rx.search(ti[cid]):
            allhit.setdefault(cid, []).append(lab)
print('標題層命中（去重後）：%d 筆' % len(allhit))
print('  各項目（可重複計，如鐵人三項含游泳）：%s'
      % dict(collections.Counter(s for v in allhit.values() for s in v)))
print()

tiers = {'甲 已 advance/unclear': [], '乙 淨回收候選': [], '丙 另有獨立出局軸': [],
         '丁 尚未判讀': []}
why = collections.Counter()
for cid, sports in allhit.items():
    o = op.get(cid)
    if o is None:
        tiers['丁 尚未判讀'].append(cid)
        continue
    if o in ('advance', 'unclear'):
        tiers['甲 已 advance/unclear'].append(cid)
        continue
    r = reason[cid]
    hits = [lab for lab, pat in INDEP if re.search(pat, r)]
    if hits:
        tiers['丙 另有獨立出局軸'].append(cid)
        for h in hits:
            why[h] += 1
    else:
        tiers['乙 淨回收候選'].append(cid)

for k, v in tiers.items():
    print('%-22s %4d 筆' % (k, len(v)))
print()
print('丙層之獨立出局軸分布（一筆可多軸）：')
for k, v in why.most_common():
    print('   %-14s %4d' % (k, v))
print()
print('🚨 **淨回收量 = 乙層 %d 筆**（另有丁層 %d 筆尚未判讀，'
      % (len(tiers['乙 淨回收候選']), len(tiers['丁 尚未判讀'])))
print('   其去留須待判畢後才知）。')
print()
print('⚠️ 本檔之限制（不得略去）：')
print('   1. 判定依據為**我寫的判讀理由**，非研究之全部事實；')
print('      若某筆我只寫了一個軸而實際另有他軸出局，')
print('      本檔會把它算進乙層 → **高估淨回收量**。')
print('   2. 乙層須逐筆讀回才能確認，本檔只做分層。')
print('   3. 標題層命中會漏掉標題未具名項目者（如「open-water」）。')
print()
print('乙層逐筆（供人工覆核）：')
for cid in tiers['乙 淨回收候選']:
    print('   %s %-10s %s' % (cid[-8:], '/'.join(allhit[cid]), ti[cid][:62]))
print()
print('=' * 66)
print('🚨 **第 365 輪逐筆讀回之結論：乙層 3 筆全部另有出局軸，'
      '淨回收量為 0**')
print('   c0e2a61a  甘油／去氨加壓素超水合，**完全無 CHO 臂**')
print('   21c353db  兩臂麥芽糊精 50 g 相同，唯一差異為蛋白；且運動前給予')
print('   77fd5cf5  無碳水給予操弄，為賽事前後之觀察量測')
print()
print('⚠️ 即：**擴充 `allowedInstruments` 不會回收任何一筆已判排除者。**')
print('   受影響的是**未來判讀**與**已在名單內的 22 筆之萃取層處置**，')
print('   不是回收既有排除。**🚨 這與「154 筆受影響」給人的印象相反，')
print('   正是 n+66（四）要求淨回收量的理由。**')
print()
print('⚠️ 惟丁層 20 筆尚未判讀，其中若有僅差工具軸者，淨回收量會 > 0；')
print('   **待逐頁推進至該些頁面後方能定案。**')
