# -*- coding: utf-8 -*-
"""**篩新池裡有自述截止日的 27 份——切題的只有 1 份。**（n+195，P3）

## ✅ 而那 1 份給了 protocol 四之 2 一個可用的答案

> **`38246879`：計畫性暫停 vs 持續能量限制，對減重與失訪的影響（系統性回顧）。
> 檢索截止 July 2023。**

⚠️ 它問的正是「怎麼讓人撐得住赤字」——**✅ 這是目前唯一直接切題的。**

**🚨 故暫定結論：我們自己的搜尋要從 2023 年 7 月起算，約兩年。**
⚠️ 那也印證第 603 輪：**「既有回顧已回答、不必做」這個最好的結果不成立。**

## 🚨 其餘 26 份為什麼不算

⚠️ 多數是「某種介入能不能減重」——**🚫 那不是本 protocol 的問題。**
🚨 protocol 一問的是**減少壓力性進食**或**提高赤字維持率**，
**⚠️ 而「這個飲食法能減幾公斤」不回答那兩件事的任何一件。**

## 🚫 一樣的紀律

- 理由取自固定詞彙，🚫 不得自創。
- 🚫 題名不進 repo；⚠️ 判定依私有根裡的題名與摘要。
- 🚨 截止日只抄論文自己寫的。
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

OUT = Path(__file__).resolve().parent / 'p3_step1f_screen_new_pool.json'
PRIOR = Path(__file__).resolve().parent / 'p3_step1e_new_pool_cutoff.json'

REASONS = {
    'on-topic': '✅ 直接回答 protocol 一的問題',
    'adjacent-adherence': '⚠️ 與依從性相鄰，✅ 可留但要註記差異',
    'off-topic': '🚫 是「某種介入能不能減重／治某病」，非本 protocol 之問題',
    'wrong-population': '🚫 族群為兒童或青少年（protocol 二之 3 要成人）',
    'excluded-by-protocol-drugs': '🚫 protocol 一明文不回答藥物',
}

SCREEN = {
    '38246879': ('on-topic',
                 '✅ 計畫性暫停 vs 持續能量限制，結局含**失訪**'
                 '——🚨 正是「撐不撐得住赤字」'),
    '37475687': ('adjacent-adherence',
                 '⚠️ 暴食症族群之行為減重結果；🚨 暴食≠壓力性進食（protocol 五）'),
    '35765718': ('adjacent-adherence', '⚠️ 個別 vs 團體之遞送形式'),
    '32027072': ('adjacent-adherence', '⚠️ 重度肥胖之長期非手術介入'),
    '28695579': ('adjacent-adherence', '⚠️ 第三層體重管理服務'),
    '30622090': ('adjacent-adherence', '⚠️ 網路數位介入之遞送形式'),
    '21552423': ('adjacent-adherence', '⚠️ 網路行為介入'),
    '19754633': ('adjacent-adherence', '⚠️ 網路介入'),
    '25134692': ('adjacent-adherence', '⚠️ 基層醫療之科技輔助介入'),
    '24739257': ('adjacent-adherence',
                 '🚨 減重**後**維持——⚠️ 正是第 601 輪查明的那個不同構念'),
    '27108215': ('wrong-population', '🚫 兒童體重管理之依從性'),
    '25512008': ('wrong-population', '🚫 兒童與青少年'),
    '29679513': ('off-topic', '🚫 飲食疾患治療中的體重抑制'),
    '18006966': ('excluded-by-protocol-drugs', '🚫 長期藥物治療'),
    '15674929': ('excluded-by-protocol-drugs', '🚫 藥物'),
    '39625083': ('off-topic', '🚫 膝骨關節炎之運動'),
    '35082903': ('off-topic', '🚫 中草藥對血脂'),
    '33441384': ('off-topic', '🚫 低碳水與第二型糖尿病緩解'),
    '32983422': ('off-topic', '🚫 抗發炎飲食與關節炎'),
    '35349233': ('off-topic', '🚫 飲料攝取與生長／肥胖風險'),
    '32588435': ('off-topic', '🚫 生酮飲食與難治型癲癇'),
    '31305905': ('off-topic', '🚫 高蛋白飲食與第二型糖尿病'),
    '31309536': ('off-topic', '🚫 乾癬之生活型態'),
    '31425606': ('off-topic', '🚫 腎病症候群之白蛋白輸注'),
    '30480770': ('off-topic', '🚫 職場政策之推行策略'),
    '18700873': ('off-topic', '🚫 低碳水 vs 低脂之減重效果'),
    '12704397': ('off-topic', '🚫 代餐策略之減重效果'),
}


def main():
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    stated = prior['statedCutoffByRecord']

    unknown = sorted(set(SCREEN) - set(stated))
    missing = sorted(set(stated) - set(SCREEN))
    bad_reason = sorted(k for k, (r, _n) in SCREEN.items() if r not in REASONS)
    tally = Counter(r for r, _n in SCREEN.values())

    on_topic = [k for k, (r, _n) in SCREEN.items() if r == 'on-topic']
    cutoffs = {k: stated[k] for k in on_topic if k in stated}
    recent_on_topic = [k for k, v in cutoffs.items()
                       if '2024' in v or '2025' in v or '2026' in v]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('篩的正是那 27 份（必觸發）',
          not unknown and not missing,
          '🚨 篩錯對象與篩對的長得一樣；額外 %s，漏掉 %s'
          % (unknown or '無', missing or '無'))
    probe('理由都在固定詞彙裡（必觸發之反向）', not bad_reason,
          '🚨 自創理由等於沒有分類；實得 %s' % (bad_reason or '無'))
    probe('至少有一份直接切題（必觸發）', bool(on_topic),
          '✅ 實得 %s；🚨 若一份都沒有，本輪就沒有可用的截止日，'
          '⚠️ 而那也要據實說' % (on_topic or '無'))
    # 🚨 這一道會紅：⚠️ 切題的那一份不夠新。
    probe('存在 2024 年以後截止的切題回顧', bool(recent_on_topic),
          '🚨 切題者的截止日為 %s——⚠️ 故我們的搜尋要從那之後補起，'
          '🚫 「不必做」不成立' % cutoffs)

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1f-screen-new-pool',
        'assignment': 'n+195：P3 第一步（篩新池之有截止日者）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'reasonVocabulary': REASONS,
        'screened': {k: {'reason': r, 'note': n, 'statedCutoff': stated.get(k)}
                     for k, (r, n) in SCREEN.items()},
        'tally': dict(tally),
        'onTopic': on_topic,
        'onTopicCutoffs': cutoffs,
        'provisionalAnswerToProtocolFour2': (
            '✅ 目前唯一直接切題的回顧檢索到 **July 2023**。'
            '🚨 故我們自己的搜尋要從 2023 年 7 月起算，約兩年。'
            '⚠️ 仍為暫定：🚫 尚未讀其方法段，且甲組 91 份未篩。'),
        'answerToProtocolFour3': (
            '⚠️ 目前跡象：**「既有回顧已回答、本領域到此為止」不成立**。'
            '🚨 而 protocol 四之 3 說那個結果最好——'
            '✅ 不成立不是失敗，🚫 只是我們知道要補哪一段了。'),
        'whyMostFail': (
            '🚨 多數落選者是「某種介入能不能減重／治某病」。'
            '⚠️ 而 protocol 一問的是**減少壓力性進食**或**提高赤字維持率**——'
            '🚫 「這個飲食法能減幾公斤」不回答那兩件事的任何一件。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3：篩新池之有截止日者（27 份）===')
    print('   判定分布：%s' % dict(tally))
    print('   ✅ 直接切題：%s｜截止日 %s' % (on_topic, cutoffs))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
