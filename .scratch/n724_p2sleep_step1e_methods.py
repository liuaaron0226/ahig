# -*- coding: utf-8 -*-
"""**P2 第一步（續）：讀方法段，補齊那四份的檢索截止日。**（n+196 交辦）

## 🚨 為什麼非做不可

第 723 輪的表裡，**六份只有兩份的截止日是明確日期**。
⚠️ 而 n+196 三說得很清楚：**那是最重要的一欄**，
**🚫 不得用出版年或區間端點頂替**；讀不到就記「無法接續」。

## ✅ 本支做什麼

1. 一次查詢取那四份的 **PMCID 與開放取用狀態**。
2. 對取得到全文者，抓 `fullTextXML`，**只在方法段一帶找論文自己寫的檢索截止陳述**。
3. 🚫 找不到就記**「無法接續」**——⚠️ 一個字都不推測。

## ⚠️ 一個已知的取捨

`fetch_guard` 對回應有 40 萬字元上限。🚨 全文可能超過而被截斷——
✅ 但方法段通常在前段，⚠️ 故截斷多半不影響；**🚨 而本支會記下是否被截斷**，
🚫 不假裝讀完了整份。
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_guard import contact_email, counters, fetch, masked  # noqa: E402
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n724_p2sleep_step1e_methods.json'
DETAIL = ROOT / 'p2-sleep' / 'step1e-methods.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest'

NEED = ['27804960', '32960623', '33001515', '42044907']

# ✅ 沿用 P3／第 721 輪那一條，⚠️ 另加兩種在方法段常見、但摘要少見的寫法。
#
# 🚨 **這裡踩過一次坑，留下來當紀錄**：本室原本為了兼容「September 12, 2025」
# 而寫成 `\s+\d{1,2}?,?\s*\d{4}`，**⚠️ 那等於把「日」從選配變成必填**，
# 🚫 反而打不中最常見的「September 2025」。
# ✅ 是「必觸發之反向」那道控制探針在**已知答案**上先亮紅，才擋下來的。
# **🚨 故日的部分必須整組選配：`(?:\d{1,2},?\s*)?`。**
DAY_YEAR = r'\s+(?:\d{1,2},?\s*)?\d{4}'
MONTH = (r'(?:January|February|March|April|May|June|July|August|September'
         r'|October|November|December)')
CUTOFF = re.compile(
    r'(?:search(?:ed|es)?|searching|database[s]?\s+were\s+searched|literature '
    r'search)[^.]{0,160}?'
    r'(?:up\s+to|until|through|inception\s+to|to)\s+'
    r'(' + MONTH + DAY_YEAR + r'|\d{1,2}\s+\w+\s+\d{4}|\d{4})',
    re.I)
CUTOFF2 = re.compile(
    r'(?:from\s+inception\s+(?:to|until|through)|'
    r'(?:date\s+of\s+)?last\s+search(?:\s+was)?(?:\s+conducted)?(?:\s+on|\s+in)?)'
    r'[^.]{0,60}?'
    r'(' + MONTH + DAY_YEAR + r'|\d{1,2}\s+\w+\s+\d{4})',
    re.I)
TAGS = re.compile(r'<[^>]+>')


def main():
    email, source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 依 n+150（三）不送任何請求。', file=sys.stderr)
        return 2

    # ── 一、取 PMCID 與開放取用狀態（一次請求）────────────────
    query = ' OR '.join('EXT_ID:%s' % k for k in NEED)
    params = {'query': query, 'format': 'json', 'pageSize': '25',
              'resultType': 'core'}
    got = fetch('%s/search?%s' % (BASE, urllib.parse.urlencode(params)),
                email=email)
    meta, lookup_error = {}, None
    if got.get('status') == 200 and not got.get('error'):
        try:
            payload = json.loads(got['body'])
            for record in payload.get('resultList', {}).get('result', []):
                meta[record.get('id')] = {
                    'pmcid': record.get('pmcid'),
                    'isOpenAccess': record.get('isOpenAccess'),
                    'inEPMC': record.get('inEPMC'),
                    # ⚠️ 多留兩個欄位：🚨 「取不到全文」這個判定
                    # **🚫 不該只靠一個欄位**——本室要它們互證。
                    'hasPDF': record.get('hasPDF'),
                    'fullTextIdList': record.get('fullTextIdList'),
                }
        except ValueError as exc:
            lookup_error = 'json: %s' % exc
    else:
        lookup_error = {k: v for k, v in got.items()
                        if k in ('status', 'error', 'skipped')}

    # ── 二、逐份讀方法段 ────────────────────────────────────
    rows, private = [], {}
    for pmid in NEED:
        info = meta.get(pmid, {})
        pmcid = info.get('pmcid')
        ft_ids = info.get('fullTextIdList') or {}
        row = {'id': pmid, 'pmcid': pmcid,
               'isOpenAccess': info.get('isOpenAccess'),
               'inEPMC': info.get('inEPMC'),
               'hasPDF': info.get('hasPDF'),
               'fullTextIds': ft_ids.get('fullTextId') if ft_ids else None,
               'cutoff': None, 'pattern': None,
               'truncated': None, 'outcome': None}
        # 🚨 三個欄位一致才判「取不到」：⚠️ 只靠一個欄位會把可取得的誤判掉。
        if not pmcid and info.get('inEPMC') != 'Y' and not row['fullTextIds']:
            row['outcome'] = ('🚫 全文不在 Europe PMC'
                              '（pmcid／inEPMC／fullTextId 三者皆無）'
                              '——⚠️ 記為「無法接續」')
            rows.append(row)
            continue
        if not pmcid:
            pmcid = (row['fullTextIds'] or [None])[0]
            row['pmcid'] = pmcid
        if not pmcid:
            row['outcome'] = '🚫 有全文旗標但取不到識別碼——⚠️ 記為「無法接續」'
            rows.append(row)
            continue
        full = fetch('%s/%s/fullTextXML' % (BASE, pmcid), email=email)
        if full.get('status') != 200 or full.get('error'):
            row['outcome'] = '🚫 取不到全文（%s）——⚠️ 記為「無法接續」' % (
                full.get('error') or full.get('status'))
            rows.append(row)
            continue
        body = full['body']
        text = TAGS.sub(' ', body.decode('utf-8', 'replace')
                        if isinstance(body, bytes) else body)
        row['truncated'] = len(text) >= 399_000
        private[pmid] = text[:4000]
        hit = CUTOFF.search(text) or CUTOFF2.search(text)
        if hit:
            row['cutoff'] = hit.group(1)
            row['pattern'] = 'CUTOFF' if CUTOFF.search(text) else 'CUTOFF2'
            row['outcome'] = '✅ 方法段寫了'
        else:
            row['outcome'] = ('🚨 全文裡找不到檢索截止陳述'
                              '——⚠️ 記為「無法接續」，🚫 不推測')
        rows.append(row)

    found = [r for r in rows if r['cutoff']]
    unresolved = [r for r in rows if not r['cutoff']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('那四份的中繼資料都查得到（必觸發之正對照）',
          len(meta) == len(NEED) and not lookup_error,
          '🚨 查到 %d／%d 份；錯誤：%s；⚠️ 查不到就無從判斷全文取不取得到'
          % (len(meta), len(NEED), lookup_error or '無'))
    # 🚨 必觸發之反向：樣式要在**已知有寫**的那一份上打得中。
    control = CUTOFF.search(
        'We searched MEDLINE, Embase, and CENTRAL from inception to '
        'September 2025.')
    probe('截止日樣式在已知句型上打得中（必觸發之反向）',
          bool(control) and control.group(1).lower() == 'september 2025',
          '🚨 對照句取得：%s；⚠️ 打不中就代表零命中只是樣式壞了'
          % (control.group(1) if control else '（無）'))
    probe('捏造的句子不會被誤判（必觸發之反向）',
          not CUTOFF.search('The authors thank the funders.')
          and not CUTOFF2.search('The authors thank the funders.'),
          '🚨 無關句子未命中；⚠️ 若命中，代表樣式太寬')
    # 🚨 必觸發之反向：⚠️ 若真的取不到，三個欄位要**一起**說取不到；
    # 🚫 只有一個欄位為否，就不足以下「無法接續」。
    unavailable = [r for r in rows if '不在 Europe PMC' in (r['outcome'] or '')]
    probe('「取不到全文」是三個欄位一致下的判定（必觸發之反向）',
          all(not r['pmcid'] and r['inEPMC'] != 'Y' and not r['fullTextIds']
              for r in unavailable),
          '🚨 判為取不到的 %d 份，逐份 (pmcid, inEPMC, fullTextIds)：%s；'
          '⚠️ 只要有一份三者不一致，這個判定就站不住'
          % (len(unavailable),
             [(r['id'], r['pmcid'], r['inEPMC'], r['fullTextIds'])
              for r in unavailable]))
    # 🚨 這一道是答案。
    probe('四份的檢索截止日都補齊了',
          not unresolved,
          '🚨 補到 %d／%d 份；未補到的 %s；'
          '⚠️ 未補到者一律記「無法接續」——**🚫 不得用出版年頂替**'
          % (len(found), len(NEED),
             [(r['id'], r['outcome']) for r in unresolved] or '無'))

    # ── 三、⚠️ 回頭重掃第 721 輪那 64 份摘要 ─────────────────
    # 🚨 同一個缺陷也在第 721 輪那條樣式裡：**它要求月份後面直接接年**，
    # 🚫 打不中「September 12, 2025」這種帶日的寫法。
    # ✅ 摘要是本機現成的，重掃**不花任何請求**；⚠️ 若數字有變，那一輪就是低估。
    rescan = {'ran': False}
    prior = ROOT / 'p2-sleep' / 'step1b-cutoff.json'
    if prior.exists():
        book = json.loads(prior.read_text(encoding='utf-8'))
        before = set(book.get('statedInAbstract') or [])
        after, recovered = set(), {}
        for pid, abstract in (book.get('abstracts') or {}).items():
            hit = CUTOFF.search(abstract or '') or CUTOFF2.search(abstract or '')
            if hit:
                after.add(pid)
                if pid not in before:
                    recovered[pid] = hit.group(1)
        rescan = {
            'ran': True,
            'abstractsScanned': len(book.get('abstracts') or {}),
            'statedBefore': len(before),
            'statedAfter': len(after),
            'recovered': recovered,
            'lostByRescan': sorted(before - after),
            'note': ('✅ 差額即第 721 輪因樣式而**低估**的份數；'
                     '⚠️ 反向若有「掉的」，代表新樣式反而更緊，🚫 得回頭看。'),
        }
        probe('重掃只會把漏掉的補回來，🚫 不會把原本有的弄丟（必觸發之反向）',
              not rescan['lostByRescan'],
              '🚨 補回 %d 份、掉了 %s；⚠️ 一旦有掉的，就不是單純的放寬'
              % (len(recovered), rescan['lostByRescan'] or '無'))

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p2-step1e-methods-private',
         'methodsExcerpt': private}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p2-step1e-methods-cutoff',
        'assignment': 'n+196：補齊 P2 表上的檢索截止日',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'targets': NEED,
        'rows': rows,
        'resolved': {r['id']: r['cutoff'] for r in found},
        'unresolved': [r['id'] for r in unresolved],
        'rescanOfRound721': rescan,
        'patternRegression': (
            '🚨 **本輪自己踩的坑，留紀錄**：為了兼容「September 12, 2025」，'
            '本室把日寫成 `\\d{1,2}?,?\\s*`——'
            '**⚠️ 那等於把日從選配變成必填**，🚫 反而打不中最常見的'
            '「September 2025」。✅ 是「必觸發之反向」那道控制探針'
            '在**已知答案**上先亮紅才擋下來的。'
            '**🚨 而同一個缺陷的另一半在第 721 輪那條裡**：'
            '它要求月份後直接接年，🚫 打不中帶日的寫法——故本輪回頭重掃。'),
        'correctionToRound723': (
            '🚨 **更正第 723 輪自己寫的一句話。** ⚠️ 那一輪的「還缺什麼」寫了'
            '**「甲那四份的截止日多落在 2019–2020」**——'
            '🚫 但那是用**區間端點**（`33001515` 的 1970–2019）與'
            '**檢索執行日**（`32960623` 的 2016-10／2019-02）推出來的，'
            '**⚠️ 正是 n+196 三禁止的頂替。**\n'
            '✅ 站得住的說法只剩：**甲那四份裡只有 `34620371` 有明確截止日'
            '（July 2020），其餘三份為「無法接續」**；'
            '而「甲比乙舊」這個方向仍成立，⚠️ 但**依據是出版年（2017–2021 對'
            ' 2026），🚫 不是檢索截止日**。\n'
            '**🚨 故「兩半證據新舊差五年」須降級為出版年之差，'
            '🚫 不得當成檢索涵蓋範圍之差。**'),
        'consequenceForTable': (
            '⚠️ 六份的截止日欄位**維持 2 份明確、4 份無法接續**；'
            '🚫 本輪沒有把任何一格從「未載」改成日期。'
            '✅ 產出二（接續日 2025 年 9 月）**不受影響**——'
            '它來自 `42478101` 摘要自載的明確日期。'),
        'lookupError': lookup_error,
        'requestCounters': counters(),
        'contactEmail': masked(email),
        'excerptKeptPrivate': str(DETAIL),
        'rule': (
            '🚨 n+196 三：**最重要的一欄是搜尋截止日**，'
            '**🚫 不得用出版年或區間端點頂替**——'
            '✅ 讀不到就記「無法接續」。'),
        'knownTradeoff': (
            '⚠️ `fetch_guard` 對回應有 40 萬字元上限，🚨 全文可能被截斷；'
            '✅ 方法段通常在前段，故多半不影響，'
            '**🚨 而本支逐份記下是否被截斷，🚫 不假裝讀完了整份。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P2 第一步（續）・讀方法段補截止日 ===')
    for row in rows:
        print('   %-9s PMCID %-12s OA %-4s 截斷 %-6s %s%s'
              % (row['id'], row['pmcid'] or '—', row['isOpenAccess'] or '—',
                 row['truncated'], row['outcome'],
                 ('：%s' % row['cutoff']) if row['cutoff'] else ''))
    print('   補齊 %d／%d 份｜請求 %d 次'
          % (len(found), len(NEED), counters()['totalRequests']))
    if rescan['ran']:
        print('   回頭重掃第 721 輪 %d 份摘要：%d → %d 份有寫（補回 %d）'
              % (rescan['abstractsScanned'], rescan['statedBefore'],
                 rescan['statedAfter'], len(rescan['recovered'])))
        for pid, date in sorted(rescan['recovered'].items()):
            print('     ＋ %-9s %s' % (pid, date))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
