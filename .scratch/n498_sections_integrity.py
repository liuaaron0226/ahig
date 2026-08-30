# -*- coding: utf-8 -*-
"""節切之內部一致性：偏移是否真的指到它自己宣稱的那段文字。

## 🚨 為什麼這是取得端的事，而不是萃取端的事

萃取要用的不是 `content` 整份，**⚠️ 是「第 N 節的字」**——
而「第 N 節的字」有兩個來源：**`sections[i]['text']`，或 `content[start:end]`。**

> **🚨 兩者若不相等，兩種寫法會拿到不同的字，而且都不會報錯。**

**⚠️ 這件事至今從未被整體驗過**：

| 既有檢查 | 涵蓋 | 🚨 沒涵蓋 |
|---|---|---|
| `_verify_committed_artifacts` | 檔案位元組 vs manifest 雜湊 | **🚫 完全不看 sections 內部** |
| `n459` 之 GROBID 驗收 | **只有 TEI 那 15 份**，且只驗**單調性** | 🚫 26 份 JATS 從未驗過；🚫 未驗「切片等於 text」 |
| `n496` | artifact 檔案是否漂移 | 🚫 檔案內部之自洽 |

**🚨 故本檔補的是那個空格：41 份全體、兩條路徑、逐節比對。**

## 契約（讀 `_with_offsets` 得來，🚫 不是猜的）

`fulltext.py` 第 181 行起，`content` 是各節之 `text` 以 `"\\n\\n"` 串接而成。
**⚠️ 因此不變式是嚴格的，不是「大致對齊」**：

| # | 不變式 |
|---|---|
| 1 | `content[startOffset:endOffset] == text`（**🚨 逐字相等**） |
| 2 | `sections[0]['startOffset'] == 0` |
| 3 | `sections[i]['startOffset'] == sections[i-1]['endOffset'] + 2`（**⚠️ 間隔恰為 2**） |
| 4 | `sections[-1]['endOffset'] == len(content)` |
| 5 | `contentSha256 == sha256(content.encode('utf-8'))`（第 302／370 行） |
| 6 | sections 檔之 `sourceSha256` 對得上**它自己那條路徑的來源檔**（🚨 見下） |

**🚨 第 3 條刻意寫死 2**：⚠️ 若只驗「不重疊」，一個把分隔符改掉的變更會靜靜通過，
**而偏移仍然指得到字——只是指到的字少一個或多一個字元。**

### 🚨 第 6 條之「來源」在兩條路徑上不是同一個檔（⚠️ 初版就栽在這裡）

**⚠️ 初版直接拿 `sections.sourceSha256` 去比 `manifest.sourceSha256`，
於是 15 份 TEI 全數報「不符」——🚨 而那 15 份其實一份都沒壞。**

| 路徑 | `sections.sourceSha256` 是誰的雜湊 | `manifest.sourceSha256` 是誰的 |
|---|---|---|
| JATS | **JATS 位元組**（`parse_jats` 第 301 行） | **同一份 JATS** → ✅ 應相等 |
| TEI | **TEI 位元組**（`parse_tei` 第 369 行） | **🚨 PDF 位元組**（n+123 五） → **🚫 本來就不該相等** |

> **🚨 我沒讀就假設兩個同名欄位是同一件事。**
> **⚠️ 這正是本 run 反覆出現的那一型：把「我以為的欄位語意」當成事實。**
> **✅ 改為逐路徑比對它自己的來源檔。**

### ⚠️ 併帶查出一件休眠中的不對稱（🚫 本檔不改 `ahig/`）

**`parse_tei` 記的是 `_sha256(raw)`——位元組雜湊；
而 manifest 之 `teiSha256` 記的是 `_text_sha256`——LF 正規化後之雜湊。**

> **🚨 同一份 TEI，兩個欄位用兩種規則。**
> **⚠️ n+122（三）／n+123（五）定下正規化規則時只改了 manifest，🚫 沒改 `parse_tei`。**
> **✅ 目前兩者相等——因為 15 份 TEI 沒有一份含 CRLF；
> 🚨 故這是休眠而不是不存在：換一個會翻譯行尾的路徑，sections 那個就不再是憑證。**

**🚫 本檔不改 `ahig/`**：⚠️ 改 `parse_tei` 之雜湊規則會使既有 41 份之
`contentSha256` 以外的記錄全部需要重寫，**🚨 那是契約變更，須協調者裁定。**

## 🚫 本檔不做什麼

- **🚫 不落盤任何文獻內容。** ⚠️ 產物只有節數、字元數、判定與**節標題之統計**
  （🚨 連標題本身都不記——標題是文獻內容）。
- **🚫 不修任何檔案。** ⚠️ 發現不一致就記錄，**🚨 不重算偏移寫回**。
- **🚫 不判斷節切得對不對**——⚠️ 「這節該不該叫 Methods」是判讀，不是檢索。

## 🚨 控制探針（n+112 二）

**⚠️ 「41 份全過」與「檢查根本沒在比」在輸出上一模一樣。** 故正反兩向皆設：

| 探針 | 必須 |
|---|---|
| 正向：合成之正確 sections 文件 | **通過**（🚨 否則「總是失敗」之實作會把全體誤判為壞） |
| 反向甲：`endOffset` 少 1 | **不過**（不變式 1） |
| 反向乙：兩節間隔改為 1 | **不過**（不變式 3） |
| 反向丙：`contentSha256` 改一字元 | **不過**（不變式 5） |
| 反向丁：`text` 改一字但偏移不動 | **不過**（🚨 這一型只有不變式 1 抓得到） |
| 反向戊：`sourceSha256` 亂填 | **不過**（不變式 6） |
| 反向己：把來源檔配到另一條路徑 | **不過**（🚨 這一道就是初版那個錯的反向對照） |

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 驗得到：偏移與文字之**自洽**、串接契約、內容雜湊、**與其路徑自己那個來源檔**之雜湊一致。
- 🚨 驗不到：**節切得對不對、標題對不對、內容完不完整**——⚠️ 那要人讀。
- 🚨 亦驗不到：**`content` 是否忠實於原始 XML／TEI**——
  ⚠️ 那要重跑解析器並比對，**🚫 本檔不重跑解析器**（重跑等於用同一份實作驗它自己）。
- ⚠️ 母體是**私有根之 acquired 全體**，🚫 不是校準集 60、也不是 60＋遞補。
"""
import hashlib
import io
import json
import os
import re
import sys
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
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
ROOT = Path(os.environ['AHIG_PRIVATE_ROOT']) / 'fulltext'
ARTIFACT_DIR = re.compile(r'-[0-9a-f]{16}$')
SEP = 2  # `_with_offsets` 以 "\n\n" 串接（fulltext.py 第 186 行）


