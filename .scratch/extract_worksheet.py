# -*- coding: utf-8 -*-
"""**萃取工作單的產生器**：論文出去那一端。（第 554 輪建立）

## 用法

```
python .scratch/extract_worksheet.py            # 只印計畫，🚫 不寫任何檔
python .scratch/extract_worksheet.py --write    # 真的寫出工作單
```

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
from ahig.extraction.corpus import acquired_roster, reading_request_for  # noqa: E402

CONTRACT_PATH = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
                 / 'scope-contract.json')
OUT_DIR = ROOT / 'extraction-worksheet'


def main(argv):
    write = '--write' in argv[1:]

    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if contract.get('status') != 'frozen':
        print('🚨 契約 status=%r，非 frozen——🚫 不得對著還會變的契約讀論文'
              % contract.get('status'), file=sys.stderr)
        return 2
    if not verify_frozen(contract, 'scopeContractHash'):
        print('🚨 契約雜湊驗不過——🚫 拒絕產生工作單', file=sys.stderr)
        return 2
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
