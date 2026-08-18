# -*- coding: utf-8 -*-
"""n+65（三）之回看結果：27 筆技能表現素材之結果方向。

⚠️ **這不是重新判讀**（n+56 一：不重判）。所有 `opinion` 與
`effectiveDecision` 一律不動；本檔只補記「該筆的技能表現結果
朝哪個方向」，那是判讀當時未寫進理由的資訊。

⚠️ **方向一律取自摘要之明文結論，逐筆人工判讀後在此以常數登錄**，
並附上摘要中據以判定的片語，**使每一格都可回頭核對**。
**這是 n+65（一）1「檢查對象是即將入庫的內容」在資料上的類比：
結論要能指回它所依據的那句話。**

🚨 產出本檔的過程中我犯了一個與本裁定同型的錯，一併記在此：
  `n65_dump_skill.py` 第一版只查 `abstractText` 欄位，而 worksheet
  的欄位名是 `abstract`，於是回報「27 筆中 25 筆實際無摘要」。
  **那是假的**——判讀理由裡帶著 p 值與具體數字，摘要不可能真的空。
  修正後：**26 筆有摘要，真正無摘要者僅 `a3ef723f` 1 筆。**
  **🚨 即我在執行「不要把『我沒看到』寫成『沒有』」這道裁定的
  當下，又犯了一次同樣的錯。猜欄位名比猜資料更危險，因為它
  安靜地回報一個看似合理的數字。**
"""
import json
import io

# short -> (方向, 摘要中據以判定之片語)
# 方向詞彙：改善／部分改善／無效／惡化／未載
D = {
    # --- 明確改善 ---
    '5eab2af7': ('部分改善', 'CHO attenuated the decline in shot speed and SPS index；'
                 'passing 與 dribbling 未受影響'),
    '5b60a887': ('部分改善', 'dribbling time 於 dextrose 臂顯著變慢而 HMS 臂未變慢；'
                 'passing penalty time 4.27 vs 7.73 s, p=.004'),
    'b28bbf87': ('改善', 'significant improvement for dribbling, agility, and shooting (p<.05)'),
    'fe2fd7f0': ('部分改善', 'passing accuracy 雙足皆較佳（9%、13%）、非慣用腳 passing speed '
                 'p=.032；dribbling 與 sprint 未變'),
    'd4c75375': ('改善', 'CHO attenuated the increase in error rate 與 VP/VPE 指數下降；'
                 '「CHO supplementation improves stroke quality」'),
    '64b3a272': ('改善', 'tackling technique 之 supplement effect 相容 (P<0.05, η2=.189-.612)；'
                 '「effective strategy for retaining tackling technique」'),
    '9b797ca9': ('改善', 'combined shooting percentage 60±8% (CES) vs 53±11% (P EUH), p=0.003'),
    'fddfca9e': ('部分改善', 'dribbling precision +29±20%, p<0.01；sprint 與 jump 未改善'),
    # ⚠️ 本筆之飲品為碳水＋咖啡因共線，**無單獨碳水臂**，故其改善
    # 不可歸因於碳水。單列一類，不併入「改善」計數。
    '9f6a78ff': ('改善(共線)', 'Putting performance over 5 m and 2 m ... showed a main '
                 'effect for drink (p < 0.05)——惟介入為 6.4 g/100 mL 碳水＋16 mg/100 mL '
                 '咖啡因之共線飲品，無單獨碳水臂'),
    '8b7f72b9': ('改善', 'MS-Test performance improved during the latter stages (P<0.05)'),
    'cc96545a': ('改善', 'More failures occurred during placebo than CHO；'
                 'NORM CHO trial had the fewest failures'),
    # --- 傾向改善但未達顯著 ---
    'af032e02': ('傾向改善', 'CHO 臂技能下降 3% vs 安慰劑 14%，P = 0.07（未達 .05）；'
                 '「showed a tendency to better maintain」'),
    'cc1d1cd9': ('傾向改善', 'long serve accuracy 之惡化，CHO 有預防傾向 P = 0.077；'
                 'short serve 無效果 P = 0.109'),
    '6d4e12d8': ('無效', 'golf performance 五項測驗未載改善；'
                 '顯著者為 PLF 疲勞感下降與 PLC 專注度上升（自覺指標，非技能）'),
    # --- 明確無效 ---
    'a85d1d11': ('無效', 'There were no differences between trials in any of the variables'),
    '1be9b1c7': ('無效', 'Neither supplement affected number of won games'),
    '721a8a69': ('無效', 'Perception ratings and hitting accuracy (BMT) were not affected '
                 'by treatment；「no ergogenic effect on tennis performance」'),
    'e7a8c6fe': ('無效', 'Carbohydrates did not attenuate reductions in physical or '
                 'technical performances (all P > 0.05)'),
    '12bd35a4': ('無效', 'no difference in number of bouts won or lost, or points '
                 'for and against'),
    '3b57d376': ('無效', 'no significant differences among the groups in the FT '
                 '(free throw) and SLDS (dribbling) tests (p > .05)'),
    'e2a387e8': ('無效', 'Bicarbonate did not alter PFT/MT/DMT/PT（惟本筆介入為'
                 '碳酸氫鈉，碳水僅為安慰劑載體）'),
    '1dae29c1': ('無效', 'no significant differences in passing skill（改善者為 sprint '
                 '與 CMJ，且介入為 CHO＋咖啡因 vs CHO）'),
    'cba3e305': ('無效', 'motor skills test 之改善出現在 CHO＋咖啡因臂 vs CHO 臂'
                 '——即碳水單獨未改善技能'),
    'f493504b': ('無效', 'CHO 改善之項目為 speed of information processing（認知），'
                 'shooting performance 未載改善'),
    # --- 明確惡化 ---
    '913d78e7': ('惡化', 'Preexercise carbohydrate 導致 marked hypoglycemia 且'
                 'impaired layup shooting performance 8.5/11 vs 10.3/11, p<.01'),
    # --- 綜述，無自身資料 ---
    '79c8b85c': ('未載', '敘述性回顧，無自身資料；明載該領域「conflicting in its findings」'),
    # --- 真正無摘要 ---
    'a3ef723f': ('未載', '池中無摘要（squash 學位論文型），無從判定'),
    # --- `[title-only-judged]`：本就只有題名，非疏漏 ---
    # ⚠️ 這兩筆是斷言攔下來的：我第一版漏列，因為 `n65_dump_skill.py`
    # 只傾印非 titleOnly 者。**漏列而斷言未攔，就會變成一個
    # 「27 筆全數處理完畢」的假結論。**
    '38305941': ('未載', '`[title-only-judged]`：碳水漱口擊劍論文，上游無摘要'),
    '518513f1': ('未載', '`[title-only-judged]`：網球擊球論文，池中無識別碼'),
}

