"""n+50 乙：單向棘輪重篩覆蓋層之寫入器。

把棘輪做成**程式強制**而非人工遵守——違反方向的轉換會被 assert 擋下，
寫不進檔案。這樣即使判讀時一時疏忽，也不可能污染統計。

允許（n+50 裁定表）：
  exclude  -> advance   （相關性提高，reset window，不利於停止）
  unclear  -> advance   （同上）
  exclude  -> unclear   （不確定性提高，計為命中，不利於停止）
拒絕：
  unclear  -> exclude   （不確定性降低）
  advance  -> 任何降級
  任何 -> 原值相同者（無意義，應直接省略）

輸出：post-ruling-abstract-rescreen.json（第二層覆蓋，
不動 n+43 已凍結之 post-ruling-reclassification.json）。

用法：python .scratch/n50_ratchet.py <changes.json>
  changes.json = [{"candidateId":..., "newDecision":"advance"|"unclear",
                   "reason":"..."}]
"""
import json, os, sys

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = OUT + '/post-ruling-abstract-rescreen.json'

ALLOWED = {('exclude', 'advance'), ('unclear', 'advance'),
           ('exclude', 'unclear')}


def _term_stat():
    """以生產程式重算目前之 pScore／windowSize（n+52 防呆用）。"""
    import subprocess, re
    out = subprocess.run(
        ['python', '-X', 'utf8', '.scratch/term.py'],
        capture_output=True, text=True, encoding='utf-8',
        env={**os.environ,
             'AHIG_PRIVATE_ROOT': r'C:/Users/User/Desktop/claude/ahig-private'})
    m = re.search(r'\{"pScore".*\}', out.stdout)
    return json.loads(m.group(0)) if m else None


def effective_before():
    """重篩前之有效標記：judgements + n+43 凍結覆蓋層。"""
    d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
    op = {e['candidateId']: e['opinion'] for e in d['entries']}
    rc = OUT + '/post-ruling-reclassification.json'
    if os.path.exists(rc):
        for e in json.load(open(rc, encoding='utf-8'))['entries']:
            cid = e['candidateId']
            assert op[cid] == e['originalOpinion'], 'overlay mismatch ' + cid
            op[cid] = e['effectiveDecision']
    return op


def main():
    changes = json.load(open(sys.argv[1], encoding='utf-8'))
    before = effective_before()

    w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
    page = {it['candidateId']: it['page'] for it in w['items']}
    # 重篩母體：worksheet 中原本無摘要者（n+51：不再以頁次劃分）
    noabs_ids = {it['candidateId'] for it in w['items']
                 if not (it.get('abstract') or '').strip()}

    entries, seen = [], set()
    for c in changes:
        cid, new = c['candidateId'], c['newDecision']
        assert cid not in seen, 'duplicate in changes: ' + cid
        seen.add(cid)
        assert cid in before, 'not judged: ' + cid
        old = before[cid]
        # 棘輪強制：方向不合者直接中止，不寫檔
        assert (old, new) in ALLOWED, (
            'RATCHET VIOLATION %s: %s -> %s (allowed: %s)'
            % (cid, old, new, sorted(ALLOWED)))
        # n+51（二）撤銷 n+50 之區段劃分：重篩範圍改為
        # **全體已判之無摘要記錄**。故此處改驗「該筆原本無摘要」，
        # 不再驗頁次——有摘要者本就不在重篩母體內。
        assert cid in noabs_ids, (
            'not a no-abstract record, outside rescreen population: %s page %s'
            % (cid, page[cid]))
        entries.append({
            'candidateId': cid,
            'originalOpinion': old,
            'effectiveDecision': new,
            'ruling': 'n+50',
            'tag': 'abstract-rescreen',
            'note': c['reason'],
        })

    # n+52（一）防呆：協調者更正了「棘輪不可能誘發終止」之論證。
    # 落在尾端窗口「之外」的新增命中會使 k_min 變大、pScore 反而下降
    # （方向輕微有利於停止），故須記錄套用前後之 pScore／windowSize。
    before_stat = _term_stat()

    doc = {
        'schemaVersion': 1,
        'source': 'standard-full-screen-pass-1',
        'ruling': 'n+50 (乙) one-way ratchet re-screen after abstract enrichment',
        'producedBy': 'claude-opus-5[1m] executor-session',
        'semantics': (
            'Second overlay layer, applied AFTER '
            'post-ruling-reclassification.json. Only ratchet-allowed '
            'transitions are representable: exclude/unclear->advance and '
            'exclude->unclear; unclear->exclude and any advance downgrade '
            'are rejected at write time. NOTE (n+52 section 1): the earlier '
            'claim that this "cannot mathematically be used to induce '
            'termination" was WRONG and is retracted. Upgrades inside the '
            'trailing window zero it (strongly anti-stopping), but upgrades '
            'OUTSIDE the window raise k_min and therefore LOWER pScore '
            '(mildly pro-stopping). The ratchet remains conservative on '
            'balance, not by construction. Every application records pScore '
            'and windowSize before/after; a batch crossing alpha halts.'),
        'segment': 'all judged no-abstract records (n+51)',
        'entries': entries,
    }
    json.dump(doc, open(DEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    from collections import Counter
    c = Counter('%s->%s' % (e['originalOpinion'], e['effectiveDecision'])
                for e in entries)
    print('wrote', len(entries), 'entries to post-ruling-abstract-rescreen.json')
    print('transitions:', dict(c))

    after_stat = _term_stat()
    if before_stat and after_stat:
        pb, pa = before_stat['pScore'], after_stat['pScore']
        wb, wa = before_stat['windowSize'], after_stat['windowSize']
        print('pScore  %.6f -> %.6f  (delta %+.6f)' % (pb, pa, pa - pb))
        print('window  %d -> %d' % (wb, wa))
        ALPHA = 0.05
        if pb >= ALPHA > pa:
            print('!! STOP: pScore crossed alpha (%.3f). Halt and report.'
                  % ALPHA)
            sys.exit(3)
        if pa < pb:
            print('note: pScore decreased — expected when upgrades fall '
                  'outside the trailing window (n+52 section 1).')


if __name__ == '__main__':
    main()
