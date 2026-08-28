# -*- coding: utf-8 -*-
"""n+115（七.1）索取：`notScreenedCount` 更正值 5,115 之產生指令。

## 🚨 為什麼需要這支腳本

`n82_anchor_source_errata.json` 之「補正三」載明 5,115 的**定義**，
**⚠️ 但定義不是產生指令**——協調者不能據此重算，也就不能覆核。
n+115（七.1）明訂：**未取得產生指令前，該更正值不得寫入報告。**

## 定義（照抄勘誤原文，不重述）

> 全 queue 15,425 扣除**六個判讀來源之聯集去重**（標準線 pass-1、safety pass-1／2、
> 影子 pass A／B、critical-harms-sweep、同 orphans）。

**⚠️ 上句列了七個目錄名而稱「六個來源」**——🚨 本檔不替它決定哪兩個算一個，
而是**逐目錄列出各自筆數與聯集**，讓「六」或「七」之爭以數字呈現而非以措辭呈現。

## 🚨 錯值 5,357 不是手打錯，這點必須併陳

生產程式 `evaluate_termination()` 依其輸入算出：
`poolSize 15425 − screenedCount 7431 − outOfSequenceCount 2637 = 5357`。
**⚠️ 錯的是餵進去的 `screenedCount`（未計入影子批次之判讀），不是算式。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：各來源之判讀 candidateId 集合、其聯集、與 queue 之差。
- 🚨 查不到：**該定義本身是否為「已篩」之正確定義**——⚠️ 那是判準問題不是計算問題。
  本檔只證明「依此定義算出的數是 5,115」，🚫 不宣稱該定義必然正確。
- ⚠️ 來源在私有根，**協調者不可及**；交付時此數須標明
  **「執行室量測、協調者未獨立覆核」**（n+115 七.3 之要求同樣適用於本項）。
"""
import io
import json
import os
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash, file_hash  # noqa: E402

RUN = (os.environ.get('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private') +
       '/search-runs/b11-exogenous-cho-endurance/b11-full-run')

SOURCES = [
    'standard-full-screen-pass-1',
    'safety-full-screen-pass-1',
    'safety-full-screen-pass-2',
    'screening-shadow-pass-a',
    'screening-shadow-pass-b',
    'critical-harms-sweep',
    'critical-harms-sweep-orphans',
]


def judged_ids(directory):
    """該來源之判讀 candidateId 集合。

    ⚠️ 不預設 judgements.json 的頂層形狀——🚨 本 run 已多次因猜格式而得到假結論。
    """
    p = os.path.join(RUN, directory, 'judgements.json')
    if not os.path.isfile(p):
        return None, 'no-judgements-file'
    doc = json.load(io.open(p, encoding='utf-8'))
    if isinstance(doc, list):
        entries, shape = doc, 'list'
    elif isinstance(doc, dict) and isinstance(doc.get('entries'), list):
        entries, shape = doc['entries'], 'dict.entries'
    else:
        raise SystemExit('🚨 %s 之 judgements.json 形狀不在已知兩種之內：%s'
                         % (directory, list(doc)[:8]))
    ids = {e['candidateId'] for e in entries if e.get('candidateId')}
    return ids, '%s／%d 筆' % (shape, len(entries))


queue = json.load(io.open(RUN + '/screening-queue/queue.json', encoding='utf-8'))
queue_ids = {r['candidateId'] for r in queue}

print('=== 各判讀來源（🚨 逐目錄列出，不替「六或七」下定論）===')
print('%-34s %8s %8s %s' % ('來源目錄', '判讀數', '在queue內', '檔案形狀'))
print('-' * 74)
union = set()
per = {}
for d in SOURCES:
    ids, shape = judged_ids(d)
    if ids is None:
        print('%-34s %8s %8s %s' % (d, '—', '—', shape))
        continue
    inq = ids & queue_ids
    per[d] = {'judged': len(ids), 'inQueue': len(inq), 'shape': shape}
    union |= inq
    print('%-34s %8d %8d %s' % (d, len(ids), len(inq), shape))
print('-' * 74)
print('%-34s %8s %8d' % ('聯集去重（∈ queue）', '', len(union)))

not_screened = len(queue_ids) - len(union)
print()
print('queue 總數        %d' % len(queue_ids))
print('已篩聯集          %d' % len(union))
print('notScreenedCount  %d' % not_screened)
print('勘誤所載正值      5115   %s'
      % ('✅ 相符' if not_screened == 5115 else '🚨 不符——🚫 該值不得寫入報告'))

doc = {
    'schemaVersion': 1,
    'documentType': 'not-screened-count-derivation',
    'ruling': 'n+115(7.1): produce the command behind the corrected 5,115',
    'population': 'screening-queue/queue.json of run b11-full-run',
    'countingUnit': 'candidate (publication)',
    'criterion': ('queue size minus the deduplicated union of candidateIds '
                  'judged in the seven listed source directories, counting only '
                  'ids that are themselves in the queue'),
    'queueSize': len(queue_ids),
    'perSource': per,
    'unionSize': len(union),
    'notScreenedCount': not_screened,
    'errataValue': 5115,
    'matches': not_screened == 5115,
    'sixOrSevenNote': ('The errata says "six sources" but names seven '
                       'directories. This file does not decide which two are '
                       'one; it lists each separately so the question is '
                       'settled by numbers rather than by wording.'),
    'wrongValueNote': ('5,357 was not a typo. evaluate_termination() computed '
                       'poolSize 15425 - screenedCount 7431 - '
                       'outOfSequenceCount 2637 from its inputs. The input '
                       'screenedCount omitted the shadow passes; the formula '
                       'was right.'),
    'verificationNote': ('Sources live in the private root and the coordinator '
                         'cannot reach them. Per n+115(7.3) this figure must be '
                         'delivered marked as measured by the executor and not '
                         'independently checked.'),
    'queueFileHash': file_hash(open(RUN + '/screening-queue/queue.json',
                                    'rb').read()),
    'contentNote': 'Counts and directory names only. No literature content.',
}
doc['derivationHash'] = content_hash(doc['perSource'])
io.open('.scratch/n440_not_screened.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → .scratch/n440_not_screened.json')
sys.exit(0 if not_screened == 5115 else 1)
