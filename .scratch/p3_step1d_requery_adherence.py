# -*- coding: utf-8 -*-
"""**改掉問錯的構念，重問一次「赤字維持得住嗎」。**（n+195，P3）

## 🚨 第 601 輪查明：本室把構念問錯了

⚠️ 舊查詢乙用 `weight loss maintenance`——**🚫 那指的是「減完之後把體重維持住」**，
**🚨 不是「減脂期間把赤字維持住」。** ✅ 而擁有者要的是後者。

## ✅ 新查詢問的是「撐不撐得住」

`dietary adherence`／`caloric restriction adherence`／`compliance`／
`attrition`／`dropout`，**⚠️ 且必須同時出現能量限制或減重介入的情境**
——🚨 否則 attrition 會撈到所有領域的失訪。

## 🚨 而「改了查詢」本身要被證明有效

⚠️ 一個沒有真的改變檢索池的修正，與一個有效的修正**在畫面上一樣**。
**✅ 故本支同時量三個數**：新集合大小、與舊集合的重疊、以及**新增了多少**。
🚨 若新舊幾乎相同，那就代表這次「修正」什麼也沒修。
"""
import json
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

OUT = Path(__file__).resolve().parent / 'p3_step1d_requery.json'
PRIOR = Path(__file__).resolve().parent / 'p3_step1_survey.json'
DETAIL = ROOT / 'p3-stress-eating' / 'step1d-requery.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'

REVIEW = ('(PUB_TYPE:"systematic review" OR PUB_TYPE:"meta-analysis" '
          'OR TITLE:"systematic review" OR TITLE:"meta-analysis")')
# ✅ 「撐不撐得住」那一面。
STICKING = ('(TITLE_ABS:"dietary adherence" OR TITLE_ABS:"diet adherence" '
            'OR TITLE_ABS:"dietary compliance" '
            'OR TITLE_ABS:"adherence to energy restriction" '
            'OR TITLE_ABS:"adherence to caloric restriction" '
            'OR TITLE_ABS:"attrition" OR TITLE_ABS:"dropout")')
# 🚨 情境：⚠️ 沒有這一段，attrition 會撈到所有領域的失訪。
CONTEXT = ('(TITLE_ABS:"weight loss" OR TITLE_ABS:"energy restriction" '
           'OR TITLE_ABS:"caloric restriction" '
           'OR TITLE_ABS:"calorie restriction" OR TITLE_ABS:"energy deficit" '
           'OR TITLE_ABS:"weight management")')
NEW_QUERY = '%s AND %s AND %s' % (STICKING, CONTEXT, REVIEW)


def page(query, email, cursor='*'):
    params = {'query': query, 'format': 'json', 'pageSize': '100',
              'resultType': 'lite', 'cursorMark': cursor}
    url = '%s?%s' % (BASE, urllib.parse.urlencode(params))
    got = fetch(url, email=email)
    if got.get('skipped') or got.get('error') or got.get('status') != 200:
        return None, got
    try:
        return json.loads(got['body']), got
    except ValueError as exc:
        return None, {'error': 'json: %s' % exc}


def main():
    email, source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 依 n+150（三）不送任何請求。', file=sys.stderr)
        return 2

    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    # 🚨 基準要用**完整**的舊集合。⚠️ 第一版拿 p3_step1_survey 裡記的那 100 筆去比，
    # 而那只是第一頁——**🚫 用局部基準算出來的重疊會偏低，讓修正看起來比實際更有效。**
    # ✅ 完整的 318 筆在私有根（第 600 輪取齊後寫入）。
    full = json.loads(
        (ROOT / 'p3-stress-eating' / 'step1b-cutoff.json')
        .read_text(encoding='utf-8'))
    old_ids = set(full['candidates'])

    records, cursor, guard, failure = {}, '*', 0, None
    while guard < 6:
        guard += 1
        payload, raw = page(NEW_QUERY, email, cursor)
        if payload is None:
            failure = raw
            break
        for record in payload.get('resultList', {}).get('result', []):
            records[record['id']] = record
        nxt = payload.get('nextCursorMark')
        if not nxt or nxt == cursor or len(records) >= int(payload.get('hitCount', 0)):
            break
        cursor = nxt
    hit_count = payload.get('hitCount') if payload else None

    new_ids = set(records)
    overlap = new_ids & old_ids
    added = new_ids - old_ids

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('新查詢真的拿到結果（必觸發）', bool(records),
          '🚨 若為零，「修正有效」無從談起；實得 %d 筆（命中 %s）%s'
          % (len(records), hit_count, ('｜失敗 %s' % failure) if failure else ''))
    # 🚨 必觸發之反向：⚠️ 修正必須真的改變檢索池。
    probe('修正確實改變了檢索池（必觸發之反向）',
          len(added) > 0 and len(overlap) < len(new_ids),
          '🚨 新集合 %d 筆，其中 %d 筆是舊集合沒有的、%d 筆重疊；'
          '⚠️ 若幾乎全部重疊，這次「修正」什麼也沒修'
          % (len(new_ids), len(added), len(overlap)))
    probe('新舊不是同一批（必觸發之反向）',
          len(overlap) < min(len(new_ids), len(old_ids)),
          '⚠️ 舊集合 %d 筆、新集合 %d 筆、重疊 %d 筆'
          % (len(old_ids), len(new_ids), len(overlap)))
    # 🚨 這一道會紅：⚠️ 換了池子不等於盤點做完。
    probe('新集合已篩選並填好截止日', False,
          '🚨 本支只做檢索。🚫 一份都還沒篩、還沒讀方法段——'
          '⚠️ 而 n+195 三之 3 禁止用出版年推測截止日')

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p3-step1d-private', 'query': NEW_QUERY,
         'items': [{'id': k, 'title': v.get('title'),
                    'pubYear': v.get('pubYear'),
                    'journal': v.get('journalTitle'),
                    'inOldSet': k in old_ids}
                   for k, v in records.items()]},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1d-requery',
        'assignment': 'n+195：P3 第一步（改構念後重問乙組）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contactEmail': masked(email),
        'requests': counters(),
        'oldQuery': prior['queries']['deficit-adherence'],
        'newQuery': NEW_QUERY,
        'whyChanged': (
            '🚨 舊查詢用 weight loss maintenance 問「赤字維持得住嗎」，'
            '⚠️ 而那在文獻裡指「減完之後把體重維持住」——🚫 不是同一個問題。'),
        'oldSetSize': len(old_ids),
        'oldSetBasis': '第 600 輪取齊後的完整聯集（甲＋乙），🚫 不是第一頁的 100 筆',
        'newHitCount': hit_count,
        'newRetrieved': len(new_ids),
        'overlapWithOld': len(overlap),
        'newlyAdded': len(added),
        'newIds': sorted(new_ids),
        'failure': {k: v for k, v in (failure or {}).items()
                    if k in ('status', 'error', 'skipped')},
        'stillNotDone': (
            '🚨 本支只做檢索。🚫 未篩選、未讀方法段、未填任何截止日。'),
        'titlesKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3：改構念後重問乙組 ===')
    print('   舊集合（完整聯集）%d 筆｜新命中 %s｜新取回 %d 筆'
          % (len(old_ids), hit_count, len(new_ids)))
    print('   🚨 重疊 %d 筆｜✅ 新增 %d 筆' % (len(overlap), len(added)))
    print('   請求數 %s' % counters().get('totalRequests'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（題名留私有根）' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
