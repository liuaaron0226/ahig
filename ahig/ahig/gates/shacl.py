"""SHACL 閘門 —— 以 pySHACL 真實執行兩個 profile 並跑 canary 語料。

設計立場
========

**Core 是唯一必要的防線，SPARQL 是 pinned audit。**

`shapes/core/ahig-core.shacl.ttl` 是純 SHACL 1.0 Core，任何合格的 SHACL
驗證器都能完整執行；結構阻擋（必填欄位、列舉、基數、條件式必填）全部
落在這裡。`shapes/sparql/ahig-v2.1.shacl.ttl` 只補上 Core 表達不了的
跨節點算術與集合條件。sh:sparql 是 SHACL 的 SPARQL 擴充，各家驗證器支援
程度不一 —— 把零容忍條件單獨押在上面，等於接受「換一個驗證器就全面
fail-open」。因此本模組的 canary 預設同時對兩個 profile 驗證，並額外檢查
「僅用 Core」時結構類 canary 仍被擋下。

canary 語料
===========

`shapes/canaries/negative/` 每個檔案都是一個**必須被擋下**的圖，且在檔頭
以 `# @expect-source-shape:` 宣告預期觸發的形狀。只檢查 `conforms=false`
是不夠的：形狀改壞之後，違規可能改由某個無關的必填欄位順手擋掉，
`conforms=false` 依舊成立，測試卻已失去意義。

`shapes/canaries/positive/` 是**必須通過**的圖。沒有正向 canary 的話，
「把所有東西都擋掉」會是滿分解 —— fail-closed 會退化成不可用。

target coverage preflight
=========================

SHACL 最安靜的失效模式是「沒有任何形狀 target 到這個節點」：驗證器回報
conforms=true，因為它根本沒檢查。`target_coverage_preflight()` 在驗證前
先確認資料圖裡每個 rdf:type 都至少被一個形狀 target 到，把這種情況變成
顯性失敗。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pyshacl
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, SH

ROOT = Path(__file__).resolve().parents[2]
SHAPES_DIR = ROOT / "shapes"
CANARY_DIR = SHAPES_DIR / "canaries"

AHIG = Namespace("https://ahig.local/ns/")
AHIGSH = Namespace("https://ahig.local/shapes/")

CORE_PROFILE = "core"
SPARQL_PROFILE = "sparql"
PROFILES = (CORE_PROFILE, SPARQL_PROFILE)

PROFILE_FILES = {
    CORE_PROFILE: SHAPES_DIR / "core" / "ahig-core.shacl.ttl",
    SPARQL_PROFILE: SHAPES_DIR / "sparql" / "ahig-v2.1.shacl.ttl",
}

# 本閘門的行為對 pySHACL 版本敏感（SPARQL 擴充的求值細節、報告結構）。
# 版本不符時測試會直接失敗，而不是靜默改變阻擋行為。
PINNED_PYSHACL_VERSION = "0.40.1"

_EXPECT_RE = re.compile(r"^#\s*@expect-(core|sparql):\s*(.+)$", re.M)
_PROFILE_RE = re.compile(r"^#\s*@profiles:\s*(.+)$", re.M)
_SELECT_PREFIX_RE = re.compile(r"(?<![\w:<])([A-Za-z][\w.-]*):[A-Za-z_]")

_SPARQL_KEYWORDS = {
    "select", "where", "filter", "optional", "bind", "group", "having",
    "order", "limit", "offset", "union", "not", "exists", "as", "distinct",
    "count", "coalesce", "bound", "in", "true", "false", "values", "minus",
    "str", "lang", "datatype", "isiri", "isliteral", "sum", "min", "max",
    "avg", "sample", "concat", "if", "regex", "a", "prefix", "base",
}


# ===========================================================================
# 形狀載入
# ===========================================================================

def profile_path(profile: str) -> Path:
    try:
        return PROFILE_FILES[profile]
    except KeyError:
        raise ValueError(f"未知的 profile：{profile}") from None


def load_shapes(profile: str) -> Graph:
    return Graph().parse(profile_path(profile), format="turtle")


def load_combined_shapes() -> Graph:
    """兩個 profile 合併 —— 這是生產環境的實際組態。"""
    graph = Graph()
    for profile in PROFILES:
        graph.parse(profile_path(profile), format="turtle")
    return graph


def strip_prefix_bindings(graph: Graph) -> Graph:
    """把圖經 N-Triples 往返並清掉所有前綴綁定。

    用來證明 SPARQL 形狀不是靠 Turtle 的 @prefix 僥倖過關 —— 真實交付
    可能是 N-Triples、JSON-LD 或 SPARQL store 往返，這些都不保留前綴。
    """
    return Graph(bind_namespaces="none").parse(
        data=graph.serialize(format="nt"), format="nt")


# ===========================================================================
# 形狀衛生檢查
# ===========================================================================

def local_name(term: object) -> str:
    text = str(term)
    for sep in ("#", "/"):
        if sep in text:
            text = text.rsplit(sep, 1)[-1]
    return text


def declared_prefixes(graph: Graph) -> set[str]:
    """由 sh:declare 宣告的前綴（不是 Turtle 的 @prefix）。"""
    return {str(p) for decl in graph.objects(None, SH.declare)
            for p in graph.objects(decl, SH.prefix)}


def sparql_prefixes_used(graph: Graph) -> set[str]:
    """所有 sh:select 內實際用到的前綴。"""
    used: set[str] = set()
    for select in graph.objects(None, SH.select):
        for match in _SELECT_PREFIX_RE.finditer(str(select)):
            token = match.group(1)
            if token.lower() not in _SPARQL_KEYWORDS:
                used.add(token)
    return used


_TARGET_PREDICATES = (
    SH.targetClass, SH.targetNode, SH.targetSubjectsOf, SH.targetObjectsOf,
)


def _has_target(graph: Graph, shape: URIRef) -> bool:
    if any((shape, p, None) in graph for p in _TARGET_PREDICATES):
        return True
    # 隱式 target：形狀本身也是一個 rdfs:Class
    if (shape, RDF.type, URIRef("http://www.w3.org/2000/01/rdf-schema#Class")) in graph:
        return True
    # 被別的形狀以 sh:property / 邏輯運算子引用者不需要自己的 target
    for predicate in (SH.property, SH.node, SH["not"], SH.qualifiedValueShape):
        if (None, predicate, shape) in graph:
            return True
    if any(shape == item for item in _list_members(graph)):
        return True
    return False


def _list_members(graph: Graph) -> Iterable[object]:
    """所有出現在 RDF list（sh:or / sh:and / sh:xone）裡的成員。"""
    for obj in graph.objects(None, RDF.first):
        yield obj


def untargeted_node_shapes(graph: Graph) -> list[str]:
    """沒有 target 也沒被引用的 node shape —— 永遠不會執行。"""
    orphans = []
    for shape in graph.subjects(RDF.type, SH.NodeShape):
        if not isinstance(shape, URIRef):
            continue
        if not _has_target(graph, shape):
            orphans.append(str(shape))
    return sorted(orphans)


def targeted_classes(graph: Graph) -> set[URIRef]:
    return {c for c in graph.objects(None, SH.targetClass)
            if isinstance(c, URIRef)}


def target_coverage_preflight(shapes: Graph, data: Graph) -> list[str]:
    """確認資料圖裡每個 rdf:type 都至少被一個形狀 target 到。

    沒有這道檢查的話，「沒有形狀管到這個類別」與「這個節點合法」在
    驗證報告上完全無法區分 —— 兩者都是 conforms=true。
    """
    covered = targeted_classes(shapes)
    problems = []
    for cls in sorted({c for c in data.objects(None, RDF.type)
                       if isinstance(c, URIRef)}, key=str):
        if cls not in covered:
            problems.append(
                f"資料類別 {local_name(cls)} 未被任何形狀 target；"
                f"驗證結果無意義（未檢查 ≠ 合法）")
    return problems


# ===========================================================================
# 驗證
# ===========================================================================

@dataclass(frozen=True)
class Outcome:
    conforms: bool
    source_shapes: frozenset
    text: str

    @property
    def source_shape_names(self) -> set[str]:
        return {local_name(s) for s in self.source_shapes}


def validate_graph(data: Graph, shapes: Graph) -> Outcome:
    conforms, report, text = pyshacl.validate(
        data, shacl_graph=shapes, advanced=True, inplace=False,
        allow_infos=False, allow_warnings=False)
    sources = frozenset(report.objects(None, SH.sourceShape))
    return Outcome(conforms=conforms, source_shapes=sources, text=text)


# ===========================================================================
# canary 語料
# ===========================================================================

@dataclass
class Canary:
    name: str
    polarity: str
    path: Path
    data: Graph
    # 期待的 sourceShape 逐 profile 宣告。兩個 profile 用不同機制實作同一條
    # 規則（Core 用 property shape / sh:or，SPARQL 用 sh:sparql），報告出來的
    # sourceShape 本來就不同 —— 硬要求兩邊一致等於逼一邊說謊。
    expect: dict[str, frozenset] = field(default_factory=dict)
    profiles: tuple[str, ...] = PROFILES

    def expected_for(self, profile: str) -> frozenset:
        return self.expect.get(profile, frozenset())

    @property
    def expect_source_shapes(self) -> frozenset:
        return frozenset().union(*self.expect.values()) if self.expect else frozenset()


def canary_path(polarity: str, name: str) -> Path:
    return CANARY_DIR / polarity / f"{name}.ttl"


def load_canary(path: Path) -> Canary:
    text = path.read_text(encoding="utf-8")

    expect: dict[str, set] = {}
    for profile, names in _EXPECT_RE.findall(text):
        bucket = expect.setdefault(profile, set())
        for token in names.split(","):
            token = token.strip()
            if token:
                bucket.add(AHIGSH[token])

    profile_match = _PROFILE_RE.search(text)
    profiles = (tuple(p.strip() for p in profile_match.group(1).split(","))
                if profile_match else PROFILES)
    for profile in profiles:
        if profile not in PROFILE_FILES:
            raise ValueError(f"{path.name} 宣告了未知 profile：{profile}")

    return Canary(
        name=path.stem,
        polarity=path.parent.name,
        path=path,
        data=Graph().parse(path, format="turtle"),
        expect={k: frozenset(v) for k, v in expect.items()},
        profiles=profiles,
    )


def iter_canaries(polarity: str | None = None) -> list[Canary]:
    polarities = (polarity,) if polarity else ("negative", "positive")
    canaries = []
    for pol in polarities:
        for path in sorted((CANARY_DIR / pol).glob("*.ttl")):
            canaries.append(load_canary(path))
    return canaries


# ===========================================================================
# 閘門進入點
# ===========================================================================

def run_all_canaries() -> dict:
    """跑完整 canary 語料，回傳可直接印出的摘要。"""
    if pyshacl.__version__ != PINNED_PYSHACL_VERSION:
        return {
            "ok": False,
            "negative": 0, "positive": 0, "checks": 0,
            "failures": [f"pySHACL 版本不符：預期 {PINNED_PYSHACL_VERSION}，"
                         f"實際 {pyshacl.__version__}"],
        }

    shapes = {profile: load_shapes(profile) for profile in PROFILES}
    failures: list[str] = []
    checks = 0
    counts = {"negative": 0, "positive": 0}

    for canary in iter_canaries():
        counts[canary.polarity] += 1

        preflight = target_coverage_preflight(load_combined_shapes(), canary.data)
        if preflight:
            failures.append(f"{canary.polarity}/{canary.name}: preflight — "
                            + "；".join(preflight))

        for profile in canary.profiles:
            checks += 1
            outcome = validate_graph(canary.data, shapes[profile])
            if canary.polarity == "negative":
                if outcome.conforms:
                    failures.append(
                        f"negative/{canary.name} [{profile}]: conforms=True（fail-open）")
                    continue
                missing = canary.expected_for(profile) - outcome.source_shapes
                if missing:
                    failures.append(
                        f"negative/{canary.name} [{profile}]: 缺少預期 sourceShape "
                        f"{sorted(local_name(m) for m in missing)}；"
                        f"實際 {sorted(outcome.source_shape_names)}")
            elif not outcome.conforms:
                failures.append(
                    f"positive/{canary.name} [{profile}]: 被誤擋 "
                    f"{sorted(outcome.source_shape_names)}")

    return {
        "ok": not failures,
        "negative": counts["negative"],
        "positive": counts["positive"],
        "checks": checks,
        "failures": failures,
    }


def main() -> int:
    from ahig.bootstrap import configure_stdio
    configure_stdio()

    print("== SHACL 閘門 ==")
    print(f"pySHACL {pyshacl.__version__}（pinned {PINNED_PYSHACL_VERSION}）")
    summary = run_all_canaries()
    print(f"canary：negative {summary['negative']}、positive {summary['positive']}、"
          f"共 {summary['checks']} 次驗證")
    for failure in summary["failures"]:
        print(f"  [FAIL] {failure}")
    print("  [OK ] 全部 canary 行為正確" if summary["ok"] else "  閘門未通過")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
