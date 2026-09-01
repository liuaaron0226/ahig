# -*- coding: utf-8 -*-
"""**擁有者簡報那三個數，今天沒有任何東西在核對。**（第 651 輪）

## 🚨 第 650 輪的掃描留下一個真的訊號

`n521_owner_briefing_crosscheck` 抽取失敗，並且**拒絕回報「無不符」**
——⚠️ 那正是它設計時就寫明的行為。

✅ 追下去發現是**好消息**：簡報已經改寫，不再用它抓的那個句式，
**🚨 而且新版自己把兩個分母講清楚了**（「🚫 不可以把 7 去除以 15」）——
⚠️ 即 n521 當初要防的母體混用，已經修掉。

> **🚨 但後果是：那三個數字現在沒有任何東西在核對。**
> **⚠️ 而擁有者正要據以決定「要不要花錢或動用圖書館」。**

## ✅ 本支做兩件事

| | |
|---|---|
| **甲** | 把守衛對著**現行措辭**重新架起來（表格列，不是舊句式） |
| **乙** | 三個數各自實算一次：**抽出 15／其中拿到 3／該層在手 7** |

## 🚨 保留 n521 那道最要緊的控制

**⚠️ 一個抓不到句子的抽取器，會安靜地回報「無不符」。**
✅ 故先對**注入版**跑一次（把 15 改成 99），🚨 抓不到就拒絕報告。

## 🚫 本支不改簡報——⚠️ 那是協調者的產物；本支只對帳並回報
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

S = Path(__file__).resolve().parent
OUT = S / 'n651_owner_briefing_recheck.json'
BRIEFING = REPO / 'docs/m1-owner-briefing.md'

GI_POOL_HINT = 'gi'

# ⚠️ 對著**現行**措辭（表格列）。🚨 樣式字面裡不得有控制字元。
ROW_SAMPLED = re.compile(
    r'當初照設計抽出來的那批，這一類抽了幾篇？\s*\|\s*\*\*(\d+)\*\*\s*篇')
ROW_OBTAINED = re.compile(
    r'那批裡實際拿到全文的\*\*\s*\|\s*\*\*(\d+)\*\*\s*篇')
ROW_IN_HAND = re.compile(
    r'這一類我們手上總共有幾篇？\*\*\s*\|\s*\*\*(\d+)\*\*\s*篇')


def extract(text):
    return {
        'sampled': ROW_SAMPLED.search(text),
        'obtained': ROW_OBTAINED.search(text),
        'inHand': ROW_IN_HAND.search(text),
    }


def main():
    text = BRIEFING.read_text(encoding='utf-8')
    found = extract(text)
    stated = {k: (int(m.group(1)) if m else None) for k, m in found.items()}

    # 🚨 必觸發：⚠️ 注入版必須抓得到，否則本支的「相符」毫無意義。
    injected = text.replace(
        '| 當初照設計抽出來的那批，這一類抽了幾篇？ | **15** 篇 |',
        '| 當初照設計抽出來的那批，這一類抽了幾篇？ | **99** 篇 |')
    injected_value = extract(injected)['sampled']
    injection_caught = (injected_value is not None
                        and injected_value.group(1) == '99')

    # 乙：三個數各自實算。
    calibration = json.loads(
        (S / 'm1_step2_calibration_set.json').read_text(encoding='utf-8'))
    assignment = json.loads(
        (S / 'm1_step2_assignment.json').read_text(encoding='utf-8'))
    roster = set(corpus.acquired_roster()[0])

    gi_pools = [pool for pool in calibration['draws']
                if GI_POOL_HINT in pool.lower()]
    # 🚨 本支第一版寫成「把 dict 裡任何字串清單都當候選」——
    # ⚠️ 而抽籤紀錄裡除了 `candidateIds`（15 筆）還有 `strata`（2 個層別名稱），
    # 於是算出 17，**差點把簡報的 15 報成錯的**。
    # **✅ 只讀 `candidateIds`：欄位名寫在那裡，不必猜。**
    sampled_ids = []
    for pool in gi_pools:
        draw = calibration['draws'][pool]
        ids = draw.get('candidateIds') if isinstance(draw, dict) else draw
        sampled_ids.extend(v for v in (ids or []) if isinstance(v, str))
    sampled_ids = sorted(set(sampled_ids))
    quota = sum(calibration['draws'][pool].get('quota', 0)
                for pool in gi_pools
                if isinstance(calibration['draws'][pool], dict))

    assigned_gi = sorted(cid for cid, pool in assignment['assignment'].items()
                         if GI_POOL_HINT in str(pool).lower())

    computed = {
        'sampled': len(sampled_ids),
        'obtained': len(set(sampled_ids) & roster),
        'inHand': len(set(assigned_gi) & roster),
    }

    mismatches = [k for k in stated
                  if stated[k] is not None and stated[k] != computed[k]]
    unextractable = [k for k, v in stated.items() if v is None]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('🚨 注入版必須抓得到（必觸發之反向）',
          injection_caught,
          '🚨 把 15 改成 99 後抽取器%s抓到；'
          '⚠️ **一個抓不到句子的抽取器會安靜地回報「無不符」**——'
          '抓不到即拒絕報告（n521 的教訓）'
          % ('' if injection_caught else '**沒有**'))
    probe('三句都抽得到（必觸發之正對照）',
          not unextractable,
          '🚨 抽不到的：%s；⚠️ 若抽不到，代表措辭又改了——'
          '**🚫 那時候不得當成「無不符」**' % unextractable)
    probe('GI 層的抽出集合非空（必觸發之正對照）',
          len(sampled_ids) > 0 and bool(gi_pools),
          '🚨 GI 池 %s、抽出 %d 篇；⚠️ 若為零，下面三個實算都沒有意義'
          % (gi_pools, len(sampled_ids)))
    probe('抽出篇數等於配額（必觸發之正對照）',
          len(sampled_ids) == quota,
          '🚨 candidateIds %d 筆 vs quota %d；'
          '⚠️ 對不上就代表本支又讀錯欄位——'
          '**本支第一版把 `strata` 那兩個層別名稱也算成候選，得出 17**'
          % (len(sampled_ids), quota))
    # 🚨 這一道是答案。
    probe('簡報所寫的三個數與實算相符',
          not mismatches and not unextractable,
          '%s 不符：%s；明細 簡報=%s／實算=%s'
          % ('✅' if not mismatches and not unextractable else '🚨',
             mismatches or '無', stated, computed))

    doc = {
        'schemaVersion': 1,
        'documentType': 'owner-briefing-recheck',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'why': (
            '🚨 第 650 輪查明 n521 因措辭改寫而抽取失敗——'
            '✅ 而它**拒絕回報「無不符」**，正是設計時寫明的行為。'
            '⚠️ 追下去是好消息：簡報已自行把兩個分母講清楚，'
            '**🚨 但後果是那三個數字現在沒有任何東西在核對。**'),
        'briefing': str(BRIEFING.relative_to(REPO)).replace('\\', '/'),
        'statedInBriefing': stated,
        'computedFromData': computed,
        'giPools': gi_pools,
        'quota': quota,
        'myOwnBugFirstTime': (
            '🚨 本支第一版把抽籤紀錄裡任何字串清單都當成候選，'
            '⚠️ 於是把 `strata` 的兩個層別名稱也算進去，得出 17——'
            '**🚫 差點把簡報正確的 15 報成錯的**。'
            '✅ 改成只讀 `candidateIds`（欄位名就寫在那裡，不必猜）。'),
        'mismatches': mismatches,
        'unextractable': unextractable,
        'supersedes': (
            '⚠️ n521 的抽取器對的是舊句式，🚫 本支不改寫 n521（已上看板）；'
            '✅ 本支是對著**現行措辭**的新守衛。'),
        'whatThisCannotSay': (
            '🚫 本支不判斷簡報**該不該**用這三個數——⚠️ 那是協調者與擁有者的事；'
            '✅ 它只回答「寫上去的那三個數，跟資料算出來的一不一樣」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n651 擁有者簡報三個數的重新核對 ===')
    print('   GI 池：%s｜抽出 %d 篇' % (gi_pools, len(sampled_ids)))
    print('   %-10s %8s %8s' % ('項目', '簡報寫', '實算'))
    for key, label in (('sampled', '抽出'), ('obtained', '其中拿到'),
                       ('inHand', '該層在手')):
        print('   %-10s %8s %8s  %s'
              % (label, stated[key], computed[key],
                 '✅' if stated[key] == computed[key] else '🚨'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
