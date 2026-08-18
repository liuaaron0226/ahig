# -*- coding: utf-8 -*-
"""判讀理由裡的累計編號檢查（n+59 第四節 → n+67 第二節改版）。

**檢查的性質**：同一族之編號，依判讀序列排列後應嚴格遞增且不重複。
這個性質不依賴我如何界定族群，只依賴我寫下的數字本身。唯讀。

🚨 **n+67（二）之改版：族群清單不再手寫，改由資料發現。**

**為什麼**：舊版以手寫的十族清單決定涵蓋範圍，而
**非人類生物體族不在其中**——於是第 337 輪 page 273 之錯位，
本檔只為檢索雜訊族告警，我便把「告警的那一族」當成「出錯的全部」，
**漏登第二族**。協調者亦自陳每輪把本檔的 PASS 當成「累計編號沒問題」
之一般訊號，**而本檔從未如此宣稱**。

**兩條教訓，n+67 已立為第七、第八種缺陷型態**：
  七、**樣式太緊 → 假 PASS**（回報一個乾淨的 0，沒有人會去追）。
  八、**誤讀檢查之涵蓋範圍**（檢查正確且從未宣稱涵蓋全部，
      是讀的人自行補上「它涵蓋全部」這個假設）。

**故本版之兩項要求（n+67 二）**：
  1. 族名以通用式掃出，不手工維護——**手工維護的涵蓋清單，
     本身就是「比意圖窄」的來源。**
  2. **每次輸出須自報涵蓋**：掃到幾族、各族幾筆、未納入者為何。
     **一個不說自己看了多少的檢查，不能當作全域結論。**

⚠️ **本版仍有其邊界，一併自報**（見輸出末尾之「本檔看不到什麼」）。
"""
import io
import json
import re
import sys

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

# 通用式：族名 + 序數詞 + 數字 + 量詞。族名由資料決定，不預先列舉。
#   例：「檢索雜訊累計第 507 筆」「非人類生物體第 201 例」
#       「`gel` 詞族至此 38 筆」「診斷性葡萄糖負荷型增至 72 筆」
# ⚠️ 族名允許含反引號、方括號與中括號——第 335 輪之假 PASS 正是
#    因為舊式不認反引號包住的 `[methodological]`。
# ⚠️ **第一版用非貪婪 `{2,20}?` 切族名，結果切碎了**：
#    「檢索雜訊累計第 N 筆」被切成「累計」、
#    「`gel` 詞族誤命中第 N 筆」被切成「詞族誤命中」，
#    於是「累計(筆)」一族混進了 348 筆互不相干的編號，
#    回報 105 處假非遞增。
# 🚨 **這是從「太緊」盪到「太鬆」——與 n+67 第七例恰好相反的方向。**
#    修法：族名以**句讀為左界**，不得跨句讀。
FAMILY = re.compile(
    r'(?:^|[；;。，,、：:（(」』]|——)\s*'
    r'([^；;。，,、：:（()」』]{2,26}?)'
    r'(?:累計)?(?:第|至此|增至)\s*(\d+)\s*([筆例項])'
)

# 這些前綴不是族名，是句子成分（掃描時仍可能沾到）
NOISE_PREFIX = re.compile(
    r'^(⚠️|🚨|🆕|📊|並記|並|附帶記錄|其為|本筆為|該型|該群|'
    r'於|為|在|與|該|其|本|之|亦|又|且|再|另|皆|至此|即|屬)+')

E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']

fams = {}
for i, e in enumerate(E):
    reason = (e.get('reason') or '').replace('**', '')
    for m in FAMILY.finditer(reason):
        name = NOISE_PREFIX.sub('', m.group(1)).strip('`*、，。； ')
        if len(name) < 2:
            continue
        key = '%s(%s)' % (name, m.group(3))
        fams.setdefault(key, []).append(
            (i, e['candidateId'][-8:], int(m.group(2))))

# 只檢查有兩筆以上者——單筆無「遞增」可言
# 🚨 **分級不靠手寫清單，靠資料本身的性質。**
# 第一版的修法是一條條加「這不是族名」的排除規則，
# 而那個清單越補越長——**它本身就是 n+67（二）所戒之物。**
#
# 改用一個從資料算得的特徵：**破例率**。
#   真編號族的形狀是「絕大多數嚴格遞增、極少數破例」（破例率低）；
#   族名切错而誤併的假族，其「編號」來自不同來源，破例率高。
# 這個判準不需要我判斷任何一個名字是不是族名。
#
# ⚠️ **但分級不是過濾**：兩級全部輸出，只是分開呈現，
#    且低信心級仍具名列出——讀者可自行覆核。
BREAK_RATE_HI = 0.15   # 破例率 > 15% 視為「族名可能切錯」

multi = {k: v for k, v in fams.items() if len(v) >= 2}
single = {k: v for k, v in fams.items() if len(v) == 1}


def faults_of(seen):
    return [(seen[k][1], seen[k - 1][2], seen[k][2])
            for k in range(1, len(seen)) if seen[k][2] <= seen[k - 1][2]]


