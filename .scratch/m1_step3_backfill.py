# -*- coding: utf-8 -*-
"""M1 第 ③ 步：依契約 `ineligibleReplacement` 執行同池遞補。

## 🚨 遞補序位之定義（n+103 四.1：「取下一個隨機序位，不得另抽一次」）

**已實測驗證可照字面實作**：對六池皆確認
`random.Random(seed).sample(pool, quota)` 之結果集合
**等於** `random.Random(seed).sample(pool, len(pool))` 之前 `quota` 個。

**故遞補序列即同一種子之完整排列**：
- 序位 `0 .. quota-1` ＝ 原抽樣（不動）
- 序位 `quota` 起依序為遞補候選

**⚠️ 這不是「另抽一次」，是同一個排列往下讀**——**🚨 且協調者可用相同兩行重算。**
產物逐筆載明 `drawIndex`（該遞補者在排列中的序位）。

## 「可得」之定義

**採 n+103 之定義：`acquired`／`available-pdf`／`available-landing-page` 三者皆算可得**
——**⚠️ 我以其表格數字反推並逐池核對，六池全部相符**（S1=5、S2=4、S3=1、S4=6、S5+S6=4、S7=1）。
🚨 即「OA 版本存在且已定位」即為可得，**不以是否已下載成 JATS 為準**。

## 🚫 不做的事（n+103 四.3）

- **不跨池挪用配額**；
- **不放寬 strata 判準**；
- **不以非 OA 途徑悄悄補上而不標明**；
- **S2／S7 不執行湊數式處置**——其池內未抽者僅 2／1 筆，
  **即使全部可得也達不到配額，如實記載（填不滿是發現，不是失敗）。**

## 節流

沿用 `w4a1_run.py` 之 1.2 秒 `PacedTransport`，不放寬。
"""
import json
import os
import random
import sys
import time

os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.search.fulltext import (  # noqa: E402
    UrllibBinaryTransport, acquire_from_run_root)

sys.path.insert(0, '.scratch')
from m1_step3_acquire import PacedTransport, contact_email, masked  # noqa: E402

RUN = (os.environ['AHIG_PRIVATE_ROOT'] +
       '/search-runs/b11-exogenous-cho-endurance/b11-full-run')
DEST = '.scratch/m1_step3_backfill.json'
OBTAINABLE = {'acquired', 'available-pdf', 'available-landing-page'}


# ⚠️ 與 m1_step3_inventory.py 之 manifest_of 同邏輯，於此內嵌而非 import——
#    該檔是腳本不是模組，import 會把整份盤點重跑一遍。
#    🚨 兩處若日後分歧，以 inventory 為準（它是產出盤點產物者）。
FT = os.path.join(os.environ['AHIG_PRIVATE_ROOT'], 'fulltext')


def _dirs():
    out = {}
    for d in os.listdir(FT):
        out.setdefault(d.split('-')[0], []).append(d)
    return out


def manifest_of(cid, dirs):
    best = None
    for d in dirs.get(cid.split(':')[-1], []):
        p = os.path.join(FT, d, 'manifest.json')
        if not os.path.isfile(p):
            sub = os.path.join(FT, d, 'manifests')
            if not os.path.isdir(sub):
                continue
            fs = sorted(os.listdir(sub))
            if not fs:
                continue
            p = os.path.join(sub, fs[-1])
        try:
            m = json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if best is None or m.get('status') == 'acquired':
            best = m
    return best


