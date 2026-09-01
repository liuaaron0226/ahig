# -*- coding: utf-8 -*-
"""**「41 篇」的分母是什麼。**（第 624 輪）

## 🚨 本 run 從頭到尾只講 41，卻沒有一處寫下 41 是「幾分之」

⚠️ 內容關卡、雙讀、稽核，全部建立在「語料 41 篇」上。
**🚫 但沒有任何一份憑證說過：那 41 篇是從多大的池子裡取出來的、
其餘的去哪了、以及「取不到」與「沒去取」有沒有分開記。**

> **🚨 系統性回顧裡，這一格漏掉就不是小事——⚠️ 它決定語料是「全部可得者」還是「剛好被跑到的那些」。**

## ✅ 本支查四件事

| | 問題 |
|---|---|
| **甲** | 全庫每一份取文清單的 status 分布——**41 之外還有什麼** |
| **乙** | 當初判定「拿得到」的那些，**最後有幾篇真的進了語料** |
| **丙** | 沒進語料的那些，**是取不到、還是沒去取**（用時間戳與 host 兩面驗） |
| **丁** | 卡住的那一大群，**卡在哪一個關卡** |

## 🚫 本支不送任何外部請求、不改任何產品程式、不改任何清冊
⚠️ 故「那 18 篇到底取不取得到」🚫 本支答不出來——要真的去抓才知道。
"""
import collections
import datetime
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402

S = Path(__file__).resolve().parent
OUT = S / 'n624_corpus_denominator.json'


