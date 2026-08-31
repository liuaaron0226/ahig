# -*- coding: utf-8 -*-
"""**篩甲組（壓力／情緒進食）有截止日的 16 份——切題 4 份。**（n+195，P3）

## ✅ 兩半的截止日終於對得起來

| 半邊 | 最新**切題**回顧的檢索截止 |
|---|---|
| 乙：赤字撐不撐得住 | **July 2023**（✅ 已讀方法段確認） |
| **甲：減少壓力／情緒進食** | **31 April 2023**（⚠️ 論文自述如此，見下） |

> **✅ 故 protocol 四之 2 的答案是一致的：我們的搜尋從 2023 年年中補起。**

## ⚠️ 一個要照抄不要改的地方

`39763344` 自己寫的是 **31 April 2023**——🚨 而四月只有 30 天。
**✅ 本室照抄論文自己寫的**，🚫 不替它改成 30 或 3 月；
⚠️ 只在此註明這個不一致，**🚨 那是讀方法段時要問的事，不是這裡能斷的。**

## ✅ 順帶撿到一份對 **P2（睡眠）** 直接相關的

`37242168`：睡眠不足 ↔ 情緒性進食 ↔ 肥胖之系統性回顧（截止 31 December 2022）。
⚠️ 對本 protocol 只是相鄰；**✅ 但擁有者的順序裡 P2 就排在 P3 之後**，
🚨 故先記下來，🚫 不要等到開 P2 時重找。

## 🚫 一樣的紀律：理由取自固定詞彙、題名不進 repo、截止日只抄論文自己寫的
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

OUT = Path(__file__).resolve().parent / 'p3_step1g_screen_stress_side.json'
SURVEY = Path(__file__).resolve().parent / 'p3_step1_survey.json'
SCAN = Path(__file__).resolve().parent / 'p3_step1b_cutoff_scan.json'

REASONS = {
    'on-topic': '✅ 成人、介入、結局為壓力／情緒驅動的進食',
    'adjacent': '⚠️ 相鄰：描述性關聯、疾患族群、手術，或結局換成了別的東西',
    'wrong-population': '🚫 兒童、青少年或大學生為主',
    'off-topic': '🚫 不在 protocol 一的問題範圍內',
    'excluded-by-protocol-drugs': '🚫 protocol 一明文不回答藥物',
}

SCREEN = {
    '39763344': ('on-topic',
                 '✅ 成人過重／肥胖之**情緒性進食介入**，並拆解行為改變技術'),
    '36768088': ('on-topic', '✅ 同一問題的較早一版'),
    '32551798': ('on-topic', '✅ **正念**介入對問題性進食行為——protocol 三所列類別'),
    '36763199': ('on-topic', '✅ **接納與承諾治療**對進食行為'),
    '37012653': ('adjacent', '⚠️ 情緒性進食之**盛行與關聯**，🚫 不是介入'),
    '37242168': ('adjacent',
                 '⚠️ 睡眠 ↔ 情緒性進食 ↔ 肥胖；🚨 **對 P2（睡眠）直接相關**'),
    '39940059': ('adjacent', '⚠️ 情緒調節與失序進食，族群含青少年'),
    '40899275': ('adjacent', '⚠️ 心理社會介入，族群為**飲食疾患**'),
    '32671964': ('adjacent', '⚠️ **減重手術**後之情緒性進食變化'),
    '33103340': ('adjacent', '⚠️ 行為體重管理對**心理健康**——結局換了'),
    '41418451': ('adjacent', '⚠️ 肥胖者之**述情障礙**，🚫 不是介入'),
    '42323682': ('wrong-population', '🚫 美國大學生'),
    '35565862': ('wrong-population', '🚫 親職餵食與**兒童**進食行為'),
    '42666688': ('excluded-by-protocol-drugs', '🚫 GLP-1 受體促效劑'),
    '40864442': ('off-topic', '🚫 皮膚科族群之失序進食'),
    '41344801': ('adjacent', '⚠️ 限時進食之質性經驗——屬乙半邊，第 601 輪已記'),
}

# 🚨 只抄論文自己寫的日期。⚠️ 四月沒有 31 日，而論文就是這樣寫的。
CUTOFF_ANOMALY = {
    '39763344': ('31 April 2023',
                 '🚨 四月只有 30 天。✅ 照抄，🚫 不代它更正——'
                 '⚠️ 那是讀方法段時要問的事。'),
}


def main():
    survey = json.loads(SURVEY.read_text(encoding='utf-8'))
    scan = json.loads(SCAN.read_text(encoding='utf-8'))
    a_ids = {r['id'] for r in survey['sets']['stress-eating']['records']}
    stated = {k: v for k, v in scan['statedCutoffByRecord'].items()
              if k in a_ids}

    unknown = sorted(set(SCREEN) - set(stated))
    missing = sorted(set(stated) - set(SCREEN))
    bad_reason = sorted(k for k, (r, _n) in SCREEN.items() if r not in REASONS)
    tally = Counter(r for r, _n in SCREEN.values())

    on_topic = {k: stated[k] for k, (r, _n) in SCREEN.items()
                if r == 'on-topic' and k in stated}
    recent = [k for k, v in on_topic.items()
              if any(y in v for y in ('2024', '2025', '2026'))]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('篩的正是甲組那 16 份（必觸發）',
          not unknown and not missing,
          '🚨 篩錯對象與篩對的長得一樣；額外 %s，漏掉 %s'
          % (unknown or '無', missing or '無'))
    probe('理由都在固定詞彙裡（必觸發之反向）', not bad_reason,
          '🚨 自創理由等於沒有分類；實得 %s' % (bad_reason or '無'))
    probe('甲半邊至少有一份直接切題（必觸發）', bool(on_topic),
          '✅ 實得 %d 份：%s；🚨 若一份都沒有，甲半邊就沒有可用的截止日'
          % (len(on_topic), on_topic))
    # 🚨 這一道會紅，且與乙半邊同一結論。
    probe('存在 2024 年以後截止的切題回顧（甲半邊）', bool(recent),
          '🚨 甲半邊切題者的截止日為 %s——⚠️ 最新僅到 2023 年，'
          '✅ 與乙半邊的 July 2023 一致，🚫 故仍要補 2023 年年中以後' % on_topic)

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1g-screen-stress-side',
        'assignment': 'n+195：P3 第一步（篩甲半邊）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'reasonVocabulary': REASONS,
        'screened': {k: {'reason': r, 'note': n, 'statedCutoff': stated.get(k)}
                     for k, (r, n) in SCREEN.items()},
        'tally': dict(tally),
        'onTopic': on_topic,
        'cutoffAnomaly': CUTOFF_ANOMALY,
        'bothHalves': {
            'stress-eating': '31 April 2023（⚠️ 論文自述，見 cutoffAnomaly）',
            'deficit-adherence': 'July 2023（✅ 已讀方法段確認）',
            'conclusion': ('✅ 兩半一致：**我們的搜尋從 2023 年年中補起**。'
                           '🚨 而這也再次確認「既有回顧已回答、不必做」不成立。'),
        },
        'crossDomainFind': {
            'record': '37242168',
            'why': ('🚨 睡眠 ↔ 情緒性進食 ↔ 肥胖之系統性回顧（截止 '
                    '31 December 2022）。⚠️ 對本 protocol 只是相鄰，'
                    '✅ 但擁有者的順序裡 P2 睡眠緊接在後——'
                    '🚫 先記下來，不要等到開 P2 再重找。'),
        },
        'stillProvisional': (
            '⚠️ 甲半邊的截止日仍取自**摘要**；🚫 尚未讀方法段。'
            '🚨 而乙半邊那一份已讀過方法段，逐字為 '
            '「searched from inception to July 2023」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3：篩甲半邊（16 份有截止日者）===')
    print('   判定分布：%s' % dict(tally))
    print('   ✅ 直接切題 %d 份：%s' % (len(on_topic), on_topic))
    print('   🚨 兩半的最新切題截止：甲 31 April 2023｜乙 July 2023')
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
