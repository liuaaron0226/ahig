# -*- coding: utf-8 -*-
"""**替身對 41 篇產出一模一樣的 draft——於是有幾條路從沒被走過。**（第 547 輪）

## 🚨 上一輪學到的那把尺

第 546 輪的缺口（工作單沒有「一頁一頁併回去」的函式）之所以躲過演練，
**是因為演練走的是「整份寫入」這條實際上不會發生的路。**
**✅ 本輪拿同一把尺量替身本身。**

`n537` 的替身對每一篇產出**完全相同**的兩項（1 個 in-scope、1 個範圍外）。
⚠️ 而真實的 41 篇會各不相同。**🚨 於是這幾條路從來沒有在真文件上跑過**：

| 沒走過的路 | 為什麼重要 |
|---|---|
| **超過 `maxStudyResultsPerStudy`（實際值 12）** | 🚨 超過時 `onExceedMax=escalate`，**會把該篇「全部」in-scope 翻成 false**——⚠️ 那是最激烈的一條分支 |
| 一篇有多個 in-scope | ⚠️ 上限、計數、摘要三者要一致 |
| 一篇**零** in-scope | 🚨 全部範圍外仍必須是成功而非失敗 |

## 🚨 併記一個我自己的錯（已修）

`n537` 原本讀 `scopeDecisionSummary['exceedsMaxStudyResults']` 來數超限篇數。
**⚠️ 那個欄位不存在**——`scope_inventory` 寫的是 **`escalated`**。
**🚨 於是那個計數永遠是 0，而 0 看起來像量到的。** ✅ 已改，並在 n537 產物內留註。

> ⚠️ 同一型的第 N 次：**量到的東西不是主張所依賴的東西。**
> 🚨 而這一次它藏在一個我沒有拿去做任何主張的數字裡——**所以更久沒被看見。**

## ✅ 併查：存放處的路徑在 41 篇真 id 上成不成立

`store.inventory_path` 的路徑在 Windows 上會有多長？41 個真 id 會不會撞？
**🚫 本支不寫任何檔**，只把路徑算出來看。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
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

from ahig.contracts.freeze import content_hash, verify_frozen  # noqa: E402
from ahig.extraction import run_inventory, store  # noqa: E402
from ahig.extraction.corpus import iter_acquired, reading_request_for  # noqa: E402

from n537_chain_rehearsal import REHEARSAL, STUB_AT  # noqa: E402

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
OUT = Path(__file__).resolve().parent / 'n547_varied_shapes.json'

IN_SCOPE = {'normalisedOutcomeRef': 'time-to-exhaustion',
            'instrument': 'cycling-tte-fixed-intensity',
            'timepointDays': 0.02, 'analysisSet': 'ITT',
            'effectMeasure': 'MD', 'statisticalModel': 'unadjusted',
            'dose': 60, 'doseUnit': 'g/h'}


def varied_reader(shape_of):
    """替身，但**每一篇形狀不同**。形狀由 ``shape_of`` 決定，🚫 不隨機。

    ⚠️ 隨機會讓重跑得到不同的產物，而演練要可複驗。
    """
    def read(request):
        n_in, n_out = shape_of(request)
        outcomes = []
        for i in range(n_in):
            outcomes.append(dict(IN_SCOPE,
                                 localLabel='%s / in-scope %d' % (REHEARSAL, i),
                                 sourceLocation={'section': REHEARSAL}))
        for i in range(n_out):
            outcomes.append({'localLabel': '%s / 範圍外 %d' % (REHEARSAL, i),
                             'sourceLocation': {'section': REHEARSAL}})
        return {
            'inventoryId': 'inv:%s' % REHEARSAL,
            'report': request.report,
            'manifestation': request.manifestation,
            'scopeContractHash': request.scope_contract_hash,
            'lifecycle': 'draft',
            'reportedOutcomes': outcomes,
            'registryComparison': {'status': 'pending'},
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
    return read


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if not (contract.get('status') == 'frozen'
            and verify_frozen(contract, 'scopeContractHash')):
        print('🚨 契約不是可用的凍結契約，拒絕演練', file=sys.stderr)
        sys.exit(2)
    cap = contract['extractionPolicy']['maxStudyResultsPerStudy']

    ids = [d.candidate_id for _n, d, _e in iter_acquired() if d is not None]
    order = {cid: i for i, cid in enumerate(ids)}

    def shape_of(request):
        """形狀由該篇在語料裡的位置決定——⚠️ 可複驗，且必定涵蓋三種情形。

        第 0 篇：超過上限（cap+1 個 in-scope）
        第 1 篇：零個 in-scope（全部範圍外）
        其餘：1–4 個 in-scope，外加 1 個範圍外
        """
        i = order[request.report]
        if i == 0:
            return cap + 1, 1
        if i == 1:
            return 0, 2
        return i % 4 + 1, 1

    # 🚨 store=None：替身的清冊一份都不落盤（與 n537 同一理由）。
    run = run_inventory(contract, reader=varied_reader(shape_of),
                        candidate_ids=ids)

    escalated, zero_in_scope, by_count = [], [], {}
    leftover_true = []
    for outcome in run.succeeded:
        summary = outcome.scoped.get('scopeDecisionSummary') or {}
        n = summary.get('candidateCount')
        by_count[n] = by_count.get(n, 0) + 1
        if summary.get('escalated'):
            escalated.append(outcome.candidate_id[-16:])
            # 🚨 超限時不得留下任何 inScope=true 讓下游誤以為可以抽取。
            if any((item.get('scopeDecision') or {}).get('inScope')
                   for item in outcome.scoped.get('reportedOutcomes') or []):
                leftover_true.append(outcome.candidate_id[-16:])
        if n == 0:
            zero_in_scope.append(outcome.candidate_id[-16:])

    # 存放處的路徑：🚫 不寫檔，只算。
    fake = 'sha256:' + '0' * 64
    paths = [store.inventory_path(cid, fake, fake) for cid in ids]
    lengths = [len(str(p)) for p in paths]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一篇仍恰好落在一個桶子裡',
          len(run.succeeded) + len(run.failed) == len(ids)
          and len(run.failed) == 0,
          '成功 %d｜失敗 %d｜語料 %d'
          % (len(run.succeeded), len(run.failed), len(ids)))
    probe('超過上限那一條真的走到了（必觸發）',
          len(escalated) == 1,
          '🚨 走不到就等於這條最激烈的分支從沒被證明過；'
          '上限 %d，實得 escalated %d 篇' % (cap, len(escalated)))
    probe('超限篇不得留下任何 inScope=true',
          not leftover_true,
          '🚨 留著會讓下游以為那幾項可以抽取；實得 %s'
          % (leftover_true or '無'))
    probe('零個 in-scope 的那一篇仍算成功',
          len(zero_in_scope) == 1,
          '🚨 全部範圍外是一種結果，🚫 不是失敗；實得 %d 篇' % len(zero_in_scope))
    probe('各篇的 in-scope 數確實不同（必觸發）',
          len(by_count) >= 4,
          '🚨 若只有一種計數，代表替身其實還是一模一樣；實得分布 %s'
          % dict(sorted(by_count.items(), key=lambda kv: (kv[0] is None, kv[0]))))
    probe('41 個存放路徑互不相同',
          len(set(map(str, paths))) == len(paths),
          '相異 %d／%d' % (len(set(map(str, paths))), len(paths)))
    probe('存放路徑長度在 Windows 限制內',
          max(lengths) < 260,
          '⚠️ 最長 %d 字元（MAX_PATH 260）；🚨 超過會在寫入時才爆'
          % max(lengths))

    doc = {
        'schemaVersion': 1,
        'documentType': 'varied-shape-rehearsal',
        'ruling': '第 546 輪之尺：演練是否走了現實不會走的路',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'readerIsAStub': True,
        'stubMarker': REHEARSAL,
        'storeDisabled': '🚨 store=None——編造的清冊一份都不落盤',
        'shapeRule': ('第 0 篇 = 上限+1 個 in-scope｜第 1 篇 = 0 個｜'
                      '其餘 = 序位 mod 4 + 1 個。🚫 不用隨機：演練要可複驗。'),
        'cap': cap,
        'run': {'attempted': run.attempted, 'succeeded': len(run.succeeded),
                'failed': len(run.failed)},
        'inScopeCountDistribution': {str(k): v for k, v in sorted(
            by_count.items(), key=lambda kv: (kv[0] is None, kv[0]))},
        'escalated': escalated,
        'zeroInScope': zero_in_scope,
        'leftoverInScopeTrue': leftover_true,
        'storePaths': {'unique': len(set(map(str, paths))), 'count': len(paths),
                       'minLen': min(lengths), 'maxLen': max(lengths),
                       'note': '🚫 只算不寫；⚠️ 長度以本機私有根為準，'
                               '搬到更深的路徑會變長。'},
        'correctedThisRound': (
            '🚨 n537 原本讀 scopeDecisionSummary["exceedsMaxStudyResults"]——'
            '⚠️ 該欄位不存在（實際是 "escalated"），故那個計數永遠是 0。'
            '✅ 已修並在 n537 產物內留註。'),
        'notProven': [
            '🚨 抽得準不準：替身編造。',
            '⚠️ 形狀是我排的，🚫 不是真實論文的分布。',
        ],
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n547 形狀各異的演練（真語料 41 篇 × 真契約）===')
    print('   上限 %d｜成功 %d｜失敗 %d' % (cap, len(run.succeeded),
                                            len(run.failed)))
    print('   in-scope 數分布：%s' % doc['inScopeCountDistribution'])
    print('   escalated %d 篇｜零 in-scope %d 篇｜殘留 inScope=true %d 篇'
          % (len(escalated), len(zero_in_scope), len(leftover_true)))
    print('   存放路徑：相異 %d／%d｜長度 %d–%d'
          % (len(set(map(str, paths))), len(paths), min(lengths), max(lengths)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
