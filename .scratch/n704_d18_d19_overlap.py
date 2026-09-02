# -*- coding: utf-8 -*-
"""**`D18` 與 `D19` 是兩批論文，還是同一批的兩種說法。**（第 704 輪）

## ✅ 這是第 703 輪那 28 對候選裡最強的一對

`D18`（那 18 篇「判定可得卻未取」要不要補取）與
`D19`（卡在 `unpaywall=blocked` 那批要不要用現有信箱重問）
**共用 18 篇論文，🚨 而兩邊的條目都沒提到對方。**

## 🚨 而重點不是「有沒有關係」，是**它們會不會是同一批**

- `D18` 的集合：第 624 輪的 `obtainableNeverTaken`（**18 篇**）
- `D19` 的集合：指紋為 `unpaywall=blocked` 者（第 624 輪數到 **144 篇**，成因是缺聯絡信箱）

> **⚠️ 若那 18 篇**同時也**卡在 blocked，那兩件事就不是兩批論文，
> 🚨 而是同一批的兩種說法——分開裁會送兩次請求、或算兩次工。**

## ✅ 而本支先證明自己讀得對

🚨 用同一套讀法把 144 重算一次——⚠️ 對不上就代表本支讀錯了 attempts。

## 🚫 本支不送任何請求（只讀本機 manifest）、不改任何清冊
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n704_d18_d19_overlap.json'
N624 = HERE / 'n624_corpus_denominator.json'


def manifests():
    """候選代號（末 16 碼）→ manifest 內容。"""
    out = {}
    for path in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        candidate = str(doc.get('candidateId') or '')
        if candidate:
            out.setdefault(candidate[-16:], doc)
    return out


def blocked_by_missing_email(doc):
    """這一筆有沒有卡在 unpaywall=blocked。🚫 只讀本機紀錄。

    🚨 第一版猜鍵名猜錯了（用 `source`／`status`），重算得到 0；
    ⚠️ 而 manifest 實際用的是 `sourceId`／`conclusion`。
    **✅ 那是本支的驗算控制探針擋下來的**——🚫 不是本室自己看出來的。
    """
    for attempt in doc.get('attempts') or []:
        if str(attempt.get('sourceId')) == 'unpaywall' \
                and str(attempt.get('conclusion')) == 'blocked':
            return True
    return False


def main():
    n624 = json.loads(N624.read_text(encoding='utf-8'))
    never_taken = list(n624['obtainableNeverTaken'])
    stored_blocked = n624['singleBlocker']['count']

    docs = manifests()
    # 🚨 第二版仍差 2 筆（142 vs 144）——⚠️ 因為 `manifests()` **先去重再判斷**，
    # 而同一個候選可能有兩個 manifest 檔（第 624 輪的舊命名目錄），
    # 「先到先贏」時可能挑到沒被擋的那一份。
    # ✅ 改成**先判斷再取聯集**：只要有任何一份紀錄被擋，就算被擋。
    # **🚨 這一步同樣是驗算探針逼出來的。**
    blocked = set()
    for path in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            one = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        candidate = str(one.get('candidateId') or '')
        if candidate and blocked_by_missing_email(one):
            blocked.add(candidate[-16:])

    found = [c for c in never_taken if c in docs]
    missing = [c for c in never_taken if c not in docs]
    overlap = sorted(c for c in found if c in blocked)
    only_d18 = sorted(c for c in found if c not in blocked)

    statuses = collections.Counter(
        str(docs[c].get('status')) for c in found)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('那 18 篇的 manifest 都找得到（必觸發之正對照）',
          not missing and len(found) == len(never_taken),
          '🚨 D18 名單 %d 篇、找到 %d 篇、找不到的：%s；'
          '⚠️ 找不到的話重疊算不準'
          % (len(never_taken), len(found), missing or '無'))
    # 🚨 這一道證明本支讀 attempts 的方式與第 624 輪一致。
    probe('用同一套讀法重算 `unpaywall=blocked`，數字對得上（必觸發之正對照）',
          len(blocked) == stored_blocked,
          '🚨 本支重算 %d 筆｜第 624 輪存的 %d 筆；'
          '⚠️ 對不上就代表本支讀錯了 attempts，'
          '**🚫 那麼下面的重疊也不能信**'
          % (len(blocked), stored_blocked))
    probe('捏造的候選代號不在任何集合裡（必觸發之反向）',
          'ffffffffffffffff' not in blocked and 'ffffffffffffffff' not in docs,
          '🚨 捏造代號查無；⚠️ 若查得到，代表集合是亂湊的')
    # 🚨 這一道是答案。
    probe('`D18` 那 18 篇與 `D19` 那批**互不重疊**',
          not overlap,
          '🚨 同時落在兩邊的 %d／%d 篇；只屬 D18 的 %d 篇；'
          '⚠️ 有重疊就代表**兩件事在講同一批論文的不同面向**——'
          '**🚨 分開裁會送兩次請求、或把同一批工算兩次**'
          % (len(overlap), len(found), len(only_d18)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd18-d19-overlap',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'why': ('✅ 第 703 輪那 28 對候選裡最強的一對——'
                '⚠️ 共用 18 篇，而兩邊條目都沒提對方。'),
        'd18Set': {'name': 'obtainableNeverTaken', 'size': len(never_taken)},
        'd19Set': {'name': 'unpaywall=blocked（缺聯絡信箱）',
                   'sizeRecomputed': len(blocked),
                   'sizeStoredInN624': stored_blocked},
        'overlap': overlap,
        'onlyD18': only_d18,
        'statusOfD18Set': dict(statuses.most_common()),
        'reading': (
            '🚨 重疊 %d／%d 篇。'
            '⚠️ 重疊處代表**同一篇論文同時是「判定可得卻未取」與'
            '「卡在缺信箱」**——✅ 那不是兩件事，是同一件事的兩種說法。'
            % (len(overlap), len(found))),
        'whatThisIsNot': (
            '🚫 本支不主張補取得到——⚠️ 第 624 輪已寫明「那 18 篇實際取不取得到，'
            '要真的去抓才知道」，🚨 而本室**不送請求**。'
            '✅ 本支只回答「這兩個決定講的是不是同一批論文」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n704 D18 與 D19 的重疊 ===')
    print('   D18 名單 %d 篇（manifest 都找得到：%s）'
          % (len(never_taken), not missing))
    print('   D19 集合（unpaywall=blocked）：重算 %d 筆｜n624 存的 %d 筆'
          % (len(blocked), stored_blocked))
    print('   🚨 同時落在兩邊：%d 篇' % len(overlap))
    print('   只屬 D18：%d 篇' % len(only_d18))
    print('   D18 那批的 status 分佈：%s' % dict(statuses.most_common()))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
