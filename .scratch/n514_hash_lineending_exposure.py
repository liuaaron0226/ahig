# -*- coding: utf-8 -*-
"""行尾曝險之逐份量測（n+169 一之 4 交辦）：**換成 CRLF 會有幾份失配。**

## ✅ 交辦原文與本檔之答法

> 「逐份重算 sections 側之來源指紋兩種形式（裸位元組 vs LF 正規化），
> 回報**若換成 CRLF 檢出會有幾份失配**。⚠️ 今日預期 0。
> 🚫 不要改 `ahig/`。🚨 併報 `parse_jats` 側。」

**✅ 本檔只量測，🚫 不改任何規則、不改任何 manifest。**

## 🚨 先更正我自己的範圍（協調者已指出，此處照收）

**⚠️ 第 498 輪我把這件事寫成「`parse_tei` 的問題」——🚨 那是錯的。**
`parse_jats`（`fulltext.py:301`）與 `parse_tei`（`:369`）**都**用裸位元組雜湊。
**✅ 故兩條路徑同樣曝險，本檔逐路徑分列。**

## 🚨 曝險是什麼：同一份檔，兩種行尾，兩個指紋

| 側 | 欄位 | 規則 | 行尾一變 |
|---|---|---|---|
| sections | `sourceSha256` | **裸位元組** | **🚨 跟著變** |
| manifest（TEI 路徑） | `teiSha256` | LF 正規化 | ✅ 不變 |

**⚠️ 故「今天兩者相等」是環境事實，🚫 不是保證**——這正是交辦要量的東西。

## 🚨 判準（逐份，🚫 不抽樣）

對每一份 sections 所雜湊之來源檔，讀其位元組後判：

| 現況 | 換成 CRLF 會不會失配 |
|---|---|
| 含 `LF` 且不含 `CRLF` | **🚨 會**——⚠️ 轉換會改動位元組 |
| 已含 `CRLF` | ✅ 不會（它已經是 CRLF）；**🚨 但換成 LF 檢出就會** |
| 完全無換行 | ✅ 兩邊都不會 |

**✅ 故本檔兩個方向都報**：轉 CRLF 之失配數、轉 LF 之失配數。
**🚨 只報一個方向，會讓人以為另一個方向是安全的。**

## ⚠️ 一項用詞須precise：這批檔案不在版控裡

**⚠️ 交辦寫「CRLF 檢出」，而私有根不在 git 內，🚫 不會發生 git 檢出。**
**✅ 真正的觸發者是「任何會翻譯行尾的搬運」**——壓縮還原、同步工具、
重新下載、或有人把它納入一個 `text=auto` 的版控。
**🚨 本檔量的是同一件事，但把觸發條件寫清楚，🚫 不讓讀者以為只有 git 會做這件事。**

## 🚨 控制探針

**⚠️ 若兩個雜湊函式的比較寫錯，「0 份失配」與「什麼都沒比」印出來一樣。**
**✅ 故先以合成內容驗三種情形**（LF-only／CRLF／無換行），
**🚨 且必須看到「兩個函式對 CRLF 內容給出不同結果」——否則整份量測沒有意義。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 量得到：每一份來源檔在兩種行尾下之指紋是否改變。
- 🚨 量不到：**未來會不會真的發生那個轉換**——⚠️ 本檔量的是曝險，不是機率。
- ⚠️ 二進位來源（PDF）**不列入**：🚫 它本來就不該被行尾翻譯，
  **🚨 若真被翻譯，壞掉的是檔案本身而不只是指紋。**
"""
import io
import json
import re
import sys

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
CRLF, LF = b'\r\n', b'\n'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def exposure(raw):
    """回傳 (轉 CRLF 會否失配, 轉 LF 會否失配, 現況標籤)。"""
    has_crlf = CRLF in raw
    has_lf = LF in raw
    to_crlf = raw.replace(CRLF, LF).replace(LF, CRLF)
    to_lf = raw.replace(CRLF, LF)
    return (F._sha256(to_crlf) != F._sha256(raw),
            F._sha256(to_lf) != F._sha256(raw),
            'crlf' if has_crlf else ('lf' if has_lf else 'no-newline'))


print('=== 行尾曝險逐份量測（n+169 一之 4）===')
print()
print('一、控制探針——🚨 未過即拒絕報告')
cases = [(b'a\nb\nc', True, False, 'lf'),
         (b'a\r\nb\r\nc', False, True, 'crlf'),
         (b'abc', False, False, 'no-newline')]
ok = True
for raw, want_c, want_l, want_kind in cases:
    gc, gl, kind = exposure(raw)
    good = (gc, gl, kind) == (want_c, want_l, want_kind)
    ok = ok and good
    print('   %s %-14s → 轉CRLF失配=%-5s 轉LF失配=%-5s 現況=%s'
          % ('✅' if good else '🚨', repr(raw)[:14], gc, gl, kind))
# 🚨 最要緊的一道：兩個雜湊函式對含 CRLF 之內容必須給出不同結果。
diff = F._sha256(b'a\r\nb') != F._text_sha256(b'a\r\nb')
same = F._sha256(b'a\nb') == F._text_sha256(b'a\nb')
print('   %s 兩函式對 CRLF 內容給出不同結果＝%s；對 LF 內容相同＝%s'
      % ('✅' if (diff and same) else '🚨', diff, same))
ok = ok and diff and same
if not ok:
    sys.exit('🚨 控制探針未過——⚠️ 比較若沒在比，「0 份失配」毫無意義，中止。')
print('   ✅ 四道皆如預期。')
print()

