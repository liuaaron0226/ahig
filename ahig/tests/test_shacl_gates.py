"""Task #10 —— SHACL 閘門的真實執行測試。

本檔不做語法煙霧測試（那是 verify.py 第 4 節的事），而是用 pySHACL 真實
執行兩個 profile，並要求：

1. Core profile 是純 SHACL 1.0 Core，獨力完成結構阻擋。
2. SPARQL profile 是 pinned audit，其前綴自足（不依賴 Turtle 綁定）。
3. 每個 property shape 都是具名 IRI 且帶自身 severity —— 否則違規報告
   的 sourceShape 會是 blank node，稽核時無法定位是哪一條規則。
4. target coverage preflight 會擋下「資料類別根本沒被任何形狀 target」
   的情況 —— 否則負向 canary 會因為沒人管而假性通過。
5. 每個負向 canary 真的 conforms=false，且期待的 sourceShape 出現在報告裡。
"""
from __future__ import annotations

from pathlib import Path

import pyshacl
from rdflib import BNode, Graph, URIRef

from ahig.gates import shacl as G

ROOT = Path(__file__).resolve().parents[1]


# ===========================================================================
# 0. 執行環境：必須是真的 pySHACL
# ===========================================================================

def test_pyshacl_version_is_pinned():
    assert pyshacl.__version__ == G.PINNED_PYSHACL_VERSION, (
        f"本閘門的行為對 pySHACL 版本敏感；預期 {G.PINNED_PYSHACL_VERSION}，"
        f"實際 {pyshacl.__version__}")


def test_both_profiles_exist_and_parse():
    for profile in (G.CORE_PROFILE, G.SPARQL_PROFILE):
        path = G.profile_path(profile)
        assert path.exists(), f"缺少 profile 檔案：{path}"
        graph = G.load_shapes(profile)
        assert len(graph) > 0


# ===========================================================================
# 1. Core profile 的形狀衛生
# ===========================================================================

def test_core_profile_contains_no_sparql_constraints():
    """Core 必須能在只支援 SHACL 1.0 Core 的驗證器上完整執行。

    若結構阻擋依賴 sh:sparql，換一個不支援 SPARQL 擴充的驗證器就會全面
    fail-open。"""
    core = G.load_shapes(G.CORE_PROFILE)
    sparql_triples = list(core.triples((None, G.SH.sparql, None)))
    assert sparql_triples == [], (
        f"Core profile 含 {len(sparql_triples)} 個 sh:sparql；Core 必須是純 Core。")
    assert list(core.triples((None, G.SH.select, None))) == []


def test_core_property_shapes_are_named_iris():
    """property shape 是 blank node 時，違規報告的 sourceShape 也是 blank
    node，稽核者無法回推是哪一條規則。"""
    core = G.load_shapes(G.CORE_PROFILE)
    anonymous = [s for s in core.subjects(G.SH.path, None) if isinstance(s, BNode)]
    assert anonymous == [], f"Core 有 {len(anonymous)} 個匿名 property shape"


def test_core_property_shapes_carry_own_severity():
    """severity 繼承自 node shape 時，無法逐條調整，也無法在報告裡分辨
    哪一條是 Violation、哪一條只是 Warning。"""
    core = G.load_shapes(G.CORE_PROFILE)
    missing = [
        str(s) for s in set(core.subjects(G.SH.path, None))
        if (s, G.SH.severity, None) not in core
    ]
    assert missing == [], f"以下 property shape 未自帶 sh:severity：{sorted(missing)}"


def test_core_node_shapes_all_have_targets():
    """沒有 target 的形狀永遠不會執行 —— 是最安靜的 fail-open。"""
    core = G.load_shapes(G.CORE_PROFILE)
    untargeted = G.untargeted_node_shapes(core)
    assert untargeted == [], f"以下 Core node shape 沒有任何 target：{untargeted}"


# ===========================================================================
# 2. SPARQL profile 的前綴自足性
# ===========================================================================

def test_sparql_profile_declares_every_prefix_it_uses():
    """sh:select 內用到的前綴必須由 sh:declare 宣告。

    pySHACL 在 sh:declare 缺漏時會回退到「shapes graph 的 Turtle 前綴綁定」，
    所以用 .ttl 讀進來時看起來正常；一旦 shapes 以 N-Triples／JSON-LD 或
    經過 SPARQL store 往返（都不保留前綴綁定）交付，同一份形狀就會直接
    拋錯或靜默失效。"""
    graph = G.load_shapes(G.SPARQL_PROFILE)
    used = G.sparql_prefixes_used(graph)
    declared = set(G.declared_prefixes(graph))
    assert used, "SPARQL profile 竟然沒有任何 sh:select"
    assert used <= declared, (
        f"sh:select 用到但未 sh:declare 的前綴：{sorted(used - declared)}")


