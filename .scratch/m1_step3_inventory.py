# -*- coding: utf-8 -*-
"""M1 第 ③ 步（其零）：60 篇校準集之全文取得現況盤點。

🚨 第 ③ 步不是從零開始取全文——W4a 階段已取得大量全文。
**故第一件事是盤點，不是發請求**：先知道缺什麼，才知道要跟外部服務要什麼。
⚠️ 這與第 ② 步「先算母體再抽樣」同一個道理，也與 n+97（三）「先建清單再核對」同源。

**⚠️ 本檔不發任何網路請求**，只讀私有根既有之 manifest。

輸出只有計數、狀態與不透明 id，零文獻內容（不讀 JATS 正文、不輸出標題）。
"""
import io
import json
import os
import sys
from collections import Counter

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

PRIV = 'C:/Users/User/Desktop/claude/ahig-private'
FT = os.path.join(PRIV, 'fulltext')
DEST = '.scratch/m1_step3_inventory.json'

cal = json.load(io.open('.scratch/m1_step2_calibration_set.json',
                        encoding='utf-8'))
by_pool = {pid: d['candidateIds'] for pid, d in cal['draws'].items()}
all_ids = [x for ids in by_pool.values() for x in ids]
assert len(all_ids) == 60 == len(set(all_ids)), '🚨 校準集不是 60 篇相異'

# 目錄名格式：<candidateId 尾段 24 碼>-<16 碼>
dirs = {}
for d in os.listdir(FT):
    head = d.split('-')[0]
    dirs.setdefault(head, []).append(d)


