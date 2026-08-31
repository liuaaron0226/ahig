# -*- coding: utf-8 -*-
"""P1 契約草稿之狀態鎖：**它現在通不過 schema，而那是對的**。

## 🚨 這支存在的理由

`ahig/domains/p1-protein-deficit/scope-contract.draft.json` 目前有**兩處**
通不過 schema，而**兩處都是如實記載，🚫 不是待辦**：

  1. `derivedFromSearchContract.hash` ＝ `null` —— ⚠️ 搜尋契約尚未起草。
  2. `provenance.approvedBy` ＝ `[]` —— 🚨 **填上任何東西都等於捏造擁有者的核准。**

**⚠️ 讓它變綠只要兩行。而那兩行寫下的是兩件沒發生的事。**

> **🚨 故本檔反過來用**：它斷言錯誤**恰為這兩處**。
> ⚠️ 錯誤變多 → 有人動了不該動的欄位；
> **🚨 錯誤變少 → 有人把空的核准欄填掉了，那不是進度。**

## ⚠️ 本檔抓不到什麼

- 🚫 **不驗契約內容對不對**：族群、劑量帶、可比性分類是否合理，⚠️ 要領域專家讀。
- 🚫 **不驗那幾項 schema 容不下的判準有沒有被遵守**——
  🚨 它們根本不在 JSON 裡（見 `scope-extensions-required.md`），
  **⚠️ 目前只存在於散文，沒有任何東西在強制。**

Run:  python3 .scratch/n179_p1_contract_state.py
"""

import json
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

DRAFT = Path("ahig/domains/p1-protein-deficit/scope-contract.draft.json")
SCHEMA = Path("ahig/schema/extraction-scope-contract.schema.json")
EXT = Path("ahig/domains/p1-protein-deficit/scope-extensions-required.md")

# 🚨 預期之錯誤路徑（排序後）。⚠️ 逐字比對，🚫 不用「數量相符」代替。
EXPECTED = [
    ("derivedFromSearchContract", "hash"),
    ("provenance", "approvedBy"),
]

# 🚨 schema 容不下而移出 JSON 之判準——⚠️ 登記檔中必須逐項留有其名。
# 🚨 第 491 輪增列第四、第五項（ADR-0012 決策 1，外部審視指出）：
#    ⚠️ 納入條件已要求「有赤字、有阻力訓練」，但那只擋掉「完全沒有」，
#    🚫 擋不掉「合併不同程度」——而現行 schema 只表達得出納入，不表達分層。
UNEXPRESSIBLE = ["stratifyDoNotPool", "doseUnitPolicy", "requireMatchedDeficit",
                 "stratifyByDeficitMagnitude", "stratifyByTrainingDose"]


def main():
    from jsonschema import Draft202012Validator
    draft = json.loads(DRAFT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errs = list(Draft202012Validator(schema).iter_errors(draft))
    paths = sorted({tuple(e.path) for e in errs})

    problems = []
    print("=== P1 契約草稿狀態 ===")
    print(f"  schema 未通過之路徑 {len(paths)} 處：{[list(p) for p in paths]}")

    if paths != EXPECTED:
        extra = [list(p) for p in paths if p not in EXPECTED]
        gone = [list(p) for p in EXPECTED if p not in paths]
        if extra:
            problems.append(f"🚨 出現預期外之 schema 錯誤：{extra}"
                            "——⚠️ 草稿被改壞了，🚫 不得續行")
        if gone:
            problems.append(
                f"🚨 預期中的未完成項不見了：{gone}"
                "——**⚠️ 那不是進度**：`hash` 要有值必須先凍結搜尋契約；"
                "`approvedBy` 要有值必須擁有者真的核准。"
                "🚫 若兩者皆未發生而此欄已填，那是捏造。")

    if draft.get("status") != "draft":
        problems.append(f"🚨 `status` 已非 draft（現為 {draft.get('status')!r}）"
                        "——⚠️ 凍結屬契約級動作，🚫 非協調者可為（ADR-0010 四）")

    # 🚨 schema 容不下者，登記檔須逐項留名（數量由 UNEXPRESSIBLE 決定）——⚠️ 否則它們會安靜消失。
    ext = EXT.read_text(encoding="utf-8") if EXT.exists() else ""
    missing = [k for k in UNEXPRESSIBLE if k not in ext]
    if missing:
        problems.append(f"🚨 登記檔未提及之不可表達判準：{missing}"
                        "——⚠️ 那些不在 JSON 裡，**登記檔是它們唯一的存放處**")

    if problems:
        for p in problems:
            print(f"  {p}")
    else:
        print("  ✅ 恰為預期之兩處未完成（搜尋契約未起草／擁有者未核准），"
              "且 %d 項不可表達之判準皆已登記" % len(UNEXPRESSIBLE))
    print()
    print("⚠️ **本檔不驗契約內容是否合理**——🚫 那要領域專家讀；"
          "🚨 亦不驗那 %d 項判準有沒有被遵守，**它們目前沒有任何機器在看**。"
          % len(UNEXPRESSIBLE))

    # ── 🚨 反向對照：把空的核准欄填掉，本檔必須叫 ────────────────
    import copy
    inj = copy.deepcopy(draft)
    inj["provenance"]["approvedBy"] = [
        {"agent": "aaron", "agentClass": "human-self", "at": "2026-01-01T00:00:00Z"}]
    assert inj != draft, "🚨 注入未生效——🚫 對照無效"
    inj_paths = sorted({tuple(e.path)
                        for e in Draft202012Validator(schema).iter_errors(inj)})
    caught = inj_paths != EXPECTED
    print()
    print(f"反向對照（把 `approvedBy` 填成已核准）："
          f"{'✅ 會被抓到' if caught else '🚨 抓不到'}")
    if not caught:
        problems.append("🚨 本檢查有盲區——⚠️ 捏造核准不會被發現")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
