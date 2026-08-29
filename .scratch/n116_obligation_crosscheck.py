"""Reconcile the report obligations against the M1 documents.

`docs/m1-obligations.md` guarantees nothing is missed; it does NOT say anything
has been done. This script asks the only question a machine can answer here:
**does any M1 document actually mention each obligation's subject?**

🚨 It cannot judge "已辦" — that needs a human read. What it can do is separate
"某節確實談到這件事" from "沒有任何一節談到它", so the second group is short
enough to walk through by hand.

Method: each obligation gets an ANCHOR — a distinctive string or a set of
alternatives drawn from its board text. A hit means some M1 document contains
that anchor. Anchors live here, in version control, so the mapping is auditable
and re-runnable (n+44: 判準即產物).

Run:  python3 .scratch/n116_obligation_crosscheck.py
"""

import re
from pathlib import Path

# ── n+132 之機制（🚫 不是規則）──────────────────────────────────────
# ⚠️ 本檔輸出短，但仍常被順手接 `| head`。管線提前關閉時 Python 會丟
# `BrokenPipeError`，**使一次完整且通過的執行在畫面上長得像失敗**。
# 🚨 該情形已列為缺陷型錄第 15 型（規則寫下了，立規則者下一輪照犯）。
# 故此處**改以機制解決**：把 SIGPIPE 還原為系統預設，接管線即安靜結束。
import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):  # 非 POSIX 或非主執行緒
    pass
# ──────────────────────────────────────────────────────────────────

DOCS = {
    "甲": "docs/m1-a-search-coverage-skeleton.md",
    "乙": "docs/m1-b-screening-limits-skeleton.md",
    "丙": "docs/m1-c-termination-skeleton.md",
    "丁": "docs/m1-d-audit-debt-skeleton.md",
    "己": "docs/m1-e-delivery-checklist.md",
    "庚": "docs/m1-f-harms-skeleton.md",
    "辛": "docs/m1-g-acquisition-skeleton.md",
    "措": "docs/m1-wording-checklist.md",
}
REGISTER = "docs/m1-obligations.md"

