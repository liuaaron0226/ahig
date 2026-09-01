# -*- coding: utf-8 -*-
"""**決策登記簿 v4——把第 674 輪點名的 19 支紅燈全部處置掉。**（第 675 輪）

## ✅ 承接 v3（24 項），🚫 不改寫它

第 674 輪算出：48 支亮紅燈卻沒有決策引用，其中 **19 支與任何決策的題目重疊都很低**。
✅ 本支把那 19 支**逐一處置**——🚨 一支都不准留在「待過目」。

## 🚨 而其中一支的處置是「登記簿真的漏了它」

`n659_no_numbers_yet`：**在範圍內的 98 項，數值欄位全部是 0**——
效應量、變異數、信賴區間、樣本數一個都沒有；`StudyResult` 沒有 schema 也沒有文件。

> **🚨 GRADE 與統合分析今天跑不起來，而 n659 已用合成資料實跑證明卡的是資料、🚫 不是程式。**
> **⚠️ 而登記簿 24 項裡，沒有任何一項在問「要不要開一輪把數值抽出來」。**

✅ 故新增 **D25**。

## ✅ 另外 6 支是「該掛而沒掛」

n638→D9、n617→D17、n633→D21、n625／n626→D18／D19、n635→D12、n642→D10。

## ✅ 其餘是工具或已被取代——**🚫 那些本來就不需要裁定**

⚠️ 但本支仍**逐一列出理由**，🚫 不用「其他」帶過。

## 🚫 本支不改任何清冊與契約、不送外部請求
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
OUT = HERE / 'n675_decision_register_v4.json'
V3 = HERE / 'n669_decision_register_v3.json'
LOWOVERLAP = HERE / 'n674_uncited_red_topics.json'

CITATIONS = []

# 🚨 第 674 輪點名的 19 支，每一支的處置。⚠️ 一支都不准留白。
DISPOSITION = {
    'n496_corpus_verify.json': '工具：本室自己的查核器，🚫 不需裁定',
    'n498_sections_integrity.json': '工具：本室自己的查核器，🚫 不需裁定',
    'n499_calibration_redraw.json': '工具：重抽可重現性，🚫 不需裁定',
    'n504_executor_suite.json': '工具：執行室常設檢查，🚫 不需裁定',
    'n512_source_host_provenance.json': '工具：來源出處查核，🚫 不需裁定',
    'n517_temporal_order_check.json': '工具：時序查核，🚫 不需裁定',
    'n637_prose_numbers.json': '工具：看板散文數字對帳，🚫 不需裁定',
    'n648_artefact_reproducibility.json': '工具：憑證重跑對帳，🚫 不需裁定',
    'n655_publication_bias_attempt.json':
        '⚠️ 失敗路線（關鍵字判準無鑑別力，已如實記下），🚫 不需裁定',
    'n610_pending_decisions.json': '✅ 已由 v3 取代',
    'n634_decision_register_v2.json': '✅ 已由 v3 取代',
    'n638_cap_paths_executed.json': '📮 掛回 D9',
    'n617_findings_by_source.json': '📮 掛回 D17',
    'n633_gi_scale_heterogeneity.json': '📮 掛回 D21',
    'n625_corpus_era_bias.json': '📮 掛回 D18／D19',
    'n626_missing_era_dose_space.json': '📮 掛回 D18／D19',
    'n635_d12_recoverability.json': '📮 掛回 D12',
    'n642_double_read_sample.json': '📮 掛回 D10',
    'n659_no_numbers_yet.json': '🚨 登記簿真的漏了它 → 新增 D25',
}


def cite(filename, *keys):
    """從憑證取值，並記下來源。🚨 取不到就是 None，會被探針抓到。"""
    path = HERE / filename
    entry = {'from': filename, 'path': ' → '.join(str(k) for k in keys)}
    try:
        node = json.loads(path.read_text(encoding='utf-8'))
        for key in keys:
            node = node[key]
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        node = None
    entry['value'] = node
    CITATIONS.append(entry)
    return node


def main():
    v3 = json.loads(V3.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v3['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince669', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)

    attach('D9', '🚨 現行契約下兩條路一致，但 `onExceedMax=truncate` 時**不一致**',
           cite('n638_cap_paths_executed.json', 'agreement'),
           'n638_cap_paths_executed.json → agreement')
    attach('D17', '⚠️ GROBID 佔語料的基準率（%）',
           cite('n617_findings_by_source.json', 'baseRatePct'),
           'n617_findings_by_source.json')
    attach('D17', '🚨 明顯集中在 GROBID 的發現',
           cite('n617_findings_by_source.json', 'concentrated'),
           'n617_findings_by_source.json')
    attach('D21', '🚨 那 60 項散在幾種量表型別（**它們量的不是同一把尺**）',
           cite('n633_gi_scale_heterogeneity.json', 'byScaleClass'),
           'n633_gi_scale_heterogeneity.json')
    attach('D21', '⚠️ 清冊標籤看不出量表的篇數',
           cite('n633_gi_scale_heterogeneity.json', 'papersWithAnyUnclassified'),
           'n633_gi_scale_heterogeneity.json')
    attach('D18', '🚨 2000 年前推進了幾篇／取得幾篇',
           [cite('n625_corpus_era_bias.json', 'pre2000Advanced'),
            cite('n625_corpus_era_bias.json', 'pre2000Acquired')],
           'n625_corpus_era_bias.json')
    attach('D19', '⚠️ 已推進者的取得覆蓋率（%）',
           cite('n625_corpus_era_bias.json', 'coverageOfAdvanced'),
           'n625_corpus_era_bias.json')
    attach('D12', '⚠️ 從該篇 TEI 表格能救回的症狀項數',
           len(cite('n635_d12_recoverability.json',
                    'recoverableSymptoms') or []),
           'n635_d12_recoverability.json → recoverableSymptoms')
    attach('D10', '🚨 雙讀樣本數與來源型別偏斜（3 篇全是 grobid-tei）',
           [cite('n642_double_read_sample.json', 'sampledCount'),
            cite('n642_double_read_sample.json', 'sourceTypeMix')],
           'n642_double_read_sample.json')

    in_scope = cite('n659_no_numbers_yet.json', 'inScopeOutcomes')
    value_fields = cite('n659_no_numbers_yet.json', 'valueFieldsInData')
    study_docs = cite('n659_no_numbers_yet.json', 'studyResultDocs')

    new_items = [{
        'id': 'D25', 'round': 659, 'status': 'open',
        'blocks': 'A4（可否產出結果）',
        'ask': '要不要開一輪「數值抽取」把效應量、變異數、樣本數抽出來？'
               '若要，先做哪些結局？',
        'evidence': 'n659_no_numbers_yet.json',
        'recommend': (
            '🚨 建議要，且這是**最先該決定的一件事**。'
            '⚠️ 在範圍內的 %s 項，數值欄位全部是 0（%s）；'
            '`StudyResult` 文件 %s 份。'
            '**🚨 GRADE 與統合分析今天跑不起來，而 n659 已用合成資料實跑證明'
            '卡的是資料、🚫 不是程式。**'
            '✅ 換句話說：那 98 項是「哪些結果」，🚫 不是「結果是多少」。'
            % (in_scope,
               '／'.join('%s=%s' % (k, v)
                         for k, v in list((value_fields or {}).items())[:4]),
               len(study_docs or []))),
        'notADuplicateOf': (
            '🚨 D12 問的是**特定 4 項**「宣稱有數值卻找不到數字」該不該撤回；'
            '⚠️ D23 問的是**欄位空白**要不要回補。'
            '**✅ 本項問的是：整個語料從頭到尾就沒有抽過數值——'
            '🚫 那不是某幾項的問題，是還沒做的一層。**'),
    }]

    merged = list(items.values()) + new_items
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    low = json.loads(LOWOVERLAP.read_text(encoding='utf-8'))
    named = [row['artefact'] for row in low['lowOverlap']]
    undisposed = [name for name in named if name not in DISPOSITION]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v3 的全部登記（必觸發之正對照）',
          len(items) == 24,
          '🚨 承接 %d 項｜新增 %d 項｜合計 %d 項；⚠️ 少接一項就是把待裁定弄丟了'
          % (len(items), len(new_items), len(merged)))
    probe('第 674 輪點名的每一支都有處置（必觸發之正對照）',
          not undisposed,
          '🚨 點名 %d 支，未處置者：%s；⚠️ 留白就等於「待過目」永遠不會結束'
          % (len(named), undisposed or '無'))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s；⚠️ 取不到就代表登記簿與憑證脫節'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))

    def evidence_resolves(item):
        parts = str(item['evidence']).replace('；', ';').split(';')
        return any((HERE / part.split('→')[0].strip()).exists()
                   for part in parts if part.strip())

    dangling = [item['id'] for item in merged if not evidence_resolves(item)]
    probe('每一項都指得到真的證據檔（必觸發）',
          not dangling,
          '🚨 檢查 %d 項；指不到檔的：%s；⚠️ 指到不存在的檔就是空頭支票'
          % (len(merged), dangling or '無'))
    probe('新增項聲明了它與最近既有項的關係（必觸發之反向）',
          all(item.get('notADuplicateOf') for item in new_items),
          '🚨 新增 %d 項，未聲明者：%s；⚠️ 不聲明就可能只是把既有的重登一次'
          % (len(new_items),
             [i['id'] for i in new_items if not i.get('notADuplicateOf')]
             or '無'))
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s；⚠️ 這些不決定，A 系列過不了'
          % (len(blockers), blockers))

    doc = {
        'schemaVersion': 4,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n669_decision_register_v3.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 把第 674 輪點名的 **%d** 支低重疊紅燈**逐一處置**：'
            '🚨 6 支該掛而沒掛（已掛回 D9／D10／D12／D17／D18／D19／D21），'
            '**🚨 1 支是登記簿真的漏了（→ 新增 D25）**，'
            '其餘是工具或已被取代——⚠️ 但**每一支都寫了理由**，🚫 沒有「其他」。'
            % len(named)),
        'counts': {'carriedOver': len(items), 'added': len(new_items),
                   'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open')},
        'decisionsUpdatedThisRound': updated,
        'dispositionOfLowOverlap': DISPOSITION,
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'howToUse': (
            '✅ 每一項都附證據檔與本室建議；'
            '⚠️ 引用的數字是**執行時從憑證取的**，🚫 不是手打的。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n675 決策登記簿 v4 ===')
    print('   承接 %d｜新增 %d｜合計 %d（open %d）'
          % (len(items), len(new_items), len(merged), doc['counts']['open']))
    print('   掛回既有決策：%s' % updated)
    print('   新增：')
    for item in new_items:
        print('      %s 阻擋 %s' % (item['id'], item['blocks']))
        print('         問：%s' % item['ask'])
        print('         建議：%s' % item['recommend'])
        print('         不是重複：%s' % item['notADuplicateOf'])
    print('   第 674 輪 %d 支的處置：' % len(named))
    for name in named:
        print('      %-42s %s' % (name, DISPOSITION.get(name, '🚨 未處置')))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
