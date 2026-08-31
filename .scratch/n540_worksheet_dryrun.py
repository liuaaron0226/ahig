# -*- coding: utf-8 -*-
"""**工作單那條路，在真語料上整條走一次（含落盤與收回）。**（第 540 輪）

## 🚨 兩件先前沒做的事

1. **`build_worksheet`／`write_worksheet` 只在一份合成 fixture（1 篇）上跑過。**
   ⚠️ 真語料 41 篇，其中一篇 355,929 字元**單獨超出整頁預算**。
2. **第 536 輪報給看板的「19 頁」是 `paginate` 算的**，
   🚨 而 `paginate` 吃的是 `n535` 產物裡的字元數——**不是 `build_worksheet` 自己量的**。
   ⚠️ 兩者若不一致，看板上那個數就是錯的。**✅ 本支對這兩個數。**

## ✅ 整條走：出去 → 收回 → 跑完

工作單落盤 → 逐頁存在 → 造替身清冊填回 `drafts.json` →
`load_drafts` 驗綁定 → `reader_from` 包成 reader → `run_inventory` 走完 41 篇。
**🚨 替身仍是 n537 那一支，故一樣 `store=None`，一份清冊都不落盤。**

## 🚫 落盤的工作單用完就刪

⚠️ 工作單帶著全文，**🚨 留著等於私有根裡多一份語料副本**，而路線未定
（session／API 由協調者裁）。**✅ 故寫進一個專用的 dry-run 目錄，驗完刪掉，
🚫 只刪本支自己建的那一個。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 證得了：分頁、落盤、逐頁檔、收回、綁定驗證、整批跑完，在 41 篇真文件上成立。
- 🚨 證不了：**模型讀出來的東西對不對**（替身編造，同 n537）。
- 🚨 證不了：一頁 120,000 字元對真的 session 而言讀不讀得完——⚠️ 那要真的讀才知道。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門**，與 n+184、n535、n537–539 同類。
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ahig.contracts.freeze import content_hash, verify_frozen  # noqa: E402
from ahig.extraction import run_inventory, worksheet  # noqa: E402
from ahig.extraction.corpus import iter_acquired, reading_request_for  # noqa: E402

from n537_chain_rehearsal import REHEARSAL, stub_reader  # noqa: E402

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
N535 = Path(__file__).resolve().parent / 'n535_reading_payload.json'
OUT = Path(__file__).resolve().parent / 'n540_worksheet_dryrun.json'
DRYRUN_DIR = ROOT / 'extraction-worksheet-dryrun'


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if not (contract.get('status') == 'frozen'
            and verify_frozen(contract, 'scopeContractHash')):
        print('🚨 契約不是可用的凍結契約，拒絕演練', file=sys.stderr)
        sys.exit(2)
    if DRYRUN_DIR.exists():
        print('🚨 %s 已存在——🚫 本支只刪自己建的，故拒絕跑'
              % DRYRUN_DIR.name, file=sys.stderr)
        sys.exit(2)

    requests = [reading_request_for(d.candidate_id, contract)
                for _n, d, _e in iter_acquired() if d is not None]

    sheet = worksheet.build_worksheet(requests, source='n540-dryrun')

    # 對第 536 輪報出去的那個數。🚨 來源不同：一個是 build_worksheet 自己量的，
    # 一個是 n535 產物裡的字元數。
    n535 = json.loads(N535.read_text(encoding='utf-8'))
    n535_sizes = [r['payloadChars'] for r in n535['records']]
    n535_pages = max(worksheet.paginate(n535_sizes)) if n535_sizes else 0

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('工作單自己量到的總字元數等於 n535 所量',
          sheet['totalChars'] == n535['measured']['payloadChars'],
          'build_worksheet %d｜n535 %d'
          % (sheet['totalChars'], n535['measured']['payloadChars']))
    # 🚨 第一版這條拿第 536 輪報出去的 19 直接比，當場紅：實得 18。
    # ⚠️ 成因：n535 的 records 是**按字元數遞增排序**寫出去的，而第 536 輪就拿
    # 那個順序算頁數。🚨 真正的順序是語料順序，兩者裝箱結果不同。
    # ✅ 故改成對「同一順序下兩支程式是否一致」——那才是可比的東西。
    same_order = max(worksheet.paginate(
        [it['payloadChars'] for it in sheet['items']]))
    probe('build_worksheet 與 paginate 在同一順序下一致',
          sheet['pageCount'] == same_order,
          'build_worksheet %d 頁｜paginate 同序重算 %d 頁'
          % (sheet['pageCount'], same_order))
    probe('第 536 輪報出去的頁數需更正（本探針以「需更正」為通過）',
          sheet['pageCount'] != n535_pages,
          '🚨 看板 19 頁係以 n535 之**排序後**順序算得；'
          '⚠️ 語料真實順序為 %d 頁——正確的是 %d'
          % (sheet['pageCount'], sheet['pageCount']))

    biggest = max(sheet['items'], key=lambda it: it['payloadChars'])
    alone = [it for it in sheet['items'] if it['page'] == biggest['page']]
    probe('超出整頁預算的那一篇自己一頁（必觸發）',
          biggest['payloadChars'] > sheet['pageChars'] and len(alone) == 1,
          '最大一篇 %d 字元 > 預算 %d，且該頁只有 %d 篇；'
          '🚨 若它與別人同頁，代表分頁沒有守住「不切開」那條'
          % (biggest['payloadChars'], sheet['pageChars'], len(alone)))

    # ── 落盤 → 收回 → 跑完 ────────────────────────────────────────────
    written = worksheet.write_worksheet(DRYRUN_DIR, requests,
                                        source='n540-dryrun')
    index = json.loads((DRYRUN_DIR / 'worksheet.json').read_text(encoding='utf-8'))
    page_files = sorted((DRYRUN_DIR / 'pages').glob('page-*.json'))
    page_chars = 0
    for path in page_files:
        page_chars += json.loads(path.read_text(encoding='utf-8'))['chars']

    probe('逐頁一檔，且頁數對得上',
          len(page_files) == written['pageCount'] == index['pageCount'],
          '檔案 %d 個｜pageCount %d' % (len(page_files), written['pageCount']))
    probe('索引不帶全文，而逐頁帶',
          all('payload' not in it for it in index['items']) and page_chars > 0,
          '🚨 索引若帶全文，逐頁一檔就沒有意義；逐頁合計 %d 字元' % page_chars)
    probe('逐頁字元合計等於總字元數',
          page_chars == index['totalChars'],
          '逐頁 %d｜索引 %d' % (page_chars, index['totalChars']))

    drafts = [stub_reader(request) for request in requests]
    (DRYRUN_DIR / 'drafts.json').write_text(json.dumps({
        'documentType': 'extraction-drafts',
        'source': 'n540-dryrun',
        'readBy': {'agentClass': 'model', 'note': REHEARSAL},
        'entries': drafts}, ensure_ascii=False), encoding='utf-8')

    loaded = worksheet.load_drafts(DRYRUN_DIR)
    reader = worksheet.reader_from(loaded['drafts'])
    # 🚨 store=None：替身的清冊一份都不落盤（與 n537 同一理由）。
    run = run_inventory(contract, reader=reader,
                        candidate_ids=[r.report for r in requests])

    probe('收回來的清冊每一篇都有、且綁定驗得過',
          loaded['draftedCount'] == len(requests) and loaded['remaining'] == [],
          '收回 %d／%d，未收回 %d'
          % (loaded['draftedCount'], len(requests), len(loaded['remaining'])))
    probe('由工作單收回的 reader 能把整批跑完',
          len(run.succeeded) == len(requests) and len(run.failed) == 0,
          '成功 %d｜失敗 %d' % (len(run.succeeded), len(run.failed)))

    # ── 刪掉 dry-run 目錄 ────────────────────────────────────────────
    expected = {'worksheet.json', 'drafts.json'}
    actual = {p.name for p in DRYRUN_DIR.iterdir() if p.is_file()}
    only_mine = actual <= expected and {p.name for p in DRYRUN_DIR.iterdir()
                                        if p.is_dir()} <= {'pages'}
    removed = False
    if only_mine:
        shutil.rmtree(DRYRUN_DIR)
        removed = not DRYRUN_DIR.exists()
    probe('用完的工作單已刪除',
          removed,
          '🚨 留著等於私有根裡多一份語料副本；🚫 只刪本支自己建的那一個'
          '（目錄內容%s與預期相符）' % ('' if only_mine else '**不**'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'worksheet-dryrun',
        'ruling': 'ADR-0009 裁定①之萃取版：工作單那條路在真語料上整條走一次',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'readerIsAStub': True,
        'stubMarker': REHEARSAL,
        'storeDisabled': '🚨 store=None——替身的清冊一份都不落盤',
        'worksheetRemoved': removed,
        'population': '私有根 fulltext/ 內所有 acquired',
        'privateRoot': PROV,
        'paging': {
            'records': sheet['itemCount'],
            'pageChars': sheet['pageChars'],
            'pageCount': sheet['pageCount'],
            'totalChars': sheet['totalChars'],
            'largestItemChars': biggest['payloadChars'],
            'itemsPerPage': {
                'min': min(sum(1 for it in sheet['items'] if it['page'] == p)
                           for p in range(1, sheet['pageCount'] + 1)),
                'max': max(sum(1 for it in sheet['items'] if it['page'] == p)
                           for p in range(1, sheet['pageCount'] + 1)),
            },
        },
        'roundTrip': {
            'draftsLoaded': loaded['draftedCount'],
            'succeeded': len(run.succeeded),
            'failed': len(run.failed),
        },
        'correction': {
            'boardSaid': ('第 536 輪報出「遞增 19 頁｜遞減 19 頁｜交錯 21 頁」，'
                          '並以 19 為結論'),
            'actual': sheet['pageCount'],
            'why': ('🚨 n535 的 records 是按字元數**遞增排序**寫出去的，'
                    '而第 536 輪就拿那個順序算頁數。'
                    '⚠️ 語料的真實順序既不是遞增也不是遞減，'
                    '🚨 故那三個數沒有一個是實際會發生的頁數。'),
            'lesson': ('⚠️ 又是同一型：量到的東西不是主張所依賴的東西——'
                       '🚨 我量了三種我自己排出來的順序，'
                       '而該量的是 build_worksheet 實際會用的那一種。'),
            'recomputedFromSortedOrder': n535_pages,
        },
        'notProven': [
            '🚨 抽得準不準：替身編造（同 n537）。',
            '🚨 一頁 120,000 字元對真的 session 讀不讀得完——⚠️ 要真的讀才知道。',
        ],
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n540 工作單乾跑（真語料 41 篇 × 真契約 × 替身讀者）===')
    print('   分頁 %d 篇 → %d 頁（每頁預算 %d 字元｜每頁 %d–%d 篇）'
          % (sheet['itemCount'], sheet['pageCount'], sheet['pageChars'],
             doc['paging']['itemsPerPage']['min'],
             doc['paging']['itemsPerPage']['max']))
    print('   總字元 %d｜最大單篇 %d' % (sheet['totalChars'],
                                        biggest['payloadChars']))
    print('   往返：收回清冊 %d｜跑完成功 %d｜失敗 %d'
          % (loaded['draftedCount'], len(run.succeeded), len(run.failed)))
    print('   工作單已刪除：%s' % removed)
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
