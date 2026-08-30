# -*- coding: utf-8 -*-
"""私有根之前置檢查：**來源不在就拒絕產出，🚫 不得產出一個「零」再落盤。**

## 🚨 事故（n+162 九）

協調者跑了本室之總跑套件一次。**⚠️ 而那不是唯讀動作**：

```
n492_stratum_table.json → totals.withBackfill   27 → 0
n499_calibration_redraw.json                    整份被重寫
```

**🚨 成因**：那幾支是產生器，資料源在私有根。
**⚠️ 在協調者的環境裡私有根不存在，而它們沒有拒絕**——
**🚨 它們量到「什麼都沒有」，然後把 0 寫回去，並以 0 結束（通過）。**

> **🚨 這是字面意義上的 fail-open。**
> **⚠️ 而被寫壞的正是協調者在引用的來源**（`EXTRACTABLE_N`、`S56_ACQ`、`S3_ACQ_BACKFILL`）。
> **🚨 若沒有人在提交前看一眼 `git status`，之後每一個引用該檔的數字都會是 0，而閘門全綠。**

**⚠️ 它是型錄第 13 型（護欄失敗而被護之動作照跑）的近親**——
**🚨 這次是「量測失敗而落盤照跑」。**

## ✅ 本檔即那道拒絕

**🚨 一個「量到零」與一個「量不到」，在檔案裡必須看得出來。**
故凡讀私有根之產生器，**開頭第一件事就是 `require(...)`**：

- 🚫 `AHIG_PRIVATE_ROOT` 未設定 → **拒絕**
- 🚫 該路徑不存在或不是目錄 → **拒絕**
- 🚫 指定之子路徑缺任何一個 → **拒絕**
- 🚫 `fulltext/` 內找不到任何 artifact 目錄 → **拒絕**（⚠️ 空殼目錄照樣是空的）

**拒絕＝印出確切原因並以 `exit 2` 結束，🚨 且發生在任何寫檔之前。**

**⚠️ 為什麼是 2 而不是 1**：🚨 1 是「檢查跑了而且不通過」，
**2 是「這裡根本不該跑」**——兩者對讀者是不同的事。

## 🚨 一併移除 `setdefault` 那個陷阱

各支原本都寫 `os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/...')`。
**⚠️ 那行在別台機器上會「成功」地把根設成一個不存在的路徑，
🚨 於是後續每一個讀取都安靜地讀到空的。**
**✅ 本檔改為：預設值仍給，但給完立刻驗——存在才算數。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 擋得住：根不存在、子路徑缺失、`fulltext/` 是空殼。
- 🚨 擋不住：**根存在但內容被截斷**（例如只複製了一半的紀錄）——
  ⚠️ 那看起來就是一個比較小的真實母體，**🚫 本檔分不出來。**
  **✅ 故 `require()` 一併回傳實際看到的 artifact 目錄數，供產生器寫進產物；
  🚨 數字變小時，讀的人至少看得到它變小了。**
"""
import os
import re
import sys
from pathlib import Path

DEFAULT = r'C:/Users/User/Desktop/claude/ahig-private'
ARTIFACT_DIR = re.compile(r'-[0-9a-f]{16}$')
EXIT_WRONG_PLACE = 2


def _die(reasons):
    print('🚨 私有根前置檢查未過——🚫 拒絕產出（n+162 九之二）：', file=sys.stderr)
    for r in reasons:
        print('   🚫 %s' % r, file=sys.stderr)
    print('   ⚠️ 一個「量到零」與一個「量不到」在檔案裡必須看得出來；'
          '🚨 故本支不寫入任何值。', file=sys.stderr)
    sys.exit(EXIT_WRONG_PLACE)