# 看板行 -> (一組替代錨點, 說明)
# ⚠️ 錨點取自義務原文之特徵詞，不取行號（行號會位移）。
ANCHORS = {
    # 甲 3
    22769: (["未解釋漏口", "22769"], "影子工作單外之紀錄是否有系統性漏口"),
    23176: (["交集漏口", "交集處出現漏口"], "lane 分派與 flag 篩選之交集漏洞成因"),
    23522: (["queue 全集為母數做覆蓋率驗證"], "建單方式之通則建議"),
    # 乙 9
    7693: (["數值門檻", "同試驗分裂"], "同試驗分裂之兩筆一併處理"),
    41893: (["title-only-judged"], "僅憑標題判讀之限制"),
    47460: (["方法學品質之具體事證"], "方法學品質事證"),
    48928: (["敘述式比對估計", "正式補上方括號掛牌"], "敘述式類別須掛牌或標估計"),
    49702: (["SEX_REPRESENTATION", "性別代表性"], "性別代表性併記行為差異"),
    50612: (["從未單獨作為排除理由被檢驗"], "技能表現未曾單獨檢驗"),
    52108: (["27 筆", "回看"], "27 筆逐筆回看"),
    61541: (["不可回溯"], "33 段不可回溯之筆數與成因"),
    61653: (["33 段"], "同上（第二處）"),
    # 丙 8
    68: (["絆網比檢定更嚴"], "不得寫成檢定被糾正"),
    32249: (["w4b-design-inputs"], "設計輸入隨 M1 呈交"),
    32719: (["w4b-design-inputs"], "同上"),
    32901: (["w4b-design-inputs"], "同上"),
    # 🚫 兩度收緊：先移除「漂移」（五份抬頭皆有），再移除「交付時現算」（七份命中）。
    # ⚠️ 兩次都是稀釋——該義務的實體措辭是「骨架不得寫固定值」，只有丙節寫了。
    48900: (["不得寫固定值"], "不得寫固定值"),
    55163: (["檢定被糾正", "絆網比檢定更嚴"], "同 68"),
    55481: (["絆網比檢定更嚴"], "同 68"),
    56940: (["w4b-design-inputs"], "同 32249"),
    # 丁 10
    840: (["抽查債", "帳本"], "抽查債帳本"),
    1127: (["W2", "抽查債"], "W2 補抽 5 筆轉債"),
    3045: (["ownerAuditQueue"], "分歧進 ownerAuditQueue"),
    3083: (["unresolvedOpposedCandidateIds"], "對立歸零後餘額記帳"),
    3129: (["17 筆"], "17 筆一次清償"),  # 🚫 移除「累計」：甲節碰撞條數亦用該詞，屬假命中
    48466: (["撤稿"], "撤稿筆數改為 5"),
    48478: (["撤稿筆數", "重跑"], "交付前須重跑之項目"),
    48662: (["撤稿"], "同 48466"),
    48864: (["撤稿"], "同 48466"),
    49142: (["撤稿"], "同 48466"),
    # 己 3
    48414: (["逐筆確認其主題涵蓋", "撤稿狀態重查"], "交付前應重查"),
    48897: (["不得沿用任何一輪"], "不得沿用任何一輪之數字"),
    49308: (["敘述式估計不得以單一數字呈現"], "敘述式估計"),
    # 庚 9
    51108: (["方向不一致", "皆為陰性"], "應為方向不一致"),
    51143: (["皆為陰性"], "不得寫皆為陰性"),
    52047: (["皆為陰性"], "同上"),
    52061: (["皆為陰性"], "同上"),
    52084: (["逐筆分流", "不可把兩個數字相加"], "須逐筆分流"),
    52220: (["不得再簡化"], "正式表述定案"),
    52731: (["三度改版", "改過三版"], "表述須再次更新"),
    53102: (["第 N 筆"], "不得以第 N 筆作為族群大小"),
    53795: (["第 N 筆"], "同上"),
    # ── n+117 補入：清冊自 n+88 未重跑，重跑後淨增 13 條（執行室第 448 輪查出）──
    # 🚨 我的 42/42 是對著過期清冊做的；以下錨點使勾稽回到 55 條之上。
    61908: (["皆為陰性"], "不得寫皆為陰性（庚類重述）"),
    # ⚠️ 假陰性修正：檢查表第 3 行「每一節寫完後逐條過一次。這是檢查表，不是章節」
    # 即本義務。🚨 我原以看板措辭當錨點，找的是文件裡不存在的字串。
    61919: (["這是檢查表，不是章節"], "庚類須逐條套用於每一節，不是獨立成節"),
    62000: (["不得寫固定值"], "M1 骨架不得寫固定值（丙 48900 之重述）"),
    62058: (["17 筆"], "抽查債 17 筆一次清償（丁 3129 之重述）"),
    62369: (["不可回溯"], "依 n+86（17）須於方法限制章節載明兩件事"),
    62967: (["那不是失敗，那是發現"], "須於 M1 harms 章節載明其意義"),
    62986: (["候選池大小"], "不得把候選池大小當成文獻分布的描述（檢查表第十二條）"),
    63655: (["文獻存在，是付費牆後"], "取得可行性限制之寫法（🚫 不得寫成「這些主題文獻少」）"),
    64007: (["不可回溯"], "三處皆無方得標不可回溯"),
    64158: (["不可回溯"], "若確為文獻但清單佚失 → 維持不可回溯"),
    64201: (["不可回溯"], "乙案已否定（清單未佚失）"),
    64376: (["27 筆"], "27 筆逐筆回看（乙 52108 之重述）"),
    64412: (["不得併入無效", "不得併入「無效」"], "殘量 4 筆須載明為無從判定"),
}


def load_docs():
    return {k: Path(v).read_text(encoding="utf-8") for k, v in DOCS.items()}


