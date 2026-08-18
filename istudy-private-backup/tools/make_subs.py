# -*- coding: utf-8 -*-
"""替已下載的課程影片產生繁體中文字幕（.vtt），與影片放在一起。

實測（RTX 3060 6GB、large-v3、int8_float16）：
  逐段 beam=1  → 7.7x 實時、平均 1.4 秒/句   ← 採用
  逐段 beam=5  → 7.0x 實時、平均 1.6 秒/句
  批次 batch=16→ 22.6x 但 30 秒併成一段且出現重複幻覺，當字幕不可用
Whisper 輸出簡體，統一用 OpenCC s2twp 轉臺灣正體。

用法：
  python tools/make_subs.py --limit 1        # 先做一支
  python tools/make_subs.py                  # 全部沒字幕的都做（可中斷續跑）
  python tools/make_subs.py --only 115春矩陣  # 只做代號含指定字串的
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

OUT_ROOT = Path(r"F:\istudy-backup")
STATE_FILE = OUT_ROOT / "state.json"
LOG = OUT_ROOT / "subs.log"
MODEL = "large-v3"


def setup_cuda() -> bool:
    """pip 版 CUDA 執行庫不在 PATH，要手動掛進 DLL 搜尋路徑。"""
    try:
        import nvidia
    except ImportError:
        return False
    found = False
    for root in list(nvidia.__path__):
        for sub in ("cublas", "cudnn"):
            for leaf in ("bin", os.path.join("lib", "x64")):
                p = os.path.join(root, sub, leaf)
                if os.path.isdir(p):
                    os.add_dll_directory(p)
                    os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
                    found = True
    return found


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# 語音辨識常見的術語誤字 → 正確寫法。
# 刻意留空起步：先跑一支課看實際錯在哪，再據實補進來，不要憑空猜。
FIXES: list[tuple[str, str]] = [
    # (誤, 正) 例：(r"奈式", "奈氏"),
]

# 勘誤飛輪：make_notes.py 分析影片時找到的錯詞累積在 fixes.json，按科目分桶
# （「志工→資工」在線代裡對、在多益裡是災難）。字面替換，AI 給的字串不當 regex 用。
FILE_FIXES: dict[str, dict[str, str]] = {}


def load_file_fixes() -> int:
    try:
        d = json.loads((OUT_ROOT / "fixes.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 0
    if d and all(isinstance(x, str) for x in d.values()):
        d = {"線代": d}              # 試產期的扁平舊格式
    total = 0
    for subj, m in d.items():
        if not isinstance(m, dict):
            continue
        FILE_FIXES[subj] = {k: v for k, v in m.items()
                            if isinstance(k, str) and isinstance(v, str)
                            and len(k) >= 2 and k != v}
        total += len(FILE_FIXES[subj])
    return total


def apply_fixes(text: str, lit=()) -> str:
    for bad, good in FIXES:
        text = re.sub(bad, good, text)
    for bad, good in lit:
        text = text.replace(bad, good)
    return text


def ts(sec: float) -> str:
    h = int(sec // 3600); m = int(sec % 3600 // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def write_vtt(segs, dest: Path, cc, lit=()) -> int:
    lines = ["WEBVTT", ""]
    n = 0
    for s in segs:
        txt = apply_fixes(cc.convert(s.text.strip()), lit)
        if not txt:
            continue
        lines.append(f"{ts(s.start)} --> {ts(s.end)}")
        lines.append(txt)
        lines.append("")
        n += 1
    tmp = dest.with_suffix(".vtt.tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    tmp.replace(dest)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--beam", type=int, default=1)
    args = ap.parse_args()

    if not setup_cuda():
        log("找不到 CUDA 執行庫（pip install nvidia-cublas-cu12 nvidia-cudnn-cu12）")
    n_fix = load_file_fixes()
    if n_fix:
        log(f"勘誤飛輪：載入 fixes.json 共 {n_fix} 條")
    from faster_whisper import WhisperModel
    from opencc import OpenCC
    cc = OpenCC("s2twp")

    st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    todo = []
    for v in st.values():
        if v.get("status") != "done" or not v.get("path"):
            continue
        mp4 = Path(v["path"])
        if not mp4.exists():
            continue
        if args.only and args.only not in v.get("code", ""):
            continue
        if mp4.with_suffix(".vtt").exists():
            continue
        todo.append((v, mp4))
    todo.sort(key=lambda x: x[0]["code"])
    if args.limit:
        todo = todo[:args.limit]
    log(f"待製字幕 {len(todo)} 支")
    if not todo:
        return 0

    t0 = time.time()
    model = WhisperModel(args.model, device="cuda", compute_type="int8_float16")
    log(f"模型載入 {time.time()-t0:.0f}s")

    for i, (v, mp4) in enumerate(todo, 1):
        dest = mp4.with_suffix(".vtt")
        log(f"▶ [{i}/{len(todo)}] {v['code']}｜{v.get('title','')[:34]}")
        t = time.time()
        try:
            segs, info = model.transcribe(
                str(mp4), language="zh", beam_size=args.beam, vad_filter=True,
                condition_on_previous_text=False,   # 避免上下文把後段帶進重複迴圈
            )
            lit = FILE_FIXES.get(v.get("series", "").split("/")[0], {}).items()
            n = write_vtt(segs, dest, cc, lit)
            el = time.time() - t
            rate = (v.get("sec") or 0) / max(el, 1)
            log(f"  ✓ {n} 句・耗時 {el/60:.1f} 分・{rate:.1f}x 實時 → {dest.name}")
        except Exception as exc:  # noqa: BLE001
            log(f"  ✗ 失敗：{str(exc)[:200]}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
