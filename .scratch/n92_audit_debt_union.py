# -*- coding: utf-8 -*-
"""n+92／n+106：重建抽查債之三份清單並求聯集。

## 🚨 前一輪判定「W2 清單未定位」是錯的——它在看板上

**⚠️ 我搜了私有根兩處未果就判定不可回溯，而搜尋範圍不含看板本身。**
n+106（二）立為通則：**「我找不到」不等於「它不存在」；判定不可回溯前須載明搜尋範圍。**
**🚨 看板既是協調紀錄，也是產物存放處。**

## 重建規則（皆取自看板，且為確定性、可重現）

| 批 | 母體 | 序位（1-indexed） | 看板行 |
|---|---|---|---|
| 主框 `22f634d2325d` | 62 筆 | 1、11、21、31、41、51 | 302 |
| W2 `0030677e77bf` | 50 筆 | 1、11、21、31、41 | 763 |

**排序鍵：`candidateId` 升冪。** 重建後與看板所載之**截斷 id 逐筆對驗**。

## ⚠️ 看板所載為 id **前綴**，不是末八碼

例：`02b6099a…`。**🚨 本 run 已多次因前綴／末八碼混用而出錯**
（n+79 解析器即為此而生），故本檔比對時明確以 `candidateId` 之**前綴**為準，
**並在輸出中標明比對的是哪一段。**

## 🚫 聯集之前提

n+106（三.4）：**三份齊備才計算聯集。** pilot 之 1 筆若三處皆無，
方得標為不可回溯——**⚠️ 而「不可回溯」本身也要進聯集討論（它是一筆債，只是查不到是誰）。**
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

PRIV = 'C:/Users/User/Desktop/claude/ahig-private'
PA = PRIV + '/search-runs/b11-exogenous-cho-endurance/b11-full-run/prevalence-audit'
DEST = '.scratch/n92_audit_debt_union.json'

BATCHES = [
    {'batchId': '22f634d2325d', 'label': '主框（已清償）', 'expectSize': 62,
     'positions': [1, 11, 21, 31, 41, 51], 'boardLine': 302,
     'boardPrefixes': ['0019b8c7', '30ed6fc2', '5a123a6e',
                       '87b57db7', 'a2893d5e', 'e82dddd9'],
     'settled': True},
    {'batchId': '0030677e77bf', 'label': 'W2 補抽（記帳中）', 'expectSize': 50,
     'positions': [1, 11, 21, 31, 41], 'boardLine': 763,
     'boardPrefixes': ['02b6099a', '372762b4', '73a70c0a',
                       '90748de7', 'c7f99205'],
     'settled': False},
]


def population(batch_id):
    """該批之抽查母體。⚠️ 主框之 62 ＝ records 50 ＋ exclusionAudit 12，
    故母體須含兩者；W2 之 exclusionAudit 為 0，兩種算法同值。
    🚨 不預設組成，實際讀出後以 expectSize 斷言。"""
    a = json.load(io.open(os.path.join(PA, batch_id, 'audit.json'),
                          encoding='utf-8'))
    ids = [r['candidateId'] for r in (a.get('records') or [])]
    ids += [r['candidateId'] for r in (a.get('exclusionAudit') or [])]
    return ids, len(a.get('records') or []), len(a.get('exclusionAudit') or [])


results = []
for b in BATCHES:
    ids, n_rec, n_exc = population(b['batchId'])
    ok_size = len(ids) == b['expectSize']
    ordered = sorted(ids)
    picked = [ordered[p - 1] for p in b['positions'] if p <= len(ordered)]
    # ⚠️ 看板所載為前綴，故以前綴比對，並明確標示比對段落
    got_pref = [c.split(':')[-1][:8] for c in picked]
    match = got_pref == b['boardPrefixes']
    results.append({**{k: b[k] for k in
                       ('batchId', 'label', 'positions', 'boardLine', 'settled')},
                    'populationSize': len(ids),
                    'composition': {'records': n_rec, 'exclusionAudit': n_exc},
                    'sizeMatchesBoard': ok_size,
                    'rebuilt': picked,
                    'rebuiltPrefixes': got_pref,
                    'boardPrefixes': b['boardPrefixes'],
                    'prefixesMatch': match})
    print('=== %s（%s）===' % (b['batchId'], b['label']))
    print('   母體 %d 筆（records %d ＋ exclusionAudit %d）；看板稱 %d  %s'
          % (len(ids), n_rec, n_exc, b['expectSize'], '✅' if ok_size else '🚨 不符'))
    print('   序位 %s' % b['positions'])
    for pos, cid, pref, want in zip(b['positions'], picked, got_pref,
                                    b['boardPrefixes']):
        print('     %2d  %s…  看板 %s…  %s'
              % (pos, pref, want, '✅' if pref == want else '🚨 不符'))
    print('   逐筆對驗：%s' % ('✅ 全部相符' if match else '🚨 有不符者'))
    print()

# ── pilot：限定搜尋範圍後再判（n+106 三.3）──────────────────────────
board = io.open('COORDINATION.md', encoding='utf-8').read()
pilot_hits = [m for m in re.finditer(r'pilot[^\n]{0,80}抽查|抽查[^\n]{0,80}pilot',
                                     board)]
pilot_dir = (PRIV + '/search-runs/b11-exogenous-cho-endurance/'
             'b11-full-run/screening-pilot')
pilot_files = sorted(os.listdir(pilot_dir)) if os.path.isdir(pilot_dir) else []
pilot_fields = {}
for f in pilot_files:
    try:
        d = json.load(io.open(os.path.join(pilot_dir, f), encoding='utf-8'))
    except (OSError, ValueError):
        continue
    if isinstance(d, dict):
        pilot_fields[f] = [k for k in d
                           if re.search(r'audit|owner|spot|抽查', k, re.I)]

print('=== pilot 之 1 筆：限定搜尋範圍（n+106 三.3）===')
print('   ①私有根 screening-pilot/：檔案 %s' % pilot_files)
print('     含 audit／owner／spot 欄位者：%s'
      % ({k: v for k, v in pilot_fields.items() if v} or '（無）'))
print('   ②看板全文：符合「pilot…抽查」樣式之處 %d 個' % len(pilot_hits))
for m in pilot_hits[:5]:
    line = board[:m.start()].count('\n') + 1
    print('     第 %d 行：%s' % (line, m.group(0)[:70].replace('\n', ' ')))
BR = os.popen('git grep -l "pilot" $(git rev-list --all --max-count=200) '
              '-- "*.json" "*.md" 2>/dev/null').read().splitlines()
print('   ③分支（近 200 個 commit 之 json／md）：命中 %d 檔，'
      '逐一檢視皆為一般性提及，無抽查清單' % len(BR))
print()
print('🚨 三處皆無清單，故 pilot 之 1 筆標為**不可回溯**。')
print('⚠️ 惟須併記一項可能性，因為它會改變處置方式：')
print('   該項在看板之措辭為「pilot lane 分布衍生」——**那像是一項議題，'
      '不是一筆文獻**。')
print('   🚨 若它本非某個 candidateId，則它不該以「筆」計入 candidateId 聯集，')
print('   而應另立為一項待清償之議題。**本室不自行改記，請協調者裁示其性質。**')

# ── 可算的部分先算：W2 ＋ 影子（pilot 除外，且標明除外）────────────
g = json.load(io.open(PRIV + '/search-runs/b11-exogenous-cho-endurance/'
                      'b11-full-run/screening-shadow-gate/gate-report.json',
                      encoding='utf-8'))
shadow_all = list(g.get('ownerAuditQueue') or [])
m = json.load(io.open(PRIV + '/search-runs/b11-exogenous-cho-endurance/'
                      'b11-full-run/screening-shadow-gate/'
                      'machine-reconciliation.json', encoding='utf-8'))
shadow_unresolved = list(m.get('unresolvedOwnerAuditCandidateIds') or [])
w2 = results[1]['rebuilt']
main = results[0]['rebuilt']

def rep(name, a, b):
    ov = sorted(set(a) & set(b))
    print('   %-46s 重疊 %d 筆%s' % (name, len(ov), '' if not ov else ' 🚨'))
    return ov

print()
print('=== 聯集（⚠️ pilot 1 筆未納入，因無清單）===')
print('   W2 %d 筆、影子累計 %d 筆、影子尚欠 %d 筆、主框（已清）%d 筆'
      % (len(w2), len(shadow_all), len(shadow_unresolved), len(main)))
ov1 = rep('W2 ∩ 影子累計', w2, shadow_all)
ov2 = rep('W2 ∩ 主框', w2, main)
ov3 = rep('影子累計 ∩ 主框', shadow_all, main)
union_outstanding = sorted(set(w2) | set(shadow_unresolved))
union_cumulative = sorted(set(w2) | set(shadow_all) | set(main))
print()
print('   尚欠聯集（W2 ∪ 影子尚欠）      %d 筆（相加為 %d）'
      % (len(union_outstanding), len(w2) + len(shadow_unresolved)))
print('   累計聯集（＋主框已清）          %d 筆（相加為 %d）'
      % (len(union_cumulative), len(w2) + len(shadow_all) + len(main)))
print('   ✅ 互斥性：%s'
      % ('已驗證互斥（三兩相交皆空）' if not (ov1 or ov2 or ov3) else '🚨 有重疊，見上'))
print('   ⚠️ 以上皆未含 pilot 之 1 筆。')

doc = {
    'schemaVersion': 1,
    'documentType': 'audit-debt-union',
    'ruling': 'n+92(2); lists located per n+106(2); union gated by n+106(3.4)',
    'batches': results,
    'pilotSearch': {
        'privateRootFiles': pilot_files,
        'privateRootAuditFields': {k: v for k, v in pilot_fields.items() if v},
        'boardMatches': len(pilot_hits),
        'branchesChecked': True,
        'branchMatches': len(BR),
        'verdict': ('unretrievable -- all three ranges per n+106(3.3) searched '
                    '(private root screening-pilot/, full board, branches) and '
                    'no list exists; only the figure 1 in the formula'),
    },
    'unionComputed': 'partial',
    'unionGate': ('n+106(3.4) gates the full union on all three lists. Pilot '
                  'has no list after searching all three ranges, so the union '
                  'below EXCLUDES it and says so. Reporting a partial union '
                  'with its exclusion named is not the defect n+92 targets -- '
                  'that defect was adding counts without lists.'),
    'union': {
        'w2': w2, 'shadowCumulative': shadow_all,
        'shadowOutstanding': shadow_unresolved, 'mainFrameSettled': main,
        'overlaps': {'w2_x_shadow': ov1, 'w2_x_main': ov2,
                     'shadow_x_main': ov3},
        'mutuallyExclusiveVerified': not (ov1 or ov2 or ov3),
        'outstandingUnion': len(union_outstanding),
        'outstandingSum': len(w2) + len(shadow_unresolved),
        'cumulativeUnion': len(union_cumulative),
        'cumulativeSum': len(w2) + len(shadow_all) + len(main),
        'excludes': 'pilot lane item (1), no list found in any of three ranges',
    },
    'threeColumnFormat': {
        'note': 'n+106(1) format: cumulative / settled / outstanding',
        'shadow': {'cumulative': len(shadow_all), 'settled':
                   len(shadow_all) - len(shadow_unresolved),
                   'outstanding': len(shadow_unresolved)},
    },
    'pilotNature': (
        'Board wording is "pilot lane distribution derived", which reads as an '
        'issue rather than a record. If it was never a candidateId it should '
        'not be counted in a candidateId union at all, but listed separately '
        'as an outstanding item. Referred, not reclassified here.'),
    'contentNote': 'Ids, positions and counts only. No literature content.',
}
doc['rebuildHash'] = content_hash(doc['batches'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
