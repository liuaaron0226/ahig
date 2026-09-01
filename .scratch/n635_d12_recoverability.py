# -*- coding: utf-8 -*-
"""**那 4 項「沒有數值結果」的東西，是不是躺在被丟掉的表格裡。**（第 635 輪）

## 🚨 D12 目前的問法可能是錯的

⚠️ 第 597 輪找到 4 個在範圍內結局宣稱 `hasNumericResult=True`，
🚨 而本室在**內文**裡找不到支撐的數字，於是 D12 問「要不要撤回」。

> **🚨 但那 4 項全部出自同一篇 `1105537918c174c9`——⚠️ 而它是 GROBID 那 15 篇之一。**
> **🚨 第 612 輪已證明 `parse_tei` 把 `<figure type="table">` 整個漏掉。**

**⚠️ 也就是說：本室是在一份「表格被拿掉的文本」裡找表格裡的數字。**

## ✅ 本支怎麼問

直接開那份 TEI，**看被丟掉的表格裡有沒有那四個症狀與數字**。

| 若 | 則 D12 應改成 |
|---|---|
| 表裡找得到 | **🚨 不是撤回，是「D17 修完後重讀」**——⚠️ 兩個決定變成一個 |
| 表裡也沒有 | ⚠️ **要先確認那張表本來就該有這些東西**，否則「沒有」什麼都不代表 |

**🚨 而本輪的答案落在第二列，且對照沒過**：這一篇只有 1 張表、741 字元，
**連內文有數字的對照症狀都不在表裡**——⚠️ 即那張表不含腸胃症狀內容。
**✅ 故本支只結清一件事：表格救援這條路對這 4 項不適用；🚫 不對 D12 本身下結論。**

## ⚠️ 內容紀律

🚫 本支不輸出任何表格文字、不輸出題名——**✅ 只輸出計數與布林**（n+195 一）。
🚫 不改解析器、不改任何清冊。
"""
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

OUT = Path(__file__).resolve().parent / 'n635_d12_recoverability.json'

REPORT = '1105537918c174c9'
# ⚠️ 第 597 輪那 4 項的症狀詞。
SYMPTOMS = ['comfort', 'cramp', 'nausea', 'headache']
# 🚨 對照組：同一篇在內文裡**找得到**數字的那些症狀（第 597 輪已量）。
CONTROL_SYMPTOMS = ['fullness', 'bloat', 'thirst']

NUMBER = re.compile(r'\d')


def local(tag):
    return tag.rsplit('}', 1)[-1]


def flatten(node):
    return ' '.join(x.strip() for x in node.itertext() if x and x.strip())


