# -*- coding: utf-8 -*-
"""替已有字幕的課程影片產生「思考地圖」筆記（.notes.json），並做四件副產品：
  ① 勘誤套回 .vtt、累積到 fixes.json（勘誤飛輪，make_subs.py 會讀）
  ② 重點時段在 .vtt 以 <c.key> 標記（網站用 ::cue(.key) 上色）
  ③ ffmpeg 抽板書快照 <影片名>.snap_<秒>.jpg
  ④ 重建全文搜尋索引 search_index.json

分析引擎是 claude -p（無頭模式），一部影片一個呼叫，逐字稿全文塞進 prompt。

用法：
  python tools/make_notes.py --limit 1 --only 115暑線代01   # 試產一支
  python tools/make_notes.py                                # 依衝刺週序補齊全部
  python tools/make_notes.py --index-only                   # 只重建搜尋索引
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

OUT_ROOT = Path(r"F:\istudy-backup")
STATE_FILE = OUT_ROOT / "state.json"
FIXES_FILE = OUT_ROOT / "fixes.json"
INDEX_FILE = OUT_ROOT / "search_index.json"
LOG = OUT_ROOT / "notes.log"
HERE = Path(__file__).resolve().parent
PROMPT_FILE = HERE / "notes_prompt.md"
HUB = Path(r"C:\Users\User\Desktop\claude\grad-exam-hub")

SUBJ_FULL = {"電子學": "電子學", "工數": "工程數學", "線代": "線性代數",
             "多益": "多益", "控制": "自動控制"}
CLAUDE_TIMEOUT = 1500          # 秒；3 小時課的地圖生成實測需要數分鐘，抓寬
SNAP_LIMIT = 6
# 寫死模型與思考強度，不跟著全域設定漂移：這批筆記是同一套複習素材，
# 全域若改成較弱的模型，會默默產出半套 Opus 半套別的，事後也分不出哪集是哪個做的。
# 電子學／工數的觀念錯誤，初學者看不出來，所以這裡不省。
NOTES_MODEL = "opus[1m]"
NOTES_EFFORT = "xhigh"


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def norm(code: str) -> str:
    return code.replace("(喻)", "")


def hms(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


# ---------- 衝刺週序：code → (章節名, 週) ----------

def chapter_week_map() -> dict[str, tuple[str, int]]:
    try:
        videos = json.loads((HUB / "data" / "videos.json").read_text(encoding="utf-8"))
        sprint = json.loads((HUB / "data" / "sprint.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        log(f"讀 videos/sprint.json 失敗，不排優先序：{str(exc)[:80]}")
        return {}
    info: dict[str, tuple[str, int]] = {}
    chap: dict[str, tuple[str, int]] = {}
    for s in sprint.get("subjects", []):
        for c in s.get("chapters", []):
            chap[c["id"]] = (c.get("name", c["id"]), int(c.get("week", 9)))
    for cid, eps in videos.get("istudy", {}).get("byChapter", {}).items():
        name, week = chap.get(cid, (cid, 9))
        for e in eps:
            info[norm(e["code"])] = (name, week)
    return info


# ---------- VTT ----------

TS = re.compile(r"^(\d{2,}):(\d{2}):(\d{2})\.(\d{3}) --> (\d{2,}):(\d{2}):(\d{2})\.(\d{3})")


def vtt_cues(path: Path) -> list[tuple[float, float, str]]:
    cues: list[tuple[float, float, str]] = []
    cur: tuple[float, float] | None = None
    buf: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines() + [""]:
        m = TS.match(raw)
        if m:
            if cur and buf:
                cues.append((cur[0], cur[1], " ".join(buf)))
            g = [int(x) for x in m.groups()]
            cur = (g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                   g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000)
            buf = []
        elif raw.strip() == "":
            if cur and buf:
                cues.append((cur[0], cur[1], " ".join(buf)))
            cur = None
            buf = []
        elif cur is not None:
            buf.append(re.sub(r"</?c[^>]*>", "", raw.strip()))
    return cues


# ---------- prompt 組裝與 claude -p ----------

def build_prompt(v: dict, cues, chapinfo: tuple[str, int] | None) -> str:
    tpl = PROMPT_FILE.read_text(encoding="utf-8")
    subj = SUBJ_FULL.get(v["series"].split("/")[0], v["series"].split("/")[0])
    chap = f"{chapinfo[0]}（衝刺第 {chapinfo[1]} 週）" if chapinfo else "（未對應）"
    lines = "\n".join(f"{int(a)}|{t}" for a, _b, t in cues if t)
    dur = int(v.get("sec") or (cues[-1][1] if cues else 0))
    return (tpl.replace("«SUBJECT»", subj)
               .replace("«CODE»", v["code"])
               .replace("«TITLE»", v.get("title", ""))
               .replace("«CHAPTER»", chap)
               .replace("«DUR»", hms(dur))
               .replace("«DURSEC»", str(dur))
               .replace("«TRANSCRIPT»", lines))


def call_claude(prompt: str) -> str:
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("找不到 claude CLI")
    r = subprocess.run([exe, "-p", "--output-format", "text",
                        "--model", NOTES_MODEL, "--effort", NOTES_EFFORT],
                       input=prompt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=CLAUDE_TIMEOUT, cwd=str(OUT_ROOT))
    if r.returncode != 0:
        raise RuntimeError(f"claude -p 退出碼 {r.returncode}：{(r.stderr or '')[:200]}")
    return r.stdout


def extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("輸出裡沒有 JSON 物件")
    return json.loads(text[a:b + 1])


# ---------- 驗證與收斂 ----------

def clampt(t, dur: int) -> int:
    try:
        return max(0, min(int(float(t)), dur))
    except (TypeError, ValueError):
        return 0


def validate(d: dict, dur: int) -> dict:
    out: dict = {"version": 1}
    fixes = []
    for p in d.get("fixes", []):
        if (isinstance(p, (list, tuple)) and len(p) == 2
                and all(isinstance(x, str) for x in p)
                and len(p[0]) >= 2 and p[0] != p[1]):
            fixes.append([p[0], p[1]])
    out["fixes"] = fixes

    chs = sorted({clampt(c.get("t"), dur): str(c.get("title", ""))[:20]
                  for c in d.get("chapters", []) if isinstance(c, dict)}.items())
    out["chapters"] = [{"t": t, "title": ti} for t, ti in chs if ti]

    keys = []
    for k in d.get("keys", []):
        if not isinstance(k, dict):
            continue
        a, b = clampt(k.get("a"), dur), clampt(k.get("b"), dur)
        if b > a:
            keys.append({"a": a, "b": b, "why": str(k.get("why", ""))[:40]})
    out["keys"] = sorted(keys, key=lambda x: x["a"])

    snaps = []
    for s in d.get("snaps", []):
        if isinstance(s, dict):
            t = clampt(s.get("t"), dur)
            if t:
                snaps.append({"t": t, "cap": str(s.get("cap", ""))[:40]})
    out["snaps"] = sorted(snaps, key=lambda x: x["t"])[:SNAP_LIMIT]

    m = d.get("map") or {}
    out["map"] = {
        "tldr": [str(x) for x in m.get("tldr", [])][:8],
        "concepts": [c for c in m.get("concepts", []) if isinstance(c, dict) and c.get("name")],
        "flow": str(m.get("flow", "")),
        "examples": [{**e, "t": clampt(e.get("t"), dur), "snap": clampt(e.get("snap"), dur)}
                     for e in m.get("examples", []) if isinstance(e, dict)],
        "pitfalls": [str(x) for x in m.get("pitfalls", [])],
    }
    return out


# ---------- 副產品 ----------

def apply_to_vtt(vtt: Path, fixes: list[list[str]], keys: list[dict]) -> None:
    """勘誤字面替換＋重點時段 <c.key> 標記。可重複執行（先剝舊標記）。"""
    text = vtt.read_text(encoding="utf-8")
    text = text.replace("<c.key>", "").replace("</c>", "")
    for bad, good in fixes:
        text = text.replace(bad, good)
    lines = text.splitlines()
    out: list[str] = []
    hot = False
    for ln in lines:
        m = TS.match(ln)
        if m:
            g = [int(x) for x in m.groups()[:4]]
            start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
            hot = any(k["a"] <= start <= k["b"] for k in keys)
            out.append(ln)
        elif hot and ln.strip() and "-->" not in ln and ln != "WEBVTT":
            out.append(f"<c.key>{ln}</c>")
        else:
            out.append(ln)
    tmp = vtt.with_suffix(".vtt.tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
    tmp.replace(vtt)


def extract_snaps(mp4: Path, snaps: list[dict]) -> int:
    n = 0
    for s in snaps:
        dest = mp4.with_name(f"{mp4.stem}.snap_{s['t']}.jpg")
        if dest.exists():
            continue
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-ss", str(s["t"]), "-i", str(mp4),
                            "-frames:v", "1", "-q:v", "3", "-y", str(dest)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and dest.exists():
            n += 1
        else:
            log(f"  快照 {s['t']}s 失敗：{(r.stderr or '')[:80]}")
    return n


def rebuild_fixes(state: dict) -> dict[str, int]:
    """從所有 notes.json 重建勘誤飛輪，格式 {科目: {誤: [正, 幾支影片提過]}}。

    分兩層防護：
    ① 按科目分桶——「志工→資工」在線代裡對，套到多益是災難。
    ② 只有「兩支以上影片各自獨立提出」的規則才會被 make_subs.py 套用。
       單支提出的留在檔案裡（n=1）但不生效：系統性的聽錯會在不同堂課重複出現，
       一次性的多半是那堂課的上下文產物。實例：線代 05 一支就吐 326 條，裡面
       混進「反正→反證」——「反正」是老師口頭禪，全庫 85 次，無條件替換會安靜
       毀掉教材而且事後查不出來。
    """
    votes: dict[str, dict[str, dict[str, int]]] = {}
    for v in state.values():
        if not v.get("path"):
            continue
        notes = Path(v["path"]).with_suffix(".notes.json")
        if not notes.exists():
            continue
        try:
            d = json.loads(notes.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        subj = v.get("series", "").split("/")[0]
        for pair in d.get("fixes", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                bad, good = pair
                votes.setdefault(subj, {}).setdefault(bad, {})
                votes[subj][bad][good] = votes[subj][bad].get(good, 0) + 1
    out: dict[str, dict[str, list]] = {}
    stat: dict[str, int] = {}
    for subj, rules in votes.items():
        bucket = {}
        for bad, goods in rules.items():
            good, n = max(goods.items(), key=lambda kv: kv[1])
            bucket[bad] = [good, n]
        out[subj] = dict(sorted(bucket.items(), key=lambda kv: -kv[1][1]))
        stat[subj] = sum(1 for g, n in out[subj].values() if n >= 2)
    FIXES_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    return stat


def rebuild_index(state: dict) -> None:
    """所有 .vtt → 20 秒窗的全文索引，網站搜尋用。"""
    bypath = {v["path"]: v for v in state.values() if v.get("path")}
    vids = []
    for vtt in sorted(OUT_ROOT.rglob("*.vtt")):
        mp4 = vtt.with_suffix(".mp4")
        meta = bypath.get(str(mp4))
        if not meta:
            continue
        windows: list[list] = []
        wstart, wtxt = None, []
        for a, _b, t in vtt_cues(vtt):
            if wstart is None:
                wstart = a
            wtxt.append(t)
            if a - wstart >= 20 or sum(len(x) for x in wtxt) > 90:
                windows.append([int(wstart), " ".join(wtxt)])
                wstart, wtxt = None, []
        if wtxt:
            windows.append([int(wstart or 0), " ".join(wtxt)])
        vids.append({"code": meta["code"], "title": meta.get("title", ""),
                     "rel": mp4.relative_to(OUT_ROOT).as_posix(),
                     "cues": windows})
    INDEX_FILE.write_text(json.dumps(
        {"updated": time.strftime("%Y-%m-%d %H:%M"), "videos": vids},
        ensure_ascii=False), encoding="utf-8")
    log(f"搜尋索引重建：{len(vids)} 支影片 → {INDEX_FILE.name}"
        f"（{INDEX_FILE.stat().st_size // 1024} KB）")


# ---------- 主流程 ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--index-only", action="store_true")
    ap.add_argument("--dry", action="store_true", help="只列清單不執行")
    args = ap.parse_args()

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if args.index_only:
        rebuild_index(state)
        return 0

    cwmap = chapter_week_map()
    onlys = [s.strip() for s in args.only.split(",") if s.strip()]
    todo = []
    for v in state.values():
        if v.get("status") != "done" or not v.get("path"):
            continue
        mp4 = Path(v["path"])
        vtt = mp4.with_suffix(".vtt")
        notes = mp4.with_suffix(".notes.json")
        if not mp4.exists() or not vtt.exists():
            continue
        if onlys and not any(o in v["code"] or o in norm(v["code"]) for o in onlys):
            continue
        if notes.exists() and not args.force:
            continue
        week = cwmap.get(norm(v["code"]), ("", 9))[1]
        todo.append((week, v["code"], v, mp4, vtt, notes))
    todo.sort(key=lambda x: (x[0], x[1]))
    if args.limit:
        todo = todo[:args.limit]
    log(f"待產思考地圖 {len(todo)} 支")
    for week, _c, v, *_ in todo:
        log(f"  W{week} {v['code']}｜{v.get('title', '')[:30]}")
    if args.dry or not todo:
        return 0

    done = 0
    for week, _c, v, mp4, vtt, notes in todo:
        log(f"▶ [{done + 1}/{len(todo)}] {v['code']}（W{week}）")
        t0 = time.time()
        try:
            cues = vtt_cues(vtt)
            prompt = build_prompt(v, cues, cwmap.get(norm(v["code"])))
            log(f"  逐字稿 {len(cues)} 句、prompt {len(prompt) // 1000}k 字，呼叫 claude -p …")
            raw = call_claude(prompt)
            try:
                data = extract_json(raw)
            except (ValueError, json.JSONDecodeError):
                log("  第一次輸出不是合法 JSON，重試一次")
                raw = call_claude(prompt + "\n\n（再次強調：只輸出 JSON 物件本身，不要任何其他文字）")
                data = extract_json(raw)
            dur = int(v.get("sec") or (cues[-1][1] if cues else 0))
            data = validate(data, dur)
            data["code"] = v["code"]
            data["dur"] = dur
            data["by"] = f"{NOTES_MODEL}/{NOTES_EFFORT}"   # 日後品質有落差時查得出是誰做的
            tmp = notes.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            tmp.replace(notes)
            apply_to_vtt(vtt, data["fixes"], data["keys"])
            ns = extract_snaps(mp4, data["snaps"])
            log(f"  ✓ {time.time() - t0:.0f}s：章節 {len(data['chapters'])}"
                f"・重點 {len(data['keys'])}・例題 {len(data['map']['examples'])}"
                f"・勘誤 {len(data['fixes'])}・快照 {ns}/{len(data['snaps'])}")
            done += 1
        except Exception as exc:  # noqa: BLE001
            log(f"  ✗ 失敗：{str(exc)[:200]}")
    rebuild_index(state)
    stat = rebuild_fixes(state)
    log(f"勘誤飛輪重建：{ {k: f'{v} 條生效' for k, v in stat.items()} }（需 2 支以上影片各自提過）")
    log(f"完成 {done}/{len(todo)}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
