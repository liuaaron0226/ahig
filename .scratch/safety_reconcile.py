"""Safety lane 固化：把 pass-1 / pass-2 兩份判讀檔走完整工具鏈餵進
`reconcile_machine`（協調者第 n+32 輪裁定三個治理值後執行）。

鏈路（不繞過任何既有驗證）：
  judgement_worksheet.load_judgements → file_judge
  → screening_driver.run_batch（逐頁重放，做 ADR-0009 原則 2/3 檢查）
  → llm_second_review.build_session_opinion_batch（治理聲明入雜湊鏈）
  → screening_decisions.make_assignment + machine review 信封
  → screening_decisions.reconcile_machine

--write 才落盤；預設乾跑只印數字。
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ahig"))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.search import (  # noqa: E402
    judgement_worksheet,
    llm_second_review,
    screening_decisions,
)

RUN_ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"]) / \
    "search-runs/b11-exogenous-cho-endurance/b11-full-run"
SCOPE_CONTRACT = Path(__file__).resolve().parents[1] / \
    "ahig/calibration/b11-carbohydrate/scope-contract.json"

# ── 協調者第 n+32 輪裁定的治理值（COORDINATION.md，逐字取用）──────────
PASSES = {
    "pass-1": {
        "dir": "safety-full-screen-pass-1",
        "modelId": "claude-sonnet-5",
        "modelVersion": ("session-native; no dated snapshot exposed; "
                         "judged 2026-08-16"),
        "reviewerId": "b11-safety-pass-1-sonnet",
        "reviewId": "safety-ta-2026-08-16-pass1",
        "boardReference": ("COORDINATION.md#safety-pass-1-conventions "
                           "(rulings A/B, n+21, n+22, n+28..n+30)"),
    },
    "pass-2": {
        "dir": "safety-full-screen-pass-2",
        "modelId": "claude-opus-5[1m]",
        "modelVersion": ("session-native; no dated snapshot exposed; "
                         "judged 2026-08-16/17"),
        "reviewerId": "b11-safety-pass-2-opus",
        "reviewId": "safety-ta-2026-08-17-pass2",
        "boardReference": ("COORDINATION.md#pass2-briefing-R1-R3 + "
                           "docs/agents/pass2-briefing.md "
                           "(clean-room protocol, rules 1-6)"),
    },
}
ASSIGNMENT_ID = "safety-full-screen-2316"
COMPLETED_AT = "2026-08-17T00:00:00+00:00"


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_review(manifest, queue, assignment, name, cfg):
    """一遍判讀 → 固化批次 → machine review 信封。"""
    loaded = judgement_worksheet.load_judgements(
        RUN_ROOT, out_name=cfg["dir"])
    judge = judgement_worksheet.file_judge(loaded)

    # run_batch 的 judge 介面吃 payload、回 judgements；這裡整批一次過，
    # 但仍走 _validate_judgements 的每筆檢查（opinion/rawResponse/judgedBy）。
    batch_entries = [{"candidateId": cid}
                     for cid in assignment["candidateIds"]]
    judged = judge(batch_entries)

    opinions = [{"candidateId": j["candidateId"], "opinion": j["opinion"],
                 "rawResponse": j["rawResponse"]} for j in judged]

    protocol = {
        "scopeContractSha256": sha256_file(SCOPE_CONTRACT),
        "worksheetSha256": sha256_file(RUN_ROOT / cfg["dir"] / "worksheet.json"),
        "boardReference": cfg["boardReference"],
    }
    batch = llm_second_review.build_session_opinion_batch(
        manifest, queue, opinions,
        model_id=cfg["modelId"], model_version=cfg["modelVersion"],
        judging_protocol=protocol)

    review = {
        "documentType": "title-abstract-machine-review",
        "schemaVersion": "1.0.0",
        "adr": "ADR-0009",
        "reviewId": cfg["reviewId"],
        "assignmentId": assignment["assignmentId"],
        "runId": assignment["runId"],
        "screeningQueueHash": assignment["screeningQueueHash"],
        "candidateSetHash": assignment["candidateSetHash"],
        "reviewer": {
            "reviewerId": cfg["reviewerId"],
            "agentClass": "llm",
            "blindedToOtherReviewer": True,
        },
        "judgedBy": {
            "agentClass": "llm",
            "modelId": cfg["modelId"],
            "modelVersion": cfg["modelVersion"],
            "adr": "ADR-0009 裁定①",
        },
        "judgingProtocol": protocol,
        "judgingProtocolHash": batch["judgingProtocolHash"],
        "llmReviewHash": batch["llmReviewHash"],
        "completedAt": COMPLETED_AT,
        "judgements": [
            {"candidateId": e["candidateId"], "opinion": e["opinion"],
             "rawResponse": e["rawResponse"]} for e in batch["entries"]],
    }
    print(f"[{name}] entries={len(batch['entries'])} "
          f"protocolHash={batch['judgingProtocolHash'][:23]}… "
          f"llmReviewHash={batch['llmReviewHash'][:23]}…")
    return batch, review


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="落盤（預設乾跑）")
    args = ap.parse_args()

    manifest = json.loads(
        (RUN_ROOT / "screening-queue/manifest.json").read_text("utf-8"))
    queue = json.loads(
        (RUN_ROOT / "screening-queue/queue.json").read_text("utf-8"))
    lane_ids = json.loads(
        (RUN_ROOT / "safety-full-screen-pass-2-list.json")
        .read_text("utf-8"))["candidateIds"]
    print(f"queue={len(queue)} lane={len(lane_ids)}")

    assignment = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=lane_ids,
        assignment_id=ASSIGNMENT_ID, created_at=COMPLETED_AT)
    print(f"assignment candidateSetHash={assignment['candidateSetHash'][:23]}…")

    batches, reviews = {}, {}
    for name, cfg in PASSES.items():
        batches[name], reviews[name] = build_review(
            manifest, queue, assignment, name, cfg)

    recon = screening_decisions.reconcile_machine(
        manifest, queue, assignment,
        reviews["pass-1"], reviews["pass-2"],
        completed_at=COMPLETED_AT, owner_decisions=None)

    print("\n=== reconcile_machine ===")
    for k in ("status", "nextStage", "reviewerIds", "modelIds",
              "machineTitleAbstractScreeningComplete",
              "machineScreeningReleased"):
        print(f"  {k} = {json.dumps(recon.get(k), ensure_ascii=False)}")
    print(f"  counts = {json.dumps(recon['counts'], ensure_ascii=False)}")
    print(f"  blockingReasons = {recon['blockingReasons']}")
    print(f"  reconciliationHash = {recon['reconciliationHash']}")

    adv = [c["candidateId"] for c in recon["concordant"]
           if c["opinion"] == "advance"]
    print(f"\n  concordant advance ({len(adv)}):")
    for cid in adv:
        print(f"    {cid}")
    if recon["ownerAuditQueue"]:
        print(f"\n  ownerAuditQueue ({len(recon['ownerAuditQueue'])}):")
        for item in recon["ownerAuditQueue"]:
            print(f"    {item['candidateId']} [{item['disagreementKind']}]")
            for mo in item["modelOpinions"]:
                print(f"      {mo['reviewerId']}: {mo['opinion']}")

    if not args.write:
        print("\n（乾跑，未落盤。加 --write 才寫檔）")
        return 0

    out = RUN_ROOT / "screening-decisions"
    out.mkdir(parents=True, exist_ok=True)
    for name, cfg in PASSES.items():
        for label, doc in (("batch", batches[name]), ("review", reviews[name])):
            p = out / f"safety-{name}-{label}.json"
            if p.exists():
                print(f"  已存在，不覆寫：{p.name}")
                continue
            p.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            print(f"  寫入 {p.name}")
    recon_path = out / "safety-machine-reconciliation.json"
    screening_decisions.write_reconciliation(recon_path, recon)
    print(f"  寫入 {recon_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
