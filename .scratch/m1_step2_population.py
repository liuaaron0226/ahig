# -*- coding: utf-8 -*-
"""M1 第 ② 步（其零）：算出最終判讀狀態並落盤，供校準集抽樣使用。

🚨 為什麼第 ② 步的第一件事不是抽樣：**硬碟上沒有最終名單。**
`judgements.json` 是 append-only 且不改寫，最終狀態須套用三份 overlay 才得出，
**而套用順序會改變答案**。故先把母體算出來、把每一層的增減攤開，再談抽樣
——與 n+97（三）「先建清單，再核對」同一個道理。

## 套用順序（不是我決定的，是各檔自己寫的）

1. `post-ruling-reclassification.json`（121 筆）
   > 「decisions 層與 ADR-0008 終止檢定之 labels 序列一律以本檔之 effectiveDecision 為準。
   >   未列於本檔之 candidateId 沿用 judgements.json 之 opinion。」
2. `post-ruling-abstract-rescreen.json`（5 筆）
   > 「Second overlay layer, **applied AFTER** post-ruling-reclassification.json.
   >   Only ratchet-allowed transitions are representable:
   >   exclude/unclear→advance 與 exclude→unclear」
3. `post-ruling-deferred-tags.json`（28 筆）
   > 「Holding tags only. These records **keep their original judgement (unclear)**」
   > `affectsTerminationStatistic: False`
   **⚠️ 即第三份不改判讀，只掛標籤——套用它不會動到任何 opinion。**

## 🚨 每一層都驗證它自己宣稱的規則，不盲目套用

- 第 1 層：`originalOpinion` 必須與 `judgements.json` 之 opinion 相符
  ——**不符即表示 overlay 是對另一個版本的判讀寫的**，當場擋下。
- 第 2 層：轉換必須落在棘輪允許集合內
  ——**⚠️ 棘輪的意義是「只准往證據更充分的方向動」，若出現反向轉換，
  該檔就不是它自稱的那種檔案。**
- 第 3 層：其 opinion 必須全為 unclear，且**套用後 opinion 分布須零變動**。

⚠️ 輸出只有 id 與判讀狀態，零文獻內容。
"""
import io
import json
import os
import sys
from collections import Counter

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT + '/standard-full-screen-pass-1'
DEST = '.scratch/m1_step2_population.json'


def load(name):
    return json.load(io.open(os.path.join(OUT, name), encoding='utf-8'))


judged = load('judgements.json')['entries']
base = {e['candidateId']: e['opinion'] for e in judged}
print('基底 judgements.json                %5d 筆' % len(base))
print('  分布 %s' % dict(Counter(base.values())))
print()

report = {'layers': []}
cur = dict(base)

# ── 第 1 層 ──────────────────────────────────────────────────────────
L1 = load('post-ruling-reclassification.json')
mismatch, changes = [], Counter()
for e in L1['entries']:
    cid, orig, eff = e['candidateId'], e['originalOpinion'], e['effectiveDecision']
    if cid not in cur:
        mismatch.append((cid[-8:], 'not-in-judgements', orig))
        continue
    if cur[cid] != orig:
        mismatch.append((cid[-8:], cur[cid], orig))
        continue
    if cur[cid] != eff:
        changes['%s->%s' % (orig, eff)] += 1
    cur[cid] = eff
assert not mismatch, (
    '🚨 第 1 層之 originalOpinion 與 judgements 不符 %d 筆——'
    'overlay 可能是對另一版判讀寫的，在查明前不得套用：%s'
    % (len(mismatch), mismatch[:5]))
print('第 1 層 reclassification  entries %3d  實際改動 %3d'
      % (len(L1['entries']), sum(changes.values())))
for k, v in sorted(changes.items()):
    print('    %-22s %3d' % (k, v))
report['layers'].append({'file': 'post-ruling-reclassification.json',
                         'entries': len(L1['entries']),
                         'changed': sum(changes.values()),
                         'transitions': dict(changes)})
print('  分布 %s' % dict(Counter(cur.values())))
print()

# ── 第 2 層（棘輪）───────────────────────────────────────────────────
RATCHET = {('exclude', 'advance'), ('unclear', 'advance'), ('exclude', 'unclear')}
L2 = load('post-ruling-abstract-rescreen.json')
bad, ch2 = [], Counter()
for e in L2['entries']:
    cid, orig, eff = e['candidateId'], e['originalOpinion'], e['effectiveDecision']
    if orig != eff and (orig, eff) not in RATCHET:
        bad.append((cid[-8:], orig, eff))
        continue
    if cur.get(cid) != eff:
        ch2['%s->%s' % (cur.get(cid), eff)] += 1
    cur[cid] = eff
assert not bad, (
    '🚨 第 2 層出現棘輪不允許之轉換 %s——'
    '該檔自稱 one-way ratchet，出現反向轉換即表示它不是它自稱的那種檔案' % bad)
print('第 2 層 abstract-rescreen entries %3d  實際改動 %3d（棘輪規則已驗證）'
      % (len(L2['entries']), sum(ch2.values())))
for k, v in sorted(ch2.items()):
    print('    %-22s %3d' % (k, v))
report['layers'].append({'file': 'post-ruling-abstract-rescreen.json',
                         'entries': len(L2['entries']),
                         'changed': sum(ch2.values()),
                         'transitions': dict(ch2)})
print('  分布 %s' % dict(Counter(cur.values())))
print()

# ── 第 3 層（只掛標籤，不改判讀）──────────────────────────────────────
before = Counter(cur.values())
L3 = load('post-ruling-deferred-tags.json')
not_unclear = [e['candidateId'][-8:] for e in L3['entries']
               if e.get('opinion') != 'unclear']
assert not not_unclear, (
    '🚨 第 3 層自稱「這些記錄維持原判讀 unclear」，惟有非 unclear 者：%s'
    % not_unclear)
tags = {e['candidateId']: e.get('holdingTag') for e in L3['entries']}
after = Counter(cur.values())
assert before == after, '🚨 第 3 層不應改動任何 opinion，實測有變動'
print('第 3 層 deferred-tags     entries %3d  實際改動 %3d（僅掛標籤，已驗證零變動）'
      % (len(L3['entries']), 0))
report['layers'].append({'file': 'post-ruling-deferred-tags.json',
                         'entries': len(L3['entries']), 'changed': 0,
                         'note': 'holding tags only; opinions unchanged (verified)'})
print()

final = Counter(cur.values())
print('=' * 60)
print('最終判讀狀態')
print('=' * 60)
for k in ('advance', 'unclear', 'exclude'):
    print('  %-10s %5d' % (k, final.get(k, 0)))
print('  %-10s %5d' % ('合計', sum(final.values())))

doc = {
    'schemaVersion': 1,
    'documentType': 'm1-step2-screening-population',
    'purpose': ('Final judgement state after applying all three overlays, '
                'filed so the calibration-set draw has a checkable population. '
                'Per ADR-0010 M1 step 2.'),
    'derivation': report,
    'applicationOrder': [l['file'] for l in report['layers']],
    'counts': dict(final),
    'contentNote': 'Opaque candidateIds and decisions only. No literature content.',
    'decisions': {cid: op for cid, op in sorted(cur.items())},
    'holdingTags': {cid: t for cid, t in sorted(tags.items())},
}
doc['populationHash'] = content_hash(doc['decisions'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
print('   populationHash %s' % doc['populationHash'])