def register_lines():
    """看板行號 -> 義務原文，自清冊表格讀出（不重打）。"""
    text = Path(REGISTER).read_text(encoding="utf-8")
    out = {}
    in_appendix = False
    for line in text.split("\n"):
        if line.startswith("## 附錄"):
            in_appendix = True
        if in_appendix:
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*$", line)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


docs = load_docs()
reg = register_lines()

missing_anchor = sorted(set(reg) - set(ANCHORS))
stale_anchor = sorted(set(ANCHORS) - set(reg))
assert not missing_anchor, f"清冊有義務未配錨點：{missing_anchor}"
assert not stale_anchor, f"錨點指向已不存在之義務：{stale_anchor}"

covered, uncovered = [], []
for line_no in sorted(reg):
    alts, label = ANCHORS[line_no]
    hits = sorted(sec for sec, text in docs.items()
                  if any(a in text for a in alts))
    (covered if hits else uncovered).append((line_no, label, hits))

print(f"清冊義務 {len(reg)} 條｜**有章節談到 {len(covered)}**｜"
      f"🚨 **無任何章節談到 {len(uncovered)}**")
print()
print("| 看板行 | 主旨 | 談到它的文件 |")
print("|---|---|---|")
for line_no, label, hits in covered:
    print(f"| {line_no} | {label} | {'／'.join(hits)} |")
if uncovered:
    print()
    print("🚨 **以下義務目前沒有任何 M1 文件談到**：")
    print()
    print("| 看板行 | 主旨 |")
    print("|---|---|")
    for line_no, label, _ in uncovered:
        print(f"| {line_no} | {label} |")

print()
print("⚠️ 「有章節談到」≠「已辦」。本檢查只保證不會有義務完全沒被寫到；"
      "逐條之辦理狀態仍須人讀。")

# ---------------------------------------------------------------------------
# 🚨 全數命中正是假 PASS 的形狀。以下兩道自我稽核，先證明這個檢查會失敗。
# ---------------------------------------------------------------------------
print()
print("=== 自我稽核甲：反向對照（這些主旨本就不在 M1 文件內，必須 MISS）===")
NEGATIVE = {
    "一個不存在的判準名稱": ["[nonexistent-tag-zzz]"],
    "本 run 未使用之統計法": ["bootstrap 重抽樣"],
    "未曾出現之 lane 名": ["metabolomics-review"],
    "隨機字串": ["QQQZZZ-anchor-control"],
}
neg_fail = 0
for label, alts in NEGATIVE.items():
    hits = sorted(s for s, t in docs.items() if any(a in t for a in alts))
    mark = "MISS ✅" if not hits else f"🚨 命中 {hits}（對照失效）"
    neg_fail += bool(hits)
    print(f"  {label:22s} {mark}")
print(f"  → 反向對照 {len(NEGATIVE) - neg_fail}/{len(NEGATIVE)} 正確 MISS"
      f"{'，檢查確實會失敗 ✅' if not neg_fail else '，🚨 檢查有問題'}")

print()
print("=== 自我稽核乙：錨點是否太鬆（命中數愈多，證據力愈弱）===")
loose = []
for line_no in sorted(reg):
    alts, label = ANCHORS[line_no]
    n = sum(1 for t in docs.values() if any(a in t for a in alts))
    # ⚠️ 判準只留「稀釋」一項。字數長短不是證據力的代理——
    # 「撤稿」只有兩字卻高度specific，「漂移」兩字卻五份文件都有。
    # 🚨 前一版以字數為準，把 14 條標成可疑，其中 12 條實查是好錨點。
    if n >= 5:
        loose.append((line_no, label, n, alts))
print(f"  錨點總數 {len(ANCHORS)}｜🚨 **稀釋（命中 ≥5 份文件）{len(loose)}**")
for line_no, label, n, alts in loose:
    print(f"  🚨 {line_no} {label}：命中 {n} 份，錨點 {alts}")
if loose:
    print("  ⚠️ 上列各條之「有談到」不得採信，須人工逐條確認。")
else:
    print("  ✅ 無稀釋錨點。⚠️ 惟仍請記得：有談到 ≠ 已辦。")