rows = []
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') != 'acquired':
        continue
    for a in (m.get('artifacts') or []):
        st = a.get('sourceType')
        # sections 側之 `sourceSha256` 雜湊的是哪一份檔：
        #   JATS 路徑 → rawFile（.jats.xml）；TEI 路徑 → teiFile（.tei.xml）
        name = a.get('teiFile') if st == 'grobid-tei' else a.get('rawFile')
        p = d / (name or '')
        if not name or not p.exists():
            rows.append({'dir': d.name[:8], 'route': st,
                         'verdict': 'source-file-missing'})
            continue
        raw = p.read_bytes()
        to_crlf, to_lf, kind = exposure(raw)
        rows.append({'dir': d.name[:8], 'route': st, 'lineEndings': kind,
                     'wouldMismatchAsCrlf': to_crlf,
                     'wouldMismatchAsLf': to_lf,
                     'rawEqualsNormalised':
                         F._sha256(raw) == F._text_sha256(raw)})

routes = sorted({r.get('route') for r in rows})
print('二、逐路徑（🚫 不抽樣，逐份）')
print('   %-18s %6s %10s %10s %12s'
      % ('路徑', '份數', '轉CRLF失配', '轉LF失配', '現況'))
print('   ' + '-' * 66)
for rt in routes:
    sub = [r for r in rows if r.get('route') == rt]
    c = sum(1 for r in sub if r.get('wouldMismatchAsCrlf'))
    l = sum(1 for r in sub if r.get('wouldMismatchAsLf'))
    kinds = {}
    for r in sub:
        kinds[r.get('lineEndings', '?')] = kinds.get(r.get('lineEndings', '?'), 0) + 1
    print('   %-18s %6d %10d %10d %12s'
          % (rt, len(sub), c, l,
             '／'.join('%s %d' % kv for kv in sorted(kinds.items()))))
print('   ' + '-' * 66)
tot_c = sum(1 for r in rows if r.get('wouldMismatchAsCrlf'))
tot_l = sum(1 for r in rows if r.get('wouldMismatchAsLf'))
same_now = sum(1 for r in rows if r.get('rawEqualsNormalised'))
print('   %-18s %6d %10d %10d' % ('合計', len(rows), tot_c, tot_l))
print()
print('三、交辦所問之答案')
print('   🚨 若換成 CRLF，sections 側之來源指紋會失配之份數：**%d／%d**'
      % (tot_c, len(rows)))
print('   ⚠️ 反方向（換成 LF）：%d／%d——🚨 只報一個方向會讓人以為另一邊安全。'
      % (tot_l, len(rows)))
print('   ✅ 今日裸位元組雜湊與 LF 正規化雜湊相等者：%d／%d' % (same_now, len(rows)))
print('   🚨 「今天是 %d」與「不會變」是兩句話——⚠️ 上表第三欄就是那個差別。'
      % tot_c)
print()
print('四、⚠️ 觸發條件之用詞更正')
print('   🚫 私有根不在 git 內，故不會發生 git 檢出。')
print('   ✅ 真正的觸發者是任何會翻譯行尾的搬運：壓縮還原、同步工具、'
      '重新下載、或被納入 `text=auto` 之版控。')
print('   🚨 併記：manifest 側之 `teiSha256` 為 LF 正規化，不受影響；'
      '⚠️ 兩側因此會在同一次搬運後不一致。')

doc = {
    'schemaVersion': 1,
    'documentType': 'line-ending-exposure',
    'ruling': 'n+169(1)(4): recompute both forms per record and report how many '
              'would mismatch under a CRLF checkout; measure only, change nothing',
    'population': 'every acquired artifact, both routes',
    'countingUnit': 'artifact',
    'criterion': 'the file that sections.sourceSha256 hashes -- rawFile for the '
                 'JATS route, teiFile for the TEI route -- rehashed after '
                 'converting its line endings',
    'scopeCorrection': 'Round 498 called this a parse_tei problem. It is not: '
                       'parse_jats hashes raw bytes the same way, so both routes '
                       'are exposed. The coordinator caught this and it is '
                       'accepted here.',
    'controlProbes': {'cases': [{'input': repr(r), 'expected':
                                 {'crlf': c, 'lf': l, 'kind': k}}
                                for r, c, l, k in cases],
                      'hashesDifferOnCrlf': diff, 'hashesAgreeOnLf': same,
                      'why': 'If the comparison is not comparing, zero mismatches '
                             'and no measurement at all print the same number.'},
    'records': rows,
    'wouldMismatchAsCrlf': tot_c,
    'wouldMismatchAsLf': tot_l,
    'rawEqualsNormalisedToday': same_now,
    'total': len(rows),
    'triggerNote': 'The private root is not in git, so no git checkout applies. '
                   'The trigger is any transfer that translates line endings: an '
                   'archive round-trip, a sync tool, a re-download, or being '
                   'placed under version control with text=auto. The manifest '
                   'side is normalised and unaffected, so the two sides would '
                   'disagree after the same move.',
    'coverageStatement': 'Measures exposure, not likelihood: it says what would '
                         'change, not whether it will. Binary sources are '
                         'excluded because a PDF put through line-ending '
                         'translation is damaged as a file, not merely '
                         're-fingerprinted.',
    'contentNote': 'Directory prefixes, route names and counts only.',
}
doc['exposureHash'] = content_hash({'crlf': tot_c, 'lf': tot_l, 'n': len(rows)})
io.open(S + 'n514_hash_lineending_exposure.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn514_hash_lineending_exposure.json' % S)
