# -*- coding: utf-8 -*-
"""**P2 第一步（續）：64 份逐份篩切題性。**（n+196 交辦）

## ✅ 與 P3 同一套（`p3_step1c_screen_recent.py`）

🚨 **逐份判讀**，🚫 不用關鍵字規則——⚠️ 本 run 已三次做出沒有鑑別力的關鍵字規則。
✅ 產物只記**識別碼、判定、理由**，**🚫 題名不進本 repo**（n+196 三之 1）。

## 🚨 篩選要問的三件事（照 protocol）

1. 是**系統性回顧／統合分析**嗎（🚫 計畫書不算）
2. 族群是**成人**嗎
3. **方向對嗎**——⚠️ 要的是「睡眠 → 食慾／減脂依從」，
   **🚫 不是「飲食／運動／手術 → 睡眠」**

## 🚨 兩個特別要記的

- **同一篇兩筆**：`IND607690744` 與 `33876534` 是同一份回顧的兩個紀錄——
  ⚠️ 正是 n+196 第四節說的「研究 vs 論文」，**🚨 這次出現在回顧層級**。
- **計畫書**：有一筆是 `systematic review protocol`，🚫 沒有結果可用
  （⚠️ P3 第 600 輪踩過同一個坑）。
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
OUT = HERE / 'n722_p2sleep_step1c_screen.json'
PRIOR = HERE / 'n721_p2sleep_step1b_cutoff.json'

# 🚨 逐份判讀的結果。⚠️ 理由寫中文，🚫 題名一個字都不進 repo。
VERDICTS = {
    # ✅ 直接切題
    '42478101': ('✅ 直接切題・乙', '睡眠與成人減重介入成效'),
    '42044907': ('✅ 直接切題・甲乙', '行為性睡眠介入 → 肥胖指標與飲食攝取'),
    '33001515': ('✅ 直接切題・甲', '睡眠健康 → 飲食攝取，且為介入研究之統合'),
    '34620371': ('✅ 直接切題・甲', '睡眠時數 → 進食慾望與實際攝食量'),
    '32960623': ('✅ 直接切題・甲', '部分睡眠剝奪 → 飲食能量攝取'),
    '27804960': ('✅ 直接切題・甲', '部分睡眠剝奪 → 能量平衡'),
    # ⚠️ 相鄰：方向對、但結局不是食慾或赤字依從
    '40843663': ('⚠️ 相鄰', '睡眠限制 → 食慾調節荷爾蒙（非攝食行為本身）'),
    '32537891': ('⚠️ 相鄰', '短睡眠 → 食慾調節荷爾蒙（觀察性）'),
    '31166059': ('⚠️ 相鄰', '睡眠延長介入，但結局是心代謝風險因子'),
    '30870662': ('⚠️ 相鄰', '睡眠限制 → 代謝參數'),
    '26098388': ('⚠️ 相鄰', '睡眠時數之隨機對照試驗，結局待讀方法段確認'),
    '18239586': ('⚠️ 相鄰', '短睡眠與體重增加（觀察性，非赤字依從）'),
    '22836029': ('⚠️ 相鄰', '進食驅力的生活型態決定因子，睡眠僅其一'),
    '40980047': ('⚠️ 相鄰', '夜食症候群之介入（與睡眠—進食交界，但族群特殊）'),
    # 🚫 方向相反：X → 睡眠
    '41783703': ('🚫 方向相反', '運動 → 睡眠品質與 BMI'),
    '41076324': ('🚫 方向相反', '間歇性斷食 → 睡眠'),
    '41202521': ('🚫 方向相反', '間歇性斷食 → 睡眠品質與心代謝'),
    '40257510': ('🚫 方向相反', '限時進食 → 睡眠品質與身體組成'),
    '36083207': ('🚫 方向相反', '蛋白質攝取 → 睡眠'),
    '33876534': ('🚫 方向相反', '巨量營養素攝取 → 睡眠'),
    'IND607690744': ('🚨 同一篇之另一筆', '與 33876534 為同一份回顧'),
    '33919698': ('🚫 方向相反', '醣類 → 睡眠'),
    '39964667': ('🚫 方向相反', '減重手術 → 睡眠結構'),
    '31911659': ('🚫 方向相反', '多專業減重介入 → 阻塞型睡眠呼吸中止'),
    '42061031': ('🚫 方向相反', '心理介入 → 睡眠呼吸中止患者之體重管理'),
    '39605179': ('🚫 方向相反', '睡眠時序改變 → 血糖（結局非本題）'),
    # 🚫 族群不符
    '39363896': ('🚫 族群不符', '兒童肥胖'),
    '31100467': ('🚫 族群不符', '青少年'),
    '41302350': ('🚫 族群不符', '青少年、且暴露為社群媒體'),
    # 🚫 是計畫書
    '42504974': ('🚫 是計畫書', '系統性回顧之計畫書，無結果可用'),
    # 🚫 離題
    '41707432': ('🚫 離題', '齋戒與癲癇'),
    '41803962': ('🚫 離題', '限時進食與第二型糖尿病'),
    '41889380': ('🚫 離題', '中國肥胖危險因子總覽'),
    '40816297': ('🚫 離題', '運動時機'),
    '41750826': ('🚫 離題', '牛磺酸與認知'),
    '41318106': ('🚫 離題', '糖尿病長者跌倒'),
    '41939748': ('🚫 離題', '睡眠呼吸中止之各式治療比較'),
    '42394382': ('🚫 離題', '肝醣儲積症之連續血糖監測'),
    '41484800': ('🚫 離題', '跆拳道訓練負荷與傷害'),
    '42118376': ('🚫 離題', '飲食失調風險之個體因子'),
    '41450504': ('🚫 離題', '長者口腔衰弱'),
    '41220708': ('🚫 離題', '情緒性進食之性別差異（屬 P3 題目）'),
    '40026259': ('🚫 離題', '褪黑激素與心衰竭'),
    '40046125': ('🚫 離題', '日常健康行為與日常生活功能'),
    '39930945': ('🚫 離題', '睡眠問題之藥物與非藥物處置'),
    '40454897': ('🚫 離題', '同上，另一族群'),
    '38643903': ('🚫 離題', '健康與非體重結局之觀察性研究'),
    '38969775': ('🚫 離題', 'eHealth／mHealth 介入之傘狀回顧'),
    '39175092': ('🚫 離題', '泌乳延遲'),
    '38361353': ('🚫 離題', '孕期居家運動'),
    '37938356': ('🚫 離題', '放鬆技術與癌症病人'),
    '37477854': ('🚫 離題', '超加工食品之雙向關聯'),
    '36507753': ('🚫 離題', '長牙不適之處置'),
    '35466271': ('🚫 離題', '呼吸肌訓練與睡眠呼吸中止'),
    '35141156': ('🚫 離題', '沙利竇邁與化療噁心嘔吐'),
    '32616106': ('🚫 離題', '飽足商數量表之使用'),
    '32590219': ('🚫 離題', '感恩介入'),
    '31726017': ('🚫 離題', '肥胖低通氣症候群之陽壓治療'),
    '31365842': ('🚫 離題', '同上，通氣模式比較'),
    '30957509': ('🚫 離題', '職場睡眠健康promotion'),
    '29923186': ('🚫 離題', '肥胖之環境危險因子與非藥物介入總覽'),
    '25028535': ('🚫 離題', 'quetiapine 與雙相憂鬱'),
    '24788672': ('🚫 離題', 'lisdexamfetamine 安全性'),
    '23881308': ('🚫 離題', '喪親後健康行為改變'),
}


def main():
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    private = json.loads(
        (ROOT / 'p2-sleep' / 'step1-candidates.json').read_text(
            encoding='utf-8'))
    ids = sorted({r['id'] for recs in private['sets'].values()
                  for r in recs})

    judged = {k: v for k, v in VERDICTS.items() if k in ids}
    unjudged = [k for k in ids if k not in VERDICTS]
    extra = [k for k in VERDICTS if k not in ids]

    buckets = Counter(v[0] for v in judged.values())
    on_topic = sorted(k for k, v in judged.items()
                      if v[0].startswith('✅'))
    adjacent = sorted(k for k, v in judged.items()
                      if v[0].startswith('⚠️'))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一份候選都判過了（必觸發之正對照）',
          not unjudged and len(judged) == len(ids),
          '🚨 候選 %d 份、判過 %d 份、漏判 %s、判到清單外的 %s；'
          '⚠️ 漏判的話「幾份切題」就不是全貌'
          % (len(ids), len(judged), unjudged or '無', extra or '無'))
    probe('判定真的分得出差別（必觸發之反向）',
          len(buckets) >= 4,
          '🚨 判定分佈：%s；⚠️ 若全部同一類，這一遍等於沒篩'
          % dict(buckets.most_common()))
    probe('本支沒有把題名寫進 repo（必觸發之反向）',
          all('sleep' not in v[1].lower() and 'systematic' not in v[1].lower()
              for v in judged.values()),
          '✅ 理由一律中文摘述；🚫 題名只留私有根')
    # 🚨 這一道是答案。
    probe('切題的份數足以回答擁有者的問題',
          len(on_topic) >= 3,
          '🚨 直接切題 %d 份、相鄰 %d 份；'
          '⚠️ 而「足夠」還要看它們的檢索截止日與族群——**🚫 本支不下那個判斷**'
          % (len(on_topic), len(adjacent)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'p2-step1c-screen',
        'assignment': 'n+196：P2（睡眠）第一步之切題性篩選',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'method': ('✅ 逐份判讀（與 `p3_step1c_screen_recent.py` 同一套），'
                   '🚫 不用關鍵字規則。'),
        'candidates': len(ids),
        'verdictCounts': dict(buckets.most_common()),
        'onTopic': on_topic,
        'adjacent': adjacent,
        'verdicts': {k: {'verdict': v[0], 'why': v[1]}
                     for k, v in sorted(judged.items())},
        'duplicatePairAtReviewLevel': {
            'ids': ['IND607690744', '33876534'],
            'note': ('🚨 同一份回顧的兩個紀錄——⚠️ 正是 n+196 第四節說的'
                     '「研究 vs 論文」，**🚨 這次出現在回顧層級**；'
                     '**🚫 合成時不得當成兩筆獨立證據。**'),
        },
        'protocolNotReview': {
            'ids': ['42504974'],
            'note': ('🚫 是系統性回顧的**計畫書**，沒有結果可用——'
                     '⚠️ P3 第 600 輪踩過同一個坑。'),
        },
        'directionTrap': (
            '🚨 離題裡最大的一族是**方向相反**：'
            '⚠️ 飲食／運動／手術 → 睡眠，'
            '**🚫 而本題要的是睡眠 → 食慾／減脂依從。**'
            '✅ 查詢用 `TITLE_ABS` 兩邊都會命中，故這一遍非篩不可。'),
        'whatThisDoesNotDo': (
            '🚫 本支**不下**「既有回顧是否已回答擁有者的問題」那個判斷——'
            '⚠️ 那要先把切題那幾份的**檢索截止日**與**族群**讀出來。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P2 第一步（續）・切題性篩選 ===')
    print('   候選 %d 份｜判定分佈：' % len(ids))
    for label, count in buckets.most_common():
        print('      %-16s %d' % (label, count))
    print('   ✅ 直接切題 %d 份：%s' % (len(on_topic), on_topic))
    print('   ⚠️ 相鄰 %d 份：%s' % (len(adjacent), adjacent))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
