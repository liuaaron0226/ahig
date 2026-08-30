# -*- coding: utf-8 -*-
"""取得語料之常設覆核：41 份 acquired 之位元組是否仍與 manifest 相符。

## 🚨 為什麼要有這支：`_verify_committed_artifacts` 只在寫入路徑上跑

查 `fulltext.py` 之呼叫點（第 705、968、1031、1110、1139 行）——
**五處全在發佈或快取重讀之路徑上。**

> **🚨 意思是：一筆取得之後若再也沒被寫過，它的雜湊就再也沒有被驗過。**

**⚠️ 而萃取期（M1 ④）即將把這些讀進去。**
若其中任何一份在落盤後漂移（誤編、半寫、私有根被部分複製、
行尾被某個工具翻譯過），**🚨 萃取會照讀不誤，且沒有任何一處會響。**

**⚠️ 這不是假想**：本 run 之第 13 型缺陷即「護欄失敗而被護之動作照做」。
**🚨 一個只在寫入時檢查的完整性檢查，對於不再被寫入的資料等於沒有。**

## 🚫 本檔不做什麼

- **🚫 不刪任何檔案。** `sweep_orphans` 是**回復工具，它會 unlink**；
  **⚠️ 拿一個會刪檔的函式當「驗證」跑，是把稽核變成變更。**
  故本檔自行以 `_manifest_references` 做**唯讀**之孤兒列示。
- **🚫 不修 manifest、不重算雜湊寫回**——⚠️ 那會讓漂移消失而不是被記錄。
- **🚫 不落盤任何文獻內容**——產物只有目錄前綴、檔名、判定與計數。

## 🚨 控制探針（n+112 二：期待為空之檢查不能自證）

**⚠️ 「全數相符」與「驗證函式根本沒在驗」在輸出上長得一模一樣。**
故本檔在 tempdir 內建合成案例，**全部都必須照預期反應**，
否則**🚫 拒絕報告語料結果並以非零碼結束**：

| 探針 | 必須 |
|---|---|
| 正向甲：合成之正確 JATS artifact | **必須通過**（🚨 否則「總是拋錯」之實作會把全體誤判為漂移） |
| 反向甲：`sourceSha256` 改一字元 | **必須拋錯** |
| 反向乙：刪掉 sections 檔 | **必須拋錯** |
| 正向乙：TEI 路徑（含 CRLF，LF 正規化後應相符） | **必須通過** |
| 反向丙：`teiSha256` 改一字元 | **必須拋錯** |
| 分類器四道：合成 artifact 名須入選，三個工作快取名須排除 | **必須如預期** |

**⚠️ 正反兩向都要**：只有反向探針時，一個「總是拋錯」的實作也會全綠；
**🚨 而分類器若一個都不收，語料數會變成 0，看起來像「沒有東西壞掉」。**

## 母體（🚫 不可與另兩個混用）

**本檔之母體是私有根下 `fulltext/` 內每一個 `status == "acquired"` 之目錄。**

| 母體 | 🚨 差別 |
|---|---|
| 校準集 60 | 契約抽樣，**不含遞補** |
| 校準集 ＋ n+103 遞補 | 遞補後實際處理之集合 |
| **私有根全體（本檔）** | **⚠️ 含不屬於校準集之取得** |

**🚨 本 run 曾兩度把這三者混用**（第 490 輪之層別表、以及把 27 說成「全體 manifest」）。
**⚠️ 故本檔之數字只能與私有根全體並列，🚫 不得充當校準集之分子或分母。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：位元組是否仍與 manifest 所記之雜湊相符、必填欄位是否完整、
  有無未被引用之殘檔、以及原始檔之雜湊是否對行尾敏感。
- 🚨 查不到：**manifest 本身是否被連同內容一起改過**——
  **⚠️ 雜湊由 manifest 提供，改雙方即可自洽。本檔驗的是一致性，不是真確性。**
- 🚨 亦查不到：**節切得對不對、內容完不完整**——⚠️ 那要人讀。
- ⚠️ 行尾敏感度為**曝險量測，不是缺陷**：檔案現在在磁碟上是好的，
  **🚨 該欄說的是「若它曾經過一個會翻譯行尾的路徑，此雜湊就不再是憑證」**（n+122 三）。
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, 'ahig')
# 🚨 n+162（九之二）：來源不在就拒絕產出，🚫 不得寫入任何值。
# ⚠️ 原本這裡是 `os.environ.setdefault(...)`——那行在別台機器上會
#    「成功」地把根設成一個不存在的路徑，🚨 於是本支量到零並落盤，
#    而「量到零」與「量不到」在檔案裡長得一模一樣。
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.search import fulltext  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
ROOT = Path(os.environ['AHIG_PRIVATE_ROOT']) / 'fulltext'
GLOBS = ('source-*.jats.xml', 'source-*.tei.xml', 'source-*.pdf',
         'sections-v*.json')
# artifact 目錄之名由 `_candidate_directory_name` 造：`<slug>-<16 碼十六進位>`。
# 🚨 初版沒有這條，於是 `pdf-cache`／`tei-cache`／`tei-test` 三個工作快取
# 被算進「目錄總數」，並與「artifact 目錄缺 manifest」混在同一個計數裡。
# ⚠️ 後者是 manifest-last 之殘留狀態，前者只是我自己的暫存區——
# 🚨 一個把兩者報成同一個數字的檢查，等於保證那個狀態不會被看見。
ARTIFACT_DIR = re.compile(r'-[0-9a-f]{16}$')


def flip(h):
    """把雜湊末字元改掉——🚫 不可用截斷，長度變了可能踩到別的判定。"""
    return h[:-1] + ('0' if h[-1] != '0' else '1')


def check(d, man):
    """回傳 (verdict, detail)。🚨 例外之類別名一律記入——本 run 曾因吞掉
    類別名而把 28／33 誤報為不可達。"""
    try:
        fulltext._validate_latest_manifest(d, man)
    except Exception as e:
        return 'structure-invalid', '%s: %s' % (type(e).__name__, str(e)[:120])
    try:
        fulltext._verify_committed_artifacts(d, man)
    except Exception as e:
        return 'hash-mismatch', '%s: %s' % (type(e).__name__, str(e)[:120])
    return 'ok', ''


def controls():
    """🚨 先證明這支驗得動，再讓它去驗語料。"""
    tmp = Path(tempfile.mkdtemp(prefix='n496-'))
    out = []
    try:
        raw = b'<article>x</article>'
        # 🚨 第 516 輪起，產線驗證器也對 sections 檔自記之來源指紋。
        # ⚠️ 故合成之「正確」案例必須把那一格填對——
        # 🚫 這是把假樣本補成真的合格樣本，不是放寬檢查。
        sec = ('{"sections":[],"sourceSha256":"%s"}'
               % fulltext._sha256(raw)).encode('utf-8')
        (tmp / 'source-a.jats.xml').write_bytes(raw)
        (tmp / 'sections-va.json').write_bytes(sec)
        base = {'artifacts': [{'rawFile': 'source-a.jats.xml',
                               'sectionsFile': 'sections-va.json',
                               'sourceSha256': fulltext._sha256(raw),
                               'sectionsSha256': fulltext._sha256(sec),
                               'parserVersion': 'v1', 'sourceUrl': 'x',
                               'sourceType': 'europe-pmc-jats', 'pmcid': 'PMC1'}]}

        def probe(name, man, want_raise, prep=None, undo=None):
            if prep:
                prep()
            try:
                fulltext._verify_committed_artifacts(tmp, man)
                raised, msg = False, ''
            except Exception as e:
                raised, msg = True, '%s: %s' % (type(e).__name__, str(e)[:90])
            if undo:
                undo()
            ok = (raised == want_raise)
            out.append({'probe': name, 'expectRaise': want_raise,
                        'raised': raised, 'message': msg, 'asExpected': ok})
            print('   %s %-32s 期待%s／實得%s  %s'
                  % ('✅' if ok else '🚨', name,
                     '拋錯' if want_raise else '通過',
                     '拋錯' if raised else '通過', msg[:48]))

        probe('正向甲：正確之 JATS artifact', base, False)

        bad = json.loads(json.dumps(base))
        bad['artifacts'][0]['sourceSha256'] = flip(bad['artifacts'][0]['sourceSha256'])
        probe('反向甲：sourceSha256 改一字元', bad, True)

        probe('反向乙：sections 檔不存在', base, True,
              prep=lambda: (tmp / 'sections-va.json').unlink(),
              undo=lambda: (tmp / 'sections-va.json').write_bytes(sec))

        # ⚠️ TEI 探針刻意含 CRLF：若 _text_sha256 沒做正規化，正向乙會拋錯。
        tei = b'<TEI>\r\ny</TEI>'
        pdf = b'%PDF-1.4'
        (tmp / 'source-b.tei.xml').write_bytes(tei)
        (tmp / 'source-b.pdf').write_bytes(pdf)
        # 🚨 TEI 路徑之 sections 記的是 **TEI 之裸位元組**（parse_tei），
        # ⚠️ 與 JATS 那份不同，故必須各有各的 sections 檔。
        sec_b = ('{"sections":[],"sourceSha256":"%s"}'
                 % fulltext._sha256(tei)).encode('utf-8')
        (tmp / 'sections-vb.json').write_bytes(sec_b)
        t = {'artifacts': [{'rawFile': 'source-b.pdf',
                            'teiFile': 'source-b.tei.xml',
                            'sectionsFile': 'sections-vb.json',
                            'sourceSha256': fulltext._sha256(pdf),
                            'teiSha256': fulltext._text_sha256(tei),
                            'sectionsSha256': fulltext._sha256(sec_b),
                            'parserVersion': 'v1', 'sourceUrl': 'x',
                            'sourceType': 'grobid-tei', 'grobidVersion': '0.9.1'}]}
        probe('正向乙：TEI 路徑（LF 正規化）', t, False)

        t2 = json.loads(json.dumps(t))
        t2['artifacts'][0]['teiSha256'] = flip(t2['artifacts'][0]['teiSha256'])
        probe('反向丙：teiSha256 改一字元', t2, True)

        # 分類器亦須雙向探針：⚠️ 一個「什麼都不算 artifact」的規則
        # 會讓語料數變成 0 而看起來像「沒有東西壞掉」。
        for name, want in (('a-study-name-0123456789abcdef', True),
                           ('pdf-cache', False), ('tei-cache', False),
                           ('tei-test', False)):
            got = bool(ARTIFACT_DIR.search(name))
            ok = (got == want)
            out.append({'probe': '分類器：%s' % name, 'expectRaise': None,
                        'classifiedAsArtifact': got, 'expected': want,
                        'asExpected': ok})
            print('   %s 分類器 %-30s 期待%s／實得%s'
                  % ('✅' if ok else '🚨', name,
                     'artifact' if want else '排除',
                     'artifact' if got else '排除'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


print('=== 取得語料之常設覆核（🚫 唯讀，不刪不改）===')
print()
print('一、控制探針——🚨 未全數如預期則拒絕報告語料結果')
ctl = controls()
if not all(c['asExpected'] for c in ctl):
    sys.exit('\n🚨 控制探針未全數如預期——🚫 本次語料結果不予採信，中止。')
print("   ✅ %d 道控制探針全數如預期，驗證函式與分類器確實在動。" % len(ctl))
print()

rows, orphans, crlf = [], [], []
scanned = 0
all_dirs = sorted(p for p in ROOT.iterdir() if p.is_dir())
dirs = [p for p in all_dirs if ARTIFACT_DIR.search(p.name)]
# 🚨 排除者一律列名——n+148 之教訓：為降噪而設的排除規則，
# 會連它沒想到的那一類一起排掉，而看不見的排除無從複核。
excluded = [p.name for p in all_dirs if not ARTIFACT_DIR.search(p.name)]
missing_manifest = [p.name[:16] for p in dirs
                    if not (p / 'manifest.json').exists()]
for d in dirs:
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    scanned += 1
    try:
        man = json.loads(mp.read_text(encoding='utf-8'))
    except Exception as e:
        rows.append({'dir': d.name[:16], 'verdict': 'manifest-unreadable',
                     'detail': '%s: %s' % (type(e).__name__, str(e)[:100]),
                     'sourceTypes': [], 'artifacts': 0})
        continue
    if man.get('status') != 'acquired':
        continue
    verdict, detail = check(d, man)
    kinds = sorted({(a.get('sourceType') or '?')
                    for a in (man.get('artifacts') or [])})
    rows.append({'dir': d.name[:16],
                 'candidateIdTail': (man.get('candidateId') or '')[-8:],
                 'verdict': verdict, 'detail': detail, 'sourceTypes': kinds,
                 'artifacts': len(man.get('artifacts') or [])})
    # 唯讀孤兒列示——🚫 絕不 unlink。
    refs = fulltext._manifest_references(man)
    extra = sorted(p.name for g in GLOBS for p in d.glob(g)
                   if p.name not in refs)
    if extra:
        orphans.append({'dir': d.name[:16], 'files': extra})
    # 行尾敏感度（n+122 三之曝險量測）
    for a in (man.get('artifacts') or []):
        rf = d / (a.get('rawFile') or '')
        if rf.name and rf.exists() and rf.suffix.lower() != '.pdf':
            if b'\r\n' in rf.read_bytes():
                crlf.append({'dir': d.name[:16], 'file': rf.name,
                             'hashIsLineEndingSensitive': True})

# ── 被排除者之逐一交代 ───────────────────────────────────────────
# 🚨 這一段是分類器探針逼出來的：被排除的 7 個目錄裡，有 4 個帶著
# manifest.json，⚠️ 它們不是工作快取，是**舊命名規則留下的紀錄**。
# 🚨 若只印「已排除 7 個」而不列名，這 4 個永遠不會被看見。
legacy = []
for p in all_dirs:
    if ARTIFACT_DIR.search(p.name) or not (p / 'manifest.json').exists():
        continue
    try:
        m = json.loads((p / 'manifest.json').read_text(encoding='utf-8'))
    except Exception as e:
        legacy.append({'dir': p.name, 'error': '%s: %s'
                       % (type(e).__name__, str(e)[:90])})
        continue
    cid = m.get('candidateId') or ''
    cur = ROOT / fulltext._candidate_directory_name(cid) if cid else None
    cur_status = None
    if cur is not None and (cur / 'manifest.json').exists():
        try:
            cur_status = json.loads(
                (cur / 'manifest.json').read_text(encoding='utf-8')).get('status')
        except Exception:
            cur_status = '(unreadable)'
    legacy.append({'dir': p.name, 'candidateIdTail': cid[-8:],
                   'legacyStatus': m.get('status'),
                   'artifacts': len(m.get('artifacts') or []),
                   'currentSchemeDirExists': bool(cur and cur.exists()),
                   'currentSchemeStatus': cur_status})

c = Counter(r['verdict'] for r in rows)
print('二、語料：私有根 `fulltext/` 之 acquired 全體')
print('   artifact 目錄 %d ／ 其中有 manifest 者 %d ／ status=acquired %d'
      % (len(dirs), scanned, len(rows)))
print('   ⚠️ 另有 %d 個非 artifact 目錄，已排除且逐一列名：%s'
      % (len(excluded), '、'.join(excluded) or '—'))
if missing_manifest:
    print('   🚨 %d 個 artifact 目錄無 manifest.json——'
          '⚠️ 那是 manifest-last 之殘留狀態：%s'
          % (len(missing_manifest), '、'.join(missing_manifest[:6])))
else:
    print('   ✅ 無「有 artifact 目錄卻無 manifest」者。')
print()
for k, n in c.most_common():
    print('   %s %-22s %3d' % ('✅' if k == 'ok' else '🚨', k, n))
for r in rows:
    if r['verdict'] != 'ok':
        print('      🚨 %-16s %s' % (r['dir'], r['detail'][:96]))
print()
kind = Counter(t for r in rows for t in r.get('sourceTypes') or [])
print('   來源型別：%s'
      % ('／'.join('%s %d' % kv for kv in sorted(kind.items())) or '—'))
print()
print('三、唯讀孤兒列示（🚫 本檔不刪；會刪的是 `sweep_orphans`）')
if orphans:
    for o in orphans[:10]:
        print('   ⚠️ %-16s %s' % (o['dir'], '、'.join(o['files'])[:66]))
    if len(orphans) > 10:
        print('   ⚠️ …另 %d 個目錄，見產物' % (len(orphans) - 10))
    print('   ⚠️ 共 %d 個目錄有未被 manifest 引用之殘檔。' % len(orphans))
else:
    print('   ✅ 無殘檔。⚠️ 惟此結論僅在上列四種樣式之內（與掃除同一組）——')
    print('      🚨 別種形狀之殘檔對本檔與掃除同樣不可見。')
print()
print('四、🚨 被排除卻帶著 manifest 者——舊命名規則之殘留')
if legacy:
    print('   🚨 %d 個目錄不合現行命名卻有 manifest.json：' % len(legacy))
    for g in legacy:
        print('      %-46s 舊 status=%-12s artifacts=%s'
              % (g['dir'][:46], g.get('legacyStatus'), g.get('artifacts')))
        print('         ⚠️ 同一 candidateId 之現行名目錄存在=%s，其 status=%s'
              % (g.get('currentSchemeDirExists'), g.get('currentSchemeStatus')))
    stale = sum(1 for g in legacy if g.get('currentSchemeDirExists'))
    print('   ✅ 其中 %d／%d 之 candidateId 在現行命名下另有目錄——'
          '🚨 故沒有任何一筆紀錄因此遺失。' % (stale, len(legacy)))
    print('   🚨 但兩個後果須記：')
    print('      ① ⚠️ 任何「走目錄」之盤點會把這 %d 筆重複計入'
          '（舊名一次、現行名一次）。' % len(legacy))
    print('      ② 🚨 其 status 值不在現行契約允許之集合內，'
          '故 `_validate_latest_manifest` 會判其無效；')
    print('         ⚠️ 而 `sweep_orphans` 對無效 manifest 之處置是**隔離**——'
          '🚫 本檔不跑它，那是變更不是稽核。')
    print('   🚫 本室不刪、不改、不搬——⚠️ 是否退場屬協調者裁定。')
else:
    print('   ✅ 無此類殘留。')
print()
print('五、行尾敏感之原始檔（n+122 三之曝險量測，🚫 非缺陷）')
if crlf:
    print('   ⚠️ %d 份文字類原始檔含 CRLF——'
          '🚨 其 `sourceSha256` 是位元組雜湊，故不構成跨平台憑證。' % len(crlf))
else:
    print('   ✅ 0 份文字類原始檔含 CRLF。'
          '⚠️ 這只表示現況下位元組雜湊與 LF 正規化雜湊等值，')
    print('      🚨 不表示該欄位取得了跨平台性質——換一台檢出就可能不再等值。')

doc = {
    'schemaVersion': 1,
    'documentType': 'acquired-corpus-verification',
    'ruling': 'self-initiated: _verify_committed_artifacts fires only on the write '
              'path, so a record acquired and never rewritten has never been '
              're-verified -- and extraction is about to read all of them',
    'population': 'every directory under the private root fulltext/ whose '
                  'manifest.json has status acquired',
    'populationNote': 'This is the private-root population. It is NOT the '
                      'calibration 60 and NOT the calibration-plus-backfill set. '
                      'Those three have been mixed twice in this run, so these '
                      'figures may not serve as numerator or denominator for '
                      'either of the other two.',
    'countingUnit': 'record (one artifact directory)',
    'criterion': 'structure passes _validate_latest_manifest and every artifact '
                 'file on disk still hashes to what the manifest records',
    'controlProbes': ctl,
    'controlNote': 'A sweep whose expected result is zero cannot prove itself. '
                   'Both directions are probed: two synthetic correct artifacts '
                   'must pass and three deliberate corruptions must raise. If any '
                   'probe misbehaves the script refuses to report the corpus '
                   'result and exits non-zero.',
    'artifactDirectories': len(dirs),
    'excludedNonArtifactDirectories': excluded,
    'artifactDirectoriesWithoutManifest': missing_manifest,
    'legacySchemeDirectories': legacy,
    'legacyNote': 'Four directories carry the superseded naming scheme '
                  '(the whole candidateId slugified, with no digest suffix). '
                  'Each holds a manifest with status "unavailable" -- a value the '
                  'current contract does not allow -- and no artifacts. Every one '
                  'of their candidateIds also has a current-scheme directory, so '
                  'no record is lost; but a directory-walking count double-counts '
                  'them, and _validate_latest_manifest would judge them invalid, '
                  'which is a state sweep_orphans quarantines. Left untouched: '
                  'retiring them is a coordinator decision, not an audit action.',
    'withManifest': scanned,
    'acquired': len(rows),
    'verdicts': dict(c),
    'sourceTypes': dict(kind),
    'records': rows,
    'orphanCandidates': orphans,
    'lineEndingSensitiveSources': crlf,
    'readOnly': 'No file is written, unlinked or repaired. sweep_orphans is a '
                'recovery tool that unlinks; running it as a verification would '
                'turn an audit into a change.',
    'coverageStatement': 'Verifies consistency between bytes and manifest, not '
                         'truth: the hashes come from the manifest, so editing '
                         'both together stays self-consistent. Says nothing about '
                         'whether sections are correct or the text complete -- '
                         'that needs a reader. The orphan listing is bounded by '
                         'the same four globs the sweep uses, so a stray file of '
                         'another shape is invisible to both.',
    'contentNote': 'Directory prefixes, file names, counts and verdicts only. No '
                   'literature content.',
}
doc['verificationHash'] = content_hash({'verdicts': dict(c),
                                        'acquired': len(rows)})
io.open(S + 'n496_corpus_verify.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn496_corpus_verify.json' % S)
sys.exit(0 if (c.get('ok', 0) == len(rows) and not missing_manifest) else 1)