def test_sparql_profile_survives_prefix_binding_loss():
    """把 shapes 與 data 都剝掉 Turtle 前綴綁定後仍須正常執行。

    這是上一個測試的行為版：直接證明形狀不是靠 Turtle 綁定僥倖過關。"""
    shapes = G.strip_prefix_bindings(G.load_shapes(G.SPARQL_PROFILE))
    canary = G.load_canary(G.canary_path("negative", "grade-model-override-approved"))
    data = G.strip_prefix_bindings(canary.data)
    outcome = G.validate_graph(data, shapes)
    assert not outcome.conforms, "剝掉前綴綁定後 SPARQL 形狀失效（fail-open）"


def test_sparql_profile_still_targets_every_class_core_targets():
    """兩個 profile 的守備範圍必須一致；SPARQL 是稽核，不是縮編。"""
    core = G.targeted_classes(G.load_shapes(G.CORE_PROFILE))
    sparql = G.targeted_classes(G.load_shapes(G.SPARQL_PROFILE))
    assert core, "Core 沒有 target 任何類別"
    assert sparql, "SPARQL 沒有 target 任何類別"


# ===========================================================================
# 3. target coverage preflight
# ===========================================================================

def test_preflight_flags_untargeted_class():
    """preflight 本身必須被證明有效，否則它只是一個永遠回傳空清單的裝飾品。"""
    shapes = G.load_shapes(G.CORE_PROFILE)
    orphan = Graph().parse(
        data='@prefix ahig: <https://ahig.local/ns/> .\n'
             '<urn:x> a ahig:TotallyUnknownClass .',
        format="turtle")
    problems = G.target_coverage_preflight(shapes, orphan)
    assert problems, "preflight 未偵測到沒有任何形狀 target 的類別"
    assert any("TotallyUnknownClass" in p for p in problems)


def test_preflight_passes_for_every_canary():
    """每個 canary 的資料類別都必須真的被守備 —— 否則 conforms=false
    可能來自別的形狀，而 conforms=true 可能只是沒人管。"""
    combined = G.load_combined_shapes()
    failures = []
    for canary in G.iter_canaries():
        problems = G.target_coverage_preflight(combined, canary.data)
        if problems:
            failures.append((canary.name, problems))
    assert failures == [], f"canary 的 target coverage preflight 失敗：{failures}"


# ===========================================================================
# 4. canary：正向必過、負向必擋
# ===========================================================================

def test_canary_corpus_is_non_trivial():
    negative = G.iter_canaries("negative")
    positive = G.iter_canaries("positive")
    assert len(negative) >= 10, f"負向 canary 只有 {len(negative)} 個"
    assert len(positive) >= 4, f"正向 canary 只有 {len(positive)} 個"


def test_every_positive_canary_conforms():
    failures = []
    for canary in G.iter_canaries("positive"):
        for profile in canary.profiles:
            outcome = G.validate_graph(canary.data, G.load_shapes(profile))
            if not outcome.conforms:
                failures.append(
                    (canary.name, profile, sorted(outcome.source_shape_names)))
    assert failures == [], f"正向 canary 被誤擋：{failures}"


def test_every_negative_canary_is_blocked():
    failures = []
    for canary in G.iter_canaries("negative"):
        for profile in canary.profiles:
            outcome = G.validate_graph(canary.data, G.load_shapes(profile))
            if outcome.conforms:
                failures.append((canary.name, profile, "conforms=True（fail-open）"))
    assert failures == [], f"負向 canary 未被阻擋：{failures}"


def test_every_negative_canary_names_its_source_shape():
    """光是 conforms=false 不夠 —— 必須是「預期的那條規則」擋下來的，
    否則形狀改壞了也測不出來（例如被某個無關的必填欄位順手擋掉）。

    期待值逐 profile 宣告：兩個 profile 用不同機制實作同一條規則
    （Core 用 property shape 與 sh:or，SPARQL 用 sh:sparql），報告出來的
    sourceShape 本來就不同。"""
    failures = []
    for canary in G.iter_canaries("negative"):
        for profile in canary.profiles:
            expected = canary.expected_for(profile)
            assert expected, (
                f"{canary.name} 未宣告 profile {profile} 期待的 sourceShape")
            outcome = G.validate_graph(canary.data, G.load_shapes(profile))
            missing = expected - outcome.source_shapes
            if missing:
                failures.append((
                    canary.name, profile,
                    "缺少：" + ", ".join(sorted(G.local_name(m) for m in missing)),
                    "實際：" + ", ".join(sorted(outcome.source_shape_names))))
    assert failures == [], f"負向 canary 的 sourceShape 不符：{failures}"


def test_all_violation_source_shapes_are_identifiable():
    """報告裡不得出現 blank node 的 sourceShape。"""
    offenders = []
    for canary in G.iter_canaries("negative"):
        for profile in canary.profiles:
            outcome = G.validate_graph(canary.data, G.load_shapes(profile))
            anon = [s for s in outcome.source_shapes if isinstance(s, BNode)]
            if anon:
                offenders.append((canary.name, profile, len(anon)))
    assert offenders == [], f"sourceShape 是 blank node，無法定位規則：{offenders}"


# ===========================================================================
# 5. 四個已知 fail-open —— 逐一定點回歸
# ===========================================================================