rows = json.load(io.open('.scratch/m1_skill_performance.json', encoding='utf-8'))
by = {r['short']: r for r in rows}

# 併回：既有 4 筆已在判讀理由中記過方向者
PRIOR = {'e020d071': '改善', 'f3ae34f0': '惡化', 'ad98a40f': '無效',
         'd6469f54': '無效'}

merged = {}
for r in rows:
    s = r['short']
    if s in D:
        merged[s] = (D[s][0], 'n+65 回看摘要', D[s][1])
    elif s in PRIOR:
        merged[s] = (PRIOR[s], '判讀當時已記', r['directionEvidence'])
    else:
        merged[s] = ('未載', '', '')

assert len(merged) == len(rows), (len(merged), len(rows))
unresolved = [s for s, v in merged.items() if v[0] == '未載' and not v[1]]
assert not unresolved, ('仍有未處理者', unresolved)

print('技能表現素材 %d 筆，全數有方向登錄或明載無從判定' % len(merged))
print()
tally = {}
for s, (d, src, ev) in sorted(merged.items()):
    tally[d] = tally.get(d, 0) + 1
    print('%-9s %-6s %-12s %s' % (s, d, src, ev[:64]))

print()
print('=== 方向分布（n+65 三所令之回看完成後）===')
for k in ['改善', '部分改善', '傾向改善', '改善(共線)', '無效', '惡化', '未載']:
    if k in tally:
        print('  %-5s %2d' % (k, tally[k]))
print('  合計   %2d' % sum(tally.values()))

pos = tally.get('改善', 0) + tally.get('部分改善', 0)
# ⚠️ 共線者不計入 pos——其改善不可歸因於碳水。
print()
print('🚨 呈改善或部分改善者 %d 筆（非 n+63 所述之「零筆」，'
      '亦非 n+64 所述之「1 筆」）' % pos)
print('⚠️ 另有傾向改善 %d 筆（p 值介於 .05 與 .10）'
      % tally.get('傾向改善', 0))
print('⚠️ 惡化 %d 筆；無效 %d 筆；仍無從判定 %d 筆'
      % (tally.get('惡化', 0), tally.get('無效', 0), tally.get('未載', 0)))

out = [{'short': s, 'direction': d, 'source': src, 'evidence': ev}
       for s, (d, src, ev) in sorted(merged.items())]
json.dump(out, io.open('.scratch/m1_skill_direction.json', 'w',
                       encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('已寫出 .scratch/m1_skill_direction.json')
