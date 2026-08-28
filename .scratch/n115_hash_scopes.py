"""Determine, by measurement, what each frozen artefact's hash actually covers.

丙節骨架第四節要求「每步附其產物與雜湊，並註明**該雜湊涵蓋什麼範圍**」。
本 run 已知至少三種涵蓋範圍並存，只寫欄位名而不寫範圍，稽核者會驗不過。

作法：對每個 `*Hash` 欄位，逐一試算候選範圍，報實際相符者。
🚨 不相符時輸出「未知」，不臆測——猜範圍正是 n+100 的錯誤形狀。

Run:  python3 .scratch/n115_hash_scopes.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "ahig")
from ahig.contracts.freeze import content_hash  # noqa: E402

TARGETS = [
    ".scratch/n68_termination_evidence.json",
    ".scratch/n68_tail_sample.json",
    ".scratch/n68_tail_information.json",
    ".scratch/n68_tail_result.json",
    ".scratch/n68_preconditions.json",
    ".scratch/n78_termination_evidence.json",
    ".scratch/n78_tail_sample.json",
    ".scratch/n78_tail_information.json",
    ".scratch/n78_tail_result.json",
    ".scratch/n85_tail_population.json",
]

# ADR-0008 之證據雜湊原像（`statistical_termination.py` 現行版本，12 欄）。
PREIMAGE_12 = ["alpha", "pScore", "relevantFound", "screenedCount", "poolSize",
               "targetRecall", "windowSize", "notScreenedCount",
               "mandatoryLanesFullyScreened", "pScoreExcludedCount",
               "outOfSequenceCount", "allowedToStop"]
# 預設值：兩個區塊各自缺存 alpha／targetRecall 或 outOfSequenceCount，
# 補入後才可能重算。🚨 補的是版控內之預設值，不是猜的。
DEFAULTS = {"alpha": 0.05, "targetRecall": 0.95}


def candidates(doc, hashfield, container):
    """Every scope worth trying, named in the terms a report would use."""
    yield "整份文件（扣除該雜湊欄）", {k: v for k, v in doc.items() if k != hashfield}
    for key, val in doc.items():
        if isinstance(val, dict):
            yield f"子物件 `{key}`（原樣）", val
            yield (f"子物件 `{key}`（扣除 *Hash 欄）",
                   {a: b for a, b in val.items() if not a.endswith("Hash")})
        elif isinstance(val, list):
            yield f"清單 `{key}`", val
    if container is not doc:
        yield "所在子物件（扣除該雜湊欄）", {
            k: v for k, v in container.items() if k != hashfield}
    # 第四步之資訊條件雜湊：原像是「本檔 rows ＋ 上游 sampleHash」。
    # 🚨 這一種混合了本檔內容與外來值，猜不到——是讀 `.scratch/n78_step4_information.py`
    # 第 96–97 行得知的（n+100 之規則：先讀產生腳本，再寫驗證器）。
    if hashfield == "informationConditionHash" and "rows" in doc:
        up = doc.get("readsStep3", {}).get("sampleHash")
        if up:
            yield ("**本檔 `rows` ＋ 上游 `sampleHash`**（讀產生腳本得知）",
                   {"rows": doc["rows"], "sampleHash": up})
    # ADR-0008 之證據雜湊：原像是固定欄位清單，不是整個區塊。
    # ⚠️ 兩次觸發之原像欄位數不同，故兩種都要試。
    if hashfield == "terminationEvidenceHash":
        filled = {**DEFAULTS, **container}
        for label, keys in (
                ("ADR-0008 十二欄原像（現行）", PREIMAGE_12),
                ("ADR-0008 **十一欄**原像（無 `outOfSequenceCount`）",
                 [k for k in PREIMAGE_12 if k != "outOfSequenceCount"])):
            if all(k in filled for k in keys):
                yield label, {k: filled[k] for k in keys}


def walk(doc, node, prefix=""):
    for key, val in list(node.items()):
        path = f"{prefix}.{key}" if prefix else key
        if key.endswith("Hash") and isinstance(val, str):
            yield path, key, val, node
        elif isinstance(val, dict):
            yield from walk(doc, val, path)


docs = {}
for rel in TARGETS:
    p = Path(rel)
    if p.exists():
        docs[rel] = json.loads(p.read_text(encoding="utf-8"))

# 每個雜湊值出現在哪些 (檔, 路徑) —— 用來把「未知」與「引用自上游」分開。
where = {}
for rel, doc in docs.items():
    for path, _key, stored, _c in walk(doc, doc):
        where.setdefault(stored, []).append((rel, path))

rows = []
for rel in TARGETS:
    if rel not in docs:
        rows.append((rel, "—", "❌ 檔案不存在", ""))
        continue
    doc = docs[rel]
    found = list(walk(doc, doc))
    if not found:
        rows.append((rel, "—", "（無 *Hash 欄）", ""))
        continue
    for path, key, stored, container in found:
        scope = None
        for name, obj in candidates(doc, key, container):
            try:
                if content_hash(obj) == stored:
                    scope = name
                    break
            except (TypeError, ValueError):
                continue
        if scope:
            rows.append((rel, path, f"**自證**：{scope}", ""))
            continue
        # 非自證：是不是上游步驟算出、抄進來做鏈結的？
        others = [f"`{Path(r).name}` → `{q}`"
                  for r, q in where[stored] if (r, q) != (rel, path)]
        if others:
            rows.append((rel, path, "**引用**（非本檔算出）",
                         "實測與 " + "、".join(others) + " 相同 ✅"))
        else:
            rows.append((rel, path, "🚨 **未定位**",
                         "本組檔案內無同值者；其來源在版控外（如 worksheet 檔）"))

print("| 產物 | 雜湊欄 | 種類與涵蓋範圍 | 鏈結實測 |")
print("|---|---|---|---|")
for rel, path, scope, link in rows:
    print(f"| `{Path(rel).name}` | `{path}` | {scope} | {link} |")

print()
self_n = sum(1 for r in rows if r[2].startswith("**自證**"))
ref_n = sum(1 for r in rows if r[2].startswith("**引用**"))
unk_n = sum(1 for r in rows if "未定位" in r[2])
print(f"（依欄位計）自證 {self_n}｜引用且已比對相符 {ref_n}｜未定位 {unk_n}")

# ⚠️ 依欄位計會蓋掉一件事：某個雜湊「值」可能在所有檔案裡都只是被抄來抄去，
# 沒有任何一檔算得出它。那種值鏈結得起來，但原像仍未定位。
print()
print("=== 依雜湊值計：有沒有任何一檔算得出它？ ===")
selfproved = {stored for rel, path, scope, _ in rows if scope.startswith("**自證**")
              for stored in [next(v for p, k, v, c in walk(docs[rel], docs[rel])
                                  if p == path)]}
allvals = set(where)
orphan = sorted(allvals - selfproved)
print(f"相異雜湊值 {len(allvals)}｜其中至少一檔可自證 {len(allvals) - len(orphan)}"
      f"｜**無一檔可自證 {len(orphan)}**")
for v in orphan:
    names = sorted({q.split(".")[-1] for _r, q in where[v]})
    files = sorted({Path(r).name for r, _q in where[v]})
    print(f"  🚨 {'／'.join(names)}：出現於 {len(where[v])} 處"
          f"（{'、'.join(files)}），皆相同 ✅，但原像不在本組檔案內")

print()
print("=== 證據雜湊之原像：兩次觸發不同 ===")
for rel, block in [(".scratch/n68_termination_evidence.json", "terminationResult"),
                   (".scratch/n78_termination_evidence.json",
                    "evaluateTerminationStandardBasis")]:
    doc = docs.get(rel)
    if doc is None:
        continue
    blk = doc
    for k in block.split("."):
        blk = blk[k]
    stored = blk["terminationEvidenceHash"]
    filled = {**DEFAULTS, **blk}
    ver = blk.get("schemaVersion", "（未存）")
    for label, keys in [("12 欄（現行）", PREIMAGE_12),
                        ("11 欄（無 outOfSequenceCount）",
                         [k for k in PREIMAGE_12 if k != "outOfSequenceCount"])]:
        if any(k not in filled for k in keys):
            continue
        if content_hash({k: filled[k] for k in keys}) == stored:
            print(f"  {Path(rel).name} → `{block}`"
                  f"（schemaVersion {ver}）：**{label} 重現 ✅**")
            break
    else:
        print(f"  {Path(rel).name} → `{block}`：🚨 兩種原像皆不重現")
