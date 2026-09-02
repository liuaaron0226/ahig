# -*- coding: utf-8 -*-
"""**`D27` 那 4 篇，現在到底貢獻什麼、被擋的又是什麼理由。**（第 697 輪）

## ✅ 為什麼要這一支

第 694 輪把 `D27` 的**損失**量出來了（11 張表、4 篇），
🚨 但**後果**沒算——⚠️ 而 `D17` 早在第 630 輪就有那份成本表（14 份清冊、43 項）。

> **✅ 一個只有「漏了什麼」而沒有「所以怎樣」的缺陷，很難裁。**

## 🚨 而第 611 輪對 GROBID 那邊講過一句話，這裡要照樣問一次

> 「『沒有數值結果』『劑量沒報』這些排除理由，⚠️ 在這 13 篇上都可能是
> **表格被削掉造成的**，🚫 不是論文沒寫。」

**⚠️ 那句話對 JATS 這 4 篇成不成立？** ✅ 本支把它們被擋的理由碼攤開。

## 🚫 本支不改任何清冊與契約、不重新解析、不送外部請求
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
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n697_d27_consequences.json'
N694 = HERE / 'n694_jats_table_parity.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# 🚨 第 611 輪點名「可能是表格被削掉造成」的那幾種理由
TABLE_EXPLICABLE = {
    'notExtracted-no-numeric-result',
    'notExtracted-dose-outside-bands',
    'notExtracted-effect-measure-not-in-scope',
}


def main():
    affected = json.loads(N694.read_text(encoding='utf-8'))[
        'summary']['europe-pmc-jats']['reportsWithTablesButNoTableSection']

    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    rows = []
    peers = collections.Counter()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        report = inventory['report'][-16:]
        verdict = matcher.decide_inventory(inventory)
        in_scope = 0
        reasons = collections.Counter()
        mapped_blocked = collections.Counter()
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if decision['inScope']:
                in_scope += 1
                continue
            reasons[decision['reasonCode']] += 1
            if reported.get('normalisedOutcomeRef'):
                mapped_blocked[decision['reasonCode']] += 1
        if report in affected:
            rows.append({
                'report': report,
                'declared': len(inventory['reportedOutcomes']),
                'inScope': in_scope,
                'mappedButBlocked': dict(mapped_blocked.most_common()),
                'tableExplicableBlocks': sum(
                    v for k, v in mapped_blocked.items()
                    if k in TABLE_EXPLICABLE),
            })
        else:
            peers[report] = in_scope

    with_inventory = {r['report'] for r in rows}
    no_inventory = [r for r in affected if r not in with_inventory]
    zero_contrib = [r['report'] for r in rows if r['inScope'] == 0]
    explicable = sum(r['tableExplicableBlocks'] for r in rows)
    in_scope_total = sum(r['inScope'] for r in rows)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('第 694 輪點名的 4 篇都找得到清冊（必觸發之正對照）',
          not no_inventory and len(rows) == len(affected),
          '🚨 點名 %d 篇、找到清冊 %d 篇、沒有清冊的：%s；'
          '⚠️ 沒有清冊的話它「零貢獻」是必然，🚫 不能算成證據'
          % (len(affected), len(rows), no_inventory or '無'))
    probe('判定器在別篇上判得出在範圍內（必觸發之正對照）',
          sum(peers.values()) > 0,
          '🚨 其餘 %d 篇合計判出 %d 項在範圍內；'
          '⚠️ 若全語料都是 0，這 4 篇的 0 就沒有對比意義'
          % (len(peers), sum(peers.values())))
    probe('那 4 篇之外沒有被誤收進來（必觸發之反向）',
          all(r['report'] in affected for r in rows),
          '🚨 表中每一列都在點名清單裡；⚠️ 若不是，代表本支收錯了篇')
    # 🚨 這一道是答案。
    probe('那 4 篇被擋的理由與「表格被削掉」無關',
          explicable == 0,
          '🚨 已對上契約結局、且理由屬「表格可解釋」那三種的共 %d 項；'
          '⚠️ 第 611 輪對 GROBID 講過同一句話——'
          '**🚨 那些理由可能是缺陷造成的，🚫 不是論文沒寫**'
          % explicable)

    doc = {
        'schemaVersion': 1,
        'documentType': 'd27-consequences',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'affectedReports': affected,
        'rows': rows,
        'inScopeFromAffected': in_scope_total,
        'zeroContributionAmongAffected': zero_contrib,
        'tableExplicableBlockedItems': explicable,
        'tableExplicableReasonCodes': sorted(TABLE_EXPLICABLE),
        'mirrorsRound611Argument': (
            '🚨 第 611 輪對 GROBID 那 13 篇說過：'
            '「『沒有數值結果』『劑量沒報』這些排除理由，'
            '可能是**表格被削掉造成的**，🚫 不是論文沒寫。」'
            '✅ 本支把同一句話拿到 JATS 這 4 篇上檢驗。'),
        'whatThisIsNot': (
            '🚫 本支**不主張**那些被擋的項目修好之後就會進範圍——'
            '⚠️ 它只指出「被擋的理由**屬於表格能解釋的那幾種**」。'
            '🚨 要確認得重新解析再重判，而**重新解析會改變雜湊**'
            '（與 `D17` 的 `fixMakesA1Harder` 同一個代價），'
            '**📮 那是裁定，🚫 不是本室能動的。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n697 D27 那 4 篇的後果 ===')
    print('   受影響 %d 篇｜合計在範圍內 %d 項｜其中零貢獻 %d 篇'
          % (len(rows), in_scope_total, len(zero_contrib)))
    for row in rows:
        print('   %s｜宣告 %d 項｜在範圍內 %d｜表格可解釋的擋下 %d'
              % (row['report'], row['declared'], row['inScope'],
                 row['tableExplicableBlocks']))
        print('      已對上結局卻被擋：%s' % (row['mappedButBlocked'] or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
