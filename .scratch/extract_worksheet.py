# -*- coding: utf-8 -*-
"""**萃取工作單的產生器**：論文出去那一端。（第 554 輪建立）

## 用法

```
python .scratch/extract_worksheet.py               # 只印計畫，🚫 不寫任何檔
python .scratch/extract_worksheet.py --write       # 首次寫出工作單
python .scratch/extract_worksheet.py --regenerate  # 🚨 就地更新，保住已讀的清冊
```

## 🚨 `--regenerate`：payload 變了要重發，**而不能把讀過的東西一起刪掉**

n+189 讓請求帶上 `allowedInstruments`，⚠️ 故 payload 變了、工作單要重發。
**🚨 但 `--write` 遇到既有目錄會拒絕**，照做的人只能先刪目錄——
**⚠️ 而 `drafts.json` 與 `drafts/` 就在那個目錄裡。**

> **✅ `--regenerate` 只覆寫 `worksheet.json` 與 `pages/`，
> 🚫 一個位元組都不碰 `drafts.json`、`drafts/`、`second/`。**
>
> **🚨 前提條件：沒有任何一篇換頁。** ⚠️ 逐頁清冊是按頁碼存的
> （`drafts/page-008.json`），**若分頁邊界移動，舊的清冊會對到新的別頁上**，
> 🚨 而那是**安靜的錯**——檔案結構完全正常，只是內容對錯了篇。
> **✅ 故換頁即拒絕，並列出是哪幾篇。**

## 🚨 為什麼預設是不寫

工作單**帶著全文**：實測 41 篇合計 2,039,858 字元（`n535`）。
**⚠️ 寫出去等於私有根裡多一份完整語料副本**，而萃取要走哪一條路
（session 讀／API 讀）**尚待協調者裁定**（第 536 輪提出）。

> **✅ 故本支預設乾跑**：印出會產生幾頁、每頁多大、寫到哪裡，**🚫 一個位元組都不寫。**
> **⚠️ 要真的寫，得自己加 `--write`。**

## 🚫 已存在就拒絕

⚠️ 目錄已存在時**直接拒絕**，🚫 不覆寫也不合併——
**🚨 半新半舊的工作單，與一份乾淨的工作單，在磁碟上看起來一樣。**

## 讀回來那一端

見 `.scratch/extract_run.py`。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import verify_frozen  # noqa: E402
from ahig.extraction import worksheet  # noqa: E402
from ahig.state import atomic_write_json  # noqa: E402
from ahig.extraction.corpus import acquired_roster, reading_request_for  # noqa: E402

CONTRACT_PATH = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
                 / 'scope-contract.json')
OUT_DIR = ROOT / 'extraction-worksheet'


def _regenerate(contract):
    """就地更新工作單，🚫 不動任何已交回的清冊。"""
    if not (OUT_DIR / 'worksheet.json').exists():
        print('🚨 沒有既有工作單可更新：%s' % OUT_DIR, file=sys.stderr)
        print('   ⚠️ 首次請用 --write。', file=sys.stderr)
        return 2

    old = json.loads((OUT_DIR / 'worksheet.json').read_text(encoding='utf-8'))
    ids, unnameable = acquired_roster()
    requests = [reading_request_for(candidate_id, contract)
                for candidate_id in ids]
    new = worksheet.build_worksheet(requests, source='b11-extraction')

    old_page = {it['report']: it['page'] for it in old['items']}
    new_page = {it['report']: it['page'] for it in new['items']}
    moved = sorted(r for r in set(old_page) | set(new_page)
                   if old_page.get(r) != new_page.get(r))

    print('=== 就地更新工作單 ===')
    print('   舊 %d 篇／%d 頁／%d 字元' % (old['itemCount'], old['pageCount'],
                                          old['totalChars']))
    print('   新 %d 篇／%d 頁／%d 字元' % (new['itemCount'], new['pageCount'],
                                          new['totalChars']))
    print('   payload 變動 %+d 字元' % (new['totalChars'] - old['totalChars']))

    if moved:
        print('🚨 有 %d 篇換頁，🚫 拒絕就地更新：' % len(moved), file=sys.stderr)
        for report in moved[:8]:
            print('   %s：第 %s 頁 → 第 %s 頁'
                  % (report[-16:], old_page.get(report), new_page.get(report)),
                  file=sys.stderr)
        print('   ⚠️ 逐頁清冊是按頁碼存的；分頁一移動，舊清冊會對到別頁上，',
              file=sys.stderr)
        print('   🚨 而那是安靜的錯——檔案結構完全正常，只是內容對錯了篇。',
              file=sys.stderr)
        return 2

    print('   ✅ 沒有任何一篇換頁——逐頁清冊仍對得上。')

    kept = sorted(p.name for p in OUT_DIR.rglob('*.json')
                  if p.parent.name in ('drafts', 'second')
                  or p.name == 'drafts.json')
    index = {k: v for k, v in new.items() if k != 'items'}
    index['items'] = [{k: v for k, v in item.items() if k != 'payload'}
                      for item in new['items']]
    atomic_write_json(OUT_DIR / 'worksheet.json', index)
    for number in range(1, new['pageCount'] + 1):
        items = [it for it in new['items'] if it['page'] == number]
        atomic_write_json(OUT_DIR / 'pages' / ('page-%03d.json' % number), {
            'documentType': 'extraction-worksheet-page',
            'source': 'b11-extraction', 'page': number,
            'pageCount': new['pageCount'], 'itemCount': len(items),
            'chars': sum(it['payloadChars'] for it in items),
            'items': items})
    print('   ✅ 已更新 worksheet.json 與 pages/page-001..%03d.json'
          % new['pageCount'])
    print('   🚫 未觸碰：%s' % (', '.join(kept) if kept else '（無既有清冊）'))
    return 0


def main(argv):
    write = '--write' in argv[1:]
    regenerate = '--regenerate' in argv[1:]

    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if contract.get('status') != 'frozen':
        print('🚨 契約 status=%r，非 frozen——🚫 不得對著還會變的契約讀論文'
              % contract.get('status'), file=sys.stderr)
        return 2
    if not verify_frozen(contract, 'scopeContractHash'):
        print('🚨 契約雜湊驗不過——🚫 拒絕產生工作單', file=sys.stderr)
        return 2
    if regenerate:
        return _regenerate(contract)
    if write and OUT_DIR.exists():
        print('🚨 %s 已存在——🚫 拒絕覆寫或合併。' % OUT_DIR.name, file=sys.stderr)
        print('   ⚠️ 半新半舊的工作單，與一份乾淨的工作單，在磁碟上看起來一樣。',
              file=sys.stderr)
        return 2

    ids, unnameable = acquired_roster()
    if not ids:
        print('🚨 名冊為零——🚫 拒絕產生空工作單', file=sys.stderr)
        return 2
    requests = [reading_request_for(candidate_id, contract)
                for candidate_id in ids]
    sheet = worksheet.build_worksheet(requests, source='b11-extraction')

    per_page = {}
    for item in sheet['items']:
        per_page.setdefault(item['page'], []).append(item['payloadChars'])

    print('=== 萃取工作單 ===')
    print('   契約   %s（frozen ✅）' % contract.get('scopeContractId'))
    print('   語料   %d 篇' % len(ids))
    if unnameable:
        print('   🚨 連 candidateId 都讀不出來的目錄 %d 個，'
              '⚠️ 它們不在工作單內：' % len(unnameable))
        for name, error in unnameable[:5]:
            print('      %s  %s' % (name[-16:], error[:70]))
    print('   分頁   %d 頁（每頁預算 %d 字元）'
          % (sheet['pageCount'], sheet['pageChars']))
    print('   總量   %d 字元｜每頁 %d–%d 篇／%d–%d 字元'
          % (sheet['totalChars'],
             min(len(v) for v in per_page.values()),
             max(len(v) for v in per_page.values()),
             min(sum(v) for v in per_page.values()),
             max(sum(v) for v in per_page.values())))
    print('   寫到   %s' % OUT_DIR)

    if not write:
        print()
        print('   🚫 乾跑：一個位元組都沒寫。⚠️ 要真的寫請加 --write。')
        print('   🚨 工作單帶著全文——寫出去等於私有根裡多一份完整語料副本，')
        print('      ⚠️ 而萃取走哪一條路（session／API）尚待裁定。')
        return 0

    worksheet.write_worksheet(OUT_DIR, requests, source='b11-extraction')
    print()
    print('   ✅ 已寫出：worksheet.json（索引，🚫 不帶全文）'
          '＋ pages/page-001..%03d.json＋空的 drafts.json'
          % sheet['pageCount'])
    print('   下一步：一輪讀一頁，把清冊併回 drafts.json，'
          '再跑 .scratch/extract_run.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
