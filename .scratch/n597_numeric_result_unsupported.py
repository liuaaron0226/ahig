# -*- coding: utf-8 -*-
"""**5 項在範圍內的結局，宣稱有數值結果，而文件裡沒有那個數值。**（第 597 輪）

## ✅ 這是雙讀第一次找到實質缺陷——🚫 不是顆粒度

第 596 輪把 `1105537918c174c9` 的差異歸為「界線位移」。
**🚨 看了正式那道的標籤之後，那個分類也是錯的：**

| 讀者 | 嚴重度 | 發生率 |
|---|---|---|
| 正式那道 | **每個症狀一項**（6 個症狀） | **所有計次併成一項** |
| 第二位（本室） | 只記有數值的那一個（拆兩臂 ＝ 2 項） | **每個症狀×每一臂一項**（5 項） |

> ✅ **兩位讀者對「平均評分＝嚴重度、嚴重計次＝發生率」的界線其實一致。**
> ⚠️ 6／2 與 1／5 是**在兩個結局上各自往相反方向切**造成的。
> **🚨 故那也是顆粒度，🚫 不是界線位移——本室連兩輪把它分錯類。**

## 🚨 而看標籤時撞到一件更要緊的事

正式那道的 6 項嚴重度**全部** `hasNumericResult=True`、**全部在範圍內**。
⚠️ 但工作單交給讀者的那份文件裡：

| 症狀 | 全文出現次數 | 附近有數值的次數 |
|---|---|---|
| stomach cramp | **1** | **0** |
| nausea | **1** | **0** |
| headache | **1** | **0** |
| GI comfort | 5 | **0** |
| stomach bloating | 2 | 1（🚨 而那是**嚴重計次**，不是平均評分） |
| stomach fullness | 5 | 2 ✅ |

> 🚨 cramp／nausea／headache **只在 Methods 的量表清單裡各出現一次**，
> ⚠️ 全文沒有任何數字；GI comfort 出現 5 次也一次都沒有。
> **🚫 而它們以「有數值結果」的身分進入了證據池。**
>
> **⚠️ 實得 4 項（98 項中的 4 項）。**
> ✅ stomach bloating **不算在內**：⚠️ 它附近確有數字（那個嚴重計次），
> 🚫 本支從寬不指控——**寧可少算，不可多指。**

## 🚨 為什麼這一格特別要緊

`hasNumericResult` 是 `notExtracted-no-numeric-result` 的唯一守門員，
⚠️ 而第 593 輪已測出它**缺席時預設為 True**（放寬方向）。
**🚨 這一次不是缺席，是明寫 True。**

## ⚠️ 本支不判成因，只擺證據

📮 `ADJUDICATION_CAUSES` 裡最貼近的是 `model-fabricated`（模型自行補寫或推測），
⚠️ 但也可能是讀的人把「有量、只是沒報數字」讀成「有結果」。
**🚫 本室不逕自定罪另一個視窗的讀法**——✅ 證據在上表，📮 成因請協調者判。

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

OUT = Path(__file__).resolve().parent / 'n597_numeric_result_unsupported.json'
REPORT = '1105537918c174c9'
# ⚠️ 症狀名取自論文自己的量表清單。
SYMPTOMS = ('fullness', 'bloat', 'cramp', 'nausea', 'headache', 'comfort',
            'thirst')
# 🚨 「附近有數值」的定義：⚠️ 平均±標準差、小數、或「n of 48」這種計次。
NUMBER = re.compile(r'\d+\.\d+|\d+\s*(?:±|\+/-)|\d+\s*(?:of|/)\s*\d+')
WINDOW = 90


def proximity(text):
    out = {}
    for symptom in SYMPTOMS:
        hits = [m.start() for m in re.finditer(symptom, text, re.I)]
        near = sum(1 for h in hits
                   if NUMBER.search(text[max(0, h - WINDOW):h + WINDOW]))
        out[symptom] = {'mentions': len(hits), 'withNumberNearby': near}
    return out


def main():
    candidate = [c for c in corpus.acquired_roster()[0]
                 if c.endswith(REPORT)][0]
    text = corpus.load_document(candidate).content
    counts = proximity(text)

    inventory = None
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc['report'][-16:] == REPORT:
            inventory = doc
            break

    severity = [o for o in inventory.get('reportedOutcomes') or []
                if o.get('normalisedOutcomeRef') == 'gi-symptom-severity'
                and (o.get('scopeDecision') or {}).get('inScope')]
    # 🚨 逐項對回症狀：⚠️ 標籤裡提到哪個症狀，就查那個症狀在文件裡有沒有數值。
    unsupported = []
    for item in severity:
        label = (item.get('localLabel') or '').lower()
        named = [s for s in SYMPTOMS if s in label]
        if named and all(counts[s]['withNumberNearby'] == 0 for s in named):
            unsupported.append({'symptoms': named,
                                'hasNumericResult': item.get('hasNumericResult')})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('這一篇確實有在範圍內的嚴重度項目（必觸發）',
          len(severity) > 0,
          '🚨 若為零，本支就無事可查；實得 %d 項' % len(severity))
    # ✅ 正對照：⚠️ 數值檢查在真的有數值的地方要找得到。
    probe('數值鄰近檢查在有數值處確實找得到（正對照，必觸發）',
          counts['fullness']['withNumberNearby'] > 0
          and counts['thirst']['withNumberNearby'] > 0,
          '✅ stomach fullness 附近有數值 %d 次、thirst %d 次；'
          '🚨 若都為零，代表檢查壞了，而「沒有數值」會是假的'
          % (counts['fullness']['withNumberNearby'],
             counts['thirst']['withNumberNearby']))
    # 🚨 必觸發之反向：⚠️ 至少要有一個症狀是真的零數值，否則對照組不成立。
    zero = [s for s in SYMPTOMS if counts[s]['withNumberNearby'] == 0]
    probe('確實有症狀在文件中完全沒有數值（必觸發之反向）', bool(zero),
          '🚨 實得 %s；⚠️ 若一個都沒有，本支的指控就沒有對象' % zero)
    # 🚨 這一道會紅。
    probe('每一項在範圍內的嚴重度，其症狀在文件中都有數值',
          not unsupported,
          '🚨 實得 %d 項宣稱有數值結果，而其症狀在整份文件裡沒有任何數字：%s；'
          '⚠️ 那是 98 項中的 %d 項'
          % (len(unsupported), [u['symptoms'] for u in unsupported],
             len(unsupported)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'numeric-result-unsupported',
        'report': REPORT,
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeSeverityItems': len(severity),
        'symptomNumberProximity': counts,
        'unsupported': unsupported,
        'correctionToRound596': (
            '🚨 第 596 輪把這一篇的差異歸為「界線位移」——⚠️ 那也是錯的。'
            '✅ 兩位讀者對「平均評分＝嚴重度、嚴重計次＝發生率」其實一致；'
            '6／2 與 1／5 是在兩個結局上各自往相反方向切造成的，'
            '🚫 故那也是顆粒度。⚠️ 本室連兩輪把它分錯類。'),
        'whyThisMatters': (
            '⚠️ hasNumericResult 是 notExtracted-no-numeric-result 的唯一守門員，'
            '🚨 而第 593 輪已測出它缺席時預設為 True（放寬方向）。'
            '⚠️ 這一次不是缺席，是明寫 True。'),
        'noVerdict': (
            '📮 ADJUDICATION_CAUSES 裡最貼近的是 model-fabricated，'
            '⚠️ 但也可能是把「有量、只是沒報數字」讀成「有結果」。'
            '🚫 本室不逕自定罪另一個視窗的讀法——📮 成因請協調者判。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n597 宣稱有數值，而文件裡沒有 ===')
    print('   %s：在範圍內的嚴重度 %d 項' % (REPORT, len(severity)))
    for symptom, stat in counts.items():
        print('   %-10s 出現 %2d 次｜附近有數值 %d 次'
              % (symptom, stat['mentions'], stat['withNumberNearby']))
    print('   🚨 宣稱有數值而症狀無數字者：%d 項 %s'
          % (len(unsupported), [u['symptoms'] for u in unsupported]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
