# -*- coding: utf-8 -*-
"""取得層之時序：**「先抽樣，再取得」這句話，紀錄支不支持。**

## 🚨 起因：兩輪之內兩次「結論對而理由假」，而兩次都是翻紀錄才發現的

n+174（甲節）與 n+175（丙節）連續抓到同一型：**方向沒錯，理由是假的。**
n+175 三自陳：**「🚨 而兩次都是翻紀錄才發現的——沒有任何機器在看理由。」**

**⚠️ 一般化的「查核理由」做不出來**（理由是散文）。
**✅ 但其中有一類是可查的：宣稱兩件事有先後關係，而兩者都在版控裡。**
🚨 丙節那一次正是如此——「參數依事前模擬訂出」被提交時刻推翻。

**✅ 故本檔把取得層依賴的那幾條先後關係做成檢查。**

## 🚨 本層依賴的先後關係（🚫 逐條寫明，不藏在程式裡）

| # | 必須先 | 必須後 | 🚨 若顛倒，什麼句子會失去依據 |
|---|---|---|---|
| 1 | 判讀母體 `m1_step2_population.json` | 校準集 `m1_step2_calibration_set.json` | **「從該母體抽出 60 筆」**——⚠️ 母體若後出現，抽樣就不是從它抽的 |
| 2 | 分層指派 `m1_step2_assignment.json` | 校準集 | **「依契約分層抽樣」**——⚠️ 池若後出現，配額無所依 |
| 3 | 校準集 | 取得盤點 `m1_step3_inventory.json` | **「就抽出的那 60 筆去取全文」** |
| 4 | 校準集 | 遞補 `m1_step3_backfill.json` | **「不可得者以同層遞補」**——🚨 遞補是替代品，🚫 不能早於被替代者 |

## ✅ 併驗一條更硬的（第四節）

**⚠️ 先後順序只排除「順序不對」，🚨 排除不了「先抽、看了結果、再回頭改」。**
**✅ 故另驗一條**：抽樣結果之檔案自寫入起**有沒有被改過**。
**🚨 那一條排除的是動機，🚫 不只是時間**——⚠️ 正是丙節最後改用的那種理由。

## 🚨 這道檢查證得了什麼、證不了什麼——**兩邊都要講**

**⚠️ 提交時刻不是產生時刻。** 一份檔可以先寫好、很久以後才提交。

> **✅ 故違反是硬證據**：若遞補早於校準集，「遞補」那句話就站不住。
> **🚫 而通過只是「與所述一致」，不是「證明如此」。**

**🚨 這正是丙節那一課的另一半**：⚠️ 協調者查出模擬產物晚了 17 小時，
**而真正撐住那一節的理由改成了「那三行寫進去之後從未被修改」**——
**✅ 一個「沒有被改過」比一個「先後順序」硬，因為它排除的是動機，不只是時間。**

## 🚨 控制探針

**⚠️ 一個比不出先後的比較器，會把每一條都判成通過。**
**✅ 故以合成時刻各驗一次順序與逆序，🚨 兩者都要如預期。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：版控內首次出現之時刻，及其是否符合上表。
- 🚨 查不到：**檔案真正產生的時刻**——⚠️ 見上，通過只是一致，不是證明。
- 🚨 亦查不到：**內容是否真的取自它所宣稱的來源**——
  ⚠️ 那由 `n499` 之重抽與 `n496` 之對帳各管一段，**🚫 本檔只管時序。**
"""
import io
import json
import subprocess
import sys

S = '.scratch/'
ROUND = 517

CLAIMS = [
    ('m1_step2_population.json', 'm1_step2_calibration_set.json',
     '「從該母體抽出 60 筆」——⚠️ 母體若後出現，抽樣就不是從它抽的'),
    ('m1_step2_assignment.json', 'm1_step2_calibration_set.json',
     '「依契約分層抽樣」——⚠️ 池若後出現，配額無所依'),
    ('m1_step2_calibration_set.json', 'm1_step3_inventory.json',
     '「就抽出的那 60 筆去取全文」'),
    ('m1_step2_calibration_set.json', 'm1_step3_backfill.json',
     '🚨 遞補是替代品，🚫 不能早於被替代者'),
]


