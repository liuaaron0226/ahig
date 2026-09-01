# -*- coding: utf-8 -*-
"""**清冊綁的那份契約與那份文本，今天還對得上嗎。**（第 630 輪）

## 🚨 本 run 從未查過的一層：綁定

⚠️ 每份清冊都帶兩個綁定：`scopeContractHash`（**對的是哪一份契約**）與
`manifestation`（**讀的是哪一份文本**）。
🚨 內容關卡 A1／A3 整個站在這兩者上，**🚫 而從沒有人驗過它們今天還成不成立。**

> **⚠️ 一份指向已不存在的文本的清冊，看起來跟一份好清冊一模一樣。**

## ✅ 本支查四件事

| | 問題 |
|---|---|
| **甲** | 38 份清冊是不是綁**同一份**契約 |
| **乙** | 那份契約在 repo 裡**自我一致**嗎，且與清冊所綁**相符**嗎 |
| **丙** | 每份清冊的 `manifestation` 與**今天磁碟上**的 sections 相符嗎 |
| **丁** | 📮 D17（修 `parse_tei`）**會讓多少份清冊的綁定失效** |

⚠️ 甲丙都是「期待全部相符」的檢查——**🚨 那種檢查自證不了自己**（n+112 二），
✅ 故各配一道**會亮**的反向：把一個值弄壞，確認比對抓得到。

## 🚫 本支不送外部請求、不改任何產品程式、不改任何清冊
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

from ahig.contracts.freeze import content_hash, document_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n630_binding_integrity.json'
CONTRACT = REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json'


def main():
    # 磁碟現況：每篇的 sections 雜湊與來源型別。
    on_disk = {}
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue
        path = entry / 'manifest.json'
        if not path.exists():
            continue
        manifest = json.loads(path.read_text(encoding='utf-8'))
        sections_file = manifest.get('sectionsFile')
        record = {'sourceType': manifest.get('sourceType'),
                  'sectionsSha': None}
        if sections_file and (entry / sections_file).is_file():
            sections = json.loads(
                (entry / sections_file).read_text(encoding='utf-8'))
            record['sectionsSha'] = sections.get('contentSha256')
        on_disk[manifest['candidateId']] = record

    inventories = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventories.append(json.loads(path.read_text(encoding='utf-8')))

    # ⚠️ 比對抽成函式，🚨 反向控制才走得到**真正的比對路徑**——
    # 第 628 輪的教訓：拿 `假值 != 真值` 當反向控制是恆真，什麼也沒驗到。
    def compare(docs):
        matched = mismatched = absent = 0
        rows = []
        for entry in docs:
            report = entry['report']
            disk = on_disk.get(report)
            if disk is None or disk['sectionsSha'] is None:
                absent += 1
                rows.append({'report': report[-16:],
                             'disk': '（無 sections）',
                             'inventory': entry.get('manifestation')})
            elif disk['sectionsSha'] == entry.get('manifestation'):
                matched += 1
            else:
                mismatched += 1
                rows.append({'report': report[-16:],
                             'disk': disk['sectionsSha'],
                             'inventory': entry.get('manifestation')})
        return matched, mismatched, absent, rows

    contract_hashes = collections.Counter()
    by_source = collections.Counter()
    in_scope_by_source = collections.Counter()
    for entry in inventories:
        contract_hashes[entry.get('scopeContractHash')] += 1
        source = (on_disk.get(entry['report']) or {}).get(
            'sourceType') or '（無清單）'
        by_source[source] += 1
        in_scope_by_source[source] += sum(
            1 for o in entry.get('reportedOutcomes') or []
            if (o.get('scopeDecision') or {}).get('inScope'))

    matched, mismatched, absent, mismatch_rows = compare(inventories)

    # 🚨 必觸發之反向：把**一份**清冊的 manifestation 弄壞，
    # ⚠️ 餵進同一支比對函式，它必須把不符數從 0 變成 1。
    tampered_inventories = [dict(e) for e in inventories]
    tampered_inventories[0]['manifestation'] = (
        str(tampered_inventories[0].get('manifestation')) + 'ZZ-竄改-ZZ')
    _, tampered_mismatched, _, _ = compare(tampered_inventories)

    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    declared = contract.get('scopeContractHash')
    recomputed = document_hash(contract, 'scopeContractHash')
    bound = next(iter(contract_hashes), None)

    # ⚠️ 反向控制之一：把契約改一個字，雜湊必須跟著變。
    tampered = dict(contract)
    tampered['researchQuestion'] = str(
        tampered.get('researchQuestion', '')) + ' ZZ-竄改-ZZ'
    tampered_hash = document_hash(tampered, 'scopeContractHash')
    d17_inventories = by_source['grobid-tei']
    d17_in_scope = in_scope_by_source['grobid-tei']
    total_in_scope = sum(in_scope_by_source.values())

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('清冊數與語料相符（必觸發之正對照）',
          sum(contract_hashes.values()) == 38,
          '🚨 實得 %d 份清冊；⚠️ 若少了幾份，「全部相符」就只是「看到的都相符」'
          % sum(contract_hashes.values()))
    probe('契約改一個字，雜湊就變（必觸發之反向）',
          tampered_hash != declared,
          '🚨 竄改後 %s；⚠️ 若不變，「與清冊相符」這句話沒有意義'
          % tampered_hash[:26])
    probe('弄壞一份清冊的 manifestation，同一支比對函式必須抓到（必觸發之反向）',
          tampered_mismatched == mismatched + 1,
          '🚨 竄改一份後，不符數 %d → %d；⚠️ 若沒變，'
          '「38/38 相符」不代表任何事——**而這一道走的是真正的比對路徑，'
          '🚫 不是拿假值跟真值比大小**'
          % (mismatched, tampered_mismatched))
    # ✅ 以下三道是答案。
    probe('38 份清冊綁同一份契約',
          len(contract_hashes) == 1,
          '%s 實得 %d 種契約雜湊：%s'
          % ('✅' if len(contract_hashes) == 1 else '🚨',
             len(contract_hashes),
             [str(k)[:26] for k in contract_hashes]))
    probe('repo 的契約自我一致，且與清冊所綁相符',
          declared == recomputed == bound,
          '%s 檔內宣告 %s｜重算 %s｜清冊所綁 %s'
          % ('✅' if declared == recomputed == bound else '🚨',
             str(declared)[:26], str(recomputed)[:26], str(bound)[:26]))
    probe('每份清冊的 manifestation 與今天磁碟上的 sections 相符',
          mismatched == 0 and absent == 0,
          '%s 相符 %d｜不符 %d｜查無 sections %d'
          % ('✅' if mismatched == 0 and absent == 0 else '🚨',
             matched, mismatched, absent))

    doc = {
        'schemaVersion': 1,
        'documentType': 'binding-integrity-audit',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': sum(contract_hashes.values()),
        'distinctContractHashes': len(contract_hashes),
        'contractFile': str(CONTRACT.relative_to(REPO)).replace('\\', '/'),
        'contractDeclaredHash': declared,
        'contractRecomputedHash': recomputed,
        'contractBoundInInventories': bound,
        'contractStatus': contract.get('status'),
        'frozenFieldNote': (
            '⚠️ 契約沒有 `frozen` 這個鍵，凍結狀態寫在 `status`。'
            '✅ 而 inventory_draft.py:123 查的正是 `status != "frozen"`——'
            '🚫 故此處沒有「兩個名字指同一件事」的缺陷（本室實查後排除）。'),
        'manifestationMatched': matched,
        'manifestationMismatched': mismatched,
        'manifestationAbsent': absent,
        'mismatchRows': mismatch_rows[:8],
        'inventoriesBySource': dict(by_source),
        'inScopeBySource': dict(in_scope_by_source),
        'd17Cost': {
            'inventoriesBoundToGrobidSections': d17_inventories,
            'inScopeOutcomesAffected': d17_in_scope,
            'shareOfAllInScope': round(100 * d17_in_scope
                                       / max(1, total_in_scope), 1),
            'note': (
                '🚨 修 `parse_tei`（D17）會改變 TEI→sections 的位元組，'
                '⚠️ 於是這 %d 份清冊綁的 manifestation 立刻失效——'
                '**它們必須重讀**，涉及 %d 個在範圍內結局（全體的 %.1f%%）。'
                '✅ 這是 D17 的成本，🚫 本室不因此建議不修——'
                '⚠️ 第 612／613 輪已證明現行 TEI 路徑漏掉表格。'
                % (d17_inventories, d17_in_scope,
                   100 * d17_in_scope / max(1, total_in_scope))),
        },
        'whatThisCannotAnswer': (
            '🚫 綁定相符只證明「讀的是同一份位元組」——'
            '⚠️ 不證明讀得對，也不證明那份位元組本身完整'
            '（第 611／615／616 輪已量出 GROBID 酬載的三處缺口）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n630 綁定完整性稽核 ===')
    print('   清冊 %d 份｜契約雜湊種類 %d'
          % (sum(contract_hashes.values()), len(contract_hashes)))
    print('   契約：宣告=%s｜重算=%s｜清冊所綁=%s｜status=%r'
          % (str(declared)[:22], str(recomputed)[:22], str(bound)[:22],
             contract.get('status')))
    print('   manifestation：相符 %d｜不符 %d｜查無 %d'
          % (matched, mismatched, absent))
    print('   清冊來源：%s' % dict(by_source))
    print('   📮 D17 成本：%d 份清冊、%d 個在範圍內結局（%.1f%%）需重讀'
          % (d17_inventories, d17_in_scope,
             100 * d17_in_scope / max(1, total_in_scope)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
