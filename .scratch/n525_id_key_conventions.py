# -*- coding: utf-8 -*-
"""識別碼切法之清冊：**同一筆紀錄被兩種切法標識，而併接時不會有人提醒你。**

## 🚨 三輪之內兩次

| 輪 | 情形 |
|---|---|
| 522 | `idFrag` 是尾段之**前 16 碼**，而我比對**後 16 碼** → 控制探針整個沒跑成 |
| 524 | `n490` 以**前 16 碼**為鍵、近期產物以**尾 8 碼**為鍵 → 直接比對，7 筆會全部判成「未涵蓋」 |

> **🚨 兩次的失敗方式一樣：交集為空，而空交集看起來像「那邊真的沒有」。**
> **⚠️ 而它不會報錯——併接照跑，只是什麼都沒對上。**

**✅ 故本檔把「哪一份產物用哪一種切法」列成一張表**，
**🚨 讓要併接的人在寫併接之前就看得到不一致。**

## 切法（🚫 逐一寫明，不藏在程式裡）

| 名稱 | 樣子 | 出處 |
|---|---|---|
| `full` | `ahig:candidate:publication:<24 碼>` | 佇列、校準集、遞補 |
| `frag16` | 尾段之**前 16 碼** | `n489`／`n490`（欄名多為 `idFrag`） |
| `hex8` | **8 碼十六進位**——🚨 可能是**前 8** 也可能是**後 8**，形狀分不出 | `idTail`（後 8）／`dir`（前 8） |
| `dir24` | 目錄名前綴之 24 碼 | 走目錄之產物 |

## 🚨 而 8 碼那一類，本身又是一個陷阱

⚠️ 初版把 8 碼一律叫 `tail8`。**🚫 錯的。**
本室有兩種 8 碼：**`dir[:8]`（目錄名之前 8 碼）與 `cid[-8:]`（id 之後 8 碼）**。

> **🚨 兩者形狀一模一樣，光看樣子分不出來——而它們併接起來交集是空的。**
> **⚠️ 也就是說：兩份產物都標「8 碼」，仍然可能對不上。**

**✅ 故改為拿已知的完整 id 去比對，實測那一欄到底是頭還是尾**（`head8`／`last8`）。

## 🚨 這張表擋得住什麼、擋不住什麼

- ✅ 擋得住：**寫併接之前**看不出兩邊切法不同。
- 🚨 **擋不住已經寫好的併接**——⚠️ 本檔不掃描程式碼，只看產物。
- 🚨 亦擋不住：**同一份產物內混用兩種切法**——⚠️ 本檔會把它列成「多種」，
  **🚫 但不判斷那樣對不對。**

## 🚨 控制探針

**⚠️ 一個什麼都認得出來的分類器，會把每份產物都標成「四種切法都有」而毫無用處；
一個什麼都認不出的，會回報「沒有識別碼」。**
**✅ 故兩向皆探：四種真樣本須各自歸位，四種假樣本（英文字、日期、雜湊全長）須一律不認。**
"""
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
from ahig.contracts.freeze import content_hash  # noqa: E402

S = Path('.scratch')
FULL = re.compile(r'^ahig:candidate:[a-z]+:[0-9a-f]{24}$')
HEX24 = re.compile(r'^[0-9a-f]{24}$')
HEX16 = re.compile(r'^[0-9a-f]{16}$')
HEX8 = re.compile(r'^[0-9a-f]{8}$')


def slicing(value):
    """回傳切法名稱，或 None。🚨 只認這四種，🚫 其餘一律不認。"""
    if not isinstance(value, str):
        return None
    if FULL.match(value):
        return 'full'
    if HEX24.match(value):
        return 'dir24'
    if HEX16.match(value):
        return 'frag16'
    if HEX8.match(value):
        # 🚨 8 碼十六進位**分不出頭尾**——⚠️ 見下方 resolve_hex8()。
        return 'hex8'
    return None


