"""八份 M1 文件之交叉一致性檢查。

⚠️ 這些文件共用數字、共用措辭、互相引用，**而目前只靠人記**。
本檔查四件目前沒有任何機制在看的事：

  ① 同一佔位符出現在多節時，其類別（凍結／漂移）是否一致
  ② 拘束措辭是否逐字相同（n+80 二要求「一字不改」）
  ③ 各節引用之檢查表條數是否一致
  ④ **節次代號在「文件集」與「義務清冊」兩套體系中所指是否相同**（n+133）

🚨 ④ 之由來（值得原地記住）：n+60 訂的 M1 大綱是甲乙丙丁＝
「做了什麼／要你決定什麼／已知限制／流程品質」，現行文件集的甲乙丙丁卻是
「檢索／判讀／終止／稽核債」。**代號被重新指派而無人對帳，於是「要你決定什麼」
那一節整節消失了四十餘輪，而義務勾稽每輪都回報 55／55 全數涵蓋**
——**🚨 因為它查的是「該說的話」，從來沒有查過「該有的章節」。**

🚨 並附反向對照：故意注入四種不一致，確認本檢查抓得到。
沒有反向對照的檢查，全數通過時無法分辨「真的一致」與「根本沒在看」。

Run:  python3 .scratch/n131_cross_consistency.py
"""

import re
import sys
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

SECTIONS = {
    "甲": "docs/m1-a-search-coverage-skeleton.md",
    "乙": "docs/m1-b-screening-limits-skeleton.md",
    "丙": "docs/m1-c-termination-skeleton.md",
    "丁": "docs/m1-d-audit-debt-skeleton.md",
    "己": "docs/m1-e-delivery-checklist.md",
    "庚": "docs/m1-f-harms-skeleton.md",
    "辛": "docs/m1-g-acquisition-skeleton.md",
    "壬": "docs/m1-h-owner-decisions-skeleton.md",
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


# ── ④ 節次代號之雙軌宣告（n+133）────────────────────────────────────
# ⚠️ 🚫 不做模糊比對——**明列此刻兩套體系各自的抬頭**，任何一邊改動即失敗。
# 🚨 `collision=True` 者為**已知且尚未解決**之同代號異義，須在輸出中大聲印出。
REGISTER_DOC = "docs/m1-obligations.md"
LETTERS = {
    "甲": ("檢索與涵蓋完整性", "檢索與涵蓋完整性", False),
    "乙": ("判讀方法與其限制", "判讀方法與其限制", False),
    "丙": ("統計終止與抽驗", "統計終止與尾端抽驗", False),
    "丁": ("稽核債與流程品質", "稽核債與流程品質", False),
    "己": ("呈現與交付通則（跨章節）", "交付檢查清單（跨章節）", False),
    # 🚨 同一個「庚」在兩套體系指不同的東西，且兩者現皆在用。
    "庚": ("措辭與計數規則", "harms（腸胃道不適）之層別與其意義", True),
    "戊": ("未分類（須人工歸類）", None, False),   # 清冊有、文件集無
    "辛": (None, "全文取得之可行性與其限制", False),
    "壬": (None, "需要擁有者決定的事", False),
}


def letter_headings(texts):
    """回傳 (清冊代號 -> 抬頭, 文件集代號 -> 抬頭)。"""
    reg = dict(re.findall(r"^## ([甲乙丙丁戊己庚辛壬癸]) · (.+)$",
                          read(texts, REGISTER_DOC), re.M))
    doc = {}
    for sec, rel in SECTIONS.items():
        first = read(texts, rel).split("\n", 1)[0]
        m = re.match(r"^# M1 · .*?[節類](?:骨架)?[：]?(.*)$", first)
        doc[sec] = (m.group(1) if m and m.group(1) else first).strip()
    return reg, doc


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

    # ④ 節次代號雙軌宣告
    reg_h, doc_h = letter_headings(texts)
    for letter, (want_reg, want_doc, _known) in LETTERS.items():
        got_reg, got_doc = reg_h.get(letter), doc_h.get(letter)
        if want_reg != got_reg:
            problems.append(f"代號宣告不符：清冊之「{letter}」宣告為"
                            f"「{want_reg}」，實際為「{got_reg}」")
        if want_doc != got_doc:
            problems.append(f"代號宣告不符：文件集之「{letter}」宣告為"
                            f"「{want_doc}」，實際為「{got_doc}」")
    for letter in sorted(set(reg_h) | set(doc_h)):
        if letter not in LETTERS:
            problems.append(f"代號未宣告：「{letter}」出現於實際檔案而不在 LETTERS")

    print(f"=== {label} ===")
    if problems:
        for p in problems:
            print(f"  🚨 {p}")
    else:
        print("  ✅ 四項皆一致")
    print(f"  （拘束措辭出現於 {sum(len(v) for v in variants.values())} 節；"
          f"檢查表實際 {actual} 條）")
    known = [(l, r, d) for l, (r, d, c) in LETTERS.items() if c]
    for l, r, d in known:
        print(f"  🚨 **已知同代號異義（尚未解決）**：「{l}」在清冊＝{r}；"
              f"在文件集＝{d}")
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
# (d) 動一個節次抬頭——模擬「代號被重新指派而無人對帳」（n+133 ④ 之由來）
inj[SECTIONS["辛"]] = inj[SECTIONS["辛"]].replace(
    "# M1 · 辛節骨架：全文取得之可行性與其限制",
    "# M1 · 辛節骨架：全文取得", 1)
inj[REGISTER_DOC] = Path(REGISTER_DOC).read_text(encoding="utf-8")

control = run(inj, "反向對照（已注入四種不一致）")

print()
kinds = {("類別不一致" in p) * 1 or ("拘束措辭" in p) * 2
         or ("條數" in p) * 3 or ("代號" in p) * 4
         for p in control}
ok = {1, 2, 3, 4} <= kinds
print(f"反向對照：抓到 {len(control)} 項，涵蓋四型 → "
      f"{'✅ 本檢查會失敗' if ok else '🚨 本檢查有盲區'}")

sys.exit(1 if real or not ok else 0)
