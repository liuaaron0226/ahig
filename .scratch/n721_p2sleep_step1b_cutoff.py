# -*- coding: utf-8 -*-
"""**P2 第一步（續）：從摘要撈「搜尋截止日」。**（n+196 交辦）

## ✅ 與 P3 同一套（`p3_step1b_cutoff_scan.py`），🚫 不另發明

- **樣式**：逐字沿用 P3 那一條——✅ 只抓論文**自己寫出來**的檢索截止陳述，
  **🚫 不從出版年推測。**
- **分批**：`core` 記錄大，⚠️ 一次 100 筆會被 `fetch_guard` 的 40 萬字元上限截斷；
  🚨 故一次只要 25 筆（P3 第 599 輪學到的）。

## 🚨 而這一遍**不是**盤點的答案

⚠️ 摘要**經常不寫**搜尋截止日——🚨 權威來源是方法段。
**✅ 故本支的產出是「哪幾份摘要裡就寫了」＋「其餘要去讀方法段」，
🚫 不是一份填好的截止日清單。**

> **🚨 n+196 三：沒有截止日的回顧記為「無法接續」，
> 🚫 不得用「大概是那幾年」補上去。**

## ⚠️ 命名

🚨 `.gitignore` 有 `.scratch/p2_*.json`（篩選第二輪的每頁暫存檔）——
**✅ 故本支用輪次編號命名**，🚫 免得產物被靜默排除在 git 之外（第 720 輪撞過）。
"""
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_guard import contact_email, counters, fetch, masked  # noqa: E402
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n721_p2sleep_step1b_cutoff.json'
PRIOR = HERE / 'n720_p2sleep_step1_survey.json'
DETAIL = ROOT / 'p2-sleep' / 'step1b-cutoff.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
CORE_PAGE = 25

# ✅ 逐字沿用 P3 的樣式，🚫 不自行改寫（改了就不能跟 P3 比）。
CUTOFF = re.compile(
    r'(?:search(?:ed|es)?|searching|database[s]?\s+were\s+searched|literature '
    r'search)[^.]{0,120}?'
    r'(?:up\s+to|until|through|inception\s+to|to)\s+'
    r'((?:January|February|March|April|May|June|July|August|September|October'
    r'|November|December)\s+\d{4}|\d{1,2}\s+\w+\s+\d{4}|\d{4})',
    re.I)


def page(query, email, size=CORE_PAGE, kind='core'):
    params = {'query': query, 'format': 'json', 'pageSize': str(size),
              'resultType': kind, 'cursorMark': '*'}
    url = '%s?%s' % (BASE, urllib.parse.urlencode(params))
    got = fetch(url, email=email)
    if got.get('skipped') or got.get('error') or got.get('status') != 200:
        return None, got
    try:
        return json.loads(got['body']), got
    except ValueError as exc:
        return None, {'error': 'json: %s' % exc,
                      'bodyChars': len(got.get('body') or '')}


