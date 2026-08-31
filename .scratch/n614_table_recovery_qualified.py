# -*- coding: utf-8 -*-
"""**上一輪那個「12 張」講得太寬——其中 4 張是別人的研究。**（第 614 輪）

## 🚨 本室去驗自己說過的一句話

第 613 輪說「表格文字被攤平後很難判讀」，同時又建議修。
**⚠️ 兩邊都說，等於沒說。✅ 故本輪把那 12 張讀出來。**

## ✅ 結論一：攤平後**確實讀得懂**

實測某篇的 Table 2.2 攤成：
「Exogenous CHO oxidation 63.4 ± 8.1 / 68.6 ± 10.8 p = 0.003 …」
**✅ 那是可以直接抽的。🚫 故「很難判讀」那句話對這一張是錯的。**

## 🚨 結論二：**但 12 張裡有 4 張是別人的研究**

那 4 張全在那本博士論文，是它第二章的**文獻整理表**
（引註 8–11 次、標題寫著「adapted from …」）。

> **🚨 救回來反而會把別的試驗的數字混進本語料。**
> ⚠️ 這是「參考文獻陷阱」**第三次**出現——
> 第 587 輪是 `time trial` 全在參考文獻裡、第 589 輪是劑量全在導論裡，
> **🚨 這一次是整張表都是別人的研究。**

## ✅ 結論三：真正乾淨的救援，比 12 少但**打在痛點上**

| 表 | 為什麼要緊 |
|---|---|
| `c3028a8a7b1ae2a1`「**嚴重腸胃道症狀發生率**」 | 🚨 **該篇目前貢獻 0 項** |
| `65dd82a89b2c5340`（206 個數字，含 GI） | 🚨 n598 那 7 項被指向方法段的同一篇 |
| `48da8a7f2f35af1f`（氧化，25 個數字） | ⚠️ 但寫的是肝醣**氧化**，🚫 不是運動後濃度（第六型） |

## 📮 故本室修正第 613 輪的建議

**✅ 仍建議修**，⚠️ 但要附一條：
**🚨 那本論文的文獻整理表不得當成它自己的結果**——
🚫 修好之後若沒有這條，會把別人的試驗數字讀進來。
"""
import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n614_table_recovery_qualified.json'
ZERO = Path(__file__).resolve().parent / 'n586_zero_contribution_census.json'

VOCAB = re.compile(
    r'time[- ]trial|completion time|time to exhaustion|exercise capacity'
    r'|exogenous|glycogen|nausea|bloat|cramp|fullness|reflux|flatulence'
    r'|gastrointestinal', re.I)
NUMBER = re.compile(r'\d+\.\d+|\d+\s*(?:±|\+/-)')
# 🚨 「這一張是別人的研究」的訊號：⚠️ 引註密度。
CITATION = re.compile(r'adapted from|et al\.|\(\d{4}\)|,\s*\d{4}\)')


def local(tag):
    return tag.rsplit('}', 1)[-1]


def main():
    zero_reports = set()
    if ZERO.exists():
        zero_reports = {r['report'] for r in json.loads(
            ZERO.read_text(encoding='utf-8')).get('zeroRows', [])}

    rows = []
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        if doc.get('sourceType') != 'grobid-tei':
            continue
        target = manifest.parent / (doc.get('teiFile') or '')
        if not target.is_file():
            continue
        try:
            body = next(n for n in ET.parse(target).getroot().iter()
                        if local(n.tag) == 'body')
        except (ET.ParseError, StopIteration):
            continue
        for figure in [c for c in body if local(c.tag) == 'figure'
                       and (c.get('type') or '') == 'table']:
            text = ' '.join(''.join(figure.itertext()).split())
            if not (NUMBER.search(text) and VOCAB.search(text)):
                continue
            numbers = len(NUMBER.findall(text))
            citations = len(CITATION.findall(text))
            kind = ('literature-summary' if citations >= 3
                    else 'thin' if numbers < 3 else 'own-results')
            report = doc['candidateId'][-16:]
            rows.append({'report': report, 'kind': kind, 'numbers': numbers,
                         'citations': citations,
                         'reportContributesZero': report in zero_reports})

    kinds = collections.Counter(r['kind'] for r in rows)
    literature = [r for r in rows if r['kind'] == 'literature-summary']
    own = [r for r in rows if r['kind'] == 'own-results']
    zero_recovery = [r for r in own if r['reportContributesZero']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('分類到的是第 613 輪那 12 張（必觸發）',
          len(rows) == 12,
          '🚨 對不上就代表本支看的不是同一批；實得 %d 張' % len(rows))
    # 🚨 必觸發之反向：⚠️ 分類器要真的分得出兩類。
    probe('分類器分得出不只一類（必觸發之反向）',
          len(kinds) >= 2,
          '⚠️ 實得 %s；🚨 若只有一類，這個分類什麼都沒說' % dict(kinds))
    # 🚨 這一道會紅，而它修正了本室上一輪的說法。
    probe('被丟掉的表全部是該篇自己的結果',
          not literature,
          '🚨 實得 %d 張是**別人的研究**（文獻整理表，引註 %s 次），'
          '⚠️ 全在那本博士論文；🚫 救回來會把別的試驗數字混進本語料——'
          '✅ 這是「參考文獻陷阱」第三次出現，這次是整張表'
          % (len(literature), sorted(r['citations'] for r in literature)))
    # ✅ 而真正的救援仍然存在，且打在痛點上。
    probe('有乾淨的救援對象（必觸發）',
          bool(own),
          '✅ 自有結果的表 %d 張，其中 %d 張屬於**目前貢獻 0 項**的論文'
          % (len(own), len(zero_recovery)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'table-recovery-qualified',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'classified': dict(kinds),
        'rows': rows,
        'correctsRound613': (
            '🚨 第 613 輪報「12 張帶著結局」——⚠️ 講得太寬。'
            '✅ 其中 4 張是那本論文的文獻整理表（別人的研究），'
            '🚫 救回來會把別的試驗數字混進來。'),
        'flattenedTablesAreReadable': (
            '✅ 實測某篇的表攤平成「Exogenous CHO oxidation 63.4 ± 8.1 / '
            '68.6 ± 10.8 p = 0.003」——**可以直接抽**。'
            '🚫 故第 613 輪「很難判讀」那句對這一張是錯的。'),
        'cleanRecoveries': (
            '✅ c3028a8a7b1ae2a1 的「嚴重腸胃道症狀發生率」表——'
            '🚨 該篇目前貢獻 0 項；'
            '✅ 65dd82a89b2c5340 的 206 數字表——'
            '🚨 正是 n598 那 7 項被指向方法段的同一篇。'),
        'caveatOnGlycogen': (
            '⚠️ 那張氧化表寫的是肝醣**氧化**，🚫 不是運動後**濃度**——'
            '🚨 第 568 輪之第六型。故第 613 輪「肝醣 6 張」的收益要打折。'),
        'revisedRecommendation': (
            '✅ 仍建議修 D17，⚠️ 但必須附一條：'
            '🚨 那本論文的文獻整理表不得當成它自己的結果。'
            '🚫 沒有這條，修好之後會把別人的試驗數字讀進來。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n614 那 12 張的分類 ===')
    print('   %s' % dict(kinds))
    print('   🚨 文獻整理表（別人的研究）：%d 張，全在 %s'
          % (len(literature), sorted({r['report'] for r in literature})))
    print('   ✅ 自有結果：%d 張｜其中屬貢獻 0 項之論文：%d 張'
          % (len(own), len(zero_recovery)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
