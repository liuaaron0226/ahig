#!/usr/bin/env python3
"""standard-screening lane 的 active-learning 第三排序鍵。

**這個模組只會重排順序，不會改變任何一筆候選的去留。**queue 成員、
``screeningLane``、``priorityTier``、``requiresHumanScreening`` 一律原封不動；
AL 分數只在 ``standard-screening`` lane 內部、且在 ``priorityTier`` 之下當作
第三排序鍵使用。低分候選不會被移出 queue，也不會被自動排除——這是
screening.py 「priority-only-never-auto-include-or-exclude」不變量的延伸。

排序組合照抄 ASReview 的 ``elas_u4`` 預設模型（Apache-2.0）。ASReview 本身
未併入依賴（見 COORDINATION.md 協調者對 T1 的裁定「借邏輯、不併依賴」），
只以 scikit-learn 重寫等價組合。超參數出處：

* ``asreview/models/models.py`` — ``elas_u4``：querier=max、classifier=svm、
  ``{"loss": "squared_hinge", "C": 0.11}``、balancer=balanced ``{"ratio": 9.8}``、
  feature_extractor=tfidf
  ``{"ngram_range": (1, 2), "sublinear_tf": True, "min_df": 1, "max_df": 0.95}``。
  上游註記該組參數是在 SYNERGY 資料集上最佳化的結果。
* ``asreview/models/classifiers.py`` — ``SVM`` 是 ``sklearn.svm.LinearSVC``
  的空殼子類，因此此處直接用 ``LinearSVC``。
* ``asreview/models/balancers.py`` — ``Balanced`` 產生的是 **sample_weight**
  而非 ``class_weight``：權重字典為 ``{1: 1.0, 0: n_pos / (ratio * n_neg)}``，
  再整體乘上 ``len(y) / sum(weights)`` 正規化。``_balanced_sample_weight``
  逐行對應該公式。

冷啟動策略：標記數不足 ``MIN_LABELS_FOR_AL`` 時不啟用模型，改以既有的
regex ``priorityTier`` 當 prior（即維持原順序），避免用 5 筆標籤訓練出的
噪音去擾動人工篩選次序。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

from ahig.contracts.freeze import content_hash
from ahig.search.screening import TIER_ORDER, normalise_for_matching
from ahig.state import atomic_write_json

# 排序器版本。改動超參數、特徵組合或排序鍵語意時必須升版，
# 這個字串會連同已標記集 hash 一起落盤。
RANKER_VERSION = "b11-al-rank/1.0.0"

# 只有這個 lane 會被重排；其餘 lane 的順序由 screening.py 決定。
TARGET_LANE = "standard-screening"

# 上游 elas_u4 超參數，逐字照抄，不要「順手調一下」。
TFIDF_PARAMS: dict[str, Any] = {
    "ngram_range": (1, 2),
    "sublinear_tf": True,
    "min_df": 1,
    "max_df": 0.95,
}
SVM_PARAMS: dict[str, Any] = {"loss": "squared_hinge", "C": 0.11}
BALANCER_RATIO = 9.8

# 冷啟動門檻（協調者裁定：累積 50–100 筆才啟用，取下界）。
MIN_LABELS_FOR_AL = 50

# screening_decisions 的 decision 值 → 二元標籤。unclear 不是訓練訊號，
# 丟掉而非猜測，否則會把人類的「說不準」硬編成 include 或 exclude。
LABEL_MAP = {"advance": 1, "exclude": 0}


class ActiveLearningError(ValueError):
    """AL 重排的輸入缺漏、漂移或違反 queue 不變量。"""


def _feature_text(entry: dict, abstracts: dict[str, str] | None) -> str:
    """queue entry 只有 title；abstract 需由 candidate pool 補。"""
    parts = [entry.get("title")]
    if abstracts:
        parts.append(abstracts.get(entry["candidateId"]))
    return "\n".join(normalise_for_matching(p) for p in parts if p)


def _balanced_sample_weight(labels: list[int], ratio: float) -> list[float]:
    """對應 ASReview ``Balanced.compute_sample_weight``。"""
    n_pos = sum(1 for y in labels if y == 1)
    n_neg = sum(1 for y in labels if y == 0)
    if n_pos == 0 or n_neg == 0:
        raise ActiveLearningError("balanced 權重需要正負兩類標籤都存在")
    weight_neg = n_pos / (ratio * n_neg)
    raw = [1.0 if y == 1 else weight_neg for y in labels]
    scale = len(labels) / sum(raw)
    return [w * scale for w in raw]


def _decision_labels(reconciliation: dict) -> dict[str, int]:
    """從 screening 對帳結果取出已解決的二元標籤。

    人類路徑（:func:`ahig.search.screening_decisions.reconcile`）產出
    ``resolved``/``decision``；W9 機器路徑
    （:func:`ahig.search.screening_decisions.reconcile_machine`）產出
    ``concordant``/``opinion``——欄位名不同，但兩者都是「兩位審查者已經
    一致同意、不需要再送人審」的已解決標籤，對 AL 冷啟動而言是同一件事。
    兩個鍵都讀（一份文件通常只會有其中一個，但都支援才不用看文件是哪條
    路徑產出的）。
    """
    out: dict[str, int] = {}
    for decision in reconciliation.get("resolved") or []:
        label = LABEL_MAP.get(decision.get("decision"))
        if label is not None:
            out[decision["candidateId"]] = label
    for item in reconciliation.get("concordant") or []:
        label = LABEL_MAP.get(item.get("opinion"))
        if label is not None:
            out[item["candidateId"]] = label
    return out


def score_entries(entries: list[dict], labels: dict[str, int], *,
                  abstracts: dict[str, str] | None = None) -> dict[str, float]:
    """對未標記 entry 產生 AL 分數（decision_function，越大越優先）。

    已標記者不給分——它們已經篩過了，重排它們沒有意義。
    """
    labelled = [(e, labels[e["candidateId"]]) for e in entries
                if e["candidateId"] in labels]
    unlabelled = [e for e in entries if e["candidateId"] not in labels]
    if not labelled or not unlabelled:
        return {}

    y = [label for _, label in labelled]
    weights = _balanced_sample_weight(y, BALANCER_RATIO)
    train_text = [_feature_text(e, abstracts) for e, _ in labelled]
    query_text = [_feature_text(e, abstracts) for e in unlabelled]

    vectoriser = TfidfVectorizer(**TFIDF_PARAMS)
    x_train = vectoriser.fit_transform(train_text)
    x_query = vectoriser.transform(query_text)

    model = LinearSVC(**SVM_PARAMS)
    model.fit(x_train, y, sample_weight=weights)
    scores = model.decision_function(x_query)
    return {e["candidateId"]: float(s) for e, s in zip(unlabelled, scores)}


def rerank(queue: list[dict], labels: dict[str, int], *,
           abstracts: dict[str, str] | None = None) -> dict:
    """在 standard-screening lane 內套用 AL 第三排序鍵。

    回傳 ``{"queue": [...], "provenance": {...}}``。queue 是新的 list，
    entry 物件本身不被修改（AL 分數不寫進 entry，避免污染
    ``screeningQueueHash``）。
    """
    original_ids = [e["candidateId"] for e in queue]
    target = [e for e in queue if e["screeningLane"] == TARGET_LANE]
    labelled_in_lane = sum(1 for e in target if e["candidateId"] in labels)

    enabled = labelled_in_lane >= MIN_LABELS_FOR_AL
    scores: dict[str, float] = {}
    reason = None
    if not enabled:
        reason = (f"cold-start：lane 內已標記 {labelled_in_lane} 筆 "
                  f"< {MIN_LABELS_FOR_AL}，維持 regex tier 順序")
    else:
        try:
            scores = score_entries(target, labels, abstracts=abstracts)
        except (ActiveLearningError, ValueError) as exc:
            # AL 只是排序鍵，壞掉不該拖垮 screening 管線。常見情形：
            # max_df=0.95 在同質語料上把詞彙表剪空，TfidfVectorizer 直接
            # 拋 ValueError。一律退回 regex tier 順序並記錄原因。
            enabled = False
            reason = f"退回 regex tier 順序：{exc}"

    if enabled and scores:
        # 只在 lane 內重排，且 tier 仍是較高優先的鍵——AL 只當第三鍵。
        # 已標記者沒有分數，用 -inf 沉到同 tier 尾端（它們已篩過）。
        order = {cid: i for i, cid in enumerate(original_ids)}
        reordered = sorted(target, key=lambda e: (
            TIER_ORDER[e["priorityTier"]],
            -scores.get(e["candidateId"], float("-inf")),
            order[e["candidateId"]],
        ))
        slots = [i for i, e in enumerate(queue)
                 if e["screeningLane"] == TARGET_LANE]
        new_queue = list(queue)
        for slot, entry in zip(slots, reordered):
            new_queue[slot] = entry
    else:
        new_queue = list(queue)

    _assert_invariants(queue, new_queue)
    return {
        "queue": new_queue,
        "provenance": {
            "rankerVersion": RANKER_VERSION,
            "alEnabled": enabled and bool(scores),
            "disabledReason": reason,
            "targetLane": TARGET_LANE,
            "labelledSetHash": content_hash(
                sorted([cid, int(v)] for cid, v in labels.items())),
            "labelledCount": len(labels),
            "labelledInLaneCount": labelled_in_lane,
            "scoredCount": len(scores),
            "minLabelsForAl": MIN_LABELS_FOR_AL,
            "hyperparameters": {
                "featureExtractor": "tfidf",
                "tfidf": {**TFIDF_PARAMS,
                          "ngram_range": list(TFIDF_PARAMS["ngram_range"])},
                "classifier": "svm/LinearSVC",
                "svm": dict(SVM_PARAMS),
                "balancer": "balanced",
                "balancerRatio": BALANCER_RATIO,
                "querier": "max",
            },
            "sklearnVersion": sklearn.__version__,
            "upstreamSource": (
                "ASReview elas_u4（Apache-2.0）：asreview/models/models.py、"
                "classifiers.py、balancers.py；本模組為等價重寫，未併入依賴"),
        },
    }


def _assert_invariants(before: list[dict], after: list[dict]) -> None:
    """AL 只准換順序。成員、lane、tier、人工篩選旗標一動就炸。"""
    if len(before) != len(after):
        raise ActiveLearningError(
            f"queue 長度改變：{len(before)} → {len(after)}")
    if {e["candidateId"] for e in before} != {e["candidateId"] for e in after}:
        raise ActiveLearningError("queue 成員改變：AL 只能重排，不能增刪候選")
    index = {e["candidateId"]: e for e in before}
    for entry in after:
        old = index[entry["candidateId"]]
        for field in ("screeningLane", "priorityTier", "priorityScore",
                      "requiresHumanScreening", "requiredReviewMode",
                      "autoDecision"):
            if entry.get(field) != old.get(field):
                raise ActiveLearningError(
                    f"{entry['candidateId']} 的 {field} 被改動：AL 不得變更此欄位")
        if entry.get("requiresHumanScreening") is not True:
            raise ActiveLearningError(
                f"{entry['candidateId']} 的 requiresHumanScreening 不是 True")
    # 非目標 lane 的相對順序必須完全不變。
    for lane in {e["screeningLane"] for e in before} - {TARGET_LANE}:
        seq_before = [e["candidateId"] for e in before
                      if e["screeningLane"] == lane]
        seq_after = [e["candidateId"] for e in after
                     if e["screeningLane"] == lane]
        if seq_before != seq_after:
            raise ActiveLearningError(f"非目標 lane {lane} 的順序被改動")
    # 目標 lane 的佔位位置也不能移動（不得跨 lane 插隊）。
    slots_before = [i for i, e in enumerate(before)
                    if e["screeningLane"] == TARGET_LANE]
    slots_after = [i for i, e in enumerate(after)
                   if e["screeningLane"] == TARGET_LANE]
    if slots_before != slots_after:
        raise ActiveLearningError("standard-screening 的佔位位置改變")


def rerank_run_root(run_root: Path, *, dry_run: bool = False) -> dict:
    """讀 screening-queue ＋ 對帳結果，輸出 AL 重排順序與 provenance。

    **不覆寫 queue.json / manifest.json**——``screeningQueueHash`` 是凍結
    契約的一部分，重排結果另存 ``al-rank/``，供人工篩選介面取用。
    """
    run_root = Path(run_root).resolve()
    queue_dir = run_root / "screening-queue"
    queue = json.loads((queue_dir / "queue.json").read_text(encoding="utf-8"))
    manifest = json.loads((queue_dir / "manifest.json").read_text(encoding="utf-8"))

    recon_path = run_root / "screening-decisions" / "reconciliation.json"
    labels: dict[str, int] = {}
    if recon_path.exists():
        labels = _decision_labels(json.loads(
            recon_path.read_text(encoding="utf-8")))

    abstracts = None
    candidates_path = run_root / "candidate-pool" / "candidates.json"
    if candidates_path.exists():
        abstracts = {c["candidateId"]: c.get("abstract") or ""
                     for c in json.loads(
                         candidates_path.read_text(encoding="utf-8"))}

    result = rerank(queue, labels, abstracts=abstracts)
    provenance = dict(result["provenance"])
    provenance["runId"] = manifest.get("runId")
    provenance["screeningQueueHash"] = manifest.get("screeningQueueHash")
    provenance["screeningRuleVersion"] = manifest.get("screeningRuleVersion")
    provenance["rankedOrderHash"] = content_hash(
        [e["candidateId"] for e in result["queue"]])
    if dry_run:
        return provenance

    out = run_root / "al-rank"
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "provenance.json", provenance)
    atomic_write_json(out / "ranked-order.json",
                      [e["candidateId"] for e in result["queue"]])
    return provenance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(rerank_run_root(args.run_root, dry_run=args.dry_run),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
