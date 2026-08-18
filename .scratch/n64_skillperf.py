# -*- coding: utf-8 -*-
"""n+64（一）2：`[skill-performance]` 掛牌之 M1 契約審輸入清單。

⚠️ 本腳本存在的理由，是 n+64 更正的那個錯誤之根源：
協調者寫「已量測之兩筆皆為陰性或反向」時，那個「兩筆」與「皆為陰性」
都是憑印象的——**當時該構念已有 8 筆，且其中一筆為顯著改善**。
n+64 令 M1 一律寫「方向不一致」而非「皆為陰性」，並把本掛牌之
契約審優先序提高。**光靠裁定文字，幾十輪後仍會重蹈**——
故把它落成產物，且方向欄不得憑印象。

⚠️ 方向判定之作法與其限制（須與結論同時讀）：
  * 方向**只從判讀正文讀回**，比對明確片語（顯著較高／反而顯著低
    ／未改善……）。**這是 n+64（三）照准之自我約束的機械化版本。**
  * **讀不出方向者一律標 `未載`，不得推定為陰性**——
    🚨 **這正是本次錯誤的形狀：把「我沒看到」寫成「沒有」。**
  * ⚠️ **`未載` 有兩種截然不同的成因，本腳本區分不了**：
    （甲）該筆只有題名可判（`[title-only-judged]`），本就無結果資料；
    （乙）有摘要但我當初判讀時未記方向。
    **前者是資料的限制，後者是我的疏漏。** 兩者都輸出為 `未載`，
    **M1 撰寫時須逐筆回看，不可把 `未載` 當成同一件事。**
  * ⚠️ 本腳本**不判斷該筆是否真屬技能表現構念**——它只收集
    正文提及技能表現字樣者。**收得太寬好過收得太窄**：漏掉一筆
    陽性結果，正是 n+64 要防的事。

🚨 執行本腳本測出之最重要事實（比 n+64 所更正者更根本）：

  **該構念之素材數，歷來自報為 3 → 7 → 8 筆；本腳本測得 33 筆。**

  成因不是資料變多，是**本 lane 對同一構念用過兩套互不相通的計數**：
    （甲）早期輪次記為「**認知/技能**名單」，自報至第 13 筆；
    （乙）第 254 輪起改記為「**技能表現**構念」，**從 1 重新起算**。
  **兩套交集僅 5 筆。** n+63 的「兩筆」與 `e020d071` 自報的「8 筆」
  都只站在（乙）上，**整批漏掉（甲）**。

  ⚠️ **且（甲）本身把兩個構念合記**：已逐筆讀回確認
  `39b0c942`（反應時間、視覺搜尋、Go/Nogo）與 `ab38821f`
  （go/no-go、N-back、事件相關電位）**為純認知構念，非技能表現**。
  **故（甲）不能整批併入**——**M1 須逐筆分流，不可只把兩個數字相加。**

  🚨 **這正是 n+64 那句「這個決定沒有代價」該觸發查證的理由之延伸**：
  當時查的是方向對不對，**沒查數本身是怎麼數出來的**。
"""
import json
import io
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')

J = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
OV = json.load(io.open(R + '/post-ruling-reclassification.json',
                       encoding='utf-8'))['entries']
ov_by = {e['candidateId']: e for e in OV}

# 構念字樣。刻意寬鬆——寧可多收再逐筆看。
CONSTRUCT = re.compile(r'技能表現|技能構念|技能成功率|技能測驗|擊球|發球成功率|推桿|技能專項')

# 方向片語。每條都須是「結果方向」之陳述，不是設計描述。
DIRECTION = [
    ('改善', [r'顯著較高', r'顯著改善', r'成功率.{0,12}顯著較高',
              r'碳水顯著改善技能表現']),
    ('惡化', [r'反而顯著低', r'反而顯著較低', r'傾向較低']),
    ('無效', [r'未改善', r'無差異', r'未轉化為', r'僅自陳疲勞有差異']),
]


# ⚠️ 判方向前必須先剝除「引述他筆」之片段，否則會把別人的結果
# 讀成本筆的結果。第一版未剝除，`e020d071` 之理由中引了
# 「第 258 輪 `f3ae34f0`（足球剷球成功率反而顯著較低）」，
# 於是本筆被標成「惡化／改善」——**它自己只有改善**。
# 🚨 這與 n+54 未錨定 grep、n+59 乳鐵蛋白子字串同族：樣式比對
# 吃進了不屬於受測對象的文字。**且本例特別危險**：它會讓一筆
# 純陽性看起來方向混雜，正好稀釋掉 n+64 要保住的那個事實。
CITATION = re.compile(r'第 \d+ 輪[^；。]{0,80}')


