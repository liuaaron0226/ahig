# -*- coding: utf-8 -*-
"""辛節之對帳：**協調者寫的是本室這一層的事實，而本室從沒回頭核對過。**

## 🚨 為什麼這件事該由本室做

辛節（`docs/m1-g-acquisition-report.md`）整節講取得層——
**⚠️ 而那一層的每一個數字都出自本室的產物。**

> **🚨 寫的人不是量的人。**
> ⚠️ 協調者依交接檔與看板成稿，**🚫 沒有辦法回去對私有根**；
> **✅ 而本室有那些產物，卻從來沒有回頭讀過它寫成什麼樣。**

**⚠️ 這正是第 503 輪那條教訓的另一半**：那次是「值產出來沒人接」，
**🚨 這次要防的是「接過去之後被寫成別的意思」。**

## 本檔驗三件事

| # | 檢查 | 判準 |
|---|---|---|
| 1 | **文件內部算術** | 三條路徑相加＝上界；上界＋缺口＝設計數；遭擋＝有替代＋無替代；版本四項相加＝在手總數 |
| 2 | **與本室產物對帳** | 版本四項之和須等於本室量得之在手總數、遭擋筆數、替代位址分流 |
| 3 | **🚨 自相矛盾之限制句** | ⚠️ 文件若已無「待執行室量測」標記，卻仍在限制節寫「仍待另一台機器量測」，即為**過期的自述** |

**🚨 第 3 條是本檔最要緊的一項**：⚠️ 它不是數字錯，
**是文件對自己狀態的描述停在過去**——
**🚨 而那會讓讀者以為兩個已經量到的數字還沒量到。**

## 🚫 本檔不做什麼

- **🚫 不改協調者的產生器或文件**——⚠️ 那是他的產物；本檔只回報。
- **🚫 不判斷文字寫得好不好**——只驗**算術**、**與產物一致**、**自述是否過期**。

## 🚨 控制探針

**⚠️ 一個「什麼都比對不到」的抽取器，會安靜地回報「零項不符」。**
**✅ 故先對一份注入過的副本跑一次**：把其中一個數字改掉，
**🚨 本檔必須抓到；抓不到即拒絕報告。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 驗得到：可對應到本室產物之數、文件內部算術、過期自述。
- 🚨 驗不到：**只在看板留痕而無產物者**——⚠️ 本檔略過並列名，🚫 不猜。
- 🚨 亦驗不到：**版本四項各自之值**——⚠️ 其來源是三份母體互斥之產物合成，
  **🚫 本檔不重組那個合成**（重組等於再做一次同樣的判斷），
  ✅ 只驗它們加起來等於在手總數。
- ⚠️ 抽取以「粗體數字」為準，**🚨 故換一種排版就抽不到**；已列出抽到幾個。
"""
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
DOC = Path('docs/m1-g-acquisition-report.md')
MISSING_MARK = '待執行室量測'
STALE_CLAIM = '仍待另一台機器量測'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def bold_numbers(text):
    """抽出所有粗體數字（含千分位與小數）。🚨 換排版就抽不到，已於報告註明。"""
    out = []
    for m in re.finditer(r'\*\*([0-9][0-9,]*(?:\.[0-9]+)?)\*\*', text):
        out.append(float(m.group(1).replace(',', '')))
    return out


