# -*- coding: utf-8 -*-
"""傾印某一頁之未判讀記錄，供逐筆判讀。

輸出兩個檔案：
  .scratch/_pNNN.txt       全文（含標題與摘要）——**不得 commit**，
                           判讀完即刪；n+48 內容制衛生檢查會攔。
  .scratch/_pNNN_ids.json  僅 short 與 candidateId——可 commit，
                           供 mk_pNNN.py 取用（不得人手轉寫識別碼）。

用法：python -X utf8 .scratch/dump_page.py <page>
"""
import io
import json
import os
import sys

ROOT = os.environ.get('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
RUN = ROOT.replace('\\', '/') + \
    '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

page = int(sys.argv[1])
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
judged = {e['candidateId'] for e in d['entries']}

ab, pv = {}, {}
if os.path.exists(DEST + '/abstracts.json'):
    ab = json.load(open(DEST + '/abstracts.json', encoding='utf-8'))
if os.path.exists(DEST + '/provenance.json'):
    pv = json.load(open(DEST + '/provenance.json',
                        encoding='utf-8'))['records']

# ---- n+56（三）：同標題副本查找（僅適用於「尚未判讀」之記錄）----
# 判讀前若該筆無摘要、但池中有同標題副本且副本有摘要，以副本摘要
# 供判讀使用，並記錄來源為副本。這是資訊條件之改善，前瞻適用。
# ⚠️ 已判讀者不適用——n+56（一）明令不重判（n+49 位置盲目）。
import re as _re


def _norm(t):
    return _re.sub(r'[^a-z0-9 ]', '', (t or '').lower()).strip()


_by_title = {}
for _it in w['items']:
    _by_title.setdefault(_norm(_it.get('title')), []).append(_it)


def dup_text(it):
    """同標題副本之全文（無則 None）。空標題不比對。"""
    key = _norm(it.get('title'))
    if not key:
        return None, None
    for tw in _by_title.get(key, []):
        if tw['candidateId'] == it['candidateId']:
            continue
        t = (tw.get('abstract') or '').strip() or ab.get(tw['candidateId'])
        if t:
            return t, tw['candidateId']
    return None, None


buf, ids, total = [], [], 0
for it in w['items']:
    if it['page'] != page:
        continue
    total += 1
    cid = it['candidateId']
    if cid in judged:
        continue
    text = (it.get('abstract') or '').strip() or ab.get(cid) or ''
    st = 'inline' if (it.get('abstract') or '').strip() else \
        (pv.get(cid) or {}).get('status', 'no-abstract')
    if not text:
        text, dup_id = dup_text(it)
        if text:
            st = 'same-title-duplicate:%s' % dup_id[-8:]
    buf.append('--- %s seq%s [%s]' % (cid[-8:], it['seq'], st))
    buf.append('Y:%s T:%s' % (it.get('publicationYear'),
                              it.get('publicationTypes')))
    buf.append('TITLE: %s' % it.get('title'))
    if text:
        buf.append('ABS: %s' % text[:1500])
    buf.append('')
    ids.append({'short': cid[-8:], 'candidateId': cid})

buf.append('[p%d unjudged: %d of %d]' % (page, len(ids), total))
io.open('.scratch/_p%d.txt' % page, 'w', encoding='utf-8').write(
    '\n'.join(buf))

# ⚠️ 不得以空清單覆寫既有 ids 檔。重跑已判畢之頁時 ids 會是空的，
# 若直接寫出就會把該頁 mk_pNNN.py 的識別碼來源清空——而識別碼
# **只能來自程式輸出**，清掉就沒有合法來源可重建。
ids_path = '.scratch/_p%d_ids.json' % page
if ids or not os.path.exists(ids_path):
    json.dump(ids, open(ids_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
else:
    print('[kept existing %s: page fully judged, refusing to blank it]'
          % ids_path)

# n+51 管線約束之「涵蓋」= **補摘要已跑到終局**，非「有摘要文字」。
# 三種終局狀態代表上游已窮盡、再試也拿不到（與 n+52 名冊之
# 39＋29＋9 組成同義），故與已取得摘要者同列為完成。
TERMINAL = {'upstream-no-abstract', 'not-found-all-ids', 'no-identifier'}


def _resolved(it):
    cid = it['candidateId']
    if (it.get('abstract') or '').strip() or cid in ab:
        return True
    return (pv.get(cid) or {}).get('status') in TERMINAL


page_items = [it for it in w['items'] if it['page'] == page]
resolved = sum(1 for it in page_items if _resolved(it))
withtext = sum(1 for it in page_items
               if (it.get('abstract') or '').strip()
               or it['candidateId'] in ab)
print('page %d: %d recs, unjudged %d, enrich-complete %d/%d '
      '(with-text %d)' % (page, total, len(ids), resolved, total, withtext))