def manifest_of(cid):
    """回傳該 candidateId 之 manifest（取最新者），查無則 None。"""
    tail = cid.split(':')[-1]
    cands = dirs.get(tail) or []
    best = None
    for d in cands:
        p = os.path.join(FT, d, 'manifest.json')
        if not os.path.isfile(p):
            sub = os.path.join(FT, d, 'manifests')
            if os.path.isdir(sub):
                fs = sorted(os.listdir(sub))
                if fs:
                    p = os.path.join(sub, fs[-1])
            else:
                continue
        try:
            m = json.load(io.open(p, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        # ⚠️ 同一筆可能有多個目錄（多次嘗試）；取 status=acquired 者優先
        if best is None or m.get('status') == 'acquired':
            best = m
    return best


def unresolved_sources(m):
    """逐筆列出每個來源之嘗試結論——**「為什麼還沒取得」必須可查。**

    🚨 n+102（二）：前一版之 `records` 只有 status，**產物說不出任何一筆為什麼
    incomplete**，故「38 筆卡在缺信箱」協調者無法自版控驗證，只能採信自陳。
    ⚠️ 這與契約 `ineligibleReplacement` 要求「記錄被剔除者的理由碼」是同一紀律。

    ⚠️ 欄位名在不同來源之 manifest 中不一致（conclusion／outcome／status／reason），
    故逐一嘗試；**🚨 取不到就記 `<未載>`，不猜。**
    """
    out = []
    for a in ((m or {}).get('attempts') or []):
        concl = (a.get('conclusion') or a.get('outcome')
                 or a.get('status') or '<未載>')
        out.append({
            'sourceId': a.get('sourceId'),
            'conclusion': concl,
            'reason': a.get('reason'),
            'httpStatus': a.get('httpStatus'),
        })
    return out


LICENCE_SHAPES = Counter()
BLOCK_REASONS = Counter()


def _licence_text(m):
    """取授權文字。⚠️ manifest 之 licence 型別不一致，兩種都要處理。

    🚨 不把不認得的型別當成「沒有授權」——那會把一個格式問題誤報成合規問題。
    """
    lic = (m or {}).get('licence')
    LICENCE_SHAPES[type(lic).__name__] += 1
    if isinstance(lic, dict):
        return lic.get('text') or lic.get('href')
    if isinstance(lic, str):
        return lic.strip() or None
    return None


rows, status_c, source_c = [], Counter(), Counter()
missing = []
for pid, ids in by_pool.items():
    for cid in ids:
        m = manifest_of(cid)
        st = (m or {}).get('status') or 'no-manifest'
        status_c[st] += 1
        if m:
            source_c[m.get('sourceType') or '<未載>'] += 1
        ok = st == 'acquired'
        if not ok:
            missing.append({'poolId': pid, 'candidateId': cid, 'status': st})
        rows.append({
            'poolId': pid, 'candidateId': cid, 'status': st,
            'sourceType': (m or {}).get('sourceType'),
            'hasSections': bool((m or {}).get('sectionsFile')),
            # ⚠️ `licence` 的型別不一致：有些 manifest 存 dict（含 href/text），
            #    有些直接存字串。**這本身是一項發現，記在產物的 licenceShapes。**
            'licenceText': bool(_licence_text(m)),
            # 🚨 n+102（二）所要求之逐筆理由碼
            'unresolvedSources': unresolved_sources(m),
        })
        for s in rows[-1]['unresolvedSources']:
            if s['reason']:
                BLOCK_REASONS['%s / %s' % (s['sourceId'], s['reason'])] += 1

print('校準集 60 篇之全文取得現況（讀既有 manifest，未發任何請求）')
print()
print('=== 狀態分布 ===')
for k, v in status_c.most_common():
    print('   %-20s %3d' % (k, v))
print()
print('=== 來源型別 ===')
for k, v in source_c.most_common():
    print('   %-20s %3d' % (k, v))
print()
print('=== 各池取得率 ===')
print('%-34s %6s %8s %8s' % ('池', '篇數', 'acquired', '取得率'))
print('-' * 62)
pool_rows = []
for pid, ids in by_pool.items():
    got = sum(1 for r in rows if r['poolId'] == pid and r['status'] == 'acquired')
    pool_rows.append({'poolId': pid, 'total': len(ids), 'acquired': got})
    print('%-34s %6d %8d %7.0f%%'
          % (pid, len(ids), got, 100 * got / len(ids)))
print('-' * 62)
acq = status_c.get('acquired', 0)
print('%-34s %6d %8d %7.0f%%' % ('合計', len(all_ids), acq, 100 * acq / len(all_ids)))

print()
print('=== 🚨 逐筆理由碼彙總（n+102 二）——使「為什麼還沒取得」可自版控驗證 ===')
for k, v in BLOCK_REASONS.most_common():
    print('   %-46s %3d' % (k, v))
if not BLOCK_REASONS:
    print('   （無任何帶 reason 之嘗試）')
print()
if missing:
    print('🚨 未取得者 %d 筆：' % len(missing))
    for m in missing:
        print('   %-34s %s  status=%s'
              % (m['poolId'], m['candidateId'].split(':')[-1], m['status']))
    print('⚠️ 下一步須逐筆查明原因（非 OA／無 PMC 對應／取得失敗），'
          '再決定是否對外查詢，不一律重試。')
else:
    print('✅ 60 篇全數已取得全文。')

# ⚠️ 有 sections 才談得上第 ④ 步之抽取；分開報，不與 acquired 混為一談。
no_sec = [r for r in rows if r['status'] == 'acquired' and not r['hasSections']]
print()
print('已取得但無 sections 解析檔：%d 筆 %s'
      % (len(no_sec), '🚨 第 ④ 步無法對其抽取' if no_sec else '✅'))
no_lic = [r for r in rows if r['status'] == 'acquired' and not r['licenceText']]
print('已取得但 manifest 未載授權文字：%d 筆 %s'
      % (len(no_lic), '⚠️ 交付前須查明' if no_lic else '✅'))

doc = {
    'schemaVersion': 1,
    'documentType': 'm1-step3-fulltext-inventory',
    'purpose': ('Inventory of full-text acquisition status for the 60-record '
                'calibration set. Read-only over existing manifests; issues '
                'no network requests.'),
    'calibrationSetHash': cal['calibrationSetHash'],
    'counts': {'total': len(all_ids), 'acquired': acq,
               'byStatus': dict(status_c), 'bySourceType': dict(source_c)},
    'pools': pool_rows,
    'missing': missing,
    'acquiredWithoutSections': [r['candidateId'] for r in no_sec],
    'acquiredWithoutLicenceText': [r['candidateId'] for r in no_lic],
    'licenceShapes': dict(LICENCE_SHAPES),
    'blockReasons': dict(BLOCK_REASONS),
    'wordingConstraint': (
        'Post-query state (all 60 queried). n+102(3) barred calling 6/60 an '
        'acquisition rate while 39 were still unqueried; that condition is '
        'now cleared -- every record has a settled answer. Correct wording: '
        '"6 full texts acquired; 38 confirmed to have no OA full text; 15 '
        'located but not retrieved (9 PDF, 6 landing page) because those sit '
        'off the JATS path; 1 incomplete." Still do NOT write "54 '
        'unobtainable" -- the 15 located ones are not known to be '
        'unobtainable, only not yet retrieved by the current path.'),
    'records': rows,
    'contentNote': 'Status and opaque ids only. No literature content.',
}
doc['inventoryHash'] = content_hash(doc['records'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
