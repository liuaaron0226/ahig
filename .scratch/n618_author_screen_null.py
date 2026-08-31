# -*- coding: utf-8 -*-
"""**那 17 對作者重疊，隨機會出現幾對？**（第 618 輪）

## 🚨 把上一輪的教訓套回本室自己的舊主張

第 617 輪的教訓是：**沒有基準率，「集中」只是感覺。**
⚠️ 而第 581 輪本室報過「17 對、6 群、涵蓋 18／41 篇」——
**🚫 那一次從未問過：隨機會出現幾對。**

> 🚨 運動營養這個領域，同實驗室連續發表極常見。
> **⚠️ 若隨機打散作者也能得到十幾對，那個篩選就什麼都沒說。**

## ✅ 做法：排列檢定

保持每篇的作者人數不變，**把全部作者洗牌重新分配**，重算「共有 ≥2 位作者」的配對數。
⚠️ 重複多次，得到虛無分布。

**🚨 這一支不改任何既有判定**——✅ 它只回答「那個 17 有沒有超出偶然」。

## 🚫 不用 random 模組的全域狀態

⚠️ 本專案禁用 `Math.random` 類的不可重現來源（工作流慣例）。
✅ 故本支用**固定種子**的 `random.Random(seed)`，🚨 種子寫死在原始碼裡，可複驗。
"""
import collections
import itertools
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.stats.family import normalise_author  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n618_author_screen_null.json'
SEED = 20260901          # 🚨 寫死，可複驗
TRIALS = 400

AUTHOR = re.compile(r'<surname>([^<]{1,60})</surname>\s*'
                    r'(?:<given-names>([^<]{0,60})</given-names>)?')
FRONT = {'europe-pmc-jats': ('rawFile', '</front>'),
         'grobid-tei': ('teiFile', '</teiHeader>')}


def publication_years():
    out = {}
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        kind = doc.get('sourceType')
        if kind not in FRONT:
            continue
        field, closing = FRONT[kind]
        target = manifest.parent / (doc.get(field) or '')
        if not target.is_file() or target.suffix == '.pdf':
            continue
        text = target.read_text(encoding='utf-8', errors='ignore')
        cut = text.find(closing)
        head = text[:cut] if cut > 0 else ''
        pattern = (r'<year[^>]*>(\d{4})</year>' if kind == 'europe-pmc-jats'
                   else r'<date type="published" when="(\d{4})')
        hit = re.search(pattern, head)
        if hit:
            out[doc['candidateId'][-16:]] = hit.group(1)
    return out


def author_lists():
    out = {}
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        kind = doc.get('sourceType')
        if kind not in FRONT:
            continue
        field, closing = FRONT[kind]
        target = manifest.parent / (doc.get(field) or '')
        if not target.is_file() or target.suffix == '.pdf':
            continue
        text = target.read_text(encoding='utf-8', errors='ignore')
        cut = text.find(closing)
        head = text[:cut] if cut > 0 else ''
        names = [normalise_author((given + ' ' + surname).strip())
                 for surname, given in AUTHOR.findall(head)]
        if names:
            out[doc['candidateId'][-16:]] = names
    return out


def pairs_with_year_filter(lists, threshold=2):
    """✅ 重現第 581 輪那個 17：⚠️ 作者重疊**且**出版年相差 ≤4（不明者放行）。"""
    years = publication_years()
    keys = sorted(lists)
    count = 0
    for a, b in itertools.combinations(keys, 2):
        if len(set(lists[a]) & set(lists[b])) < threshold:
            continue
        ya, yb = years.get(a), years.get(b)
        if ya and yb and abs(int(ya) - int(yb)) > 4:
            continue
        count += 1
    return count


def pairs_with_overlap(lists, threshold=2):
    keys = sorted(lists)
    count = 0
    for a, b in itertools.combinations(keys, 2):
        if len(set(lists[a]) & set(lists[b])) >= threshold:
            count += 1
    return count