def main():
    email, source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 依 n+150（三）不送任何請求。', file=sys.stderr)
        return 2

    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    # ✅ 第 720 輪兩組都一次取回（41／29），🚫 故本支不需要再分頁取齊。
    by_set = {name: info['ids'] for name, info in prior['results'].items()}
    union = sorted({i for ids in by_set.values() for i in ids})

    private = json.loads(
        (ROOT / 'p2-sleep' / 'step1-candidates.json').read_text(
            encoding='utf-8'))
    year_of = {}
    for records in private['sets'].values():
        for record in records:
            year_of[record['id']] = record.get('pubYear')

    stated, scanned, failures = {}, 0, {}
    abstracts_private = {}
    order = sorted(union, key=lambda k: year_of.get(k) or '0', reverse=True)
    for start in range(0, len(order), CORE_PAGE):
        batch = order[start:start + CORE_PAGE]
        query = ' OR '.join('EXT_ID:%s' % k for k in batch
                            if str(k).isdigit())
        if not query:
            continue
        payload, raw = page(query, email)
        if payload is None:
            failures['core:%d' % start] = {
                k: v for k, v in (raw or {}).items()
                if k in ('status', 'error', 'skipped', 'bodyChars')}
            continue
        for record in payload.get('resultList', {}).get('result', []):
            scanned += 1
            text = record.get('abstractText') or ''
            abstracts_private[record['id']] = text
            hit = CUTOFF.search(text)
            if hit:
                stated[record['id']] = hit.group(1)

    dated = sorted(((re.search(r'(\d{4})', v).group(1), v, k)
                    for k, v in stated.items() if re.search(r'\d{4}', v)),
                   reverse=True)
    cutoff_years = Counter(y for y, _v, _k in dated)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('候選數與第 720 輪一致（必觸發之正對照）',
          len(union) == prior['unionIds'],
          '🚨 聯集 %d 筆｜第 720 輪記的 %d 筆；⚠️ 對不上代表接錯了上一步'
          % (len(union), prior['unionIds']))
    probe('摘要真的拿到了（必觸發之正對照）',
          scanned > 0,
          '🚨 取得 %d 份摘要（失敗 %s）；⚠️ 若為零，'
          '「摘要裡沒寫截止日」只是沒讀到' % (scanned, failures or '無'))
    # 🚨 必觸發之反向：樣式要真的打得中，否則零命中沒有意義。
    probe('截止日樣式確實打得中（必觸發之反向）',
          bool(stated),
          '✅ 實得 %d 份摘要自己寫了檢索截止；'
          '🚨 若為零，那可能是樣式壞了而不是文獻沒寫' % len(stated))
    # 🚨 這一道**故意會紅**：⚠️ 摘要不是權威來源。
    probe('每一份候選都已填入搜尋截止日', False,
          '🚨 %d／%d 份的摘要裡寫了；⚠️ 其餘 %d 份要去讀**方法段**——'
          '**🚫 不得用出版年或「大概是那幾年」補上去**（n+196 三）'
          % (len(stated), len(union), len(union) - len(stated)))

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p2-step1b-cutoff-private',
         'statedInAbstract': stated,
         'abstracts': abstracts_private},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p2-step1b-cutoff-scan',
        'assignment': 'n+196：P2（睡眠）第一步之截止日第一遍',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'method': '✅ 與 P3 的 `p3_step1b_cutoff_scan.py` 同一套（樣式逐字沿用）。',
        'candidates': len(union),
        'abstractsScanned': scanned,
        'statedInAbstract': len(stated),
        'needMethodsSection': len(union) - len(stated),
        'cutoffYearHistogram': dict(sorted(cutoff_years.items(),
                                           reverse=True)),
        'newestStated': dated[0][:2] if dated else None,
        'failures': failures,
        'requestCounters': counters(),
        'contactEmail': masked(email),
        'abstractsKeptPrivate': str(DETAIL),
        'whyThisIsNotTheAnswer': (
            '⚠️ 摘要**經常不寫**搜尋截止日——🚨 權威來源是方法段。'
            '✅ 故本支的產出是「哪幾份摘要裡就寫了」＋「其餘要去讀方法段」，'
            '🚫 不是一份填好的截止日清單。'
            '**🚨 且這 %d 份尚未篩選切題性——'
            '⚠️ 那份「最新」的回顧未必切題，🚫 不得當成結論。**'
            % len(union)),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P2 第一步（續）・摘要裡的截止日 ===')
    print('   候選 %d 筆｜取得摘要 %d 份｜摘要就寫了截止日的 %d 份'
          % (len(union), scanned, len(stated)))
    print('   截止年分佈：%s' % doc['cutoffYearHistogram'])
    # 🚨 `newestStated` 是 tuple，⚠️ 直接餵給 `%s` 會被當成多個參數。
    # ✅ 第一次跑就是這樣崩的（JSON 已寫出，只有這一行掛掉），🚫 故未重跑。
    print('   最新（暫定，尚未篩切題性）：%s'
          % (str(doc['newestStated']) if doc['newestStated'] else '（無）'))
    print('   請求計數：%s' % counters()['totalRequests'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
