# -*- coding: utf-8 -*-
"""n+151（一）派給執行室的那 17 格：**做成一道指令，而不是交付當日的一場手工重建。**

## 🚨 這支解決什麼

交付盤點第 1 項：**佔位符全數須於交付當日現算**，
**⚠️ 其中「不可及」者（權威來源在私有根，協調者開不了）須執行室代跑。**

**🚨 而那 17 格目前散在**：私有根三個名冊、八份 worksheet、`n60_tags.py` 之輸出、
manifest 目錄走訪、以及兩格「還不存在」的值。

> **⚠️ 交付當日若靠手工重建這 17 格，就是本 run 已經栽過很多次的那件事：
> 🚨 手算不會自己說它用了哪個母體。**

**✅ 本檔把它們變成一道指令。🚫 本檔不改任何報告、不填任何值。**

## 🚨 清單從哪裡來——**不是我手打的**

**⚠️ 手打一份 17 格的清單，下一次檢查表變動它就過期而不會有人發現。**
**✅ 故本檔以 `ast` 解析 `.scratch/n115_delivery_checklist.py` 之 `DETAIL` 字面，
取出 `kind == '不可及'` 者。🚫 不 import（import 會執行它）。**

**🚨 並印出實得格數與 n+151 所載之 17 相比**——⚠️ 不符即代表清單漂移了。

## 🚫 三條紀律

1. **🚫 不得把本輪之值寫進報告。** ⚠️ n+151 明訂逐格須為**交付當日**現算；
   **🚨 本檔今天跑出來的值只證明「這格產得出來」，不是那格的答案。**
2. **🚨 產不出來的格子一律寫明「產不出來」與確切阻礙**，
   **🚫 不得以近似值、舊值或看板值頂替。**
3. **⚠️ 每一格都要帶母體聲明**——🚨 本 run 之母體混用事故已達三次。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 產得到：能由私有根檔案或既有唯讀腳本直接數出來者。
- 🚨 產不到：**需要判讀者**（某筆是否「僅卡族群措辭」）、
  **需要裁定者**（該用哪個率去推導）、**尚不存在者**（萃取後才有）。
- ⚠️ 解析 `n60_tags.py` 之輸出屬**讀他人印出來的表**——
  **🚨 故每一項解析都配一個錨點；錨點找不到即報 `parse-failed`，🚫 不報數字。**
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.search.fulltext import _candidate_directory_name  # noqa: E402

S = '.scratch/'
PRIV = Path(os.environ['AHIG_PRIVATE_ROOT'])
FULL = PRIV / 'fulltext'
RUN = (PRIV / 'search-runs' / 'b11-exogenous-cho-endurance' / 'b11-full-run')
ARTIFACT_DIR = re.compile(r'-[0-9a-f]{16}$')
# 🚨 這個數是「上一次裁定點過的格數」，不是常數。
# ⚠️ n+151 點的是 17；n+152（一）新增 `RETRACT_IN_EVIDENCE` → 18。
# 🚨 不符時腳本會直接說「清單已漂移」——⚠️ 上一輪它就是這樣抓到新格的。
EXPECTED_CELLS = 18
EXPECTED_SOURCE = 'n+151 十七格 ＋ n+152（一）新增 RETRACT_IN_EVIDENCE'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


# ── 清單：由檢查表原始碼解析，🚫 不手打 ──────────────────────────
tree = ast.parse(io.open(S + 'n115_delivery_checklist.py', encoding='utf-8').read())
detail = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'DETAIL' for t in node.targets):
        detail = node.value
        break
if detail is None:
    sys.exit('🚨 在 n115_delivery_checklist.py 找不到 DETAIL——🚫 中止，不猜清單。')
# ⚠️ 🚫 不能用 literal_eval：說明欄由變數串接而成（`EV + "…"`），
# 🚨 而我只需要「鍵」與「型態」，兩者都是字面。取字面即可，
# ⚠️ 硬要求整個字面可求值，反而會讓這支因為說明欄的寫法而拒跑。
kinds = {}
for k, v in zip(detail.keys, detail.values):
    if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
        continue
    first = v.elts[0] if isinstance(v, ast.Tuple) and v.elts else None
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        kinds[k.value] = first.value
    else:
        kinds[k.value] = None      # 🚨 型態非字面——不歸入任何一類，且下方會列出
nonliteral = sorted(k for k, v in kinds.items() if v is None)
cells = sorted(k for k, v in kinds.items() if v == '不可及')

print('=== n+151（一）之「不可及」格：一道指令代替一場手工重建 ===')
print('   清單以 ast 解析檢查表 `DETAIL` 取得，🚫 非手打。')
print('   實得 %d 格；裁定所載 %d 格 %s'
      % (len(cells), EXPECTED_CELLS,
         '✅ 相符' if len(cells) == EXPECTED_CELLS
         else '🚨 不符——⚠️ 清單已漂移'))
print('   （%s）' % EXPECTED_SOURCE)
if nonliteral:
    print('   🚨 %d 格之型態非字面，本檔無從分類：%s'
          % (len(nonliteral), '、'.join(nonliteral[:6])))
print()

out = {}


def give(cell, value, population, note=''):
    out[cell] = {'producible': True, 'value': value,
                 'population': population, 'note': note}


def block(cell, why, kind):
    out[cell] = {'producible': False, 'blocker': why, 'blockerKind': kind}


# ── 私有根名冊 ───────────────────────────────────────────────────
roster = jload(RUN / 'standard-full-screen-pass-1' / 'title-only-judged-roster.json')
n_roster, n_entries = roster.get('entryCount'), len(roster.get('entries') or [])
if n_roster != n_entries:
    block('TITLE_ONLY_N',
          'entryCount %r ≠ entries 實際長度 %d——🚨 名冊自相矛盾，不報數'
          % (n_roster, n_entries), 'inconsistent-source')
else:
    give('TITLE_ONLY_N', n_roster,
         'standard-full-screen-pass-1 之 title-only-judged 名冊檔',
         '✅ 控制：entryCount 與 entries 長度相符')

rec = jload(RUN / 'screening-shadow-gate' / 'machine-reconciliation.json')['counts']
give('SHADOW_CONCORDANT', rec.get('concordantCount'),
     'screening-shadow-gate 之 machine-reconciliation（candidateCount %s）'
     % rec.get('candidateCount'))
give('SHADOW_QUEUED', rec.get('ownerAuditCount'),
     '同上——⚠️ 與 concordant 同母體，🚫 不得與其他影子批次相加')

# ── 撤稿：🚨 八份 worksheet，母體必須點名 ────────────────────────
per_ws, union = {}, set()
for p in sorted(RUN.glob('*/worksheet.json')):
    items = jload(p).get('items') or []
    hit = {i['candidateId'] for i in items
           if 'Retracted Publication' in (i.get('publicationTypes') or [])}
    per_ws[p.parent.name] = len(hit)
    union |= hit
give('RETRACT_FIELD_N', len(union),
     '八份 worksheet 之聯集，逐筆去重（candidateId）',
     '🚨 逐份為 %s——⚠️ 各份互有重疊。✅ n+152（一）已裁定本格母體即此聯集；'
     '🚫 不得與 `NARR_RETRACT_TEXT_N`（理由文字）或 `RETRACT_IN_EVIDENCE`'
     '（進入證據體）相加或互換。' % per_ws)

# ── 🆕 n+152（一）：聯集之中「進入證據體」者 ──────────────────────
# 🚨 母體是上面那個聯集（篩選過程遇到的），🚫 不是全體文獻；
# ⚠️ 而「進入證據體」以**錨定母體之最終判讀**為準（`m1_step2_population.json`
#    之 `decisions`，即校準抽樣所錨定的那一份），🚫 不是我自己定義的。
pop = jload(S + 'm1_step2_population.json')
dec = pop['decisions']


def in_evidence(ids, decisions):
    '''回傳 (進入證據體者, 逐筆狀態)。🚨 只有 `advance` 算進入。'''
    state = {cid: decisions.get(cid, '(不在錨定母體之 decisions 內)')
             for cid in sorted(ids)}
    return {c for c, v in state.items() if v == 'advance'}, state


# 🚨 控制探針：⚠️ 若不設，一個「永遠回 0」的實作與「真的沒有」長得一樣。
_ctl_ok = in_evidence({'a', 'b', 'c'},
                      {'a': 'advance', 'b': 'exclude'})[0] == {'a'}
print('   %s 控制：合成之 advance／exclude／缺席 → 只有 advance 被算進去'
      % ('✅' if _ctl_ok else '🚨'))
if not _ctl_ok:
    sys.exit('🚨 in_evidence 控制探針未過——🚫 不報 RETRACT_IN_EVIDENCE。')

adv, state = in_evidence(union, dec)
# ⚠️ 安全線之判讀不在錨定母體內，須另查其 judgements
#    （🚨 鍵為 `opinion`，🚫 不是 `decision`——本輪一次猜錯已由實查更正）。
elsewhere = {}
for jp in sorted(RUN.glob('*/judgements.json')):
    for e in (jload(jp).get('entries') or []):
        if e['candidateId'] in union and e['candidateId'] not in dec:
            elsewhere.setdefault(e['candidateId'], set()).add(e.get('opinion'))
never = sorted(c for c in union if c not in dec and c not in elsewhere)
give('RETRACT_IN_EVIDENCE', len(adv),
     '上一格之聯集 %d 筆中，錨定母體判為 `advance` 者' % len(union),
     '🚨 逐筆狀態：錨定母體 exclude %d 筆；⚠️ 安全線另檔判讀 %d 筆（皆 %s）；'
     '🚨 完全無判讀 %d 筆（%s）——⚠️ 未判讀者不可能「進入」證據體，故本格仍為 %d，'
     '🚫 但它與「已被排除」不是同一回事，報告不得寫成一律排除。'
     % (sum(1 for v in state.values() if v == 'exclude'), len(elsewhere),
        '／'.join(sorted({o for s2 in elsewhere.values() for o in s2})) or '—',
        len(never), '、'.join(c[-8:] for c in never) or '無', len(adv)))

# ── 取得層（🚨 依 n+151 三：走目錄者須列出被排除之舊命名目錄） ────
dirs = [p for p in FULL.iterdir() if p.is_dir()]
art = [p for p in dirs if ARTIFACT_DIR.search(p.name)]
legacy = [p.name for p in dirs
          if not ARTIFACT_DIR.search(p.name) and (p / 'manifest.json').exists()]
other = [p.name for p in dirs
         if not ARTIFACT_DIR.search(p.name) and not (p / 'manifest.json').exists()]
acq = {}
for p in art:
    mp = p / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') == 'acquired':
        acq[m['candidateId']] = m
give('ACQ_ALL', len(acq),
     '私有根 fulltext/ 全體之 acquired manifest（⚠️ 含本工作線以外之舊工作線）',
     '🚨 依 n+151（三）：走目錄之計數須列出被排除者——'
     '舊命名目錄 %d 個（%s）、非 artifact 目錄 %d 個（%s）。'
     % (len(legacy), '、'.join(n[:34] for n in legacy) or '無',
        len(other), '、'.join(other) or '無'))

cal = jload(S + 'm1_step2_calibration_set.json')
bf = jload(S + 'm1_step3_backfill.json')
scope = {c for d in cal['draws'].values() for c in d['candidateIds']}
scope |= {r['candidateId'] for p in bf['pools']
          for r in (p.get('backfilled') or []) if r.get('accepted')}
give('ACQ_SCOPED', sum(1 for c in scope if c in acq),
     '校準集抽出 60 ＋ n+103 接受之遞補 %d ＝ %d 筆之中的 acquired'
     % (len(scope) - 60, len(scope)),
     '🚨 n+138 曾把此數誤標為「全體 manifest」——⚠️ 分母是 %d，🚫 不是 60，'
     '亦🚫 不是 ACQ_ALL 之母體。' % len(scope))

# 🚨 判準已於第 505 輪更正：**改用明示欄位 `licenceProvenance`。**
# ⚠️ 初版以「授權欄之形狀」（字串 vs `{href,text}`）區分，並自陳
#    「脆弱，因為沒有『由誰填』的欄位」——🚨 而那個欄位一直都在，
#    我只是沒去看欄位清單，就把自己的沒看寫成了資料的缺陷。
prov = auto = 0
for m in acq.values():
    for a in (m.get('artifacts') or []):
        if not a.get('licence'):
            continue
        if 'licenceProvenance' in a:
            prov += 1
        else:
            auto += 1
give('LIC_FILLED', prov,
     'acquired manifest 之 artifact 具 `licenceProvenance` 者'
     '（🚨 即由本室依 n+138（三）填入並附來源與查取日期者）',
     '⚠️ 另有 %d 筆之授權係自 JATS `<license>` 自動擷取，🚫 無 provenance 欄，'
     '故不計入本格——🚨 兩者不是同一件事，🚫 不得相加後稱「有授權 N 筆」。' % auto)

# ── n60_tags.py：🚨 讀他人印出來的表，故每項配錨點 ────────────────
r = subprocess.run([sys.executable, S + 'n60_tags.py'], capture_output=True,
                   encoding='utf-8', errors='replace',
                   env=dict(os.environ, PYTHONIOENCODING='utf-8'))
tags_out = r.stdout or ''


def anchored(cell, pattern, population, note='', group=1):
    m = re.search(pattern, tags_out)
    if not m:
        block(cell, 'n60_tags 輸出找不到錨點 %r——🚫 不報數字（rc=%s）'
              % (pattern, r.returncode), 'parse-failed')
    else:
        give(cell, int(m.group(group)), population, note)


anchored('NARR_COMPARATOR_N', r'comparator 缺口（敘述式）\s+(\d+)\s+(\d+)/',
         'standard-full-screen-pass-1 之判讀理由文字中 comparator 缺口字樣',
         '🚨 這是**已掛牌者**之數，🚫 不是該類母體——⚠️ 未掛牌者本檔看不到。')
anchored('NARR_COMPARATOR_ADV', r'comparator 缺口（敘述式）\s+\d+\s+(\d+)/',
         '同上之 advance 筆數',
         '⚠️ 這一格存在的理由就是「總數會被讀成排除數」（n+115）。')
anchored('NARR_INSTRUMENT_N', r'instrument 缺口（敘述式）\s+(\d+)\s',
         '同上，儀器效度敘述式')
anchored('NARR_RETRACT_TEXT_N', r'撤稿（Retracted，非方括號）\s+(\d+)\s',
         '同上，理由文字之撤稿字樣',
         '🚨 🚫 不得與 `RETRACT_FIELD_N` 混用或相加——⚠️ 一個來自理由文字、'
         '一個來自 `publicationTypes` 欄位，母體與認定方式都不同。')
anchored('TAG_ROSTER_TOTAL', r'掛牌記錄去重後合計：(\d+)\s*筆',
         '所有掛牌名單去重後之合計（同一筆可掛多牌）')

rows = re.findall(r'^(\[[a-z-]+\]|撤稿（[^）]*）|comparator 缺口（[^）]*）|'
                  r'instrument 缺口（[^）]*）)\s+\d+', tags_out, re.M)
if rows:
    give('TAG_ROSTER_COUNT', len(rows), 'n60_tags 現跑之掛牌名單份數',
         '⚠️ 份數本身會隨新掛牌而變；🚨 已解析之列名：%s'
         % '、'.join(rows[:4] + ['…']))
else:
    block('TAG_ROSTER_COUNT', 'n60_tags 輸出解析不到任何掛牌列', 'parse-failed')

# ── 產不出來的（🚨 逐格寫明阻礙，🚫 不以近似值頂替） ──────────────
block('TITLE_ONLY_EXPECTED_GAP',
      '須由「僅憑題名判讀」之**率**推導，而 n+121 已裁定舊率（14.7%）取自特定'
      '段落不得直接套用；🚨 該用哪個率是裁定，🚫 不是檢索——待協調者裁定。',
      'needs-ruling')
block('SEX_SAMPLE_COMPOSITION',
      '證據體之性別組成須讀全文之受試者段落；🚨 萃取階段尚未開始，'
      '⚠️ 且它與「規劃率」是兩個量，🚫 不得互代。', 'needs-extraction')
block('POP_WORDING_UNCLEAR_N',
      '「僅卡族群措辭」是對判讀理由的**判讀**，🚫 不是檢索；'
      '⚠️ `[population]` 掛牌數（n60_tags 現跑）是**已掛牌者**，'
      '🚨 不等於該類母體，故不得頂替。', 'needs-judgement')
block('HARMS_S5_ACTUAL',
      '🚨 全文取得後、萃取判讀完成才存在；⚠️ 且 n+147 已明訂：'
      'GI 是否為主要結局之判斷正是 S5 要量的東西，🚫 不得由取得端順手做掉。',
      'needs-extraction')

# ── 輸出 ─────────────────────────────────────────────────────────
ok = [c for c in cells if out.get(c, {}).get('producible')]
no = [c for c in cells if c in out and not out[c]['producible']]
missing = [c for c in cells if c not in out]

print('%-26s %10s  %s' % ('格', '本輪現算', '母體／阻礙'))
print('-' * 104)
for c in cells:
    e = out.get(c)
    if e is None:
        print('%-26s %10s  🚨 本檔未涵蓋此格——⚠️ 清單漂移了' % (c, '—'))
    elif e['producible']:
        print('%-26s %10s  %s' % (c, e['value'], e['population'][:64]))
        if e.get('note'):
            print('%-26s %10s  %s' % ('', '', e['note'][:96]))
    else:
        print('%-26s %10s  🚫 %s' % (c, '產不出', e['blocker'][:64]))
print('-' * 104)
print('   ✅ 產得出 %d 格｜🚫 產不出 %d 格｜🚨 未涵蓋 %d 格'
      % (len(ok), len(no), len(missing)))
print()
print('🚨 本輪之值 🚫 不得寫進報告——n+151（一）明訂逐格須為**交付當日**現算。')
print('⚠️ 本檔今天證明的是「這格產得出來」，🚫 不是那格的答案。')

doc = {
    'schemaVersion': 1,
    'documentType': 'inaccessible-placeholder-producer',
    'ruling': 'n+151(1): the 不可及 cells are the executor room to run. This '
              'makes them one command instead of a hand rebuild on delivery day.',
    'population': "cells whose kind is 不可及 in n115_delivery_checklist.py's "
                  'DETAIL, read by ast rather than copied',
    'countingUnit': 'placeholder cell',
    'cellsFound': len(cells),
    'cellsWithNonLiteralKind': nonliteral,
    'cellsPerRuling': EXPECTED_CELLS,
    'cellsPerRulingSource': EXPECTED_SOURCE,
    'listDrift': len(cells) != EXPECTED_CELLS,
    'producible': ok,
    'notProducible': no,
    'notCovered': missing,
    'cells': out,
    'retractionPerWorksheet': per_ws,
    'retractionDecisionState': {c[-8:]: v for c, v in state.items()},
    'retractionJudgedElsewhere': {c[-8:]: sorted(v)
                                  for c, v in elsewhere.items()},
    'retractionNeverJudged': [c[-8:] for c in never],
    'legacyDirectoriesExcluded': legacy,
    'nonArtifactDirectoriesExcluded': other,
    'mustRecomputeOnDeliveryDay': True,
    'valuesAreNotAnswers': 'Every value here is evidence that the cell can be '
                           'produced, not the value to paste. n+151(1) requires '
                           'each cell to be computed on the day of delivery.',
    'coverageStatement': 'Produces what can be counted from private-root files or '
                         'existing read-only scripts. Cells needing a judgement, '
                         'a ruling, or an extraction that has not happened are '
                         'reported as not producible with the specific blocker, '
                         'never filled with an approximation. Values parsed out '
                         "of n60_tags.py's printed table are anchored; a missing "
                         'anchor yields parse-failed rather than a number.',
    'contentNote': 'Counts, cell names and population statements only.',
}
doc['producerHash'] = content_hash({'producible': ok, 'blocked': no})
io.open(S + 'n500_inaccessible_cells.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn500_inaccessible_cells.json' % S)
sys.exit(1 if missing else 0)
