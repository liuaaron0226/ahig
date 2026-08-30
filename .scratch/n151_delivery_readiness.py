# -*- coding: utf-8 -*-
"""M1 交付盤點——**骨架完稿 ≠ 可交付**。

## 🚨 這支存在的理由

到第 453 輪，兩室都沒有「明列未辦項」了。
**⚠️ 而那句話很容易被讀成「快好了」。** 實情是：

  - 一百多格佔位符**一格都還沒填值**
  - 壬節四項待決**從未呈給擁有者**
  - 萃取階段**尚未開始**，而三項設計檢查都押在那裡

🚨 故本檔把「還缺什麼」列成可勾稽的清單。

## ⚠️ 每一項都必須有「完成的判準」

**🚫 只列項目名是不夠的**——沒有完成判準的項目，
**交付時會被當成「差不多好了」**，而那正是本 run 一路在防的那種讀法。

## 🚨 本檔最重要的一欄，是「有沒有機器檢查」

有些項目可以由程式判定（佔位符填了沒、義務涵蓋了沒）；
**⚠️ 有些不能**（擁有者有沒有真的看過、有沒有真的理解）。

> **🚫 本檔不得假裝後者也被驗證了。**
> **🚨 一份把「無法驗證」寫成「已驗證」的盤點，比沒有盤點更危險。**

## ⚠️ 第三種狀態：半可驗（n+153 新增）

**🚨 「有機器檢查」與「機器檢查涵蓋這一項的全部」是兩件事。**
檢查表逐節套用即屬此類：機器能證明 108 格都寫了字，
**🚫 證明不了那些字是對的。**

> **⚠️ 若把半可驗併入「可驗」，本檔就成了自己在防的那種盤點。**
> 故三態分列：可驗／**半可驗**／不可驗。

Run:  python3 .scratch/n151_delivery_readiness.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

CHECKLIST = "docs/m1-e-delivery-checklist.md"
OWNER = "docs/m1-h-owner-decisions-skeleton.md"


def placeholder_state():
    """自交付清單之產生表讀出格數與其來源型態分布。"""
    text = Path(CHECKLIST).read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\S+) \| `([A-Z0-9_]+)` \| (\S+) \| (\S+) \|",
                      text, re.M)
    kinds = {}
    for _sec, _name, _klass, src in rows:
        kinds[src] = kinds.get(src, 0) + 1
    return len(rows), kinds


def owner_pending():
    """壬節第二節之待決項標題。"""
    text = Path(OWNER).read_text(encoding="utf-8")
    body = text.split("## 二、真正待他決定的事", 1)[-1].split("\n## 三、", 1)[0]
    return re.findall(r"^### （[一二三四五六七]）(.+)$", body, re.M)


def gate(cmd):
    r = subprocess.run([sys.executable, cmd], capture_output=True, text=True)
    return r.returncode


def _drafted():
    """已成稿之節數。🚨 現數，🚫 不寫死——⚠️ 每多寫一節就會變。"""
    return len(list(Path("docs").glob("m1-*-report.md")))


def _n154_cov():
    """（已解, 可及, 已登記為不可解）——🚨 現數，🚫 不得寫死。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "n154", str(Path(".scratch/n154_cell_producer.py")))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rows = m.parse_rows()
    reach = [r for r in rows if r["srctype"] in ("產物", "原始碼", "推導")]
    # 🚨 以**相異佔位符**為單位，🚫 不用列數——同一格可出現在數節，
    # ⚠️ 而「88 列」與「82 個佔位符」相減會得到一個不指任何東西的數（n+155 二）。
    names = {r["name"] for r in reach}
    done = len(names & set(m.RESOLVERS))
    return done, len(names), len(m.UNRESOLVABLE)


# ── 盤點表 ────────────────────────────────────────────────────────
# 欄位：項目／誰做／依據／**完成判準**／機器可驗？
ITEMS = []

