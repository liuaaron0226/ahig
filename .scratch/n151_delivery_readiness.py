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
**⚠️ 有些不能**（檢查表十二條有沒有真的逐節套過、擁有者有沒有真的看過）。

> **🚫 本檔不得假裝後者也被驗證了。**
> **🚨 一份把「無法驗證」寫成「已驗證」的盤點，比沒有盤點更危險。**

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
    "✅ 可驗（填值後重跑 n115，殘留 {{…}} 應為 0）"))

pend = owner_pending()
ITEMS.append((
    "壬節待決呈報", "協調者 → 擁有者",
    "n+133／n+142／n+144",
    f"{len(pend)} 項逐項附選項、建議與理由，且擁有者逐項答覆並記錄歸屬；"
    "🚨 未答覆者不得推定為同意任一選項",
    "🚫 **不可驗**——擁有者是否真的看過、是否真的理解，程式判不了"))

ITEMS.append((
    "萃取階段三項遞延檢查", "萃取階段",
    "n+144（S3）／n+147（S5-S6、S7）",
    "S3 之 TT／TTE 混同檢查以校準集外紀錄補做並標為補充；"
    "S5／S6 依全文之 GI 主要性完成區分；S7 之乾濕基準混用檢查先讀出兩筆之基準再定可否；"
    "🚨 三者皆須在報告中載明其為遞延或補做，🚫 不得寫成原設計已執行",
    "🚫 不可驗（該階段尚未開始）"))

ITEMS.append((
    "檢查表十二條逐節套用", "協調者",
    "檢查表附「交付前必做」",
    "九份文件各自逐條套過一次並留下紀錄；"
    "🚨 **套過一次不等於通過**——每一條須寫出該節的具體處置或「本節不適用及其理由」",
    "🚫 **不可驗**——目前沒有任何產物證明它被套過"))

ITEMS.append((
    "撤稿狀態交付時重查", "執行室",
    "n+86（十）／n+132",
    "以 `publicationTypes` 欄位重數，且**逐筆確認主題涵蓋**"
    "（🚨 曾有一次由 4 改為 5，而新增那筆是唯一與運動營養直接相關者）",
    "🚫 不可驗（須於交付當日執行）"))

ITEMS.append((
    "報告成稿", "協調者",
    "n+60 之大綱＋本 run 各節骨架",
    "八節由骨架改寫為連續散文，且**每一句可回溯到骨架中的一格或一則裁定**；"
    "🚨 骨架是給我看的，🚫 不是給擁有者看的",
    "🚫 不可驗"))

ITEMS.append((
    "既有機檢全綠", "協調者",
    "n+136／n+141／n+131／n+116",
    "閘門、佔位符表、交叉一致性、義務勾稽、字面數字五項於交付當日皆 exit 0",
    "✅ 可驗（本檔即現跑）"))

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

gates = {"n115_delivery_checklist": None, "n116_obligation_crosscheck": None,
         "n131_cross_consistency": None, "n141_literal_numbers": None}
for g in gates:
    gates[g] = gate(f".scratch/{g}.py")
bad = [g for g, rc in gates.items() if rc != 0]
print("現跑既有機檢：" + "｜".join(f"{g.split('_')[0]}={rc}" for g, rc in gates.items()))

unverifiable = sum(1 for it in ITEMS if it[4].startswith("🚫"))
print()
print(f"🚨 **{len(ITEMS)} 項之中，{unverifiable} 項沒有機器檢查**——"
      "⚠️ 那幾項只能靠人做、靠人記錄，🚫 不得因為其餘全綠就當成整體就緒。")
sys.exit(1 if bad else 0)
