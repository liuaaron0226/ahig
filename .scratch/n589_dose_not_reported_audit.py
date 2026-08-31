# -*- coding: utf-8 -*-
"""**那 12 項 `dose=None`，是論文沒寫還是讀的人沒填。**（第 589 輪）

## 🚨 本支差一點回報「5 項可救回」——**而正確答案是 1 項**

第 588 輪數出 `notExtracted-dose-outside-bands` 裡有 12 項是 `dose=None`。
⚠️ 全文搜尋顯示其中 3 篇**明寫了 g/h 或 g/min**，
🚨 其中一篇甚至寫著 55／60／90 g/h——**全在帶內。**

> **⚠️ 若就此回報，本室會說「至少 5 項被白白丟掉」。**
> **🚨 而查了段落之後：那些數字全部在 Introduction 與 Discussion 裡。**
> ✅ 它們是**引述文獻的建議攝取率**（60、90 g/h 是這個領域的常見數字），
> **🚫 不是那篇研究自己餵的量。**

**✅ 這是第 587 輪那個教訓的第二次應驗**：
⚠️ `44243ac624c9b5e0` 的 `time trial` 全在參考文獻裡；
🚨 這一次是劑量全在導論與討論裡。**「數字出現在哪一段」決定它是什麼。**

## ✅ 真正可救的只有一項

`0cfceb6c8a86f78b` 在**方法段**寫明餵食速率 **1.8 g/min**（＝108 g/h，很高帶內），
⚠️ 而讀的人留了 `dose=None`，於是被判成「劑量不在帶內」。

> **📮 但這需要一個裁定**：g/min → g/h 是**單位換算**，
> ⚠️ 與「6% 溶液 × 每次 284 ml」換算成 g/h **不是同一件事**——
> 🚨 後者是本室自己造一個論文沒寫的數，前者只是換單位。
> **🚫 本室不逕自換算**，✅ 只把這一項列出來。

## 🚫 本支不入輪次閘門
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

OUT = Path(__file__).resolve().parent / 'n589_dose_not_reported_audit.json'
REASON = 'notExtracted-dose-outside-bands'

RATE = re.compile(r'\d+(?:\.\d+)?\s*(?:g|grams?)\s*(?:·|\.|/| per )\s*'
                  r'(?:h|hr|hour|min)', re.I)
# 🚨 這些段落講的是**別人的研究**：⚠️ 裡面的數字不是這篇自己餵的量。
CONTEXT = re.compile(r'introduction|background|discussion|conclusion'
                     r'|references|perspective|limitation', re.I)


def rates_by_role(candidate):
    """回傳 (研究自身段落的速率, 引述性段落的速率)。"""
    doc = corpus.load_document(candidate)
    own, cited = set(), set()
    for section in doc.sections:
        title = str(section.title or '')
        hits = set(RATE.findall(section.text or ''))
        (cited if CONTEXT.search(title) else own).update(hits)
    return own, cited


def main():
    ids = {c[-16:]: c for c in corpus.acquired_roster()[0]}

    blanks = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        count = sum(1 for o in doc.get('reportedOutcomes') or []
                    if (o.get('scopeDecision') or {}).get('reasonCode') == REASON
                    and o.get('dose') is None)
        if count:
            blanks[doc['report'][-16:]] = count

    rows, recoverable, naive = [], [], []
    for report, count in sorted(blanks.items(), key=lambda kv: -kv[1]):
        own, cited = rates_by_role(ids[report])
        if own or cited:
            naive.append(report)          # ⚠️ 天真做法：全文有數字就算「有報」
        if own:
            recoverable.append(report)
        rows.append({
            'report': report, 'blankItems': count,
            'ratesInStudySections': sorted(own),
            'ratesInCitingSections': sorted(cited),
            'verdict': ('recoverable-rate-stated-in-methods' if own
                        else 'blank-is-correct'),
        })

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('找到第 588 輪數到的那 12 項（必觸發）',
          sum(blanks.values()) == 12 and len(blanks) == 6,
          '🚨 對不上就代表本支看的不是同一批項目；實得 %d 項／%d 篇'
          % (sum(blanks.values()), len(blanks)))
    # 🚨 必觸發之反向：段落分類要**兩邊都真的分得出來**，
    # ⚠️ 否則它可能把每一處都歸到同一邊，而結論會長得一模一樣。
    only_cited = [r for r in rows if r['ratesInCitingSections']
                  and not r['ratesInStudySections']]
    only_own = [r for r in rows if r['ratesInStudySections']
                and not r['ratesInCitingSections']]
    probe('段落分類兩邊都真的出現（必觸發之反向）',
          bool(only_cited) and bool(only_own),
          '⚠️ 只在引述段落 %d 篇、只在研究段落 %d 篇；'
          '🚨 若其中一邊為空，這個分類可能根本沒生效'
          % (len(only_cited), len(only_own)))
    # 🚨 這一道量的是**天真做法會多報多少**——⚠️ 那正是本支存在的理由。
    probe('天真做法（全文有數字就算有報）與段落分類給的答案不同',
          len(naive) != len(recoverable),
          '🚨 天真做法會說 %d 篇有報劑量，✅ 段落分類說 %d 篇；'
          '⚠️ 差的那 %d 篇，數字全在導論與討論裡——那是別人的研究'
          % (len(naive), len(recoverable), len(naive) - len(recoverable)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'dose-not-reported-audit',
        'question': '12 項 dose=None 是論文沒寫，還是讀的人沒填',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'blankItems': sum(blanks.values()),
        'blankReports': len(blanks),
        'naiveWholeDocumentSaysReported': len(naive),
        'sectionAwareSaysReported': len(recoverable),
        'recoverableReports': recoverable,
        'rows': rows,
        'headline': (
            '🚨 全文搜尋會說 3 篇有寫劑量（其中一篇寫著 55／60／90 g/h，全在帶內），'
            '⚠️ 而那些數字全部在 Introduction 與 Discussion——'
            '✅ 它們是引述文獻的建議攝取率，🚫 不是那篇自己餵的量。'
            '✅ 真正在方法段寫明速率的只有 1 篇。'),
        'theOneRecoverable': (
            '`0cfceb6c8a86f78b` 於方法段寫明 1.8 g/min（＝108 g/h，很高帶內），'
            '⚠️ 而讀的人留空。📮 但這需要裁定：g/min → g/h 是單位換算，'
            '🚨 與「6% 溶液 × 每次 284 ml」換算成 g/h 不是同一件事。'
            '🚫 本室不逕自換算。'),
        'lesson': (
            '✅ 這是第 587 輪那個教訓的第二次應驗：'
            '⚠️ 一次是 time trial 全在參考文獻裡，一次是劑量全在導論裡。'
            '🚨 **數字出現在哪一段，決定它是什麼。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n589 dose=None 是誰沒寫 ===')
    print('   🚨 天真做法：%d 篇「有報劑量」｜✅ 段落分類：%d 篇'
          % (len(naive), len(recoverable)))
    for row in rows:
        print('   %s｜留空 %d 項｜研究段落 %s｜引述段落 %s｜%s'
              % (row['report'], row['blankItems'],
                 row['ratesInStudySections'] or '無',
                 row['ratesInCitingSections'] or '無', row['verdict']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
