# -*- coding: utf-8 -*-
"""第九型（以自己產生的敘述作為資料）之全面自查。

🚨 n+75 立第九型並說「立規則的人是第一個要被規則檢查的人」。
**那我該回頭問：除了重疊清單，我還有哪些腳本在拿 `reason` 當資料？**

⚠️ 關鍵區分——**不是所有讀 `reason` 的腳本都犯第九型**：

  （甲）**正當**：檢查的對象**就是**我的敘述本身。
        例：`n59_counters.py` 驗族序號是否遞增——序號是我寫的，
        要驗的就是它；`scan_any.py` 驗夾雜外文——外文也是我寫的。
        **這類的資料來源與檢查對象一致，沒有錯位。**

  （乙）**第九型**：想知道**研究本身**的性質，卻去讀我的敘述。
        例：`n73_overlap.py` 第一版問「這篇研究屬於哪個國家樣本」，
        該看標題，卻比對了判讀理由。

本檔列出所有讀 `reason` 的腳本，逐一標記屬甲或乙，並說明理由。
**⚠️ 這份分類是我做的判斷，不是程式測出來的**——請協調者覆核。
"""
import glob
import io
import re

PAT = re.compile(r"\['reason'\]|\[.reason.\]|e\.get\('reason'\)")
hits = []
for p in sorted(glob.glob('.scratch/*.py')):
    try:
        src = io.open(p, encoding='utf-8').read()
    except Exception:
        continue
    if PAT.search(src) or "'reason'" in src:
        hits.append(p.split('/')[-1].split('\\')[-1])

print('讀取 judgements 之 reason 欄位的腳本：%d 個' % len(hits))
for h in hits:
    print('   ' + h)
print()

