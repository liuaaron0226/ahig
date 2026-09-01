# -*- coding: utf-8 -*-
"""**語料只涵蓋篩選通過者的一成三，而缺的那塊集中在同一個年代。**（第 625 輪）

## 🚨 承第 624 輪：分母寫下來之後，下一個問題是「缺的是隨機的嗎」

⚠️ 第 624 輪查明語料 41 篇的分母沒被寫下來。**🚫 但「少」本身不是問題**——
**🚨 問題是「少掉的那些有沒有系統性地長得不一樣」。**

> **⚠️ 若缺的是隨機的，結論只是精度差；🚨 若缺的集中在某個年代，那是選擇偏差。**

## ✅ 本支的做法

以**篩選第一關判 `advance` 的 310 篇**為分母（🚨 而非全庫 311，那是取文碰過的集合），
逐年代算取得率。**⚠️ 並加一道抗分箱操弄的穩健性探針**——
🚨 分箱是本室自己選的，若換一種分法結論就變，那結論是分箱做出來的，不是資料。

## 🚫 本支不送任何外部請求、不改任何產品程式、不印任何題名
"""
import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n625_corpus_era_bias.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'

BINS = [(0, 1999, '≤1999'), (2000, 2009, '2000-09'),
        (2010, 2019, '2010-19'), (2020, 2030, '2020+')]


