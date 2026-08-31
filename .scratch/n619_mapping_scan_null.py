# -*- coding: utf-8 -*-
"""**n576 那個「零矛盾」，規則真的抓得到嗎？**（第 619 輪）

## 🚨 同一把尺，量本室另一個乾淨結果

第 576 輪掃過 98 項在範圍內的結局，**回報 0 項標籤／結局矛盾**。
⚠️ 當時證明了規則在**合成樣本**上打得中——
**🚫 但從未問過：拿真實標籤隨機配對，規則會亮幾次。**

> **🚨 若隨機配對也幾乎不亮，那個零就什麼都沒說**——
> ⚠️ 它只代表規則太窄，不代表資料乾淨。

## ✅ 做法：把（標籤，結局）配對打散

保持 98 個標籤與 98 個結局代碼不變，**只把兩者的對應關係洗牌**，
重跑 n576 的同一組規則，看亮幾次。⚠️ 固定種子、可複驗。

## ⚠️ 這一支不改 n576，也不重新判定任何一項
"""
import json
import random
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
OUT = HERE / 'n619_mapping_scan_null.json'
N576 = HERE / 'n576_mapping_contradictions.json'
SEED = 20260902
TRIALS = 400


def load_rules():
    """✅ 直接用 n576 憑證裡記下的規則，🚫 不重打一份。"""
    doc = json.loads(N576.read_text(encoding='utf-8'))
    return [(r['outcomeId'], r['contradictoryPattern'], r['rescuePattern'],
             r['why']) for r in doc['rules']]


def flags(pairs, rules):
    count = 0
    for ref, label in pairs:
        for outcome_id, bad, rescue, _why in rules:
            if ref != outcome_id:
                continue
            if not re.search(bad, label, re.I):
                continue
            if rescue and re.search(rescue, label, re.I):
                continue
            count += 1
    return count


def main():
    rules = load_rules()
    items = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for item in doc.get('reportedOutcomes') or []:
            if not (item.get('scopeDecision') or {}).get('inScope'):
                continue
            items.append((item.get('normalisedOutcomeRef'),
                          item.get('localLabel') or ''))

    observed = flags(items, rules)

    refs = [ref for ref, _label in items]
    labels = [label for _ref, label in items]
    rng = random.Random(SEED)
    null = []
    for _ in range(TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        null.append(flags(list(zip(refs, shuffled)), rules))
    null.sort()
    mean = sum(null) / len(null)
    zero_trials = sum(1 for n in null if n == 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('掃到的是那 98 項（必觸發）', len(items) == 98,
          '🚨 對不上就代表本支看的不是同一批；實得 %d 項' % len(items))
    probe('規則取自 n576 憑證（必觸發）', len(rules) >= 6,
          '✅ 取到 %d 條規則；🚨 重打一份規則等於換了一把尺' % len(rules))
    probe('觀察值與 n576 一致（必觸發）', observed == 0,
          '🚨 對不上代表本支重跑的不是同一件事；實得 %d 項' % observed)
    # 🚨 這一道的紅綠就是答案：⚠️ 規則在隨機配對下會不會亮。
    probe('規則在隨機配對下會亮（必觸發之反向）',
          mean > 0 and zero_trials < TRIALS,
          '⚠️ 虛無平均 %.1f 次、範圍 %d–%d，%d／%d 次為零；'
          '🚨 若隨機也幾乎不亮，那個「零矛盾」只代表規則太窄，'
          '🚫 不代表資料乾淨'
          % (mean, null[0], null[-1], zero_trials, TRIALS))

    doc = {
        'schemaVersion': 1,
        'documentType': 'mapping-scan-null',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'seed': SEED, 'trials': TRIALS,
        'inScopeItems': len(items),
        'rules': len(rules),
        'observedFlags': observed,
        'nullMean': round(mean, 2),
        'nullRange': [null[0], null[-1]],
        'nullZeroTrials': zero_trials,
        'nullPercentiles': {'p50': null[len(null) // 2],
                            'p95': null[int(len(null) * 0.95)]},
        'whatThisTests': (
            '✅ 只問一件事：第 576 輪那個「0 項矛盾」，'
            '🚨 是資料乾淨，還是規則根本不會亮。'
            '⚠️ 做法是保持標籤與結局代碼不變，只洗牌兩者的對應關係。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n619 零矛盾的虛無分布 ===')
    print('   在範圍內 %d 項｜規則 %d 條｜觀察 %d 項矛盾'
          % (len(items), len(rules), observed))
    print('   虛無（%d 次、種子 %d）：平均 %.1f｜中位數 %d｜第 95 百分位 %d｜範圍 %d–%d'
          % (TRIALS, SEED, mean, null[len(null) // 2],
             null[int(len(null) * 0.95)], null[0], null[-1]))
    print('   隨機配對下完全不亮的次數：%d／%d' % (zero_trials, TRIALS))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
