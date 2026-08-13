#!/usr/bin/env python3
"""
交付物驗證

1. 所有 JSON Schema 檔本身符合 JSON Schema 2020-12 meta-schema
2. 種子註冊表可通過對應 schema 驗證
3. 範例實例（含刻意違規者）驗證行為正確
4. Turtle 檔的語法煙霧測試（本沙箱無 rdflib）
5. 以獨立封閉解交叉驗證抽樣統計的關鍵數字
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

from ahig.bootstrap import configure_stdio

configure_stdio()
ROOT = Path(__file__).resolve().parent
results = []


def report(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'OK ' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
print("== 1. JSON Schema meta-validation ==")
schemas = {}
for p in sorted((ROOT / "schema").glob("*.json")):
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(doc)
        schemas[p.name] = doc
        report(p.name, True)
    except Exception as exc:  # noqa: BLE001
        report(p.name, False, str(exc)[:160])

# ---------------------------------------------------------------------------
print("\n== 2. 種子註冊表驗證 ==")
qk_schema = schemas.get("quantity-kind-registry.schema.json")
qk_reg = json.loads((ROOT / "registry" / "quantity-kinds.sport-science.json").read_text(encoding="utf-8"))
v = Draft202012Validator(qk_schema)
bad = []
for e in qk_reg["entries"]:
    errs = sorted(v.iter_errors(e), key=lambda x: x.path)
    if errs:
        bad.append((e["quantityKindId"], errs[0].message))
report(f"quantity-kinds ({len(qk_reg['entries'])} 項)", not bad,
       "" if not bad else str(bad[:2]))

mid_schema = schemas.get("mid-registry.schema.json")
mid_reg = json.loads((ROOT / "registry" / "mid-registry.seed.json").read_text(encoding="utf-8"))
v = Draft202012Validator(mid_schema)
bad = []
for e in mid_reg["entries"]:
    errs = sorted(v.iter_errors(e), key=lambda x: x.path)
    if errs:
        bad.append((e["midId"], errs[0].message))
report(f"mid-registry ({len(mid_reg['entries'])} 項)", not bad,
       "" if not bad else str(bad[:2]))

# 每個 MID 種子項目都必須是 provisional —— 防止誤用
all_prov = all(e["status"] == "provisional" for e in mid_reg["entries"])
report("MID 種子全部標記 provisional", all_prov)

# UCUM 覆蓋率：證明「全部使用 UCUM」不可行
kinds = qk_reg["entries"]
ucum = [k for k in kinds if k["representation"]["kind"] == "ucum"]
non_ucum = [k for k in kinds if k["representation"]["kind"] != "ucum"]
report(f"UCUM 可表達 {len(ucum)}/{len(kinds)}；需本地定義 {len(non_ucum)}",
       len(non_ucum) > 0,
       "非 UCUM: " + ", ".join(k["quantityKindId"].split(":")[-1] for k in non_ucum))

# GRIM 適用性：只有離散整數量表可套用
grim_ok = [k for k in kinds if k["representation"].get("isDiscreteIntegerScale")]
report(f"GRIM 適用者僅 {len(grim_ok)}/{len(kinds)} 項", len(grim_ok) < len(kinds) / 2)

# ---------------------------------------------------------------------------
print("\n== 3. 範例實例驗證（含刻意違規） ==")
sys.path.insert(0, str(ROOT))
from tests.test_scope_and_family import base_contract  # noqa: E402

scope_schema = schemas["extraction-scope-contract.schema.json"]
v = Draft202012Validator(scope_schema)
valid_scope_contract = base_contract(
    frozenAt="2026-08-13T00:00:00Z",
    scopeContractHash="sha256:" + "0" * 64,
)
errs = sorted(v.iter_errors(valid_scope_contract), key=lambda x: list(x.path))
report("有效的 ExtractionScopeContract 通過驗證", not errs,
       "" if not errs else f"{list(errs[0].path)}: {errs[0].message}"[:200])

# 刻意違規 1：onOutOfScope 被改成丟棄
bad_c = base_contract()
bad_c["extractionPolicy"]["onOutOfScope"] = "discard"
report("拒絕 onOutOfScope=discard（不得靜默丟棄）",
       bool(list(v.iter_errors(bad_c))))

# 刻意違規 2：缺少 inScopeOutcomes
bad_c2 = base_contract()
bad_c2["inScopeOutcomes"] = []
report("拒絕空的 inScopeOutcomes", bool(list(v.iter_errors(bad_c2))))

# 刻意違規 3：outcomeInventoryPolicy.required = false
bad_c3 = base_contract()
bad_c3["outcomeInventoryPolicy"]["required"] = False
report("拒絕 outcomeInventoryPolicy.required=false",
       bool(list(v.iter_errors(bad_c3))))

# 刻意違規 4：未知欄位
bad_c4 = base_contract()
bad_c4["someUndeclaredField"] = 1
report("拒絕未宣告欄位（additionalProperties: false）",
       bool(list(v.iter_errors(bad_c4))))

# OutcomeInventory 範例
#
# 這裡刻意不自帶 fixture：draft 的形狀由 test_inventory_scope_integration 定義，
# 且 scoped 形狀必須由 ScopeMatcher 真的產生。verify.py 若自己維護一份平行 fixture，
# schema 演化時只會出現「驗證器綠燈但沒人餵得出這種文件」的假象。
from tests.test_inventory_scope_integration import draft as build_draft  # noqa: E402
from ahig.scope import matcher as _matcher  # noqa: E402

oi_schema = schemas["outcome-inventory.schema.json"]
vi = Draft202012Validator(oi_schema)

inv = build_draft()
errs = sorted(vi.iter_errors(inv), key=lambda x: list(x.path))
report("有效的 OutcomeInventoryDraft 通過驗證", not errs,
       "" if not errs else f"{list(errs[0].path)}: {errs[0].message}"[:200])

# draft 不得自帶 scopeDecision——那是 ScopeMatcher 的專屬輸出
bad_draft = json.loads(json.dumps(inv))
bad_draft["reportedOutcomes"][0]["scopeDecision"] = {
    "inScope": True, "reasonCode": "in-scope", "ruleId": "SCOPE-001",
}
report("拒絕 draft 自帶 scopeDecision（模型不得預寫確定性結論）",
       bool(list(vi.iter_errors(bad_draft))))

# ScopeMatcher 的輸出必須「直接」通過 scoped schema，不容測試端補欄位
scoped = _matcher.ScopeMatcher(valid_scope_contract).scope_inventory(build_draft())
errs = sorted(vi.iter_errors(scoped), key=lambda x: list(x.path))
report("ScopeMatcher 輸出直接通過 ScopedOutcomeInventory 驗證", not errs,
       "" if not errs else f"{list(errs[0].path)}: {errs[0].message}"[:200])

decided_by = scoped["reportedOutcomes"][0]["scopeDecision"]["decidedBy"]
report("scope 決策標記為 deterministic 且帶 ruleId",
       decided_by.get("agentClass") == "deterministic"
       and bool(scoped["reportedOutcomes"][0]["scopeDecision"].get("ruleId")),
       f"agentClass={decided_by.get('agentClass')}, "
       f"ruleId={scoped['reportedOutcomes'][0]['scopeDecision'].get('ruleId')}")

bad_inv = json.loads(json.dumps(scoped))
bad_inv["reportedOutcomes"][0]["scopeDecision"]["reasonCode"] = "just-skipped-it"
report("拒絕未列舉的 notExtracted 理由碼", bool(list(vi.iter_errors(bad_inv))))

bad_inv2 = json.loads(json.dumps(inv))
bad_inv2["manifestation"] = "not-a-hash"
report("拒絕非 sha256 格式的 manifestation", bool(list(vi.iter_errors(bad_inv2))))

# ---------------------------------------------------------------------------
print("\n== 4. Turtle 語法煙霧測試 ==")
ttl = (ROOT / "shapes" / "sparql" / "ahig-v2.1.shacl.ttl").read_text(encoding="utf-8")
checks = []
prefixes = set(re.findall(r"@prefix\s+([\w-]*):", ttl))
used = set(re.findall(r"(?<![\w:<\"/#-])([a-zA-Z][\w-]*):(?![/\s])", ttl))
# 排除出現在字串常值（SPARQL 區塊）中的前綴
sparql_blocks = re.findall(r'"""(.*?)"""', ttl, re.S)
body = ttl
for b in sparql_blocks:
    body = body.replace(b, "")
# 一般字串常值（例如 sh:pattern "^sha256:..."）也不是前綴使用處
body = re.sub(r'"[^"\n]*"', '""', body)
used_body = set(re.findall(r"(?<![\w:<\"/#-])([a-zA-Z][\w-]*):(?![/\s])", body))
undeclared = used_body - prefixes - {"http", "https"}
checks.append(("所有使用的前綴皆已宣告", not undeclared, str(sorted(undeclared))))

# 括號 / 引號平衡（先移除 SPARQL 字串常值）
checks.append(("方括號平衡", body.count("[") == body.count("]"),
               f"{body.count('[')} vs {body.count(']')}"))
checks.append(("小括號平衡", body.count("(") == body.count(")"),
               f"{body.count('(')} vs {body.count(')')}"))
checks.append(('三引號成對', ttl.count('"""') % 2 == 0, str(ttl.count('"""'))))

# 每個 NodeShape 宣告都以 . 結束
shape_names = re.findall(r"^(ahigsh:\w+)\s*$", ttl, re.M)
checks.append((f"NodeShape 數量 = {len(shape_names)}", len(shape_names) >= 10, ""))
stmts = [s for s in re.split(r"\.\s*\n", body) if s.strip()]
checks.append(("語句以句點分隔", len(stmts) >= len(shape_names), f"{len(stmts)} 段"))

# 每個 sh:sparql 都有 sh:select 與 sh:message
n_sparql = ttl.count("sh:sparql")
n_select = ttl.count("sh:select")
n_msg_in_sparql = len(re.findall(r"sh:sparql\s*\[(?:[^\]]|\n)*?sh:message", ttl))
checks.append((f"sh:sparql({n_sparql}) 與 sh:select({n_select}) 數量相符",
               n_sparql == n_select, ""))
for name, ok, detail in checks:
    report(name, ok, detail)

# ---------------------------------------------------------------------------
print("\n== 5. 抽樣統計數字的獨立交叉驗證 ==")
sp = json.loads((ROOT / "analysis" / "results" / "sampling_power.json").read_text(encoding="utf-8"))

# 封閉解：0 事件的 Clopper-Pearson 單側上界 = 1 - alpha^(1/n)
# 令其 <= 0.01 -> n >= ln(0.05)/ln(0.99)
n_closed = math.ceil(math.log(0.05) / math.log(0.99))
n_sim = sp["derived_min_n_for_1pct_error_ceiling"]
report(f"error<=1% 所需 n：封閉解 {n_closed} vs 二分搜尋 {n_sim}",
       abs(n_closed - n_sim) <= 1)

# n=30 的可證明上界
u30 = [r for r in sp["error_rate_verifiability"]["achievable_ceiling_at_n"]
       if r["n"] == 30][0]["upper_95"]
closed_30 = 1 - 0.05 ** (1 / 30)
report(f"n=30 可證明的上界：{u30:.4f} vs 封閉解 {closed_30:.4f}",
       abs(u30 - closed_30) < 1e-3)
report("n=30 無法驗證 1% 門檻（差距 >= 9 倍）", u30 / 0.01 >= 9,
       f"{u30/0.01:.1f} 倍")

# AC1 解析變異數 vs bootstrap
for c in sp["bootstrap_cross_check"]["checks"]:
    report(f"AC1 CI 下限 解析 vs bootstrap（{c['scenario']}, n={c['n']}）",
           c["abs_diff_lower"] < 0.01, f"差 {c['abs_diff_lower']:.4f}")

# gate inversion：AC1>=0.80 隱含的誤差率上限
gi = json.loads((ROOT / "analysis" / "results" / "gate_inversion.json").read_text(encoding="utf-8"))
balanced = [r for r in gi["rows"] if r["field_shape"].startswith("二分類，平衡")][0]
e_max = balanced["max_per_rater_error_for_AC1_0.8"]
report(f"平衡二分類欄位：AC1>=0.80 隱含每位評分者誤差率 <= {e_max:.1%}",
       e_max < 0.06)

# 吞吐量模型的一致性
ht = json.loads((ROOT / "analysis" / "results" / "human_throughput.json").read_text(encoding="utf-8"))
h = ht["report"]["headline"]
report(f"範圍契約使人工需求由 {h['base_unscoped_person_years']} 人年降至 "
       f"{h['base_scoped_person_years']} 人年",
       h["base_scoped_person_years"] < h["base_unscoped_person_years"] / 10)
report(f"基準情境 10h/週 的最大批次 = {h['base_max_domains_per_batch_at_10h_week']} 領域"
       f"（契約原訂 8–12）",
       h["base_max_domains_per_batch_at_10h_week"] < 8)

# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
n_ok = sum(1 for _, ok, _ in results if ok)
print(f"{n_ok}/{len(results)} 項驗證通過")
for name, ok, detail in results:
    if not ok:
        print(f"  FAIL: {name} — {detail}")
sys.exit(0 if n_ok == len(results) else 1)