def main():
    roster = set(corpus.acquired_roster()[0])

    # 甲：全庫 status 分布，並記下每份的嘗試結論指紋。
    #
    # 🚨 第一版本支數出 315 份、其中 4 份 status=unavailable；
    # ⚠️ 但那 4 份與另外 4 份**是同一個 candidateId**——
    # 它們躺在舊命名的目錄 `ahig_candidate_publication_<hex>` 底下，
    # 而現行程式的正規目錄是 `<slug>-<sha16>`（fulltext.py:380）。
    # **🚨 故 315 是檔案數，不是候選數；相異候選是 311。**
    # ⚠️ 產品的 `_artifact_dir` 永遠走不到那 4 個舊目錄，
    # 🚨 但 `corpus._acquired_manifests` 是 `root.iterdir()`——**它看得到**，
    # 擋住它們的只有一句 `status != "acquired"` 的過濾。
    manifests = {}
    mtimes = {}
    status_count = collections.Counter()
    legacy_orphans = []
    fingerprints = collections.defaultdict(collections.Counter)
    for path in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        if path.parent.name.startswith('ahig_candidate_publication_'):
            legacy_orphans.append({
                'dir': path.parent.name,
                'status': doc.get('status'),
                'attempts': len(doc.get('attempts') or []),
                'otherFiles': [p.name for p in path.parent.iterdir()
                               if p.name != 'manifest.json'],
            })
            continue
        manifests[doc['candidateId']] = doc
        mtimes[doc['candidateId']] = datetime.datetime.fromtimestamp(
            path.stat().st_mtime).isoformat()
        status_count[doc.get('status')] += 1
        attempts = doc.get('attempts') or []
        key = ' / '.join('%s=%s' % (a.get('sourceId'), a.get('conclusion'))
                         for a in attempts) or '（無嘗試）'
        fingerprints[doc.get('status')][key] += 1

    # 乙：n438 當初的「可得」定義，套回今天的名冊。
    inv = json.loads((S / 'm1_step3_inventory.json').read_text(encoding='utf-8'))
    backfill = json.loads(
        (S / 'm1_step3_backfill.json').read_text(encoding='utf-8'))
    obtainable_def = set(backfill['obtainableDefinition'])
    final = {r['candidateId']: r['status'] for r in inv['records']}
    for pool in backfill['pools']:
        for rec in pool.get('backfilled') or []:
            if rec.get('accepted'):
                final[rec['candidateId']] = rec['status']
    obtainable = {k for k, v in final.items() if v in obtainable_def}
    in_corpus = obtainable & roster
    never_taken = sorted(obtainable - roster)
    outside_pool = roster - obtainable

    # 丙之一：⚠️ 無辜的解釋——「那 18 篇是 GROBID 那輪跑完之後才解析出來的」。
    # 🚨 若成立，它們從來沒有資格被取，本支就沒有發現。
    grobid = [c for c in roster
              if manifests.get(c, {}).get('sourceType') == 'grobid-tei']
    latest_missed = max((mtimes[c] for c in never_taken), default='')
    earliest_grobid = min((mtimes[c] for c in grobid), default='')
    too_late = latest_missed < earliest_grobid  # ✅ True ⇒ 那個解釋被否定

    # 丙之二：⚠️ 另一個無辜的解釋——「那些 host 本來就不抓」。
    def host(url):
        return urlparse(url or '').netloc or '（無 URL）'

    missed_hosts = collections.Counter(
        host(manifests[c].get('availableUrl')) for c in never_taken)
    taken_hosts = collections.Counter(
        host(manifests[c].get('sourceUrl')) for c in roster)
    both_sides = sorted(set(missed_hosts) & set(taken_hosts))

    # 丁：卡住的那一群卡在哪。
    blocked_key = 'europe-pmc=miss / openalex=miss / unpaywall=blocked'
    blocked_count = fingerprints['incomplete'][blocked_key]
    # ⚠️ 舊目錄是否曾污染名冊：只要有一個是 acquired，名冊就會多出一筆
    # **同一篇的重複 id**——而重複的 id 看起來跟正常的 id 一模一樣。
    orphan_acquired = [o for o in legacy_orphans if o['status'] == 'acquired']
    orphan_statuses = sorted({o['status'] for o in legacy_orphans})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('「可得」集合非空且與名冊有交集（必觸發之正對照）',
          len(obtainable) > 0 and len(in_corpus) > 0,
          '🚨 可得 %d 篇、其中 %d 篇進了語料；⚠️ 若交集為零，'
          '本支整個比較就沒有意義' % (len(obtainable), len(in_corpus)))
    probe('以不存在的 status 查，計數為零（必觸發之反向）',
          status_count['ZZ-不存在-ZZ'] == 0,
          '🚨 若這也數得出東西，「41 / 52 / 154」這些數就不可信')
    probe('⚠️ 未取得的 18 篇不是「來不及」（時間戳）',
          too_late,
          '🚨 未取得者最後的清單寫入 %s；⚠️ 最早的 GROBID 取得 %s——'
          '故 GROBID 那一輪跑的時候它們**早已躺在那裡**'
          % (latest_missed[:16], earliest_grobid[:16]))
    probe('⚠️ 未取得的原因不是「這個 host 不抓」',
          bool(both_sides),
          '🚨 有 %d 個 host 兩邊都出現（取到的與沒取的各有）：%s'
          % (len(both_sides), both_sides[:4]))
    # 🚨 以下兩道是紅燈——它們就是本支的發現。
    probe('判定可得者全部都進了語料',
          not never_taken,
          '🚨 實得 %d 篇判定可得卻至今未取（%s）；'
          '⚠️ 而 repo 與私有根都查不到那一步餵了哪份名單'
          % (len(never_taken),
             '、'.join('%s×%d' % (k, v)
                       for k, v in collections.Counter(
                           manifests[c].get('status')
                           for c in never_taken).most_common())))
    probe('沒有一大群卡在單一關卡',
          blocked_count == 0,
          '🚨 實得 %d 份卡在同一個指紋「%s」——'
          '⚠️ 而 blocked 的成因是 missing-contact-email（fulltext.py:931），'
          '即 **Unpaywall 從來沒有被問過**' % (blocked_count, blocked_key))
    probe('沒有舊命名的孤兒目錄',
          not legacy_orphans,
          '🚨 實得 %d 個 `ahig_candidate_publication_*` 目錄，status=%s、'
          '皆零嘗試且無任何產物；⚠️ acquire_fulltext 寫不出這個 status'
          '（它只寫 acquired／available-*／no-oa-fulltext／incomplete），'
          '故它們是舊命名時代的空殼，🚫 不是「取得失敗」'
          % (len(legacy_orphans), orphan_statuses))
    probe('✅ 名冊未被孤兒目錄污染（本支的證明，非假設）',
          not orphan_acquired,
          '✅ 孤兒目錄裡 status=acquired 者 %d 個；⚠️ 只要有一個，'
          '名冊就會多出一筆同一篇的重複 id——**而重複的 id 看起來跟正常的一樣**'
          % len(orphan_acquired))

    doc = {
        'schemaVersion': 1,
        'documentType': 'corpus-denominator-audit',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'distinctCandidates': sum(status_count.values()),
        'manifestFilesOnDisk': sum(status_count.values()) + len(legacy_orphans),
        'legacyOrphanDirs': legacy_orphans,
        'orphanNote': (
            '🚨 磁碟上有 %d 個 manifest 檔，但相異候選只有 %d 個——'
            '差額是 %d 個舊命名目錄，它們與現行目錄**指向同一批 candidateId**。'
            '⚠️ 產品的 _artifact_dir 走不到它們；'
            '🚨 但 corpus._acquired_manifests 的 iterdir 看得到，'
            '擋住它們的只有一句 status != "acquired"。'
            % (sum(status_count.values()) + len(legacy_orphans),
               sum(status_count.values()), len(legacy_orphans))),
        'statusDistribution': dict(status_count.most_common()),
        'attemptFingerprints': {k: dict(v.most_common(4))
                                for k, v in fingerprints.items()},
        'obtainableAtN438': len(obtainable),
        'obtainableInCorpus': len(in_corpus),
        'obtainableNeverTaken': [c[-16:] for c in never_taken],
        'corpusFromOutsideThatPool': len(outside_pool),
        'rosterTotal': len(roster),
        'latestMissedManifestWrite': latest_missed,
        'earliestGrobidAcquire': earliest_grobid,
        'hostsOnBothSides': both_sides,
        'missedHosts': dict(missed_hosts.most_common()),
        'singleBlocker': {'fingerprint': blocked_key,
                          'count': blocked_count,
                          'cause': 'missing-contact-email（fulltext.py:931）'},
        'namingTrap': (
            '⚠️ fulltext.py:1293 的 unavailableCount 數的是 no-oa-fulltext，'
            '🚨 而磁碟上另有字面上的 status=unavailable（那 4 個孤兒）——'
            '**同一個詞指兩件事**。'),
        'whatThisCannotAnswer': (
            '🚫 那 18 篇實際取不取得到——⚠️ 要真的去抓才知道，本支不送請求。'
            '🚫 當初 PDF→GROBID 那一步的選取準則——⚠️ 沒有紀錄，本室不編。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n624 語料分母稽核 ===')
    print('   相異候選 %d 個（磁碟上 %d 個 manifest 檔，差額為舊命名孤兒 %d 個）：'
          % (sum(status_count.values()),
             sum(status_count.values()) + len(legacy_orphans),
             len(legacy_orphans)))
    for k, v in status_count.most_common():
        print('      %-24s %d' % (k, v))
    print('   當初判定可得 %d｜其中進語料 %d｜🚨 未取 %d｜語料另有 %d 篇來自池外'
          % (len(obtainable), len(in_corpus), len(never_taken),
             len(outside_pool)))
    print('   名冊合計 %d' % len(roster))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