n_ph, ph_kinds = placeholder_state()
inaccessible = ph_kinds.get("不可及", 0)
ITEMS.append((
    "佔位符填值", "執行室（不可及者）＋協調者",
    "n+115／清冊 48897",
    f"{n_ph} 格全部填入現算值，其中「不可及」{inaccessible} 格須執行室代跑；"
    "🚨 每格皆為交付當日現算，🚫 不得沿用任何一輪之值",
    # 🚨 覆蓋率**現數，🚫 不寫死**：上一輪把 79／88 打進這句，
    # ⚠️ 一輪後就成了 82／88，而那正是本檔在替別人抓的第 12 型。
    f"⚠️ **半可驗**（`n154_cell_producer.py`）：協調者可及之 {_n154_cov()[1]} 格中"
    f" {_n154_cov()[0]} 格已可由權威來源現算，且逐格與定位欄自報值比對；"
    f"🚫 其餘 {_n154_cov()[2]} 格已登記為「定位欄不足以決定值」，⚠️ 待裁；"
    "🚫 填值完成本身仍須以 n115 殘留 {{…}}＝0 認定"))

pend = owner_pending()
ITEMS.append((
    "壬節待決呈報", "協調者 → 擁有者",
    "n+133／n+142／n+144",
    f"{len(pend)} 項逐項附選項、建議與理由，且擁有者逐項答覆並記錄歸屬；"
    "🚨 未答覆者不得推定為同意任一選項。"
    "⚠️ **三個階段須分開看**：①產出（`docs/m1-owner-briefing.md`，n+155 已產）"
    "／②送出（🚫 尚未）／③逐項答覆（🚫 尚未）",
    "🚫 **不可驗**——⚠️ 產出有了，而**產出不是送出，送出不是看懂**；"
    "🚨 擁有者是否真的理解，程式判不了"))

ITEMS.append((
    "萃取階段四項遞延檢查", "萃取階段",
    "n+144（S3）／n+147（S5-S6、S7）／**n+169（雜湊規則）**",
    "S3 之 TT／TTE 混同檢查以校準集外紀錄補做並標為補充；"
    "S5／S6 依全文之 GI 主要性完成區分；S7 之乾濕基準混用檢查先讀出兩筆之基準再定可否；"
    "**⚠️ 第四項（n+169 新增）**：`parse_tei`／`parse_jats` 之 `sourceSha256` 為裸位元組雜湊，"
    "而 manifest 之 `teiSha256` 為 LF 正規化後之雜湊——"
    "🚨 **同一份 TEI 兩個欄位兩種規則，目前相等只因無一份含 CRLF**；"
    "⚠️ 該階段會重寫 41 份紀錄，**✅ 屆時一併處理成本最低**，"
    "🚫 而處理前須先裁定 `sourceSha256` 之語意（「我實際取得的那份」抑或「這段文字的身分」），"
    "**🚨 不得只換函式而不定語意**；"
    "🚨 四者皆須在報告中載明其為遞延或補做，🚫 不得寫成原設計已執行",
    "🚫 不可驗（該階段尚未開始）"))

ITEMS.append((
    "檢查表十二條逐節套用", "協調者",
    "檢查表附「交付前必做」／n+153",
    "九份文件各自逐條套過一次並留下紀錄（產物：`docs/m1-wording-audit.md`，9×12＝108 格）；"
    "🚨 **套過一次不等於通過**——每一條須寫出該節的具體處置或「本節不適用及其理由」",
    "⚠️ **半可驗**（`n153_wording_audit_check.py`）：機器只證明 108 格齊備、"
    "無空格、無僅打勾、條數與檢查表同步；"
    "🚫 **格子裡寫的是不是真的，機器判不了**——一格寫「不適用」而其實適用，照樣放行"))

ITEMS.append((
    "撤稿狀態交付時重查", "執行室",
    "n+86（十）／n+132",
    "以 `publicationTypes` 欄位重數，且**逐筆確認主題涵蓋**"
    "（🚨 曾有一次由 4 改為 5，而新增那筆是唯一與運動營養直接相關者）",
    "🚫 不可驗（須於交付當日執行）"))

ITEMS.append((
    "報告成稿", "協調者",
    "n+60 之大綱＋本 run 各節骨架",
    f"八節由骨架改寫為連續散文，且**每一句可回溯到骨架中的一格或一則裁定**；"
    f"🚨 骨架是給我看的，🚫 不是給擁有者看的。"
    f"⚠️ **現況：{_drafted()}／8 節已成稿**",
    "🚫 **不可驗**——⚠️ 產生器能證明數字現算、禁句未出現、"
    "同值未在同段重複；🚨 **證明不了論證是對的**，那要人讀"))