# 我的分類。鍵為檔名前綴，值為 (類別, 檢查對象, 理由)
CLASS = {
    'n59_counters': ('甲 正當', '我寫的族序號',
                     '要驗的就是序號本身是否遞增，資料來源與檢查對象一致'),
    'scan_any': ('甲 正當', '我寫的判讀文字',
                 '要找的就是我文字裡的夾雜外文'),
    'scan': ('甲 正當', '我寫的判讀文字', '同上'),
    'n68_scan_audit': ('甲 正當', '我寫的判讀文字',
                       '慣用語 vs 漏譯之分類，對象即我的用字'),
    'n68_xref': ('甲 正當', '我寫的引述',
                 '驗「我引的那筆是否真如我所述」，對象即引述本身'),
    'n66_counter_audit': ('甲 正當', '我寫的編號', '錯號登記簿'),
    'n71_seqaudit': ('甲 正當', '我寫的族序號', '同 n59'),
    'n64_skillperf': ('⚠️ 邊界', '構念之素材數',
                      '問「哪些研究屬該構念」——**該由標題／摘要判定**，'
                      '惟該構念無標題層特徵詞，只能由判讀理由識別；'
                      '🚨 已於該檔標明此限制，屬「無替代來源」之例外'),
    'n65_direction': ('⚠️ 邊界', '各研究之效果方向',
                      '方向是研究的性質而非我的敘述，惟其來源為摘要、'
                      '我已逐筆記錄所依據之摘要原句；🚨 仍應以摘要為準'),
    'n73_overlap': ('🚨 乙 第九型', '研究屬哪個樣本群',
                    '**已於第 355 輪自行發現並改為掃標題**（n73_overlap2）'),
    'n68_fam': ('甲 正當', '我寫的族序號', '判讀前量測既有序號'),
    'p28': ('甲 正當', '我寫的族序號與先例', '同上'),
    'n73_overlap2': ('甲 正當', '標題',
                     '已改為掃 worksheet 之 title 欄位，非我的敘述'),
    # 以下為第二階段（n75_type9_scan.py 之 C 級）逐檔檢視後補入。
    'n60_tags': ('甲 正當', '我下的掛牌標記',
                 '比對的是 `[age]`／`[chronic-strategy]` 等我自己寫入之'
                 '標記字串，檢查對象即該些標記本身'),
    'n66_step1_criterion': ('甲 正當', '我寫的排除理由',
                            'n+66（一）問「我的排除理由是否只引契約未列舉」'
                            '——問的就是我的措辭'),
    'n42_': ('甲 正當', '我寫的排除理由',
             'n+42 系列問「哪些判讀之理由屬該裁定所涵蓋」，對象即理由'),
    'mk_deferred': ('甲 正當', '我寫的排除理由',
                    '掛待裁名單，依理由措辭挑出待裁者'),
    'cnt': ('甲 正當', '我寫的族序號', '族序號計數，同 n59'),
    'ch_': ('甲 正當', '我寫的判讀', 'critical-harms 批次之 QA'),
    'ch76_qa': ('甲 正當', '我寫的判讀', '同上'),
    'qa': ('甲 正當', '我寫的判讀', 'append 前之結構 QA（筆數、順序、非空）'),
    'term2': ('甲 正當', '不讀 reason 做分類',
              '僅為錯誤訊息拼接，未以 reason 判定任何研究性質'),
    'p280_prec': ('甲 正當', '我寫的族序號與先例', '判讀前量測'),
    'p282_prec': ('甲 正當', '我寫的族序號與先例', '同上'),
    'n50_ratchet': ('甲 正當', '不以 reason 做分類',
                    '僅將原判讀理由抄進覆蓋層之 note 欄位備查，'
                    '棘輪方向之判定完全依 opinion 欄位'),
    'audit_n35': ('甲 正當', '我的理由與我的決定是否自相矛盾',
                  '問「哪些 advance 之理由自承結局不在契約清單」'
                  '——對象就是我的敘述與決定之一致性'),
    'sweep_sa': ('甲 正當（且為正解示範）', '設計是否單臂',
                 '⚠️ 它問的確實是研究性質（第九型的形狀），'
                 '**惟它用兩張獨立的網**：我的理由措辭 ＋ 摘要原文，'
                 '且輸出逐筆標明命中來自 `[reason]` 抑或 `[abs]`；'
                 '🚨 即「用敘述當線索但不當證據」，此為第九型之正解'),
    # ── 第 361 輪：B 級 15 個逐檔判定完畢，補入 ──
    'sweep5': ('甲 正當（正解示範）', '設計是否單臂',
               '主判定用摘要之 `cmp_pat`，理由僅為第三道補網（elif），'
               '且輸出以 BLANK／NO-CMP／REASON 標明命中來源'),
    'sweep2': ('甲 正當', '不以 reason 判定',
               'reason 僅隨題摘一併印出供我人工閱讀，未參與任何篩選條件'),
    'sweep4': ('甲 正當', '不以 reason 判定', '同 sweep2'),
    'sweep6': ('甲 正當', '不以 reason 判定', '同 sweep2'),
    'unc': ('甲 正當', '不以 reason 判定', '同 sweep2'),
    'chk': ('甲 正當', '不以 reason 判定',
            'reason 僅印出供人工閱讀（chk2 之關鍵字為列印過濾，'
            '非研究性質之判定）'),
    'prec137': ('甲 正當', '我寫的先例與族序號', '判讀前讀回先例'),
    'prec_e8': ('甲 正當', '不以 reason 判定', 'reason 僅印出供閱讀'),
    'probe137': ('甲 正當', '不以 reason 判定', '同上'),
    'probe_unclear': ('甲 正當', '不以 reason 判定', '同上'),
    'p2_final': ('甲 正當', '我寫的理由之結構',
                 '量測空理由數與理由長度分布，對象即理由本身'),
    'verify_n31': ('甲 正當（三網並用）', '記錄是否含某特徵',
                   '`pat.search(ab) or pat.search(ti) or pat.search(reason)`'
                   '——摘要與標題為主，理由為第三網，且輸出標明來源為 '
                   '`ABS`／`TITLE`／`reason-only`'),
    'chk5': ('甲 正當', '我寫的族序號', '族序號抽取，同 n59'),
}

print('== 我的分類（⚠️ 此為我的判斷，非程式測得，請覆核）==')
# ⚠️ 以**最長**前綴比對：`n73_overlap2` 必須配到自己那條，
#    否則會被 `n73_overlap` 前綴接走而誤標為第九型（本檔第一版之錯）。
unclassified = []
for h in hits:
    cands = [k for k in CLASS if h.startswith(k)]
    key = max(cands, key=len) if cands else None
    if key is None:
        unclassified.append(h)
        continue
    cat, obj, why = CLASS[key]
    print('   %-28s %s' % (h, cat))
    print('        檢查對象：%s' % obj)
    print('        理由：%s' % why)
