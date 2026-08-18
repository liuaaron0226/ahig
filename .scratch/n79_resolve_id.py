# -*- coding: utf-8 -*-
"""把判讀原文裡的任意 id 片段解析成本檔所用之末八碼寫法。

🚨 為什麼需要這支：第 391、392、393 連續三輪，我都在寫「與 XXX 並列」
時直接把另一筆判讀敘述裡的 id 抄進 W4b 檔——那正是第九型缺陷
（以敘述為資料來源）。三次的錯法完全相同：

  - 判讀原文用 **id 前綴**（`591748db`）稱呼記錄，
    W4b 檔用 **末八碼**（`cf9f6a42`）——**兩者是同一筆記錄的兩種寫法**，
    抄過去必然對不上。
  - 其中還混著**根本不存在**的 id（`2a7c3e0b`、`faf6ca11`），
    若非驗證器攔下，會以「某某清單共 N 筆」之姿交到擁有者手上。

⚠️ 驗證器攔得住「寫錯了」，攔不住「寫的時候沒查」——它是事後閘門。
**本檔是事前工具：跨記錄引用一律先過這裡，不從敘述複製。**

用法：
    python -X utf8 .scratch/n79_resolve_id.py 591748db faf6ca11 ...

輸出每個片段之判定：解析成功者印出末八碼與標題首句，
查無者明確標示 NOT-FOUND——**⚠️ 查無不是「大概是別的寫法」，
是「這個 id 不能寫進檔案」。**
"""
import io
import json
import sys

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')

E = json.load(io.open(ROOT + '/standard-full-screen-pass-1/judgements.json',
                      encoding='utf-8'))['entries']
W = json.load(io.open(ROOT + '/standard-full-screen-pass-1/worksheet.json',
                      encoding='utf-8'))
page = dict((it['candidateId'], it['page']) for it in W['items'])
by_full = dict((x['candidateId'], x) for x in E)

frags = sys.argv[1:]
if not frags:
    print(__doc__)
    sys.exit(0)

bad = []
for frag in frags:
    # ⚠️ 判讀原文之兩種寫法皆為 8 碼；短於 8 碼者不是寫法差異，是打錯或截斷，
    # **不可讓它去比對——比中了反而給出一個看似成功的錯誤答案。**
    if len(frag) < 8:
        print('🚨 %s  片段僅 %d 碼 —— id 之兩種寫法皆為 8 碼，'
              '短片段一律拒收（比中亦不可信）' % (frag, len(frag)))
        bad.append(frag)
        continue
    hits = [c for c in by_full if frag in c]
    if not hits:
        print('🚨 %s  NOT-FOUND —— 判讀庫查無，不得寫入檔案' % frag)
        bad.append(frag)
        continue
    if len(hits) > 1:
        # ⚠️ 片段太短而撞到多筆：這種情況必須人工裁決，不可自動選一筆。
        print('⚠️ %s  片段不唯一，命中 %d 筆（僅列前 5）：%s'
              % (frag, len(hits), [c[-8:] for c in hits[:5]]))
        bad.append(frag)
        continue
    cid = hits[0]
    last8 = cid[-8:]
    note = '' if frag == last8 else '  （⚠️ 原文為前綴寫法，檔內須寫 %s）' % last8
    reason = by_full[cid].get('reason', '')
    head = reason.split('。')[0][:60].replace('\n', ' ')
    print('✅ %s → `%s`  p%s%s' % (frag, last8, page.get(cid, '?'), note))
    print('     %s' % head)

if bad:
    print()
    print('🚨 上列 %d 個片段不可寫入 W4b 檔' % len(bad))
    sys.exit(1)
