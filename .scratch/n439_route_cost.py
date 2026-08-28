# -*- coding: utf-8 -*-
"""兩條取文路徑之實際成本——⚠️ n+114（三）之成本區分需要修正。

## 🚨 要修正的那一句

n+114（三）呈給擁有者之成本欄寫：

| ＋PDF 解析 | **裝** GROBID 或 Docling | 29 | **裝工具**（`parse_tei` 已在，**不需寫程式**）|

**⚠️ 「`parse_tei` 已在」屬實，但「不需寫程式」不成立。**

**🚨 實查**：
- `parse_tei` **只有測試在呼叫**（`tests/test_fulltext.py` 兩處），
  **取文流程中沒有任何地方用到它**；對照 `parse_jats` 接在 `fulltext.py:681`。
- `available-pdf` 分支（`fulltext.py:1001`）**只把網址寫進 manifest 就結束**
  ——**⚠️ 不下載 PDF、不呼叫 GROBID、不產生 artifacts**（該 manifest 之 `artifacts` 為 `[]`）。
- `fulltext.py:360` 尚有 `"pdfLocatorReady": False` 之標記。

**故 PDF 路缺的是**：①抓 PDF ②呼叫 GROBID ③把 TEI 接進 manifest／artifacts 之寫入路徑。
**✅ 已有的是最難的那塊**——`parse_tei` 之節切分與字元偏移契約已寫好且有測試。

**⚠️ 修正後的說法應是**：
**「PDF 路：解析器已備，缺取得與接線」vs「HTML 路：解析器與取得皆缺」**
——**🚨 仍有量級差，但兩者都要寫程式。**

## 🚨 第二項發現：兩條路都大量是機構典藏庫，不是各家出版社版面

**⚠️ 「HTML 解析器」聽起來像要對付 16 種出版社版面**，實際網域分布不是那樣：
機構典藏庫（DSpace／Pure／Eprints 等）有標準介面，與逐家刻版面不是同一件事。

**🚨 本檔只依網域分類，不宣稱各站實際可取**——⚠️ 那要真的去抓，屬新能力，本室不自行開通。

## ⚠️ 第三項：`miss` 這個結論標籤混了兩種成因

第 438 輪本室報「33 筆全部 miss，該路徑已窮盡」。**結論成立，但標籤不精確**：

- **甲：查不到 PMCID（走 search 端點）** ← 32 筆
- **乙：已知 PMCID，`fullTextXML` 回 404** ← 1 筆（1995 年之期刊，PMC 有掃描件但不在 OA 全文子集）

**⚠️ 兩者的補救路徑不同**，只寫「miss」會讓讀者以為都是同一回事。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：程式碼中是否存在接線、網域分布、`miss` 之成因。
- 🚨 查不到：**各典藏庫是否真的提供可解析全文**——⚠️ 需實際抓取方知，
  故本檔之分類是**成本估計之依據，不是可取得之保證**。
"""
import io
import json
import os
import re
import sys
from collections import Counter
from urllib.parse import urlparse

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.search.fulltext import _artifact_dir  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'

# ⚠️ 分類逐一列名，🚨 不用樣式猜——網域名稱不足以自動判別典藏庫軟體。
KIND = {
    'researchportal.bath.ac.uk': '機構典藏庫',
    'purehost.bath.ac.uk': '機構典藏庫',
    'dspace.lboro.ac.uk': '機構典藏庫',
    'cris.maastrichtuniversity.nl': '機構典藏庫',
    'birmingham.elsevierpure.com': '機構典藏庫',
    'utoronto.scholaris.ca': '機構典藏庫',
    'eprints.gla.ac.uk': '機構典藏庫',
    'ro.ecu.edu.au': '機構典藏庫',
    'researchonline.ljmu.ac.uk': '機構典藏庫',
    'figshare.com': '資料典藏（有 API）',
    'doi.org': '🚨 未解析之 DOI（真正的落點未知）',
    'www.ncbi.nlm.nih.gov': 'NCBI PMC（掃描件，不在 OA 全文子集）',
    'link.springer.com': '出版社',
    'www.sciencedirect.com': '出版社',
    'onlinelibrary.wiley.com': '出版社',
    'journals.physiology.org': '出版社',
    'journals.humankinetics.com': '出版社',
    'www.cambridge.org': '出版社',
}

inv = json.load(io.open(S + 'm1_step3_inventory.json', encoding='utf-8'))
bf = json.load(io.open(S + 'm1_step3_backfill.json', encoding='utf-8'))
final = {r['candidateId']: r['status'] for r in inv['records']
         if r['status'] in set(bf['obtainableDefinition'])}