def first_commit(path):
    """該檔在版控中**首次出現**之時刻（🚫 不是最後一次改動）。"""
    r = subprocess.run(
        ['git', 'log', '--diff-filter=A', '--format=%h %aI', '--', path],
        capture_output=True, encoding='utf-8', errors='replace')
    lines = [l for l in (r.stdout or '').strip().split('\n') if l.strip()]
    if not lines:
        return None, None
    sha, when = lines[-1].split()
    return sha, when


def ordered(a, b):
    """a 是否不晚於 b。🚨 相等視為通過（同一次提交）。"""
    return a <= b


print('=== 取得層之時序檢查（🚫 唯讀）===')
print()
print('一、控制探針——🚨 比不出先後的比較器會把每條都判成通過')
probes = [('2026-01-01T00:00:00+08:00', '2026-01-02T00:00:00+08:00', True),
          ('2026-01-02T00:00:00+08:00', '2026-01-01T00:00:00+08:00', False),
          ('2026-01-01T00:00:00+08:00', '2026-01-01T00:00:00+08:00', True)]
ok = True
for a, b, want in probes:
    got = ordered(a, b)
    good = got == want
    ok = ok and good
    print('   %s %s ≤ %s → %s（期待 %s）'
          % ('✅' if good else '🚨', a[:10], b[:10], got, want))
if not ok:
    sys.exit('🚨 控制探針未過——🚫 不報時序結果。')
print('   ✅ 三道皆如預期：順、逆、同時都分得出來。')
print()

print('二、逐條')
print('   %-36s %-36s %s' % ('必須先', '必須後', '判定'))
print('   ' + '-' * 92)
rows = []
for earlier, later, why in CLAIMS:
    sa, ta = first_commit(S + earlier)
    sb, tb = first_commit(S + later)
    if not ta or not tb:
        rows.append({'earlier': earlier, 'later': later, 'verdict': 'not-in-git',
                     'why': why})
        print('   %-36s %-36s 🚨 版控內找不到' % (earlier, later))
        continue
    good = ordered(ta, tb)
    rows.append({'earlier': earlier, 'later': later,
                 'earlierCommit': sa, 'earlierAt': ta,
                 'laterCommit': sb, 'laterAt': tb,
                 'verdict': 'consistent' if good else 'violated', 'why': why})
    print('   %-36s %-36s %s' % (earlier, later,
                                 '✅ 相符' if good else '🚨 顛倒'))
    print('      %s → %s   %s' % (ta[:19], tb[:19], why[:56]))
print('   ' + '-' * 92)
bad = [r for r in rows if r['verdict'] != 'consistent']
print('   %s %d／%d 條與所述一致'
      % ('✅' if not bad else '🚨', len(rows) - len(bad), len(rows)))
for r in bad:
    print('      🚨 %s → %s：%s' % (r['earlier'], r['later'], r['why'][:60]))
print()
print('三、🚨 這道檢查證得了什麼')
print('   ✅ 違反是硬證據：順序顛倒，那句話就站不住。')
print('   🚫 通過只是「與所述一致」，🚨 不是「證明如此」——')
print('      ⚠️ 提交時刻不是產生時刻，一份檔可以先寫好、很久以後才提交。')
print('   ⚠️ 丙節那一課的另一半：協調者最後改用「那三行寫進去之後從未被修改」，')
print('      🚨 而那比先後順序硬——它排除的是動機，不只是時間。')

# ── 更硬的一種：寫進去之後有沒有被改過 ──────────────────────────
def commit_count(path):
    r = subprocess.run(['git', 'log', '--format=%h', '--', path],
                       capture_output=True, encoding='utf-8', errors='replace')
    return len([l for l in (r.stdout or '').strip().split('\n') if l.strip()])