def main():
    a = json.load(open('.scratch/m1_step2_assignment.json', encoding='utf-8'))
    cal = json.load(open('.scratch/m1_step2_calibration_set.json',
                         encoding='utf-8'))
    inv = json.load(open('.scratch/m1_step3_inventory.json', encoding='utf-8'))
    stat = {r['candidateId']: r['status'] for r in inv['records']}
    # ⚠️ 併入前一次遞補已查得之狀態，避免對同一批記錄重複發請求
    #    （n+48 一：對公共 OA API 之無謂請求是實質成本）。
    if os.path.isfile(DEST):
        prev = json.load(open(DEST, encoding='utf-8'))
        for pr in prev.get('pools', []):
            for b in pr.get('backfilled', []):
                stat.setdefault(b['candidateId'], b['status'])
        print('已載入前次遞補之 %d 筆狀態，不重複查詢'
              % sum(len(pr.get('backfilled', [])) for pr in prev.get('pools', [])))

    email, src = contact_email()
    if not email:
        print('🚨 未取得聯絡信箱，中止。')
        return 1
    print('聯絡信箱 %s（來源 %s）；節流 1.2 秒／請求' % (masked(email), src))
    print()

    transport = PacedTransport(UrllibBinaryTransport())
    pools_out, grand = [], {'quotaTotal': 0, 'obtainable': 0}

    for p in a['pools']:
        pid = p['poolId']
        d = cal['draws'][pid]
        quota, seed = d['quota'], d['seed']
        pool = sorted(p['candidateIds'])
        perm = random.Random(seed).sample(pool, len(pool))
        assert sorted(perm[:quota]) == sorted(d['candidateIds']), (
            '🚨 %s：排列前 %d 個與已凍結之抽樣不符，遞補序列無效' % (pid, quota))

        drawn = d['candidateIds']
        have = [c for c in drawn if stat.get(c) in OBTAINABLE]
        need = quota - len(have)
        reserve = perm[quota:]
        grand['quotaTotal'] += quota

        row = {'poolId': pid, 'quota': quota, 'seed': seed,
               'drawnObtainable': len(have), 'needed': need,
               'reserveSize': len(reserve), 'backfilled': [],
               'exhausted': False}

        if need <= 0:
            print('%-34s 配額已足（%d/%d），不遞補' % (pid, len(have), quota))
        elif not reserve:
            row['exhausted'] = True
            print('%-34s 缺 %d，🚨 池內已無未抽者——不湊數，如實記載'
                  % (pid, need))
        else:
            print('%-34s 缺 %d，自序位 %d 起依序遞補（備選 %d 筆）'
                  % (pid, need, quota, len(reserve)), flush=True)
            for offset, cid in enumerate(reserve):
                # 🚨 終止條件必須是「已接受數」，不是「已嘗試數」。
                # ⚠️ 本檔第一版寫的是 len(row['backfilled']) >= need——
                #    backfilled 含不可得者，於是「試滿 need 次」就停，
                #    而不是「補滿 need 個」才停。
                # 🚨 後果是低估最終可得數，而該數字正要用來判斷 M1 是否可達
                #    ——低估會讓我們拿一個假的缺口去驚動擁有者。
                if sum(1 for b in row['backfilled'] if b['accepted']) >= need:
                    break
                idx = quota + offset
                st = stat.get(cid)
                if st is None:                     # 尚未查詢 → 查
                    acquire_from_run_root(
                        __import__('pathlib').Path(RUN), [cid],
                        transport=transport, contact_email=email)
                    m = manifest_of(cid, _dirs())
                    st = (m or {}).get('status') or 'no-manifest'
                ok = st in OBTAINABLE
                row['backfilled'].append(
                    {'candidateId': cid, 'drawIndex': idx, 'status': st,
                     'accepted': ok,
                     'reasonCode': None if ok else st})
                print('   序位 %3d  %s  %s'
                      % (idx, cid.split(':')[-1], st + (' ✅' if ok else ' ✗')),
                      flush=True)
            accepted = [b for b in row['backfilled'] if b['accepted']]
            row['acceptedCount'] = len(accepted)
            if len(accepted) < need:
                row['exhausted'] = True
        row['finalObtainable'] = len(have) + len(
            [b for b in row['backfilled'] if b['accepted']])
        row['shortfall'] = max(quota - row['finalObtainable'], 0)
        grand['obtainable'] += row['finalObtainable']
        pools_out.append(row)

    print()
    print('%-34s %6s %10s %10s' % ('池', '配額', '最終可得', '缺口'))
    print('-' * 66)
    for r in pools_out:
        print('%-34s %6d %10d %10d' % (r['poolId'], r['quota'],
                                       r['finalObtainable'], r['shortfall']))
    print('-' * 66)
    print('%-34s %6d %10d %10d'
          % ('合計', grand['quotaTotal'], grand['obtainable'],
             grand['quotaTotal'] - grand['obtainable']))

    doc = {
        'schemaVersion': 1,
        'documentType': 'm1-step3-backfill',
        'ruling': 'n+103(4); ineligibleReplacement per strata.json',
        'obtainableDefinition': sorted(OBTAINABLE),
        'obtainableDefinitionNote': (
            "Matches n+103's per-pool figures exactly across all six pools "
            "(S1=5, S2=4, S3=1, S4=6, S5+S6=4, S7=1); derived by reconciling "
            'against that table rather than assumed.'),
        'replacementRule': (
            'Same seed, same permutation: indices 0..quota-1 are the frozen '
            'draw, quota onward are replacements in order. Verified per pool '
            'that sample(pool, quota) equals the first quota of '
            'sample(pool, len(pool)). Not a re-draw.'),
        'calibrationSetHash': cal['calibrationSetHash'],
        'pools': pools_out,
        'totals': {'quota': grand['quotaTotal'],
                   'obtainable': grand['obtainable'],
                   'shortfall': grand['quotaTotal'] - grand['obtainable']},
        'requests': transport.calls,
        'contentNote': 'Opaque ids, statuses and draw indices only.',
    }
    doc['backfillHash'] = content_hash(doc['pools'])
    open(DEST, 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1))
    print()
    print('請求 %d 次；✅ 已落盤 → %s' % (transport.calls, DEST))
    return 0


if __name__ == '__main__':
    sys.exit(main())