def direction_of(reason):
    reason = CITATION.sub('', reason)
    hits = []
    for label, pats in DIRECTION:
        for p in pats:
            m = re.search(p, reason)
            if m:
                hits.append((label, m.group(0)))
                break
    if not hits:
        return '未載', ''
    labels = sorted(set(h[0] for h in hits))
    return '／'.join(labels), '；'.join(h[1] for h in hits)


rows = []
for e in J:
    if not CONSTRUCT.search(e['reason']):
        continue
    cid = e['candidateId']
    d, ev = direction_of(e['reason'])
    ov = ov_by.get(cid)
    rows.append({
        'short': cid[-8:],
        'opinion': e['opinion'],
        'effective': ov['effectiveDecision'] if ov else e['opinion'],
        'overlayRuling': ov['ruling'] if ov else '',
        'direction': d,
        'directionEvidence': ev,
        'titleOnly': ('title-only-judged' in e['reason']
                      or 'not-found-all-ids' in e['reason']
                      or '所有識別碼皆查無' in e['reason']
                      or '池中無任何識別碼' in e['reason']),
        'reasonLen': len(e['reason']),
    })

print('技能表現構念素材：%d 筆' % len(rows))
print()
print('%-9s %-8s %-8s %-9s %-6s %s'
      % ('id', 'opinion', 'effective', 'direction', 'title?', 'evidence'))
for r in rows:
    print('%-9s %-8s %-8s %-9s %-6s %s'
          % (r['short'], r['opinion'], r['effective'], r['direction'],
             'Y' if r['titleOnly'] else '', r['directionEvidence'][:40]))

print()
tally = {}
for r in rows:
    tally[r['direction']] = tally.get(r['direction'], 0) + 1
print('方向分布：%s' % tally)

measured = [r for r in rows if r['direction'] != '未載']
print('有方向記載者 %d 筆，方向種類 %d 種'
      % (len(measured), len(set(r['direction'] for r in measured))))

# n+64（一）1 之守門：M1 不得寫「皆為陰性」。
neg_only = all(r['direction'] in ('無效', '惡化') for r in measured)
print()
print('『皆為陰性或反向』是否成立：%s' % ('是' if neg_only else '**否**'))
if not neg_only:
    pos = [r['short'] for r in measured if '改善' in r['direction']]
    print('  → 呈改善方向者：%s' % ', '.join(pos))
    print('  → 故 M1 一律寫「方向不一致」，不得寫「皆為陰性」（n+64 一2）。')

unstated = [r for r in rows if r['direction'] == '未載']
print()
print('⚠️ `未載` %d 筆，其中僅題名可判者 %d 筆——**兩者成因不同，'
      'M1 撰寫時須逐筆回看，不可合併陳述。**'
      % (len(unstated), sum(1 for r in unstated if r['titleOnly'])))

# --- 兩套計數之對照（本腳本測出之主要事實）---
SELF = re.compile(r'認知/技能名單累計第 (\d+) 筆')
old = {e['candidateId'][-8:]: int(SELF.search(e['reason']).group(1))
       for e in J if SELF.search(e['reason'])}
new = {r['short'] for r in rows}
print()
print('=== 兩套計數對照（n+64 之數字所以偏低的原因）===')
print('（甲）早期「認知/技能名單」自報序號 %d 筆，最大第 %d 筆'
      % (len(old), max(old.values())))
print('（乙）第 254 輪起「技能表現構念」自報：3 → 7 → 8')
print('（丙）本腳本內容制測得：**%d 筆**' % len(rows))
print('    甲∩丙 %d、僅甲 %d、僅丙 %d'
      % (len(set(old) & new), len(set(old) - new), len(new - set(old))))
print('⚠️ 僅甲者已逐筆讀回：為**純認知構念**（反應時間／Go-Nogo／'
      'N-back），非技能表現——**故兩套不得逕行相加，M1 須逐筆分流。**')

json.dump(rows, io.open('.scratch/m1_skill_performance.json', 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('已寫出 .scratch/m1_skill_performance.json')
