# -*- coding: utf-8 -*-
"""行尾轉換演習：**真的轉一次，看哪一道檢查會響、哪一道不會。**

## 🚨 為什麼「曝險 39／41」還不夠

第 514 輪量出：一次 CRLF 轉換會讓 **39／41** 之來源指紋失配。
**⚠️ 但「指紋會變」與「有沒有人會發現」是兩件事。**

> **🚨 一個會被抓到的損壞，和一個不會被抓到的損壞，嚴重性差一個數量級。**
> ⚠️ 前者是麻煩，**後者是一份看起來完好的證據。**

**✅ 故本檔不再推論，直接演習**：把 artifact 目錄複製到暫存區、
**在複本上**做行尾轉換，然後把既有檢查逐一跑過去，**看誰響。**

**🚫 全程不動私有根一個位元組**——⚠️ 演習在複本上做，做完刪掉。

## 🚨 演習推翻了我的預測，而那正是演習存在的理由

**⚠️ 我原本預測 TEI 路徑會靜默通過。🚫 全轉的情形下不會**——
**🚨 因為 sections 檔本身也是文字檔，它一被轉換，`sectionsSha256` 就失配，生產端立刻響。**
**⚠️ 我漏掉的是「被轉換的不只有來源檔」。**

> **🚨 若我只用推論寫報告，就會寫下一句錯的話。**

**✅ 但把條件收緊成「只轉來源檔」之後，那個不對稱就出現了**——見第二之二節。
**⚠️ 故正確的說法不是「安全」，是「只有在所有檔一起被轉換時才安全」。**

## 🚨 原本的預期不對稱（下表為推論，實測見第二節）

| 路徑 | manifest 側 | sections 側 | 轉換後 |
|---|---|---|---|
| **JATS** | `sourceSha256` ＝ **同一份 JATS 之裸位元組** | 裸位元組 | **✅ 會響**——⚠️ 兩側都變，`_verify_committed_artifacts` 抓得到 |
| **TEI** | `sourceSha256` ＝ **PDF**（二進位，免疫）；`teiSha256` ＝ **LF 正規化**（免疫） | **裸位元組** | **🚨 不會響**——⚠️ 生產端檢查全過，而 sections 側之來源指紋已失效 |

**🚨 若屬實，TEI 那 15 份就是「靜靜地壞掉」的那一類**，
**⚠️ 而唯一看得到它的是本室之 `n498`（不變式 6），🚫 那不是生產端的護欄。**

## 🚨 控制探針：**先在未轉換的複本上跑一次**

**⚠️ 若複製過程本身就弄壞了什麼，「轉換後失敗」會被誤讀成轉換造成的。**
**✅ 故同一組檢查先跑未轉換之複本，🚨 必須全過；不全過即中止。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 演得到：既有檢查在一次行尾轉換後各自的反應。
- ✅ 兩種情形都演了：**全轉**與**只轉來源檔**——🚨 而不對稱只在後者出現。
- 🚨 演不到：**更零碎的部分轉換**（例如只轉了某幾份而非某類檔）——
  ⚠️ 本檔演的是兩個端點，**🚫 中間還有很多種組合。**
- ⚠️ 只取樣**每條路徑各一份**：🚫 這不是普查，
  **🚨 但兩條路徑之差異是結構性的（欄位定義不同），不是逐份不同。**
"""
import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.search import fulltext as F  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
FULL = PRIVATE_ROOT / 'fulltext'
AD = re.compile(r'-[0-9a-f]{16}$')
TEXT_SUFFIX = ('.jats.xml', '.tei.xml', '.json')
LF, CRLF = b'\n', b'\r\n'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def to_crlf(raw):
    return raw.replace(CRLF, LF).replace(LF, CRLF)


def production_check(d, man):
    """生產端之檢查：🚨 這就是發佈路徑上真正跑的那一支。"""
    try:
        F._verify_committed_artifacts(d, man)
        return 'pass', ''
    except Exception as e:
        return 'fail', '%s: %s' % (type(e).__name__, str(e)[:90])


