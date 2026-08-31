# -*- coding: utf-8 -*-
"""**n+169（一之 4）交辦的那道監測，外加它所依附的前提之核對。**（第 538 輪）

## 交辦內容

> 「逐份重算兩種形式，回報『若換成 CRLF 檢出會有幾份失配』。
>  今日答案應為 0；**而「今天是 0」與「不會變」是兩句話。**」

## ⚠️ 這一題有兩個問題，不是一個

同一份 TEI 被記了兩次，規則不同：

| 欄位 | 記的是 | 規則 |
|---|---|---|
| `manifest.artifact.teiSha256` | 那份 TEI | **LF 正規化**（`_text_sha256`） |
| `sections.sourceSha256`（`parse_tei` 寫的） | 同一份 TEI | **裸位元組**（`_sha256`） |

**🚨 於是行尾一旦被翻譯，一側會變、另一側不會。** ⚠️ 而第 516 輪起
`corpus.load_document` 會驗 sections 那一側，**故現在的後果不是靜靜通過，
是 TEI 那 15 份在萃取時全部讀不出來**——🚨 安全，但看起來會像資料壞了。

**✅ 故本支回報兩個數，🚫 不只一個**：
1. **今天**兩側是否相符（n+169 預期 0 失配）。
2. **若行尾被翻譯**，幾份的 sections 側會變、幾份的 manifest 側會變。

## 🚨 併報：遞延的理由本身

n+169（一之 2）遞延的理由是「**萃取期本來就要重寫那 41 份，併做成本最低**」。
**⚠️ 本支核對萃取階段實際會寫什麼。**

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門**，與 n+184、n535、n537 同類。
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n538_tei_crlf_monitor.json'


def sha_raw(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def sha_text(data: bytes) -> str:
    """與 `fulltext._text_sha256` 同規則：行尾正規化為 LF 之後再算。"""
    return sha_raw(data.replace(b'\r\n', b'\n').replace(b'\r', b'\n'))


def to_crlf(data: bytes) -> bytes:
    """模擬一次 CRLF 化的搬運：先歸零成 LF，再全部換成 CRLF。"""
    return data.replace(b'\r\n', b'\n').replace(b'\r', b'\n').replace(b'\n', b'\r\n')


def main():
    records, others = [], 0
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        manifest_path = entry / 'manifest.json'
        if not (entry.is_dir() and manifest_path.exists()):
            continue
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest.get('status') != 'acquired':
            continue
        artifacts = manifest.get('artifacts') or []
        if len(artifacts) != 1:
            continue
        artifact = artifacts[0]
        if artifact.get('sourceType') != 'grobid-tei':
            others += 1
            continue

        tei_name = artifact.get('teiFile') or ''
        tei_bytes = (entry / tei_name).read_bytes()
        sections = json.loads(
            (entry / artifact['sectionsFile']).read_text(encoding='utf-8'))

        recorded_tei = artifact.get('teiSha256')
        recorded_source = sections.get('sourceSha256')
        crlf = to_crlf(tei_bytes)

        records.append({
            'dir': entry.name[-16:],
            'hasCRLFToday': b'\r\n' in tei_bytes,
            'lfCount': tei_bytes.count(b'\n'),
            # 今天：兩側各自與所記之值相符嗎
            'manifestSideOkToday': sha_text(tei_bytes) == recorded_tei,
            'sectionsSideOkToday': sha_raw(tei_bytes) == recorded_source,
            # 若行尾被翻譯成 CRLF：哪一側會失配
            'manifestSideWouldBreak': sha_text(crlf) != recorded_tei,
            'sectionsSideWouldBreak': sha_raw(crlf) != recorded_source,
        })

    today_mismatch = sum(1 for r in records
                         if not (r['manifestSideOkToday']
                                 and r['sectionsSideOkToday']))
    would_break_sections = sum(1 for r in records if r['sectionsSideWouldBreak'])
    would_break_manifest = sum(1 for r in records if r['manifestSideWouldBreak'])
    have_newlines = sum(1 for r in records if r['lfCount'] > 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('今日失配為 0（n+169 一之 4 之預期）', today_mismatch == 0,
          '%d／%d 份失配' % (today_mismatch, len(records)))
    probe('今日無任何 TEI 含 CRLF',
          not any(r['hasCRLFToday'] for r in records),
          '⚠️ 這是環境事實，🚨 不是保證——n+169 的原話')
    probe('模擬 CRLF 化真的動得到東西（必觸發）',
          would_break_sections > 0,
          '🚨 若模擬之後一份都不失配，代表模擬沒生效，'
          '而「今天是 0」就會被誤讀成「怎樣都是 0」')
    probe('非對稱確實存在：一側會斷、另一側不會',
          would_break_sections == have_newlines and would_break_manifest == 0,
          'sections 側 %d 份會斷｜manifest 側 %d 份會斷（含換行者 %d）'
          % (would_break_sections, would_break_manifest, have_newlines))

    # ── n+169（一之 2）遞延之理由的核對 ────────────────────────────────
    # 「萃取期本來就要重寫那 41 份，併做成本最低」。⚠️ 那句話成不成立，
    # 看的是萃取實際會寫到哪裡。🚫 不用讀原始碼下結論，直接問寫入函式。
    from ahig.extraction import store  # noqa: E402

    # 用一個合成 id 就夠了——問的是「路徑落在哪個目錄下」，
    # 🚫 不需要把真的 id 寫進進版控的產物。
    sample_id = 'ahig:candidate:publication:' + '0' * 24
    fake_hash = 'sha256:' + '0' * 64
    write_targets = {
        'inventory': store.inventory_path(sample_id, fake_hash, fake_hash),
        'batch': store.batch_path('inventory-batch-' + '0' * 16),
    }
    fulltext_root = (ROOT / 'fulltext').resolve()
    into_fulltext = sorted(
        name for name, path in write_targets.items()
        if fulltext_root == path.resolve().parent
        or fulltext_root in path.resolve().parents)

    premise = {
        'claim': 'n+169（一之 2）：「萃取期本來就要重寫那 41 份，併做成本最低」',
        'writeTargets': {name: path.resolve().relative_to(ROOT).as_posix()
                         for name, path in write_targets.items()},
        'writesIntoFulltext': into_fulltext,
        'holds': bool(into_fulltext),
        'note': ('🚨 萃取的兩個寫入點都落在 extraction/ 之下，'
                 '⚠️ 而 corpus.py 對 fulltext/ 只讀不寫。'
                 '故「本來就要重寫那 41 份」對**已建成的萃取階段**不成立——'
                 '🚨 換雜湊規則需要它自己的一次重寫，併做省不到那個成本。'
                 '🚫 這不是說該現在改；⚠️ 只是說遞延時所寫的理由要重新看一次。'),
    }

    probe('遞延所依附之前提：萃取是否會重寫那 41 份',
          not premise['holds'],
          '🚨 實測萃取的寫入點為 %s，皆不在 fulltext/ 之下——'
          '⚠️ 故前提不成立（本探針以「不成立」為通過，因為那是實情）'
          % list(premise['writeTargets'].values()))

    doc = {
        'schemaVersion': 1,
        'documentType': 'tei-line-ending-monitor',
        'deferralPremise': premise,
        'ruling': 'n+169（一之 4）交辦：逐份重算兩種形式',
        'notAGate': '🚫 不入輪次閘門（n+181 三）；與 n+184、n535、n537 同類',
        'population': '私有根 acquired 中 sourceType=grobid-tei 者',
        'privateRoot': PROV,
        'nonTeiRecords': others,
        'counts': {
            'teiRecords': len(records),
            'mismatchToday': today_mismatch,
            'withCRLFToday': sum(1 for r in records if r['hasCRLFToday']),
            'withNewlines': have_newlines,
            'sectionsSideWouldBreakUnderCRLF': would_break_sections,
            'manifestSideWouldBreakUnderCRLF': would_break_manifest,
        },
        'theTwoAnswers': {
            'today': ('✅ %d 份失配——與 n+169 之預期相同。' % today_mismatch),
            'ifLineEndingsWereTranslated': (
                '🚨 %d／%d 份的 sections 側會失配，而 manifest 側 %d 份會失配。'
                '⚠️ 也就是說那道非對稱是實的，只是今天還沒被觸發。'
                % (would_break_sections, len(records), would_break_manifest)),
        },
        'consequenceToday': (
            '⚠️ 第 516 輪起 corpus.load_document 會驗 sections 那一側，'
            '🚨 故行尾一旦被翻譯，後果不是靜靜通過，是 TEI 那 %d 份在萃取時'
            '全部讀不出來——安全，但看起來會像資料壞了。'
            '🚫 而 manifest 側不會有任何動靜，所以查的人會先看錯地方。'
            % len(records)),
        'controlProbes': probes,
        'records': records,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n538 TEI 行尾監測（n+169 一之 4 交辦）===')
    print('   TEI 紀錄 %d 份（非 TEI %d 份不在母體內）' % (len(records), others))
    print('   今日失配            %d' % today_mismatch)
    print('   今日含 CRLF 者      %d' % doc['counts']['withCRLFToday'])
    print('   ── 若行尾被翻譯成 CRLF ──')
    print('   sections 側會失配   %d' % would_break_sections)
    print('   manifest 側會失配   %d' % would_break_manifest)
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
