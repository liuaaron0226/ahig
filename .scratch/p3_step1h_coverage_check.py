# -*- coding: utf-8 -*-
"""**去驗自己的答案：368 份從未篩過主題。**（n+195，P3）

## 🚨 先講本室答案的洞

第 605 輪說「搜尋從 2023 年年中補起」。**⚠️ 那個結論建立在 43 份上。**

| | 份數 |
|---|---|
| 全部候選（兩池聯集） | **420** |
| ✅ 已篩過主題 | 52 |
| **🚨 從未篩過主題** | **368** |
| 其中 2024 年以後 | **112** |

> **🚨 若那 112 份裡藏著一份更新的切題回顧，本室的答案就是錯的。**
> ⚠️ 而「沒去看」與「看過而沒有」在報告上長得一樣。

## ✅ 做法：確定性關鍵字先縮小，再逐一看

甲側詞：情緒性進食／壓力性進食／正念／情緒調節…
乙側詞：adherence／attrition／dropout／compliance／retention…
**112 → 26 命中 → 逐一看題名 → 3 份是從未篩過的切題候選。**

## 🚨 而其中一份**真的改變了答案**

| 記錄 | 方法段寫的 | 結果 |
|---|---|---|
| `39489689`（正念介入對肥胖性進食行為，2025） | **search was completed in June 2023** | **🚨 甲半邊自 31 April 2023 更新為 June 2023** |
| `38784136`（CBT 減重之中途退出，2024） | ⚠️ 兩種樣式讀全文皆**找不到檢索日期** | 依 protocol 二之 2 記為**無法接續** |
| `39228092`（地中海飲食介入之依從與留存，2024） | 🚫 **非開放取用**，讀不到方法段 | 截止日不明 |

> **✅ 結論「2023 年年中」站得住，⚠️ 但確切日期動了。**
> **🚨 而它會動，是因為本室去驗了自己的答案——🚫 不是因為它本來就對。**
"""
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

OUT = Path(__file__).resolve().parent / 'p3_step1h_coverage_check.json'
PRIV = ROOT / 'p3-stress-eating'
SCREENS = ('p3_step1c_screen_recent', 'p3_step1f_screen_new_pool',
           'p3_step1g_screen_stress_side')

TOPIC_A = re.compile(r'emotional eating|stress eating|stress-induced eating'
                     r'|disinhibit|mindful|food craving|self-regulation'
                     r'|emotion regulation', re.I)
TOPIC_B = re.compile(r'adherence|attrition|dropout|drop-out|compliance'
                     r'|retention|sustain', re.I)

# ✅ 逐一看過題名之後的判定。🚫 題名不進 repo。
NEWLY_ON_TOPIC = {
    '39489689': {
        'side': 'stress-eating',
        'what': '正念介入對肥胖性進食行為（2025）',
        'statedCutoff': 'June 2023',
        'source': 'full-text methods：search was completed in June 2023',
    },
    '38784136': {
        'side': 'deficit-adherence',
        'what': 'CBT 減重之中途退出（2024）',
        'statedCutoff': None,
        'source': ('⚠️ 開放取用，但兩種樣式讀全文皆找不到檢索日期；'
                   '🚨 依 protocol 二之 2 記為「無法接續」。'
                   '🚫 本室不排除是樣式漏看——但兩遍都沒有。'),
    },
    '39228092': {
        'side': 'deficit-adherence',
        'what': '地中海飲食介入之依從與留存（2024）',
        'statedCutoff': None,
        'source': '🚫 非開放取用，讀不到方法段。',
    },
}


