# -*- coding: utf-8 -*-
"""**那 19 篇的腸胃症狀，量的是同一把尺嗎。**（第 633 輪）

## 🚨 第 632 輪把這件事留成「未知」

⚠️ 那 60 項腸胃症狀結局的 `instrument` 全是 `None`，
🚨 而它們通過的儀器關卡對它們是空的。**⚠️ 於是「合不合得起來」只能寫成未知。**

> **✅ 但未知是可以縮小的**——清冊裡有 `localLabel`，
> 🚨 它是本 run 讀論文時逐字抄下來的結局名稱，**⚠️ 裡面通常寫著量表。**

## ✅ 本支怎麼做，以及守什麼

在腳本內把標籤分類成量表型別，**🚫 只輸出計數**——
⚠️ 不輸出任何標籤文字、不寫進 repo（n+195 一）。

| 型別 | 判準（關鍵詞） |
|---|---|
| VAS | visual analogue／VAS／mm scale |
| Likert／點量表 | likert／n-point／scale of N |
| 數值範圍 | 0–10、1–9 之類的區間寫法 |
| 發生率／人數 | incidence／number of participants／% reporting |
| 具名問卷 | GSRS、Bristol 等具名工具 |
| **未能分類** | 🚨 以上皆非——**這一格才是重點** |

**⚠️ 分類器自己要先驗身**：🚨 認不出已知的樣本，「分得出幾類」毫無意義。

## 🚫 本支不送外部請求、不改任何產品程式、不改任何清冊
"""
import collections
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

OUT = Path(__file__).resolve().parent / 'n633_gi_scale_heterogeneity.json'

GI_REFS = ('gi-symptom-severity', 'gi-symptom-incidence')

CLASSES = [
    ('VAS', re.compile(r'visual\s+analog|vas\b|\bmm\s+scale', re.I)),
    ('具名問卷', re.compile(r'gsrs|bristol|rome\s+i|questionnaire', re.I)),
    ('Likert／點量表', re.compile(r'likert|\d+\s*-\s*point|point\s+scale', re.I)),
    ('數值範圍', re.compile(r'\b\d\s*(?:-|–|to)\s*\d{1,2}\b(?!\s*%)', re.I)),
    ('發生率／人數', re.compile(
        r'incidence|number\s+of\s+(?:participants|subjects)|'
        r'proportion|% ?report|prevalence|frequency', re.I)),
]

# ⚠️ 分類器驗身用的樣本：🚨 每一類各一，外加一個應當落入「未能分類」的。
SELF_TEST = [
    ('VAS', 'abdominal pain on a 100 mm visual analogue scale'),
    ('具名問卷', 'GSRS total score'),
    ('Likert／點量表', 'nausea rated on a 9-point scale'),
    ('數值範圍', 'bloating rated 0-10'),
    ('發生率／人數', 'incidence of vomiting'),
    ('未能分類', 'stomach problems'),
]


def classify(label):
    for name, pattern in CLASSES:
        if pattern.search(label or ''):
            return name
    return '未能分類'


def main():
    self_ok = {expected: classify(text) == expected
               for expected, text in SELF_TEST}

    per_paper = collections.defaultdict(set)
    per_class = collections.Counter()
    labels_seen = 0
    unclassified_papers = set()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if not (outcome.get('scopeDecision') or {}).get('inScope'):
                continue
            if outcome.get('normalisedOutcomeRef') not in GI_REFS:
                continue
            labels_seen += 1
            verdict = classify(outcome.get('localLabel'))
            per_class[verdict] += 1
            per_paper[doc['report'][-16:]].add(verdict)
            if verdict == '未能分類':
                unclassified_papers.add(doc['report'][-16:])

    # ⚠️ 一篇可能同時有 VAS 與發生率，故逐篇記「用了幾類」。
    classes_per_paper = collections.Counter(
        len(v) for v in per_paper.values())
    only_unclassified = [p for p, v in per_paper.items()
                         if v == {'未能分類'}]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('分類器認得出每一類樣本（必觸發之正對照）',
          all(self_ok.values()),
          '🚨 驗身結果 %s；⚠️ 少認一類，「分得出幾類」就沒有意義' % self_ok)
    probe('模糊的標籤會落入「未能分類」（必觸發之反向）',
          self_ok.get('未能分類') is True,
          '🚨 以一個沒有量表資訊的樣本試；⚠️ 若它也被歸進某一類，'
          '本支只是在亂貼標籤')
    probe('真的讀到腸胃症狀標籤（必觸發之正對照）',
          labels_seen == 60,
          '🚨 實得 %d 項（第 632 輪數到 60）；⚠️ 對不上就代表本支讀的不是同一批'
          % labels_seen)
    # 🚨 以下兩道是結果。
    probe('腸胃症狀的量表型別是單一的',
          len([k for k in per_class if k != '未能分類']) <= 1,
          '🚨 實得型別分布：%s' % dict(per_class.most_common()))
    probe('沒有篇是完全看不出量表的',
          not only_unclassified,
          '🚨 實得 %d 篇的腸胃症狀標籤**完全看不出量表**：%s'
          % (len(only_unclassified), sorted(only_unclassified)[:6]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'gi-scale-heterogeneity',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contentDiscipline': (
            '✅ 只輸出計數與型別名；🚫 不輸出任何標籤文字（n+195 一）。'),
        'giOutcomesExamined': labels_seen,
        'papers': len(per_paper),
        'byScaleClass': dict(per_class.most_common()),
        'classesPerPaper': dict(sorted(classes_per_paper.items())),
        'papersWithOnlyUnclassified': sorted(only_unclassified),
        'papersWithAnyUnclassified': len(unclassified_papers),
        'whyItMatters': (
            '⚠️ 第 632 輪把腸胃症狀的可合併性寫成「未知」——'
            '🚨 因為那 60 項的 instrument 全是 None，關卡對它們是空的。'
            '✅ 本支從標籤把未知縮小：⚠️ 若型別散在好幾類，'
            '**那 19 篇量的就不是同一把尺**，'
            '🚫 而「19 篇」這個數在合併時不能照面額使用。'),
        'classifierIsOrdered': (
            '⚠️ 本支的分類是**有序優先**：一個標籤先撞到哪一條規則就算哪一類。'
            '🚨 故型別之間可能重疊——例如「rated 0-10」被歸為數值範圍，'
            '而它在論文裡也可能其實是一支 VAS。'
            '**✅ 因此「幾類」這個數不精確；🚫 但「不是同一把尺」是穩的**：'
            'VAS、Likert 點量表與具名問卷是明確不同的家族。'),
        'whatThisCannotAnswer': (
            '🚫 標籤沒寫量表，不代表論文沒寫——⚠️ 本支只讀清冊的標籤，'
            '不重讀全文；🚨 故「未能分類」是**清冊裡看不出來**，'
            '不是「該研究沒有量表」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n633 腸胃症狀量表異質性 ===')
    print('   腸胃症狀在範圍內結局 %d 項、分布於 %d 篇'
          % (labels_seen, len(per_paper)))
    print('   量表型別分布：')
    for name, count in per_class.most_common():
        print('      %-16s %d 項' % (name, count))
    print('   每篇用到幾類：%s' % dict(sorted(classes_per_paper.items())))
    print('   完全看不出量表的篇數：%d' % len(only_unclassified))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
