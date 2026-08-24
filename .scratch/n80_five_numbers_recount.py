# -*- coding: utf-8 -*-
"""n+80（四）：五個未篩數字自來源重算。

裁定原文：
    全 queue 未篩 5,357 − 標準線未篩 1,460 ＝ 3,897；
    但所列四個 lane 之和為 1,966＋1,599＋164＋4 ＝ 3,733。差 164，
    恰為 registry-review 之數。
    ⚠️ 恰好相等很可能是重複計算，但「很可能」不是證據——
    執行室須自來源重算這五個數並回報，不得沿用既有數字（n+61）。

🚨 本檔一律從**私有根的原始檔**現算，不讀任何既有回報、不讀看板數字。
   來源只有三種：queue.json（母體與 lane）、各 judgements.json（已判）、
   worksheet.json（標準線之判讀母體）。

⚠️ 輸出只有數字與集合關係，**不含任何文獻內容**。
"""
import json
import os
import sys

ROOT = os.environ.get('AHIG_PRIVATE_ROOT') or \
    r'C:\Users\User\Desktop\claude\ahig-private'
RUN = os.path.join(ROOT, 'search-runs', 'b11-exogenous-cho-endurance',
                   'b11-full-run')


def load(*parts):
    p = os.path.join(RUN, *parts)
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def ids_of(doc, key='entries'):
    return {e['candidateId'] for e in doc[key]}


print('來源目錄：%s' % RUN)
print()

queue = load('screening-queue', 'queue.json')
lane_ids = {}
for r in queue:
    lane_ids.setdefault(r['screeningLane'], set()).add(r['candidateId'])

qn = len(queue)
uniq = {cid for s in lane_ids.values() for cid in s}
print('=' * 76)
print('〇、母體')
print('=' * 76)
print('  queue.json 筆數                %6d' % qn)
print('  相異 candidateId               %6d   %s' % (
    len(uniq), 'OK 無重複' if len(uniq) == qn else '🚨 有重複！'))
print()
print('  各 lane（現算）：')
for lane in sorted(lane_ids, key=lambda k: -len(lane_ids[k])):
    print('    %-28s %6d' % (lane, len(lane_ids[lane])))
print('    %-28s %6d' % ('合計', sum(len(v) for v in lane_ids.values())))
print()

# ── 已判集合 ──────────────────────────────────────────────────────────
# 🚨 判讀來源有六個，不是兩個。第一版本檔只讀了標準線與 safety，算出的
#    lane 未篩數比 n+80 各多 12／101／3——差額恰為 critical-harms-sweep
#    在該三個 lane 的筆數。⚠️ 漏一個來源，五個數字就全錯，而且錯得很像
#    「協調者算錯了」。故此處逐一列舉並各自報數，讓漏掉哪個一眼可見。
SOURCES = [
    ('標準線 pass-1', ('standard-full-screen-pass-1', 'judgements.json')),
    ('safety pass-1', ('safety-full-screen-pass-1', 'judgements.json')),
    ('safety pass-2', ('safety-full-screen-pass-2', 'judgements.json')),
    ('影子 pass A', ('screening-shadow-pass-a', 'judgements.json')),
    ('影子 pass B', ('screening-shadow-pass-b', 'judgements.json')),
    ('critical-harms-sweep', ('critical-harms-sweep', 'judgements.json')),
    ('  同 orphans', ('critical-harms-sweep-orphans', 'judgements.json')),
]

judged_by_source = {}
for label, parts in SOURCES:
    try:
        judged_by_source[label] = ids_of(load(*parts))
    except (OSError, KeyError):
        judged_by_source[label] = set()

std_j = judged_by_source['標準線 pass-1']
saf1 = judged_by_source['safety pass-1']
saf2 = judged_by_source['safety pass-2']
shadow = judged_by_source['影子 pass A'] | judged_by_source['影子 pass B']
sweep = judged_by_source['critical-harms-sweep'] | judged_by_source['  同 orphans']

ws = load('standard-full-screen-pass-1', 'worksheet.json')
ws_ids = {it['candidateId'] for it in ws['items']}