def check_doc(text):
    """回傳問題清單。🚨 供正向與注入版共用——⚠️ 兩者跑同一套才有對照意義。"""
    bad = []
    nums = bold_numbers(text)
    have = set(nums)

    def need(x, what):
        if x not in have:
            bad.append('%s：文件中找不到粗體 %g' % (what, x))

    # ① 內部算術（🚨 只驗文件自己聲稱的關係）
    m = re.search(r'已在手（可直接萃取）\s*\|\s*\*\*(\d+)\*\*', text)
    p = re.search(r'有 PDF 可抓\s*\|\s*\*\*(\d+)\*\*', text)
    w = re.search(r'只有一個網頁\s*\|\s*\*\*(\d+)\*\*', text)
    if m and p and w:
        tot = int(m.group(1)) + int(p.group(1)) + int(w.group(1))
        cap = re.search(r'免費管道拿得到的上界\s*\*\*(\d+)\*\*', text)
        if cap and tot != int(cap.group(1)):
            bad.append('三條路徑相加 %d ≠ 上界 %s' % (tot, cap.group(1)))
    else:
        bad.append('抽不到三條路徑之表格列——⚠️ 排版可能已變')
    design = re.search(r'設計要收 \*\*(\d+)\*\*', text)
    cap = re.search(r'免費管道拿得到的上界 \*\*(\d+)\*\*', text)
    gap = re.search(r'缺口 \*\*(\d+)\*\* 篇', text)
    if design and cap and gap:
        if int(cap.group(1)) + int(gap.group(1)) != int(design.group(1)):
            bad.append('上界＋缺口 ≠ 設計數')
    else:
        bad.append('抽不到設計／上界／缺口三數')

    # ② 與本室產物對帳
    # 🚨 版本四項之來源是三份產物之合成（n487 之批次 ＋ n488 之補查 ＋ 另一批），
    # ⚠️ 而三者母體互斥、欄位名各異。初版直接去 n487 取 `distribution`——
    #    🚨 那個鍵根本不存在（實為 `versionDistribution`），於是比對整段沒跑，
    #    而控制探針當場攔下「零項不符」。✅ 故改為驗**它加不加得起來**：
    #    四項之和須等於本室量得之 `ACQ_ALL`。
    ver_rows = {}
    for label in ('刊出版', '作者接受版', '投稿版', '版本不明'):
        mm = re.search(r'\|\s*\*{0,2}%s\*{0,2}\s*\|\s*\*\*(\d+)\*\*' % label,
                       text)
        if mm:
            ver_rows[label] = int(mm.group(1))
    if len(ver_rows) != 4:
        bad.append('版本表抽到 %d／4 列——⚠️ 排版可能已變' % len(ver_rows))
    else:
        ho = jload(S + 'executor_cells.json')
        acq_all = (ho['cells'].get('ACQ_ALL') or {}).get('value')
        if acq_all is None:
            bad.append('交接檔無 ACQ_ALL，🚫 無從對帳版本總數')
        elif sum(ver_rows.values()) != acq_all:
            bad.append('版本四項相加 %d ≠ 本室量得之在手總數 %s（ACQ_ALL）'
                       % (sum(ver_rows.values()), acq_all))
    surv = jload(S + 'n450_landing_survey.json')
    blocked = surv['counts'].get('blocked-or-error')
    if blocked is not None:
        need(blocked, '遭擋筆數（n450）')
    alt = jload(S + 'n477_alt_oa_locations.json')
    need(alt['anyAlternativeReachable'], '有替代位址且連得上（n477）')
    need(alt['pdfObtainable'], '其中取得 PDF（n477）')

    # ③ 🚨 過期自述
    if MISSING_MARK not in text and STALE_CLAIM in text:
        bad.append('🚨 過期自述：文件已無「%s」標記，卻仍寫「%s」'
                   % (MISSING_MARK, STALE_CLAIM))
    return bad, nums


if not DOC.exists():
    sys.exit('🚨 找不到 %s——🚫 中止。' % DOC)
text = DOC.read_text(encoding='utf-8')

print('=== 辛節對帳（🚫 唯讀，不改協調者之產物）===')
print()
print('一、控制探針——🚨 抓不到注入即拒絕報告')
injected = text.replace('| 刊出版 | **30** |', '| 刊出版 | **99** |', 1)
if injected == text:
    sys.exit('🚨 注入點不存在（排版已變）——🚫 無從自證，中止。')
inj_bad, _ = check_doc(injected)
caught = any('版本四項相加' in b for b in inj_bad)
print('   %s 把「刊出版 30」改成 99 → %s'
      % ('✅' if caught else '🚨', '抓到了' if caught else '🚨 沒抓到'))
if not caught:
    sys.exit('🚨 控制探針未過——🚫 本次對帳結果不予採信。')
print('   ✅ 它抓得到，故下面的「無不符」才有意義。')
print()

bad, nums = check_doc(text)
print('二、對帳（抽到粗體數字 %d 個）' % len(nums))
if bad:
    for b in bad:
        print('   🚨 %s' % b)
else:
    print('   ✅ 內部算術與本室產物皆一致，且無過期自述。')
print()
print('三、⚠️ 本檔未涵蓋者')
print('   🚫 只在看板留痕而無產物之數（例如缺口逐層之 6／3）——本檔略過，不猜。')
print('   🚫 文字是否寫得準確——⚠️ 那是閱讀，不是對帳。')

doc = {
    'schemaVersion': 1,
    'documentType': 'section-g-crosscheck',
    'ruling': 'self-initiated: section G is entirely about this room\'s layer, '
              'written by someone who cannot reach the private root, and this '
              'room had never read it back. Round 503 was "a value nobody reads"; '
              'this is the other half -- a value that gets read as something else.',
    'population': 'bold numbers and stated arithmetic in '
                  'docs/m1-g-acquisition-report.md',
    'countingUnit': 'claim',
    'criterion': 'internal arithmetic, agreement with this room\'s artefacts, and '
                 'whether the document\'s own statement of what is still '
                 'outstanding is still true',
    'boldNumbersFound': len(nums),
    'findings': bad,
    'controlProbe': {'injection': '刊出版 30 → 99', 'caught': caught,
                     'why': 'An extractor that matches nothing reports zero '
                            'discrepancies, which looks exactly like agreement.'},
    'notCovered': ['figures with board-only provenance and no artefact',
                   'whether the prose is accurate, which is reading'],
    'rootProvenance': ROOT_PROVENANCE,
    'coverageStatement': 'Extraction keys on bold numbers, so a change of layout '
                         'silently reduces coverage; the count of numbers found '
                         'is printed so that shows up. This checks agreement and '
                         'staleness, not whether the wording is right.',
    'contentNote': 'Counts and claim descriptions only.',
}
doc['crosscheckHash'] = content_hash({'findings': bad})
io.open(S + 'n508_section_g_crosscheck.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn508_section_g_crosscheck.json' % S)
sys.exit(1 if bad else 0)
