# -*- coding: utf-8 -*-
"""**這條鏈在真語料上產出的 scoped，schema 收不收？**（第 539 輪）

## 🚨 已經被測過的，與還沒有的

`test_inventory_scope_integration.py` 已經釘住「ScopeMatcher 把 draft 升級為
scoped，輸出必須**直接**通過 schema」。**✅ 那一條是真的，而且很有力。**

**⚠️ 但它餵進去的是合成 draft。** 真語料進去之後，有幾個欄位的值變成真的：

- `report` — 真的 candidateId（41 個）
- `manifestation` — 真的 `contentSha256`
- `completenessAttestation.sectionsScanned` — **各篇真的章節標題**
  （全語料 968 節，🚨 其中 20 節的標題是字面 `Untitled`，最多一篇 160 節）

**🚨 而 `outcome-inventory.schema.json` 是 `additionalProperties: false`。**
⚠️ 合成 fixture 只有 2 個短標題；**這 41 篇是第一次拿真的值去撞它。**

## ✅ draft 與 scoped 都驗

⚠️ `validate_draft`（本鏈的驗收）與 schema（下游的驗收）是**兩套標準**。
**🚨 若前者收得下而後者收不下，那道縫隙要在接上模型之前知道**——
否則會看起來像模型回了壞東西。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 證得了：**形狀**在 41 篇真文件上都過得了下游 schema。
- 🚨 證不了：**內容對不對**。⚠️ draft 的 `reportedOutcomes` 仍是替身編造的
  （n537 同一支替身），**🚫 故本支對「抽得準不準」一個字都沒說。**
- 🚨 證不了：SHACL 那一層——⚠️ 本機缺 `pyshacl`，該測試檔本來就未被收集。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門**，與 n+184、n535、n537、n538 同類。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsonschema import Draft202012Validator  # noqa: E402

from ahig.contracts.freeze import content_hash, verify_frozen  # noqa: E402
from ahig.extraction import inventory_draft as bridge  # noqa: E402
from ahig.extraction.corpus import iter_acquired, reading_request_for  # noqa: E402

from n537_chain_rehearsal import REHEARSAL, stub_reader  # noqa: E402

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
SCHEMA_PATH = REPO / 'ahig' / 'schema' / 'outcome-inventory.schema.json'
OUT = Path(__file__).resolve().parent / 'n539_scoped_schema_conformance.json'


def errors_of(validator, doc):
    return ['%s: %s' % ('/'.join(str(p) for p in e.path) or '(root)', e.message)
            for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))]


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if not (contract.get('status') == 'frozen'
            and verify_frozen(contract, 'scopeContractHash')):
        print('🚨 契約不是可用的凍結契約，拒絕演練', file=sys.stderr)
        sys.exit(2)

    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    validator = Draft202012Validator(schema)

    records, draft_bad, scoped_bad = [], 0, 0
    titles_seen, untitled_scanned, max_scanned = set(), 0, 0
    a_scoped = None

    for name, document, _error in iter_acquired():
        if document is None:
            continue
        request = reading_request_for(document.candidate_id, contract)
        draft = stub_reader(request)
        bridge.validate_draft(draft, request)
        scoped = bridge.draft_to_scoped(draft, contract,
                                        now='2026-08-31T00:00:00Z')
        a_scoped = a_scoped or scoped

        d_err = errors_of(validator, draft)
        s_err = errors_of(validator, scoped)
        draft_bad += bool(d_err)
        scoped_bad += bool(s_err)

        scanned = draft['completenessAttestation']['sectionsScanned']
        titles_seen.update(scanned)
        untitled_scanned += sum(1 for t in scanned if t.strip() == 'Untitled')
        max_scanned = max(max_scanned, len(scanned))

        records.append({
            'dir': name[-16:],
            'sectionsScanned': len(scanned),
            'draftErrors': d_err[:3],
            'scopedErrors': s_err[:3],
        })

    probes = []

    def probe(pname, ok, detail):
        probes.append({'probe': pname, 'passed': bool(ok), 'detail': detail})

    probe('41 篇的 scoped 全部通過下游 schema', scoped_bad == 0,
          '不通過 %d／%d' % (scoped_bad, len(records)))
    probe('41 篇的 draft 也通過同一份 schema', draft_bad == 0,
          '🚨 若 draft 過不了，代表本鏈的驗收與下游的驗收有縫；'
          '不通過 %d／%d' % (draft_bad, len(records)))
    # 🚨 必觸發：全綠也可能是因為驗證器根本沒在驗。
    tampered = dict(a_scoped or {}, anUnexpectedField=REHEARSAL)
    probe('驗證器真的會擋（必觸發）', bool(errors_of(validator, tampered)),
          '🚨 加一個 schema 沒宣告的欄位，additionalProperties:false 應當拒絕；'
          '實得 %d 條錯誤' % len(errors_of(validator, tampered)))
    probe('真的章節標題確實被餵進去了',
          len(titles_seen) > 100 and untitled_scanned > 0,
          '相異標題 %d 個｜其中 Untitled 被掃描 %d 次｜單篇最多 %d 節；'
          '⚠️ 若這些數字很小，代表撞 schema 的仍是合成值'
          % (len(titles_seen), untitled_scanned, max_scanned))

    doc = {
        'schemaVersion': 1,
        'documentType': 'scoped-schema-conformance',
        'ruling': 'n+183 之「scoped → family/gates（既有）」：本鏈的產出下游收不收',
        'notAGate': '🚫 不入輪次閘門（n+181 三）；與 n+184、n535、n537、n538 同類',
        'readerIsAStub': True,
        'stubMarker': REHEARSAL,
        'storeDisabled': '🚨 本支不寫任何清冊（與 n537 同一理由）',
        'schema': SCHEMA_PATH.relative_to(REPO).as_posix(),
        'schemaAdditionalProperties': schema.get('additionalProperties'),
        'population': '私有根 fulltext/ 內所有 acquired',
        'privateRoot': PROV,
        'counts': {
            'records': len(records),
            'draftFailures': draft_bad,
            'scopedFailures': scoped_bad,
            'distinctSectionTitles': len(titles_seen),
            'untitledScanned': untitled_scanned,
            'maxSectionsInOneRecord': max_scanned,
        },
        'notProven': [
            '🚨 抽得準不準：draft 的 reportedOutcomes 是替身編造的。',
            '🚨 SHACL 那一層：本機缺 pyshacl，該測試檔未被收集。',
        ],
        'controlProbes': probes,
        'records': [r for r in records if r['draftErrors'] or r['scopedErrors']],
        'recordsNote': ('🚫 只列出有錯的；全數通過時此陣列為空——'
                        '⚠️ 空陣列與「沒有跑」由 counts.records 區分。'),
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n539 本鏈產出之 scoped 對下游 schema 的相容性 ===')
    print('   紀錄 %d 篇｜draft 不通過 %d｜scoped 不通過 %d'
          % (len(records), draft_bad, scoped_bad))
    print('   餵進去的真值：相異章節標題 %d 個｜Untitled 掃描 %d 次｜單篇最多 %d 節'
          % (len(titles_seen), untitled_scanned, max_scanned))
    for r in doc['records'][:5]:
        print('   🚨 %s draft=%s scoped=%s'
              % (r['dir'], r['draftErrors'], r['scopedErrors']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