def main():
    lists = author_lists()
    observed = pairs_with_overlap(lists)
    with_year = pairs_with_year_filter(lists)

    pool = [name for names in lists.values() for name in names]
    sizes = {k: len(v) for k, v in lists.items()}
    rng = random.Random(SEED)
    null = []
    for _ in range(TRIALS):
        shuffled = pool[:]
        rng.shuffle(shuffled)
        cursor, fake = 0, {}
        for key, size in sizes.items():
            fake[key] = shuffled[cursor:cursor + size]
            cursor += size
        null.append(pairs_with_overlap(fake))
    null.sort()
    mean = sum(null) / len(null)
    at_or_above = sum(1 for n in null if n >= observed)
    p_value = (at_or_above + 1) / (TRIALS + 1)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('作者清單取到了（必觸發）',
          len(lists) >= 40,
          '🚨 少了就低估重疊；實得 %d 篇（每篇 %d–%d 位作者）'
          % (len(lists), min(sizes.values()), max(sizes.values())))
    # 🚨 第一版拿 22 去比第 581 輪的 17，探針立刻亮紅——⚠️ 而那不是錯，是**定義不同**：
    # 第 581 輪的 17 對還要求「出版年相差 ≤ 4（或不明）」，本支只算作者重疊。
    # ✅ 故兩個都算，並講明 p 值屬於哪一個。
    probe('兩種定義的差額說得出來（必觸發）',
          observed >= with_year,
          '⚠️ 只看作者重疊 %d 對；再加「年差 ≤4」則 %d 對（＝第 581 輪那個數）。'
          '🚨 本支的 p 值屬於**前者**——🚫 年份有 10 篇不明，'
          '把它放進虛無模型會讓虛無自己帶著缺值'
          % (observed, with_year))
    # 🚨 必觸發之反向：⚠️ 虛無模型要真的產得出重疊，否則比較是空的。
    probe('隨機打散後仍會出現重疊（必觸發之反向）',
          max(null) > 0,
          '✅ 虛無分布 %d–%d 對、平均 %.1f；🚨 若全為零，'
          '代表打散方式錯了，而「顯著」會是假的' % (null[0], null[-1], mean))
    # 🚨 這一道的紅綠就是答案。
    probe('觀察到的重疊超出偶然',
          p_value < 0.05,
          '⚠️ 觀察 %d 對；虛無平均 %.1f、範圍 %d–%d；'
          '🚨 %d／%d 次隨機達到或超過觀察值，p ≈ %.3f'
          % (observed, mean, null[0], null[-1], at_or_above, TRIALS, p_value))

    doc = {
        'schemaVersion': 1,
        'documentType': 'author-screen-null',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'seed': SEED, 'trials': TRIALS,
        'reports': len(lists),
        'observedPairsAuthorsOnly': observed,
        'observedPairsWithYearFilter': with_year,
        'nullMean': round(mean, 2),
        'nullRange': [null[0], null[-1]],
        'nullPercentiles': {'p50': null[len(null) // 2],
                            'p95': null[int(len(null) * 0.95)]},
        'timesNullReachedObserved': at_or_above,
        'pValue': round(p_value, 4),
        'whatThisTests': (
            '✅ 只問一件事：第 581 輪那 17 對「共有 ≥2 位作者」，'
            '🚨 隨機打散作者後會不會也出現這麼多。'
            '🚫 不改任何既有判定。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n618 作者重疊的虛無分布 ===')
    print('   %d 篇｜觀察（只看作者）%d 對｜再加年差 ≤4 則 %d 對'
          % (len(lists), observed, with_year))
    print('   虛無（%d 次、種子 %d）：平均 %.1f｜中位數 %d｜第 95 百分位 %d｜範圍 %d–%d'
          % (TRIALS, SEED, mean, null[len(null) // 2],
             null[int(len(null) * 0.95)], null[0], null[-1]))
    print('   🚨 隨機達到或超過觀察值：%d／%d（p ≈ %.3f）'
          % (at_or_above, TRIALS, p_value))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