def sections_source_check(d, man):
    """本室 `n498` 之不變式 6：sections 側之來源指紋是否仍對得上來源檔。

    ⚠️ 生產端不驗這一項——🚨 那正是本演習要顯示的缺口。
    """
    bad = []
    for a in (man.get('artifacts') or []):
        st = a.get('sourceType')
        name = a.get('teiFile') if st == 'grobid-tei' else a.get('rawFile')
        sp = d / (a.get('sectionsFile') or '')
        src = d / (name or '')
        if not sp.exists() or not src.exists():
            bad.append('缺檔')
            continue
        sec = jload(sp)
        if sec.get('sourceSha256') != F._sha256(src.read_bytes()):
            bad.append('sections.sourceSha256 與來源檔不符')
    return ('fail' if bad else 'pass'), '；'.join(bad)


def drill(src_dir, convert, only_source=False):
    """把目錄複製到暫存區（可選轉換行尾），回傳兩道檢查之結果。

    ⚠️ `only_source`：**只轉來源檔，🚫 不動 sections 檔**——
    🚨 這一模擬的是「搬運只翻譯了一部分檔案」，而那才是靜默損壞的條件。
    """
    tmp = Path(tempfile.mkdtemp(prefix='n515-'))
    try:
        dst = tmp / src_dir.name
        shutil.copytree(src_dir, dst)
        changed = []
        if convert:
            for p in dst.iterdir():
                if only_source and p.name.startswith('sections-'):
                    continue      # 🚨 刻意不動 sections——見 docstring
                if p.is_file() and any(p.name.endswith(s) for s in TEXT_SUFFIX):
                    raw = p.read_bytes()
                    new = to_crlf(raw)
                    if new != raw:
                        p.write_bytes(new)
                        changed.append(p.name.split('-')[0])
        man = jload(dst / 'manifest.json')
        return {'converted': convert, 'filesChanged': sorted(set(changed)),
                'production': production_check(dst, man),
                'sectionsSource': sections_source_check(dst, man)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 取樣：每條路徑各一份 ─────────────────────────────────────────
picks = {}
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') != 'acquired':
        continue
    for a in (m.get('artifacts') or []):
        st = a.get('sourceType')
        if st not in picks:
            picks[st] = d
if not picks:
    sys.exit('🚨 找不到任何 acquired——🚫 中止。')

print('=== 行尾轉換演習（🚫 只動複本，私有根一個位元組都不碰）===')
print('   取樣：每條路徑各一份 → %s'
      % '、'.join('%s=%s' % (k, v.name[:8]) for k, v in sorted(picks.items())))
print()

print('一、控制探針——🚨 未轉換之複本必須全過')
ctl_ok = True
for st, d in sorted(picks.items()):
    r = drill(d, convert=False)
    good = r['production'][0] == 'pass' and r['sectionsSource'][0] == 'pass'
    ctl_ok = ctl_ok and good
    print('   %s %-18s 生產端=%s｜sections 來源=%s'
          % ('✅' if good else '🚨', st, r['production'][0],
             r['sectionsSource'][0]))
if not ctl_ok:
    sys.exit('🚨 未轉換之複本就不通過——⚠️ 複製本身有問題，'
             '🚫 轉換後的結果不予採信，中止。')
print('   ✅ 複製過程乾淨，故下面的失敗只能來自轉換。')
print()

print('二、轉換之後，誰響')
print('   %-18s %-26s %-14s %s' % ('路徑', '被改動之檔', '生產端檢查', 'sections 來源'))
print('   ' + '-' * 84)
rows = []
for st, d in sorted(picks.items()):
    r = drill(d, convert=True)
    rows.append({'route': st, 'dir': d.name[:8], **r})
    print('   %-18s %-26s %-14s %s'
          % (st, '／'.join(r['filesChanged'])[:26] or '（無）',
             ('🚨 響了' if r['production'][0] == 'fail' else '⚠️ 沒響'),
             ('🚨 響了' if r['sectionsSource'][0] == 'fail' else '⚠️ 沒響')))
print('   ' + '-' * 84)

# ── 🚨 第二種情形：只轉來源檔（模擬部分轉換） ──────────────────
print()
print('二之二、🚨 只轉來源檔（sections 檔不動）——模擬「搬運只翻譯了一部分」')
print('   %-18s %-26s %-14s %s'
      % ('路徑', '被改動之檔', '生產端檢查', 'sections 來源'))
print('   ' + '-' * 84)
partial = []
for st, d in sorted(picks.items()):
    r = drill(d, convert=True, only_source=True)
    partial.append({'route': st, 'dir': d.name[:8], 'mode': 'source-only', **r})
    print('   %-18s %-26s %-14s %s'
          % (st, '／'.join(r['filesChanged'])[:26] or '（無）',
             ('🚨 響了' if r['production'][0] == 'fail' else '⚠️ 沒響'),
             ('🚨 響了' if r['sectionsSource'][0] == 'fail' else '⚠️ 沒響')))
print('   ' + '-' * 84)
rows += partial

silent = [r for r in rows
          if r['production'][0] == 'pass' and r['sectionsSource'][0] == 'fail']
print()
print('三、🚨 結論')
if silent:
    for r in silent:
        print('   🚨 `%s`（%s）：**生產端檢查全過，而 sections 側之來源指紋已失效。**'
              % (r['route'], r.get('mode', 'all-text')))
    print('   ⚠️ 即：那條路徑上的損壞**不會被生產端發現**——')
    print('      🚨 唯一看得到它的是本室之 `n498`（不變式 6），'
          '🚫 而那不是生產端的護欄。')
else:
    print('   ✅ 兩條路徑之損壞皆為生產端所捕獲。')
loud = [r for r in rows if r['production'][0] == 'fail']
for r in loud:
    print('   ✅ `%s`：生產端立刻失敗——%s'
          % (r['route'], r['production'][1][:70]))

doc = {
    'schemaVersion': 1,
    'documentType': 'line-ending-conversion-drill',
    'ruling': 'follows n+169(1)(4) and round 514: measuring that 39 of 41 '
              'fingerprints would change says nothing about whether anyone would '
              'notice, and a corruption nobody notices is the worse kind',
    'population': 'one acquired artifact per acquisition route',
    'countingUnit': 'route',
    'criterion': 'copy the directory, convert text sources to CRLF in the copy, '
                 'then run the production verifier and the sections-source '
                 'invariant and record which one fails',
    'doesNotTouchPrivateRoot': True,
    'controlProbe': 'The same checks run first on an unconverted copy and must '
                    'all pass; otherwise a failure after conversion could be an '
                    'artefact of copying rather than of the conversion.',
    'predictionWasWrong': 'Predicted the TEI route would pass silently. Under a '
                          'whole-directory conversion it does not: the sections '
                          'file is itself text, so converting it breaks '
                          'sectionsSha256 and the production verifier fires. The '
                          'asymmetry appears only when the conversion touches the '
                          'source file and not the sections file -- so the right '
                          'statement is not "safe" but "safe only if everything '
                          'moves together".',
    'results': rows,
    'silentlyBroken': [r['route'] for r in silent],
    'loudlyBroken': [r['route'] for r in loud],
    'whyAsymmetric': 'On the JATS route the manifest records a raw-byte hash of '
                     'the same file the sections document hashes, so both move '
                     'together and the production verifier catches it. On the TEI '
                     'route the manifest hashes the PDF (binary) and the '
                     'LF-normalised TEI, both immune, while the sections document '
                     'hashes the TEI raw -- so the production verifier passes '
                     'while that fingerprint is already stale.',
    'coverageStatement': 'One record per route, because the difference is '
                         'structural -- it follows from which field hashes which '
                         'file -- not per record. The drill converts every text '
                         'file; a real transfer might convert only some, so this '
                         'is the simplest case rather than the worst.',
    'contentNote': 'Route names, file-name prefixes and verdicts only.',
}
doc['drillHash'] = content_hash({'silent': [r['route'] for r in silent],
                                 'loud': [r['route'] for r in loud]})
io.open(S + 'n515_conversion_drill.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn515_conversion_drill.json' % S)
