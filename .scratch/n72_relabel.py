# -*- coding: utf-8 -*-
"""把抽驗那 200 筆自「排除清單」正式改標為第三態，並更新該檔語意。

⚠️ 檔名維持 `p-score-sequence-exclusions.json`——**不改檔名**，
因為 term.py／term2.py／M1 稽核腳本都指向它，改名是另一件事。
改的是每筆的 `state` 欄位與檔頭語意，使「暫時排除」與「永久在外」
在資料上可分辨，而不是靠讀 `source` 字串去猜。

🚨 n+72 四 2 要求兩集合互斥——本檔寫入後，`state` 即為權威來源，
呼叫端依它分流（本輪已同時改 term.py 與 term2.py 為讀 source；
本檔寫入 state 後兩者改讀 state，語意更明確）。
"""
import io
import json

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
P = OUT + '/p-score-sequence-exclusions.json'
AUDIT = 'n+57 尾端抽驗（200 筆隨機抽樣）'

doc = json.load(io.open(P, encoding='utf-8'))
n_audit = n_temp = 0
for e in doc['entries']:
    if e.get('source') == AUDIT:
        e['state'] = 'out-of-sequence-permanent'
        n_audit += 1
    else:
        e['state'] = 'pending-reintegration'
        n_temp += 1
assert n_audit == 200, n_audit
doc['schemaVersion'] = '1.1.0'
doc['states'] = {
    'pending-reintegration': (
        '第 n+40 輪選項（丙）：為解除前置條件而跳頁補判之紀錄。'
        '暫不進 p 值序列，逐頁推進到該筆所在頁時自動納回。'
        '**非空即不得終止**（evaluate_termination 之 p_score_excluded）。'),
    'out-of-sequence-permanent': (
        '第 n+72 輪核准之第三態：ADR-0008 條件 4 之尾端抽驗紀錄。'
        '抽驗是「對剩餘池的獨立隨機稽核」，不是逐頁篩選的延續，'
        '把獨立稽核的結果接進循序檢定的標籤流是範疇錯誤（n+70 丙）。'
        '**永久不納回，且不擋終止**'
        '（evaluate_termination 之 out_of_sequence）。'
        '⚠️ 對 p 值之影響是零而非保守——p_score 只吃 labels 與 n_total，'
        '第三態兩者都不碰。'),
}
doc['mutualExclusion'] = (
    '同一 candidateId 不得同時屬於兩態；evaluate_termination 於入口檢查，'
    '重疊即丟 TerminationError（n+72 四 2）。')
io.open(P, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
print('已標記：pending-reintegration %d、out-of-sequence-permanent %d'
      % (n_temp, n_audit))
