# -*- coding: utf-8 -*-
"""n+66（一）第①步：逐筆確認排除理由是否「只引契約未列舉」。

⚠️ **本檔為第①步之獨立產物，先落盤，再做第②步量測**
（n+64 二之建議：讓推理順序自帶時間戳，不靠檔頭宣稱）。
**本步不量測影響、不做任何寫入。**

判準（n+66 一）：
  「契約未列舉此項目」不是一個存在的排除理由。
  持續型耐力項目（游泳／越野滑雪／划船／鐵人三項等）一律在
  族群軸範圍內。
  ⚠️ 但 n+42（四）之間歇性團隊球類排除**不受影響**——其依據是
  「該族群不是耐力運動員」之實質判斷，不是「契約沒列到它」。

分類：
  A = 只引「未列舉」而無其他獨立出局軸  → 須更正
  B = 另有獨立出局軸（設計／介入／結果／時序／族群）→ 維持原判
  C = 其排除依據為 n+42（四）團隊球類實質判斷 → 不適用本裁定

⚠️ **樣式須寬**（第 335 輪教訓：太緊會回報一個乾淨的 0）。
故先以寬樣式撈出所有「未列」語句，再逐筆人工核對，
**不以樣式本身決定分類**。
"""
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']

# 寬樣式：任何形式的「契約未列（舉）…型態／項目」
WIDE = re.compile(r'契約未列[^，。；]{0,12}|未列[入舉]契約|非契約[^，。；]{0,6}列舉')

hits = []
for i, e in enumerate(E):
    r = e['reason']
    for m in WIDE.finditer(r):
        hits.append({
            'seq': i,
            'short': e['candidateId'][-8:],
            'opinion': e['opinion'],
            'phrase': m.group(0).replace('**', ''),
            'context': r[max(0, m.start() - 110):m.start() + 60].replace('**', ''),
        })
        break

print('寬樣式命中 %d 筆' % len(hits))
print()
for h in hits:
    print('--- %s  seq%-5d %s' % (h['short'], h['seq'], h['opinion']))
    print('    片語：%s' % h['phrase'])
    print('    脈絡：...%s...' % h['context'])
    print()

json.dump(hits, io.open('.scratch/n66_step1.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('已寫出 .scratch/n66_step1.json（%d 筆待人工核對）' % len(hits))
print()
print('⚠️ 本步僅產生候選清單，分類 A／B／C 須逐筆讀完整理由後判定，')
print('   不由樣式決定——樣式只負責「不漏」，不負責「判準」。')