def require(*needs, want_fulltext=True):
    """驗私有根，回傳 (root, provenance)。🚨 不通過即 `exit 2`，🚫 不回傳。

    `needs` 為相對於私有根之子路徑；`want_fulltext` 另要求 `fulltext/`
    內至少有一個 artifact 目錄（⚠️ 空殼目錄照樣是空的）。
    """
    raw = os.environ.get('AHIG_PRIVATE_ROOT') or DEFAULT
    root = Path(raw)
    reasons = []
    if not root.is_dir():
        reasons.append('私有根不存在或不是目錄：%s' % root)
        _die(reasons)
    for n in needs:
        if not (root / n).exists():
            reasons.append('缺子路徑：%s' % n)
    n_art = 0
    if want_fulltext:
        ft = root / 'fulltext'
        if not ft.is_dir():
            reasons.append('缺 fulltext/')
        else:
            n_art = sum(1 for p in ft.iterdir()
                        if p.is_dir() and ARTIFACT_DIR.search(p.name))
            if not n_art:
                reasons.append('fulltext/ 內找不到任何 artifact 目錄'
                               '——⚠️ 空殼與「真的沒有取得」在檔案裡分不出來')
    if reasons:
        _die(reasons)
    os.environ['AHIG_PRIVATE_ROOT'] = str(root)
    return root, {'privateRootVerified': True,
                  'artifactDirectoriesSeen': n_art,
                  'note': 'Recorded so a truncated source shows up as a smaller '
                          'number rather than passing silently. The preflight '
                          'can tell a missing root from a present one; it cannot '
                          'tell a complete root from a half-copied one.'}


def _selftest():
    """🚨 正反兩向；⚠️ 反向以子行程跑，因為不通過會 `exit`。"""
    import subprocess
    import tempfile
    ok = True

    def say(name, cond, detail=''):
        nonlocal ok
        ok = ok and cond
        print('   %s %-40s %s' % ('✅' if cond else '🚨', name, detail))

    code = ('import sys; sys.path.insert(0, r"%s");'
            'import private_root; private_root.require(); print("REACHED")'
            % os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ, PYTHONIOENCODING='utf-8')

    # 反向甲：根不存在 → 必須 exit 2 且不得印出 REACHED
    bad = os.path.join(tempfile.gettempdir(), 'n162-no-such-root')
    r = subprocess.run([sys.executable, '-c', code],
                       env=dict(env, AHIG_PRIVATE_ROOT=bad),
                       capture_output=True, encoding='utf-8', errors='replace')
    say('反向甲：根不存在 → exit 2 且未執行後續',
        r.returncode == EXIT_WRONG_PLACE and 'REACHED' not in (r.stdout or ''),
        'rc=%s' % r.returncode)

    # 反向乙：根存在但 fulltext/ 是空的 → 亦須拒絕
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / 'fulltext').mkdir()
        r = subprocess.run([sys.executable, '-c', code],
                           env=dict(env, AHIG_PRIVATE_ROOT=tmp),
                           capture_output=True, encoding='utf-8',
                           errors='replace')
        say('反向乙：fulltext/ 空殼 → exit 2',
            r.returncode == EXIT_WRONG_PLACE, 'rc=%s' % r.returncode)

    # 正向：真的私有根 → 必須通過
    # 🚨 沒有這一道，一個「永遠拒絕」的實作也會讓上面兩道全綠。
    r = subprocess.run([sys.executable, '-c', code], env=env,
                       capture_output=True, encoding='utf-8', errors='replace')
    say('正向：真實私有根 → 通過並繼續',
        r.returncode == 0 and 'REACHED' in (r.stdout or ''),
        'rc=%s' % r.returncode)
    return ok


if __name__ == '__main__':
    print('=== 私有根前置檢查之自測（n+162 九之二）===')
    good = _selftest()
    if good:
        root, prov = require()
        print('   ✅ 現行私有根 %s；artifact 目錄 %d 個'
              % (root, prov['artifactDirectoriesSeen']))
    print('%s 自測%s' % ('✅' if good else '🚨', '全綠' if good else '未過'))
    sys.exit(0 if good else 1)
