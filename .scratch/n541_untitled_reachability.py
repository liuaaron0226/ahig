# -*- coding: utf-8 -*-
"""**取得階段交下來的那兩項限制，在萃取這一端到底會不會咬人。**（第 541 輪）

## 交辦內容（`m1-g-acquisition-skeleton.md`）

> | 無標題之節 | **🚨 這些節無法用標題定位**——萃取若以節名尋找「方法」「結果」，會找不到 |
> | 首節即無標題者 | ⚠️ 通常表示摘要或前言未被標出，**🚨 而那正是最常被取用的一段** |
>
> **🚫 這兩項不由取得端處置**——**⚠️ 如何在無標題時定位，是萃取階段的判準問題。**

## ✅ 先查一件事實，再決定要不要造東西

那段警語的前提是「**萃取若以節名尋找**」。**⚠️ 而本鏈根本不以節名尋找**：
`prompt_payload()` 送的是**整份 content**，`sections_titled` 全鏈無人呼叫
（只有測試在用）。

> **🚨 故這項限制目前是「未被觸發」，不是「已被處置」。**
> **⚠️ 兩者差別很大**：前者會在有人改成「只送選定章節」的那一天立刻復活。
> **✅ 本支把它量成一句可查核的話，🚫 而不是順手造一個定位器來「解決」它**——
> 爬梯子第一階：**現在不需要那東西存在。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 證得了：無標題節的**文字**確實在送出去的 payload 裡，且偏移對得上。
- ✅ 證得了：`sections_titled` 確實找不到它們（必觸發：有標題的照樣找得到）。
- 🚨 證不了：**模型看得到就抓得到**——⚠️ 那要真的讀才知道。
- 🚨 證不了：改成分段送之後會怎樣。**⚠️ 那正是這項限制復活的條件。**

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction.corpus import (UNTITLED, iter_acquired,  # noqa: E402
                                    reading_request_for, sections_titled)

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
N492 = Path(__file__).resolve().parent / 'n492_stratum_table.json'
OUT = Path(__file__).resolve().parent / 'n541_untitled_reachability.json'


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))

    records, untitled_total, leading = [], 0, 0
    text_missing, offset_bad, content_truncated = [], [], []
    found_by_title = 0

    for name, document, _error in iter_acquired():
        if document is None:
            continue
        untitled = [s for s in document.sections if s.is_untitled]
        untitled_total += len(untitled)
        is_leading = bool(document.sections) and document.sections[0].is_untitled
        leading += is_leading

        request = reading_request_for(document.candidate_id, contract)
        payload = request.prompt_payload()

        # 1. 送出去的 content 是不是整份（🚨 這才是「不會咬人」所依賴的那件事）
        if payload['content'] != document.content:
            content_truncated.append(name[-16:])

        # 2. 無標題節的文字，在送出去的那份 content 裡找得到嗎；偏移對不對
        for section in untitled:
            if section.text and section.text not in payload['content']:
                text_missing.append(name[-16:])
            sliced = document.content[section.start_offset:section.end_offset]
            if sliced != section.text:
                offset_bad.append(name[-16:])

        # 3. 用標題找它們——應該一個都找不到
        if untitled and sections_titled(document, UNTITLED):
            found_by_title += 1

        records.append({
            'dir': name[-16:],
            'sections': len(document.sections),
            'untitled': len(untitled),
            'leadingUntitled': is_leading,
            'untitledChars': sum(len(s.text) for s in untitled),
        })

    with_untitled = [r for r in records if r['untitled']]

    # 正向對照：有標題的節照樣找得到，否則上面那個「找不到」沒有意義。
    positive = 0
    for _n, document, _e in iter_acquired():
        if document is None:
            continue
        titles = [s.title for s in document.sections if not s.is_untitled]
        if titles and sections_titled(document, titles[0]):
            positive += 1

    probes = []

    def probe(pname, ok, detail):
        probes.append({'probe': pname, 'passed': bool(ok), 'detail': detail})

    probe('送出去的是整份 content（🚨 這項限制之所以未被觸發的原因）',
          not content_truncated,
          '🚨 若哪天改成只送選定章節，這項限制立刻復活；'
          '目前被截斷者 %d 篇' % len(content_truncated))
    probe('無標題節的文字確實在送出去的那份 content 裡',
          not text_missing,
          '找不到者 %d 處' % len(text_missing))
    probe('無標題節的偏移切得出同一段文字',
          not offset_bad, '不符者 %d 處' % len(offset_bad))
    probe('用標題找無標題節，一篇都找不到（必觸發之反向）',
          found_by_title == 0,
          '🚨 若找得到，代表 UNTITLED 不是真的預設值；實得 %d 篇' % found_by_title)
    probe('而有標題的節照樣找得到（必觸發之正向）',
          positive == len(records),
          '🚨 沒有這一條，上一條在「什麼都找不到」時一樣會綠；'
          '實得 %d／%d' % (positive, len(records)))

    # 併查 n+144 之遞延：S3 現況（🚨 兩個母體，兩個答案）
    strata = json.loads(N492.read_text(encoding='utf-8'))
    s3 = next((row for row in strata['rows'] if row['pool'].startswith('S3')), {})

    doc = {
        'schemaVersion': 1,
        'documentType': 'untitled-section-reachability',
        'ruling': 'm1-g 交辦萃取階段之兩項既知限制',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'population': '私有根 fulltext/ 內所有 acquired',
        'privateRoot': PROV,
        'counts': {
            'records': len(records),
            'untitledSections': untitled_total,
            'recordsWithUntitled': len(with_untitled),
            'recordsWithLeadingUntitled': leading,
            'untitledChars': sum(r['untitledChars'] for r in records),
        },
        'verdict': {
            'status': 'not-triggered',
            'why': ('🚨 本鏈不以節名尋找：`prompt_payload()` 送整份 content，'
                    '而 `sections_titled` 全鏈無人呼叫（只有測試在用）。'
                    '⚠️ 故無標題節的文字照樣送得出去。'),
            'notTheSameAsHandled': ('🚨 「未被觸發」不等於「已被處置」——'
                                    '⚠️ 有人把送法改成「只送選定章節」的那一天，'
                                    '這項限制會立刻復活。'),
            'whyNothingWasBuilt': ('✅ 爬梯子第一階：現在不需要一個「無標題定位器」'
                                   '存在。🚫 造了它等於為一個尚未成立的需求寫程式，'
                                   '而它會看起來像已經解決了什麼。'),
        },
        'alsoDeferredToThisStage': {
            'ruling': 'n+144（三之處置 2）：萃取階段開始時若 S3 仍為空，'
                      '須以校準集以外之 TTE 紀錄執行同一檢查',
            's3Row': s3,
            'twoPopulationsTwoAnswers': (
                '🚨 校準 60 之 S3 取得數為 %s（**仍為空**）；'
                '而含補抽之 S3 取得數為 %s（**不為空**）。'
                '⚠️ 該遞延條款沒有指明是哪一個母體——'
                '🚨 而本 run 一路在抓的正是混母體。**故不由本室自行選一個。**'
                % (s3.get('acquiredCalibration60'), s3.get('acquiredWithBackfill'))),
            'alsoUndecided': ('⚠️ 「萃取階段開始」是否已發生亦未定義：'
                             '確定性鏈已建成並在真語料上演練過，'
                             '🚨 但一篇論文都還沒有被讀。'),
        },
        'controlProbes': probes,
        'records': with_untitled,
        'recordsNote': '🚫 只列出含無標題節者；其餘 %d 篇無。'
                       % (len(records) - len(with_untitled)),
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n541 無標題節在萃取端的可及性 ===')
    print('   %d 篇｜無標題節 %d 個，分布於 %d 篇｜首節即無標題者 %d 篇'
          % (len(records), untitled_total, len(with_untitled), leading))
    print('   那些節合計 %d 字元，全部隨整份 content 送出'
          % doc['counts']['untitledChars'])
    print('   判定：**未被觸發**（🚫 不等於已被處置）')
    print('   併查 S3（n+144 遞延）：校準 60 為 %s｜含補抽為 %s'
          % (s3.get('acquiredCalibration60'), s3.get('acquiredWithBackfill')))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
