# -*- coding: utf-8 -*-
"""**P3 那張表自己寫了警語，卻在自己的計數裡違反它。**（第 686 輪）

## 🚨 `p3_step1i_table.json` 的 `chainWarning` 寫著

> 「36768088 與 39763344 是同一條線的前後兩版（後者自述為 update）。
> ⚠️ 合成時**不得當成兩筆獨立證據**——✅ 與 B.11 那條『研究 vs 論文』是同一個問題。」

**🚨 但同一份文件的 `countsBySide` 與 `countsByDirection` 加起來都是 6——
⚠️ 正好把那一對算成兩筆。**

## ✅ 而去重之後，標題數字會變

⚠️ 原表：`favourable 3／mixed 2／null 1`。
🚨 把同一條線收成一筆之後：**`favourable 2／mixed 2／null 1`**——
**⚠️ 從「有利方向是多數」變成「2 比 2 平手，另有 1 筆無差別」。**

## ⚠️ 順帶記一件原文的事

`39763344` 的檢索截止日逐字是 **`31 April 2023`**——**🚨 四月沒有 31 日。**
✅ 本支**照原文記下並標記**，🚫 不自行更正（n+195：不得用「大概是那幾年」補）。

## 🚫 本支不改那張凍結的表（更正另存），🚫 不送外部請求、不輸出私有數字
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n686_p3_chained_pair_errata.json'
TABLE = HERE / 'p3_step1i_table.json'

MONTH_DAYS = {'january': 31, 'february': 29, 'march': 31, 'april': 30,
              'may': 31, 'june': 30, 'july': 31, 'august': 31,
              'september': 30, 'october': 31, 'november': 30,
              'december': 31}


def impossible_dates(rows):
    """🚨 只認「日數超過該月上限」這一種，🚫 不做其他推測。"""
    bad = {}
    for key, row in rows.items():
        text = str(row.get('cutoff') or '')
        parts = text.split()
        if len(parts) >= 2 and parts[0].isdigit():
            day = int(parts[0])
            limit = MONTH_DAYS.get(parts[1].lower())
            if limit and day > limit:
                bad[key] = {'asWritten': text, 'monthMaxDays': limit}
    return bad


def main():
    table = json.loads(TABLE.read_text(encoding='utf-8'))
    rows = table['rows']
    pair = list(table['chainedPair'])

    def tally(keys):
        return (
            dict(collections.Counter(rows[k].get('side') for k in keys)),
            dict(collections.Counter(rows[k].get('direction') for k in keys)),
        )

    all_keys = list(rows)
    as_stored_side, as_stored_dir = tally(all_keys)

    # ✅ 同一條線收成一筆：留**較新的那一版**（自述為 update）。
    keep_of_pair = sorted(pair)[-1]
    collapsed_keys = [k for k in all_keys if k not in pair] + [keep_of_pair]
    collapsed_side, collapsed_dir = tally(collapsed_keys)

    bad_dates = impossible_dates(rows)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('那一對真的都在表裡（必觸發之正對照）',
          all(k in rows for k in pair) and len(pair) == 2,
          '🚨 chainedPair=%s，都在 rows 裡：%s；'
          '⚠️ 不在的話就沒有東西可收合' % (pair, all(k in rows for k in pair)))
    # 🚨 這一道證明本支重算的方法與原表一致，⚠️ 否則後面的差異可能是本支算錯。
    probe('不收合時，本支重算的數字與原表完全相同（必觸發之正對照）',
          as_stored_side == table['countsBySide']
          and as_stored_dir == table['countsByDirection'],
          '🚨 重算 side=%s／dir=%s；原表 side=%s／dir=%s；'
          '⚠️ 對不上代表差異來自本支算錯，🚫 不是原表的問題'
          % (as_stored_side, as_stored_dir,
             table['countsBySide'], table['countsByDirection']))
    probe('收合真的少掉一列（必觸發之反向）',
          len(collapsed_keys) == len(all_keys) - 1,
          '🚨 原 %d 列 → 收合後 %d 列；⚠️ 沒少的話收合等於沒做'
          % (len(all_keys), len(collapsed_keys)))
    # 🚨 這一道是答案。
    probe('原表的計數已經把同一條線的兩版算成一筆',
          as_stored_dir == collapsed_dir,
          '🚨 原表 dir=%s；收合後 dir=%s；'
          '⚠️ 兩者不同就代表**原表的警語沒有套用到它自己的計數上**'
          % (as_stored_dir, collapsed_dir))

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-chained-pair-errata',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'correctsButDoesNotEdit': (
            '🚨 `p3_step1i_table.json` 是凍結產物——'
            '✅ 本支**另存更正**，🚫 不就地改它。'),
        'chainedPair': pair,
        'keptVersion': keep_of_pair,
        'keptBecause': '⚠️ 較新的那一版自述為 update，✅ 對「搜尋接續」也是它有效。',
        'asStored': {'rows': len(all_keys), 'countsBySide': as_stored_side,
                     'countsByDirection': as_stored_dir},
        'afterCollapsing': {'rows': len(collapsed_keys),
                            'countsBySide': collapsed_side,
                            'countsByDirection': collapsed_dir},
        'headlineChange': (
            '⚠️ 原表：`favourable %s／mixed %s／null %s`；'
            '🚨 收合後：`favourable %s／mixed %s／null %s`——'
            '**⚠️ 從「有利方向是多數」變成「平手，另有一筆無差別」。**'
            % (as_stored_dir.get('favourable'), as_stored_dir.get('mixed'),
               as_stored_dir.get('null'), collapsed_dir.get('favourable'),
               collapsed_dir.get('mixed'), collapsed_dir.get('null'))),
        'impossibleDatesAsWritten': bad_dates,
        'dateNote': (
            '🚨 `31 April 2023` 四月沒有 31 日。'
            '✅ 本支**照原文記下並標記**，🚫 不自行更正——'
            '⚠️ 那是逐字轉錄，改了就變成本室的推測（n+195）。'),
        'doesNotChange': (
            '✅ 搜尋接續點**不受影響**：接續點由最新的截止日決定'
            '（June 2023／July 2023），🚫 不是那一對。'),
        'whatThisIsNot': (
            '🚫 本支不重新判讀任何一篇回顧的方向，'
            '⚠️ 只是把**同一條線的兩版收成一筆**再數一次。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n686 P3 同線兩版的重複計數 ===')
    print('   原表 %d 列：side=%s｜dir=%s'
          % (len(all_keys), as_stored_side, as_stored_dir))
    print('   收合 %d 列：side=%s｜dir=%s'
          % (len(collapsed_keys), collapsed_side, collapsed_dir))
    print('   保留的版本：%s（較新、自述為 update）' % keep_of_pair)
    print('   🚨 原文即不存在的日期：%s' % (bad_dates or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
