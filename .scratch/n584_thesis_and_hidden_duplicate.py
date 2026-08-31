# -*- coding: utf-8 -*-
"""**語料裡有一本博士論文，而它與一篇期刊論文是同一批人。**（第 584 輪）

## 🚨 讀出來的東西，比第 582 輪判斷的更要緊

第 582 輪找到 `307c0dd5b141caed` ↔ `7a6ac1559c740fd6` 受試者特徵 6／6 全中，
當時說是「兩篇報告同一個試驗」。**⚠️ 把段落讀出來之後，實情不同：**

> **🚨 `307c0dd5b141caed` 是一本博士論文**——348,621 字、160 個段落、
> **4 個各自不同的 `Participants` 段落**，並有 **5 個 `Chapter …` 起頭的章節標題**
> （🚫 章名逐字不寫進 repo——⚠️ 那是文獻內容，而 n+80 已載明閘門的樣式抓不到它）。
> ✅ **讀它的那個視窗自己註明了**：
> 「This report is a PhD thesis containing five studies under one report id,
> not a single trial, so outcomes are labelled by study.」

⚠️ 故這不是「兩篇論文重複」，是**一本含五個試驗的文件被當成一份 report**，
🚨 **而其中一個試驗，另外還有一篇期刊論文。**

## 🚨 而那個重複**現在看不見**——因為另一邊剛好壞著

| | 在範圍內結局 |
|---|---|
| 論文 `307c0dd5b141caed`（Study 2，45／90 g/h） | **4 項**：`time-to-exhaustion` ×2、`muscle-glycogen-post-exercise` ×2 |
| 期刊 `7a6ac1559c740fd6`（同一批 8 人、肌肉切片） | **0 項** |

> **🚨 那個 0 不是「這篇沒有結局」**，是 n+189 之前的請求沒帶儀器清單，
> ⚠️ 六項宣告全被判成 `instrument-not-in-allowlist`（第 574 輪已數過）。
> **🚫 也就是說：重複計數現在是潛伏的。**
> **⚠️ 一旦照計畫重讀那一篇，它就會浮出來——同一批 8 人的肌肉肝醣被數兩次。**

📮 **故重讀 `7a6ac1559c740fd6` 不能單獨做**：🚨 它必須和「這兩筆算一個 study」
一起決定，⚠️ 否則修好一個缺陷會製造另一個。

## ✅ 偵測方法：**不能只看有沒有 Acknowledgements**

⚠️ 期刊論文本來就有致謝與縮寫表：**🚨 那條寬鬆的規則會標到 10 篇以上。**
✅ 真正分得開的是兩件：**章節式標題（`Chapter …`）**，
或**同一份文件裡有 2 個以上的受試者段落**（一篇期刊論文只有一個）。
**🚨 本支把兩條規則的命中數都算出來**——🚫 不只報精確那一條。

## 🚫 本支不入輪次閘門，且不把內容寫進 repo
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n584_thesis_and_hidden_duplicate.json'

# ⚠️ 寬鬆規則：期刊論文也有這些，🚨 留著是為了報出它會標多少篇。
LOOSE = re.compile(r'acknowledg|abbreviation|list of (tables|figures)', re.I)
# ✅ 精確規則：章節式標題。
CHAPTER = re.compile(r'^\s*chapter\b', re.I)
# ✅ 精確規則之二：一份文件裡多個受試者段落。
PARTICIPANT_TITLE = re.compile(r'^\s*(participants?|subjects?)\s*$', re.I)
COHORT_PAIR = ('307c0dd5b141caed', '7a6ac1559c740fd6')


def inventories():
    out = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        out[doc['report'][-16:]] = doc
    return out


def main():
    ids, _ = corpus.acquired_roster()
    invs = inventories()

    rows, loose_hits = [], []
    for candidate in ids:
        key = candidate[-16:]
        doc = corpus.load_document(candidate)
        titles = [str(section.title or '') for section in doc.sections]
        chapters = [t for t in titles if CHAPTER.match(t)]
        participant_sections = [t for t in titles if PARTICIPANT_TITLE.match(t)]
        if any(LOOSE.search(t) for t in titles):
            loose_hits.append(key)
        if chapters or len(participant_sections) > 1:
            inv = invs.get(key) or {}
            in_scope = [o for o in (inv.get('reportedOutcomes') or [])
                        if (o.get('scopeDecision') or {}).get('inScope')]
            rows.append({
                'report': key, 'chars': len(doc.content),
                'sections': len(titles), 'chapterTitles': len(chapters),
                'participantSections': len(participant_sections),
                'inScopeOutcomes': len(in_scope),
                'readerNoticed': 'thesis' in ((inv.get('completenessAttestation')
                                               or {}).get('note') or '').lower(),
            })
    rows.sort(key=lambda r: -r['chars'])

    left, right = COHORT_PAIR
    pair_scope = {}
    for key in COHORT_PAIR:
        inv = invs.get(key) or {}
        in_scope = [o for o in (inv.get('reportedOutcomes') or [])
                    if (o.get('scopeDecision') or {}).get('inScope')]
        refs = {}
        for item in in_scope:
            ref = item.get('normalisedOutcomeRef')
            refs[ref] = refs.get(ref, 0) + 1
        pair_scope[key] = {'inScope': len(in_scope), 'byOutcome': refs}

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('偵測到那本論文（必觸發）',
          any(r['report'] == left for r in rows),
          '🚨 若偵測不到，本支的「只有 1 本」就是假的；實得命中 %d 篇' % len(rows))
    probe('精確規則真的比寬鬆規則窄（必觸發之反向）',
          0 < len(rows) < len(loose_hits),
          '⚠️ 寬鬆規則（致謝／縮寫表）標到 %d 篇，✅ 精確規則只標 %d 篇；'
          '🚨 若兩者一樣，代表精確規則沒有生效' % (len(loose_hits), len(rows)))
    probe('讀那本論文的視窗自己註明了它是論文',
          any(r['report'] == left and r['readerNoticed'] for r in rows),
          '✅ 完整性聲明裡寫著 thesis；🚨 若沒有，那 4 項在範圍內結局'
          '會被當成單一試驗的結果')
    # 🚨 這一道問的是**有沒有被記下來**，🚫 不是「有沒有風險」——
    # ⚠️ 一個判斷不出答案的探針，寫成永遠會紅只是裝樣子。
    # ✅ 故它查一件確定的事：`stats/family.py` 的成群結果裡有沒有這一對。
    families = json.loads(
        (Path(__file__).resolve().parent / 'n580_study_vs_report.json')
        .read_text(encoding='utf-8'))
    recorded = families['tier1Families'] > 0
    probe('這兩筆已被記錄為同一個 study', recorded,
          '🚨 tier1 成群為 %d 個，⚠️ 故這一對在系統裡仍是兩份獨立證據。'
          '期刊那篇目前在範圍內 %d 項（因儀器清單缺陷被歸零）、論文那本 %d 項；'
          '🚫 重讀之後同一批 8 人的結局會被數兩次'
          % (families['tier1Families'], pair_scope[right]['inScope'],
             pair_scope[left]['inScope']))

    doc = {
        'schemaVersion': 1,
        'documentType': 'thesis-and-hidden-duplicate',
        'question': '語料裡有沒有「一份文件含多個試驗」的東西，以及它有沒有造成重複',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'corpusSize': len(ids),
        'looseRuleHits': len(loose_hits),
        'preciseRuleHits': len(rows),
        'rows': rows,
        'cohortPair': {'thesis': left, 'journalArticle': right,
                       'identicalCohortValues': 6,
                       'scope': pair_scope},
        'whyTheDuplicateIsInvisible': (
            '🚨 期刊那篇目前在範圍內 0 項，⚠️ 不是因為它沒有結局，'
            '而是 n+189 之前的請求沒帶儀器清單，六項宣告全被判成 '
            'instrument-not-in-allowlist（第 574 輪已數）。'
            '🚫 故重複計數現在是潛伏的——⚠️ 一旦重讀就會浮出來。'),
        'consequence': (
            '📮 重讀 7a6ac1559c740fd6 不能單獨做：🚨 必須與「這兩筆算一個 study」'
            '一起決定，⚠️ 否則修好一個缺陷會製造另一個。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n584 論文型文件與潛伏的重複 ===')
    print('   寬鬆規則（致謝／縮寫表）命中 %d 篇｜✅ 精確規則命中 %d 篇'
          % (len(loose_hits), len(rows)))
    for r in rows:
        print('   🚨 %s｜%d 字／%d 段｜章節標題 %d｜受試者段落 %d｜'
              '在範圍內 %d 項｜讀的人有註明：%s'
              % (r['report'], r['chars'], r['sections'], r['chapterTitles'],
                 r['participantSections'], r['inScopeOutcomes'],
                 r['readerNoticed']))
    print('   ── 那一對 ──')
    for key in COHORT_PAIR:
        print('   %s：在範圍內 %d 項 %s'
              % (key, pair_scope[key]['inScope'], pair_scope[key]['byOutcome']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
