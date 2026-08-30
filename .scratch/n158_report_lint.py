# -*- coding: utf-8 -*-
"""成稿之共用自檢（供各節產生器 import）。

## 🚨 為什麼抽成一支，而不是每支各寫一份

n+157 起，每一節成稿都要過同三道檢查。**⚠️ 各寫一份的結果是可預期的**：
改了一支，另外七支還是舊的，**🚨 而輸出全綠，看不出來。**

> **⚠️ 但抽取共用碼這件事，本 run 上一輪剛出過事**（n+157 三：
> 為「不要重打拘束措辭」而寫的抽取函式，把拘束措辭改掉了）。
> **🚨 那次的教訓是「抽取的範圍要精確」，🚫 不是「不要共用」。**
> ✅ 故本檔只共用**判準**，🚫 不共用任何一節的**內容**。

## 三道判準

| # | 問什麼 | 為何 |
|---|---|---|
| ① | 成稿裡有沒有骨架用語 | 🚨 骨架是給我看的；一份寫著「不得寫成…」的報告等於交出工作筆記 |
| ② | 有沒有出現禁句 | ⚠️ 各節之禁句由該節自行提供 |
| ③ | 同一段裡，登記為同值異義的值有沒有出現兩次 | 🚨 危險寫法本身就是「16…其中 16…」 |

## 涵蓋範圍聲明（n+80 三）

- 🚨 ③ **只看得到 `**粗體**` 起來的數字。**⚠️ 沒加粗的並排，本檔看不到。
- 🚨 本檔🚫 不判**論證是否正確**——那要人讀。
- ⚠️ ① 之詞表是列舉的，**🚫 不是「所有骨架用語」**；新詞出現時須自行補入。
"""

import re

# 🚨 骨架用語：出現在成稿即為漏帶。⚠️ 列舉法，🚫 非窮舉——見涵蓋範圍聲明。
SKELETON_WORDS = ["骨架", "佔位符", "待辦", "本檔是", "交付時由", "檢查表第"]


def leaks(text):
    return [w for w in SKELETON_WORDS if w in text]


# 🚨 禁止語：一行帶了這些字，該行對禁句就是**提及**而不是**使用**。
PROHIBITION = ["🚫", "不得", "不寫", "禁句", "不可以"]


def forbidden(text, phrases):
    """phrases：該節自訂之禁句片段。

    ## 🚨 這裡要分「使用」與「提及」

    ⚠️ 成稿本來就會寫「**🚫 不得寫成「這些主題文獻少」**」——
    **那是在禁止它，不是在犯它。**
    🚨 初版不分，於是本節照抄看板原句的那一段當場被判違規。

    **✅ 判準**：該句須同時
    ① 被引號括住（`「…」`），且 ② 該行帶禁止語，才算提及。

    > **🚨 而這個判準有一個明白的洞，須寫出來**：
    > **⚠️ 一句真的違規，只要同一行剛好有個 🚫，就會被放過。**
    > **🚫 故本檢查不是「禁句絕不出現」的保證**，
    > 只是「禁句未在沒有任何否定語境下出現」。
    """
    hits = []
    for p in phrases:
        if not p:
            continue
        for line in text.split("\n"):
            if p not in line:
                continue
            mentioned = (f"「{p}" in line
                         and any(m in line for m in PROHIBITION))
            if not mentioned:
                hits.append(p)
                break
    return hits


def repeated_in_paragraph(text, coincidence, value_of):
    """🚨 同一段內，登記為同值異義之值出現兩次以上。

    ⚠️ 判準之所以是「同一段內出現兩次」而非「兩格同時出現」，
    見 n+157 六：**檢查看得到數字，看不到那個數字是哪一格產生的**，
    🚫 故「兩格同時出現」必然誤報。
    """
    out = []
    paras = [p for p in text.split("\n\n") if p.strip()]
    for key in coincidence:
        try:
            val = f"{value_of(key[0])}"
        except Exception:                              # noqa: BLE001
            continue
        for para in paras:
            if len(re.findall(rf"\*\*{re.escape(val)}\*\*", para)) > 1:
                out.append((key, val))
                break
    return out


def run(text, coincidence, value_of, forbidden_phrases=()):
    """回傳 (problems, 反向對照是否三型皆會失敗)。"""
    problems = []
    for w in leaks(text):
        problems.append(f"🚨 成稿含骨架用語「{w}」——⚠️ 那是給我看的，不是給讀者看的")
    for p in forbidden(text, forbidden_phrases):
        problems.append(f"🚨 成稿出現禁句片段「{p}」")
    for key, val in repeated_in_paragraph(text, coincidence, value_of):
        problems.append(
            f"🚨 同一段內 **{val}** 出現兩次以上，而該值登記為同值異義"
            f"（{'／'.join(key)}）——⚠️ 讀者會讀成同一個量")

    # ── 🚨 反向對照：三型各注入一次（n+134：沒試過會不會失敗的護欄不算護欄）
    c1 = bool(leaks(text + "\n本檔是骨架，佔位符交付時由腳本填入。\n"))
    probe = forbidden_phrases[0] if forbidden_phrases else "△不可能出現之字串△"
    c2 = bool(forbidden(text + f"\n{probe}\n", [probe]))
    c3 = False
    for key in coincidence:
        try:
            val = f"{value_of(key[0])}"
        except Exception:                              # noqa: BLE001
            continue
        inj = text + f"\n\n甲 **{val}** 筆，其中乙 **{val}** 筆。\n"
        if repeated_in_paragraph(inj, {key: ""}, value_of):
            c3 = True
            break
    return problems, (c1, c2, c3)


def report(problems, controls, label="成稿自檢"):
    print(f"=== {label} ===")
    for p in problems:
        print(f"  {p}")
    if not problems:
        print("  ✅ 通過：無骨架用語、無禁句、無同段同值重複"
              "（🚫 不代表論證正確——見涵蓋範圍聲明）")
    c1, c2, c3 = controls
    print(f"  反向對照①骨架用語 {'✅' if c1 else '🚨'}｜"
          f"②禁句 {'✅' if c2 else '🚨'}｜③同段同值 {'✅' if c3 else '🚨'}")
    return bool(problems) or not all(controls)