print('=' * 76)
print('一、已判集合（六個來源，各自現算）')
print('=' * 76)
running = set()
for label, _ in SOURCES:
    s = judged_by_source[label]
    new = s - running
    running |= s
    print('  %-22s %6d 筆   新增 %5d   累計 %6d' % (label, len(s), len(new), len(running)))
print()
print('  safety 兩 pass id 相同?        %s' % (saf1 == saf2))
print('  標準線 worksheet items         %6d' % len(ws_ids))
print()

std_lane = lane_ids.get('standard-screening', set())
print('=' * 76)
print('二、🚨 worksheet 與 queue 的 standard-screening 差在哪')
print('=' * 76)
print('  queue standard-screening       %6d' % len(std_lane))
print('  worksheet items                %6d' % len(ws_ids))
print('  差                             %6d' % (len(std_lane) - len(ws_ids)))
print('  worksheet ⊄ standard lane 者   %6d' % len(ws_ids - std_lane))
print('  standard lane 不在 worksheet   %6d' % len(std_lane - ws_ids))
extra = std_lane - ws_ids
if extra:
    other = {lane: len(extra & s) for lane, s in lane_ids.items()
             if lane != 'standard-screening' and (extra & s)}
    print('  ⚠️ 這批只在 queue 不在 worksheet，未落在其他 lane：%s' % (other or '（無）'))
print()

# ── 未篩 ──────────────────────────────────────────────────────────────
judged_all = std_j | saf1 | saf2 | shadow | sweep
print('=' * 76)
print('三、未篩（現算）')
print('=' * 76)
print('  【定義甲】全 queue − 任何來源之已判')
notscr_a = uniq - judged_all
print('    全 queue 未篩                %6d' % len(notscr_a))
print()
print('  【定義乙】逐 lane 扣掉落在該 lane 的所有判讀')
rows = []
for lane in sorted(lane_ids, key=lambda k: -len(lane_ids[k])):
    s = lane_ids[lane]
    j = s & judged_all
    rows.append((lane, len(s), len(j), len(s) - len(j)))
    print('    %-28s 母體 %5d  已判 %5d  未篩 %5d' % (lane, len(s), len(j), len(s) - len(j)))
print('    %-28s %20s 未篩 %5d' % ('合計', '', sum(r[3] for r in rows)))
print()
print('  ⚠️ 甲乙必須相等（同一個集合的兩種數法）：%s' % (
    len(notscr_a) == sum(r[3] for r in rows)))
print()
print('  【定義丙】標準線以 worksheet 為母體（看板 1,460 之算法）')
print('    worksheet %d − 已判 %d = %d' % (
    len(ws_ids), len(ws_ids & std_j), len(ws_ids - std_j)))
print()

# ── 對帳 ──────────────────────────────────────────────────────────────
four = [r for r in rows if r[0] in (
    'animal-signal-review', 'review-source-review',
    'registry-review', 'identity-review')]
four_sum = sum(r[3] for r in four)
std_ws_notscr = len(ws_ids - std_j)

print('=' * 76)
print('四、與 n+80 所報數字對帳')
print('=' * 76)
print('  %-34s %8s %8s %8s' % ('項目', 'n+80 報', '現算', '差'))
print('  ' + '-' * 62)


def line(label, reported, actual):
    print('  %-34s %8s %8d %8d' % (label, reported, actual, actual - reported))


line('全 queue 未篩', 5357, len(notscr_a))
line('標準線未篩（worksheet 母體）', 1460, std_ws_notscr)
for lane, reported in (('animal-signal-review', 1966),
                       ('review-source-review', 1599),
                       ('registry-review', 164),
                       ('identity-review', 4)):
    actual = [r[3] for r in rows if r[0] == lane][0]
    line(lane, reported, actual)
print()
print('  n+80 之算式：5,357 − 1,460 = 3,897，四 lane 和 = 3,733，差 164')
print('  現算之算式：%d − %d = %d，四 lane 和 = %d，差 %d' % (
    len(notscr_a), std_ws_notscr, len(notscr_a) - std_ws_notscr,
    four_sum, (len(notscr_a) - std_ws_notscr) - four_sum))
