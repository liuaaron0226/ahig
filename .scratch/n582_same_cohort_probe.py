# -*- coding: utf-8 -*-
"""**哪兩篇報告的是同一批受試者。**（第 582 輪）

## 🚨 結論先講：找到一對，而**署名篩選看不見它**

`7a6ac1559c740fd6` 的受試者特徵**六個值全部逐字出現在** `307c0dd5b141caed` 裡，
**⚠️ 且它自己沒有任何一個值是對方沒有的。** 對方另外還有第二組人。

> **🚨 那不是「作者重疊」，是「同一批人」。**
> ⚠️ 而第 581 輪的署名篩選**完全沒抓到這一對**——
> 🚨 因為 `307c0dd5b141caed` 只抽得到 **1 位作者**（GROBID 沒解出作者清單），
> **⚠️ 於是「共有 ≥2 位作者」永遠不可能成立。**
>
> **🚨 這正是本 run 一再抓到的那一族**：第 581 輪報「作者涵蓋率 41／41」，
> ⚠️ 而那量的是**有沒有**，不是**完不完整**——
> **🚫 4 篇的作者清單只有 1–2 位，它們實際上沒有被篩選過。**

## ✅ 為什麼這個判準可信

⚠️ 同一實驗室連發五篇不同試驗，署名會長得一模一樣；
**✅ 但受試者的年齡、體重、身高、VO₂max 不會逐字相同**——即使只差 0.4 歲也不同。

🚫 **不看全文**：⚠️ 結果段落裡也有幾百個 `±`，那些是**結果**不是**受試者**，
🚨 拿來比會製造大量假的相同。
**✅ 只讀 `Participants`／`Subjects` 段落，外加 `Table 1`**（第 583 輪加，見下）。

## 🚨 第 583 輪：加了 Table 1，而它一度把判準弄壞

⚠️ 12 篇的受試者特徵**寫在表格裡**，文字段落一個 `±` 都沒有，故加 `Table 1`。
**🚨 但有一篇的 Table 1 有 84 個 `±`——那不是受試者表，是結果表。**
⚠️ 數值一多，純靠巧合撞到 2 個的機會就大，**實測當場生出 4 對假的「同一批」。**

> ✅ **兩個修法，缺一不可**：
> ① 一張表超過 20 個數值就**整張不用**（🚫 不從裡面挑——挑等於本室替論文
> 決定哪幾個是特徵）；
> ② 判定改看**比例**而非個數：**較小那一方要有一半以上的特徵中**。
> 🚨 修完假陽性從 6 對回到 1 對，而**那一對是 100%**——⚠️ 次高者只有 50%
> 且只共用 1 個值。

## 🚨 而「零相同」要能被相信，得先量巧合率

⚠️ 若隨便兩篇不相干的論文也常常「相同 2 個數值」，這個判準就沒有分辨力。
**✅ 實測 820 對裡有重疊卻比例不足者僅 4 對，🚨 而那一對是 6／6 全中。**

## 🚨 本輪的第二個坑：同一個控制字元又來了

⚠️ 改 `Table 1` 那條樣式時，word boundary **又被塌成 0x08（backspace）**，
🚫 於是它對 `Table 1` 永遠不命中，**而畫面上「判不了 442 對」一個字都沒變**——
🚨 看起來像是「表格裡根本沒東西」。
**✅ 第 576 輪已在 n576 立過同一道探針，本支當時沒裝，於是同一個坑踩第二次；已補。**
⚠️ 成因是**寫檔的方式**：經 shell 傳遞的 Python 字面會把 `\\b` 塌成 `\b`（backspace），
**✅ 故含反斜線的樣式一律改用檔案編輯工具寫，🚫 不經 shell。**

## 🚫 本支不入輪次閘門，且不把數值寫進 repo

⚠️ 受試者特徵是論文內容；**✅ repo 內只留計數與 16 碼雜湊**，數值留私有根。
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n582_same_cohort_probe.json'
DETAIL = ROOT / 'extraction' / 'n582-cohort-values.json'
SCREEN = Path(__file__).resolve().parent / 'n580_study_vs_report.json'

# 平均 ± 標準差。⚠️ 兩種寫法都收：Unicode ± 與 ASCII 的 +/-、+-。
VALUE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:±|\+/-|\+-)\s*(\d+(?:\.\d+)?)')
# 🚨 只取受試者段落——⚠️ 標題是自由文字故比對寬鬆，
# **🚫 但不退回全文**：退回去等於拿結果數值來比。
PARTICIPANT = re.compile(r'participant|subject|volunteer', re.I)
# 🚨 第 583 輪加：12 篇的受試者特徵**寫在表格裡**，文字段落一個 ± 都沒有。
# ⚠️ 而慣例上 Table 1 就是受試者特徵表。**🚫 但那只是慣例，不是保證**——
# ✅ 故第二來源獨立記帳，且**由巧合率探針當守門員**：
# 🚨 若加了它之後「只相同 1 個值」的配對暴增，就代表它抓進來的是結果不是受試者。
# 🚨 「(1|i) 後面不接數字」是為了不讓 Table 1 吃到 Table 10／Table 12。
TABLE_ONE = re.compile(r'^\s*table\s*(1|i)(?![0-9])', re.I)
TABLE_VALUE_CAP = 20    # 🚨 超過就判定那張不是受試者特徵表
MIN_COMPARABLE = 2      # 兩邊各至少要有這麼多個值，「零相同」才說得出「不同批」


def cohort_values(candidate):
    doc = corpus.load_document(candidate)

    def values_of(match):
        text = ' '.join((section.text or '') for section in doc.sections
                        if match(str(section.title or '')))
        return {'%s±%s' % pair for pair in VALUE.findall(text)}, bool(text)

    from_text, had_section = values_of(lambda t: bool(PARTICIPANT.search(t)))
    from_table, _ = values_of(lambda t: bool(TABLE_ONE.match(t)))
    # 🚨 受試者特徵表只有幾個數值（年齡、身高、體重、VO₂max…）。
    # ⚠️ 實測有一篇的 Table 1 有 **84 個** ±——**那不是受試者表，是結果表。**
    # ✅ 故超過上限就整張不用，🚫 不從裡面挑——挑就等於本室在替論文決定哪幾個是特徵。
    if len(from_table) > TABLE_VALUE_CAP:
        return from_text, set(), had_section, len(from_table)
    return from_text, from_table, had_section, 0


def verdict(values_a, values_b):
    """✅ 這個判準**擅長排除**，🚫 不擅長證明。

    🚨 第 583 輪改為看**比例**而非個數。⚠️ 加進 Table 1 之後，
    有的論文一張表就有 84 個數值，**而數值愈多，純靠巧合撞到 2 個的機會愈大**——
    實測那樣會生出 4 對「相同 2 個」的假陽性。
    **✅ 同一批人的特徵，較小那一方應該幾乎全中**（本 run 找到的那一對是 6／6）。
    """
    both = len(values_a & values_b)
    smaller = min(len(values_a), len(values_b))
    ratio = both / smaller if smaller else 0.0
    if both >= 2 and ratio >= 0.5:
        return 'possible-same-cohort', both, ratio
    if len(values_a) >= MIN_COMPARABLE and len(values_b) >= MIN_COMPARABLE:
        return (('partial-overlap-not-same-cohort' if both
                 else 'different-cohort'), both, ratio)
    return 'undetermined-too-few-values', both, ratio


def main():
    ids, _ = corpus.acquired_roster()

    values, sources, no_section = {}, {}, []
    for candidate in ids:
        from_text, from_table, had_section, rejected = cohort_values(candidate)
        values[candidate[-16:]] = from_text | from_table
        sources[candidate[-16:]] = {'text': len(from_text),
                                    'table1': len(from_table),
                                    'table1RejectedAsTooLarge': rejected}
        if not had_section:
            no_section.append(candidate[-16:])

    screened = json.loads(SCREEN.read_text(encoding='utf-8'))
    flagged = {tuple(sorted(item['pair'])): item
               for item in screened['authorOverlapScreen']['flagged']}

    rows, counts = [], {}
    for a, b in combinations(sorted(values), 2):
        call, both, ratio = verdict(values[a], values[b])
        counts[call] = counts.get(call, 0) + 1
        # ⚠️ 只列出「有相同」或「署名篩選有標」的，🚫 820 對全列沒有用。
        if both or (a, b) in flagged:
            item = flagged.get((a, b))
            rows.append({
                'pair': [a, b], 'identicalValues': both,
                'matchedFractionOfSmaller': round(ratio, 3), 'verdict': call,
                'valuesAvailable': [len(values[a]), len(values[b])],
                'inAuthorScreen': item is not None,
                'sharedAuthors': item['sharedAuthors'] if item else 0,
                'sameFirstAuthor': bool(item and item['sameFirstAuthor']),
                'sameLastAuthor': bool(item and item['sameLastAuthor']),
            })
    rows.sort(key=lambda r: (-r['identicalValues'], -r['sharedAuthors']))

    findings = [r for r in rows if r['verdict'] == 'possible-same-cohort']
    missed = [r for r in findings if not r['inAuthorScreen']]
    coincidental = counts.get('partial-overlap-not-same-cohort', 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    with_values = sum(1 for v in values.values() if v)
    probe('多數論文真的抽得到受試者數值（必觸發）',
          with_values >= len(ids) * 0.7,
          '🚨 抽不到的話，「零相同」只是沒東西可比；'
          '實得 %d／%d 篇有數值，%d 篇連受試者段落都沒認出來'
          % (with_values, len(ids), len(no_section)))
    # 🚨 第 583 輪加，而且是**本輪自己觸發的第二次**：改 Table 1 那條樣式時，
    # word boundary 又被塌成 0x08（backspace），⚠️ 於是它對 'Table 1' 永遠不命中，
    # **🚫 而畫面上「判不了 442 對」一個字都沒變——看起來像是這個來源沒東西。**
    # ✅ 第 576 輪已在 n576 立過同一道探針；🚨 本支當時沒裝，於是同一個坑踩第二次。
    malformed = [(name, repr(rx.pattern)) for name, rx in
                 (('VALUE', VALUE), ('PARTICIPANT', PARTICIPANT),
                  ('TABLE_ONE', TABLE_ONE))
                 if any(ord(c) < 32 for c in rx.pattern)]
    probe('樣式字面裡沒有控制字元（必觸發之反向）', not malformed,
          '🚨 控制字元會讓樣式永遠不命中，⚠️ 而「沒命中」看起來像是「沒東西」；'
          '實得壞掉的樣式 %d 條%s'
          % (len(malformed), ''.join('｜%s %s' % m for m in malformed)))
    probe('判準抓得到相同（必觸發之反向）',
          len({'30.3±6.5', '78.2±10.5'} & {'30.3±6.5', '78.2±10.5'}) == 2,
          '🚨 以兩組相同的合成數值試比對；⚠️ 抓不到的話，'
          '所有「零相同」都只是比對沒動')
    # 🚨 必觸發：判準要真的在真實資料上說過「不同批」，
    # ⚠️ 否則它可能只是對每一對都回「不知道」。
    probe('判準在真實資料上排除得掉（必觸發）',
          counts.get('different-cohort', 0) > 0,
          '✅ 實得判為「不同批」者 %d 對；🚨 若為零，代表它只會說「不知道」'
          % counts.get('different-cohort', 0))
    # ⚠️ 巧合率：只共用 1 個數值的配對有多少。🚨 這個數字大，「相同 2 個」就沒意義。
    probe('巧合率低（有部分重疊但判為不同批者很少）', coincidental <= 15,
          '⚠️ 820 對裡有重疊卻比例不足者 %d 對；'
          '🚨 若這個數字大，「相同 ≥2 個」就不代表同一批人' % coincidental)

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'cohort-values-private',
         'values': {k: sorted(v) for k, v in values.items()}},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'same-cohort-probe',
        'question': '哪兩篇報告的是同一批受試者',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'method': ('✅ 只比對 Participants／Subjects 段落裡的「平均 ± 標準差」字串。'
                   '🚫 不看全文——⚠️ 結果段落裡也有幾百個 ±。'),
        'corpusSize': len(ids),
        'reportsWithValues': with_values,
        'reportsWithoutParticipantSection': no_section,
        'verdictCounts': counts,
        'valueSources': sources,
        'tableValueCap': TABLE_VALUE_CAP,
        'possibleSameCohort': len(findings),
        'missedByAuthorScreen': len(missed),
        'headline': (
            '🚨 找到一對報告同一批受試者的論文，⚠️ 而第 581 輪的署名篩選看不見它：'
            '該對其中一篇只抽得到 1 位作者（GROBID 未解出作者清單），'
            '故「共有 ≥2 位作者」永遠不可能成立。'
            '🚨 第 581 輪報的「作者涵蓋率 41／41」量的是有沒有，不是完不完整。'),
        'rows': rows,
        'whatThisCannotDo': [
            '🚨 證明兩篇**是**同一批人——⚠️ 數值相同也可能是巧合或抄寫；'
            '✅ 但它能**排除**：數字不同就不是同一批。',
            '⚠️ 只看受試者段落；🚨 若一篇把特徵寫在表格而非文字裡本支看不到，'
            '🚫 那時「零相同」不代表不同批（已另立 undetermined 一類）。',
        ],
        'detailKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n582 是不是同一批受試者 ===')
    print('   %d 篇中 %d 篇抽得到受試者數值｜%d 篇沒認出受試者段落'
          % (len(ids), with_values, len(no_section)))
    print('   判定分布：%s' % counts)
    print('   🚨 可能同一批：%d 對，其中署名篩選漏掉 %d 對'
          % (len(findings), len(missed)))
    for r in rows[:14]:
        print('   %s %s ↔ %s：相同 %d（可比 %d／%d，佔小者 %.0f%%）'
              '｜%s｜署名共同 %d%s%s'
              % ('🚨' if r['verdict'] == 'possible-same-cohort' else '  ',
                 r['pair'][0], r['pair'][1], r['identicalValues'],
                 r['valuesAvailable'][0], r['valuesAvailable'][1],
                 100 * r['matchedFractionOfSmaller'],
                 r['verdict'], r['sharedAuthors'],
                 '＋同第一' if r['sameFirstAuthor'] else '',
                 '＋同末位' if r['sameLastAuthor'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（數值留私有根：%s）' % (OUT.name, DETAIL.name))
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