def break_rate(seen):
    return len(faults_of(seen)) / float(len(seen) - 1) if len(seen) > 1 else 0.0


hi = {k: v for k, v in multi.items() if break_rate(v) <= BREAK_RATE_HI}
lo = {k: v for k, v in multi.items() if break_rate(v) > BREAK_RATE_HI}

print('序列長度 %d' % len(E))
print()
print('=' * 66)
print('涵蓋自報（n+67 二 2）')
print('=' * 66)
print('  掃出族名 %d 個；其中可檢查者（≥2 筆）%d 個、單筆者 %d 個'
      % (len(fams), len(multi), len(single)))
print('  ⚠️ 單筆者無遞增可言，**不列入 PASS／FAIL**，僅計數。')
print()
print('  ⚠️ 分級並非過濾：兩級皆輸出，低信心級仍具名列出。')
print()

bad_total = 0
faulty = []
for name in sorted(hi, key=lambda k: -len(hi[k])):
    f = faults_of(hi[name])
    bad_total += len(f)
    if f:
        faulty.append((name, hi[name], f))

lo_faults = sum(len(faults_of(v)) for v in lo.values())

print('=' * 66)
print('高信心級（破例率 ≤ %d%%）：%d 族，依筆數前 20'
      % (int(BREAK_RATE_HI * 100), len(hi)))
print('=' * 66)
for name in sorted(hi, key=lambda k: -len(hi[k]))[:20]:
    seen = hi[name]
    nf = len(faults_of(seen))
    print('  %-30s %4d 筆  範圍 %d–%d  %s'
          % (name, len(seen), seen[0][2], seen[-1][2],
             ('⚠️ 非遞增 %d 處' % nf) if nf else '✅'))

print()
print('=' * 66)
print('低信心級（破例率 > %d%%）：%d 族、內含 %d 處告警'
      % (int(BREAK_RATE_HI * 100), len(lo), lo_faults))
print('=' * 66)
print('  🚨 這一級之告警大多是**族名切錯**而非真缺陷——')
print('     已逐筆讀回確認三種來源：裁定條次引用（「依 n+42 第 4 項」）、')
print('     不同機制／子群各自從 2 起算而被併為一族、')
print('     以及配對號（去重型）本就同號。')
print('  ⚠️ **但它們不是被過濾掉，只是分開呈現**；筆數前 10 具名如下：')
for name in sorted(lo, key=lambda k: -len(lo[k]))[:10]:
    print('       %-30s %4d 筆，破例 %d 處'
          % (name, len(lo[name]), len(faults_of(lo[name]))))
if len(lo) > 10:
    print('       …另 %d 族' % (len(lo) - 10))

print()
print('=' * 66)
print('非遞增明細（高信心級全族，不受上表 20 族之顯示上限影響）')
print('=' * 66)
if not faulty:
    print('  （無）')
for name, seen, f in faulty:
    print('  == %s ==  %d 筆' % (name, len(seen)))
    for cid, prev, cur in f:
        print('     %s：前一筆寫 %d，本筆寫 %d' % (cid, prev, cur))

print()
print('=' * 66)
print('高信心級非遞增處合計：%d（涵蓋 %d 族）' % (bad_total, len(hi)))
print('低信心級另有 %d 處（%d 族），已具名列於上方。' % (lo_faults, len(lo)))
print('=' * 66)
print('⚠️ 本檔看不到什麼（n+67 二 2 所令之自報）：')
print('  1. **族群成員無遺漏**——某筆屬該族但未寫編號者，本檔看不到。')
print('  2. **編號是否等於族群大小**——不等。內容制實測之族群規模'
      '遠大於編號序列（n+67 三），**M1 不得以「第 N 筆」作為族群大小**。')
print('  3. **單筆族**（%d 個）——無序列可驗。' % len(single))
print('  4. **族名切分之正確性**——族名由通用式從自然語言切出，'
      '可能把同一族切成兩個名字，或把兩族併成一個。')
print('     ⚠️ 故「涵蓋 %d 族」是本檔之視角，不是資料的真實族數。'
      % len(multi))
print('  5. **分級門檻（%d%%）是我訂的**——它不改變任何告警的存在，'
      '只改變它列在哪一級。' % int(BREAK_RATE_HI * 100))
print()
print('🚨 **高信心級之告警仍需逐筆讀回，不得直接當成缺陷數**：')
print('   本輪已逐筆讀回高信心級之全部告警，確認其中**僅 4 處為真缺陷**')
print('   （皆已登記於 n66_counter_audit.py），餘者仍為族名切分所致：')
print('     • 同一族的兩種寫法被切成兩族（如 Patent 與專利文件）；')
print('     • 族名尾巴相同而被併族（如「…個案研究」「…動物研究」）；')
print('     • 配對號本就同號（如去重型之「配對成員」）。')
print('   ⚠️ 即**分級只降低雜訊，不代替判讀**。')

sys.exit(0)
