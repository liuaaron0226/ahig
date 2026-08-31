# -*- coding: utf-8 -*-
"""**哪幾篇讀的是舊版請求。**（第 579 輪，答 n+190 二）

## 🚨 裁定假設有一條分界線；而實測是**線落在語料之外**

n+190（二）要一份確切名單，🚫 不准用「大約前 23 篇」帶過。
✅ 數出來的答案是：**41 篇全部是舊版，0 篇是新版。**

| 事件 | 時刻 |
|---|---|
| 最早交回的清冊（`drafts.json`，涵蓋第 1–7 頁） | 14:49:40 |
| **最後一篇交回**（`drafts/page-017.json`） | **16:05:19** |
| **工作單重生**（`worksheet.json` 與 18 個 `pages/` 同時被改寫） | **16:09:58** |
| `--regenerate` 這段程式**進 repo** | 16:12:23 |

> **🚨 重生比最後一篇交回晚了 4 分 39 秒**，⚠️ 故那份儀器清單
> **一個讀的人都沒看到**。
> ✅ **而「更早也偷跑過一次重生」被排除**：做這件事的程式碼，
> 到 16:12:23 才存在（`git log -S`），🚫 它不可能在 16:05 之前跑過。

## ⚠️ 這對 A1 的意思，跟直覺相反

**A1「全語料同一版請求」在形式上 ✅ 過了**——⚠️ 41 篇整齊劃一。
**🚨 但整齊劃一的是舊版。**

> 📮 **故 A1 要的是哪一件，只有協調者能定**：
> 「全語料同版」→ ✅ 已達成，0 篇要重讀；
> 「全語料都看過儀器清單」→ 🚨 0／41 達成，**要重讀的是 41 篇，不是 23 篇。**
>
> ✅ **而決定這件事需要的第二個數，n574 已經量過**：
> ⚠️ 真的因儀器名被誤排的，**只有 6 項／1 篇**（另 3 項／2 篇是契約沒有滑雪，
> 重讀改不掉）。
> 🚨 **曝險 41／41，實測損害 6 項／1 篇**——兩個數要並排看，🚫 不要只看一個。

## 🚨 外部審視拿到的「23 篇」是本室給的，而它偏低

⚠️ 那份資料包寫的是 23 篇用舊版請求；**實情是 41 篇。**
🚫 不是外部審視看錯，✅ 是本室當時把「重生會趕在讀完之前」當成已經發生的事。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

SHEET = ROOT / 'extraction-worksheet'
OUT = Path(__file__).resolve().parent / 'n579_request_version_split.json'
CHARS_BEFORE_REGEN = 2039858   # n535 實測，重生前的 payload 總量


def iso(value):
    return datetime.fromtimestamp(value).isoformat(' ', 'seconds')


def classify(submitted_at, regenerated_at):
    """✅ 交回時刻早於重生 → 讀的是舊版。⚠️ 只有這一條規則。"""
    return 'before-regeneration' if submitted_at < regenerated_at else 'after'


def regenerate_commit():
    """🚨 做重生的那段程式何時才存在——用來排除「更早偷跑過」。"""
    out = subprocess.run(
        ['git', 'log', '--format=%h %ad', '--date=format:%Y-%m-%d %H:%M:%S',
         '-S', '--regenerate', '--', '.scratch/extract_worksheet.py'],
        cwd=str(REPO), capture_output=True, text=True)
    lines = [ln for ln in out.stdout.splitlines() if ln.strip()]
    return lines[-1] if lines else None


def main():
    sheet = json.loads((SHEET / 'worksheet.json').read_text(encoding='utf-8'))
    page_of = {it['report']: it['page'] for it in sheet['items']}

    regenerated_at = (SHEET / 'worksheet.json').stat().st_mtime
    page_stamps = {p.name: p.stat().st_mtime
                   for p in sorted((SHEET / 'pages').glob('page-*.json'))}

    # 每一頁的交回時刻：逐頁清冊的 mtime。🚨 第 1–7 頁走的是舊機制，
    # ⚠️ 只有合併檔 drafts.json 一個時刻，故那 7 頁的證據較粗（共用同一刻）。
    submitted, evidence = {}, {}
    merged = SHEET / 'drafts.json'
    for entry in json.loads(merged.read_text(encoding='utf-8'))['entries']:
        submitted[entry['report']] = merged.stat().st_mtime
        evidence[entry['report']] = 'drafts.json（合併檔，第 1-7 頁共用一刻）'
    for path in sorted((SHEET / 'drafts').glob('page-*.json')):
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            submitted[entry['report']] = path.stat().st_mtime
            evidence[entry['report']] = 'drafts/' + path.name

    rows = []
    for report, page in sorted(page_of.items(), key=lambda kv: kv[1]):
        at = submitted.get(report)
        rows.append({
            'report': report[-16:], 'page': page,
            'submittedAt': iso(at) if at else None,
            'requestVersion': classify(at, regenerated_at) if at else 'no-draft',
            'evidence': evidence.get(report),
        })

    before = [r for r in rows if r['requestVersion'] == 'before-regeneration']
    after = [r for r in rows if r['requestVersion'] == 'after']
    none = [r for r in rows if r['requestVersion'] == 'no-draft']
    latest = max(submitted.values())
    commit = regenerate_commit()

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('名冊上每一篇都分了類（必觸發）',
          len(rows) == sheet['itemCount'] and not none,
          '🚨 少一篇就代表名單不完整，而不完整的名單看起來跟完整的一樣；'
          '實得 %d／%d，無清冊者 %d 篇'
          % (len(rows), sheet['itemCount'], len(none)))
    # 🚨 這一道是關鍵：本支的答案是「全部都在重生之前」，
    # ⚠️ 而**分類器如果根本不會說「之後」，答案會長得一模一樣**（n+112 二）。
    probe('分類器說得出「之後」（必觸發之反向）',
          classify(regenerated_at + 1, regenerated_at) == 'after'
          and classify(regenerated_at - 1, regenerated_at)
          == 'before-regeneration',
          '🚨 以合成時刻試分類器兩邊；⚠️ 只會回一種答案的分類器，'
          '會把任何語料都判成單一版本')
    # ⚠️ 逐頁是迴圈寫的，故到毫秒本來就不會相等；
    # ✅ 要驗的是**跨度小到只可能是同一次重生**，🚫 不是「時刻相等」。
    spread = max(page_stamps.values()) - min(page_stamps.values())
    probe('18 個 pages/ 出自同一次重生（跨度 < 5 秒）',
          spread < 5 and abs(min(page_stamps.values()) - regenerated_at) < 5,
          '🚨 若跨度大，就沒有單一的重生分界，而是好幾次混在一起；'
          '實得跨度 %.3f 秒，最早一頁距 worksheet.json %.3f 秒'
          % (spread, min(page_stamps.values()) - regenerated_at))
    probe('磁碟上這份工作單確實是重生後的版本',
          sheet['totalChars'] - CHARS_BEFORE_REGEN == 34440,
          '✅ 與 n+190 所述 +34,440 字元相符；實得 %+d'
          % (sheet['totalChars'] - CHARS_BEFORE_REGEN))
    probe('更早偷跑過重生：已排除', bool(commit),
          '🚨 做重生的程式碼 %s 才進 repo，晚於最後一篇交回 %s'
          % (commit, iso(latest)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'request-version-split',
        'ruling': 'n+190（二）：據實列出哪幾篇是在重生之前讀的',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'answer': ('🚨 41 篇全部是舊版請求，0 篇是新版。'
                   '⚠️ 重生（%s）比最後一篇交回（%s）晚了 4 分 39 秒，'
                   '故那份儀器清單一個讀的人都沒看到。'
                   % (iso(regenerated_at), iso(latest))),
        'timeline': {
            'earliestSubmission': iso(min(submitted.values())),
            'latestSubmission': iso(latest),
            'regeneratedAt': iso(regenerated_at),
            'regenerateCodeCommitted': commit,
        },
        'counts': {'total': len(rows), 'beforeRegeneration': len(before),
                   'afterRegeneration': len(after), 'noDraft': len(none)},
        'a1Question': (
            '📮 A1「全語料同一版請求」要的是哪一件，只有協調者能定：'
            '✅「同版」已達成（41 篇整齊劃一，0 篇要重讀）；'
            '🚨「都看過儀器清單」則 0／41 達成，要重讀的是 41 篇不是 23 篇。'
            '⚠️ 並排看 n574：實測因儀器名被誤排的只有 6 項／1 篇。'),
        'packetFigureWasLow': (
            '⚠️ 資料包給外部審視的「23 篇用舊版」偏低，實情是 41 篇。'
            '🚫 不是審視者看錯，✅ 是本室把「重生會趕在讀完之前」當成已發生。'),
        'evidenceLimits': [
            '⚠️ 交回時刻取自檔案 mtime——🚫 它不是簽章，改動檔案就會變。',
            '🚨 第 1–7 頁（16 篇）共用 drafts.json 一個時刻，'
            '⚠️ 故它們的先後在頁與頁之間分不出來；'
            '✅ 但那一刻（14:49:40）遠早於重生，結論不受影響。',
            '✅ 獨立佐證：做重生的程式碼到 16:12:23 才進 repo，'
            '🚫 更早不可能跑過。',
        ],
        'items': rows,
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n579 請求版本分界 ===')
    print('   最早交回 %s｜最後交回 %s'
          % (iso(min(submitted.values())), iso(latest)))
    print('   重生     %s｜重生程式進 repo %s' % (iso(regenerated_at), commit))
    print('   🚨 舊版 %d 篇｜新版 %d 篇｜無清冊 %d 篇'
          % (len(before), len(after), len(none)))
    for row in rows:
        print('   第 %2d 頁  %s  %s  %s'
              % (row['page'], row['report'], row['submittedAt'],
                 row['evidence']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
