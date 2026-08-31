# -*- coding: utf-8 -*-
"""**逐頁認領**：多個終端機同時讀時，每個視窗用這一支拿自己那一頁。（第 487 輪）

## 用法

```
python .scratch/extract_page.py                 # 每一頁的狀態（已讀／未讀）
python .scratch/extract_page.py 3               # 印出第 3 頁，供這個視窗讀
python .scratch/extract_page.py 3 --submit x.json   # 把讀好的清冊交回
python .scratch/extract_page.py 3 --submit x.json --lane second   # 第二位讀者
```

## 🚨 第二位讀者（`--lane second`）

⚠️ **另一個模型讀同一頁**，寫進另一道。**🚫 那一道永遠不會進入正式清冊**
——✅ 它存在的理由是**比對**，🚫 不是補產量。
🚨 一批半數由 A 讀、半數由 B 讀的清冊，看起來和一批乾淨的一模一樣。

## 🚨 為什麼需要這一支

`append_drafts` 是「整份讀回 → 改 → 整份寫回」。**⚠️ 一個視窗跑沒事；
🚨 兩個視窗同時跑，後寫的那份會把先寫的整個蓋掉，而且不出任何錯**——
蓋掉之後的檔案結構完全正常，只是少了一頁。

> **✅ 故交回走 `write_page_drafts`：一頁一個檔，兩個視窗寫的是不同檔案。**
> 🚫 沒有任何共用的東西被改，故不必排隊、不必鎖。

## ⚠️ 這一支不做的事

- 🚫 **不讀論文**：它只把該讀的東西印出來，讀的是這個視窗裡的會話本身。
- 🚫 **不判範圍**：清冊要據實登錄「論文報告了什麼」，含範圍外的；
  🚨 判定是 `extract_run.py` 那一端的確定性層在做。
- 🚫 **不呼叫任何模型、不需要金鑰**（ADR-0009 裁定①）。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.extraction import worksheet  # noqa: E402

OUT_DIR = ROOT / 'extraction-worksheet'


def _pages():
    sheet = json.loads((OUT_DIR / 'worksheet.json').read_text(encoding='utf-8'))
    loaded = worksheet.load_drafts(OUT_DIR, require_complete=False)
    done = set(loaded['drafts'])
    out = []
    for number in range(1, sheet['pageCount'] + 1):
        items = [it for it in sheet['items'] if it['page'] == number]
        reports = {it['report'] for it in items}
        out.append({
            'page': number,
            'papers': len(items),
            'chars': sum(it['payloadChars'] for it in items),
            'read': len(reports & done),
        })
    return sheet, out


def _status():
    sheet, pages = _pages()
    print('=== 萃取工作單｜%d 篇／%d 頁 ===' % (sheet['itemCount'],
                                              sheet['pageCount']))
    print()
    print('  頁  篇數     字元   狀態')
    free = []
    for p in pages:
        if p['read'] == p['papers']:
            state = '✅ 已讀'
        elif p['read']:
            state = '🚧 讀了 %d／%d' % (p['read'], p['papers'])
        else:
            state = '⬜ 未讀'
            free.append(p['page'])
        print('  %2d   %3d  %7d   %s' % (p['page'], p['papers'], p['chars'],
                                         state))
    print()
    if free:
        print('⬜ **還沒人讀的頁：%s**' % ', '.join(str(n) for n in free))
        print('   ✅ 一個視窗認一頁，🚫 不必排隊——逐頁一檔，彼此不會蓋到。')
    else:
        print('✅ **每一頁都有清冊了。** 接著跑 `python .scratch/extract_run.py --run`。')
    return 0


def _show(number):
    page = worksheet.page(OUT_DIR, number)
    print(json.dumps(page, ensure_ascii=False, indent=2))
    return 0


def _submit(number, path, lane):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    entries = payload['entries'] if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        print('🚨 交回的檔案要嘛是清冊陣列，要嘛是含 entries 的物件',
              file=sys.stderr)
        return 2
    read_by = (payload.get('readBy') if isinstance(payload, dict) else None) \
        or {'agentClass': 'model'}
    result = worksheet.write_page_drafts(OUT_DIR, number, entries,
                                         read_by=read_by, lane=lane)
    print('✅ 第 %d 頁已交回（lane=%s）：%d 筆%s'
          % (number, lane, result['written'],
             '（%s）' % result['reason'] if result.get('reason') else ''))
    if lane != worksheet.PRIMARY_LANE:
        print('   🚫 這一道**不會**進入正式清冊——⚠️ 它是拿來比對的。')
        print('   ✅ 比對：`python .scratch/extract_agreement.py`')
        return 0
    print('   接著任一個視窗跑 `python .scratch/extract_run.py --run` 都可以，')
    print('   ⚠️ 它只會把**已經有清冊**的那些跑進鏈裡。')
    return 0


def main(argv):
    if not (OUT_DIR / 'worksheet.json').exists():
        print('🚨 找不到工作單：%s' % OUT_DIR, file=sys.stderr)
        print('   ⚠️ 請先跑 .scratch/extract_worksheet.py --write', file=sys.stderr)
        return 2
    args = argv[1:]
    if not args:
        return _status()
    try:
        number = int(args[0])
    except ValueError:
        print('🚨 第一個參數要是頁碼', file=sys.stderr)
        return 2
    lane = (args[args.index('--lane') + 1] if '--lane' in args
            else worksheet.PRIMARY_LANE)
    if '--submit' in args:
        return _submit(number, args[args.index('--submit') + 1], lane)
    return _show(number)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
