# -*- coding: utf-8 -*-
"""**真的要送出去的那一串，到底多長。**（第 535 輪）

## 🚨 為什麼還要再量一次

n+184 已經把「讀 41 篇要多少錢」從「不知道」變成一個實測導出的區間，
**✅ 那是對的，而且解開了擁有者的決定。** ⚠️ 但它量的是**正文字元數**，
再加上一個**估計的**固定開銷（「≈ 2,042,415，開銷佔 3.0%」）。

**🚨 而真正會被送出去的不是正文，是 `DraftRequest.prompt_payload()` 序列化後的那一串。**
它另含：章節標題清單、**範圍契約裡的 6 個結局**（`contractOutcomesForReference`）、
任務描述與回傳形狀、以及 JSON 本身的引號與跳脫。

⚠️ 那個 3.0% 是估的。**✅ 本支把它量出來**——🚫 不是為了推翻 n+184，
而是因為**現在量得到，而量得到的東西不該繼續用估的**。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 量得到：以**真的那份凍結契約**組出的請求，序列化後的字元數，逐篇一筆。
- 🚨 量不到：**token 數與金額**。⚠️ 換算率與牌價此處皆無憑據
  （n+184 自己也這麼說），🚫 故本支一個字都不寫。
- 🚨 量不到：**分段之後**會變成幾次呼叫。⚠️ 現行行為是整份一次送，本支照它量。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門**，與 n+184 同類：一次性試算。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.extraction.corpus import iter_acquired, reading_request_for  # noqa: E402
from ahig.contracts.freeze import content_hash, verify_frozen  # noqa: E402

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
N184_ESTIMATE = 2042415          # n+184 之「加上每篇固定開銷與章節標題」
N184_CONTENT = 1981436           # n+184 之正文字元數（第 530 輪實測）

OUT = Path(__file__).resolve().parent / 'n535_reading_payload.json'


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if contract.get('status') != 'frozen':
        print('🚨 契約不是 frozen，拒絕以它量測', file=sys.stderr)
        sys.exit(2)
    if not verify_frozen(contract, 'scopeContractHash'):
        print('🚨 契約雜湊驗不過，拒絕以它量測', file=sys.stderr)
        sys.exit(2)

    records, unreadable = [], []
    for name, document, error in iter_acquired():
        if document is None:
            unreadable.append({'dir': name[-16:], 'error': error})
            continue
        request = reading_request_for(document.candidate_id, contract)
        payload = request.prompt_payload()
        full = len(json.dumps(payload, ensure_ascii=False))
        # 把 content 換成空字串再量一次：兩者之差就是**量到的**固定開銷，
        # 🚫 不是估的。⚠️ 同時它是一道必觸發控制——若這個差不隨正文變動，
        # 🚨 代表這個數字量的不是正文。
        bare = len(json.dumps(dict(payload, content=''), ensure_ascii=False))
        records.append({
            'dir': name[-16:],
            'sourceType': document.route,
            'sections': len(document.sections),
            'contentChars': len(document.content),
            'payloadChars': full,
            'overheadChars': bare,
            'contentAsJsonChars': full - bare,
        })

    records.sort(key=lambda r: r['payloadChars'])
    total_content = sum(r['contentChars'] for r in records)
    total_payload = sum(r['payloadChars'] for r in records)
    total_overhead = sum(r['overheadChars'] for r in records)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每篇 payload 都大於其正文',
          all(r['payloadChars'] > r['contentChars'] for r in records),
          '否則正文根本沒進去')
    probe('固定開銷隨正文變動則為誤（必觸發）',
          len({r['overheadChars'] for r in records}) > 1,
          '開銷含章節標題清單，故本應逐篇不同；'
          '🚨 若全部相同，代表章節標題沒被算進去')
    probe('正文的 JSON 形式不小於原字元數',
          all(r['contentAsJsonChars'] >= r['contentChars'] for r in records),
          '跳脫只會變長，不會變短')
    # 🚨 第一版這條拿 PROV['artifactDirectoriesSeen'] 來比，當場紅：
    # ⚠️ 那個數是 fulltext/ 內**所有** artifact 目錄（311），
    # 🚨 而本支的母體是其中 status=acquired 的那些。
    # ✅ 對照的對象換成獨立走一次目錄數出來的 acquired 數——
    # 那才是 iter_acquired 若漏掉幾篇會現形的那個數。
    acquired_on_disk = 0
    for entry in (ROOT / 'fulltext').iterdir():
        manifest = entry / 'manifest.json'
        if not (entry.is_dir() and manifest.exists()):
            continue
        try:
            if json.loads(manifest.read_text(encoding='utf-8')
                          ).get('status') == 'acquired':
                acquired_on_disk += 1
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    probe('走訪所得篇數等於磁碟上 status=acquired 之數',
          len(records) + len(unreadable) == acquired_on_disk,
          '磁碟 %d｜走訪 %d（含讀不了的 %d）；'
          '⚠️ 目錄總數 %d 不是本支母體'
          % (acquired_on_disk, len(records) + len(unreadable), len(unreadable),
             PROV['artifactDirectoriesSeen']))
    probe('正文總數與 n+184 所報相同',
          total_content == N184_CONTENT,
          '本支 %d｜n+184 %d' % (total_content, N184_CONTENT))

    doc = {
        'schemaVersion': 1,
        'documentType': 'reading-payload-measurement',
        'ruling': 'n+184（讀論文那一端的價錢）之後續：把估的那 3.0% 量出來',
        'notAGate': '🚫 本支不入輪次閘門（n+181 三已裁定停止加機檢）；與 n+184 同類',
        'contract': {
            'path': CONTRACT_PATH.relative_to(REPO).as_posix(),
            'scopeContractId': contract.get('scopeContractId'),
            'scopeContractHash': contract.get('scopeContractHash'),
            'frozenVerified': True,
            'inScopeOutcomes': len(contract.get('inScopeOutcomes') or []),
        },
        'population': '私有根 fulltext/ 內所有 acquired（🚨 非校準 60，非 84）',
        'privateRoot': PROV,
        'measured': {
            'records': len(records),
            'unreadable': len(unreadable),
            'contentChars': total_content,
            'payloadChars': total_payload,
            'overheadChars': total_overhead,
            'overheadPct': round(100.0 * total_overhead / total_payload, 2),
            'minPayload': records[0]['payloadChars'] if records else 0,
            'medianPayload': (records[len(records) // 2]['payloadChars']
                              if records else 0),
            'maxPayload': records[-1]['payloadChars'] if records else 0,
        },
        'versusN184': {
            'n184Estimate': N184_ESTIMATE,
            'n184OverheadPctAssumed': 3.0,
            'measuredTotal': total_payload,
            'differenceChars': total_payload - N184_ESTIMATE,
            'differencePct': round(100.0 * (total_payload - N184_ESTIMATE)
                                   / N184_ESTIMATE, 2),
            'note': ('🚨 差額若為正，代表 n+184 低估了送出去的量；'
                     '⚠️ 但量級是否改變要看區間，不看這個百分比。'),
        },
        'notMeasured': [
            '🚨 token 數：無分詞器，🚫 不換算。',
            '🚨 金額：牌價與匯率此處無憑據（n+184 自陳），🚫 不寫。',
            '🚨 回來的清冊有多長：那要模型真的讀過才知道，⚠️ 目前是猜的。',
            '🚨 讀錯要重來幾次：本支只算「讀一趟」。',
        ],
        'controlProbes': probes,
        'records': records,
        'unreadable': unreadable,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n535 送出字串之實測（真契約 × 真語料）===')
    print('   契約 %s（frozen ✅）' % contract.get('scopeContractId'))
    print('   篇數 %d｜讀不了 %d' % (len(records), len(unreadable)))
    print('   正文合計   %10d 字元' % total_content)
    print('   payload    %10d 字元' % total_payload)
    print('   固定開銷   %10d 字元（%.2f%%）'
          % (total_overhead, doc['measured']['overheadPct']))
    print('   最小／中位／最大 payload：%d／%d／%d'
          % (doc['measured']['minPayload'], doc['measured']['medianPayload'],
             doc['measured']['maxPayload']))
    print('   對照 n+184 之 %d：差 %+d（%+.2f%%）'
          % (N184_ESTIMATE, doc['versusN184']['differenceChars'],
             doc['versusN184']['differencePct']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
