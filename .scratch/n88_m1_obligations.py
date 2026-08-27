# -*- coding: utf-8 -*-
"""n+88：自看板萃取全部「M1 報告須…」之義務，落盤為可追溯清冊。

⚠️ 依 n+44「判準即產物，必須落盤版控」：本檔即萃取判準本身，
   清冊一律由本檔重跑產生，**不得手抄**（手抄即第九型缺陷）。
🚨 依 n+48 內容制衛生：輸出前過濾疑似文獻內容之行，寧可漏收也不落地標題。
⚠️ 行號為萃取當下之 COORDINATION.md 行號，會隨看板增長而位移；
   故清冊同時記錄**該行文字**，使其在行號失效後仍可 grep 回溯。
"""
import io
import re
import subprocess

BOARD = 'COORDINATION.md'
OUT = 'docs/m1-obligations.md'

# 🚨 第一版把「可支持 M1 討論**建議值**之歷史演變」抓成義務——
#    「建議」在該處是劑量術語「建議值」的一部分，不是義務動詞。
#    修正後分兩類，且兩類互斥：
#
# （一）報告義務：M1 報告本身必須做的事
OBLIGATION = re.compile(
    r'M1[^。]{0,30}(報告[^。]{0,20})?'
    r'(須|應|必須|不得|清償|呈交|揭露|載明|明列|列出|記錄為)')
# 排除「建議值」「建議量」等術語誤傷（不含義務動詞時不予收錄）
NOT_OBLIGATION = re.compile(r'建議(值|量|攝取|範圍)')

# （二）素材線索：某筆記錄可供 M1 某章節引用——不是義務，但不可遺失
MATERIAL = re.compile(r'(可支持|可供|供|對)\s*M1|M1\s*(之|的)?\s*(討論|敘事|實務落地|契約審)')

# 內容制衛生：疑似逐字標題（同 n+85 公布之樣式）
TITLE = re.compile(r'〈([^〉]{25,300})〉')
TITLE_INNER = re.compile(r'[A-Za-z]{4,}\s+[A-Za-z]{4,}')

# 分類：依關鍵詞歸入 M1 報告之四節
SECTIONS = [
    ('甲 · 檢索與涵蓋完整性',
     ('檢索', '涵蓋', '完整性', '漏', 'lane', '流程圖', '去重', '碰撞')),
    ('乙 · 判讀方法與其限制',
     ('判讀', '判準', '摘要', 'title-only', '標題', '契約', '軸', '重篩', '盲測')),
    ('丙 · 統計終止與抽驗',
     ('終止', '抽驗', 'pScore', '絆網', 'ADR-0008', '母體', '未篩')),
    ('丁 · 稽核債與流程品質',
     ('抽查債', '債', '稽核', '撤稿', '勘誤', '衛生', '更正', 'retract',
      '清償', '記帳', 'ownerAuditQueue')),
    ('己 · 呈現與交付通則（跨章節）',
     ('交付', '筆數規則', '呈現', '重跑', '沿用', '不得以單一數字')),
]


def classify(text):
    for name, keys in SECTIONS:
        if any(k in text for k in keys):
            return name
    return '戊 · 未分類（須人工歸類）'


def main():
    lines = io.open(BOARD, encoding='utf-8').read().split('\n')
    rows, material, skipped = [], [], 0
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if 'M1' not in line:
            continue
        # 內容制衛生過濾（兩類共用）
        if any(TITLE_INNER.search(m) for m in TITLE.findall(line)):
            skipped += 1
            continue
        # 🚨 素材優先：「可支持 M1 討論劑量帶**應**以絕對量」句中之「應」
        #    屬被討論內容，不是報告義務。先判素材，可避免此類誤收。
        if MATERIAL.search(line):
            material.append((n, line))
        elif OBLIGATION.search(line) and not NOT_OBLIGATION.search(line):
            rows.append((n, line))

    buckets = {}
    for n, line in rows:
        buckets.setdefault(classify(line), []).append((n, line))

    head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                          capture_output=True, text=True).stdout.strip()
    out = [
        '# M1 報告義務清冊',
        '',
        '**本檔由 `.scratch/n88_m1_obligations.py` 自 `COORDINATION.md` 重跑產生，'
        '不得手動編輯。**',
        '',
        f'- 萃取自看板 commit `{head}`，共 **{len(lines)}** 行',
        f'- **報告義務 {len(rows)} 條**（M1 報告本身必須做的事）',
        f'- **素材線索 {len(material)} 條**（某筆記錄可供某章節引用，不是義務）',
        f'- 因疑似含逐字文獻標題而略過 **{skipped}** 條'
        '（內容制衛生，n+48／n+85 樣式）',
        '',
        '🚨 **兩類必須分開，且分錯過兩次**：第一版把「可支持 M1 討論**建議值**'
        '之歷史演變」收成義務——「建議」在該處是劑量術語的一部分；第二版又把'
        '「可支持 M1 討論劑量帶**應**以絕對量」收成義務——該「應」屬被討論的內容。'
        f'**混在一起，{len(rows)} 條真義務會被 {len(material)} 條素材淹沒。**',
        '',
        '⚠️ **行號會隨看板增長而位移**；每條同時保留原文，'
        '行號失效時以原文 grep 回溯。',
        '',
        '⚠️ **本清冊只負責「不漏」，不負責「已辦」**——'
        '勾稽狀態須於 M1 撰寫時逐條標註，不得由本檔推定。',
        '',
    ]
    for name, _ in SECTIONS + [('戊 · 未分類（須人工歸類）', ())]:
        items = buckets.get(name)
        if not items:
            continue
        out += [f'## {name}', '', f'共 {len(items)} 條。', '',
                '| 看板行 | 義務原文 |', '|---|---|']
        for n, line in items:
            out.append('| %d | %s |' % (n, line.replace('|', '\\|')))
        out.append('')

    out += ['---', '', '## 附錄 · 素材線索（非義務）', '',
            f'共 {len(material)} 條。**這些不是報告義務**，是判讀過程中標記為'
            '「某章節可引用」的記錄。**列此以免遺失，但不得當成待辦清單。**', '',
            '| 看板行 | 原文 |', '|---|---|']
    for n, line in material:
        out.append('| %d | %s |' % (n, line.replace('|', '\\|')))
    out.append('')

    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    print('✅ 已產生 %s' % OUT)
    print('   報告義務 %d 條、素材線索 %d 條、衛生過濾略過 %d 條'
          % (len(rows), len(material), skipped))
    for name, _ in SECTIONS + [('戊 · 未分類（須人工歸類）', ())]:
        if buckets.get(name):
            print('   %-24s %d 條' % (name, len(buckets[name])))


if __name__ == '__main__':
    main()