def main():
    old = json.loads((PRIV / 'step1b-cutoff.json')
                     .read_text(encoding='utf-8'))['candidates']
    new = json.loads((PRIV / 'step1e-new-pool.json')
                     .read_text(encoding='utf-8'))['items']
    screened = set()
    for name in SCREENS:
        screened |= set(json.loads(
            (Path(__file__).resolve().parent / (name + '.json'))
            .read_text(encoding='utf-8'))['screened'])

    records = {}
    for key, value in list(old.items()) + list(new.items()):
        records.setdefault(key, {'title': value.get('title') or '',
                                 'year': value.get('pubYear') or ''})
    unscreened = {k: v for k, v in records.items() if k not in screened}
    recent = {k: v for k, v in unscreened.items() if v['year'] >= '2024'}
    hits = {k: v for k, v in recent.items()
            if TOPIC_A.search(v['title']) or TOPIC_B.search(v['title'])}

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('候選與已篩數對得上（必觸發）',
          len(records) > 0 and len(screened) > 0,
          '🚨 對不上就代表本支看的不是同一批；'
          '實得候選 %d／已篩 %d／未篩 %d'
          % (len(records), len(screened), len(unscreened)))
    # 🚨 必觸發之反向：⚠️ 關鍵字要真的縮小，否則它沒有做事。
    probe('關鍵字確實縮小了範圍（必觸發之反向）',
          0 < len(hits) < len(recent),
          '✅ 2024 年以後未篩 %d 份 → 命中 %d 份；'
          '🚨 若等於全部或為零，這個前篩就沒有作用'
          % (len(recent), len(hits)))
    # 🚨 這一道會紅：⚠️ 先前的答案只建立在一小部分上。
    probe('先前的答案涵蓋了全部候選',
          not unscreened,
          '🚨 實得 %d／%d 份從未篩過主題（其中 %d 份是 2024 年以後）；'
          '⚠️ 而「沒去看」與「看過而沒有」在報告上長得一樣'
          % (len(unscreened), len(records), len(recent)))
    # 🚨 這一道也會紅：⚠️ 答案確實被本輪改動了。
    probe('甲半邊的截止日未因本輪而改變', False,
          '🚨 自 31 April 2023 更新為 **June 2023**（%s，方法段逐字）；'
          '✅ 結論「2023 年年中」仍站得住，'
          '⚠️ 但它會動是因為本室去驗了自己的答案' % '39489689')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1h-coverage-check',
        'assignment': 'n+195：P3 第一步（驗證自己的答案）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'totalCandidates': len(records),
        'screenedBefore': len(screened),
        'neverScreened': len(unscreened),
        'neverScreenedRecent': len(recent),
        'keywordHits': len(hits),
        'newlyFoundOnTopic': NEWLY_ON_TOPIC,
        'answerUpdate': {
            'stress-eating': {'was': '31 April 2023', 'now': 'June 2023',
                              'evidence': '39489689 方法段逐字'},
            'deficit-adherence': {'was': 'July 2023', 'now': 'July 2023',
                                  'evidence': '38246879 方法段逐字（第 605 輪）'},
            'conclusion': ('✅ 「搜尋從 2023 年年中補起」仍成立；'
                           '⚠️ 甲半邊的確切日期由四月改為六月。'),
        },
        'whatRemains': (
            '🚨 仍有 %d 份從未篩過主題（%d 份為 2024 年以後但未命中關鍵字）。'
            '⚠️ 關鍵字前篩會漏掉題名不含那些詞的切題回顧——'
            '🚫 故本輪不宣稱已窮盡。'
            % (len(unscreened), len(recent) - len(hits))),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3：驗證自己的答案 ===')
    print('   候選 %d｜已篩 %d｜🚨 未篩 %d（2024 年以後 %d）'
          % (len(records), len(screened), len(unscreened), len(recent)))
    print('   關鍵字命中 %d → ✅ 新找到切題候選 %d 份'
          % (len(hits), len(NEWLY_ON_TOPIC)))
    for key, value in NEWLY_ON_TOPIC.items():
        print('      %s｜%s｜截止 %s' % (key, value['what'],
                                        value['statedCutoff'] or '🚨 不明'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