def main():
    judgements = json.loads(
        (RUN / 'standard-full-screen-pass-1/judgements.json')
        .read_text(encoding='utf-8'))
    opinion = {e['candidateId']: e['opinion'] for e in judgements['entries']}
    advance = {c for c, o in opinion.items() if o == 'advance'}

    pool = {r['candidateId']: r for r in json.loads(
        (RUN / 'candidate-pool/candidates.json').read_text(encoding='utf-8'))}

    status = {}
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue  # ⚠️ 第 624 輪查明的舊命名孤兒，🚫 不計入
        path = entry / 'manifest.json'
        if path.exists():
            doc = json.loads(path.read_text(encoding='utf-8'))
            status[doc['candidateId']] = doc.get('status')
    acquired = {c for c, s in status.items() if s == 'acquired'}

    def year(cid):
        raw = pool.get(cid, {}).get('publicationYear')
        return int(raw) if raw else None

    def rate_table(bins):
        rows = []
        for lo, hi, label in bins:
            ids = [c for c in advance
                   if year(c) is not None and lo <= year(c) <= hi]
            got = [c for c in ids if c in acquired]
            rows.append({'era': label, 'advanced': len(ids),
                         'acquired': len(got),
                         'rate': round(100 * len(got) / len(ids), 1)
                         if ids else None})
        return rows

    rows = rate_table(BINS)
    # ⚠️ 穩健性：換成五年一箱，看「2000 年前為零」與遞增是不是分箱做出來的。
    fine_bins = [(y, y + 4, '%d-%d' % (y, y + 4)) for y in range(1975, 2026, 5)]
    fine = [r for r in rate_table(fine_bins) if r['advanced']]
    # 🚨 判斷「2000 年前」要用數值下界，不能拿標籤去比字串——
    # ⚠️ '1975-1979' < '2000' 只是字典序碰巧成立，換個標籤格式就靜靜地錯。
    fine_lower = {label: lo for lo, hi, label in fine_bins}
    fine_pre2000 = [r for r in fine if fine_lower[r['era']] < 2000]

    acquired_years = sorted(y for y in (year(c) for c in acquired)
                            if y is not None)
    pre2000_advanced = [c for c in advance
                        if year(c) is not None and year(c) < 2000]
    pre2000_acquired = [c for c in pre2000_advanced if c in acquired]
    # ⚠️ 光說「那個年代零代表」不夠——🚨 要說出它卡在哪，D18／D19 才有形狀。
    fingerprint = {}
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue
        path = entry / 'manifest.json'
        if path.exists():
            doc_m = json.loads(path.read_text(encoding='utf-8'))
            fingerprint[doc_m['candidateId']] = ' / '.join(
                '%s=%s' % (a.get('sourceId'), a.get('conclusion'))
                for a in (doc_m.get('attempts') or [])) or '（無嘗試）'

    def era_block(ids):
        return {
            '已取得': sum(1 for c in ids if status.get(c) == 'acquired'),
            '位置已知未取': sum(1 for c in ids
                                if str(status.get(c, '')).startswith('available')),
            'Unpaywall 從未被問': sum(
                1 for c in ids
                if fingerprint.get(c, '').endswith('unpaywall=blocked')),
            '三源實查皆無': sum(1 for c in ids
                                if status.get(c) == 'no-oa-fulltext'),
            '缺識別碼問不了': sum(
                1 for c in ids
                if 'not-applicable' in fingerprint.get(c, '')
                and status.get(c) != 'no-oa-fulltext'),
            '無清單': sum(1 for c in ids if c not in status),
        }

    era_blockers = {
        label: era_block([c for c in advance
                          if year(c) is not None and lo <= year(c) <= hi])
        for lo, hi, label in BINS}

    never_attempted = sorted(advance - set(status))
    acquired_not_advanced = sorted(acquired - advance)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('advance 集合非空且與已取得有交集（必觸發之正對照）',
          len(advance) > 0 and len(acquired & advance) > 0,
          '🚨 advance %d 篇、其中 %d 篇已取得；⚠️ 若交集為零，'
          '整張取得率表就沒有意義'
          % (len(advance), len(acquired & advance)))
    probe('以不存在的 opinion 查，計數為零（必觸發之反向）',
          sum(1 for o in opinion.values() if o == 'ZZ-不存在-ZZ') == 0,
          '🚨 若這也數得出東西，「advance 310」這個分母就不可信')
    probe('⚠️ 遞增不是分箱做出來的（穩健性）',
          (len(fine_pre2000) >= 4
           and all(r['acquired'] == 0 for r in fine_pre2000)),
          '🚨 換成五年一箱共 %d 箱（2000 年前 %d 箱、涵蓋 %d 篇 advance）：'
          '那些箱的取得數全為 0；⚠️ 若換個分法就不成立，'
          '那結論是分箱做出來的' % (len(fine), len(fine_pre2000),
                                    sum(r['advanced'] for r in fine_pre2000)))
    # 🚨 以下三道是紅燈——它們就是本支的發現。
    probe('語料涵蓋各年代',
          bool(pre2000_acquired),
          '🚨 篩選通過的 %d 篇 2000 年前文獻，語料裡有 %d 篇——'
          '⚠️ 語料最早的一篇是 %s 年'
          % (len(pre2000_advanced), len(pre2000_acquired),
             acquired_years[0] if acquired_years else '（無）'))
    probe('取得率與年代無關',
          len({r['rate'] for r in rows if r['rate'] is not None}) <= 1,
          '🚨 逐年代取得率：%s——**單調遞增**'
          % '｜'.join('%s %s%%' % (r['era'], r['rate']) for r in rows))
    probe('每一篇 advance 都至少被嘗試過取文',
          not never_attempted,
          '🚨 實得 %d 篇 advance **連一次取文嘗試都沒有**（無清單）：%s'
          % (len(never_attempted), [c[-16:] for c in never_attempted]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'corpus-era-bias-audit',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'screeningOpinionCounts': dict(
            collections.Counter(opinion.values()).most_common()),
        'advancedTotal': len(advance),
        'acquiredTotal': len(acquired),
        'acquiredWithinAdvanced': len(acquired & advance),
        'acquiredNotAdvancedAtPass1': [
            {'report': c[-16:], 'pass1Opinion': opinion.get(c, '（此關未判）')}
            for c in acquired_not_advanced],
        'coverageOfAdvanced': round(
            100 * len(acquired & advance) / len(advance), 1),
        'eraTable': rows,
        'eraBlockers': era_blockers,
        'fineBinTable': fine,
        'acquiredYearRange': [acquired_years[0], acquired_years[-1]]
        if acquired_years else None,
        'acquiredMedianYear': (statistics.median(acquired_years)
                               if acquired_years else None),
        'pre2000Advanced': len(pre2000_advanced),
        'pre2000Acquired': len(pre2000_acquired),
        'advancedNeverAttempted': [c[-16:] for c in never_attempted],
        'mechanism': (
            '⚠️ 成因不神祕：OA 存放本身比 2000 年輕，Europe PMC 的 JATS 路徑'
            '更是如此。🚨 但「成因合理」不等於「後果無害」——'
            '**本 run 從未把這件事宣告出來過。**'),
        'whatThisCannotAnswer': (
            '🚫 那 107 篇 2000 年前的文獻內容是否真的關鍵——⚠️ 本支不讀內容、'
            '不判相關性；它只說「語料對那個年代零代表」。'
            '🚫 也不主張補得到——那要另外的取文途徑，屬擁有者裁定。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n625 語料年代偏差稽核 ===')
    print('   篩選第一關：%s' % doc['screeningOpinionCounts'])
    print('   advance %d 篇｜已取得 %d 篇（其中 %d 在 advance 內）｜涵蓋率 %.1f%%'
          % (len(advance), len(acquired), len(acquired & advance),
             doc['coverageOfAdvanced']))
    print('   %-10s %8s %8s %8s' % ('年代', 'advance', '已取得', '取得率'))
    for r in rows:
        print('   %-10s %8d %8d %7s%%' % (r['era'], r['advanced'],
                                          r['acquired'], r['rate']))
    print('   卡點交叉表：')
    for label, block in era_blockers.items():
        print('   %-10s %s' % (label, '｜'.join(
            '%s %d' % (k, v) for k, v in block.items() if v)))
    print('   語料年份範圍 %s｜中位 %s'
          % (doc['acquiredYearRange'], doc['acquiredMedianYear']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
