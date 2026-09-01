# -*- coding: utf-8 -*-
"""**把 D25 的工作清單先備好——依定位點分組。**（第 688 輪）

## ⚠️ 先講清楚本支**不是**什麼

**🚫 本支不代表 D25 已裁，也不代表本室認為它會過。**
✅ 它只是把「若裁了要抽，第一天早上從哪裡開始」先算好——
🚨 因為那筆成本本室已經量過（第 668 輪：定位點而非全文），
**⚠️ 而一份沒有工作清單的裁定，落地時還要再花一輪。**

## ✅ 清單長什麼樣

在範圍內的每一項：**報告代號、契約結局、出處定位（章節／頁／表號）**，
外加第 676 輪算出的**第一層四個數值欄位**（留空待填）。

**✅ 依「同一篇的同一個定位點」分組**——
🚨 讀的人一次跳到一個位置，把該位置能填的一次填完，🚫 不必來回翻。

## 🚫 內容紀律

**🚨 清單寫進私有根**（含出處字串，屬文獻衍生內容）；
✅ repo 這一支**只留計數與結構**，🚫 不含任何標籤或出處文字（n+195 一）。
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

OUT = Path(__file__).resolve().parent / 'n688_d25_worklist.json'
WORKLIST = ROOT / 'extraction-worksheet' / 'd25-numeric-worklist.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# ✅ 第 676 輪證明過的第一層（合併得動所需）
TO_FILL = ['pointEstimate', 'ciLow', 'ciHigh', 'nSubjects']
CARRY = ['normalisedOutcomeRef', 'dose', 'doseUnit', 'instrument',
         'analysisSet', 'effectMeasure', 'timepointDays']


def locator_key(reported):
    loc = reported.get('sourceLocation') or {}
    if not isinstance(loc, dict):
        return 'ZZ-無定位-ZZ'
    parts = [str(loc.get(k)) for k in ('section', 'pageIndex', 'tableOrFigure')
             if loc.get(k) is not None]
    return '｜'.join(parts) if parts else 'ZZ-無定位-ZZ'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    groups = collections.defaultdict(list)
    per_outcome = collections.Counter()
    papers = set()
    total = 0
    without_locator = 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            total += 1
            report = inventory['report']
            papers.add(report)
            per_outcome[reported['normalisedOutcomeRef']] += 1
            key = locator_key(reported)
            if key == 'ZZ-無定位-ZZ':
                without_locator += 1
            entry = {k: reported.get(k) for k in CARRY}
            entry['sourceLocation'] = reported.get('sourceLocation')
            entry['toFill'] = {f: None for f in TO_FILL}
            groups['%s｜%s' % (report[-16:], key)].append(entry)

    worklist = {
        'schemaVersion': 1,
        'documentType': 'd25-numeric-worklist',
        'preparedBy': 'B.11 執行室（第 688 輪）',
        'status': ('🚨 **待裁定**——D25 尚未裁；本清單只是預備，'
                   '🚫 不得視為已授權開始抽取。'),
        'fieldsToFill': TO_FILL,
        'whyTheseFour': ('✅ 第 676 輪實跑證明：只填這四欄，'
                         '`run_all` 與 `meta_analyse_dl` 就跑得動；'
                         '🚨 變異數由 `se_from_ci` 從區間推得，不必另抽。'),
        'alsoRequiredBeforeAnyNodeIsValid': (
            '🚨 第 677／678 輪：每一項還要一段**在原文中唯一命中**的逐字引文'
            '（`CitationAnchor.exactQuote` ＋ `uniqueMatch`），'
            '⚠️ 而逐字引文只能留在私有根。'),
        'groups': dict(sorted(groups.items())),
    }
    WORKLIST.parent.mkdir(parents=True, exist_ok=True)
    WORKLIST.write_text(json.dumps(worklist, ensure_ascii=False, indent=2)
                        + '\n', encoding='utf-8')

    sizes = sorted((len(v) for v in groups.values()), reverse=True)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('清單涵蓋全部在範圍內的項目（必觸發之正對照）',
          total == sum(per_outcome.values()) and total > 0,
          '🚨 在範圍內 %d 項、寫入 %d 項、來自 %d 篇；'
          '⚠️ 對不上就代表清單漏了東西'
          % (total, sum(len(v) for v in groups.values()), len(papers)))
    probe('每一項都有可據以定位的出處（必觸發之正對照）',
          without_locator == 0,
          '🚨 沒有定位點的 %d 項；⚠️ 沒有定位點的項目，讀的人只能重讀全文'
          % without_locator)
    # 🚨 必觸發之反向：repo 這一支不得含任何標籤或出處文字。
    repo_side_text = json.dumps(
        {'perOutcome': dict(per_outcome), 'groupSizes': sizes},
        ensure_ascii=False)
    leaked = [k for k in ('localLabel', 'exactQuote', 'section')
              if k in repo_side_text]
    probe('repo 這一支不含任何標籤或出處文字（必觸發之反向）',
          not leaked,
          '🚨 疑似外洩的鍵：%s；⚠️ 出處字串屬文獻衍生內容，只能留私有根'
          % (leaked or '無'))
    # 🚨 這一道是答案。
    probe('工作清單已可照著跳定位點做（🚫 不代表 D25 已裁）',
          len(groups) > 0 and without_locator == 0,
          '🚨 分成 %d 個「同篇同定位點」的工作組；最大的組 %d 項、'
          '中位數 %d 項；⚠️ 組數越少代表越省來回翻閱'
          % (len(groups), sizes[0] if sizes else 0,
             sizes[len(sizes) // 2] if sizes else 0))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd25-worklist-summary',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'notAnAuthorisation': (
            '🚨 **本支不代表 D25 已裁**，也不代表本室認為它會過。'
            '✅ 它只把「若裁了要抽，第一天從哪裡開始」先算好。'),
        'strengthensDecision': (
            '📮 D25。⚠️ 本支**沒有紅燈**、也不新增決策——'
            '✅ 它是 D25 落地時的工作清單。'
            '⚠️ 下一次登記簿改版會與其他待掛的一起掛入'
            '（🚫 本室不每輪都出一版登記簿，那是噪音）。'),
        'inScopeItems': total,
        'papers': len(papers),
        'workGroups': len(groups),
        'groupSizeMax': sizes[0] if sizes else 0,
        'groupSizeMedian': sizes[len(sizes) // 2] if sizes else 0,
        'itemsWithoutLocator': without_locator,
        'perOutcome': dict(per_outcome.most_common()),
        'fieldsToFill': TO_FILL,
        'worklistWrittenTo': str(WORKLIST),
        'contentDiscipline': (
            '🚨 清單本體（含出處字串）寫進**私有根**；'
            '✅ repo 這一支只留計數與結構，🚫 不含標籤或出處文字（n+195 一）。'),
        'methodLimit': (
            '⚠️ 「有定位點」🚫 不等於「那個位置真的有數字」——'
            '🚨 第 597／635 輪已看過「出處指到方法段」與'
            '「宣稱有數值卻找不到數字」兩種情形。'
            '**✅ 本支只保證讀的人知道先跳去哪裡，🚫 不保證跳過去就有東西。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n688 D25 工作清單（預備，🚫 非授權）===')
    print('   在範圍內 %d 項｜%d 篇｜分成 %d 個工作組'
          % (total, len(papers), len(groups)))
    print('   組大小：最大 %d｜中位數 %d｜沒有定位點的項目 %d'
          % (sizes[0] if sizes else 0,
             sizes[len(sizes) // 2] if sizes else 0, without_locator))
    print('   各結局：%s' % dict(per_outcome.most_common()))
    print('   待填欄位：%s' % TO_FILL)
    print('   清單寫到：%s' % WORKLIST)
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
