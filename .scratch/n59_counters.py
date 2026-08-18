# -*- coding: utf-8 -*-
"""n+59 第四節套用到本執行室自己的產物：**判讀理由裡的累計編號。**

`n59_audit.py` 掃出的 mk_pNNN.py 命中多為判讀敘述本身（那是判讀內容，
不是計算結果）。但那些敘述裡**夾帶了手寫的累計編號**
（「檢索雜訊累計第 507 筆」「[methodological] 累計第 35 筆」…），
**那些數字是呈現為結果的字串，而且是我手打的。**

⚠️ 本檔第一版以「族群標記字樣」界定成員再重算序號，結果大量不符
——查證後發現**不符來自我的族群界定過窄**（早期用「第 45 項待裁之
活躍案例第 N 筆」，後期改為「第 45 項活躍案例第 N 筆」），
**不是編號本身錯。** 那個版本會產生一個看起來像結果的錯誤結論，
正是 n+59 第四節所戒。故改為只檢查編號序列自身之內在一致性：

  **同一族之編號，依判讀序列排列後，應嚴格遞增且不重複。**

這個性質不依賴我如何界定族群，只依賴我寫下的數字本身。
唯讀，不寫任何檔案。
"""
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

# 只抓「明寫編號」之樣式；族群界定完全由該樣式決定，不另猜測
NUMBERED = [
    ('檢索雜訊累計', re.compile(r'檢索雜訊累計第 (\d+) 筆')),
    # 🚨 第 335 輪測出：以下三式原本都太窄，於是本檢查對它們回報
    # 「非遞增 0」——**那是假的 PASS，不是真的沒問題**。
    #   `[methodological]`：後期理由改用反引號包住標籤
    #     （`` `[methodological]` 累計第 N 筆 ``），窄式漏掉 3 筆，
    #     而那 3 筆裡正好有一組重號（33 寫了兩次）。
    #   `第 45 項…活躍案例`：中綴詞不只「待裁之」一種，漏 1 筆。
    #   `診斷性葡萄糖負荷型`：量詞寫過「增至」也寫過「第」，
    #     漏 2 筆，而那 2 筆也是一組重號（60 寫了兩次）。
    # ⚠️ 教訓與 n+54 未錨定 grep 恰好相反：那次是樣式太鬆吃到別的，
    # **這次是樣式太緊看不到自己該看的**——**而檢查漏看的後果，
    # 是它會回報一個乾淨的 0。** 兩個方向都要防。
    ('[methodological] 累計',
     re.compile(r'\[methodological\][`｀]? 累計第 (\d+) 筆')),
    ('第 45 項活躍案例',
     re.compile(r'第 45 項[^第]{0,8}活躍案例第 (\d+) 筆')),
    ('自選補給型累計', re.compile(r'自選補給型累計第 (\d+) 筆')),
    ('診斷性葡萄糖負荷型',
     re.compile(r'診斷性葡萄糖負荷型(?:增至|第) (\d+) 筆')),
    ('冰球語料', re.compile(r'冰球語料第 (\d+) 筆')),
    ('游泳選手語料', re.compile(r'游泳選手語料第 (\d+) 筆')),
    ('禁藥檢測語料', re.compile(r'禁藥檢測語料第 (\d+) 筆')),
    # ⚠️ 須排除「乳鐵蛋白語料」——其字串含「鐵蛋白語料」為子字串。
    # 第一版未排除，把乳鐵蛋白第 4 筆讀成鐵蛋白第 4 筆，產生一個
    # 假的「非遞增」告警。這與 n+54 未錨定 grep 同型：樣式比對太鬆。
    ('鐵蛋白語料', re.compile(r'(?<!乳)鐵蛋白語料第 (\d+) 筆')),
    ('乳鐵蛋白語料', re.compile(r'乳鐵蛋白語料第 (\d+) 筆')),
]

E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
print('序列長度 %d' % len(E))
print()

bad_total = 0
for name, pat in NUMBERED:
    seen = []
    for i, e in enumerate(E):
        m = pat.search(e.get('reason', '') or '')
        if m:
            seen.append((i, e['candidateId'][-8:], int(m.group(1))))
    if not seen:
        print('=== %s ===  （無明寫編號者）' % name)
        continue
    faults = []
    for k in range(1, len(seen)):
        prev, cur = seen[k - 1][2], seen[k][2]
        if cur <= prev:
            faults.append((seen[k][1], prev, cur))
    bad_total += len(faults)
    print('=== %s ===' % name)
    print('  明寫編號 %d 筆，範圍 %d–%d'
          % (len(seen), seen[0][2], seen[-1][2]))
    if faults:
        print('  ⚠️ 非遞增 %d 處：' % len(faults))
        for cid, prev, cur in faults[:10]:
            print('     %s：前一筆寫 %d，本筆寫 %d' % (cid, prev, cur))
    else:
        print('  ✅ 依判讀序列嚴格遞增，無重複、無倒退')
    print()

print('=' * 60)
print('全族非遞增處合計：%d' % bad_total)
print('⚠️ 本檢查只證明編號序列自身一致，不證明「族群成員無遺漏」')
print('   ——某筆屬該族但未寫編號者，本檢查看不到。')
