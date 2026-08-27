# -*- coding: utf-8 -*-
"""第 410 輪：「僅存敘述、無法回溯」之比對（n+77 建檔時所列第三項工作）。

n+77 第三節之規則第 5 條：
    **找不到對應 `candidateId` 者，如實標記為「僅存敘述、無法回溯」**
    ——那本身就是要交給擁有者的資訊。

⚠️ 該工作明訂須待甲層回填完成後進行，否則會把「尚未回填」誤判為「無法回溯」。
**✅ 前置條件已於第 408／409 輪滿足（甲式 808／0、殘量 0）。**

🚨 本檔要回答的問題只有一個：
   **看板上每一處提到 W4b 設計輸入的地方，能不能回到某一筆記錄？**

判定方式（逐區塊，不逐句）：
  - 區塊內出現任一 8 碼 id，且該 id 存在於判讀庫 → **可回溯**
  - 區塊內出現 id 但判讀庫查無                  → **🚨 id 有誤**（比無 id 更糟）
  - 區塊內完全沒有 id                          → **⚠️ 僅存敘述**

⚠️ 「僅存敘述」不等於「錯」——心跳裡的整理性敘述本來就可能不帶 id。
**🚨 但它等於「無法查證」**，而那正是 n+77 要量出來的東西。

⚠️ 本檔只輸出位置與統計，**不複製區塊內容**（內容制衛生）。
"""
import io
import json
import os
import re

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

E = json.load(io.open(ROOT + '/standard-full-screen-pass-1/judgements.json',
                      encoding='utf-8'))['entries']
known = {x['candidateId'][-8:] for x in E}
known_pref = {x['candidateId'].split(':')[-1][:8] for x in E}

# 🚨 看板用 **id 前綴**稱呼記錄，本檔用**末八碼**——同一筆記錄的兩種寫法。
# ⚠️ 不正規化就直接比對，會把「以前綴寫法引用、且末八碼早已在本檔」的記錄
#    誤判為「尚未進本檔」。**本檔第二版就是這樣多報了一百多筆。**
# 🚨 與 n79_resolve_id.py 同一個陷阱，只是這次是批次比對而非逐筆。
TO_TAIL = {}
for x in E:
    cid = x['candidateId']
    tail = cid[-8:]
    TO_TAIL[tail] = tail
    TO_TAIL[cid.split(':')[-1][:8]] = tail


def normalise(i):
    """把任一種寫法正規化為末八碼；查無則回傳 None。"""
    return TO_TAIL.get(i)

board = io.open(os.path.join(REPO, 'COORDINATION.md'), encoding='utf-8').read()
doc = io.open(os.path.join(REPO, 'docs', 'w4b-design-inputs.md'),
              encoding='utf-8').read()
doc_ids = set(re.findall(r'`([0-9a-f]{8})`', doc))

lines = board.splitlines()
MARK = 'W4b 設計輸入'

# 🚨 區塊之界定（第一版寫錯，記在這裡）：
# ⚠️ 第一版以「空行分隔之段落」為單位，結果 114 段全數判為「無 id」——
#    因為看板的實際格式是**標記行自成一段、內容在下一段**：
#        **W4b 設計輸入**（依…照准）。本輪新增：
#        <空行>
#        - 項目（含 candidateId）
#    **即第一版把內容整個排除在區塊外，於是每一段都「無 id」。**
# 🚨 一個切分方式若讓所有樣本落入同一類，該結果幾乎必然是切分錯了，
#    而不是資料真的長那樣——這是本檔第一版的教訓。
# 現行定義：自標記行起，至下一個 markdown 標題或下一個標記為止。
starts = [k for k, l in enumerate(lines) if MARK in l]
blocks = []
for n, s in enumerate(starts):
    end = len(lines)
    for k in range(s + 1, len(lines)):
        if lines[k].startswith('#') or (MARK in lines[k]):
            end = k
            break
    blocks.append((s + 1, lines[s:end]))   # (1-indexed 起始行, 內容)

retrievable, bad_id, narrative = [], [], []
for ln_no, p in blocks:
    text = '\n'.join(p)
    ids = set(re.findall(r'`?([0-9a-f]{8})`?', text))
    real = {i for i in ids if i in known or i in known_pref}
    if real:
        retrievable.append((ln_no, p, real))
    elif ids:
        bad_id.append((ln_no, p, ids))
    else:
        narrative.append((ln_no, p))

