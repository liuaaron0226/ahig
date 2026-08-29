# -*- coding: utf-8 -*-
"""11 個已下載 PDF 之文字層檢查——在安裝任何工具之前先做。

## 🚨 為什麼現在做

擁有者已同意安裝解析器，惟工具選型（GROBID 需 JDK 11+／Docling 需另寫解析器）
尚待其裁示。**⚠️ 而有一件事不論選哪個都必須先知道**：

**🚨 這些 PDF 有沒有文字層？**
**⚠️ 若其中有掃描件（只有影像、無可取文字），GROBID 與 Docling 都救不了它**
——那需要 OCR，是第三種工具、第三次安裝。
**🚨 在裝 1GB 軟體之前先量這件事，是本 run 一路在做的「先量再建」。**

## 做法：只用標準庫，不裝任何東西

PDF 結構可直接以位元組檢視；壓縮串流以 `zlib`（標準庫）解開後再看：

| 訊號 | 意義 |
|---|---|
| `/Font` 出現次數 | 有字型資源 → 頁面預期含可取文字 |
| `Tj`／`TJ` 運算子 | 內容串流實際在畫文字 |
| `/Image` 出現次數 | 影像資源；**⚠️ 單獨出現不代表掃描件**（插圖亦然） |
| 頁數 | 由 `/Type/Page` 計數估算 |

**分類**：有字型且有文字運算子 → `text-layer`；
只有影像而無字型 → `scanned-likely`；其餘 → `uncertain`。

## 🚨 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：檔內是否存在字型資源與文字繪製運算子。
- 🚨 查不到：**文字品質、是否為完整全文、是否切得出節與偏移**
  ——⚠️ 那要真的解析。**🚫 `text-layer` 只代表「GROBID 有東西可讀」。**
- ⚠️ 加密或使用物件串流（ObjStm）之 PDF，本檔可能低估——
  **🚨 故 `uncertain` 不等於「沒有文字」，只代表本法看不出來。**
- 🚫 **本檔不輸出任何文字內容**，只輸出計數與布林值。
"""
import io
import json
import os
import re
import sys
import zlib
from collections import Counter

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash, file_hash  # noqa: E402

DEST = os.path.join(os.environ.get('AHIG_PRIVATE_ROOT',
                                   r'C:/Users/User/Desktop/claude/ahig-private'),
                    'fulltext', 'pdf-cache')
S = '.scratch/'

STREAM = re.compile(rb'stream\r?\n(.*?)endstream', re.S)
TEXTOP = re.compile(rb'(?:^|[\s>\]])(Tj|TJ)[\s(]')


def inspect(raw):
    """🚨 只回結構訊號，🚫 不回任何文字。"""
    fonts = raw.count(b'/Font')
    images = raw.count(b'/Image')
    pages = len(re.findall(rb'/Type\s*/Page[^s]', raw))
    textops = len(TEXTOP.findall(raw))
    inflated = 0
    if textops == 0:                      # ⚠️ 內容多半壓縮著，解開再看
        for m in STREAM.finditer(raw):
            try:
                d = zlib.decompress(m.group(1).strip(b'\r\n'))
            except zlib.error:
                continue
            inflated += 1
            textops += len(TEXTOP.findall(d))
            if textops > 50:
                break
    return {'fonts': fonts, 'images': images, 'pages': pages,
            'textOps': textops, 'streamsInflated': inflated}


files = sorted(f for f in os.listdir(DEST) if f.endswith('.pdf'))
print('=== PDF 文字層檢查（%d 檔；🚫 不輸出任何文字內容）===' % len(files))
print('%-20s %7s %6s %7s %8s %s'
      % ('檔案（id 片段）', '大小KB', '頁數', '/Font', 'Tj/TJ', '判定'))
print('-' * 78)
rows = []
for fn in files:
    raw = open(os.path.join(DEST, fn), 'rb').read()
    s = inspect(raw)
    if s['fonts'] and s['textOps']:
        v = 'text-layer'
    elif s['images'] and not s['fonts']:
        v = '🚨 scanned-likely'
    else:
        v = '⚠️ uncertain'
    rows.append({'file': fn[:-4], 'bytes': len(raw), 'fileHash': file_hash(raw),
                 **s, 'verdict': v.replace('🚨 ', '').replace('⚠️ ', '')})
    print('%-20s %7d %6d %7d %8d %s'
          % (fn[:-4][:20], len(raw) // 1024, s['pages'], s['fonts'],
             s['textOps'], v))

c = Counter(r['verdict'] for r in rows)
print('-' * 78)
for k, v in c.most_common():
    print('   %-18s %2d' % (k, v))
print()
if c['scanned-likely']:
    print('🚨 有 %d 檔疑為掃描件——⚠️ GROBID／Docling 皆無法處理，需 OCR（第三種工具）。'
          % c['scanned-likely'])
else:
    print('✅ 無疑似掃描件——⚠️ 即選定之解析器有東西可讀。')
print('🚨 惟這只代表「有文字可讀」，🚫 不代表「切得出節與偏移」。')

doc = {
    'schemaVersion': 1,
    'documentType': 'pdf-text-layer-check',
    'ruling': 'pre-installation diligence; owner consented to a parser but the '
              'tool choice is still open',
    'population': 'the PDFs downloaded in round 455 to the private pdf-cache',
    'countingUnit': 'file',
    'criterion': 'fonts and text-showing operators present -> text-layer; '
                 'images without fonts -> scanned-likely; otherwise uncertain. '
                 'Compressed streams are inflated with zlib before looking.',
    'counts': dict(c),
    'files': rows,
    'coverageStatement': ('Says a parser will find something to read. It does '
                          'not say the text is complete, of usable quality, or '
                          'sectionable under the offset contract. PDFs using '
                          'object streams or encryption may be undercounted, so '
                          'uncertain means this method could not tell, not that '
                          'there is no text.'),
    'contentNote': 'Counts, sizes and hashes only. No text is extracted, '
                   'printed or stored.',
}
doc['checkHash'] = content_hash(doc['counts'])
io.open(S + 'n456_pdf_textlayer.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn456_pdf_textlayer.json' % S)
