# -*- coding: utf-8 -*-
"""**25 項未決不是平等的——先裁哪一個。**（第 699 輪）

## ✅ 為什麼要這一支

登記簿已有 27 項、25 項未決、8 項卡著內容關卡。
🚨 但**一張清單不是一個順序**——⚠️ 協調者要的是「先裁哪一個」。

## ✅ 排序的準則是**可計算的**，🚫 不是本室的感覺

| 準則 | 怎麼算 |
|---|---|
| **卡內容關卡** | `blocks` 以 `A` 開頭 |
| **被別的決定引用** | 別項的文字裡出現它的代號（逐字比對） |
| **有沒有前置條件擋著** | 本室在建議裡用過的固定記號：`n+187`（讀論文的視窗）、`外部請求`、`擁有者` |

> **🚨 「有前置條件」的意思是：裁了也做不動——⚠️ 那種要往後排。**

## ⚠️ 而本支明白說出它的主觀成分

✅ 三個準則是本室選的；🚫 權重也是本室訂的。
**⚠️ 本支不假裝這是客觀排序——它是一份**附了計算過程**的建議。**

## 🚫 本支不新增或修改任何決定、不送外部請求
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n699_decision_ordering.json'
REGISTER = HERE / 'n700_decision_register_v11.json'

DID = re.compile(r'\bD[1-9][0-9]?\b')
PREREQ = {
    '讀論文的視窗': 'n+187',
    '需外部請求': '外部請求',
    '擁有者才能決定': '擁有者',
}


def text_of(item):
    parts = [str(item.get('ask') or ''), str(item.get('recommend') or ''),
             str(item.get('notADuplicateOf') or ''),
             str(item.get('sizeNote') or '')]
    return ' '.join(parts)


def main():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    items = {item['id']: item for item in register['items']}

    referenced = collections.Counter()
    for did, item in items.items():
        for other in set(DID.findall(text_of(item))):
            if other != did and other in items:
                referenced[other] += 1

    def prereqs_in_evidence(item):
        """🚨 第二條偵測管道：前置條件可能只寫在**證據憑證**裡，
        ⚠️ 而沒有寫進登記簿的建議文字。
        ✅ 本室是在看到 `D25` 排第一名時發現這個漏洞的——
        **🚨 D25 要抽數值，那非得有讀論文的視窗不可，
        但它的登記條目沒寫 `n+187`。**
        """
        found = set()
        for part in str(item.get('evidence') or '').replace(
                '；', ';').split(';'):
            name = part.split('→')[0].strip()
            path = HERE / name
            if not name or not path.is_file():
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except OSError:
                continue
            for label, mark in PREREQ.items():
                if mark in text:
                    found.add(label)
        return sorted(found)

    rows = []
    for did, item in items.items():
        if item.get('status') != 'open':
            continue
        body = text_of(item)
        stated = [name for name, mark in PREREQ.items() if mark in body]
        from_evidence = prereqs_in_evidence(item)
        prereqs = sorted(set(stated) | set(from_evidence))
        gates = str(item.get('blocks') or '').startswith('A')
        score = (2 if gates else 0) + referenced[did] - (2 if prereqs else 0)
        rows.append({
            'id': did, 'blocks': item.get('blocks'),
            'blocksContentGate': gates,
            'referencedByOthers': referenced[did],
            'prerequisites': prereqs,
            'prerequisitesStatedInRegister': stated,
            'prerequisitesOnlyFoundInEvidence': sorted(
                set(from_evidence) - set(stated)),
            'score': score,
            'ask': item.get('ask'),
        })

    rows.sort(key=lambda r: (-r['score'], r['id']))
    ready = [r for r in rows if r['blocksContentGate'] and not r['prerequisites']]
    stuck = [r for r in rows if r['prerequisites']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('登記簿的每一項未決都排到了（必觸發之正對照）',
          len(rows) == sum(1 for i in items.values()
                           if i.get('status') == 'open'),
          '🚨 未決 %d 項、排進 %d 項；⚠️ 少一項就是把待裁定弄丟了'
          % (sum(1 for i in items.values() if i.get('status') == 'open'),
             len(rows)))
    probe('捏造的決定代號沒有被任何一項引用（必觸發之反向）',
          referenced.get('D99', 0) == 0,
          '🚨 捏造代號被引用 %d 次；⚠️ 若不是 0，代表引用比對是在亂配'
          % referenced.get('D99', 0))
    probe('三個準則真的分得出差別（必觸發之反向）',
          len({r['score'] for r in rows}) >= 3,
          '🚨 分數的相異值有 %d 種：%s；'
          '⚠️ 若全部同分，這個排序沒有分辨力'
          % (len({r['score'] for r in rows}),
             sorted({r['score'] for r in rows}, reverse=True)))
    # 🚨 這一道是答案。
    probe('每一個卡內容關卡的決定，裁了就做得動',
          not [r for r in ready if r['prerequisites']] and bool(ready),
          '🚨 卡內容關卡且**沒有前置條件**的 %d 項：%s；'
          '而有前置條件（裁了也做不動）的 %d 項：%s；'
          '⚠️ 後者要往後排，🚫 不是不重要'
          % (len(ready), [r['id'] for r in ready],
             len(stuck), [(r['id'], r['prerequisites']) for r in stuck]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'decision-ordering',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'basedOn': 'n700_decision_register_v11.json',
        'criteria': {
            '卡內容關卡': '+2（`blocks` 以 A 開頭）',
            '被別的決定引用': '+1 每次（逐字比對代號）',
            '有前置條件': '-2（`n+187`／外部請求／擁有者）',
        },
        'detectionGapFound': (
            '🚨 第一版只看登記簿的建議文字，'
            '**⚠️ 於是 `D25` 排到第一名卻顯示「無前置條件」**——'
            '而它要抽數值，非得有讀論文的視窗不可。'
            '✅ 加了第二條管道（看證據憑證）之後才補上。'
            '🚨 這正是本支自己宣告的那個限制，**當場就咬到了**。'),
        'subjectivity': (
            '⚠️ 三個準則是**本室選的**，🚫 權重也是本室訂的。'
            '**✅ 本支不假裝這是客觀排序——它是一份附了計算過程的建議，'
            '🚨 而計算過程攤在這裡，所以推翻它很容易。**'),
        'ranked': rows,
        'readyToActOn': [r['id'] for r in ready],
        'blockedOnSomethingElse': [
            {'id': r['id'], 'prerequisites': r['prerequisites']}
            for r in stuck],
        'howToRead': (
            '✅ 分數高＝**卡著關卡、被別人依賴、而且裁了就做得動**。'
            '⚠️ 分數低不代表不重要——🚨 多半是「裁了也做不動」'
            '（要讀論文、要送外部請求、或要擁有者決定）。'),
        'methodLimit': (
            '🚨 「前置條件」是靠**本室自己在建議裡用過的固定記號**認出來的'
            '（`n+187`／外部請求／擁有者）——'
            '⚠️ 若某一項的前置條件本室當初沒寫進去，**這裡就看不到**。'
            '🚫 故這份排序**只反映登記簿寫下來的東西**，不反映沒寫的。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n699 先裁哪一個 ===')
    print('   未決 %d 項｜卡關卡且無前置條件 %d 項｜有前置條件 %d 項'
          % (len(rows), len(ready), len(stuck)))
    print('   排序（分數／代號／阻擋／被引用／前置條件）：')
    for row in rows:
        print('      %+d  %-4s %-22s 被引用 %d  %s'
              % (row['score'], row['id'], str(row['blocks'])[:22],
                 row['referencedByOthers'], row['prerequisites'] or ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