# ── 🚨 初版把 8 碼一律叫 `tail8`，而那是錯的 ────────────────────
# ⚠️ 本室有兩種 8 碼：`dir[:8]`（目錄名之**前** 8 碼）與 `cid[-8:]`（id 之**後** 8 碼）。
# 🚨 兩者形狀一模一樣，故光看樣子分不出來——**而它們併接起來交集是空的。**
# ✅ 故改為拿已知的完整 id 去比對，實測那一欄到底是頭還是尾。
def known_ids():
    ids = set()
    try:
        cal = json.load(io.open(S / 'm1_step2_calibration_set.json',
                                encoding='utf-8'))
        for d in cal['draws'].values():
            ids |= set(d['candidateIds'])
        bf = json.load(io.open(S / 'm1_step3_backfill.json', encoding='utf-8'))
        for pool in bf['pools']:
            for r in (pool.get('backfilled') or []):
                if r.get('candidateId'):
                    ids.add(r['candidateId'])
    except Exception:
        pass
    return {i.split(':')[-1] for i in ids}


TAILS = known_ids()
HEAD8 = {t[:8] for t in TAILS}
LAST8 = {t[-8:] for t in TAILS}


def resolve_hex8(values):
    """回傳 'head8'／'last8'／'both'／'unresolved'。🚨 以實際 id 比對，🚫 不猜。"""
    vs = {v for v in values if HEX8.match(v or '')}
    if not vs or not TAILS:
        return 'unresolved'
    h = len(vs & HEAD8)
    l = len(vs & LAST8)
    if h and not l:
        return 'head8'
    if l and not h:
        return 'last8'
    if h and l:
        return 'both'
    return 'unresolved'


def walk(doc, depth=0):
    """產生 (欄名, 切法)。⚠️ 只下探兩層——🚫 更深的結構本檔不看。"""
    if depth > 2:
        return
    if isinstance(doc, dict):
        for k, v in doc.items():
            sl = slicing(v)
            if sl:
                yield k, sl, v
            else:
                yield from walk(v, depth + 1)
    elif isinstance(doc, list):
        for v in doc[:400]:
            yield from walk(v, depth + 1)


print('=== 識別碼切法清冊（🚫 唯讀）===')
print()
print('一、控制探針——🚨 兩向皆須如預期')
good = [('ahig:candidate:publication:' + '0' * 24, 'full'),
        ('a' * 24, 'dir24'), ('b' * 16, 'frag16'), ('c' * 8, 'hex8')]
bad = ['publishedVersion', '2026-08-30', 'sha256:' + 'd' * 64, 'S3-tte']
ok = True
for v, want in good:
    got = slicing(v)
    ok = ok and (got == want)
    print('   %s %-34s → %s（期待 %s）'
          % ('✅' if got == want else '🚨', v[:34], got, want))
for v in bad:
    got = slicing(v)
    ok = ok and (got is None)
    print('   %s %-34s → %s（期待 不認）'
          % ('✅' if got is None else '🚨', v[:34], got))
if not ok:
    sys.exit('🚨 控制探針未過——🚫 不報清冊。')
print('   ✅ 四真四假皆如預期。')
print()

rows, by_slicing = [], defaultdict(list)
for p in sorted(S.glob('n[45][0-9][0-9]_*.json')) + [S / 'executor_cells.json']:
    if not p.exists():
        continue
    try:
        doc = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        continue
    kinds = Counter()
    fields = defaultdict(set)
    hex8_by_field = defaultdict(set)
    for field, kind, value in walk(doc):
        kinds[kind] += 1
        fields[kind].add(field)
        if kind == 'hex8':
            hex8_by_field[field].add(value)
    if not kinds:
        continue
    used = sorted(kinds)
    resolved = {f: resolve_hex8(v) for f, v in hex8_by_field.items()}
    rows.append({'artefact': p.name, 'slicings': used,
                 'counts': dict(kinds),
                 'fields': {k: sorted(v)[:4] for k, v in fields.items()},
                 'hex8Resolved': resolved})
    for k in used:
        by_slicing[k].append(p.name)

print('二、逐份產物')
print('   %-42s %s' % ('產物', '切法（欄名例）'))
print('   ' + '-' * 92)
for r in rows:
    parts = []
    for k in r['slicings']:
        names = '／'.join(r['fields'][k][:2])
        if k == 'hex8':
            res = sorted({v for v in r['hex8Resolved'].values()})
            names += ' → ' + '／'.join(res)
        parts.append('%s（%s）' % (k, names))
    detail = '；'.join(parts)
    print('   %-42s %s' % (r['artefact'][:42], detail[:48]))
