# -*- coding: utf-8 -*-
"""**選擇性報告偏差：本 run 第一次做得成一篇。**（第 654 輪）

## 🚨 38 份清冊的 `registryComparison` 全是 `pending`

⚠️ 即**把已發表結局對回試驗註冊**這件事——系統性回顧查選擇性報告的核心動作
——**🚫 本 run 從未做過。**

## ✅ 而材料其實早就在手上

私有根裡有 **212 筆 clinicaltrials.gov 紀錄**（含 `outcomesModule`），
🚨 只是從來沒有人把它們對回語料。**⚠️ 本支不送任何請求，只做本地連結。**

## ⚠️ 兩條連結路徑，結果差很多

| 路徑 | 結果 |
|---|---|
| **甲：靠 PMID**（註冊紀錄引用的論文） | 87／212 筆帶 PMID、相異 432 個——**🚨 與語料交集 0** |
| **乙：靠論文全文裡寫的 NCT 編號** | **✅ 3 篇**（正是 n+192 記的 3/41） |

🚨 而那 3 個 NCT 裡**只有 1 個已在抓回的 212 筆內**——
⚠️ 另 2 個要取得就得送外部請求，**🚫 本室不自行開跑。**

## ✅ 故本支能做的是「一篇」——而一篇也是零的相反

## 🚫 本支不送外部請求、不改任何清冊、不輸出註冊或論文的敘述文字
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
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n654_registry_linkage.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'

NCT = re.compile(r'NCT\d{8}', re.IGNORECASE)
FAKE_NCT = 'NCT00000000'


def main():
    records = json.loads(
        (RUN / 'sources/clinicaltrials-gov/records.json')
        .read_text(encoding='utf-8'))
    by_nct = {}
    pmid_to_nct = {}
    for record in records:
        protocol = record.get('protocolSection') or {}
        nct = (protocol.get('identificationModule') or {}).get('nctId')
        if nct:
            by_nct[nct] = record
        for reference in ((protocol.get('referencesModule') or {})
                          .get('references') or []):
            if isinstance(reference, dict) and reference.get('pmid'):
                pmid_to_nct.setdefault(str(reference['pmid']), []).append(nct)

    pool = {r['candidateId']: r for r in json.loads(
        (RUN / 'candidate-pool/candidates.json').read_text(encoding='utf-8'))}
    roster = corpus.acquired_roster()[0]

    # 甲：靠 PMID。
    via_pmid = []
    with_pmid = 0
    for candidate in roster:
        ids = (pool.get(candidate, {}).get('identifiers') or {}).get('pmid') or []
        ids = [str(x) for x in ids if x]
        if ids:
            with_pmid += 1
        for pmid in ids:
            if pmid in pmid_to_nct:
                via_pmid.append((candidate[-16:], pmid, pmid_to_nct[pmid]))

    # 乙：靠全文裡寫的 NCT。
    via_text = {}
    for candidate in roster:
        try:
            document = corpus.load_document(candidate)
        except Exception:  # noqa: BLE001
            continue
        text = ' '.join((s.title or '') + ' ' + (s.text or '')
                        for s in document.sections)
        hits = sorted({m.upper() for m in NCT.findall(text)})
        if hits:
            via_text[candidate[-16:]] = hits
    # 🚨 必觸發之反向：⚠️ 一個不可能存在的 NCT 不得對上任何紀錄。
    fake_matches = FAKE_NCT in by_nct

    in_hand = {report: [n for n in ncts if n in by_nct]
               for report, ncts in via_text.items()}
    comparable = {r: n for r, n in in_hand.items() if n}

    # 對得成的那些，逐篇比。
    comparisons = []
    for report, ncts in comparable.items():
        record = by_nct[ncts[0]]
        outcomes_module = (record['protocolSection'].get('outcomesModule')
                           or {})
        registered_primary = len(outcomes_module.get('primaryOutcomes') or [])
        registered_secondary = len(
            outcomes_module.get('secondaryOutcomes') or [])
        declared = in_scope = 0
        refs = collections.Counter()
        for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
            if 'batches' in str(path):
                continue
            doc = json.loads(path.read_text(encoding='utf-8'))
            if not doc['report'].endswith(report):
                continue
            items = doc.get('reportedOutcomes') or []
            declared = len(items)
            in_scope = sum(1 for o in items
                           if (o.get('scopeDecision') or {}).get('inScope'))
            refs.update(o.get('normalisedOutcomeRef') for o in items
                        if (o.get('scopeDecision') or {}).get('inScope'))
        comparisons.append({
            'report': report, 'nct': ncts[0],
            'registeredPrimary': registered_primary,
            'registeredSecondary': registered_secondary,
            'declaredInInventory': declared,
            'inScope': in_scope,
            'inScopeRefs': dict(refs),
            'hasResultsInRegistry': record.get('hasResults'),
        })

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('註冊紀錄與語料都讀得到（必觸發之正對照）',
          len(by_nct) > 100 and len(roster) == 41,
          '🚨 註冊紀錄 %d 筆、語料 %d 篇；⚠️ 任一為零，本支說什麼都沒有意義'
          % (len(by_nct), len(roster)))
    probe('假的 NCT 不得對上任何紀錄（必觸發之反向）',
          not fake_matches,
          '🚨 以 %s 試；⚠️ 若它也對得上，「對上 N 篇」就沒有意義' % FAKE_NCT)
    probe('全文裡真的抓得到 NCT（必觸發之正對照）',
          len(via_text) > 0,
          '🚨 抓到 %d 篇；⚠️ 若為零，路徑乙就沒有被測到' % len(via_text))
    # 🚨 以下三道是現況。
    probe('靠 PMID 就連得起來',
          bool(via_pmid),
          '🚨 語料 %d／41 篇有 PMID，而註冊紀錄引用的 %d 個 PMID 裡'
          '**一個都不是**——⚠️ 即這條路徑在本語料上完全無效'
          % (with_pmid, len(pmid_to_nct)))
    probe('全文寫了 NCT 的那幾篇，註冊紀錄都已在手',
          all(in_hand[r] for r in via_text),
          '🚨 %d 篇寫了 NCT，其中 %d 篇的紀錄已在抓回的 %d 筆內；'
          '⚠️ 其餘要取得就得送外部請求，🚫 本室不自行開跑'
          % (len(via_text), len(comparable), len(by_nct)))
    probe('每一篇語料都做得成選擇性報告比對',
          len(comparable) == len(roster),
          '🚨 做得成的 %d／%d 篇——⚠️ 而 38 份清冊的 registryComparison '
          '至今全是 pending' % (len(comparable), len(roster)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'registry-linkage',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'registryRecordsInHand': len(by_nct),
        'recordsWithLinkedPmids': len(
            {n for ncts in pmid_to_nct.values() for n in ncts}),
        'distinctLinkedPmids': len(pmid_to_nct),
        'corpusWithPmid': with_pmid,
        'linkedViaPmid': via_pmid,
        'linkedViaFullTextNct': via_text,
        'nctRecordsAlreadyInHand': in_hand,
        'comparisons': comparisons,
        'headline': (
            '🚨 靠 PMID 連結：**交集 0**（語料 %d/41 有 PMID，'
            '註冊紀錄引用 %d 個 PMID，一個都不是）。'
            '✅ 靠全文裡的 NCT：**3 篇**（正是 n+192 記的 3/41）——'
            '⚠️ 而其中**只有 1 篇**的註冊紀錄已在手，'
            '**🚨 故本 run 今天做得成的選擇性報告比對，是 1／41。**'
            % (with_pmid, len(pmid_to_nct))),
        'whatThisCannotSay': (
            '🚫 「主要結局有報」不等於「沒有選擇性報告」——'
            '⚠️ 註冊登記本身可能不完整，且本支只比得了一篇。'
            '🚨 而「論文報得比註冊多」是**另一個方向**的訊號'
            '（未預先登記的結局），🚫 本支不判它是不是問題。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n654 註冊連結與選擇性報告 ===')
    print('   註冊紀錄在手 %d 筆｜語料 %d 篇（%d 篇有 PMID）'
          % (len(by_nct), len(roster), with_pmid))
    print('   路徑甲（PMID）：對上 %d 篇' % len({v[0] for v in via_pmid}))
    print('   路徑乙（全文 NCT）：%s' % json.dumps(via_text, ensure_ascii=False))
    print('   其中註冊紀錄已在手者：%s'
          % json.dumps({k: v for k, v in in_hand.items() if v},
                       ensure_ascii=False))
    for row in comparisons:
        print('   ── %s ↔ %s' % (row['report'], row['nct']))
        print('      註冊：主要 %d 個｜次要 %d 個｜註冊端有結果=%s'
              % (row['registeredPrimary'], row['registeredSecondary'],
                 row['hasResultsInRegistry']))
        print('      論文：宣告 %d 項｜在範圍內 %d 項 %s'
              % (row['declaredInInventory'], row['inScope'],
                 row['inScopeRefs']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
