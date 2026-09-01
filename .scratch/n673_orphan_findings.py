# -*- coding: utf-8 -*-
"""**哪幾支憑證亮了紅燈，卻沒有任何決策指向它。**（第 673 輪）

## ✅ 這是對本室自己的收尾對帳

93 支憑證裡，很多支的**答案探針是紅的**——那代表「事情不是它該有的樣子」。
🚨 若一支亮了紅燈，卻**既沒被任何決策引用，也沒有後續憑證接手**，
**⚠️ 那個發現就掉在地上了。**

## ✅ 判定方式

| 條件 | 意思 |
|---|---|
| 有失敗的控制探針 | 這支說了「有事」 |
| 🚫 沒有任何決策引用它 | 登記簿沒接 |
| 🚫 沒有更後面的憑證提到它的檔名 | 也沒有後續憑證接手 |

三者同時成立 → **候選孤兒**。

## ⚠️ 一件必須先講清楚的事

🚨 **本支產出的是「候選清單」，🚫 不是「缺陷數」。**
⚠️ 很多支的紅燈是**設計上就該紅**（答案探針就是用來說「答案是否定的」），
✅ 而其中有些本來就不需要裁定。

> **🚨 故本支不宣稱這些都是漏掉的東西——⚠️ 它只是把「沒人接手」的那些指出來，
> 讓本室逐一過目。**

## 🚫 本支不改任何清冊與契約、不送外部請求
"""
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
OUT = HERE / 'n673_orphan_findings.json'
REGISTER = HERE / 'n669_decision_register_v3.json'
ROUND_RE = re.compile(r'^n(\d+)_')

# ✅ 必觸發之反向要用的已知樣本
KNOWN_CITED = 'n588_reason_code_conflation.json'
KNOWN_FOLLOWED = 'n670_identifier_index.json'


def artefacts():
    out = []
    for path in sorted(HERE.glob('n*.json')):
        m = ROUND_RE.match(path.name)
        if not m:
            continue
        try:
            text = path.read_text(encoding='utf-8')
            doc = json.loads(text)
        except (OSError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        out.append((int(m.group(1)), path.name, doc, text))
    return out


def cited_files():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    mapping = {}
    for item in register['items']:
        for part in str(item['evidence']).replace('；', ';').split(';'):
            name = part.split('→')[0].strip()
            if name:
                mapping.setdefault(name, []).append(item['id'])
    return mapping


def main():
    docs = artefacts()
    cited = cited_files()

    rows, orphans = [], []
    for round_no, name, doc, _ in docs:
        # 🚨 掃描不能把自己的輸出算進去——⚠️ 最新的一支永遠不可能有後續。
        if name == OUT.name:
            continue
        probes = doc.get('controlProbes')
        if not isinstance(probes, list) or not probes:
            continue
        failed = [p.get('probe') for p in probes
                  if isinstance(p, dict) and not p.get('passed')]
        if not failed:
            continue
        # ⚠️ 後續憑證有沒有提到它（🚨 只看**更後面**的輪次）。
        # 🚨 第一版只比完整檔名，判不出 n671 接手了 n670——
        # ⚠️ 因為本室在文字裡都寫「第 670 輪」或 `n670`，很少寫完整檔名。
        # ✅ 這一條是必觸發之反向抓到的。
        marks = (name, name[:-5], 'n%d' % round_no, '第 %d 輪' % round_no)
        followers = [n for r, n, _, text in docs
                     if r > round_no and any(mark in text for mark in marks)]
        decisions = cited.get(name, [])
        row = {'artefact': name, 'round': round_no,
               'failedProbes': len(failed),
               'firstFailed': failed[0],
               'citedByDecisions': decisions,
               'followedUpBy': followers[:4],
               'followerCount': len(followers)}
        rows.append(row)
        if not decisions and not followers:
            orphans.append(row)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的有憑證亮著紅燈（必觸發之正對照）',
          len(rows) >= 10,
          '🚨 掃過 %d 支憑證，其中 %d 支有失敗探針；'
          '⚠️ 若很少，本支沒有可對帳的對象' % (len(docs), len(rows)))

    cited_row = next((r for r in rows if r['artefact'] == KNOWN_CITED), None)
    probe('已知被決策引用的那支不得判成孤兒（必觸發之反向）',
          cited_row is not None and cited_row['citedByDecisions'],
          '🚨 %s：引用它的決策 %s；⚠️ 若判成孤兒，代表引用關係沒接上'
          % (KNOWN_CITED,
             cited_row['citedByDecisions'] if cited_row else '該支未入表'))

    followed_row = next((r for r in rows
                         if r['artefact'] == KNOWN_FOLLOWED), None)
    probe('已知被後續憑證接手的那支不得判成孤兒（必觸發之反向）',
          followed_row is not None and followed_row['followerCount'] > 0,
          '🚨 %s：後續提到它的有 %s；⚠️ 若判成孤兒，代表「接手」判不出來'
          % (KNOWN_FOLLOWED,
             followed_row['followedUpBy'] if followed_row else '該支未入表'))

    # 🚨 這一道是答案。
    probe('每一支亮紅燈的憑證都有人接手（決策或後續憑證）',
          not orphans,
          '🚨 候選孤兒 %d 支：%s；'
          '⚠️ 這是**候選清單**，🚫 不是缺陷數——本室須逐一過目'
          % (len(orphans), [r['artefact'] for r in orphans] or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'orphan-finding-scan',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'artefactsScanned': len(docs),
        'withFailedProbes': len(rows),
        'orphanCandidates': orphans,
        'linkStrength': {
            'citedByDecision': sum(1 for r in rows if r['citedByDecisions']),
            'onlyMentionedLater': sum(
                1 for r in rows
                if not r['citedByDecisions'] and r['followerCount']),
            'neither': len(orphans),
        },
        'rows': rows,
        'whatThisIsNot': (
            '🚨 本支產出的是**候選清單**，🚫 不是缺陷數。'
            '⚠️ 很多支的紅燈是**設計上就該紅**——答案探針本來就是用來說'
            '「答案是否定的」——✅ 其中有些根本不需要裁定。'
            '🚫 故本支不宣稱這些都是漏掉的東西。'),
        'methodLimit': (
            '⚠️ 「有人接手」是用**檔名出現在更後面的憑證裡**判斷的，'
            '🚨 那只證明有人提過它，**🚫 不證明那個發現真的被處理了**。'
            '⚠️ 反過來也一樣：一支沒被提到，可能只是因為它的結論就是'
            '「沒事」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n673 亮紅燈卻沒人接手的憑證 ===')
    print('   掃過 %d 支｜有失敗探針 %d 支｜候選孤兒 %d 支'
          % (len(docs), len(rows), len(orphans)))
    print('   候選孤兒：')
    for row in orphans:
        print('      n%d %-44s 紅 %d 道｜%s'
              % (row['round'], row['artefact'], row['failedProbes'],
                 (row['firstFailed'] or '')[:44]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
