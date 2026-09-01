# -*- coding: utf-8 -*-
"""**那些「必觸發」的控制，真的會亮嗎。**（第 629 輪）

## 🚨 第 628 輪發現本室有一道探針恆真，往回查又找到三道

⚠️ 依 n+112（二），期待空輸出的檢查自證不了自己，**必須有一道會亮的反向控制**。
🚨 而第 628 輪查明：n622／n624／n625／n628 各有一道標成「必觸發」的探針
**在任何輸入下都不可能失敗**——那是裝飾，不是控制。

> **⚠️ 只查了「假鍵」那一種形狀還不夠。🚨 真正的問題是：
> 協調者正被要求依 624–628 這條鏈做裁定，而那條鏈的證據力全靠這些控制。**

## ✅ 本支的做法：突變測試，🚫 不用推論

對鏈上每一支憑證，**注入一個具體故障**，看**該亮的那一道**有沒有真的變紅。

| 憑證 | 注入的故障 | 應當亮的控制 |
|---|---|---|
| n624 | 讓一個舊命名孤兒目錄變成 `acquired` | 名冊未被孤兒污染 |
| n625 | 把 `advance` 判詞全部改名 | advance 集合非空且與已取得有交集 |
| n626 | 讓劑量抽取器永遠抽不到 | 抽取器真的抽得到劑量 |
| n627 | 把清冊的劑量單位換成 g/min | 真值的單位只有一種 |
| n628 | 把一項的結局改成假名 | 假鍵不在且真鍵在 |

**🚨 亮了才算控制；⚠️ 沒亮就是本室在拿裝飾當證據。**

## ✅ 安全性

🚫 **不動任何原始資料**：突變只作用在複製到暫存目錄的**程式碼副本**上，
⚠️ 且副本的輸出檔會落在暫存目錄（因為那些憑證都用 `__file__` 定位輸出）。

## 🚫 本支不送外部請求、不改任何產品程式、不改任何清冊
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

S = Path(__file__).resolve().parent
OUT = S / 'n629_probe_mutation_test.json'

# ⚠️ 每個案例：憑證檔、原文、替換文、應當亮的探針（子字串）。
CASES = [
    {
        'artefact': 'n624_corpus_denominator.py',
        'fault': '讓一個舊命名孤兒目錄看起來是 acquired',
        'find': "    orphan_acquired = [o for o in legacy_orphans "
                "if o['status'] == 'acquired']",
        'replace': "    orphan_acquired = [o for o in legacy_orphans "
                   "if o['status'] in ('acquired', 'unavailable')]",
        'expect': '名冊未被孤兒目錄污染',
    },
    {
        'artefact': 'n625_corpus_era_bias.py',
        'fault': '把 advance 判詞全部改名，使分母落空',
        'find': "    advance = {c for c, o in opinion.items() if o == 'advance'}",
        'replace': "    advance = {c for c, o in opinion.items() "
                   "if o == 'ZZ-改過名的-advance'}",
        'expect': 'advance 集合非空',
    },
    {
        'artefact': 'n626_missing_era_dose_space.py',
        'fault': '讓劑量抽取器永遠抽不到東西',
        'find': "    return [v for v in values "
                "if PLAUSIBLE[0] <= v <= PLAUSIBLE[1]]",
        'replace': "    return [v for v in values "
                   "if PLAUSIBLE[0] <= v <= PLAUSIBLE[1]][:0]",
        'expect': '抽取器真的抽得到劑量',
    },
    {
        'artefact': 'n627_dose_proxy_validation.py',
        'fault': '把真值的劑量單位換成 g/min',
        'find': "            units.add(outcome.get('doseUnit'))",
        'replace': "            units.add('g/min')",
        'expect': '真值的單位只有一種',
    },
    {
        'artefact': 'n628_evidence_thinness.py',
        'fault': '把真實結局名改掉，使真鍵消失',
        'find': "                'ref': outcome.get('normalisedOutcomeRef'),",
        'replace': "                'ref': 'ZZ-假結局-ZZ',",
        'expect': '以不存在的結局查',
    },
]


def probes_from(text):
    """從憑證的標準輸出裡讀回每一道探針的紅綠。"""
    found = {}
    for raw in text.split('\n'):
        line = raw.strip()
        for mark, ok in (('✅ ', True), ('🚨 ', False)):
            if line.startswith(mark):
                found[line[len(mark):]] = ok
                break
    return found


def run(path, workdir, env):
    result = subprocess.run([sys.executable, '-X', 'utf8', str(path)],
                            cwd=str(workdir), capture_output=True,
                            text=True, encoding='utf-8', errors='ignore',
                            env=env)
    return result.stdout or '', result.stderr or ''


def main():
    workdir = Path(tempfile.mkdtemp(prefix='ahig-probe-mutation-'))
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(
        [str(REPO / 'ahig'), env.get('PYTHONPATH', '')])
    env['PYTHONIOENCODING'] = 'utf-8'

    # ⚠️ 這些憑證用 `__file__` 旁的檔案，故一併帶過去。
    for name in ('private_root.py', 'm1_step3_inventory.json',
                 'm1_step3_backfill.json'):
        shutil.copy2(S / name, workdir / name)

    results = []
    for case in CASES:
        source = (S / case['artefact']).read_text(encoding='utf-8')
        applied = case['find'] in source
        target = workdir / case['artefact']

        # ① 未突變的副本：⚠️ 先確認它在暫存目錄裡本來就跑得起來，
        # 🚨 否則「突變後變紅」可能只是搬家搬壞了。
        target.write_text(source, encoding='utf-8')
        clean_out, clean_err = run(target, workdir, env)
        clean = probes_from(clean_out)

        # ② 突變後的副本。
        target.write_text(source.replace(case['find'], case['replace']),
                          encoding='utf-8')
        dirty_out, dirty_err = run(target, workdir, env)
        dirty = probes_from(dirty_out)

        def look(table):
            for name, ok in table.items():
                if case['expect'] in name:
                    return ok
            return None

        clean_state, dirty_state = look(clean), look(dirty)
        results.append({
            'artefact': case['artefact'],
            'fault': case['fault'],
            'faultApplied': applied,
            'expectProbe': case['expect'],
            'cleanCopyRuns': bool(clean),
            'probeGreenWhenClean': clean_state,
            'probeRedWhenFaulted': dirty_state is False,
            'probeFoundInBothRuns': clean_state is not None
            and dirty_state is not None,
            'cleanStderrTail': [x for x in clean_err.strip().split('\n')[-2:]
                                if x],
            'dirtyStderrTail': [x for x in dirty_err.strip().split('\n')[-2:]
                                if x],
        })

    shutil.rmtree(workdir, ignore_errors=True)

    fired = [r for r in results if r['probeRedWhenFaulted']]
    未fired = [r for r in results if not r['probeRedWhenFaulted']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每個故障都真的注入了（必觸發之正對照）',
          all(r['faultApplied'] for r in results),
          '🚨 %d/%d 個案例找得到要替換的原文；⚠️ 找不到就等於沒突變，'
          '而「沒亮」會被誤讀成「控制壞了」'
          % (sum(1 for r in results if r['faultApplied']), len(results)))
    probe('未突變的副本本來就是綠的（必觸發之對照）',
          all(r['probeGreenWhenClean'] for r in results),
          '🚨 %d/%d 個案例在未突變時該探針為綠；⚠️ 若本來就紅，'
          '「突變後變紅」證明不了任何事'
          % (sum(1 for r in results if r['probeGreenWhenClean']),
             len(results)))
    probe('每支憑證的控制在故障下都真的亮了',
          not 未fired,
          '🚨 未亮者 %d 個：%s'
          % (len(未fired),
             [(r['artefact'], r['expectProbe']) for r in 未fired]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'probe-mutation-test',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'method': ('✅ 對每支憑證的**程式碼副本**注入一個具體故障，'
                   '看該亮的控制有沒有變紅。🚫 不動任何原始資料。'),
        'cases': results,
        'firedCount': len(fired),
        'totalCases': len(results),
        'whyItMatters': (
            '⚠️ 協調者正被要求依 624–628 這條鏈做裁定，'
            '🚨 而那條鏈的證據力全靠這些控制。'
            '**⚠️ 第 628 輪已證明本室寫得出恆真的假控制**——'
            '✅ 故本支不推論、直接讓它們亮一次。'),
        'whatThisCannotAnswer': (
            '🚫 本支只驗每支**一道**控制——⚠️ 其餘各道未受檢；'
            '🚨 亮得起來也不表示它抓得到**別種**故障。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n629 控制探針突變測試 ===')
    for r in results:
        print('   %-34s %s' % (r['artefact'],
                               '✅ 故障下亮了' if r['probeRedWhenFaulted']
                               else '🚨 故障下沒亮'))
        print('      故障：%s' % r['fault'])
        print('      注入成功=%s｜未突變時為綠=%s｜兩次都找得到該探針=%s'
              % (r['faultApplied'], r['probeGreenWhenClean'],
                 r['probeFoundInBothRuns']))
        if r['dirtyStderrTail'] and not r['probeRedWhenFaulted']:
            print('      ⚠️ 突變後的 stderr：%s' % r['dirtyStderrTail'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
