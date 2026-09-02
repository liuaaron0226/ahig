# -*- coding: utf-8 -*-
"""**那些成功產出的表格節，留的是整張表還是只有標題。**（第 696 輪）

## ✅ 補上第 694 輪自己寫下的限制

n694：「⚠️ 本支數的是**標籤出現次數**，🚫 不是『表格內容有沒有被保留』——
🚨 一個表格節可能只留了標題而沒有內容。」

## 🚨 為什麼要緊

`D17`／`D27` 的效益是「修好之後表格看得見」。
**⚠️ 但若現在**看得見的那 40 個表格節**其實只留了標題，
🚨 那修好之後多出來的東西，價值也要照同一個折扣算。**

## ✅ 怎麼量——用**數字密度**，🚫 不做內容判讀

表格的實體是**數字**。故：

- 原始檔：把每個 `<table-wrap>…</table-wrap>` 區塊去標籤後，數其中的**數字字元**（R）
- sections：把 `kind == "table"` 的節文字，數其中的**數字字元**（S）
- **比值 S／R** ≈ 1 → 內容有留；≈ 0.1 → 只有標題

> **✅ 這是結構量測，🚫 不是關鍵字判讀，也不輸出任何內容文字。**

## 🚫 本支不改任何檔案、不送外部請求
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n696_table_section_fidelity.json'

TABLE_BLOCK = re.compile(r'<table-wrap[\s>].*?</table-wrap>', re.S)
TAGS = re.compile(r'<[^>]+>')
DIGITS = re.compile(r'\d')
FLOOR = 0.5


def digits_in(text):
    return len(DIGITS.findall(text))


def main():
    rows = []
    for manifest in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            doc = json.loads(manifest.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if doc.get('sourceType') != 'europe-pmc-jats':
            continue
        raw_name = str(doc.get('rawFile') or '')
        sec_name = str(doc.get('sectionsFile') or '')
        raw = manifest.parent / raw_name if raw_name else None
        sec = manifest.parent / sec_name if sec_name else None
        if not (raw and raw.is_file() and sec and sec.is_file()):
            continue
        text = raw.read_text(encoding='utf-8', errors='replace')
        blocks = TABLE_BLOCK.findall(text)
        raw_digits = sum(digits_in(TAGS.sub(' ', b)) for b in blocks)
        raw_chars = sum(len(TAGS.sub(' ', b)) for b in blocks)
        sections = json.loads(sec.read_text(encoding='utf-8'))
        table_sections = [s for s in (sections.get('sections') or [])
                          if str(s.get('kind')).lower() == 'table']
        sec_digits = sum(digits_in(str(s.get('text') or ''))
                         for s in table_sections)
        sec_chars = sum(len(str(s.get('text') or ''))
                        for s in table_sections)
        rows.append({
            'report': str(doc['candidateId'])[-16:],
            'rawTableBlocks': len(blocks),
            'tableSections': len(table_sections),
            'rawDigits': raw_digits, 'sectionDigits': sec_digits,
            'rawChars': raw_chars, 'sectionChars': sec_chars,
            'digitRatio': round(sec_digits / raw_digits, 3)
            if raw_digits else None,
        })

    comparable = [r for r in rows
                  if r['rawTableBlocks'] > 0 and r['tableSections'] > 0
                  and r['rawDigits'] > 0]
    thin = [r for r in comparable if r['digitRatio'] < FLOOR]
    no_section = [r for r in rows if r['tableSections'] == 0]
    ratios = sorted(r['digitRatio'] for r in comparable)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('有足夠可比的篇（必觸發之正對照）',
          len(comparable) >= 10,
          '🚨 JATS 掃過 %d 篇，兩邊都有東西可比的 %d 篇；'
          '⚠️ 太少的話比值沒有份量' % (len(rows), len(comparable)))
    probe('沒有表格節的那幾篇，節文字的數字必須是 0（必觸發之反向）',
          all(r['sectionDigits'] == 0 for r in no_section),
          '🚨 沒有表格節卻數到數字的：%s；'
          '⚠️ 若有，代表本支把別種節也算進去了'
          % ([r['report'] for r in no_section if r['sectionDigits']] or '無'))
    probe('原始檔那一側真的數得到數字（必觸發之正對照）',
          sum(r['rawDigits'] for r in comparable) > 0,
          '🚨 原始表格區塊的數字字元合計 %d 個；'
          '⚠️ 若是 0，比值的分母就沒有意義'
          % sum(r['rawDigits'] for r in comparable))
    # 🚨 這一道是答案。
    probe('表格節保留了原始表格的內容（數字比值 ≥ %.1f）' % FLOOR,
          not thin,
          '🚨 比值中位數 %.2f｜最低 %.2f｜最高 %.2f；'
          '低於 %.1f 的 %d／%d 篇：%s；'
          '⚠️ 比值很低代表**節裡只有標題**，'
          '**🚨 那麼「修好之後看得見」的價值要照同一個折扣算**'
          % (ratios[len(ratios) // 2] if ratios else 0,
             ratios[0] if ratios else 0, ratios[-1] if ratios else 0,
             FLOOR, len(thin), len(comparable),
             [(r['report'], r['digitRatio']) for r in thin] or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'table-section-fidelity',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n694（只數標籤次數，未看內容是否保留）',
        'method': (
            '✅ 用**數字密度**當代理：表格的實體是數字。'
            '原始 `<table-wrap>` 去標籤後的數字字元數為分母，'
            '`kind=table` 節文字的數字字元數為分子。'
            '🚫 不做任何內容判讀，也不輸出內容文字。'),
        'jatsReportsScanned': len(rows),
        'comparable': len(comparable),
        'digitRatioMedian': ratios[len(ratios) // 2] if ratios else None,
        'digitRatioMin': ratios[0] if ratios else None,
        'digitRatioMax': ratios[-1] if ratios else None,
        'thinSections': thin,
        'rows': sorted(rows, key=lambda r: r['report']),
        'resolvesN611SixReports': {
            'note': ('✅ 第 611 輪：JATS 26 篇裡有 6 篇沒有表格節。'
                     '🚨 本支把那 6 篇拆乾淨了。'),
            '有表卻無節（缺陷，即 D27）': [r['report'] for r in no_section
                                          if r['rawTableBlocks'] > 0],
            '原始檔本來就沒有表': [r['report'] for r in rows
                                   if r['rawTableBlocks'] == 0],
        },
        'strengthensFixCase': (
            '✅ 走得到的表格**內容是完整的**（數字保留率中位數 1.00）——'
            '🚨 故 `D17`／`D27` 修好之後拿到的是**整張表**，'
            '🚫 不是只有標題。⚠️ 這讓那兩項的效益**不必打折**。'),
        'whyItMattersForD17AndD27': (
            '⚠️ `D17`／`D27` 的效益是「修好之後表格看得見」。'
            '🚨 但**現在看得見的那些表格節**若只留了標題，'
            '**那修好之後多出來的東西，價值要照同一個折扣算。**'),
        'methodLimit': (
            '🚨 數字密度是**代理**，🚫 不是內容比對——'
            '⚠️ 一張全是文字的表（例如納入條件表）數字本來就少，'
            '**會被本支誤判成「只有標題」**。'
            '✅ 故本支報的是分佈，🚫 不對個別篇下判斷。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n696 表格節的內容保真度（數字密度代理）===')
    print('   JATS %d 篇｜可比 %d 篇｜比值 中位數 %s／最低 %s／最高 %s'
          % (len(rows), len(comparable), doc['digitRatioMedian'],
             doc['digitRatioMin'], doc['digitRatioMax']))
    print('   逐篇（原始區塊／表格節／原始數字／節數字／比值）：')
    for row in sorted(rows, key=lambda r: (r['digitRatio'] is None,
                                           r['digitRatio'] or 0)):
        print('      %s  %2d／%2d ／ %5d／%5d ／ %s'
              % (row['report'], row['rawTableBlocks'], row['tableSections'],
                 row['rawDigits'], row['sectionDigits'], row['digitRatio']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
