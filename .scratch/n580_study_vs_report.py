# -*- coding: utf-8 -*-
"""**41 篇裡有沒有兩篇出自同一個試驗。**（第 580 輪，答 n+192 三）

## 🚨 交辦的原話：「🚫 不要憑印象說『應該沒有』」

✅ 本支照辦：跑的是 `ahig/stats/family.py` 的**真程式**（`build_families`），
🚫 不是另寫一個近似的。

## 🚨 而它給出的答案是「答不了」，不是「沒有」

`build_families` 回報 **0 個成群**。**⚠️ 但那句話幾乎是空的**，因為 tier1 的三條規則
在本語料的訊號涵蓋率是這樣：

| tier1 規則 | 需要的訊號 | 41 篇裡有的 |
|---|---|---|
| `FAM-T1-001-same-doi` | DOI | ⚠️ 每篇各一個，**依建構就不可能相同** |
| `FAM-T1-002-same-registry-id` | 試驗登錄號 | **🚨 3 篇**（全為 NCT） |
| `FAM-T1-003-acronym-plus-shared-key-author` | 試驗簡稱 | **🚨 0 篇**（無處確定性可取） |

> **🚨 故「0 個成群」= 38 篇根本沒有被看過。**
> ⚠️ 這正是本 run 一再抓到的那一族：**量到的東西，不是結論所依賴的東西。**
> ✅ 本支因此讓那道探針**亮紅**——🚫 拒絕以 exit 0 回報一個答不了的問題。

## ✅ 能補的那一半：作者重疊篩選（🚨 不是 family.py 的任何一層）

✅ **41 篇全部取得出作者**：26 篇 JATS 取 `<front>`，15 篇 GROBID 取 `<teiHeader>`。

> **🚨 第 580 輪本支在這裡說錯過一次**：當時寫「那 15 篇只留下 PDF、連作者都取不到」。
> ⚠️ 實情是 TEI 一直都在，只是存在 manifest 的 `teiFile` 而非 `rawFile`——
> **🚨 本室只看了 rawFile 就下結論，而「檔案不存在」與「我查錯欄位」長得一樣。**

> ✅ 故本支另跑一個**自算的**篩選：兩篇共有 ≥2 位正規化後相同的作者，
> 且出版年相差 ≤ 4 年 → 列為**待人看**。
> **🚫 它不是 family.py 的 tier，也不是判定**；⚠️ 它只是把「值得看一眼的配對」
> 從 820 對（41 取 2）縮到少數幾對。
> **🚨 而這個領域同一實驗室互相掛名極常見，故偽陽性率高**——
> ✅ 每一對另記「第一作者是否相同」「末位作者是否相同」，🚫 讓人不必逐對重查。
> ✅ **涵蓋率 41／41**（🚨 第 580 輪誤報為 26／41，見上）。

## 🚫 本支不入輪次閘門，且不把識別碼寫進 repo

⚠️ 名字、DOI、登錄號一律只留在私有根；**✅ 本檔輸出只有計數與 16 碼報告雜湊。**
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402
from ahig.stats.family import (Report, build_families,  # noqa: E402
                               normalise_author, normalise_registry_id)

OUT = Path(__file__).resolve().parent / 'n580_study_vs_report.json'
DETAIL = ROOT / 'extraction' / 'n580-family-detail.json'

REGISTRY = re.compile(
    r'(NCT\d{8}|ISRCTN\d{8}|ACTRN\d{14}|ChiCTR[-\w]{6,20}|DRKS\d{8}'
    r'|UMIN\d{9}|CTRI/\d{4}/\d{2,3}/\d{6}|PACTR\d{12,16}|IRCT\d{11,18}N\d+)')
AUTHOR = re.compile(r'<surname>([^<]{1,60})</surname>\s*'
                    r'(?:<given-names>([^<]{0,60})</given-names>)?')
JATS_DOI = re.compile(r'<article-id pub-id-type="doi">([^<]+)</article-id>')
JATS_YEAR = re.compile(r'<year[^>]*>(\d{4})</year>')
TEI_DOI = re.compile(r'<idno type="DOI">([^<]+)</idno>')
TEI_YEAR = re.compile(r'<date type="published" when="(\d{4})')

# 🚨 第 581 輪更正：第 580 輪本支寫「GROBID 的 TEI 未留存，那 15 篇連作者都取不到」。
# **⚠️ 那句話是錯的。** TEI 一直都在，只是存在 manifest 的 `teiFile` 而不是 `rawFile`
# （`rawFile` 是 PDF）。🚨 本室當時只看了 rawFile 就下了結論，
# **而「檔案不存在」與「我查錯欄位」在畫面上長得一樣。**
# ✅ 15 篇的 TEI 全在，作者、DOI、出版日期都在 `<teiHeader>` 裡，涵蓋率因此是 41／41。
FRONT_CUT = {'europe-pmc-jats': ('rawFile', '</front>'),
             'grobid-tei': ('teiFile', '</teiHeader>')}


def manifests():
    """report 短碼 → 取得清單（含檔案位置）。"""
    out = {}
    for path in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        key = doc.get('candidateId', '').split(':')[-1][-16:]
        out[key] = (doc, path.parent)
    return out


def front_matter(doc, folder):
    """🚨 只取前置資料：⚠️ 參考文獻裡也有一大堆 surname，取全文等於亂抓。"""
    kind = doc.get('sourceType')
    if kind not in FRONT_CUT or folder is None:
        return None, kind
    field_name, closing = FRONT_CUT[kind]
    name = doc.get(field_name)
    path = folder / name if name else None
    if not path or not path.exists():
        return None, kind
    text = path.read_text(encoding='utf-8', errors='ignore')
    cut = text.find(closing)
    return (text[:cut] if cut > 0 else None), kind


def main():
    ids, unnameable = corpus.acquired_roster()
    mans = manifests()

    reports, coverage, detail = [], {'registry': 0, 'doi': 0, 'authors': 0,
                                     'year': 0, 'jats': 0, 'tei': 0,
                                     'noFrontMatter': 0}, []
    for candidate in ids:
        key = candidate[-16:]
        doc, folder = mans.get(key, ({}, None))
        content = corpus.load_document(candidate).content
        found = sorted({normalise_registry_id(m) for m in REGISTRY.findall(content)}
                       - {None})
        front, kind = front_matter(doc, folder)
        coverage['jats' if kind == 'europe-pmc-jats'
                 else 'tei' if kind == 'grobid-tei' else 'noFrontMatter'] += 1

        names, doi, year = [], None, None
        if front:
            names = [normalise_author((given + ' ' + surname).strip())
                     for surname, given in AUTHOR.findall(front)]
            doi_re, year_re = ((JATS_DOI, JATS_YEAR)
                               if kind == 'europe-pmc-jats'
                               else (TEI_DOI, TEI_YEAR))
            hit = doi_re.search(front)
            doi = hit.group(1) if hit else None
            hit = year_re.search(front)
            year = int(hit.group(1)) if hit else None

        # 🚨 一篇找到兩個以上登錄號時**不用**：⚠️ 多半是引用了別的試驗，
        # 而拿它當確定性訊號會製造假的成群。✅ 另列為待人看。
        registry = found[0] if len(found) == 1 else None
        coverage['registry'] += 1 if registry else 0
        coverage['doi'] += 1 if doi else 0
        coverage['authors'] += 1 if names else 0
        coverage['year'] += 1 if year else 0

        reports.append(Report(work_id=key, registry_id=registry, doi=doi,
                              authors=names, publication_year=year))
        detail.append({'report': key, 'registryIds': found, 'doi': doi,
                       'authorCount': len(names), 'year': year,
                       'sourceType': doc.get('sourceType')})

    families = build_families(reports)
    grouped = [f for f in families['families'] if len(f['members']) > 1]

    # ✅ 自算的篩選（🚫 不是 family.py 的 tier）：共有 ≥2 位作者且年份相近。
    by_id = {r.work_id: r for r in reports}
    screen = []
    for a, b in combinations([r for r in reports if r.authors], 2):
        shared = set(a.norm_authors) & set(b.norm_authors)
        span = (abs(a.publication_year - b.publication_year)
                if a.publication_year and b.publication_year else None)
        if len(shared) >= 2 and (span is None or span <= 4):
            # 🚨 這個領域同一實驗室互相掛名極常見，⚠️「共有 2 位作者」的偽陽性很高。
            # ✅ 故一併記下**第一作者**與**末位作者**是否也相同——
            # ⚠️ 同一試驗的姊妹論文通常共用資深（末位）作者，🚫 而純掛名通常不會。
            screen.append({'pair': [a.work_id, b.work_id],
                           'sharedAuthors': len(shared), 'yearSpan': span,
                           'sameFirstAuthor': a.first_author == b.first_author,
                           'sameLastAuthor': (a.last_author is not None
                                              and a.last_author == b.last_author)})
    screen.sort(key=lambda s: -s['sharedAuthors'])
    # 🚨 出版年取不到時，本篩選一律**放行**（span is None）。
    # ⚠️ 故 17 對裡有一部分是靠「不知道」進來的，🚫 那不是「年份接近」。
    unknown_year = sum(1 for s in screen if s['yearSpan'] is None)

    # ✅ 把邊併成連通群組——📮 要人看的是「這幾篇是不是同一個試驗」，
    # ⚠️ 而那是群組層次的問題，🚫 不是一對一對看得完的。
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for edge in screen:
        a, b = (find(x) for x in edge['pair'])
        if a != b:
            parent[a] = b
    groups = {}
    for node in list(parent):
        groups.setdefault(find(node), []).append(node)
    clusters = sorted((sorted(v) for v in groups.values() if len(v) > 1),
                      key=lambda g: -len(g))

    probes = []

    def probe(name, ok, detail_text):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail_text})

    probe('41 篇全部進了 family.py（必觸發）',
          len(reports) == len(ids) == 41,
          '🚨 少一篇，成群判定就是在一個較小的語料上做的，'
          '⚠️ 而較小的語料看起來跟完整的一樣；實得 %d 篇' % len(reports))
    # 🚨 必觸發之反向：**成群機制本身會不會動**。
    # ⚠️ 若 build_families 根本連不起任何一條邊，「0 個成群」也會長這樣。
    clone = Report(work_id='SYNTHETIC-CLONE', registry_id='NCT00000001')
    origin = Report(work_id='SYNTHETIC-ORIGIN', registry_id='NCT00000001')
    canary = build_families([clone, origin])
    probe('成群機制真的連得起來（必觸發之反向）',
          any(len(f['members']) > 1 for f in canary['families']),
          '🚨 以兩筆同登錄號的合成資料試 build_families；'
          '⚠️ 連不起來的話，「0 個成群」只是機制沒動')
    # 🚨 這一道**故意會紅**：它問的不是「有沒有成群」，是「有沒有資格回答」。
    probe('tier1 有足夠訊號可以回答這個問題',
          coverage['registry'] >= len(ids) * 0.5,
          '🚨 tier1 唯一會成群的訊號是登錄號，而 41 篇裡只有 %d 篇有；'
          '⚠️ 故「0 個成群」等於 %d 篇沒被看過，🚫 不是「沒有重複」'
          % (coverage['registry'], len(ids) - coverage['registry']))

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps({'documentType': 'family-detail-private',
                                  'items': detail}, ensure_ascii=False,
                                 indent=2) + '\n', encoding='utf-8')

    out = {
        'schemaVersion': 1,
        'documentType': 'study-vs-report-family-scan',
        'ruling': 'n+192（三）：拿 41 篇跑 stats/family.py 的 tier1，據實回報有沒有成群',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'corpusSize': len(ids),
        'tier1Families': len(grouped),
        'tier1Edges': len(families['tier1Edges']),
        'suspectedPairs': len(families['suspectedPairs']),
        'signalCoverage': coverage,
        'verdict': (
            '🚨 tier1 回報 0 個成群，**而那句話答不了問題**：'
            '⚠️ 唯一會讓不同論文成群的訊號是試驗登錄號，41 篇裡只有 %d 篇有；'
            'DOI 依建構每篇各異，試驗簡稱無處可取。'
            '🚫 故本支不得被引用為「沒有重複計數」。' % coverage['registry']),
        'correctionToRound580': (
            '🚨 第 580 輪本支報「15 篇只留下 PDF，連作者都取不到」——⚠️ 那是錯的。'
            'TEI 一直都在，存在 manifest 的 teiFile 而非 rawFile；'
            '✅ 作者涵蓋率實為 41／41，🚫 不是 26／41。'),
        'authorOverlapScreen': {
            'whatItIs': ('✅ 本支自算：共有 ≥2 位正規化後相同的作者且出版年相差 ≤4。'
                         '🚫 不是 family.py 的 tier，🚫 不是判定，'
                         '⚠️ 只是把值得看一眼的配對縮小。'),
            'eligibleReports': coverage['authors'],
            'pairsConsidered': len([1 for _ in combinations(
                [r for r in reports if r.authors], 2)]),
            'flaggedPairs': len(screen),
            'flaggedWithUnknownYear': unknown_year,
            'clusters': clusters,
            'largestCluster': max((len(c) for c in clusters), default=0),
            'flagged': screen,
        },
        'detailKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    out['auditHash'] = content_hash(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n580 研究 vs 論文：tier1 成群判定 ===')
    print('   語料 %d 篇｜JATS %d／TEI %d／無前置資料 %d'
          % (len(ids), coverage['jats'], coverage['tei'],
             coverage['noFrontMatter']))
    print('   訊號涵蓋：登錄號 %d｜DOI %d｜作者 %d｜年份 %d'
          % (coverage['registry'], coverage['doi'], coverage['authors'],
             coverage['year']))
    print('   🚨 tier1 成群 %d 個｜tier1 邊 %d 條｜suspected %d 對'
          % (len(grouped), len(families['tier1Edges']),
             len(families['suspectedPairs'])))
    print('   ── 作者重疊篩選（🚫 非 family.py 之層級）──')
    print('   可篩選 %d 篇｜待人看 %d 對（其中 %d 對是年份不明而放行）'
          % (coverage['authors'], len(screen), unknown_year))
    print('   🚨 併成連通群組後：%d 群，最大一群 %d 篇'
          % (len(clusters), max((len(c) for c in clusters), default=0)))
    for c in clusters:
        print('      %d 篇：%s' % (len(c), ' '.join(c)))
    for s in screen[:12]:
        print('      %s ↔ %s：共同 %d 位，年差 %s%s%s'
              % (s['pair'][0], s['pair'][1], s['sharedAuthors'], s['yearSpan'],
                 '，🚨 同第一作者' if s['sameFirstAuthor'] else '',
                 '，🚨 同末位作者' if s['sameLastAuthor'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（識別碼留在私有根：%s）' % (OUT.name, DETAIL.name))
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
