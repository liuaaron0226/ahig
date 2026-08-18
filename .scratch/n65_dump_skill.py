# -*- coding: utf-8 -*-
"""n+65（三）令之回看：傾印 27 筆技能表現素材之摘要，供判定結果方向。

⚠️ **這不是重新判讀，是回看已判讀者的結果方向。**
n+56（一）明令不重判（n+49 位置盲目），本腳本**不改動任何
`opinion`／`effectiveDecision`**，只讀摘要以補記「該筆的技能表現
結果朝哪個方向」——**那是判讀當時未寫進理由的資訊，不是判讀本身。**

輸出 `.scratch/_n65skill.txt`（含摘要全文，**不得 commit**，
n+48 內容制檢查會攔；已在 `.gitignore` 之 `_p[0-9]*.txt` 樣式外，
故另行逐檔列名加入 ignore——依 n+65（一）2，`.scratch/` 不得
`git add -A`，本檔一律不加入）。
"""
import io
import json
import os

ROOT = os.environ.get('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
RUN = ROOT.replace('\\', '/') + \
    '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

rows = json.load(io.open('.scratch/m1_skill_performance.json',
                         encoding='utf-8'))
targets = [r['short'] for r in rows
           if r['direction'] == '未載' and not r['titleOnly']]

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
recs = w['items']
ab = {}
if os.path.exists(DEST + '/abstracts.json'):
    ab = json.load(io.open(DEST + '/abstracts.json', encoding='utf-8'))

by_short = {}
for r in recs:
    cid = r.get('candidateId', '')
    if cid[-8:] in targets:
        by_short[cid[-8:]] = r

out = []
missing = []
for s in targets:
    r = by_short.get(s)
    if not r:
        missing.append(s)
        continue
    cid = r['candidateId']
    # ⚠️ worksheet 之欄位名是 `abstract`，不是 `abstractText`。
    # 第一版只查 `abstractText`，於是 27 筆中有 25 筆被回報成
    # 「實際無摘要」——**那是假的**：判讀理由裡帶著 p 值與具體
    # 數字，摘要不可能真的空。
    # 🚨 這正是 n+64／n+65 所指「把『我沒看到』寫成『沒有』」，
    # 而且發生在我執行那道裁定的當下。**猜欄位名比猜資料更危險**，
    # 因為它安靜地回報一個看似合理的數字。
    txt = (r.get('abstract') or r.get('abstractText') or ab.get(cid) or '')
    if isinstance(txt, dict):
        txt = txt.get('abstract') or txt.get('abstractText') \
            or txt.get('text') or ''
    out.append('--- %s\nTITLE: %s\nABS: %s\n'
               % (s, r.get('title', ''), (txt or '(無摘要)')[:2200]))

io.open('.scratch/_n65skill.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('targets %d, dumped %d, missing %d'
      % (len(targets), len(out), len(missing)))
if missing:
    print('⚠️ worksheet 查無：', missing)
no_abs = [o.split('\n')[0][4:] for o in out if '(無摘要)' in o]
print('⚠️ 其中實際無摘要者 %d 筆：%s' % (len(no_abs), ' '.join(no_abs)))
