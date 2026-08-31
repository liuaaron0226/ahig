# -*- coding: utf-8 -*-
"""**篩那 12 份最新的——0 份切題，而且問題出在查詢本身。**（n+195，P3）

## 🚨 兩件要更正的事

### 一、第 600 輪那個「最新截止日 July 2026」**是一份 protocol**

⚠️ 它是一份**系統性回顧的計畫書**，🚫 不是完成的回顧——**沒有結果可用。**
**✅ 故那個數字撤回**，🚫 不得當作 protocol 四之 2 的答案。
⚠️ 本室當時已標為「暫定」，🚨 而暫定的理由正是這個：**沒篩選過。**

### 二、🚨 查詢乙問錯了構念

本室用 `weight loss maintenance` 去問「赤字維持得住嗎」。

> **⚠️ 但文獻裡的 weight loss maintenance 指的是「減完之後把體重維持住」，
> 🚫 不是「減脂期間把赤字維持住」。**
> **🚨 那是兩個不同的問題**——擁有者要的是後者（ADR-0012／protocol 一）。

✅ 這解釋了 228 筆裡為什麼滿是**減重後維持**、**藥物**、**基因**的回顧。
📮 建議改問：`dietary adherence`、`caloric restriction adherence`、
`attrition`、`dropout`、`compliance` ＋ 赤字／能量限制情境。

## ✅ 12 份的篩選結果

| 判定 | 份數 |
|---|---|
| 🚫 離題 | 7 |
| 🚫 protocol 明文排除（藥物） | 2 |
| 🚫 是計畫書不是回顧 | 1 |
| ⚠️ 相鄰、可留但要註記 | 2 |
| ✅ **直接切題** | **0** |

🚨 **12 份最新的裡面，一份直接切題的都沒有。**

## 🚫 本支只記判定與理由，🚫 不把題名寫進 repo
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'p3_step1c_screen_recent.json'
PRIOR = Path(__file__).resolve().parent / 'p3_step1b_cutoff_scan.json'

# 🚨 固定的理由詞彙。⚠️ 不在這裡的理由不得使用——
# 那正是本 run 對 ADJUDICATION_CAUSES 的同一條紀律。
REASONS = {
    'off-topic': '主題不在本 protocol 的問題範圍內',
    'excluded-by-protocol-drugs': 'protocol 一明文不回答藥物',
    'protocol-not-a-review': '是系統性回顧的計畫書，🚫 沒有結果',
    'adjacent-adherence': '⚠️ 與「赤字維持」相鄰，✅ 可留但要註記差異',
}

# ✅ 判定依題名與摘要（兩者只在私有根）。🚫 repo 只留識別碼與理由。
SCREEN = {
    '42498599': ('off-topic', '試驗方法學效應，族群為乳糜瀉'),
    '40864442': ('off-topic', '皮膚科族群之飲食失調盛行，🚫 非介入、非赤字'),
    '41344801': ('adjacent-adherence',
                 '⚠️ 限時進食之質性經驗綜合；✅ 與依從性相鄰，'
                 '🚨 但結局是「感受與看法」，🚫 不是赤字維持率'),
    '42440372': ('protocol-not-a-review',
                 '🚨 這正是第 600 輪那個「最新截止日 July 2026」——'
                 '⚠️ 它是計畫書，🚫 沒有結果'),
    '40577090': ('off-topic', '飲食型態與憂鬱之傘狀回顧'),
    '42394382': ('off-topic', '肝醣儲積症之連續血糖監測'),
    '42666688': ('excluded-by-protocol-drugs', 'GLP-1 受體促效劑'),
    '42165996': ('off-topic',
                 '⚠️ 虛擬實境介入，族群為肥胖與飲食疾患，'
                 '🚫 結局為生物標記，非壓力性進食或赤字維持'),
    '40861630': ('adjacent-adherence',
                 '⚠️ 長期減重維持之**預測因子**（行為＋基因）；'
                 '🚨 是預測因子不是介入，且「減重維持」≠「赤字維持」'),
    '42426361': ('excluded-by-protocol-drugs', '抗肥胖藥物'),
    '42514369': ('off-topic', '飲食與鼻竇炎'),
    '42654169': ('off-topic', '地中海飲食與心血管事件'),
}

CONSTRUCT_NOTE = (
    '🚨 查詢乙用 weight loss maintenance 問「赤字維持得住嗎」——⚠️ 問錯了構念。'
    '文獻裡它指的是「減完之後把體重維持住」，🚫 不是「減脂期間把赤字維持住」。'
    '✅ 建議改問 dietary adherence／caloric restriction adherence／'
    'attrition／dropout／compliance ＋ 能量限制情境。')


def main():
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    stated = prior['statedCutoffByRecord']
    recent = {k: v for k, v in stated.items() if '2025' in v or '2026' in v}

    unknown = sorted(set(SCREEN) - set(recent))
    missing = sorted(set(recent) - set(SCREEN))
    bad_reason = sorted(k for k, (r, _n) in SCREEN.items() if r not in REASONS)

    tally = Counter(r for r, _n in SCREEN.values())
    included = [k for k, (r, _n) in SCREEN.items() if r == 'adjacent-adherence']
    latest = (prior.get('latestStatedCutoff') or {}).get('record')

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('篩的正是那 12 份（必觸發）',
          not unknown and not missing and len(SCREEN) == len(recent),
          '🚨 篩錯對象的結果與篩對的長得一樣；'
          '實得 %d 份，額外 %s，漏掉 %s'
          % (len(SCREEN), unknown or '無', missing or '無'))
    probe('每一筆的理由都在固定詞彙裡（必觸發之反向）',
          not bad_reason,
          '🚨 自創理由等於沒有分類；實得不在詞彙內者 %s' % (bad_reason or '無'))
    probe('四種理由都真的用到了（必觸發之反向）',
          set(tally) == set(REASONS),
          '⚠️ 沒用到的理由代表那一條從未被驗證；實得 %s，缺 %s'
          % (dict(tally), sorted(set(REASONS) - set(tally)) or '無'))
    # 🚨 這一道會紅：⚠️ 第 600 輪那個暫定值沒有通過篩選。
    probe('第 600 輪那個暫定的最新截止日，經篩選後仍成立',
          SCREEN.get(latest, ('', ''))[0] not in
          ('protocol-not-a-review', 'off-topic', 'excluded-by-protocol-drugs'),
          '🚨 該筆（%s）被判為 %s——⚠️ 它是計畫書，🚫 沒有結果，'
          '故「最新截止日 July 2026」撤回'
          % (latest, SCREEN.get(latest, ('？',))[0]))
    # 🚨 這一道也會紅：⚠️ 最新的 12 份裡沒有一份直接切題。
    probe('最新的那批裡有直接切題的回顧',
          any(r not in REASONS for r, _n in SCREEN.values()),
          '🚨 12 份中直接切題者 0 份（相鄰 %d 份、離題 %d 份、'
          '藥物 %d 份、計畫書 %d 份）；⚠️ 而成因見查詢構念那一條'
          % (tally.get('adjacent-adherence', 0), tally.get('off-topic', 0),
             tally.get('excluded-by-protocol-drugs', 0),
             tally.get('protocol-not-a-review', 0)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1c-screen-recent',
        'assignment': 'n+195：P3 第一步（篩選最新的一批）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'reasonVocabulary': REASONS,
        'screened': {k: {'reason': r, 'note': n} for k, (r, n) in SCREEN.items()},
        'tally': dict(tally),
        'adjacentKept': included,
        'directlyOnTopic': 0,
        'withdrawnHeadline': (
            '🚨 第 600 輪報的「最新自述截止日 July 2026」**撤回**：'
            '⚠️ 該筆是系統性回顧的**計畫書**，🚫 沒有結果。'
            '✅ 當時已標為暫定，而暫定的理由正是「尚未篩選」。'),
        'constructMismatch': CONSTRUCT_NOTE,
        'nextSearchSuggestion': [
            'dietary adherence', 'caloric restriction adherence',
            'energy restriction adherence', 'attrition', 'dropout',
            'compliance',
        ],
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3 第一步（篩選最新的 12 份）===')
    print('   判定分布：%s' % dict(tally))
    print('   ✅ 直接切題：0 份｜⚠️ 相鄰保留：%s' % included)
    print('   🚨 第 600 輪的最新截止日（%s）→ %s'
          % (latest, SCREEN.get(latest, ('？',))[0]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