print()
print('四、🚨 更硬的一種：抽樣結果寫下之後，有沒有被改過')
print('   ⚠️ 上面那四條只排除「順序不對」；🚨 排除不了「先抽、看了結果、再回頭改」。')
FROZEN = 'm1_step2_calibration_set.json'
n_commits = commit_count(S + FROZEN)
# 🚨 控制：偵測器要分得出「只有一次提交」與「改過很多次」。
# ⚠️ 拿一個確定被改過很多次的檔當對照；若兩者都回 1，這道檢查沒在數。
BUSY = 'n496_corpus_verify.py'
n_busy = commit_count(S + BUSY)
ctl_ok = n_busy > 1
print('   %s 控制：`%s` 提交 %d 次（須 >1，否則本節沒在數）'
      % ('✅' if ctl_ok else '🚨', BUSY, n_busy))
frozen_ok = ctl_ok and n_commits == 1
if not ctl_ok:
    print('   🚫 控制未過——不報本節結果。')
else:
    print('   %s `%s` 自寫入起共 %d 次提交'
          % ('✅' if frozen_ok else '⚠️', FROZEN, n_commits))
    if frozen_ok:
        print('   🚨 即：抽出的那 60 筆與其種子，**寫下之後從未被改過**。')
        print('      ⚠️ 故它不可能是「先取得、看了哪些拿得到、再回頭調整」的產物——')
        print('      ✅ 這一條排除的是動機，🚫 不只是時間，比第二節硬。')
    else:
        print('   ⚠️ 曾被改動 %d 次——🚨 須逐次看改了什麼，🚫 不得逕稱未經調整。'
              % (n_commits - 1))

doc = {
    'schemaVersion': 1,
    'documentType': 'temporal-order-check',
    'neverModified': {'file': FROZEN, 'commits': n_commits,
                      'controlFile': BUSY, 'controlCommits': n_busy,
                      'controlPassed': ctl_ok, 'unmodified': frozen_ok,
                      'why': 'The ordering checks rule out a wrong sequence. They '
                             'do not rule out drawing, seeing which records turned '
                             'out obtainable, and going back to adjust. One commit '
                             'and no later modification does rule that out, which '
                             'is why it is the stronger claim -- it excludes the '
                             'motive rather than only the timing.'},
    'ruling': 'generalises n+174 and n+175: twice in two rounds the conclusion '
              'was right and the stated reason was false, and both were caught '
              'only by reading the record. Reasons in general cannot be checked; '
              'claimed orderings between version-controlled files can.',
    'population': 'the four before/after relations the acquisition layer relies on',
    'countingUnit': 'claimed ordering',
    'criterion': 'first appearance in version control, earlier file must not be '
                 'later than the one that depends on it',
    'controlProbes': [{'a': a, 'b': b, 'expected': w, 'got': ordered(a, b)}
                      for a, b, w in probes],
    'claims': rows,
    'consistent': len(rows) - len(bad),
    'violated': [r['earlier'] + ' → ' + r['later'] for r in bad],
    'whatAPassMeans': 'Consistent with what is claimed, not proof of it: commit '
                      'time is not authoring time. A violation is hard evidence; '
                      'a pass is not.',
    'strongerFormAvailable': 'The coordinator ended up resting section C on "those '
                             'three lines were never modified after they were '
                             'written", which is harder than an ordering: it rules '
                             'out the motive, not merely the timing. Where such a '
                             'form exists it should be preferred.',
    'coverageStatement': 'Timing only. Whether the content really came from the '
                         'source it names is checked elsewhere -- the redraw for '
                         'the sample, the byte reconciliation for the corpus.',
    'contentNote': 'File names, commit hashes and timestamps only.',
}
io.open(S + 'n517_temporal_order_check.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn517_temporal_order_check.json' % S)
sys.exit(1 if (bad or not ctl_ok) else 0)
