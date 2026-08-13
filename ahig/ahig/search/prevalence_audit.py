#!/usr/bin/env python3
"""S2 母體比例抽查：摘要層劑量回報率的人工稽核工具。

背景：S2（TT × ≥60 g/h）的合格池大小取決於「劑量有沒有寫在摘要裡」。在決定
strata 解法（合併層 / 兩階段抽樣 / 降配額 / 擴充 regex）之前，先量測母體：

- 隨機抽 N 篇 TT 候選（預設 50），由人讀摘要並回填判定；
- 以 Wilson 95% CI 推估「摘要有劑量」與「≥60 g/h」的母體比例；
- 對照現行 ``_dose_signals`` regex 與人工判定的差距，直接量測 regex 擴充的天花板。

這不是 screening，也不是校準集抽樣：

- 只讀取 candidate-pool 與 screening-queue，絕不改動它們；
- 抽到的紀錄不因此 include/exclude，``requiresHumanScreening`` 不受影響；
- 產出只用來支撐 strata 決策，決策本身仍由人做。

抽樣種子由呼叫者在抽樣當下指定並全程記錄（與 strata.json 的 seedPolicy 一致：
不預先寫死，避免「先看池子再挑種子」）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from ahig.search import screening
from ahig.state import atomic_write_json

AUDIT_DIRNAME = "prevalence-audit"
TT_OUTCOME = "tt-completion-time"
HIGH_BANDS = frozenset({"high", "very-high"})
JUDGED_BANDS = frozenset({"low", "moderate", "high", "very-high", "unclear"})
_Z95 = 1.959963984540054


def wilson_interval(successes: int, n: int, *, z: float = _Z95) -> tuple[float, float]:
    """Wilson score 95% 區間。n=0 時無資訊，回傳 (0, 1)。"""
    if n <= 0:
        return (0.0, 1.0)
    if not 0 <= successes <= n:
        raise ValueError(f"successes 必須在 [0, n]：{successes}/{n}")
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    # k=0 的下界、k=n 的上界解析上恰為 0 / 1；夾掉浮點殘差。
    lower = 0.0 if successes == 0 else max(0.0, centre - half)
    upper = 1.0 if successes == n else min(1.0, centre + half)
    return (lower, upper)


def _dose_signals_for(title: str | None, abstract: str | None) -> list[dict]:
    text = "\n".join(
        screening.normalise_for_matching(value) for value in (title, abstract))
    return screening._dose_signals(text)


def _sample_rank(seed: int, queue_hash: str, candidate_id: str) -> str:
    payload = f"{seed}\n{queue_hash}\n{candidate_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def draw_sample(run_root: Path, *, seed: int, n: int = 50,
                redo: bool = False) -> dict:
    """從 TT 候選中確定性抽 n 篇，寫出待人工回填的稽核檔與判讀表。"""
    run_root = Path(run_root).resolve()
    queue_dir = run_root / "screening-queue"
    queue_manifest = json.loads(
        (queue_dir / "manifest.json").read_text(encoding="utf-8"))
    queue = json.loads((queue_dir / "queue.json").read_text(encoding="utf-8"))
    candidates = json.loads(
        (run_root / "candidate-pool" / "candidates.json").read_text(
            encoding="utf-8"))
    by_id = {c["candidateId"]: c for c in candidates}

    tt_entries = [e for e in queue if TT_OUTCOME in e.get("outcomeHints", [])]
    if not tt_entries:
        raise ValueError("queue 中沒有任何 TT 候選（outcomeHints 含 "
                         f"{TT_OUTCOME}），無從稽核")

    queue_hash = queue_manifest["screeningQueueHash"]
    ranked = sorted(tt_entries,
                    key=lambda e: _sample_rank(seed, queue_hash,
                                               e["candidateId"]))
    effective_n = min(n, len(ranked))
    sampled = ranked[:effective_n]

    records = []
    for entry in sampled:
        candidate = by_id.get(entry["candidateId"], {})
        records.append({
            "candidateId": entry["candidateId"],
            "title": candidate.get("title"),
            "abstract": candidate.get("abstract"),
            "publicationYear": candidate.get("publicationYear"),
            "identifiers": candidate.get("identifiers", {}),
            # ---- 以下由人工回填 ----
            "doseMentionedInAbstract": None,   # true / false
            "maxDoseGramsPerHour": None,       # 數值；摘要沒寫明確數字則留 null
            "judgedBand": None,                # low / moderate / high / very-high / unclear
            "notes": None,
        })

    audit_id = hashlib.sha256(
        f"{seed}\n{queue_hash}\n{effective_n}".encode("utf-8")).hexdigest()[:12]
    audit = {
        "auditId": audit_id,
        "purpose": "abstract-dose-reporting-prevalence-audit",
        "notAScreeningDecision": True,
        "requiresHumanScreeningUnchanged": True,
        "runId": queue_manifest["runId"],
        "screeningQueueHash": queue_hash,
        "candidatePoolHash": queue_manifest["candidatePoolHash"],
        "seed": seed,
        "requestedSampleSize": n,
        "sampleSize": effective_n,
        "ttCandidateCount": len(tt_entries),
        "samplingRule": "sha256(seed, queueHash, candidateId) 升冪取前 n；"
                        "無放回、與輸入順序無關",
        "records": records,
    }

    out = run_root / AUDIT_DIRNAME / audit_id
    if out.exists():
        if not redo:
            raise FileExistsError(f"{out} 已存在；重抽請用 --redo")
        for name in ("audit.json", "reading-sheet.md", "estimate.json"):
            path = out / name
            if path.exists():
                path.unlink()
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "audit.json", audit)
    (out / "reading-sheet.md").write_text(_reading_sheet(audit),
                                          encoding="utf-8")
    return audit


def _reading_sheet(audit: dict) -> str:
    lines = [
        f"# 劑量回報率抽查判讀表（audit {audit['auditId']}）",
        "",
        f"- TT 候選母體：{audit['ttCandidateCount']} 篇，抽出 "
        f"{audit['sampleSize']} 篇（seed={audit['seed']}）",
        "- 任務：只讀下列標題與摘要，回填 `audit.json` 中每筆的四個欄位：",
        "  - `doseMentionedInAbstract`：摘要是否寫出攝取劑量（true/false）",
        "  - `maxDoseGramsPerHour`：最高劑量（換算成 g/h 的數值；沒寫明確數字"
        "留 null）",
        "  - `judgedBand`：low(<30) / moderate(30–59.9) / high(60–89.9) / "
        "very-high(≥90) / unclear",
        "  - `notes`：自由備註（可留 null）",
        "- 這是母體比例量測，不是篩選：不要做 include/exclude 判斷。",
        "- 判讀時請勿參考任何自動劑量偵測結果；regex 對照由 estimate 階段"
        "另行計算。",
        "",
    ]
    for i, record in enumerate(audit["records"], 1):
        lines += [
            f"## {i}. {record['candidateId']}",
            "",
            f"**{record.get('title') or '(無標題)'}**"
            + (f"（{record['publicationYear']}）"
               if record.get("publicationYear") else ""),
            "",
            record.get("abstract") or "（無摘要——doseMentionedInAbstract 填 "
            "false，notes 註明 no-abstract）",
            "",
        ]
    return "\n".join(lines)


def _validate_filled(records: list[dict]) -> None:
    problems = []
    for i, record in enumerate(records):
        mentioned = record.get("doseMentionedInAbstract")
        band = record.get("judgedBand")
        if not isinstance(mentioned, bool):
            problems.append(f"#{i} {record['candidateId']}: "
                            "doseMentionedInAbstract 未回填")
            continue
        if mentioned and band not in JUDGED_BANDS:
            problems.append(f"#{i} {record['candidateId']}: judgedBand 必須是 "
                            f"{sorted(JUDGED_BANDS)} 之一")
        if not mentioned and band is not None:
            problems.append(f"#{i} {record['candidateId']}: 未回報劑量卻填了 "
                            "judgedBand")
    if problems:
        raise ValueError("稽核表尚未回填完成：\n" + "\n".join(problems))


def estimate(audit_dir: Path, *, s2_quota: int = 10, redo: bool = False) -> dict:
    """讀回填完成的 audit.json，產出母體推估與 regex 對照。"""
    audit_dir = Path(audit_dir).resolve()
    audit = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    records = audit["records"]
    _validate_filled(records)

    n = len(records)
    mentioned = [r for r in records if r["doseMentionedInAbstract"]]
    judged_high = [r for r in mentioned if r["judgedBand"] in HIGH_BANDS]
    judged_unclear = [r for r in mentioned if r["judgedBand"] == "unclear"]

    regex_missed, regex_false_positive, regex_detected = [], [], []
    for record in records:
        signals = _dose_signals_for(record.get("title"), record.get("abstract"))
        if signals:
            regex_detected.append(record["candidateId"])
        if record["doseMentionedInAbstract"] and not signals:
            regex_missed.append(record["candidateId"])
        if not record["doseMentionedInAbstract"] and signals:
            regex_false_positive.append(record["candidateId"])

    k_m, k_h, k_u = len(mentioned), len(judged_high), len(judged_unclear)
    tt_count = audit["ttCandidateCount"]
    mentioned_ci = wilson_interval(k_m, n)
    high_ci = wilson_interval(k_h, n)
    high_given_mentioned_ci = wilson_interval(k_h, k_m) if k_m else None

    projected = {
        "point": round(tt_count * (k_h / n)) if n else None,
        "wilson95": [math.floor(tt_count * high_ci[0]),
                     math.ceil(tt_count * high_ci[1])],
        "upperIfUnclearAllHigh": math.ceil(
            tt_count * wilson_interval(k_h + k_u, n)[1]),
        "basis": "只涵蓋『摘要就寫了劑量』的部分；全文才寫劑量的研究不在此數，"
                 "兩階段抽樣（讀全文方法段）只會在此之上增加，不會減少。",
    }

    result = {
        "auditId": audit["auditId"],
        "runId": audit["runId"],
        "screeningQueueHash": audit["screeningQueueHash"],
        "seed": audit["seed"],
        "sampleSize": n,
        "ttCandidateCount": tt_count,
        "counts": {
            "doseMentioned": k_m,
            "judgedHighOrVeryHigh": k_h,
            "judgedUnclear": k_u,
            "regexDetectedAny": len(regex_detected),
            "humanFoundDoseButRegexMissed": len(regex_missed),
            "regexFoundButHumanSaysNoDose": len(regex_false_positive),
        },
        "estimates": {
            "doseMentionedInAbstract": {
                "point": k_m / n, "wilson95": list(mentioned_ci)},
            "highOrVeryHighDose": {
                "point": k_h / n, "wilson95": list(high_ci)},
            "highDoseAmongDoseMentioned": (
                {"point": k_h / k_m,
                 "wilson95": list(high_given_mentioned_ci)}
                if high_given_mentioned_ci else None),
        },
        "projection": projected,
        "regexAudit": {
            "missedCandidateIds": sorted(regex_missed),
            "falsePositiveCandidateIds": sorted(regex_false_positive),
            "note": "missed = 人說摘要有劑量、現行 regex 沒抓到；這就是選項 D"
                    "（regex 擴充）的可回收上限。false positive 需逐筆看 notes。",
        },
        "s2Quota": s2_quota,
        "guidance": _guidance(projected, s2_quota, k_h, k_m, len(regex_missed)),
        "decisionRemainsHuman": True,
    }

    out_path = audit_dir / "estimate.json"
    if out_path.exists() and not redo:
        raise FileExistsError(f"{out_path} 已存在；重算請用 --redo")
    atomic_write_json(out_path, result)
    return result


def _guidance(projected: dict, s2_quota: int, k_h: int, k_m: int,
              regex_missed: int) -> dict:
    lower, upper = projected["wilson95"]
    messages = []
    if lower >= 3 * s2_quota:
        stance = "abstract-pool-sufficient"
        messages.append(
            f"摘要可辨識的高劑量池下限 {lower} 已達配額 {s2_quota} 的 3 倍以上："
            "選項 D（regex 擴充）應已足夠，兩階段抽樣非必需。")
    elif upper < 1.5 * s2_quota:
        stance = "abstract-pool-insufficient"
        messages.append(
            f"即使取上限 {upper}，摘要可辨識池仍不足配額 {s2_quota} 的 1.5 倍："
            "光靠摘要救不回來。若全文劑量回報率也低，需檢討配額或合併層"
            "（選項 C/A）；否則走兩階段抽樣（選項 B）。先確認 blocker 決策。")
    else:
        stance = "two-stage-recommended"
        messages.append(
            f"摘要可辨識池推估區間 [{lower}, {upper}] 相對配額 {s2_quota} 屬"
            "邊際：建議 D 打底、B 收尾（兩階段：先擴 regex 縮小預抽樣池，"
            "再讀方法段定劑量）。")
        if k_h:
            pre_pool = math.ceil(s2_quota / (k_h / (k_m or 1)) * 1.5)
            messages.append(
                f"兩階段預抽樣池建議大小：約 {pre_pool} 篇"
                "（配額 ÷ 高劑量占比 × 1.5 安全係數）。")
    if regex_missed:
        messages.append(
            f"本樣本中有 {regex_missed} 篇摘要寫了劑量但現行 regex 沒抓到："
            "無論走哪條路，regex 擴充都有實測到的回收空間。")
    return {"stance": stance, "messages": messages,
            "note": "以上為決策輸入，不是決策；strata 解法仍由人拍板。"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_sample = sub.add_parser("sample", help="抽出待判讀樣本")
    p_sample.add_argument("run_root", type=Path)
    p_sample.add_argument("--seed", type=int, required=True,
                          help="抽樣種子；抽樣當下決定並全程記錄")
    p_sample.add_argument("--n", type=int, default=50)
    p_sample.add_argument("--redo", action="store_true")
    p_estimate = sub.add_parser("estimate", help="以回填完成的稽核表推估母體")
    p_estimate.add_argument("audit_dir", type=Path)
    p_estimate.add_argument("--s2-quota", type=int, default=10)
    p_estimate.add_argument("--redo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "sample":
        result = draw_sample(args.run_root, seed=args.seed, n=args.n,
                             redo=args.redo)
        out = {key: result[key] for key in
               ("auditId", "sampleSize", "ttCandidateCount", "seed")}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        result = estimate(args.audit_dir, s2_quota=args.s2_quota,
                          redo=args.redo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
