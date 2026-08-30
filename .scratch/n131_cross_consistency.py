"""八份 M1 文件之交叉一致性檢查。

⚠️ 這些文件共用數字、共用措辭、互相引用，**而目前只靠人記**。
本檔查四件目前沒有任何機制在看的事：

  ① 同一佔位符出現在多節時，其類別（凍結／漂移）是否一致
  ② 拘束措辭是否逐字相同（n+80 二要求「一字不改」）
  ③ 各節引用之檢查表條數是否一致
  ④ **節次代號在「文件集」與「義務清冊」兩套體系中所指是否相同**（n+133）
  ⑤ **同一個量的兩份實作是否算出同一個數**（n+167）

🚨 ⑤ 之由來：`n116` 印「重述 17／相異義務 65」，`n154` 現算得 10／72。
**⚠️ 兩者量的是同一件事，各自都通過自己的檢查，而沒有任何一道把它們並排。**
兩份規則還都是錯的，且錯在相反方向（一份多算一條實質義務，一份漏掉六條指向）；
**🚨 更糟的是，n154 那個錯的 10 已被寫進同值異義登記簿，
成為「四個不相干的 10」之一——一個錯的數字被登記成「已查核」。**
✅ 判準已抽為單一來源（`n116_anchor_rules.py`），本項則確保它不再分家。

🚨 ④ 之由來（值得原地記住）：n+60 訂的 M1 大綱是甲乙丙丁＝
「做了什麼／要你決定什麼／已知限制／流程品質」，現行文件集的甲乙丙丁卻是
「檢索／判讀／終止／稽核債」。**代號被重新指派而無人對帳，於是「要你決定什麼」
那一節整節消失了四十餘輪，而義務勾稽每輪都回報 55／55 全數涵蓋**
——**🚨 因為它查的是「該說的話」，從來沒有查過「該有的章節」。**

🚨 並附反向對照：故意注入五種不一致，確認本檢查抓得到。
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


# ── ④ 節次代號之雙軌宣告（n+133；n+134 改為「衝突由比對推得」）──────
# ⚠️ 🚫 不做模糊比對——**明列此刻兩套體系各自的抬頭**，任何一邊改動即失敗。
# 🚨 n+133 版把「已知衝突」寫成一個 collision 旗標，**那是可以直接改掉讓它閉嘴的**。
# ✅ 改為：衝突**由兩表比對推得**（同代號而異名即為衝突，直接計為 problem）。
#    要消除它只能真的改名，🚫 改宣告沒有用。
REGISTER_DOC = "docs/m1-obligations.md"
# 天干代號＝M1 報告之章節。🚨 非章節者一律不得佔天干（n+134）。
REG_CATEGORIES = {
    "甲": "檢索與涵蓋完整性",
    "乙": "判讀方法與其限制",
    "丙": "統計終止與抽驗",
    "丁": "稽核債與流程品質",
    "己": "呈現與交付通則（跨章節）",
    "檢": "措辭與計數規則",          # ⚠️ 檢查表，🚫 不是章節（n+81 61919）
    "待": "未分類（須人工歸類）",     # ⚠️ 暫存區，🚫 不是章節
}
DOC_SECTIONS = {
    "甲": "檢索與涵蓋完整性",
    "乙": "判讀方法與其限制",
    "丙": "統計終止與尾端抽驗",
    "丁": "稽核債與流程品質",
    "己": "交付檢查清單（跨章節）",
    "庚": "harms（腸胃道不適）之層別與其意義",
    "辛": "全文取得之可行性與其限制",
    "壬": "需要擁有者決定的事",
}
# ⚠️ 兩表同代號而異名者即為衝突。丙／己雖措辭略異但指同一件事，故明列為容許。
ALLOWED_DIFF = {"丙", "己"}


def letter_headings(texts):
    """回傳 (清冊代號 -> 抬頭, 文件集代號 -> 抬頭)。"""
    reg = dict(re.findall(r"^## (\S+) · (.+)$",
                          read(texts, REGISTER_DOC), re.M))
    reg.pop("附錄", None)
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

    # ④ 節次代號：先驗宣告與實際相符，再由兩表比對推出衝突
    reg_h, doc_h = letter_headings(texts)
    for name, want, got in (("清冊", REG_CATEGORIES, reg_h),
                            ("文件集", DOC_SECTIONS, doc_h)):
        for k in sorted(set(want) | set(got)):
            if want.get(k) != got.get(k):
                problems.append(f"代號宣告不符：{name}之「{k}」宣告為"
                                f"「{want.get(k)}」，實際為「{got.get(k)}」")
    for k in sorted(set(reg_h) & set(doc_h)):
        if k in ALLOWED_DIFF:
            continue
        if reg_h[k] != doc_h[k]:
            problems.append(f"同代號異義：「{k}」在清冊＝{reg_h[k]}；"
                            f"在文件集＝{doc_h[k]}")

    print(f"=== {label} ===")
    if problems:
        for p in problems:
            print(f"  🚨 {p}")
    else:
        print("  ✅ 四項皆一致")
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
# (d) 動一個節次抬頭——模擬「代號被重新指派而無人對帳」（n+133 ④ 之由來）
inj[SECTIONS["辛"]] = inj[SECTIONS["辛"]].replace(
    "# M1 · 辛節骨架：全文取得之可行性與其限制",
    "# M1 · 辛節骨架：全文取得", 1)
# (e) 把清冊的「檢」改回天干「庚」——**專門驗證「同代號異義」偵測器本身**。
# 🚨 沒有這一項，本輪把衝突改掉之後，就分不清是「真的解決了」還是
#    「偵測器跟著被我改壞了」——兩者在輸出上都是一行「✅ 四項皆一致」。
inj[REGISTER_DOC] = Path(REGISTER_DOC).read_text(encoding="utf-8").replace(
    "## 檢 · 措辭與計數規則", "## 庚 · 措辭與計數規則", 1)

control = run(inj, "反向對照（已注入五種不一致）")


# ── ⑤ 同一個量的兩份實作必須算出同一個數（n+167）─────────────────────
# 🚨 本項**不吃 texts**：它比的不是文件裡的字，而是**兩支程式各自跑出來的數**。
# ⚠️ 故它不能併進 run()，也不能靠注入文件來反向對照——
#    它的反向對照是「把其中一邊的答案換掉，看本項會不會叫」。
_TALLY_LINE = re.compile(r"錨點總數 (\d+)｜.*?者 (\d+)｜\*\*相異義務約 (\d+)\*\*")


def obligation_agreement(n154_override=None):
    """回傳不一致之敘述串列（空＝兩邊相符）。

    ⚠️ n116 側**取其實際印出的那一行**，🚫 不重算——
    🚨 讀者看到的是那一行；若程式內部算對而印錯，本項仍該叫。
    """
    import subprocess
    out = subprocess.run([sys.executable, ".scratch/n116_obligation_crosscheck.py"],
                         capture_output=True, text=True).stdout
    m = _TALLY_LINE.search(out)
    if not m:
        return ["🚨 n116 之條目／重述／相異義務彙總行解析不到"
                "——⚠️ 格式已改，🚫 不得視為相符"]
    rows116, rest116, dist116 = (int(x) for x in m.groups())

    if n154_override is not None:
        rows154, rest154, dist154 = n154_override
    else:
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("n154", ".scratch/n154_cell_producer.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rows154 = mod.value("OBLIGATION_ROWS")
        rest154 = mod.value("OBLIGATION_RESTATED")
        dist154 = mod.value("OBLIGATION_DISTINCT")

    bad = []
    for what, a, b in (("條目數", rows116, rows154),
                       ("重述數", rest116, rest154),
                       ("相異義務數", dist116, dist154)):
        if a != b:
            bad.append(f"義務清冊之{what}兩邊不符：n116＝{a}；n154＝{b}"
                       "——⚠️ 同一個量有兩份實作，🚫 不得各報各的")
    # 🚨 併附內部閉合：相異＝條目−重述。⚠️ 兩邊相等但都算錯，仍須抓。
    if dist116 != rows116 - rest116:
        bad.append(f"n116 自身不閉合：{rows116}−{rest116}≠{dist116}")
    return bad


print()
_ob = obligation_agreement()
print("=== ⑤ 義務清冊計數：兩份實作是否相符 ===")
if _ob:
    for p in _ob:
        print(f"  🚨 {p}")
else:
    print("  ✅ n116 與 n154 之條目／重述／相異義務三數皆相符，且相異＝條目−重述")

# 反向對照：把 n154 側換成本次修正前的那組錯值（82／10／72）。
_ob_ctl = obligation_agreement(n154_override=(82, 10, 72))
_ob_ok = len(_ob_ctl) >= 2
print(f"  反向對照（注入修正前之 82／10／72）：抓到 {len(_ob_ctl)} 項 → "
      f"{'✅ 本項會失敗' if _ob_ok else '🚨 本項有盲區'}")

print()
kinds = {("類別不一致" in p) * 1 or ("拘束措辭" in p) * 2
         or ("條數" in p) * 3 or ("同代號異義" in p) * 5
         or ("代號宣告不符" in p) * 4
         for p in control}
ok = {1, 2, 3, 4, 5} <= kinds
print(f"反向對照：抓到 {len(control)} 項，涵蓋五型 → "
      f"{'✅ 本檢查會失敗' if ok else '🚨 本檢查有盲區'}")

sys.exit(1 if real or not ok or _ob or not _ob_ok else 0)