for pool in bf['pools']:
    for r in pool.get('backfilled') or []:
        if r.get('accepted'):
            final[r['candidateId']] = r['status']

by_status_kind = Counter()
miss_cause = Counter()
unknown_domains = set()
for cid, st in final.items():
    if st == 'acquired':
        continue
    man = json.load(io.open(_artifact_dir(cid) / 'manifest.json',
                            encoding='utf-8'))
    net = urlparse(man.get('availableUrl') or '').netloc
    kind = KIND.get(net)
    if kind is None:
        kind = '🚨 未分類'
        unknown_domains.add(net)
    by_status_kind[(st, kind)] += 1
    ep = [a for a in man['attempts'] if a.get('sourceId') == 'europe-pmc'][0]
    u = ep.get('url') or ''
    miss_cause['乙：已知 PMCID，fullTextXML 回 %s' % ep.get('httpStatus')
               if re.search(r'/PMC\d+/fullTextXML', u)
               else '甲：查不到 PMCID（走 search 端點）'] += 1

print('=== 一、33 筆非 acquired 之落點性質（依網域，逐一列名分類）===')
print('%-26s %-38s %s' % ('狀態', '落點性質', '筆數'))
print('-' * 76)
for (st, k), n in sorted(by_status_kind.items(), key=lambda x: (x[0][0], -x[1])):
    print('%-26s %-38s %d' % (st, k, n))
print('-' * 76)
agg = Counter()
for (_, k), n in by_status_kind.items():
    agg[k] += n
for k, n in agg.most_common():
    print('   合計 %-38s %d' % (k, n))
if unknown_domains:
    print('   🚨 未分類網域：%s（🚫 分類表需補，本檔不猜）' % sorted(unknown_domains))

print()
print('=== 二、`miss` 之兩種成因 ===')
for k, n in miss_cause.most_common():
    print('   %-42s %d 筆' % (k, n))
print('   ⚠️ 第 438 輪「該路徑已窮盡」之結論成立，🚨 惟標籤混了兩種成因。')

doc = {
    'schemaVersion': 1,
    'documentType': 'fulltext-route-cost-analysis',
    'extends': '.scratch/n438_fulltext_route.json',
    'purpose': ('Corrects the cost column n+114(3) puts in front of the owner, '
                'and measures what the two routes would actually face.'),
    'population': 'The 33 non-acquired records among the 45 obtainable.',
    'countingUnit': 'publication',
    'criterion': 'Landing domain of manifest.availableUrl, classified by an '
                 'explicit per-domain table rather than a pattern.',
    'pdfRouteWiring': {
        'parserExists': True,
        'parserWired': False,
        'evidence': ['parse_tei is called only from tests/test_fulltext.py',
                     'parse_jats is wired at fulltext.py:681',
                     'the available-pdf branch at fulltext.py:1001 records the '
                     'URL and stops; manifest artifacts is []',
                     'fulltext.py:360 still carries pdfLocatorReady: False'],
        'missing': ['fetch the PDF bytes', 'invoke GROBID',
                    'wire TEI into the manifest/artifact writer'],
        'correction': ('n+114(3) says the PDF route is "install a tool, no code '
                       'needed". The parser is indeed already written and '
                       'tested -- the hard part -- but acquisition and wiring '
                       'are not. Both routes require code; the gap between them '
                       'is smaller than install-versus-develop.'),
    },
    'landingKinds': {'%s|%s' % k: v for k, v in by_status_kind.items()},
    'landingKindsAggregate': dict(agg),
    'landingKindsNote': ('An HTML route sounds like 16 bespoke publisher '
                         'layouts. Most of these are institutional repositories '
                         '(DSpace/Pure/Eprints) with standard interfaces, plus '
                         'figshare which has an API. That is a different cost '
                         'shape from per-publisher scraping.'),
    'europePmcMissCauses': dict(miss_cause),
    'europePmcMissNote': ('Round 438 reported all 33 as miss and called the '
                          'route exhausted. That conclusion stands, but miss '
                          'conflates two causes: 32 have no PMCID at all, while '
                          '1 has a known PMCID whose fullTextXML returns 404 -- '
                          'a 1995 article held in PMC as scans but outside the '
                          'OA full-text subset. The remedies differ.'),
    'coverageStatement': ('Whether any of these repositories actually serves '
                          'parseable full text is not tested here; that needs '
                          'fetching, a capability this room does not enable on '
                          'its own. The classification informs a cost estimate; '
                          'it is not a promise of availability.'),
    'contentNote': 'Domains, counts and code locations only. No literature content.',
}
doc['costHash'] = content_hash(doc['landingKindsAggregate'])
io.open(S + 'n439_route_cost.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn439_route_cost.json' % S)
