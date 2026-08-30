# -*- coding: utf-8 -*-
"""**整條確定性鏈，在真語料上走一次讀者那一關之後。**（第 537 輪）

## 🚨 到目前為止沒有被證明過的那一段

`run_inventory` 對真語料跑過，**⚠️ 但 41 筆全部卡在 `call-reader`**——
🚨 也就是說**讀者之後的每一段（驗收、判範圍、存檔）從來沒有在真的文件上跑過**，
只在一份合成 fixture 上跑過。

⚠️ 那份 fixture 有 2 節、幾百字元；**🚨 真語料有 968 節、最多一篇 160 節、
最大 355,929 字元，且章節標題裡有 20 個是字面 `Untitled`。**
**✅ 本支拿一個明白標成演練的替身讀者，把那一段在 41 篇上真的走一次。**

## 🚨 絕對不寫進存放處

替身產出的 `reportedOutcomes` 是**編造的**。⚠️ 若把它們存進私有根的清冊存放處，
**🚨 磁碟上會出現 41 份看起來完全正常、實際上一個字都不是從論文讀來的清冊**——
而存放處的鍵只認綁定，**⚠️ 分不出真假**。

> **✅ 故本支一律 `store=None`，🚫 一份都不落盤。**
> ⚠️ 這正是本 run 反覆抓到的那一型的近親：**看起來正常的東西，來源是假的。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 證得了：讀取層 → 請求 → 驗收 → 判範圍，在 41 篇真文件上都走得完，
  且每一篇的完整性聲明是拿**它自己的**章節標題去對的。
- 🚨 證不了：**模型讀出來的東西對不對**。⚠️ 判定的輸入是編造的，
  **🚫 故本支對「抽得準不準」一個字都沒說。**
- 🚨 證不了：真實 draft 會不會有本支沒想到的形狀。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門**，與 n+184、n535 同類。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash, verify_frozen  # noqa: E402
from ahig.extraction import run_inventory  # noqa: E402
from ahig.extraction.corpus import iter_acquired  # noqa: E402

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
OUT = Path(__file__).resolve().parent / 'n537_chain_rehearsal.json'

# 🚨 一眼看得出是演練的標記。萬一哪天真的漏出去，讀的人立刻知道它不是清冊。
REHEARSAL = 'REHEARSAL-NOT-A-REAL-INVENTORY'
# 固定時戳：演練要可重跑得到同一份產物。
STUB_AT = '2026-08-31T00:00:00Z'


def stub_reader(request):
    """替身讀者：🚫 不讀任何東西，只造出**形狀**正確的 draft。

    刻意造兩項，讓判定的兩條分支都真的跑到：
      1. 依真契約的軸值湊成 in-scope（力竭時間／運動中／ITT／MD／60 g·h⁻¹）
      2. 沒有 normalisedOutcomeRef，必為 notExtracted-outcome-not-in-scope

    ⚠️ `sectionsScanned` 用的是**這一篇自己的**章節標題——
    🚨 那才會真的去撞 validate_draft 的「聲稱掃描過本文件沒有的章節」。
    """
    return {
        'inventoryId': 'inv:%s' % REHEARSAL,
        'report': request.report,
        'manifestation': request.manifestation,
        'scopeContractHash': request.scope_contract_hash,
        'lifecycle': 'draft',
        'reportedOutcomes': [
            {'localLabel': REHEARSAL + ' / in-scope 分支',
             'normalisedOutcomeRef': 'time-to-exhaustion',
             'instrument': 'cycling-tte-fixed-intensity',
             'timepointDays': 0.02,          # 0.48 小時 → 落在「運動中」窗內
             'analysisSet': 'ITT',
             'effectMeasure': 'MD',
             'statisticalModel': 'unadjusted',
             'dose': 60, 'doseUnit': 'g/h',
             'sourceLocation': {'section': REHEARSAL}},
            {'localLabel': REHEARSAL + ' / 範圍外分支',
             'sourceLocation': {'section': REHEARSAL}},
        ],
        'registryComparison': {'status': 'pending'},
        # 🚨 第 539 輪：替身原本自己就不合下游 schema（agentClass 不在列舉內、
        # 多帶 note、attestedBy 缺 at、harmsScan 缺三個必填欄位）。
        # ⚠️ 那是量測工具的錯，不是鏈的錯——修的是替身。
        # 🚫 演練標記因此改掛在 inventoryId 與 localLabel（那兩處是自由文字）。
        'createdBy': {'agentClass': 'model'},
        'completenessAttestation': {
            'sectionsScanned': list(request.section_titles),
            'supplementaryScanned': False,
            'harmsScan': {'performed': True,
                          'sectionsScanned': list(request.section_titles),
                          'harmOutcomesFound': 0,
                          'harmsReportingStatement': 'not-mentioned'},
            'attestedBy': {'agentClass': 'model', 'at': STUB_AT}},
    }


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if not (contract.get('status') == 'frozen'
            and verify_frozen(contract, 'scopeContractHash')):
        print('🚨 契約不是可用的凍結契約，拒絕演練', file=sys.stderr)
        sys.exit(2)

    ids = [d.candidate_id for _n, d, _e in iter_acquired() if d is not None]

    # 🚨 store=None：一份都不落盤。理由見模組說明。
    run = run_inventory(contract, reader=stub_reader, candidate_ids=ids)

    by_stage = {}
    for outcome in run.outcomes:
        key = outcome.stage if outcome.ok else 'FAILED@' + outcome.stage
        by_stage[key] = by_stage.get(key, 0) + 1

    decisions, capped = {}, 0
    for outcome in run.succeeded:
        summary = outcome.scoped.get('scopeDecisionSummary') or {}
        # 🚨 第 547 輪更正：這裡原本讀 `exceedsMaxStudyResults`——**那個欄位
        # 不存在**（`scope_inventory` 寫的是 `escalated`）。⚠️ 於是這個計數
        # 永遠是 0，而 0 看起來像量到的。🚫 同一型的第 N 次。
        if summary.get('escalated'):
            capped += 1
        for item in outcome.scoped.get('reportedOutcomes') or []:
            code = (item.get('scopeDecision') or {}).get('reasonCode', '(缺)')
            decisions[code] = decisions.get(code, 0) + 1

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一篇都有下落', run.attempted == len(ids),
          '嘗試 %d｜語料 %d' % (run.attempted, len(ids)))
    probe('41 篇全部走完到判範圍', len(run.succeeded) == len(ids),
          '成功 %d｜失敗 %d' % (len(run.succeeded), len(run.failed)))
    probe('兩條判定分支都真的跑到（必觸發）',
          decisions.get('in-scope', 0) == len(ids)
          and decisions.get('notExtracted-outcome-not-in-scope', 0) == len(ids),
          '🚨 只有一條跑到，等於另一條沒被證明過；實得 %s' % decisions)
    probe('沒有任何東西被寫進清冊存放處',
          not (ROOT / 'extraction').exists()
          or not any((ROOT / 'extraction').rglob('inventory-*.json')),
          '🚨 演練的清冊落盤，磁碟上就會有 41 份看起來正常而來源是假的東西')
    # 🚨 必觸發：上面那 41 篇全綠，也可能是因為那道檢查根本沒在看。
    # ⚠️ 故再跑一次，替身改口聲稱掃描過一個不存在的章節——該紅的要真的紅。
    def lying_reader(request):
        draft = stub_reader(request)
        draft['completenessAttestation']['sectionsScanned'] = [
            'A Section No Paper Has']
        return draft

    liar = run_inventory(contract, reader=lying_reader, candidate_ids=ids)
    liar_stages = {}
    for outcome in liar.failed:
        liar_stages[outcome.stage] = liar_stages.get(outcome.stage, 0) + 1

    probe('完整性聲明是拿各篇自己的章節標題去對的（必觸發）',
          len(liar.succeeded) == 0
          and liar_stages.get('validate-draft') == len(ids),
          '替身改口聲稱掃描過一個不存在的章節 → 成功 %d｜'
          'validate-draft 擋下 %d（應為 0 與 %d）'
          % (len(liar.succeeded), liar_stages.get('validate-draft', 0), len(ids)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'extraction-chain-rehearsal',
        'ruling': 'n+181（三之 2）續：確定性鏈在真語料上走完讀者之後那一段',
        'notAGate': '🚫 不入輪次閘門（n+181 三）；與 n+184、n535 同類',
        'readerIsAStub': True,
        'stubMarker': REHEARSAL,
        'storeDisabled': '🚨 store=None——編造的清冊一份都不得落盤',
        'contract': {
            'scopeContractId': contract.get('scopeContractId'),
            'scopeContractHash': contract.get('scopeContractHash'),
        },
        'population': '私有根 fulltext/ 內所有 acquired（🚨 非校準 60，非 84）',
        'privateRoot': PROV,
        'run': {
            'attempted': run.attempted,
            'succeeded': len(run.succeeded),
            'failed': len(run.failed),
            'byStage': by_stage,
            'charsSent': sum(o.request_chars for o in run.outcomes),
            'charsReturned': sum(o.draft_chars for o in run.outcomes),
        },
        'scopeDecisions': decisions,
        'escalatedExceedsMax': capped,
        'escalatedFieldNote': ('🚨 第 547 輪更正：原本讀的欄位名 '
                               '`exceedsMaxStudyResults` 不存在，'
                               '故先前那個 0 不是量測。'),
        'failures': [{'dir': o.candidate_id[-16:], 'stage': o.stage,
                      'error': o.error[:200]} for o in run.failed],
        'notProven': [
            '🚨 抽得準不準：判定的輸入是編造的，🚫 本支一個字都沒說。',
            '🚨 真實 draft 會不會有本支沒想到的形狀。',
            '⚠️ charsReturned 是替身的長度，🚫 不是模型會回多長。',
        ],
        'negativeControlRun': {
            'what': '替身改口聲稱掃描過一個不存在的章節',
            'succeeded': len(liar.succeeded),
            'blockedAtValidateDraft': liar_stages.get('validate-draft', 0),
            'note': ('🚨 沒有這一跑，「41 篇全綠」也可能是因為那道檢查沒在看。'),
        },
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n537 確定性鏈之演練（真語料 41 篇 × 真契約 × 替身讀者）===')
    print('   🚨 讀者是替身，store=None——一份都沒有落盤')
    print('   嘗試 %d｜成功 %d｜失敗 %d' % (run.attempted, len(run.succeeded),
                                            len(run.failed)))
    print('   各階段：%s' % by_stage)
    print('   判定：%s' % decisions)
    print('   送出 %d 字元｜替身回 %d 字元' % (doc['run']['charsSent'],
                                              doc['run']['charsReturned']))
    for failure in doc['failures'][:5]:
        print('   🚨 %s @%s：%s' % (failure['dir'], failure['stage'],
                                    failure['error']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