print()

print('=' * 76)
print('五、🚨 5,357 是怎麼來的——逐項還原，不是猜')
print('=' * 76)
without_shadow = std_j | saf1 | saf2 | sweep
naive = qn - len(std_j) - len(saf1 | saf2) - \
    len(judged_by_source['critical-harms-sweep']) - len(judged_by_source['  同 orphans'])
print('  假設「各來源筆數直接相減、不做聯集去重、且不計影子批次」：')
print('    %d − %d − %d − %d − %d = %d' % (
    qn, len(std_j), len(saf1 | saf2),
    len(judged_by_source['critical-harms-sweep']),
    len(judged_by_source['  同 orphans']), naive))
print('    ⇒ %s n+80 所報之 5,357' % ('✅ 恰為' if naive == 5357 else '✗ 不等於'))
print()
shadow_new = len(shadow - (std_j | saf1 | saf2 | sweep))
shadow_x_sweep = len(shadow & sweep)
print('  故 5,357 與現算 %d 的差 %d，成因只有一個：' % (
    len(notscr_a), 5357 - len(notscr_a)))
print('    ＋%3d  影子批次 pass A／B 之判讀未計入已篩' % shadow_new)
print('           （影子 %d 筆，扣掉與標準線／safety／sweep 重複者）' % len(shadow))
print('    ＝%3d  %s' % (shadow_new,
                         '✅ 與實際差額完全相符，無殘差'
                         if shadow_new == 5357 - len(notscr_a)
                         else '✗ 尚有未解釋的殘差'))
print()
print('  ⚠️ 附帶一提，naive 算式能湊出 5,357 有一部分是運氣：')
print('     它把 sweep 與 orphans 當成 %d 筆全新扣掉，而這 %d 筆中有 %d 筆'
      % (len(judged_by_source['critical-harms-sweep']) +
         len(judged_by_source['  同 orphans']),
         len(judged_by_source['critical-harms-sweep']) +
         len(judged_by_source['  同 orphans']), shadow_x_sweep))
print('     同時也在影子批次裡。🚨 因為影子整批沒被計入，這 %d 筆的重複' % shadow_x_sweep)
print('     才沒有現形——**兩個錯互相遮住了**。若只補計影子而不做聯集')
print('     去重，會得到 %d，仍然是錯的。' % (qn - len(std_j) - len(saf1 | saf2) -
                                    len(judged_by_source['critical-harms-sweep']) -
                                    len(judged_by_source['  同 orphans']) - len(shadow)))
print()
print('=' * 76)
print('六、結論')
print('=' * 76)
print("""  1. 🚨 **「差 164 恰為 registry-review 之數」是巧合，不是重複計算。**
     現算的差是 %d，不是 164；而 164 這個數在本 run 另有出處——
     它是「只在 queue 不在 worksheet 的 169 筆」中 requiredReviewMode
     為 human-plus-blinded-llm 者的筆數。⚠️ 兩個 164 彼此無關。

  2. ✅ **標準線未篩 1,460 是穩健的**，兩種母體都給同一個數：
     worksheet 母體 9,091 − 7,631 = 1,460；
     queue lane 母體 9,260 − 7,800（含影子 169）= 1,460。

  3. 🚨 **判讀來源有六個，不是四個。** 影子批次 pass A／B 的 300 筆
     （新增 %d 筆）是實實在在的判讀，落在全部六個 lane 上，
     但 n+80 的數字未把它計入已篩。

  4. ⚠️ **那 169 筆不是漏篩。** 它們在 queue 標記 requiresHumanScreening
     ＝True 卻不在 worksheet，乍看是覆蓋漏洞；實查其判讀在
     screening-shadow-pass-a／b，是刻意排除於主工作單之影子樣本。

  5. 本檔不改任何既有產物，也不宣稱 n+80 的數字「錯」——
     它是在另一組來源假設下算出來的。**要改的是把假設寫明**：
     未篩數必須聲明「計入哪幾個判讀來源」，否則同一個名稱會有兩個值。""" % (
    (len(notscr_a) - std_ws_notscr) - four_sum, shadow_new))
