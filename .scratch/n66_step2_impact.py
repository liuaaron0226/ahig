# -*- coding: utf-8 -*-
"""n+66（一）第②步：量測影響。

⚠️ **第①步之產物 `.scratch/n66_step1.json` 已先落盤**
（時間戳可稽核，n+64 二）。本步在其之後執行。

第①步之人工核對結論（逐筆讀完整理由後判定，不由樣式決定）：

| 記錄 | 分類 | 其獨立出局軸 |
|---|---|---|
| `8347c0c1` | **B** | 設計軸（橫斷面無對照臂）、介入軸（自選每日攝取、`[chronic-strategy]`）、結局軸（達標率與日內時序） |
| `e5a514cd` | **B** | 設計軸（觀察研究無隨機無對照）、介入軸（自選補給） |
| `b3913902` | **B** | **族群軸（久坐肥胖者，非受訓耐力運動員）**、時序與介入軸（10 週訓練、無運動中補給）、結局軸（體重體脂血脂） |
| `43f5d1ab` | **不適用** | 該片語出現在我自己第 334 輪的呈報文字中，是**引述兩種矛盾措辭**，不是本筆之排除理由；本筆判 unclear 且其型態軸明寫「不構成出局理由」 |

**🚨 符合 n+66（一）①之 A 類（只引「未列舉」而無其他獨立出局軸）：
0 筆。**

⚠️ **樣式充分性之驗證**（第 335 輪教訓：太緊會回報一個乾淨的 0）：
另以「持續型項目 ∩ 運動型態軸負面語句」之更寬條件複查，命中 19 筆，
逐一檢視其措辭後確認——**多出的 15 筆皆非本裁定所指**：
其中 2 筆為魚類游泳能力測驗（`26cfa27c`、`17c2e958`，族群軸為魚，
獨立出局）、其餘為現代五項／蓋爾式足球／CrossFit／Wingate 等
**非持續型項目**，或為「無運動介入方案」「型態軸不構成出局理由」
等**與本裁定方向相同或無關**之語句。
**🚨 即 0 這個數字經過了『它是不是假的』的檢驗，不是直接採信。**
"""
import io
import json
import subprocess

step1 = json.load(io.open('.scratch/n66_step1.json', encoding='utf-8'))

CLASS = {
    '8347c0c1': ('B', '設計軸＋介入軸＋結局軸皆獨立出局'),
    'e5a514cd': ('B', '設計軸＋介入軸皆獨立出局'),
    'b3913902': ('B', '族群軸（久坐肥胖者）＋時序介入軸＋結局軸皆獨立出局'),
    '43f5d1ab': ('不適用', '該片語為第 334 輪呈報中之引述，非本筆排除理由'),
}

print('=== n+66（一）第①步分類結果 ===')
for h in step1:
    k, why = CLASS[h['short']]
    print('  %-9s %-8s %-6s %s' % (h['short'], h['opinion'], k, why))

a_class = [s for s, (k, _) in CLASS.items() if k == 'A']
print()
print('🚨 A 類（須更正）：%d 筆' % len(a_class))
print()

if not a_class:
    print('=== 第②步：影響量測 ===')
    print('  A 類為 0 筆 → **無任何判讀需要更正**')
    print('  → 覆蓋層不新增條目、`judgements.json` 不變動')
    print('  → Δadvance = 0、Δunclear = 0、Δwindow = 0、ΔpScore = 0')
    print()
    print('⚠️ 依 n+62，影響為零時仍須實測而非推定。以下為實測輸出：')
    out = subprocess.run(['python', '-X', 'utf8', '.scratch/term.py'],
                         capture_output=True, text=True, encoding='utf-8')
    print(out.stdout.strip().splitlines()[-1])
    print()
    print('⚠️ 本輪未做任何寫入，故上列數值即為「更正前後皆同」之值。')
