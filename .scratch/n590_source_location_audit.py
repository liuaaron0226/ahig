# -*- coding: utf-8 -*-
"""**每一項結局宣稱的出處，站得住嗎。**（第 590 輪）

## 🚨 為什麼現在做這件事

「數字出現在哪一段決定它是什麼」這個教訓，本 run 已經應驗兩次：
⚠️ 第 587 輪——某篇的 `time trial` 全在參考文獻裡；
⚠️ 第 589 輪——某篇的 55／60／90 g/h 全在導論裡。

> **🚨 那兩次都是本室在**篩選**時差點被騙。**
> **⚠️ 而同一件事若發生在已經登錄的結局上，就不是差點——是已經記下去了。**

## ✅ 兩道檢查，跑過全部 790 項（🚫 不只在範圍內的 98 項）

| | 結果 |
|---|---|
| **甲 來源段落在該篇文件裡真的存在** | ✅ **790／790** |
| **乙 來源段落是導論／討論／參考文獻類** | 🚨 **3 項**（⚠️ 在範圍內的 98 項中：**0 項**） |

## 🚨 而那 3 項裡有 1 項是真的——它只是被另一個無關的空欄位擋住了

`c4128a6f6dd2c0b5` 宣告了一個 `tt-completion-time`，
**⚠️ 而它的出處是 `Discussion`**：讀的人取的是討論段落裡陳述的**百分比改善**，
🚫 不是結果段落裡的完成時間。

> **🚨 它沒有進入範圍，理由卻是 `effect-measure-not-in-scope`（欄位留空）。**
> **⚠️ 也就是說：擋住它的不是「出處不對」，是一個無關的漏填。**
> **🚫 若那個欄位當初填了，一個取自討論段落的數字就會進入證據池。**

另兩項出自討論段落者**沒有對應任何契約結局**（一項是流汗量，一項是選手自述），
✅ 讀的人正確地沒有宣告。

## ✅ 「在範圍內 0 項」為什麼可以相信

⚠️ 期待為零的檢查天生無法自證。本支的證據有兩層：
1. **🚨 它在真實資料上會亮**——790 項裡確實抓到 3 項，🚫 不是一個永遠不觸發的檢查；
2. **⚠️ 那些段落本來就在**——這批文件裡有 **101 個**導論／討論類段落可供引用，
   ✅ 而在範圍內的 98 項**一個都沒有用到**。

## 🚫 本支不入輪次閘門
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n590_source_location_audit.json'

CONTEXT = re.compile(r'introduction|background|discussion|conclusion'
                     r'|reference|perspective|limitation', re.I)


def main():
    ids = {c[-16:]: c for c in corpus.acquired_roster()[0]}
    cache = {}

    def sections_of(report):
        if report not in cache:
            cache[report] = {str(s.title or '')
                             for s in corpus.load_document(ids[report]).sections}
        return cache[report]

    total = in_scope = 0
    missing_section, cited_context, context_available = [], [], 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        context_available += sum(1 for t in sections_of(report)
                                 if CONTEXT.search(t))
        for item in doc.get('reportedOutcomes') or []:
            total += 1
            scoped = bool((item.get('scopeDecision') or {}).get('inScope'))
            in_scope += 1 if scoped else 0
            section = ((item.get('sourceLocation') or {}).get('section')) or ''
            if section not in sections_of(report):
                missing_section.append({'report': report, 'section': section})
            if CONTEXT.search(section):
                cited_context.append({
                    'report': report, 'section': section, 'inScope': scoped,
                    'normalisedOutcomeRef': item.get('normalisedOutcomeRef'),
                    'excludedFor': (item.get('scopeDecision')
                                    or {}).get('reasonCode'),
                })

    context_in_scope = [c for c in cited_context if c['inScope']]
    context_declared = [c for c in cited_context
                        if c['normalisedOutcomeRef'] and not c['inScope']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('掃到的是完整的那一批（必觸發）',
          total == 790 and in_scope == 98,
          '🚨 對不上就代表本支看的不是同一批；實得結局 %d 項／在範圍內 %d 項'
          % (total, in_scope))
    # 🚨 必觸發之反向：甲檢查要能說「不存在」。
    fake = 'ZZ-這個段落不存在-ZZ'
    any_report = next(iter(cache))
    probe('段落存在檢查說得出「不存在」（必觸發之反向）',
          fake not in sections_of(any_report),
          '🚨 以一個不可能存在的段落名試；⚠️ 若它也算存在，「790／790」就沒有意義')
    # 🚨 這一道是「在範圍內 0 項」能不能被相信的關鍵：⚠️ 乙檢查在真實資料上會不會亮。
    probe('引用導論類段落的檢查在真實資料上會亮（必觸發之反向）',
          len(cited_context) > 0,
          '✅ 790 項裡抓到 %d 項；🚨 若為零，「在範圍內 0 項」就可能只是檢查沒動'
          % len(cited_context))
    probe('這些文件裡本來就有導論類段落可供引用（必觸發）',
          context_available > 0,
          '⚠️ 實得 %d 個；🚨 若為零，「沒有人引用它們」是廢話' % context_available)
    # 🚨 這一道會紅：⚠️ 有一個契約結局是從討論段落取的，
    # 🚫 而擋住它的是一個無關的漏填。
    probe('沒有任何契約結局的出處是導論／討論類段落',
          not context_declared,
          '🚨 實得 %d 項：⚠️ 其中一項宣告 tt-completion-time 而出處是 Discussion，'
          '🚫 它沒進範圍的理由卻是 %s——**擋住它的不是出處不對**'
          % (len(context_declared),
             [c['excludedFor'] for c in context_declared]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'source-location-audit',
        'question': '每一項結局宣稱的出處站不站得住',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'outcomesScanned': total,
        'inScope': in_scope,
        'sourceSectionMissing': len(missing_section),
        'citedContextSections': len(cited_context),
        'citedContextInScope': len(context_in_scope),
        'citedContextWithContractOutcome': context_declared,
        'contextSectionsAvailable': context_available,
        'headline': (
            '✅ 790 項的來源段落全部真的存在，⚠️ 而在範圍內的 98 項沒有一項'
            '取自導論／討論類段落。'
            '🚨 但 790 項裡有 3 項取自討論段落，其中 1 項宣告了契約結局——'
            '⚠️ 它取的是討論段落裡陳述的百分比改善，🚫 不是結果段落裡的完成時間。'),
        'whyItMatters': (
            '🚨 那一項沒有進入範圍的理由是 effect-measure-not-in-scope（欄位留空），'
            '⚠️ 而不是「出處不對」。'
            '🚫 若那個欄位當初填了，一個取自討論段落的數字就會進入證據池。'),
        'whyZeroCanBeBelieved': (
            '⚠️ 期待為零的檢查天生無法自證。'
            '✅ 兩層證據：① 它在真實資料上抓到 3 項，🚫 不是永不觸發；'
            '② 這批文件裡有 %d 個導論類段落可供引用，'
            '而在範圍內的 98 項一個都沒用到。' % context_available),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n590 出處稽核 ===')
    print('   結局 %d 項（在範圍內 %d）｜✅ 段落存在 %d／%d'
          % (total, in_scope, total - len(missing_section), total))
    print('   🚨 出處為導論／討論類：%d 項（在範圍內 %d 項）｜'
          '⚠️ 可供引用的那種段落共 %d 個'
          % (len(cited_context), len(context_in_scope), context_available))
    for item in cited_context:
        print('      %s｜%s｜ref=%s｜排除理由=%s'
              % (item['report'], item['section'][:26],
                 item['normalisedOutcomeRef'], item['excludedFor']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
