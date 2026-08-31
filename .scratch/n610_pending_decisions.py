# -*- coding: utf-8 -*-
"""**待裁定清單：一次讀完，並先自我核銷。**（第 610 輪）

## 🚨 為什麼做這個

⚠️ 待裁定已累積到十餘項，**散在十幾則回報裡**。
🚨 協調者回來時要面對的是一面牆，而**牆與空白一樣不可行動**。

## ✅ 本支做三件事

1. **併成一張表**：每一項附**證據檔**、**本室建議**、**它擋住哪一條門檻**。
2. **先自我核銷**：⚠️ 有些項目已被後來的證據解決或修正，🚫 不該還掛著。
3. **驗證每一項都指得到真的檔案**——🚨 指不到的引用比沒有引用更糟。

## 🚫 本支不新增任何待裁定項目
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n610_pending_decisions.json'

# status：open ／ self-resolved（本室已用證據解決）／ amended（已被後續修正）
ITEMS = [
    {'id': 'D1', 'round': 579, 'status': 'open', 'blocks': 'A1',
     'ask': 'A1「全語料同一版請求」指的是「同版」還是「都看過儀器清單」？',
     'evidence': 'n579_request_version_split.json',
     'recommend': ('⚠️ 兩種讀法差 41 篇重讀。✅ 本室建議取「同版」：'
                   '🚨 因為實測損害只有 6 項／1 篇，而重讀 41 篇的成本遠高於此。')},
    {'id': 'D2', 'round': 585, 'status': 'open', 'blocks': 'A4',
     'ask': '更正表：15 項改名、5 項撤回，是否施行？（🚨 須與 D3 一起決定）',
     'evidence': 'n585_blocked_drafts_errata.json',
     'recommend': ('✅ 建議施行。⚠️ 撤回那 5 項是「平均功率當成完成時間」，'
                   '🚫 改名救不了。')},
    {'id': 'D3', 'round': 584, 'status': 'open', 'blocks': 'A4',
     'ask': '博士論文與期刊論文那一對，是否合併為一個 study？',
     'evidence': 'n584_thesis_and_hidden_duplicate.json',
     'recommend': ('🚨 建議合併。⚠️ 改名會讓期刊那篇拿回 9 項，'
                   '而其中的肌肉肝醣正是論文 Study 2 的同一批 8 人。')},
    {'id': 'D4', 'round': 594, 'status': 'self-resolved', 'blocks': 'A4',
     'ask': '切片器械是否改名為 needle-biopsy-vastus-lateralis？',
     'evidence': 'n594_a3_first_measurement.json',
     'recommend': ('🚫 不改。✅ 第二位讀者記載取樣器械為 Weil-Blakesley '
                   'conchotome——⚠️ 那 3 項移到「契約缺口」。')},
    {'id': 'D5', 'round': 588, 'status': 'open', 'blocks': '報表可信度',
     'ask': '兩個理由碼各要拆成幾碼？',
     'evidence': 'n588_reason_code_conflation.json',
     'recommend': ('⚠️ 劑量是 3 種、效應量是 2 種。'
                   '🚨 而 dose=0 那一種建議**根本不走排除路徑**——它是對照組。')},
    {'id': 'D6', 'round': 588, 'status': 'open', 'blocks': 'GI 家族（61%）',
     'ask': 'inScopeEffectMeasures 要不要收 median？',
     'evidence': 'n588_reason_code_conflation.json',
     'recommend': ('✅ 建議收。⚠️ GI 嚴重度是次序尺度，median 配 IQR 是自然寫法；'
                   '🚨 不收的話那個佔六成的家族實質上收不到。')},
    {'id': 'D7', 'round': 589, 'status': 'open', 'blocks': '1 項結局',
     'ask': 'g/min → g/h 的單位換算算不算「換算論文沒寫的東西」？',
     'evidence': 'n589_dose_not_reported_audit.json',
     'recommend': ('✅ 建議不算。⚠️ 那與「6% 溶液 × 284 ml」推出 g/h 不同——'
                   '前者只是換單位。')},
    {'id': 'D8', 'round': 591, 'status': 'open', 'blocks': '判定一致性',
     'ask': '明寫 null 與鍵缺席應否等價？policy 層的 null 該不該拒絕載入？',
     'evidence': 'n592_default_only_when_absent.json',
     'recommend': ('✅ 建議等價，且理由碼須說「論文未陳述 X」，'
                   '🚫 不得說「X 不在範圍內」。⚠️ policy 層的 null 應直接拒絕載入。')},
    {'id': 'D9', 'round': 593, 'status': 'open', 'blocks': '判定一致性',
     'ask': '兩條路徑的上限判斷應否合為同一段程式？',
     'evidence': 'n593_cap_paths_diverge.json',
     'recommend': ('✅ 建議合一。🚨 且 decide_inventory 不得產出'
                   '「摘要說 0、逐項說在範圍內」的自我矛盾文件。')},
    {'id': 'D10', 'round': 596, 'status': 'open', 'blocks': 'A2',
     'ask': 'adjudicate() 應否比對「配置」而不只是「集合成員」？',
     'evidence': 'n596_allocation_replicates.json',
     'recommend': ('✅ 建議要。⚠️ 實測三篇雙讀全部有配置差異而佇列為 0，'
                   '🚨 其中兩篇的成因（granularity）清單裡早就有名字。')},
    {'id': 'D11', 'round': 596, 'status': 'open', 'blocks': 'GI 家族',
     'ask': 'gi-symptom-incidence 的分母是人數還是時點？',
     'evidence': 'n596_allocation_replicates.json',
     'recommend': ('🚨 必須定義。⚠️ 實測兩篇論文一篇用時點（8×6＝48）、'
                   '一篇用人數（12），🚫 兩種分母合成在一起沒有意義。')},
    {'id': 'D12', 'round': 597, 'status': 'open', 'blocks': 'A2',
     'ask': '宣稱有數值而文件裡沒有那個數字的 4 項，要不要撤回？',
     'evidence': 'n597_numeric_result_unsupported.json',
     'recommend': ('⚠️ 本室不判成因（🚫 不定罪另一個視窗）。'
                   '✅ 但那 4 項的症狀在全文裡各只出現一次且無數字。')},
    {'id': 'D13', 'round': 598, 'status': 'amended', 'blocks': 'A2',
     'ask': '座標指向方法段的 7 項要不要請該視窗改指；要不要立機檢？',
     'evidence': 'n609_methods_title_check.json',
     'recommend': ('✅ 第 609 輪修正：若要立機檢，須**兩條並列**'
                   '（標題式＋內容式）並分開記——🚨 任一條單獨跑都會回報「沒事」。')},
    {'id': 'D14', 'round': 608, 'status': 'open', 'blocks': 'A2／A3 產能',
     'ask': 'write_page_drafts 是否該區分「新增一篇」與「改寫既有」？',
     'evidence': 'n608_fourth_double_read.json',
     'recommend': ('✅ 建議區分。⚠️ 現況讓多篇頁面的第二線實質上只能讀一篇；'
                   '🚫 本室未繞過，該份讀暫存於私有根。')},
    {'id': 'D15', 'round': 608, 'status': 'open', 'blocks': '契約表達力',
     'ask': '契約要不要收「條件間的百分比差」這種效應量？',
     'evidence': 'n608_fourth_double_read.json',
     'recommend': ('⚠️ 實測兩位讀者各填 mean 與 MD，兩者都不精確而都通過。'
                   '🚨 不收的話，那一軸會繼續安靜地吸收它。')},
    {'id': 'D16', 'round': 607, 'status': 'open', 'blocks': 'P3 下一步',
     'ask': '既有回顧沒回答問題，P3 是否進入補 2023 年年中以後的原始研究？',
     'evidence': 'p3_step1i_table.json',
     'recommend': ('⚠️ 那會用到 B.11 那台機器，'
                   '🚨 而它的內容門檻 A1／A2／A4 尚未過。')},
]


def main():
    missing = [i['id'] for i in ITEMS if not (HERE / i['evidence']).exists()]
    by_status = Counter(i['status'] for i in ITEMS)
    by_blocks = Counter(i['blocks'] for i in ITEMS if i['status'] == 'open')
    open_items = [i for i in ITEMS if i['status'] == 'open']

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一項都指得到真的證據檔（必觸發）', not missing,
          '🚨 指不到的引用比沒有引用更糟——⚠️ 它看起來有根據；實得缺 %s'
          % (missing or '無'))
    probe('清單裡有已自我核銷的項目（必觸發之反向）',
          by_status.get('self-resolved', 0) + by_status.get('amended', 0) > 0,
          '✅ 實得自我核銷 %d、已修正 %d；🚨 若全部都是 open，'
          '代表本室從未回頭結清自己提的問題'
          % (by_status.get('self-resolved', 0), by_status.get('amended', 0)))
    probe('每一項都有本室的建議（必觸發）',
          all(i['recommend'] for i in ITEMS),
          '🚨 只提問而不建議，等於把工作原封退回去')
    # 🚨 這一道會紅，而它就是本支存在的理由。
    probe('沒有待裁定積壓', not open_items,
          '🚨 實得 %d 項待裁定，分布於 %s；⚠️ 而其中 %d 項擋著內容門檻'
          % (len(open_items), dict(by_blocks),
             sum(n for k, n in by_blocks.items() if k.startswith('A'))))

    doc = {
        'schemaVersion': 1,
        'documentType': 'pending-decisions-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'addsNothingNew': '🚫 本支不新增任何待裁定項目，✅ 只彙整與核銷。',
        'counts': {'total': len(ITEMS), **dict(by_status)},
        'openByBlocking': dict(by_blocks),
        'items': ITEMS,
        'howToUse': (
            '✅ 每一項都附證據檔與本室建議。'
            '⚠️ 建議可以被推翻，🚫 但不必從十幾則回報裡重新拼湊。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n610 待裁定清單 ===')
    print('   共 %d 項｜%s' % (len(ITEMS), dict(by_status)))
    print('   待裁定者擋住：%s' % dict(by_blocks))
    for item in ITEMS:
        mark = {'open': '📮', 'self-resolved': '✅', 'amended': '⚠️'}[item['status']]
        print('   %s %-4s（第 %d 輪／擋 %s）%s'
              % (mark, item['id'], item['round'], item['blocks'],
                 item['ask'][:44]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