def sha(text):
    return 'sha256:' + hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha_bytes(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


PLACEHOLDER_TITLES = {'', 'untitled'}   # 🚨 第 240／346 行之預設值


def _is_untitled(section):
    """🚨 判準取自原始碼而非猜測：`parse_jats`／`parse_tei` 在找不到標題時
    填入字面 `"Untitled"`（第 240、346 行），**⚠️ 不是空字串。**"""
    return (section.get('title') or '').strip().lower() in PLACEHOLDER_TITLES


def audit(doc, expect_source=None):
    """回傳 (問題清單, 統計)。🚨 逐條對應上表六款不變式。

    ⚠️ `expect_source` 必須是**這條路徑自己的來源檔**之位元組雜湊，
    🚫 不是 manifest 的 `sourceSha256` 欄位——兩者在 TEI 路徑上不同物。
    """
    bad = []
    content = doc.get('content')
    secs = doc.get('sections')
    if not isinstance(content, str) or not isinstance(secs, list):
        return ['sections 檔缺 content 或 sections'], {}
    if sha(content) != doc.get('contentSha256'):
        bad.append('不變式 5：contentSha256 與 content 不符')
    if expect_source and doc.get('sourceSha256') != expect_source:
        bad.append('不變式 6：sections 之 sourceSha256 與其來源檔不符')
    if not secs:
        bad.append('sections 為空——🚨 契約上不算取得全文')
        return bad, {'sections': 0, 'chars': len(content)}
    if secs[0].get('startOffset') != 0:
        bad.append('不變式 2：首節不由 0 起（實為 %r）' % secs[0].get('startOffset'))
    if secs[-1].get('endOffset') != len(content):
        bad.append('不變式 4：末節終點 %r ≠ content 長度 %d'
                   % (secs[-1].get('endOffset'), len(content)))
    mismatch = gap = 0
    for i, s in enumerate(secs):
        a, b = s.get('startOffset'), s.get('endOffset')
        if not (isinstance(a, int) and isinstance(b, int)):
            bad.append('第 %d 節偏移非整數' % i)
            continue
        if content[a:b] != s.get('text'):
            mismatch += 1
        if i and a != secs[i - 1].get('endOffset', -99) + SEP:
            gap += 1
    if mismatch:
        bad.append('不變式 1：%d 節之 content[start:end] ≠ text' % mismatch)
    if gap:
        bad.append('不變式 3：%d 處相鄰節之間隔 ≠ %d' % (gap, SEP))
    stats = {'sections': len(secs), 'chars': len(content),
             # 🚨 佔位標題是字面 "Untitled"（`fulltext.py` 第 240、346 行），
             # ⚠️ 初版只看空字串，於是報出「0 個」——🚫 那是假的全綠。
             'untitled': sum(1 for s in secs if _is_untitled(s)),
             'untitledLeading': int(bool(secs) and _is_untitled(secs[0])),
             'kinds': dict(Counter(s.get('kind') or '?' for s in secs))}
    return bad, stats


def controls():
    """🚨 先證明這支比得動，再讓它去比語料。"""
    out = []
    parts = ['第一節之文字', '第二節之文字', '第三節之文字']
    content = '\n\n'.join(parts)
    secs, cur = [], 0
    for t in parts:
        secs.append({'kind': 'section', 'title': 'T', 'text': t,
                     'startOffset': cur, 'endOffset': cur + len(t)})
        cur += len(t) + SEP
    good = {'content': content, 'contentSha256': sha(content),
            'sections': secs, 'sourceSha256': 'sha256:abc'}

    def probe(name, doc, want_bad):
        bad, _ = audit(doc, expect_source='sha256:abc')
        ok = bool(bad) == want_bad
        out.append({'probe': name, 'expectFail': want_bad,
                    'failed': bool(bad), 'findings': bad, 'asExpected': ok})
        print('   %s %-34s 期待%s／實得%s  %s'
              % ('✅' if ok else '🚨', name, '不過' if want_bad else '通過',
                 '不過' if bad else '通過', '；'.join(bad)[:56]))

    probe('正向：合成之正確 sections', json.loads(json.dumps(good)), False)

    d = json.loads(json.dumps(good))
    d['sections'][1]['endOffset'] -= 1
    probe('反向甲：endOffset 少 1', d, True)

    d = json.loads(json.dumps(good))
    d['sections'][1]['startOffset'] -= 1
    d['sections'][1]['endOffset'] -= 1
    probe('反向乙：間隔改為 1', d, True)

    d = json.loads(json.dumps(good))
    h = d['contentSha256']
    d['contentSha256'] = h[:-1] + ('0' if h[-1] != '0' else '1')
    probe('反向丙：contentSha256 改一字元', d, True)

    d = json.loads(json.dumps(good))
    d['sections'][0]['text'] = 'X' + d['sections'][0]['text'][1:]
    probe('反向丁：text 改一字、偏移不動', d, True)

    d = json.loads(json.dumps(good))
    probe('反向戊：sourceSha256 與來源檔不符',
          dict(d, sourceSha256='sha256:zzz'), True)

    # 🚨 這一道是初版那個錯誤的反向對照：
    # ⚠️ 若把 TEI 路徑之期待值誤填為 PDF 之雜湊，檢查必須報不過，
    # 🚫 而不是靜靜接受一個配錯的配對。
    bad, _ = audit(json.loads(json.dumps(good)), expect_source='sha256:pdf-not-tei')
    ok = bool(bad)
    out.append({'probe': '反向己：來源檔配錯路徑', 'expectFail': True,
                'failed': ok, 'findings': bad, 'asExpected': ok})
    print('   %s %-34s 期待不過／實得%s  %s'
          % ('✅' if ok else '🚨', '反向己：來源檔配錯路徑',
             '不過' if bad else '通過', '；'.join(bad)[:52]))
    return out


print('=== 節切之內部一致性（🚫 唯讀，不修不重算）===')
print()
print('一、控制探針——🚨 未全數如預期則拒絕報告語料結果')
ctl = controls()
if not all(c['asExpected'] for c in ctl):
    sys.exit('\n🚨 控制探針未全數如預期——🚫 本次語料結果不予採信，中止。')
print('   ✅ %d 道控制探針全數如預期。' % len(ctl))
print()

rows, asymmetric = [], []
for d in sorted(p for p in ROOT.iterdir()
                if p.is_dir() and ARTIFACT_DIR.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    man = json.loads(mp.read_text(encoding='utf-8'))
    if man.get('status') != 'acquired':
        continue
    for a in (man.get('artifacts') or []):
        sp = d / (a.get('sectionsFile') or '')
        if not sp.name or not sp.exists():
            rows.append({'dir': d.name[:16], 'sourceType': a.get('sourceType'),
                         'verdict': 'sections-missing', 'findings': [],
                         'stats': {}})
            continue
        try:
            doc = json.loads(sp.read_text(encoding='utf-8'))
        except Exception as e:
            rows.append({'dir': d.name[:16], 'sourceType': a.get('sourceType'),
                         'verdict': 'sections-unreadable',
                         'findings': ['%s: %s' % (type(e).__name__, str(e)[:90])],
                         'stats': {}})
            continue
        # 🚨 逐路徑取「它自己的來源檔」，🚫 不是 manifest 的 sourceSha256 欄位。
        note = ''
        if a.get('sourceType') == 'grobid-tei':
            tp = d / (a.get('teiFile') or '')
            if not tp.name or not tp.exists():
                rows.append({'dir': d.name[:16], 'sourceType': a.get('sourceType'),
                             'verdict': 'tei-missing', 'findings': [], 'stats': {}})
                continue
            tei = tp.read_bytes()
            expect = sha_bytes(tei)
            # ⚠️ 休眠中之不對稱：manifest 記 LF 正規化，sections 記位元組。
            if expect != a.get('teiSha256'):
                note = ('⚠️ 位元組雜湊 ≠ manifest 之 LF 正規化 teiSha256'
                        '（🚨 該 TEI 含 CRLF）')
                asymmetric.append(d.name[:16])
        else:
            expect = a.get('sourceSha256')
        bad, stats = audit(doc, expect_source=expect)
        rows.append({'dir': d.name[:16], 'sourceType': a.get('sourceType'),
                     'verdict': 'consistent' if not bad else 'inconsistent',
                     'findings': bad, 'stats': stats, 'note': note})

c = Counter(r['verdict'] for r in rows)
print('二、語料：私有根之 acquired 全體（🚫 不是校準集 60）')
print('   sections 檔 %d 份' % len(rows))
for k, n in c.most_common():
    print('   %s %-22s %3d' % ('✅' if k == 'consistent' else '🚨', k, n))
for r in rows:
    if r['verdict'] != 'consistent':
        print('      🚨 %-16s %s' % (r['dir'], '；'.join(r['findings'])[:92]))
print()

by_kind = Counter(r['sourceType'] for r in rows)
print('   來源型別：%s'
      % '／'.join('%s %d' % kv for kv in sorted(by_kind.items())))
tot_sec = sum(r['stats'].get('sections', 0) for r in rows)
tot_ch = sum(r['stats'].get('chars', 0) for r in rows)
unt = sum(r['stats'].get('untitled', 0) for r in rows)
withunt = sum(1 for r in rows if r['stats'].get('untitled'))
lead = sum(r['stats'].get('untitledLeading', 0) for r in rows)
print('   節數合計 %d｜字元合計 %d｜每份中位節數 %s'
      % (tot_sec, tot_ch,
         sorted(r['stats'].get('sections', 0) for r in rows)[len(rows) // 2]
         if rows else '—'))
print()
print('三、🚨 休眠中之雜湊規則不對稱（🚫 本輪不改 `ahig/`）')
print('   `parse_tei` 記 `_sha256`（位元組）；manifest 之 `teiSha256` 記 `_text_sha256`（LF 正規化）。')
print('   ⚠️ 同一份 TEI、兩種規則——🚨 n+122 三／n+123 五只改了 manifest，沒改 `parse_tei`。')
if asymmetric:
    print('   🚨 已現形 %d 份（該 TEI 含 CRLF）：%s'
          % (len(asymmetric), '、'.join(asymmetric[:6])))
else:
    print('   ✅ 目前 0 份現形——⚠️ 因為 15 份 TEI 無一含 CRLF；')
    print('      🚨 故此為休眠而非不存在：換一個會翻譯行尾的路徑即成真。')
print('   🚫 本室不改：改雜湊規則是契約變更，⚠️ 須協調者裁定。')
print()
print('四、⚠️ 交給萃取期的兩個事實（🚫 本室不代為處理）')
print('   ① 佔位標題 `Untitled` 之節 %d 個，散在 %d／%d 份裡；'
      '🚨 其中 %d 份之**首節**即為 `Untitled`。' % (unt, withunt, len(rows), lead))
print('      ⚠️ 萃取若以標題定位章節，這些節定位不到——'
      '🚨 而首節通常是引言或摘要，是最常被定位的一節。')
big = sorted(rows, key=lambda r: -r['stats'].get('chars', 0))[:3]
print('   ② 篇幅最大之三份：%s'
      % '、'.join('%s（%d 字元／%d 節）'
                  % (r['dir'][:8], r['stats'].get('chars', 0),
                     r['stats'].get('sections', 0)) for r in big))
print('      ⚠️ 最大者是否為多研究之學位論文，屬萃取期判讀，🚫 取得端不代判。')

doc = {
    'schemaVersion': 1,
    'documentType': 'sections-internal-consistency',
    'ruling': 'self-initiated: nothing has ever checked that a section offset '
              'indexes the text the section claims. Extraction can read a '
              'section either way, and the two disagree silently.',
    'population': 'every artifact of every acquired manifest under the private '
                  'root fulltext/',
    'populationNote': 'The private-root population, not the calibration 60 and '
                      'not the calibration-plus-backfill set.',
    'countingUnit': 'sections file (one per artifact)',
    'criterion': 'the six invariants read off _with_offsets and the two '
                 'contentSha256 call sites, listed in the module docstring',
    'separatorChars': SEP,
    'controlProbes': ctl,
    'controlNote': 'Both directions. Without the positive control an '
                   'always-failing implementation would look like a corpus-wide '
                   'defect; without the negative ones a no-op would look clean.',
    'counts': dict(c),
    'sourceTypes': dict(by_kind),
    'totals': {'sections': tot_sec, 'chars': tot_ch,
               'untitledSections': unt, 'filesWithUntitled': withunt,
               'filesWhoseLeadingSectionIsUntitled': lead},
    'untitledCriterion': 'title is empty or the literal placeholder "Untitled" '
                         'that parse_jats and parse_tei write when no heading is '
                         'found (fulltext.py lines 240 and 346). A first version '
                         'of this script tested only for an empty string and '
                         'reported zero, which was a false all-clear.',
    'records': rows,
    'teiHashAsymmetry': {
        'sectionsRule': '_sha256 over raw bytes (parse_tei)',
        'manifestRule': '_text_sha256, LF-normalised (n+123(5))',
        'materialisedRecords': asymmetric,
        'why': 'n+122(3) and n+123(5) changed the manifest side only. The two '
               'agree today because no TEI in the corpus contains CRLF, so this '
               'is dormant rather than absent. Not repaired here: changing the '
               'hash rule in parse_tei is a contract change and needs a ruling.',
    },
    'forExtraction': 'Untitled sections cannot be located by heading, and the '
                     'largest documents may be multi-study; both are judgements '
                     'for the extraction stage, not for acquisition.',
    'coverageStatement': 'Checks that offsets and text agree with each other and '
                         'with the concatenation contract. Says nothing about '
                         'whether the sectioning is right, whether titles are '
                         'right, or whether content is faithful to the source XML '
                         '-- the last would mean re-running the parser, which is '
                         'checking an implementation with itself.',
    'contentNote': 'Directory prefixes, counts and verdicts. No section titles '
                   'and no text.',
}
doc['auditHash'] = content_hash({'counts': dict(c), 'files': len(rows)})
io.open(S + 'n498_sections_integrity.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn498_sections_integrity.json' % S)
sys.exit(0 if c.get('consistent', 0) == len(rows) else 1)
