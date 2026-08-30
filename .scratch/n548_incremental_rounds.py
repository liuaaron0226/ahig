# -*- coding: utf-8 -*-
"""**逐頁讀完 18 輪的中途長什麼樣。**（第 548 輪）

## 🚨 第三條「現實不會走的路」

前兩輪各抓到一條：整份寫入（第 546）、替身形狀相同（第 547）。
**⚠️ 第三條是：我每次都在「全部讀完」之後才跑鏈。**

**🚨 而 session 路線的真實樣子是：讀一頁 → 併回去 → 再跑，重複 18 次。**
中途的每一次跑，都有 38 篇還沒有清冊。**⚠️ 那時候收據長什麼樣，沒有人看過。**

## ✅ 本支就是把那 18 輪真的走一次

每一頁：造該頁的替身清冊 → `append_drafts` → 跑鏈兩次
（**一次餵全部 41 篇，一次只餵已讀的**）→ 記下兩份收據的差別。

## 🚫 一樣不落盤

替身的清冊是編造的，**🚫 `store=None`**；工作單帶全文，**✅ 驗完刪除**（同 n540）。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ahig.contracts.freeze import content_hash, verify_frozen  # noqa: E402
from ahig.extraction import run_inventory, worksheet  # noqa: E402
from ahig.extraction.corpus import iter_acquired, reading_request_for  # noqa: E402

from n537_chain_rehearsal import REHEARSAL  # noqa: E402
from n547_varied_shapes import varied_reader  # noqa: E402

CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
OUT = Path(__file__).resolve().parent / 'n548_incremental_rounds.json'
DRYRUN_DIR = ROOT / 'extraction-incremental-dryrun'


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    if not (contract.get('status') == 'frozen'
            and verify_frozen(contract, 'scopeContractHash')):
        print('🚨 契約不是可用的凍結契約，拒絕演練', file=sys.stderr)
        sys.exit(2)
    if DRYRUN_DIR.exists():
        print('🚨 %s 已存在——🚫 本支只刪自己建的，故拒絕跑' % DRYRUN_DIR.name,
              file=sys.stderr)
        sys.exit(2)

    requests = [reading_request_for(d.candidate_id, contract)
                for _n, d, _e in iter_acquired() if d is not None]
    by_report = {r.report: r for r in requests}
    order = {r.report: i for i, r in enumerate(requests)}
    cap = contract['extractionPolicy']['maxStudyResultsPerStudy']

    def shape_of(request):
        i = order[request.report]
        if i == 0:
            return cap + 1, 1
        if i == 1:
            return 0, 2
        return i % 4 + 1, 1

    read = varied_reader(shape_of)

    sheet = worksheet.write_worksheet(DRYRUN_DIR, requests, source='n548')
    rounds, drafted = [], []
    try:
        for number in range(1, sheet['pageCount'] + 1):
            page = worksheet.page(DRYRUN_DIR, number)
            entries = [read(by_report[item['report']]) for item in page['items']]
            merged = worksheet.append_drafts(
                DRYRUN_DIR, entries, read_by={'agentClass': 'model',
                                              'note': REHEARSAL})
            drafted.extend(item['report'] for item in page['items'])

            loaded = worksheet.load_drafts(DRYRUN_DIR, require_complete=False)
            reader = worksheet.reader_from(loaded['drafts'])

            # 🚨 store=None：編造的清冊一份都不落盤。
            all_run = run_inventory(contract, reader=reader,
                                    candidate_ids=list(by_report))
            only_run = run_inventory(contract, reader=reader,
                                     candidate_ids=list(drafted))

            rounds.append({
                'page': number,
                'itemsThisPage': page['itemCount'],
                'draftedSoFar': merged['draftedCount'],
                'remaining': len(merged['remaining']),
                'feedAll': {'attempted': all_run.attempted,
                            'succeeded': len(all_run.succeeded),
                            'failed': len(all_run.failed),
                            'byStage': all_run.failures_by_stage()},
                'feedDraftedOnly': {'attempted': only_run.attempted,
                                    'succeeded': len(only_run.succeeded),
                                    'failed': len(only_run.failed)},
                # 🚫 訊息裡有完整 candidateId；照 .scratch 既有慣例只留末 16 碼。
                'firstFailureReason': (
                    all_run.failed[0].error.replace(
                        all_run.failed[0].candidate_id,
                        '…' + all_run.failed[0].candidate_id[-16:])[:110]
                    if all_run.failed else ''),
            })
    finally:
        expected_files = {'worksheet.json', 'drafts.json'}
        if DRYRUN_DIR.exists():
            files = {p.name for p in DRYRUN_DIR.iterdir() if p.is_file()}
            dirs = {p.name for p in DRYRUN_DIR.iterdir() if p.is_dir()}
            if files <= expected_files and dirs <= {'pages'}:
                shutil.rmtree(DRYRUN_DIR)

    last = rounds[-1]
    mid = rounds[len(rounds) // 2]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('最後一輪全部讀完且全部跑完',
          last['remaining'] == 0 and last['feedAll']['succeeded'] == len(requests)
          and last['feedAll']['failed'] == 0,
          '第 %d 頁後：未讀 %d｜成功 %d｜失敗 %d'
          % (last['page'], last['remaining'], last['feedAll']['succeeded'],
             last['feedAll']['failed']))
    probe('中途餵全部時，未讀的那些一律記成 call-reader 失敗',
          mid['feedAll']['byStage'].get('call-reader')
          == len(requests) - mid['draftedSoFar'],
          '🚨 這是中途的常態，🚫 不是壞掉：第 %d 頁時已讀 %d，'
          'call-reader 失敗 %d'
          % (mid['page'], mid['draftedSoFar'],
             mid['feedAll']['byStage'].get('call-reader')))
    probe('中途只餵已讀的，就沒有失敗',
          all(r['feedDraftedOnly']['failed'] == 0 for r in rounds),
          '🚨 有失敗代表已讀的那些也跑不過；'
          '各輪失敗數 %s' % [r['feedDraftedOnly']['failed'] for r in rounds])
    probe('已讀數逐輪嚴格遞增（必觸發）',
          all(b['draftedSoFar'] > a['draftedSoFar']
              for a, b in zip(rounds, rounds[1:])),
          '🚨 不遞增代表 append_drafts 沒真的併進去；'
          '軌跡 %s' % [r['draftedSoFar'] for r in rounds])
    probe('未讀者的失敗訊息說得出是「沒有這一篇」',
          '沒有這一篇' in (mid['firstFailureReason'] or ''),
          '🚨 訊息若含糊，中途的收據會被讀成資料壞了；實得：%s'
          % mid['firstFailureReason'])
    probe('工作單已刪除', not DRYRUN_DIR.exists(),
          '⚠️ 帶全文，留著等於私有根多一份語料副本')

    doc = {
        'schemaVersion': 1,
        'documentType': 'incremental-rounds-rehearsal',
        'ruling': '第 546–547 輪那把尺之第三條：中途的那些輪次',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'readerIsAStub': True,
        'stubMarker': REHEARSAL,
        'storeDisabled': '🚨 store=None——編造的清冊一份都不落盤',
        'pages': sheet['pageCount'],
        'records': len(requests),
        'rounds': rounds,
        'finding': (
            '⚠️ 中途每一輪若餵全部 41 篇，收據上會有 41−N 筆 call-reader 失敗，'
            '訊息是「工作單收回來的清冊裡沒有這一篇」。'
            '🚨 那是中途的**常態**，不是壞掉——但收據長得跟真的壞掉一樣。'
            '✅ 只餵已讀的那些就沒有失敗；'
            '🚫 而目前沒有任何東西告訴呼叫端該這樣做。'),
        'recommendation': (
            '⚠️ 不改程式。`load_drafts(require_complete=False)` 已經回 `drafts` 與'
            '`remaining`，呼叫端拿 `list(loaded["drafts"])` 當 candidate_ids 即可。'
            '🚨 但這件事只寫在本產物裡是不夠的——✅ 已補進 `worksheet.load_drafts` '
            '的說明，讓要用的人在函式旁邊就看得到。'),
        'notProven': ['🚨 抽得準不準：替身編造。',
                      '⚠️ 形狀由序位決定，🚫 不是真實論文的分布。'],
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n548 逐頁 18 輪的中途 ===')
    print('   頁數 %d｜語料 %d 篇' % (sheet['pageCount'], len(requests)))
    print('   已讀軌跡：%s' % [r['draftedSoFar'] for r in rounds])
    print('   餵全部：成功 %s' % [r['feedAll']['succeeded'] for r in rounds])
    print('   餵全部：失敗 %s' % [r['feedAll']['failed'] for r in rounds])
    print('   只餵已讀：失敗 %s'
          % [r['feedDraftedOnly']['failed'] for r in rounds])
    print('   中途失敗訊息：%s' % mid['firstFailureReason'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