print('   ' + '-' * 92)
print()

print('三、🚨 併接風險：兩份產物用不同切法時，交集會是空的')
for k in sorted(by_slicing):
    print('   %-8s %d 份：%s' % (k, len(by_slicing[k]),
                                 '、'.join(n[:22] for n in by_slicing[k][:5])
                                 + ('…' if len(by_slicing[k]) > 5 else '')))
mixed = [r for r in rows if len(r['slicings']) > 1]
print()
print('   🚨 單一產物內即混用兩種以上者 %d 份：%s'
      % (len(mixed), '、'.join(r['artefact'][:24] for r in mixed[:6])))
print('   ⚠️ 混用本身不必然是錯——🚨 但併接時必須先問「這一欄是哪一種」。')
h8 = sorted({r['artefact'] for r in rows
             if 'head8' in (r.get('hex8Resolved') or {}).values()})
l8 = sorted({r['artefact'] for r in rows
             if 'last8' in (r.get('hex8Resolved') or {}).values()})
print()
print('   🚨 而 8 碼那一類實測分成兩群，彼此併接交集為空：')
print('      head8（目錄名前 8）%d 份：%s'
      % (len(h8), '、'.join(n[:24] for n in h8[:5])))
print('      last8（id 後 8）  %d 份：%s'
      % (len(l8), '、'.join(n[:24] for n in l8[:5])))
print('      ⚠️ 兩群都會被標成「8 碼」——🚨 光看標籤仍會撞上同一個坑。')
print()
print('四、⚠️ 這張表擋得住什麼')
print('   ✅ 擋得住：**寫併接之前**沒看出兩邊切法不同。')
print('   🚨 擋不住：已經寫好的併接——⚠️ 本檔不掃程式碼，只看產物。')
print('   🚨 兩次事故（第 522、524 輪）都是併接寫完才發現，'
      '⚠️ 而兩次都靠控制探針攔下，🚫 不是靠這張表。')

doc = {
    'schemaVersion': 1,
    'documentType': 'id-slicing-inventory',
    'ruling': 'twice in three rounds a join across artefacts produced an empty '
              'intersection because the two sides slice the same id differently, '
              'and an empty intersection looks like the other side having nothing',
    'population': 'artefacts numbered n400-n599 plus the handoff file',
    'countingUnit': 'artefact',
    'criterion': 'string fields matching one of four id shapes: full id, 24-hex '
                 'directory prefix, first-16 fragment, and 8-hex -- the last of '
                 'which is resolved against real ids into head8 or last8, because '
                 'shape alone cannot tell them apart',
    'controlProbes': {'positives': [{'value': v[:40], 'expected': w,
                                     'got': slicing(v)} for v, w in good],
                      'negatives': [{'value': v[:40], 'got': slicing(v)}
                                    for v in bad]},
    'artefacts': rows,
    'bySlicing': {k: v for k, v in by_slicing.items()},
    'mixedWithinOneArtefact': [r['artefact'] for r in mixed],
    'hex8Head8': h8, 'hex8Last8': l8,
    'hex8Note': 'Eight hex characters can be the head of the directory name or '
                'the tail of the id, and the two do not intersect. Both are '
                'labelled 8-hex by shape, so the label alone still walks into the '
                'same hole; they are resolved here against real ids.',
    'whatItCatches': 'A mismatch visible before a join is written.',
    'whatItDoesNot': 'Joins already written -- this reads artefacts, not code. '
                     'Both incidents were found after the join existed, and by '
                     'control probes rather than by this table.',
    'coverageStatement': 'Two levels of nesting and the first 400 items of a '
                         'list; deeper or longer structures are not inspected. '
                         'Mixing conventions inside one artefact is reported, not '
                         'judged.',
    'contentNote': 'Artefact and field names, id shapes and counts only.',
}
doc['inventoryHash'] = content_hash({r['artefact']: r['slicings'] for r in rows})
io.open('.scratch/n525_id_key_conventions.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → .scratch/n525_id_key_conventions.json')