def _blocked_by_both(canary_name: str) -> dict[str, bool]:
    canary = G.load_canary(G.canary_path("negative", canary_name))
    return {
        profile: not G.validate_graph(canary.data, G.load_shapes(profile)).conforms
        for profile in (G.CORE_PROFILE, G.SPARQL_PROFILE)
    }


def test_failopen_outcome_switching_uses_real_relation_direction():
    """原形狀走 `OutcomeInventory ahig:supports ?sr`，但契約與 schema 裡的
    正式關係是 `StudyResult ahig:derivedFromOutcomeInventory OutcomeInventory`。
    方向寫反 = 真實資料永遠不匹配 = 靜默 fail-open。"""
    assert _blocked_by_both("outcome-switching-real-relation")[G.SPARQL_PROFILE]


def test_failopen_outcome_switching_missing_decider_is_fail_closed():
    """原形狀要求 `?agent ahig:agentClass "model"` 才觸發；
    完全沒記錄裁決者時反而通過。缺欄位必須 fail-closed。"""
    assert _blocked_by_both("outcome-switching-missing-decider")[G.SPARQL_PROFILE]


def test_failopen_safety_critical_approved_without_expert():
    """原形狀只擋顯式的 self-adjudicated；`adjudicationLevel` 整個缺漏時
    高風險主張可以直接晉升 Approved。"""
    for name in ("safety-critical-approved-missing-adjudication",
                 "safety-critical-approved-self-adjudicated"):
        blocked = _blocked_by_both(name)
        assert blocked[G.CORE_PROFILE], f"{name} 未被 Core 結構阻擋"


def test_failopen_grade_requires_five_distinct_domains():
    """原形狀是 `sh:minCount 5`；五筆全是 imprecision 也通過。"""
    for name in ("grade-domains-not-distinct", "grade-domains-missing-one"):
        blocked = _blocked_by_both(name)
        assert blocked[G.CORE_PROFILE], f"{name} 未被 Core 結構阻擋"


def test_failopen_monitor_sla_honours_grace_and_missing_fields():
    """原形狀 (a) 忽略 graceHours，(b) 缺 sourceCheckAgeHours 或 maxAgeHours
    時不匹配即通過，(c) safety-critical 只擋顯式 false、不擋缺漏。"""
    assert _blocked_by_both("monitor-sla-grace-exceeded")[G.SPARQL_PROFILE]
    assert _blocked_by_both("monitor-missing-age")[G.CORE_PROFILE]
    assert _blocked_by_both("monitor-missing-maxage")[G.CORE_PROFILE]
    assert _blocked_by_both(
        "monitor-safety-critical-missing-blocks")[G.CORE_PROFILE]


def test_monitor_within_grace_window_still_conforms():
    """fail-closed 不可以退化成「全部都擋」—— grace 內的必須放行。"""
    canary = G.load_canary(G.canary_path("positive", "monitor-within-grace"))
    for profile in (G.CORE_PROFILE, G.SPARQL_PROFILE):
        outcome = G.validate_graph(canary.data, G.load_shapes(profile))
        assert outcome.conforms, (
            f"grace window 內的 ClaimVersion 被 {profile} 誤擋："
            f"{sorted(outcome.source_shape_names)}")


# ===========================================================================
# 6. Core 獨力阻擋（SPARQL 不是唯一防線）
# ===========================================================================

def test_core_alone_blocks_every_structural_canary():
    """把 SPARQL profile 整個拿掉之後，結構類 canary 仍須被擋下。"""
    core = G.load_shapes(G.CORE_PROFILE)
    failures = []
    for canary in G.iter_canaries("negative"):
        if G.CORE_PROFILE not in canary.profiles:
            continue
        if G.validate_graph(canary.data, core).conforms:
            failures.append(canary.name)
    assert failures == [], f"僅用 Core 時未被阻擋：{failures}"


def test_combined_profiles_block_every_negative_canary():
    combined = G.load_combined_shapes()
    failures = [c.name for c in G.iter_canaries("negative")
                if G.validate_graph(c.data, combined).conforms]
    assert failures == [], f"合併 profile 後仍未被阻擋：{failures}"


def test_combined_profiles_pass_every_positive_canary():
    combined = G.load_combined_shapes()
    failures = []
    for canary in G.iter_canaries("positive"):
        outcome = G.validate_graph(canary.data, combined)
        if not outcome.conforms:
            failures.append((canary.name, sorted(outcome.source_shape_names)))
    assert failures == [], f"合併 profile 後正向 canary 被誤擋：{failures}"


# ===========================================================================
# 7. 閘門進入點
# ===========================================================================

def test_run_all_canaries_reports_每個_canary():
    summary = G.run_all_canaries()
    assert summary["ok"], summary["failures"]
    assert summary["negative"] == len(G.iter_canaries("negative"))
    assert summary["positive"] == len(G.iter_canaries("positive"))
    assert summary["checks"] >= summary["negative"] + summary["positive"]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run_tests import main
    raise SystemExit(main([__file__]))
