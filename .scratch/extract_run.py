# -*- coding: utf-8 -*-
"""**萃取批次的執行器**：清冊回來那一端。（第 554 輪建立）

## 用法

```
python .scratch/extract_run.py            # 只印進度，🚫 不跑鏈、不落盤
python .scratch/extract_run.py --run      # 真的跑，並把清冊與收據落盤
```

## 🚨 只餵已讀的那些

第 548 輪實測 18 輪的中途：**若照樣餵全部 41 篇，收據上會出現 41−N 筆
`call-reader` 失敗**（訊息為「工作單收回來的清冊裡沒有這一篇」）。
**⚠️ 那是中途的常態，🚫 不是壞掉**——**🚨 但收據長得跟真的壞掉一模一樣。**

> **✅ 故本支只餵已經有清冊的那些**（`load_drafts(require_complete=False)` 的產物）。
> ⚠️ 沒有清冊的那幾篇會列在「尚未讀」，🚫 不會被算成失敗。

## 🚨 為什麼預設不跑

跑起來會**把清冊寫進私有根**。⚠️ 若 `drafts.json` 裡是替身或試寫的東西，
**🚨 落盤之後它們看起來就跟真的清冊一樣**——存放處的鍵只認綁定，分不出真假。
**✅ 故預設只印進度；要真的跑得自己加 `--run`。**
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
from ahig.extraction import run_inventory, store, worksheet  # noqa: E402

CONTRACT_PATH = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
                 / 'scope-contract.json')
OUT_DIR = ROOT / 'extraction-worksheet'


def main(argv):
    go = '--run' in argv[1:]

    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if contract.get('status') != 'frozen' or not verify_frozen(
            contract, 'scopeContractHash'):
        print('🚨 契約不是可用的凍結契約——🚫 拒絕跑', file=sys.stderr)
        return 2
    if not (OUT_DIR / 'worksheet.json').exists():
        print('🚨 找不到工作單：%s' % OUT_DIR, file=sys.stderr)
        print('   ⚠️ 請先跑 .scratch/extract_worksheet.py --write', file=sys.stderr)
        return 2

    loaded = worksheet.load_drafts(OUT_DIR, require_complete=False)
    drafted = list(loaded['drafts'])

    print('=== 萃取批次 ===')
    print('   工作單 %d 篇｜已有清冊 %d 篇｜尚未讀 %d 篇'
          % (loaded['itemCount'], loaded['draftedCount'],
             len(loaded['remaining'])))
    print('   讀的人 %s' % (loaded['readBy'] or '🚨 未記'))
    if not drafted:
        print('   🚫 一份清冊都還沒有——沒有東西可跑。')
        return 0

    if not go:
        print()
        print('   🚫 乾跑：沒有跑鏈，也沒有落盤。⚠️ 要真的跑請加 --run。')
        print('   🚨 跑起來會把清冊寫進私有根；⚠️ 若 drafts.json 裡是試寫的東西，')
        print('      落盤之後它們看起來就跟真的清冊一樣。')
        return 0

    run = run_inventory(contract, reader=worksheet.reader_from(loaded['drafts']),
                        candidate_ids=drafted, store=store)
    record = run.to_batch_record()

    print()
    print('   這一趟讀了 %d 篇｜重用 %d 篇｜失敗 %d 篇'
          % (len(run.read_this_run), len(run.reused), len(run.failed)))
    print('   送出 %d 字元｜收回 %d 字元（🚨 字元，不是 token，也不是錢）'
          % (record['charsSent'], record['charsReturned']))
    print('   出處指不到真章節者 %d 個（🚫 不影響成敗，見 run.py 說明）'
          % record['unknownSections'])
    for outcome in run.failed:
        print('   🚨 %s @%s：%s'
              % (outcome.candidate_id[-16:], outcome.stage, outcome.error[:110]))
    print('   收據 %s' % run.batch_path)
    if loaded['remaining']:
        print('   ⚠️ 尚未讀 %d 篇——🚫 它們不在本趟的分母裡，也沒有被算成失敗。'
              % len(loaded['remaining']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