GATES = ("round_gate", "n115_delivery_checklist", "n116_obligation_crosscheck",
         "n116_anchor_rules", "n131_cross_consistency", "n141_literal_numbers",
         "n153_wording_audit_check", "n154_cell_producer", "n155_owner_briefing",
         "n157_section_c_report", "n159_section_g_report", "n160_section_f_report",
         "n161_section_d_report", "n163_section_a_report", "n164_section_b_report",
         "n165_section_e_report", "n166_report_cell_coverage")

ITEMS.append((
    "既有機檢全綠", "協調者",
    "n+136／n+141／n+131／n+116／n+153／n+154／n+155／n+157／n+159／n+160／"
    "n+161／n+163／n+164／n+165／n+166／**n+167（判準單一來源）**",
    # 🚨 **現數，🚫 不寫死**——⚠️ 本句原寫「十五項」，而當時實跑已是十七支：
    #    `round_gate` 與 `n116_anchor_rules` 兩支從未被算進來。
    # 🚨 那是本檔替別人抓過的同一型（自述與實況分家），這次在自己身上。
    f"閘門、佔位符表、交叉一致性、義務勾稽、字面數字、檢查表矩陣、格值現算、"
    f"擁有者簡報、甲乙丙丁己庚辛七節成稿、格覆蓋普查**共 {len(GATES)} 支**"
    f"於交付當日皆 exit 0（⚠️ 另加本檔自身，合計 {len(GATES) + 1} 支）",
    "✅ 可驗（本檔即現跑）"))

def counts():
    """（可驗, 半可驗, 不可驗）——🚨 供成稿引用，⚠️ 🚫 不重複一份分類邏輯。"""
    unver = sum(1 for it in ITEMS if it[4].startswith("🚫"))
    half = sum(1 for it in ITEMS if it[4].startswith("⚠️"))
    return len(ITEMS) - unver - half, half, unver


def main():
    print("=== M1 交付盤點｜🚨 骨架完稿 ≠ 可交付 ===")
    print()
    print(f"⚠️ 佔位符共 {n_ph} 格，來源型態分布：{ph_kinds}")
    print(f"⚠️ 擁有者待決 {len(pend)} 項：{'／'.join(p[:12] for p in pend)}")
    print()
    for i, (name, who, basis, done, verifiable) in enumerate(ITEMS, 1):
        print(f"{i}. **{name}**（{who}｜依據 {basis}）")
        print(f"   完成判準：{done}")
        print(f"   {verifiable}")
    print()

    # 🚨 與上方完成判準**同一份清單**（n+170）——⚠️ 先前是兩份，
    #    於是判準說「十五項」而實跑十五支、我手動另跑十七支，三個數各活各的。
    gates = {g: None for g in GATES}
    for g in gates:
        p = Path(f".scratch/{g}.py")
        if not p.exists():
            gates[g] = "缺檔"                       # 🚨 不存在即失敗，🚫 不靜默略過
            continue
        gates[g] = gate(str(p))
    bad = [g for g, rc in gates.items() if rc != 0]
    # 🚨 標籤須可辨識：⚠️ `g.split('_')[0]` 使 `n116_obligation_crosscheck` 與
    #    `n116_anchor_rules` 同顯為「n116」——**其一失敗時看不出是哪一支**。
    # ✅ 故取前兩段。🚫 一份分不清誰壞了的綠燈，等於沒有燈。
    def _lab(g):
        parts = g.split("_")
        return "_".join(parts[:2]) if len(parts) > 1 else g
    print("現跑既有機檢：" + "｜".join(f"{_lab(g)}={rc}" for g, rc in gates.items()))

    unverifiable = sum(1 for it in ITEMS if it[4].startswith("🚫"))
    half = sum(1 for it in ITEMS if it[4].startswith("⚠️"))
    full = len(ITEMS) - unverifiable - half
    print()
    print(f"🚨 **{len(ITEMS)} 項之中，可驗 {full} 項／半可驗 {half} 項／"
          f"沒有機器檢查 {unverifiable} 項**——"
          "⚠️ 後兩類只能靠人做、靠人記錄，🚫 不得因為其餘全綠就當成整體就緒。")
    if half:
        print("⚠️ **半可驗者尤須當心**：它有一支會過的腳本，"
              "🚨 而那正是最容易被讀成「已驗證」的形狀。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