hits = blocks


print('=' * 72)
print('看板中含「%s」之段落' % MARK)
print('=' * 72)
print('  總計                %3d 段' % len(hits))
print('  ✅ 可回溯           %3d 段（段內至少一個 id 存在於判讀庫）' % len(retrievable))
print('  🚨 有 id 但查無      %3d 段' % len(bad_id))
print('  ⚠️ 僅存敘述、無 id   %3d 段' % len(narrative))
print()

if bad_id:
    print('=== 🚨 有 id 但判讀庫查無（比無 id 更嚴重：它看起來可回溯）===')
    for ln_no, p, ids in bad_id:
        print('  看板第 %d 行：%s' % (ln_no, sorted(ids)))
    print()

# 🚨 「無 id」不等於「有東西遺失」——本批不是同質的。
# ⚠️ 逐一讀過後至少四類，其中三類根本不是設計輸入：
NOT_INPUT = [
    ('本輪無 W4b 設計輸入', '心跳明載「本輪無」——**它是一個否定，不是一筆遺失**'),
    ('請執行室彙整', '協調者之裁定文字（指示要建這份檔案），非設計輸入本身'),
    ('照准為 W4b 設計輸入', '同上，裁定文字'),
    ('非同一集合', '關於甲乙兩層本身之元討論（第 40x 輪），非設計輸入'),
    ('甲層', '同上，元討論'),
]
spurious, substantive = [], []
for ln_no, p in narrative:
    text = '\n'.join(p)
    why = next((w for k, w in NOT_INPUT if k in text), None)
    (spurious if why else substantive).append((ln_no, p, why))

print('=== ⚠️ 無 id 之區塊，先分辨它們是不是設計輸入 ===')
print('  🚨 不是設計輸入（誤命中）  %2d 段' % len(spurious))
for ln_no, _, why in spurious:
    print('     L%-6d %s' % (ln_no, why))
print()
print('  ⚠️ 是設計輸入而無 id       %2d 段' % len(substantive))
print('     ' + '  '.join('%d' % ln_no for ln_no, _, _ in substantive))
print()
print('  🚨 但「無 id」仍不等於「內容不在本檔」——**兩者是不同的問題**：')
print('     ⚠️ 抽查即見多例之內容早已透過甲層回填入檔（該區塊只是沒寫 id），')
print('        例如「同一批資料換判準即得不同結論」＝ G-66、')
print('        「落差大小取決於分母選擇」＝ G-62、')
print('        「碳水作為統計模型之陰性對照變項」＝ C-39。')
print('     🚨 故本檔**不宣稱**這 %d 段代表 %d 項遺失的設計輸入。'
      % (len(substantive), len(substantive)))
print('     **要斷定是否遺失，須逐段將其敘述與本檔條目做語意比對——**')
print('     **⚠️ 那是人讀的工作，機械比對只能查 id 之有無，查不了內容之有無。**')
print()

covered = set()
for _, _, real in retrievable:
    covered |= {normalise(i) for i in real}
covered.discard(None)

jia = {x['candidateId'][-8:] for x in E if 'W4b' in x.get('reason', '')}
missing = covered - doc_ids

print('=== 可回溯段落所引之 id（已正規化為末八碼），是否已進本檔 ===')
print('  相異記錄數                    %3d 筆' % len(covered))
print('  其中已在 w4b-design-inputs    %3d 筆' % len(covered & doc_ids))
print('  未在本檔                      %3d 筆' % len(missing))
print()
print('  未在本檔者之性質：')
print('    ✅ 屬甲層（判讀理由提及 W4b）→ 回填漏了   %3d 筆' % len(missing & jia))
print('    ⚠️ 不屬甲層 → 乙層獨有                   %3d 筆' % len(missing - jia))
print()
if missing - jia:
    print('  🚨 「乙層獨有」的意思是：**心跳把它列為 W4b 設計輸入，')
    print('     但該筆判讀原文並未寫 W4b**——故以甲層為母體的回填永遠不會涵蓋它。')
    print('     ⚠️ n+77 已預告兩層「不是同一個集合，也不是包含關係」，')
    print('     **本檔量出了那個差集的大小。**')
    print()
    print('  乙層獨有之 id：')
    ids = sorted(missing - jia)
    for i in range(0, len(ids), 8):
        print('    ' + ' '.join(ids[i:i + 8]))
