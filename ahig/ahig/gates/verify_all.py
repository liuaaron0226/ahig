#!/usr/bin/env python3
"""`python -m ahig.cli verify --all` 的實作。

單一入口，依序跑完所有閘門並回傳非零退出碼。分十個階段，順序刻意由便宜到昂貴、
由基礎到整合——前面的階段失敗時，後面的失敗多半是衍生的，先修前面的。

  1. 執行環境（UTF-8、私密根目錄邊界）
  2. JSON Schema meta-validation
  3. Registry 驗證與量綱命名空間
  4. SHACL canary（fail-open 偵測）
  5. 交付物驗證（verify.py）
  6. 單元與整合測試
  7. B.11 凍結契約的自我驗證
  8. 端到端貫穿
  9. 分析產物與文件數字對帳
 10. 私密資料外洩掃描

每個階段回報 ok/skip/fail 與一行摘要；細節印在階段內。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Stage:
    def __init__(self, index: int, title: str):
        self.index, self.title = index, title
        self.ok: bool | None = None
        self.detail = ""

    def passed(self, detail: str = "") -> "Stage":
        self.ok, self.detail = True, detail
        return self

    def failed(self, detail: str) -> "Stage":
        self.ok, self.detail = False, detail
        return self


def _run(args: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, *args], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


# ---------------------------------------------------------------------------
# 階段
# ---------------------------------------------------------------------------

def stage_environment(stage: Stage) -> Stage:
    from ahig import bootstrap

    notes = []
    for stream_name in ("stdout", "stderr"):
        encoding = getattr(getattr(sys, stream_name), "encoding", "") or ""
        if "utf-8" not in encoding.lower():
            return stage.failed(f"{stream_name} 編碼為 {encoding!r}，非 UTF-8")
    notes.append("stdio=utf-8")

    # 私密資料命令必須在未設定根目錄時 fail-closed，而不是預設寫到某處。
    saved = os.environ.pop("AHIG_PRIVATE_ROOT", None)
    try:
        bootstrap.private_root()
    except RuntimeError:
        notes.append("private-root fail-closed")
    else:
        return stage.failed("未設定 AHIG_PRIVATE_ROOT 時 private_root() 未拒絕")
    finally:
        if saved is not None:
            os.environ["AHIG_PRIVATE_ROOT"] = saved

    return stage.passed("；".join(notes))


def stage_schemas(stage: Stage) -> Stage:
    from jsonschema import Draft202012Validator

    bad = []
    count = 0
    for path in sorted((ROOT / "schema").glob("*.json")):
        count += 1
        try:
            Draft202012Validator.check_schema(
                json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:                        # noqa: BLE001
            bad.append(f"{path.name}: {str(exc)[:120]}")
    if bad:
        return stage.failed("；".join(bad))
    return stage.passed(f"{count} 份 schema 通過 2020-12 meta-validation")


def stage_registries(stage: Stage) -> Stage:
    from jsonschema import Draft202012Validator

    from ahig.stats import adjudication as adj

    qk_schema = json.loads(
        (ROOT / "schema" / "quantity-kind-registry.schema.json").read_text(
            encoding="utf-8"))
    validator = Draft202012Validator(qk_schema)

    problems, entry_count, files = [], 0, 0
    for path in sorted((ROOT / "registry").glob("quantity-kinds.*.json")):
        files += 1
        for entry in json.loads(path.read_text(encoding="utf-8"))["entries"]:
            entry_count += 1
            errs = sorted(validator.iter_errors(entry), key=lambda e: list(e.path))
            if errs:
                problems.append(f"{entry['quantityKindId']}: {errs[0].message[:100]}")

    try:
        merged = adj._registry()
    except adj.QuantityKindCollision as exc:
        return stage.failed(str(exc))

    if len(merged) != entry_count:
        problems.append(f"合併後 {len(merged)} 項，但檔案共 {entry_count} 項")
    if problems:
        return stage.failed("；".join(problems[:3]))
    return stage.passed(f"{files} 份量綱註冊表、{entry_count} 項，命名空間無碰撞")


def stage_shacl(stage: Stage) -> Stage:
    from ahig.gates import shacl

    summary = shacl.run_all_canaries()
    if not summary["ok"]:
        return stage.failed("；".join(summary["failures"][:3]))
    return stage.passed(
        f"negative {summary['negative']}、positive {summary['positive']}、"
        f"共 {summary['checks']} 次驗證")


def stage_deliverables(stage: Stage) -> Stage:
    proc = _run(["verify.py"])
    match = re.search(r"(\d+)/(\d+) 項驗證通過", proc.stdout)
    if proc.returncode != 0 or not match:
        tail = (proc.stdout or proc.stderr).strip().splitlines()[-3:]
        return stage.failed(" / ".join(tail) or "verify.py 未產生預期輸出")
    passed, total = int(match.group(1)), int(match.group(2))
    if passed != total:
        fails = [ln.strip() for ln in proc.stdout.splitlines() if "FAIL:" in ln]
        return stage.failed(f"{passed}/{total}；{fails[:2]}")
    return stage.passed(f"{passed}/{total} 項交付物驗證通過")


def stage_tests(stage: Stage) -> Stage:
    proc = _run(["tests/run_tests.py"])
    match = re.search(r"(\d+)/(\d+) passed, (\d+) failed", proc.stdout)
    if not match:
        tail = (proc.stdout or proc.stderr).strip().splitlines()[-5:]
        return stage.failed(" / ".join(tail) or "測試執行器未產生預期輸出")
    passed, total, failed = (int(match.group(i)) for i in (1, 2, 3))
    if failed or passed != total:
        names = re.findall(r"^FAIL (\S+)", proc.stdout, re.M)
        return stage.failed(f"{passed}/{total}；失敗 {names[:3]}")
    return stage.passed(f"{passed}/{total} 項測試通過")


def stage_calibration_contract(stage: Stage) -> Stage:
    from ahig.contracts import freeze
    from ahig.scope import matcher as sm

    path = ROOT / "calibration" / "b11-carbohydrate" / "scope-contract.json"
    if not path.exists():
        return stage.failed(f"缺少凍結契約 {path.name}")
    contract = json.loads(path.read_text(encoding="utf-8"))

    if contract.get("status") != "frozen":
        return stage.failed(f"status={contract.get('status')!r}，非 frozen")
    if not freeze.verify_frozen(contract, "scopeContractHash"):
        return stage.failed("雜湊自我驗證失敗——契約可能被手動編輯過")
    problems = freeze.freeze_preflight(contract)
    if problems:
        return stage.failed(f"前置檢查 {len(problems)} 項：{problems[:2]}")
    sm.ScopeMatcher(contract)

    outcomes = contract["inScopeOutcomes"]
    critical = [o for o in outcomes if o["role"] == "critical"]
    if not any("gi-" in o["outcomeId"] for o in critical):
        return stage.failed("GI harms 不是 critical outcome")
    return stage.passed(
        f"B.11 契約已凍結；{len(outcomes)} 個 outcome（{len(critical)} 個 critical）")


def stage_walkthrough(stage: Stage) -> Stage:
    proc = _run(["tests/run_tests.py", "tests/test_end_to_end.py"])
    match = re.search(r"(\d+)/(\d+) passed, (\d+) failed", proc.stdout)
    if not match:
        return stage.failed("端到端測試未產生預期輸出")
    passed, total, failed = (int(match.group(i)) for i in (1, 2, 3))
    if failed:
        return stage.failed(f"{passed}/{total}")
    return stage.passed(f"{passed}/{total} 段貫穿通過")


def stage_analysis_reconciliation(stage: Stage) -> Stage:
    """文件與 JSON 產物宣稱的數字，必須與現場實算一致。"""
    from ahig.gates.quality_gate import clopper_pearson_upper, minimum_sample_size

    problems = []

    # 抽樣框宣稱的可證明上界
    strata_path = ROOT / "calibration" / "b11-carbohydrate" / "strata.json"
    if strata_path.exists():
        strata = json.loads(strata_path.read_text(encoding="utf-8"))
        targets = strata["scopeGoldTargets"]
        n = strata["totalSampleSize"]
        actual = clopper_pearson_upper(0, n, targets["confidence"])
        claimed = targets["provableErrorRateUpperBoundAtZeroErrors"]
        if abs(actual - claimed) >= 5e-5:
            problems.append(f"strata 宣稱上界 {claimed} vs 實算 {actual:.7f}")
        quota_sum = sum(s["quota"] for s in strata["strata"])
        if quota_sum != n:
            problems.append(f"配額合計 {quota_sum} ≠ 宣稱 {n}")
        if targets["sufficientForOnePercentCeiling"] is not False:
            problems.append("n=60 不得宣稱足以支撐 1% 上界")

        # 抽樣框釘住的契約雜湊必須與現行契約一致。契約改版而抽樣框沒跟上時，
        # 兩份檔案各自都合法，只有交叉比對抓得到。
        contract_path = (ROOT / "calibration" / "b11-carbohydrate"
                         / "scope-contract.json")
        if contract_path.exists():
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            if strata.get("scopeContractHash") != contract.get("scopeContractHash"):
                problems.append(
                    "strata 釘住的 scopeContractHash 與現行契約不符——"
                    "契約改版後抽樣框未同步")
    else:
        problems.append("缺少 strata.json")

    # 1% 上界所需樣本數
    required = minimum_sample_size(0.01)
    if required != 299:
        problems.append(f"1% 上界所需 n 實算為 {required}，與文件的 299 不符")

    # 分析產物的語意標籤
    result_path = ROOT / "analysis" / "results" / "adjudication_sensitivity.json"
    if result_path.exists():
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        text = json.dumps(payload, ensure_ascii=False)
        if "required_deterministic_auto_resolution_rate" in text:
            problems.append("分析產物仍使用會被誤讀為品質的舊欄位名")

    if problems:
        return stage.failed("；".join(problems[:3]))
    return stage.passed("抽樣框、樣本數與分析產物的數字與實算一致")


def stage_privacy(stage: Stage) -> Stage:
    """公開專案內不得出現私密健康資料的路徑或內容。

    token 以拼接方式寫出，否則本檔自己會成為第一個命中——那會讓這道掃描
    永遠紅燈，實務上等於被關掉。
    """
    forbidden = ("health" + "/log/", "health" + "/profile.md",
                 "AHIG_PRIVATE_ROOT" + "=")
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".json", ".md", ".ttl"}:
            continue
        if "__pycache__" in path.parts or path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for token in forbidden:
            if token in text:
                hits.append(f"{path.relative_to(ROOT)}: {token}")
    if hits:
        return stage.failed("；".join(hits[:3]))
    return stage.passed("未發現私密資料路徑外洩")


STAGES = [
    ("執行環境", stage_environment),
    ("JSON Schema", stage_schemas),
    ("Registry 與量綱命名空間", stage_registries),
    ("SHACL canary", stage_shacl),
    ("交付物驗證", stage_deliverables),
    ("單元與整合測試", stage_tests),
    ("B.11 凍結契約", stage_calibration_contract),
    ("端到端貫穿", stage_walkthrough),
    ("數字對帳", stage_analysis_reconciliation),
    ("私密資料掃描", stage_privacy),
]


def run() -> int:
    from ahig.bootstrap import configure_stdio

    configure_stdio()
    print("AHIG v2.1 完整驗證")
    print("=" * 72)

    results: list[Stage] = []
    for index, (title, fn) in enumerate(STAGES, start=1):
        stage = Stage(index, title)
        print(f"\n[{index}/{len(STAGES)}] {title} …", flush=True)
        try:
            fn(stage)
        except Exception as exc:                        # noqa: BLE001
            stage.failed(f"{type(exc).__name__}: {str(exc)[:200]}")
        results.append(stage)
        mark = "OK " if stage.ok else "FAIL"
        print(f"  [{mark}] {stage.detail}")

    print("\n" + "=" * 72)
    failed = [s for s in results if not s.ok]
    for stage in failed:
        print(f"  FAIL [{stage.index}] {stage.title} — {stage.detail}")
    print(f"{len(results) - len(failed)}/{len(results)} 個階段通過")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
