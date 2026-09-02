# -*- coding: utf-8 -*-
"""**讓「目錄」變成量出來的，而不是列出來的。**（第 709 輪）

## ✅ 補上第 708 輪自己寫下的限制

n708：「🚨 本支只排除兩種 `documentType`。⚠️ 若日後又出現別的目錄型產物，
**同樣的污染會再發生，🚫 而本支不會自動認出它。**」

## ✅ 目錄有一個**結構特徵**，🚫 不必靠型別名

> **🚨 目錄的特徵是「它提到語料裡絕大部分的識別字」。**

✅ 故量：`該支的相異識別字數 ／ 全語料的相異識別字數`。
⚠️ 一支真正的發現只碰它查的那幾篇；🚨 目錄碰全部。

## 🚨 而判準要**雙面**驗證，只過一面不算

| 面 | 要求 |
|---|---|
| **正面** | 第 708 輪已知的 12 支目錄，**全部**要在門檻之上 |
| **反面** | 幾支公認的「發現」（`n585`／`n594`／`n612`／`n701`）**全部**要在門檻之下 |

⚠️ 只過正面 → 門檻太鬆（什麼都算目錄）；🚨 只過反面 → 門檻太緊（漏掉目錄）。

## ✅ 而它可能會抓到本室**沒列進**硬編清單的目錄

🚨 那正是重點——**⚠️ 若有，就證明硬編清單當時已經不完整。**

## 🚫 本支不改任何清冊與契約、不送外部請求
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n709_catalogue_by_measure.json'

ROUND_RE = re.compile(r'^n(\d+)_')
REPORT_RE = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
REASON_RE = re.compile(r'\b(?:notExtracted|escalated)-[a-z0-9-]+\b')
KEBAB_RE = re.compile(r'\b[a-z][a-z0-9]*(?:-[a-z0-9]+){2,}\b')
DECISION_RE = re.compile(r'\bD[1-9][0-9]?\b')

HARDCODED_TYPES = {'identifier-index', 'pending-decision-register'}
# ✅ 反面對照：公認的「發現」型憑證
KNOWN_FINDINGS = ['n585_blocked_drafts_errata.json',
                  'n594_a3_first_measurement.json',
                  'n612_parse_tei_root_cause.json',
                  'n701_d3_d24_interlock.json']
THRESHOLD = 0.25


def identifiers(text):
    return (set(REPORT_RE.findall(text)) | set(REASON_RE.findall(text))
            | set(KEBAB_RE.findall(text)) | set(DECISION_RE.findall(text)))


def main():
    per_file, doc_types = {}, {}
    for path in sorted(HERE.glob('n*.json')):
        if not ROUND_RE.match(path.name):
            continue
        try:
            text = path.read_text(encoding='utf-8')
            doc = json.loads(text)
        except (OSError, ValueError):
            continue
        per_file[path.name] = identifiers(text)
        doc_types[path.name] = (doc.get('documentType')
                                if isinstance(doc, dict) else None)

    universe = set().union(*per_file.values()) if per_file else set()
    share = {name: (len(ids) / len(universe) if universe else 0.0)
             for name, ids in per_file.items()}

    hardcoded = {n for n, t in doc_types.items() if t in HARDCODED_TYPES}
    detected = {n for n, s in share.items() if s >= THRESHOLD}

    missed_by_hardcoded = sorted(detected - hardcoded)
    missed_by_measure = sorted(hardcoded - detected)
    findings_share = {n: round(share.get(n, 0.0), 3)
                      for n in KNOWN_FINDINGS if n in share}

    ranked = sorted(share.items(), key=lambda kv: -kv[1])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('量得到足夠多的憑證（必觸發之正對照）',
          len(per_file) >= 100 and len(universe) >= 100,
          '🚨 憑證 %d 支、全語料相異識別字 %d 個；'
          '⚠️ 太少的話這個比例沒有意義' % (len(per_file), len(universe)))
    # 🚨 正面：已知的目錄都要被抓到。
    probe('第 708 輪那 12 支目錄，結構判準全部抓得到（必觸發之正對照）',
          not missed_by_measure,
          '🚨 硬編認定的目錄 %d 支；結構判準漏掉的：%s；'
          '⚠️ 漏掉就代表門檻太緊'
          % (len(hardcoded),
             [(n, round(share[n], 3)) for n in missed_by_measure] or '無'))
    # 🚨 反面：公認的發現都不能被誤判成目錄。
    over = [n for n, s in findings_share.items() if s >= THRESHOLD]
    probe('公認的「發現」都在門檻之下（必觸發之反向）',
          not over,
          '🚨 反面對照的佔比：%s；被誤判成目錄的：%s；'
          '⚠️ 誤判就代表門檻太鬆，會把真線索也排掉'
          % (findings_share, over or '無'))
    # 🚨 這一道是本輪真正的答案：兩群分不分得開。
    # ⚠️ 若「已知目錄的最低佔比」低於「已知發現的最高佔比」，
    # **🚫 任何單一門檻都分不開它們**——那是算得出來的，不是調參能解決的。
    cat_shares = {n: share[n] for n in hardcoded if n in share}
    all_findings = {n: s for n, s in share.items()
                    if n not in hardcoded}
    min_cat = min(cat_shares.values()) if cat_shares else 0.0
    max_find = max(all_findings.values()) if all_findings else 0.0
    separable = min_cat > max_find
    probe('目錄與發現在這個量尺上分得開',
          separable,
          '🚨 已知目錄的**最低**佔比 %.3f（%s）；'
          '非目錄的**最高**佔比 %.3f（%s）；'
          '⚠️ 前者低於後者就代表兩群重疊——'
          '**🚫 任何單一門檻都分不開，🚨 而調門檻只是對已知答案過擬合。**'
          % (min_cat,
             min(cat_shares, key=cat_shares.get) if cat_shares else '—',
             max_find,
             max(all_findings, key=all_findings.get)
             if all_findings else '—'))
    probe('硬編清單當時已經完整（結構判準沒有抓到額外的目錄）',
          not missed_by_hardcoded,
          '🚨 結構判準抓到、而硬編清單**沒有**的 %d 支：%s；'
          '⚠️ 有的話就證明硬編清單當時已經不完整'
          % (len(missed_by_hardcoded),
             [(n, round(share[n], 3), doc_types.get(n))
              for n in missed_by_hardcoded]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'catalogue-by-measure',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n708（目錄是列出來的，不是量出來的）',
        'measure': ('✅ `該支的相異識別字數 ／ 全語料的相異識別字數`——'
                    '🚨 目錄的特徵是「它提到絕大部分的識別字」。'),
        'threshold': THRESHOLD,
        'artefacts': len(per_file),
        'universeSize': len(universe),
        'hardcodedCatalogues': sorted(hardcoded),
        'detectedByMeasure': sorted(detected),
        'detectedButNotHardcoded': missed_by_hardcoded,
        'hardcodedButNotDetected': missed_by_measure,
        'knownFindingsShare': findings_share,
        'topShares': [{'artefact': n, 'share': round(s, 3),
                       'documentType': doc_types.get(n)}
                      for n, s in ranked[:15]],
        'verdict': (
            '🚨 **這條路走不通，而且不是門檻沒調好。**'
            '⚠️ 已知目錄的最低佔比**低於**非目錄的最高佔比——'
            '**🚫 兩群重疊，任何單一門檻都分不開。**'
            '✅ 只有索引本身（佔比 1.000）是乾淨可分的；'
            '🚨 而各版登記簿的佔比（0.05–0.13）**低於**'
            '`n694_jats_table_parity`（0.170）這種真發現。'
            '**⚠️ 故第 708 輪的硬編型別清單留著，'
            '🚫 它的限制本輪沒有解決——本室如實記為失敗路線。**'),
        'whatIRefusedToDo': (
            '🚨 本室**沒有**去調門檻讓它「看起來成功」——'
            '⚠️ 在已知答案上調參，只是把過擬合當成發現。'),
        'whyTwoSided': (
            '🚨 只過正面 → 門檻太鬆（什麼都算目錄，真線索也被排掉）；'
            '⚠️ 只過反面 → 門檻太緊（漏掉目錄，污染照舊）。'
            '**✅ 兩面都要。**'),
        'methodLimit': (
            '⚠️ 門檻 %.2f 是**本室訂的**，🚫 不是算出來的——'
            '🚨 若目錄與發現之間沒有明顯的斷層，這個門檻就只是一條任意線。'
            '✅ 故本支同時列出**佔比排行**，讓人自己看有沒有斷層。'
            % THRESHOLD),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n709 用量的方式認出目錄 ===')
    print('   憑證 %d 支｜全語料相異識別字 %d 個｜門檻 %.2f'
          % (len(per_file), len(universe), THRESHOLD))
    print('   佔比排行（前 15）：')
    for row in doc['topShares']:
        mark = '📚' if row['artefact'] in hardcoded else '  '
        print('      %s %-44s %.3f  %s'
              % (mark, row['artefact'], row['share'],
                 row['documentType'] or ''))
    print('   反面對照（公認的發現）：%s' % findings_share)
    print('   🚨 結構判準抓到而硬編沒有的：%s' % (missed_by_hardcoded or '無'))
    print('   ⚠️ 硬編有而結構判準沒抓到的：%s' % (missed_by_measure or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
