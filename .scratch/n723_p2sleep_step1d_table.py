# -*- coding: utf-8 -*-
"""**P2 第一步的三樣產出：表、接續日、判斷。**（n+196 交辦）

## ✅ 對應 protocol 四

1. **一張表**：切題那幾份逐份一列。
2. **一段話**：最新、最高品質那一份的**搜尋截止日**是哪一天。
3. **一個判斷**：**既有回顧是否已經回答了擁有者的問題。**

## 🚨 而這一次的答案與 P3 不同，且**不對稱**

- **甲（睡眠不足 → 攝食）**：✅ 四份獨立統合分析**方向一致**。
- **乙（睡眠介入 → 減重／赤字維持）**：⚠️ **混雜**——
  🚨 而且關鍵的不對稱是：**睡眠限制會害，🚫 但睡眠延長不見得有幫助。**

## 🚫 內容紀律

✅ 只記識別碼、中文摘述、與論文自己報的數字；**🚫 逐字題名不進本 repo**。
🚫 本支不送任何請求——⚠️ 摘要是第 721 輪已抓下的。
"""
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
OUT = HERE / 'n723_p2sleep_step1d_table.json'
SCREEN = HERE / 'n722_p2sleep_step1c_screen.json'
DETAIL = ROOT / 'p2-sleep' / 'step1d-table.json'

# 🚨 逐份填表。⚠️ 數字一律抄論文自己報的，🚫 本室不重算、不推估。
ROWS = [
    {'id': '27804960', 'pubYear': '2017', 'side': '甲',
     'cutoff': '🚨 摘要未載（待讀方法段）',
     'population': '人類介入研究（成人）',
     'intervention': '部分睡眠剝奪',
     'outcome': '能量攝取／能量消耗',
     'finding': '攝取 +385 kcal（95% CI 252–517）；消耗無顯著變化',
     'direction': 'favourable-for-harm',
     'note': '17 篇納入回顧、11 篇（n=172）進入統合'},
    {'id': '32960623', 'pubYear': '2020', 'side': '甲',
     'cutoff': '🚨 摘要只寫檢索執行於 2016-10 與 2019-02（非「檢索至某日」）',
     'population': '健康族群',
     'intervention': '夜間睡眠限制 vs 習慣睡眠',
     'outcome': '飲食能量攝取、ghrelin／leptin',
     'finding': '攝取 +149.86 kcal（95% CI 10.09–289.63，p=0.04）',
     'direction': 'favourable-for-harm',
     'note': '8 篇納入，其中 6 篇可分析總攝取'},
    {'id': '33001515', 'pubYear': '2021', 'side': '甲',
     'cutoff': '⚠️ 摘要寫 1970–2019（區間，非明確截止日）',
     'population': '成人',
     'intervention': '**介入**研究：改變睡眠時數（多為部分限制）',
     'outcome': '飲食攝取',
     'finding': '部分睡眠限制 → 每日 +204 kcal（95% CI 112–295）；SMD 0.37',
     'direction': 'favourable-for-harm',
     'note': '24 篇納入、15 篇統合；🚨 這一份是**介入研究**之統合'},
    {'id': '34620371', 'pubYear': '2021', 'side': '甲',
     'cutoff': '✅ July 2020',
     'population': '50 篇 RCT（43 篇成人、7 篇兒童青少年）',
     'intervention': '睡眠時數（限制）',
     'outcome': '攝食量、體重、食慾、飢餓、進食次數與份量',
     'finding': '睡眠限制 → 上述各項均增加；總能量消耗無變化',
     'direction': 'favourable-for-harm',
     'note': '⚠️ 含兒童青少年 7 篇，🚫 未分層報告'},
    {'id': '42044907', 'pubYear': '2026', 'side': '甲乙',
     'cutoff': '🚨 摘要未載（待讀方法段）',
     'population': '成人 ≥18 歲、排除睡眠呼吸中止',
     'intervention': '🚨 **睡眠介入**：CBT-I／睡眠衛生，以及睡眠延長',
     'outcome': '肥胖指標、飲食攝取、身體活動',
     'finding': ('CBT-I／睡眠衛生 → BMI −0.64 kg/m²（p=0.0006，I²=16%）；'
                 '🚨 **睡眠延長不顯著**（−0.15，p=0.26）；'
                 '肥胖者體重 −5.55 kg、過重者 −0.83 kg'),
     'direction': 'mixed',
     'note': '27 篇納入、25 篇統合'},
    {'id': '42478101', 'pubYear': '2026', 'side': '乙',
     'cutoff': '✅ **inception 至 September 2025**',
     'population': '成人 ≥18 歲、BMI ≥25，進行行為或手術減重介入',
     'intervention': '睡眠作為**暴露**或**介入成分**',
     'outcome': '減重成效',
     'finding': ('🚨 **證據混雜**：睡眠限制**降低**脂肪減少量；'
                 '睡眠時數與減重的關聯**不一致**；'
                 '睡眠滿意度與睡眠效率**可能**支持減重（約半數研究為正）；'
                 '睡眠規律性／時序／清醒度證據稀少'),
     'direction': 'mixed',
     'note': '30 篇（13 RCT＋17 類實驗）、10,944 人、13 國'},
]


