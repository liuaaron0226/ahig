# -*- coding: utf-8 -*-
"""**兩位讀者對同一批論文各自登錄了什麼**——逐篇比。（第 488 輪）

## 🚨 為什麼需要第二位讀者

⚠️ 目前**沒有任何東西在看「讀出來的東西對不對」**。鏈上每一道守的都是
「形狀對不對、綁對了沒、有沒有挾帶判定」，**🚨 而一份形狀完全正確、
內容讀錯的清冊，會一路通過到底。**

> **✅ 系統性文獻回顧的標準作法就是兩人各自萃取再比對。**
> 🚨 而本專案至今只有一位讀者，⚠️ 這是目前**最大的品質缺口**。

## ⚠️ 這支量的是什麼，以及**不是**什麼

✅ 量的是：兩邊都登錄了、只有一邊登錄了的**標籤**（大小寫與空白不計，逐字比）。

**🚫 它不是正確率。** ⚠️ 兩位讀者把同一個結局叫成不同名字
（`fat-free mass` 對 `lean body mass`），**會被算成兩邊各有一個**。
**🚨 故「只有一邊有」是一份要人看的清單，🚫 不是錯誤數。**

🚫 不比出處、不比數值——⚠️ 那些要逐欄對，而逐欄對之前得先確定兩邊講的是
同一個結局，**🚨 那正是這一步還沒做到的事。**

## 用法

```
python .scratch/extract_agreement.py            # 與 lane=second 比
python .scratch/extract_agreement.py <lane 名>
```
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.extraction import worksheet  # noqa: E402

OUT_DIR = ROOT / 'extraction-worksheet'


def main(argv):
    lane = argv[1] if len(argv) > 1 else 'second'
    if not (OUT_DIR / 'worksheet.json').exists():
        print('🚨 找不到工作單：%s' % OUT_DIR, file=sys.stderr)
        return 2

    primary = worksheet.load_drafts(OUT_DIR, require_complete=False)['drafts']
    other = worksheet.load_lane(OUT_DIR, lane)['drafts']
    if not other:
        print('=== 兩位讀者之比對｜lane=%s ===' % lane)
        print('   ⬜ 第二位讀者還沒有交回任何一頁——🚫 沒有東西可比。')
        print('   ✅ 交回方式：`python .scratch/extract_page.py <頁> '
              '--submit x.json --lane %s`' % lane)
        return 0

    got = worksheet.agreement(primary, other)
    print('=== 兩位讀者之比對｜lane=%s ===' % lane)
    print()
    print('   兩邊都讀過 %d 篇（正式那道另有 %d 篇對方沒讀，'
          '對方另有 %d 篇正式那道還沒讀）'
          % (got['comparedReports'], len(got['primaryOnlyReports']),
             len(got['secondOnlyReports'])))
    print('   結局標籤：兩邊都有 %d｜只有正式那道有 %d｜只有對方有 %d'
          % (got['labelsBoth'], got['labelsOnlyPrimary'],
             got['labelsOnlySecond']))
    print()
    disputed = [r for r in got['rows'] if r['onlyPrimary'] or r['onlySecond']]
    if not disputed:
        print('   ✅ 兩邊逐字一致。')
    else:
        print('   ⚠️ **要人看一眼的 %d 篇**：' % len(disputed))
        for row in disputed:
            print('     · %s（兩邊都有 %d）' % (row['report'][-16:], row['both']))
            if row['onlyPrimary']:
                print('       只有正式那道有：%s' % '、'.join(row['onlyPrimary']))
            if row['onlySecond']:
                print('       只有對方有　　：%s' % '、'.join(row['onlySecond']))
    print()
    print('🚨 **%s**' % got['caveat'])
    print('⚠️ 且 lane=%s 的東西**從不進入正式清冊**——✅ 它只用來比對。' % lane)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
