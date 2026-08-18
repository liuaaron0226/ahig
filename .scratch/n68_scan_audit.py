# -*- coding: utf-8 -*-
"""🚨 第 348 輪發現：夾雜外文掃描**從未掃過累積之 judgements.json**。

成因：`scan.py` 假設輸入為 list-of-entry，而累積檔是 `{"entries": [...]}`，
餵它會 `TypeError`。歷來只在**每頁 append 前**掃該頁的暫存 list，
**尾端抽驗之 dict 形狀更是連跑都沒跑過。**

🚨 這是第 8 型（誤讀檢查之涵蓋範圍）的又一例：
**掃描每次都通過，是因為它每次只看新的一頁；我沒問過它「掃過全部沒有」。**

本檔把旗標分成兩類並各自計數：
  （甲）**已立慣用語**——`裁定A型` 中的孤立 `A`，主篩已寫 126 筆，
        屬白名單缺口而非缺陷，**不需更正、亦不得計為錯誤**；
  （乙）**真的夾雜外文**——已寫入之判讀理由中的漏譯詞。
        ⚠️ `judgements.json` 為 append-only，**不重寫**；本檔即其登記簿。

本檔看不到：漏譯詞是否影響判讀結論（我認為不影響，理由見輸出末），
以及白名單本身是否還缺其他慣用語。
"""
import io
import json
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')
OK = {'g', 'kg', 'ph', 'vs', 'mg', 'ml', 'mj', 'bmi', 'dxa', 'rm', 'kj',
      'vo', 'iga', 'wgan', 'gp', 'xgboost', 'svr', 'mlp', 'geneactiv',
      'asprosin', 'masld', 'comp', 'nefa', 'dnl', 'ebct', 'cacs', 'chd',
      'vdr', 'er', 'colia', 'paq', 'fitnessgram', 'whr', 'ldl', 'hdl',
      'tc', 'fbg', 'npa', 'ssb', 'who', 'ers', 'nhis', 'nsc', 'ct', 'ci',
      'sd', 'se', 'n'}
PAT = re.compile(r'[Ѐ-ӿ가-힯぀-ヿ]+'
                 r'|[A-Za-z]+(?=[一-鿿])'
                 r'|(?<=[一-鿿])[A-Za-z]{3,}')
# ⚠️ 慣用語清單為**逐筆讀回後實測所得**，不是猜的：
#   • `裁定A` 之四種後接（型／範圍／相關／之）——協調者所立之判準代號；
#   • `GI` ——契約 `gi-symptom-incidence` 之通用縮寫；
#   • `輔酶A` ——中文化學名（coenzyme A），A 為名稱的一部分。
# 🚨 我第一版只列「裁定A型」一種，於是把 9 筆慣用語誤計為缺陷——
#    **模式訂太緊會製造假缺陷，訂太鬆會漏掉真缺陷（n+68 第七型）。**
IDIOM = re.compile(r'裁定A(?=型|範圍|相關|之)'
                   r'|輔酶A'
                   r'|(?<=[一-鿿])GI|GI(?=[一-鿿])')

E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
idiom_only, real = [], []
for e in E:
    reason = e['reason']
    hits = [x for x in PAT.findall(reason) if x.lower() not in OK]
    if not hits:
        continue
    stripped = IDIOM.sub('〓', reason)
    rest = [x for x in PAT.findall(stripped) if x.lower() not in OK]
    (real if rest else idiom_only).append(
        (e['candidateId'][-8:], e['opinion'], rest or hits))

print('累積 judgements.json 共 %d 筆' % len(E))
print('（甲）僅慣用語命中（裁定A＊、GI、輔酶A）：%d 筆'
      '——白名單缺口，不計為缺陷' % len(idiom_only))
print('（乙）真的夾雜外文：%d 筆' % len(real))
print()
for s, op, hits in real:
    print('  %s %-8s %s' % (s, op, hits[:5]))
print()
print('🚨 已寫入者不重寫（append-only），本檔為登記簿。')
print('⚠️ 我判斷這 %d 筆不影響判讀結論：漏譯處皆為敘述性名詞'
      % len(real))
print('   （food／older／participants／prevalence／физical 等），')
print('   四軸之出局理由本身仍以中文寫明——**但這是我的判讀，請協調者覆核。**')