print()
# ⚠️ 未分類者以 `n75_type9_scan.py` 之行為分層交叉，不讓兩份輸出各說各話。
BUILDER = re.compile(r"^V\['[0-9a-f]{8}'\]\s*=", re.M)
READ_REASON = re.compile(r"\['reason'\]|e\.get\('reason'\)")
READ_TITLE = re.compile(r"\['title'\]|get\('title'\)|\['abstract'\]")
tiers = {'A 建置檔（產生敘述、不消費）': [],
         'B 讀 reason 但也讀 title/abstract': [],
         '🚨 C 只讀 reason（高風險，須逐檔判）': []}
for n in unclassified:
    src = io.open('.scratch/' + n, encoding='utf-8').read()
    if BUILDER.search(src) and not READ_REASON.search(src):
        tiers['A 建置檔（產生敘述、不消費）'].append(n)
    elif not READ_REASON.search(src):
        tiers['A 建置檔（產生敘述、不消費）'].append(n)
    elif READ_TITLE.search(src):
        tiers['B 讀 reason 但也讀 title/abstract'].append(n)
    else:
        tiers['🚨 C 只讀 reason（高風險，須逐檔判）'].append(n)

print('== ❓ 未分類 %d 個——以行為分層交叉（同 n75_type9_scan.py）=='
      % len(unclassified))
for k, v in tiers.items():
    print('   %-34s %3d 個' % (k, len(v)))
    if v and k.startswith('🚨'):
        print('        %s' % '、'.join(v))
print()
print('🚨 結論分三部分，不可混為一談：')
print('   （一）**已分類者中**，確認為第九型者僅 `n73_overlap.py` 一個，')
print('        且已於第 355 輪自行改正為 `n73_overlap2.py`（掃標題）。')
print('   （二）未分類之 %d 個中，**%d 個為 A 級（不消費 reason，'
      % (len(unclassified), len(tiers['A 建置檔（產生敘述、不消費）'])))
print('        結構上不可能是第九型）**、%d 個 B 級（有替代來源可交叉）、'
      % len(tiers['B 讀 reason 但也讀 title/abstract']))
print('        %d 個 C 級。'
      % len(tiers['🚨 C 只讀 reason（高風險，須逐檔判）']))
n_b = len(tiers['B 讀 reason 但也讀 title/abstract'])
n_c = len(tiers['🚨 C 只讀 reason（高風險，須逐檔判）'])
if n_b == 0 and n_c == 0:
    print('   （三）✅ **第 361 輪已將 B 級 15 個逐檔判定完畢**，'
          'B 與 C 兩層現皆為 0。')
    print('        🚨 **惟「全 lane 無第九型」仍是一個有邊界的宣稱**：')
    print('        本檔只涵蓋 `.scratch/*.py`，且分類依據是我讀程式碼後之判斷。')
    print('        ⚠️ `ahig/` 我另行查過（不是憑印象）：10 個模組出現 reason')
    print('        字樣，**無一讀取 `entry[\'reason\']` 做分類**——')
    print('          • `judgement_worksheet` 只**寫入**並驗其非空；')
    print('          • `screening_decisions` 用的是列舉型 `primaryReasonCode`，')
    print('            非自由文；')
    print('          • `grade.py` 之 reasons 是它自己生成的降級理由。')
    print('        **若協調者對任一分類有異議，請直接指出該檔。**')
else:
    print('   （三）⚠️ **尚有 B 級 %d、C 級 %d 未逐檔判定**——本檔目前'
          % (n_b, n_c))
    print('        **不足以**宣稱「全 lane 無第九型」。')
print()
print('⚠️ 兩個邊界案例（n64_skillperf、n65_direction）我標了限制而非改寫')
print('   ——理由是那兩個構念在標題層沒有特徵詞，沒有替代資料來源；')
print('   🚨 但那是我的判斷，若協調者認為仍屬第九型，請指示。')