def main():
    directory = None
    manifest = None
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue
        path = entry / 'manifest.json'
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc['candidateId'].endswith(REPORT):
            directory, manifest = entry, doc
            break

    if manifest is None:
        raise SystemExit('🚨 找不到 %s 的清單' % REPORT)

    tei_name = manifest.get('teiFile')
    sections_name = manifest.get('sectionsFile')
    tei_root = ET.parse(directory / tei_name).getroot()

    # 🚨 被丟掉的那些：body 底下 <figure type="table">（第 612 輪的根因）。
    body = next((n for n in tei_root.iter() if local(n.tag) == 'body'), None)
    tables = [n for n in body.iter()
              if local(n.tag) == 'figure'
              and (n.get('type') or '').lower() == 'table'
              ] if body is not None else []
    table_text = ' \n '.join(flatten(t) for t in tables)

    sections = json.loads(
        (directory / sections_name).read_text(encoding='utf-8'))
    section_text = json.dumps(sections, ensure_ascii=False)

    def hits(word, haystack):
        found = 0
        with_number = 0
        for match in re.finditer(re.escape(word), haystack, re.IGNORECASE):
            found += 1
            window = haystack[match.start(): match.end() + 120]
            if NUMBER.search(window):
                with_number += 1
        return {'mentions': found, 'withNumberNearby': with_number}

    in_tables = {w: hits(w, table_text) for w in SYMPTOMS}
    in_sections = {w: hits(w, section_text) for w in SYMPTOMS}
    control_tables = {w: hits(w, table_text) for w in CONTROL_SYMPTOMS}

    recoverable = [w for w in SYMPTOMS
                   if in_tables[w]['withNumberNearby'] > 0]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('這一篇確實走 GROBID 且表格確實不在 sections（必觸發之正對照）',
          manifest.get('sourceType') == 'grobid-tei' and len(tables) > 0,
          '🚨 sourceType=%s｜TEI 裡的 <figure type="table"> 共 %d 張；'
          '⚠️ 若是 0 張，本支整個問題不成立'
          % (manifest.get('sourceType'), len(tables)))
    probe('表格文字真的抽得出東西（必觸發之正對照）',
          len(table_text) > 200 and NUMBER.search(table_text) is not None,
          '🚨 表格攤平後 %d 字元、含數字=%s；⚠️ 若抽不出東西，'
          '「表裡沒有」只是本支沒讀到'
          % (len(table_text), bool(NUMBER.search(table_text))))
    table_has_gi = any(v['mentions'] > 0 for v in control_tables.values())
    probe('那張表裡有腸胃症狀內容（必觸發之正對照）',
          table_has_gi,
          '🚨 對照組（內文有數字的那三個症狀）在表裡的命中：%s；'
          '⚠️ 全為 0 代表**這張表根本不含腸胃症狀內容**——'
          '🚨 於是「那 4 項不在表裡」是一個**無資訊的空結果**'
          % {k: v['mentions'] for k, v in control_tables.items()})
    # 🚨 結論必須綁在對照上：⚠️ 否則它會為了錯的理由通過。
    # **本支第一版就是那樣**——對照亮紅，而結論那一道照樣判綠。
    probe('可以據此對 D12 下結論',
          table_has_gi,
          '🚨 只有在上一道成立時，「表裡找不到」才代表什麼；'
          '⚠️ 本輪對照未成立，**故本支不對 D12 下任何結論**——'
          '✅ 它能確定的只有一件：**表格救援這條路對這 4 項不適用**'
          '（表裡找到「症狀＋鄰近數字」者 %d 個）' % len(recoverable))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd12-recoverability',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'report': REPORT,
        'sourceType': manifest.get('sourceType'),
        'tablesInTei': len(tables),
        'tableTextLength': len(table_text),
        'symptomsInTables': in_tables,
        'symptomsInSections': in_sections,
        'controlSymptomsInTables': control_tables,
        'recoverableSymptoms': recoverable,
        'consequenceForD12': (
            '⚠️ 本支原本要問的是「那 4 項是不是躺在被丟掉的表格裡」。'
            '🚨 結果：這一篇的 TEI 只有 **1 張表、741 字元**，'
            '而**對照症狀（內文有數字的那三個）在表裡一個都沒有**——'
            '**⚠️ 即那張表根本不含腸胃症狀內容。**'
            '**🚨 故「那 4 項不在表裡」是無資訊的空結果，'
            '🚫 不能拿來支持撤回。**'
            '✅ 本支能確定的只有一件：**表格救援這條路對這 4 項不適用**，'
            '⚠️ 即 D12 **不會**因為 D17 而自動解決——'
            '🚫 兩者仍是各自獨立的決定。'),
        'noteOnSectionHits': (
            '⚠️ 本支的粗略規則（症狀詞後 120 字元內出現任何數字）在 sections 裡'
            '對四個症狀都有命中。🚫 這**不**表示第 597 輪錯了——'
            '🚨 該輪用的是逐項、較嚴的判準，而本支這條規則連段落編號都算數字。'
            '**✅ 故本支不對第 597 輪的判定表示意見。**'),
        'contentDiscipline': (
            '✅ 只輸出計數與布林；🚫 不輸出任何表格文字或題名（n+195 一）。'),
        'whatThisCannotAnswer': (
            '🚫 找到「症狀詞附近有數字」不等於「那就是該結局的結果」——'
            '⚠️ 本支不判讀表格內容，🚨 它只說「那裡有東西值得重讀」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n635 D12 可救回性 ===')
    print('   報告 %s｜來源 %s｜TEI 表格 %d 張｜攤平後 %d 字元'
          % (REPORT, manifest.get('sourceType'), len(tables),
             len(table_text)))
    print('   %-12s %14s %14s' % ('症狀', '表格內(數字)', 'sections內(數字)'))
    for word in SYMPTOMS:
        print('   %-12s %6d(%d) %11d(%d)'
              % (word, in_tables[word]['mentions'],
                 in_tables[word]['withNumberNearby'],
                 in_sections[word]['mentions'],
                 in_sections[word]['withNumberNearby']))
    print('   對照症狀在表格內：%s'
          % {k: v['mentions'] for k, v in control_tables.items()})
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