def main():
    screen = json.loads(SCREEN.read_text(encoding='utf-8'))
    on_topic = set(screen['onTopic'])
    listed = {r['id'] for r in ROWS}

    stated = [r for r in ROWS if r['cutoff'].startswith('✅')]
    newest = '2025-09'   # 42478101：inception 至 September 2025
    sides = {}
    for row in ROWS:
        for s in row['side']:
            sides.setdefault(s, []).append(row['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('表上的正是第 722 輪判為切題的那幾份（必觸發之正對照）',
          listed == on_topic,
          '🚨 表上 %d 份、切題 %d 份；漏 %s、多 %s；'
          '⚠️ 對不上代表表與篩選脫節'
          % (len(listed), len(on_topic),
             sorted(on_topic - listed) or '無', sorted(listed - on_topic)
             or '無'))
    probe('兩個問題都有人做過（必觸發之正對照）',
          len(sides.get('甲', [])) > 0 and len(sides.get('乙', [])) > 0,
          '🚨 甲 %d 份、乙 %d 份；⚠️ 任一為 0 就代表那一半沒有既有回顧'
          % (len(sides.get('甲', [])), len(sides.get('乙', []))))
    probe('方向欄真的分得出不同答案（必觸發之反向）',
          len({r['direction'] for r in ROWS}) >= 2,
          '🚨 方向分佈：%s；⚠️ 若全部同一個方向，這一欄沒有分辨力'
          % sorted({r['direction'] for r in ROWS}))
    # 🚨 這一道**故意會紅**：⚠️ 六份裡只有兩份的截止日是明確的。
    probe('每一份的搜尋截止日都是明確的日期',
          len(stated) == len(ROWS),
          '🚨 明確載明的 %d／%d 份；⚠️ 其餘要讀方法段——'
          '**🚫 不得用出版年或區間端點頂替**（n+196 三）'
          % (len(stated), len(ROWS)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'p2-step1d-table',
        'assignment': 'n+196：P2（睡眠）第一步之產出一／二／三',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'rows': ROWS,
        'bySide': sides,
        'cutoffStated': [r['id'] for r in stated],
        'cutoffNeedsMethods': [r['id'] for r in ROWS
                               if not r['cutoff'].startswith('✅')],
        # ── 產出二 ──────────────────────────────────────────────
        'searchStartsFrom': (
            '✅ **2025 年 9 月**——⚠️ 最新且直接切題的那一份（`42478101`，2026）'
            '明載檢索自 inception 至 September 2025。'
            '🚨 故若要補原始研究，只需從那之後開始。'),
        # ── 產出三 ──────────────────────────────────────────────
        'answerToProtocolFour3': (
            '🚨 **既有回顧已經回答了一半，而且答案不對稱。**\n'
            '✅ **甲（睡眠不足 → 攝食）：答了，且四份獨立統合分析方向一致**——'
            '部分睡眠限制使每日能量攝取增加約 **+150 至 +385 kcal**，'
            '而能量消耗無顯著變化。\n'
            '⚠️ **乙（睡眠介入 → 減重／赤字維持）：沒有定論**——'
            '🚨 2026 年那份直接切題的回顧（30 篇、10,944 人）結論是**證據混雜**：'
            '睡眠限制會**降低**脂肪減少量，但睡眠時數與減重的關聯不一致。\n'
            '🚨 **而最關鍵的不對稱在這裡**：另一份 2026 年的睡眠介入統合顯示，'
            '**CBT-I／睡眠衛生使 BMI 顯著下降（−0.64），'
            '而「睡眠延長」本身不顯著（−0.15，p=0.26）**。\n'
            '**✅ 即：「別睡不夠」有證據；🚫 「多睡一點就會瘦」沒有。**'),
        'contrastWithP3': (
            '⚠️ P3（壓力性進食）的答案是「做過而多半是零」。'
            '🚨 **P2 不同**：甲那一半有一致的正向證據，'
            '乙那一半有直接切題的最新回顧但結論混雜。'
            '**✅ 故兩邊不是同一種「零」。**'),
        'whatIsStillMissing': (
            '🚨 六份裡只有 **2** 份的檢索截止日是明確日期，'
            '⚠️ 其餘四份要讀方法段——**🚫 不得用出版年或區間端點頂替**。\n'
            '⚠️ 又：甲那四份的截止日多落在 **2019–2020**，'
            '🚨 而乙那兩份是 **2025–2026**——'
            '**⚠️ 兩半的證據新舊差了五年，🚫 不宜直接並排比較強弱。**'),
        'limits': (
            '🚫 本步驟**不做偏誤風險評估**，⚠️ 故產出不得直接當成結論。'
            '🚨 `34620371` 含 7 篇兒童青少年研究且未分層，'
            '**⚠️ 而 protocol 限成人**——該份的效果量不可照面額使用。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p2-step1d-table-private',
         'note': '⚠️ 題名對照留在 step1-candidates.json；本檔只留表列。',
         'rows': ROWS}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')

    print('=== P2 第一步・表／接續日／判斷 ===')
    print('   表列 %d 份（甲 %d／乙 %d，含兼具者）'
          % (len(ROWS), len(sides.get('甲', [])), len(sides.get('乙', []))))
    for row in ROWS:
        print('   %-9s %s %-4s %-34s %s'
              % (row['id'], row['pubYear'], row['side'],
                 row['cutoff'][:32], row['finding'][:52]))
    print()
    print('   接續日：%s' % doc['searchStartsFrom'][:60])
    print('   截止日明確的 %d／%d 份' % (len(stated), len(ROWS)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
