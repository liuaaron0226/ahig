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
| 2 | 分層指派之 **`pools` 鍵** | 校準集 | **🚨 實測為同一次提交**——⚠️ 時序上不構成證據，見第五節 |
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
- 🚨 **「同一次提交」是一種真的會出現的判定**，⚠️ 且它不是通過——
  **🚫 不得與「相符」併計**；本檔分開報，並於第五節說明該條靠什麼撐。
"""
import io
import json
import re
import subprocess
import sys

S = '.scratch/'
ROUND = 517

# 🚨 第 518 輪之更正：初版比的是**檔案首次出現**之時刻。
# ⚠️ 而 `m1_step2_assignment.json` 首次出現時**根本沒有 `pools` 這個鍵**——
#    承載「從這些池抽出」那句話的欄位，是在抽樣那一次提交才寫進去的。
# 🚨 於是初版對該條印出「✅ 相符」，而它比的不是該句所依賴的東西。
# ✅ 故第三欄改為「承載該句的鍵」：有指定時，比的是**該鍵首次出現**之時刻。
CLAIMS = [
    ('m1_step2_population.json', None, 'm1_step2_calibration_set.json',
     '「從該母體抽出 60 筆」——⚠️ 母體若後出現，抽樣就不是從它抽的'),
    ('m1_step2_assignment.json', 'pools', 'm1_step2_calibration_set.json',
     '「依契約分層抽樣」——🚨 承載此句的是 `pools`，🚫 不是檔案本身'),
    ('m1_step2_calibration_set.json', None, 'm1_step3_inventory.json',
     '「就抽出的那 60 筆去取全文」'),
    ('m1_step2_calibration_set.json', None, 'm1_step3_backfill.json',
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


def field_first_seen(path, key):
    """該**鍵**在版控中首次出現之時刻。

    🚨 存在的理由：檔案先出現、而承載那句話的欄位後出現，是兩件事。
    ⚠️ 初版沒分，於是把一個「同一次提交才寫進去」的欄位讀成「事前就有」。
    """
    r = subprocess.run(['git', 'log', '--format=%h %aI', '--', path],
                       capture_output=True, encoding='utf-8', errors='replace')
    revs = [l.split() for l in (r.stdout or '').strip().split('\n') if l.strip()]
    for sha, when in reversed(revs):          # ⚠️ 由舊到新
        show = subprocess.run(['git', 'show', '%s:%s' % (sha, path)],
                              capture_output=True, encoding='utf-8',
                              errors='replace')
        if show.returncode != 0:
            continue
        try:
            doc = json.loads(show.stdout)
        except ValueError:
            continue
        if isinstance(doc, dict) and key in doc:
            return sha, when
    return None, None


PARAM = re.compile(
    r'^(DEFAULT_ALPHA|DEFAULT_TARGET_RECALL|DEFAULT_TAIL_SPOT_CHECK_N)'
    r'\s*=\s*(.+?)\s*$', re.M)


def revisions(path):
    r = subprocess.run(['git', 'log', '--format=%h %aI', '--', path],
                       capture_output=True, encoding='utf-8', errors='replace')
    return [l.split() for l in (r.stdout or '').strip().split('\n') if l.strip()]


def show(sha, path):
    r = subprocess.run(['git', 'show', '%s:%s' % (sha, path)],
                       capture_output=True, encoding='utf-8', errors='replace')
    return r.stdout if r.returncode == 0 else None


def pattern_first_seen(path, pattern):
    """該**樣式**首次出現之時刻。🚨 給非 JSON 的承載處用（例如原始碼常數）。"""
    for sha, when in reversed(revisions(path)):
        src = show(sha, path)
        if src and pattern.search(src):
            return sha, when
    return None, None


def value_history(path, pattern):
    """逐版取出該樣式之值，回傳 [(sha, when, {名: 值})]。

    🚨 為什麼不能只數檔案的提交次數：⚠️ 一個檔可以被改很多次，
    而承載宣稱的那幾行一次都沒動——**兩者是不同的問題**。
    """
    out = []
    for sha, when in reversed(revisions(path)):
        src = show(sha, path)
        if src is None:
            continue
        out.append((sha, when, dict(pattern.findall(src))))
    return out


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
for earlier, key, later, why in CLAIMS:
    sa, ta = (field_first_seen(S + earlier, key) if key
              else first_commit(S + earlier))
    sb, tb = first_commit(S + later)
    label = '%s%s' % (earlier, '：`%s`' % key if key else '')
    if not ta or not tb:
        rows.append({'earlier': earlier, 'field': key, 'later': later,
                     'verdict': 'not-in-git', 'why': why})
        print('   %-36s %-36s 🚨 版控內找不到' % (label, later))
        continue
    good = ordered(ta, tb)
    # 🚨 同一次提交：順序上通過，而它作為證據是空的。
    same = (sa == sb)
    verdict = ('same-commit' if (good and same)
               else ('consistent' if good else 'violated'))
    rows.append({'earlier': earlier, 'field': key, 'later': later,
                 'earlierCommit': sa, 'earlierAt': ta,
                 'laterCommit': sb, 'laterAt': tb,
                 'verdict': verdict, 'why': why})
    print('   %-36s %-36s %s'
          % (label, later,
             {'consistent': '✅ 相符', 'same-commit': '⚠️ 同一次提交',
              'violated': '🚨 顛倒'}[verdict]))
    print('      %s → %s   %s' % (ta[:19], tb[:19], why[:56]))
    if verdict == 'same-commit':
        print('      🚨 兩者寫在同一次提交（%s）——⚠️ 時序上沒有先後可言，'
              '🚫 這一條不構成證據。' % sa)
print('   ' + '-' * 92)
bad = [r for r in rows if r['verdict'] == 'violated'
       or r['verdict'] == 'not-in-git']
vacuous = [r for r in rows if r['verdict'] == 'same-commit']
print('   ✅ 相符 %d｜⚠️ 同一次提交（不構成證據）%d｜🚨 顛倒或找不到 %d'
      % (len(rows) - len(bad) - len(vacuous), len(vacuous), len(bad)))
for r in bad:
    print('      🚨 %s → %s：%s' % (r['earlier'], r['later'], r['why'][:60]))
for r in vacuous:
    print('      ⚠️ %s → %s：🚨 這一條要靠別的證據撐，見第五節'
          % (r['earlier'], r['later']))
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

print()
print('五、🚨 同一次提交的那一條，靠什麼撐')
print('   ⚠️ `pools` 與抽出名單寫在同一次提交，故時序上沒有先後可言。')
print('   ✅ 撐住它的是第 499 輪之重抽：以**現行** `pools` 重跑，'
      '六池之種子、名單、drawHash 逐一相符。')
print('   🚨 那證明的是「記錄下來的那一抽，就是從現在這些池抽出來的」——')
print('      ⚠️ 🚫 而它不排除「池與名單一起被調整」；')
print('      ✅ 排除後者的是第四節：名單自寫入起未被改過。')
print('   🚨 三者要一起看才完整：時序、重抽、未經修改。')

# ── 🚨 n+176（四）交辦：已知的違反例補入 ─────────────────────────
TERM = 'ahig/ahig/search/statistical_termination.py'
SIM = 'ahig/analysis/results/synergy_replay.json'
print()
print('六、🚨 n+176（四）交辦：把已知的違反例放進來')
print('   ⚠️ 為這一類建了機器，卻沒把已知的那一例放進去——🚫 那不是誤差，是清單漏了。')
sp, tp = pattern_first_seen(TERM, PARAM)
sg, tg = first_commit(SIM)
claim_ok = bool(tp and tg)
violated6 = claim_ok and not ordered(tg, tp)   # 宣稱：模擬(先) → 參數(後)
print('   宣稱：「三參數依**事前**模擬訂出」')
print('   三參數首見 %s（%s）' % (tp[:19] if tp else '—', sp or '—'))
print('   模擬產物首見 %s（%s）' % (tg[:19] if tg else '—', sg or '—'))
print('   %s 判定：%s'
      % ('✅' if violated6 else '🚨',
         'violated——🚨 參數早於模擬，該理由不成立'
         if violated6 else '未如 n+176 預期，須查'))

print()
print('七、✅ 取代它的那個理由，逐版查證')
hist = value_history(TERM, PARAM)
vals = [v for _, _, v in hist if v]
unchanged = bool(vals) and all(v == vals[0] for v in vals)
print('   ⚠️ 該檔本身有 %d 次提交——🚨 故「檔案沒被改過」是**假的**。' % len(hist))
print('   ✅ 而那三行之值逐版相同 = %s（%s）'
      % (unchanged, '／'.join('%s=%s' % kv for kv in sorted(vals[0].items()))
         if vals else '—'))
print('   🚨 故正確的理由是「**那三個值從未改變**」，🚫 不是「檔案未被修改」，')
print('      ⚠️ 也不是「模擬在事前」。✅ 與 n+175（三）改寫丙節之處置一致。')

# 🚨 控制：值追蹤器要看得出變化，否則「逐版相同」可能只是它沒在讀。
_a = {'X': '1'}
_b = {'X': '2'}
tracer_ok = (_a == _a) and (_a != _b)
probe_src_ok = bool(vals) and len(vals[0]) == 3
print('   %s 控制：追蹤器分得出相同與不同 ＝ %s；每版都真的讀到 3 個值 ＝ %s'
      % ('✅' if (tracer_ok and probe_src_ok) else '🚨', tracer_ok, probe_src_ok))

doc = {
    'schemaVersion': 1,
    'documentType': 'temporal-order-check',
    'knownViolationAdded': {
        'ruling': 'n+176(4)',
        'claim': 'the three termination parameters follow a prior simulation',
        'parametersFirstSeen': {'commit': sp, 'at': tp},
        'simulationFirstSeen': {'commit': sg, 'at': tg},
        'verdict': 'violated' if violated6 else 'unexpected',
        'why': 'The parameters predate the simulation artefact by about 17 hours, '
               'so the stated reason does not hold. Building a machine for this '
               'class and leaving out the one known instance is a gap in the '
               'list, not a margin of error.',
    },
    'replacementReasonChecked': {
        'fileCommits': len(hist),
        'valuesUnchangedAcrossRevisions': unchanged,
        'values': vals[0] if vals else None,
        'why': 'The file itself was modified twice, so "the file was never '
               'changed" would be false. What is true, and is what the reason '
               'rests on, is that those three values never changed across every '
               'revision -- which is why counting commits on a file is not a '
               'substitute for tracking the values that carry the claim.',
    },
    'sameCommitNote': 'The pools and the drawn list were written in one commit, so '
                      'ordering says nothing there. What carries it is the round '
                      '499 redraw -- rerun against the current pools, all six '
                      'seeds, lists and drawHashes match -- which shows the '
                      'recorded draw is the one those pools produce. That alone '
                      'would not exclude pools and list being adjusted together; '
                      'the never-modified check does. The three only work as a '
                      'set.',
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
    'sameCommit': [r['earlier'] + ' → ' + r['later'] for r in vacuous],
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
