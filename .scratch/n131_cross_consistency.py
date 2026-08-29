"""七份 M1 文件之交叉一致性檢查。

⚠️ 這些文件共用數字、共用措辭、互相引用，**而目前只靠人記**。
本檔查三件目前沒有任何機制在看的事：

  ① 同一佔位符出現在多節時，其類別（凍結／漂移）是否一致
  ② 拘束措辭是否逐字相同（n+80 二要求「一字不改」）
  ③ 各節引用之檢查表條數是否一致

🚨 並附反向對照：故意注入三種不一致，確認本檢查抓得到。
沒有反向對照的檢查，全數通過時無法分辨「真的一致」與「根本沒在看」。

Run:  python3 .scratch/n131_cross_consistency.py
"""

import re
import sys
from pathlib import Path

SECTIONS = {
    "甲": "docs/m1-a-search-coverage-skeleton.md",
    "乙": "docs/m1-b-screening-limits-skeleton.md",
    "丙": "docs/m1-c-termination-skeleton.md",
    "丁": "docs/m1-d-audit-debt-skeleton.md",
    "己": "docs/m1-e-delivery-checklist.md",
    "庚": "docs/m1-f-harms-skeleton.md",
    "辛": "docs/m1-g-acquisition-skeleton.md",
}
CHECKLIST = "docs/m1-wording-checklist.md"

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
ROW = re.compile(r"^\|\s*(`[^|]+`)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$")
CODE = re.compile(r"`([A-Z0-9_*]+)`")
# 各節抬頭寫「檢查表（十二條）」之類
RULE_COUNT = re.compile(r"m1-wording-checklist\.md`（([一二三四五六七八九十]+)條）")

# n+80（二）之拘束措辭。⚠️ 以「本統計涵蓋宣稱」起、至「永久保留可稽核」止。
BINDING_START = "本統計涵蓋宣稱僅及於標準線之"
BINDING_END = "永久保留可稽核。"

CN = {"十": 10, "十一": 11, "十二": 12, "十三": 13, "十四": 14}


def read(texts, rel):
    return texts[rel] if rel in texts else Path(rel).read_text(encoding="utf-8")


def classes_by_placeholder(texts):
    """佔位符 -> {節: 類別}，只取各節附表所宣告者。"""
    out = {}
    for sec, rel in SECTIONS.items():
        text = read(texts, rel)
        i = text.find("## 附：佔位符來源表")
        if i < 0:
            continue
        used = set(PLACEHOLDER.findall(text[:i]))
        for line in text[i:].split("\n"):
            m = ROW.match(line)
            if not m or "佔位符" in m.group(1):
                continue
            klass = ("凍結" if "凍結" in m.group(2)
                     else "漂移" if "漂移" in m.group(2) else "❓")
            for raw in CODE.findall(m.group(1)):
                names = ([u for u in used if u.startswith(raw[:-1])]
                         if raw.endswith("*") else [raw])
                for name in names:
                    out.setdefault(name, {})[sec] = klass
    return out


def binding_text(texts, rel):
    """抽出拘束措辭；回傳去除 markdown 引用記號與空白後的比對用字串。"""
    text = read(texts, rel)
    i = text.find(BINDING_START)
    if i < 0:
        return None
    j = text.find(BINDING_END, i)
    if j < 0:
        return None
    seg = text[i:j + len(BINDING_END)]
    return re.sub(r"[\s>*]+", "", seg)


def run(texts, label):
    problems = []

    # ① 類別一致性
    for name, per_sec in classes_by_placeholder(texts).items():
        if len(set(per_sec.values())) > 1:
            problems.append(f"類別不一致：`{name}` → " +
                            "、".join(f"{s}={k}" for s, k in sorted(per_sec.items())))

    # ② 拘束措辭逐字相同（n+80 二）
    variants = {}
    for sec, rel in SECTIONS.items():
        got = binding_text(texts, rel)
        if got is not None:
            variants.setdefault(got, []).append(sec)
    if len(variants) > 1:
        problems.append("拘束措辭不一致，出現 %d 種版本：%s"
                        % (len(variants),
                           "；".join("／".join(v) for v in variants.values())))

    # ③ 檢查表條數引用一致
    counts = {}
    for sec, rel in SECTIONS.items():
        for cn in RULE_COUNT.findall(read(texts, rel)):
            counts.setdefault(CN.get(cn, cn), []).append(sec)
    actual = len(re.findall(r"^## [一二三四五六七八九十]+、",
                            read(texts, CHECKLIST), re.M))
    if len(counts) > 1:
        problems.append("檢查表條數引用不一致：" +
                        "；".join(f"{n} 條←{'／'.join(s)}" for n, s in counts.items()))
    elif counts and next(iter(counts)) != actual:
        problems.append(f"檢查表條數引用為 {next(iter(counts))}，"
                        f"而實際條數為 {actual}")

    print(f"=== {label} ===")
    if problems:
        for p in problems:
            print(f"  🚨 {p}")
    else:
        print("  ✅ 三項皆一致")
    print(f"  （拘束措辭出現於 {sum(len(v) for v in variants.values())} 節；"
          f"檢查表實際 {actual} 條）")
    return problems


live = {}
real = run(live, "實際文件")

# ── 反向對照：注入三種不一致，本檢查必須抓到三項 ──────────────────────
inj = {rel: Path(rel).read_text(encoding="utf-8") for rel in SECTIONS.values()}
inj[CHECKLIST] = Path(CHECKLIST).read_text(encoding="utf-8")
# (a) 把辛節某格的類別由漂移改為凍結
inj[SECTIONS["辛"]] = inj[SECTIONS["辛"]].replace(
    "| `ALT_HAS`／`ALT_REACHABLE`／`ALT_PDF`／`ALT_NONE`／`ALT_LANDING_ONLY` | **漂移** |",
    "| `ALT_HAS`／`ALT_REACHABLE`／`ALT_PDF`／`ALT_NONE`／`ALT_LANDING_ONLY` | 凍結 |", 1)
# ⚠️ 注入時踩到一件值得記的事：第一版改的是 `COLLISION_N`，
# 而它只在甲節宣告——**只出現於一節者，本檢查依定義不可能報不一致**。
# 🚨 若當初沒發現，這個反向對照會少驗一型而看起來仍然「有在驗」。
# 故改用同時出現於庚、辛兩節之 `SHORTFALL_HARMS`。
inj[SECTIONS["庚"]] = inj[SECTIONS["庚"]].replace(
    "| `SHORTFALL_HARMS` | **漂移** |", "| `SHORTFALL_HARMS` | 凍結 |", 1)
# (b) 動拘束措辭一個字
inj[SECTIONS["甲"]] = inj[SECTIONS["甲"]].replace(
    "其未篩狀態是設計使然", "其未篩狀態係設計使然", 1)
# (c) 改一節之檢查表條數引用
inj[SECTIONS["乙"]] = inj[SECTIONS["乙"]].replace("（十二條）", "（十一條）", 1)

control = run(inj, "反向對照（已注入三種不一致）")

print()
kinds = {("類別不一致" in p) * 1 or ("拘束措辭" in p) * 2 or ("條數" in p) * 3
         for p in control}
ok = {1, 2, 3} <= kinds
print(f"反向對照：抓到 {len(control)} 項，涵蓋三型 → "
      f"{'✅ 本檢查會失敗' if ok else '🚨 本檢查有盲區'}")

sys.exit(1 if real or not ok else 0)
