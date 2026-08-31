"""萃取工作單：**論文出去、清冊回來**——照 ADR-0009 裁定①既有的那條路。

## 為什麼不是寫一個 API 呼叫

`read_sections` 目前的形狀是 ``(request) -> draft``，那是一次性 API 呼叫的形狀。
**而本專案早就有一條「模型讀東西」的路，且它刻意不是 API：**

- `llm_second_review` 開宗明義：「本模組不呼叫任何 LLM——它管理證據。」
- ADR-0009 裁定①把正式判讀器定為 **session 本身**，並明講
  「**repo 內不放任何 API 呼叫程式或金鑰**」。
- `judgement_worksheet` 就是那條路的兩端：題摘出去、判讀回來。

本模組是萃取的同一對兩端。**它同樣不呼叫任何模型**，只管「給出去的長什麼樣、
收回來的合不合法」。

> ⚠️ 萃取要走哪一條（session 讀，還是 API 讀）是**協調者的決定**，不是這裡定的。
> 這裡做的是把 session 那條接通——它**不需要對外請求、不需要金鑰**，
> 故現在就做得完；而 `run_inventory(reader=…)` 那個注入點對兩條路都成立。

## 分頁為什麼按字元算，不按篇數算

判讀工作單一頁固定 25 筆，因為題摘長度相近。**萃取不是**：實測本語料一篇
最小 13,282、中位 40,222、最大 355,929 字元（`n535`），差 27 倍。
**一頁「5 篇」可能是 6 萬字，也可能是 30 萬字。** 故這裡按字元編頁。

**超出預算的單篇自成一頁，🚫 不切開。** 切不切、怎麼切會改變讀的人看到什麼，
那是契約層的決定（`corpus.py` 已記同一件事）。

## 綁定：清冊要能證明它讀的是哪一份

每一筆都帶 ``manifestation``（sections 檔自記的 ``contentSha256``）。
`reader_from` 據此拒絕**綁到別份文件**的清冊——⚠️ 一份上週寫的清冊，
若文件之後重新解析過，看起來仍然完全正常，🚨 只是它讀的不是現在這一份。
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path

from ahig.bootstrap import private_root
from ahig.state import atomic_write_json

# 一頁的字元預算。n535 實測中位 40,222 字元／篇，故約 3 篇一頁。
# 太大：一輪 session 讀不完，讀到後面已經在壓縮前面。
# 太小：頁數變多，每頁的固定開銷（開檔、回寫、核對）跟著變多。
DEFAULT_PAGE_CHARS = 120_000


class WorksheetError(ValueError):
    """工作單輸入缺漏，或收回來的清冊違反結構規則。"""


def _require_private(path: Path) -> Path:
    """工作單帶著全文，只能待在私有根底下。"""
    root = private_root()
    resolved = Path(path).expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise WorksheetError(f"萃取工作單只能在 AHIG_PRIVATE_ROOT 之下：{root}")
    return resolved


def paginate(sizes: Sequence[int], page_chars: int = DEFAULT_PAGE_CHARS
             ) -> list[int]:
    """依字元預算編頁，回傳每一筆的頁碼（1 起算）。

    順序照給定的順序，🚫 不重排——重排會讓「第 3 頁」在兩次產生之間指向
    不同的東西（判讀工作單記過同一件事）。
    """
    if page_chars <= 0:
        raise WorksheetError("page_chars 必須為正整數")
    pages, page, used = [], 1, 0
    for size in sizes:
        if used and used + size > page_chars:
            page += 1
            used = 0
        pages.append(page)
        used += size
    return pages


def build_worksheet(requests: Sequence, *, source: str,
                    page_chars: int = DEFAULT_PAGE_CHARS) -> dict:
    """把一批 ``DraftRequest`` 展開成分頁工作單。

    ``requests`` 為 ``corpus.reading_request_for`` 的產出——**已經驗過**
    （來源指紋、契約已凍結）。這裡不再驗一次，也不自己去讀私有根：
    驗證屬讀取層，⚠️ 在這裡重做一次會變成兩個地方各有一份規則。
    """
    if not requests:
        raise WorksheetError("沒有要讀的東西——空工作單與「這批沒有論文」分不出來")
    payloads = [r.prompt_payload() for r in requests]
    sizes = [len(json.dumps(p, ensure_ascii=False)) for p in payloads]
    pages = paginate(sizes, page_chars)
    items = []
    for i, (request, payload, size, page) in enumerate(
            zip(requests, payloads, sizes, pages)):
        items.append({
            "seq": i + 1,
            "page": page,
            "report": request.report,
            # 這一份清冊讀的是哪一份文件。收回來時據此比對。
            "manifestation": request.manifestation,
            "scopeContractHash": request.scope_contract_hash,
            "payloadChars": size,
            "sectionCount": len(request.section_titles),
            "payload": payload,
        })
    return {
        "documentType": "extraction-worksheet",
        "adr": "ADR-0009",
        "source": source,
        "itemCount": len(items),
        "pageChars": page_chars,
        "pageCount": pages[-1] if pages else 0,
        "totalChars": sum(sizes),
        "items": items,
        "note": ("按字元編頁而非按篇數：本語料單篇 13k–356k 字元，差 27 倍，"
                 "固定篇數的一頁大小不可預測（n535）。超出預算的單篇自成一頁，"
                 "不切開——切法會改變讀的人看到什麼，那是契約層的決定。"),
    }


def write_worksheet(out_dir: Path, requests: Sequence, *, source: str,
                    page_chars: int = DEFAULT_PAGE_CHARS) -> dict:
    """產生工作單並落盤：索引一份、每頁一份、外加一份空的清冊檔。

    **逐頁一檔**，因為一頁就是一輪要讀的東西；全部塞成一個檔，讀第 3 頁的人
    得先把 1、2 頁一起載進來。判讀工作單塞得下是因為題摘短，⚠️ 這裡不是。
    """
    out_dir = _require_private(Path(out_dir))
    sheet = build_worksheet(requests, source=source, page_chars=page_chars)
    out_dir.mkdir(parents=True, exist_ok=True)

    index = {k: v for k, v in sheet.items() if k != "items"}
    index["items"] = [{k: v for k, v in item.items() if k != "payload"}
                      for item in sheet["items"]]
    atomic_write_json(out_dir / "worksheet.json", index)

    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for page in range(1, sheet["pageCount"] + 1):
        items = [it for it in sheet["items"] if it["page"] == page]
        atomic_write_json(pages_dir / f"page-{page:03d}.json", {
            "documentType": "extraction-worksheet-page",
            "source": source,
            "page": page,
            "pageCount": sheet["pageCount"],
            "itemCount": len(items),
            "chars": sum(it["payloadChars"] for it in items),
            "items": items,
        })

    drafts_path = out_dir / "drafts.json"
    if not drafts_path.exists():
        atomic_write_json(drafts_path, {
            "documentType": "extraction-drafts",
            "adr": "ADR-0009",
            "source": source,
            "readBy": None,
            "entries": [],
        })
    return sheet


def _validate_entry(i: int, item: object, index: dict[str, dict],
                    seen: set[str]) -> dict:
    if not isinstance(item, dict):
        raise WorksheetError(f"清冊[{i}] 必須是物件")
    report = item.get("report")
    if report not in index:
        raise WorksheetError(f"清冊[{i}] 的 report 不在工作單內：{report}")
    if report in seen:
        raise WorksheetError(f"清冊[{i}] 重複 report：{report}")
    seen.add(report)
    expected = index[report]
    for field in ("manifestation", "scopeContractHash"):
        if item.get(field) != expected[field]:
            raise WorksheetError(
                f"清冊[{i}] {report}: {field} 與工作單不符——"
                f"工作單 {expected[field]!r}，清冊 {item.get(field)!r}；"
                "綁錯了的清冊看起來完全正常，只是它讀的不是這一份")
    return item


# 誰讀的，記下來還不夠——**有些記載在這個專案裡不可能為真**。
# 本專案唯一的人讀不了英文文獻（ADR-0009），故 human-self 讀完 41 篇是假的；
# 而 deterministic 更直接：**確定性程式碼讀不出論文報告了什麼**，
# 那正是這個接縫存在的理由。兩者都會讓清冊的來源記載變成錯的，而錯的來源
# 記載看起來和對的一模一樣。
_CANNOT_HAVE_READ = {
    "human-self": "本專案唯一的人讀不了英文文獻（ADR-0009）",
    "deterministic": "確定性程式碼讀不出論文報告了什麼——那正是本接縫存在的理由",
}


def _require_readable_agent(read_by: object) -> None:
    if not (isinstance(read_by, dict) and read_by.get("agentClass")):
        raise WorksheetError(
            "readBy 缺 agentClass——誰讀的沒有記下來，清冊就不可稽核"
            "（ADR-0009 原則 2 對判讀的要求，同樣適用於萃取）")
    why = _CANNOT_HAVE_READ.get(read_by["agentClass"])
    if why:
        raise WorksheetError(
            f"readBy.agentClass 記為 {read_by['agentClass']!r}——{why}；"
            "🚫 來源記載不可能為真的清冊不得收下")


# 正式紀錄那一道。🚫 其他 lane 的東西**永遠不會**進入清冊——
# ⚠️ 第二位讀者是拿來比對的，不是拿來補產量的。
PRIMARY_LANE = "drafts"
_LANE_OK = re.compile(r"^[a-z][a-z0-9-]{0,31}$")


def _lane_dir(out_dir: Path, lane: str) -> Path:
    if not _LANE_OK.match(lane):
        raise WorksheetError(f"lane 名稱不合法：{lane!r}")
    return out_dir / lane


def _page_draft_files(out_dir: Path, lane: str = PRIMARY_LANE) -> list[Path]:
    return sorted(_lane_dir(out_dir, lane).glob("page-*.json"))


def write_page_drafts(out_dir: Path, page: int, entries: Sequence[dict], *,
                      read_by: dict, lane: str = PRIMARY_LANE) -> dict:
    """一頁的清冊寫成**自己的檔**：`drafts/page-NNN.json`。

    ## 🚨 為什麼要有這一支

    `append_drafts` 是「讀 `drafts.json` → 改 → 整份寫回」。⚠️ 一個視窗跑的時候
    沒事；**🚨 兩個視窗同時跑，後寫的那份會把先寫的整個蓋掉，而且不出任何錯**
    ——⚠️ 蓋掉之後的檔案結構完全正常，只是少了一頁。

    擁有者要開多個終端機同時讀，**故並行必須先變成安全的**：
    ✅ 一頁一個檔，兩個視窗寫的是不同檔案，🚫 沒有共用的東西被改。

    **同名而內容不同 → 丟錯，🚫 不覆寫**（與清冊存放處同一條規矩）：
    ⚠️ 那代表同一頁被讀了兩次而結果不同，**🚨 是要有人看一眼的事，
    不是後寫的自動贏。**
    """
    out_dir = _require_private(Path(out_dir))
    sheet = json.loads((out_dir / "worksheet.json").read_text(encoding="utf-8"))
    index = {it["report"]: it for it in sheet["items"]}
    _require_readable_agent(read_by)

    on_page = {it["report"] for it in sheet["items"] if it["page"] == page}
    if not on_page:
        raise WorksheetError(f"工作單沒有第 {page} 頁")
    validated = [_validate_entry(i, item, index, set())
                 for i, item in enumerate(entries)]
    stray = sorted({e["report"] for e in validated} - on_page)
    if stray:
        raise WorksheetError(
            f"這些不在第 {page} 頁上：{stray}——⚠️ 寫進別頁的檔案，"
            "會讓兩個視窗各自登錄同一篇而彼此看不見")

    doc = {"documentType": "extraction-drafts-page", "adr": "ADR-0009",
           "source": sheet["source"], "page": page, "lane": lane,
           "readBy": read_by, "entries": validated}
    path = _lane_dir(out_dir, lane) / f"page-{page:03d}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing == doc:
            return {"page": page, "written": 0, "reason": "與既有內容相同"}
        raise WorksheetError(
            f"第 {page} 頁已有清冊且內容不同：{path.name}——"
            "🚫 不覆寫；同一頁被讀了兩次而結果不同，要有人看一眼")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, doc)
    return {"page": page, "written": len(validated)}


def load_drafts(out_dir: Path, *, require_complete: bool = True) -> dict:
    """讀回清冊檔並檢查結構與綁定。

    ``require_complete``：預設要求工作單每一篇都有清冊——⚠️ 有洞的一批會讓
    下游的分母悄悄變小（判讀工作單記過同一件事）。續讀途中要看進度就傳
    ``False``。

    🚫 這裡不驗清冊的**內容**：那是 `inventory_draft.validate_draft` 的事，
    而它在 `run_inventory` 裡對每一筆都會跑。⚠️ 兩個地方各驗一次，遲早會分岔。

    **中途要跑鏈時，candidate_ids 請傳 ``list(回傳值["drafts"])``。**
    🚨 第 548 輪實測 18 輪的中途：若照樣餵全部 41 篇，收據上會出現 41−N 筆
    `call-reader` 失敗（訊息為「工作單收回來的清冊裡沒有這一篇」）。
    ⚠️ 那是中途的**常態**，🚫 不是壞掉——但收據長得跟真的壞掉一模一樣。
    只餵已讀的那些，18 輪的失敗數全是 0。
    """
    out_dir = _require_private(Path(out_dir))
    sheet = json.loads((out_dir / "worksheet.json").read_text(encoding="utf-8"))
    doc = json.loads((out_dir / "drafts.json").read_text(encoding="utf-8"))
    index = {it["report"]: it for it in sheet["items"]}
    raw = doc.get("entries")
    if not isinstance(raw, list):
        raise WorksheetError("drafts.json 的 entries 必須是陣列")
    seen: set[str] = set()
    entries = [_validate_entry(i, item, index, seen)
               for i, item in enumerate(raw)]
    read_by = doc.get("readBy")
    if entries:
        _require_readable_agent(read_by)

    # 逐頁的清冊檔一併收進來。⚠️ `seen` 是同一個，故同一篇出現在兩處會被擋下
    # ——🚨 兩個視窗都讀了同一頁時，那是唯一看得見它的地方。
    read_by_pages: dict[str, dict] = {}
    for path in _page_draft_files(out_dir):
        page_doc = json.loads(path.read_text(encoding="utf-8"))
        page_entries = page_doc.get("entries")
        if not isinstance(page_entries, list):
            raise WorksheetError(f"{path.name} 的 entries 必須是陣列")
        if page_entries:
            _require_readable_agent(page_doc.get("readBy"))
        read_by_pages[str(page_doc.get("page"))] = page_doc.get("readBy")
        entries += [_validate_entry(f"{path.name}[{i}]", item, index, seen)
                    for i, item in enumerate(page_entries)]

    remaining = sorted(set(index) - seen)
    if require_complete and remaining:
        raise WorksheetError(
            f"工作單還有 {len(remaining)} 篇沒有清冊：{remaining[:3]}")
    return {
        "source": sheet["source"],
        "itemCount": sheet["itemCount"],
        "draftedCount": len(entries),
        "remaining": remaining,
        "readBy": read_by,
        # ⚠️ 18 頁由 18 個視窗讀時，「誰讀的」本來就不只一個——
        # 🚫 硬塞成一個會把其中 17 個記錯。
        "readByPages": read_by_pages,
        "drafts": {entry["report"]: entry for entry in entries},
    }


def append_drafts(out_dir: Path, new_entries: Sequence[dict], *,
                  read_by: dict | None = None) -> dict:
    """把一頁讀好的清冊併回 ``drafts.json``。

    18 頁分 18 輪讀完（第 540 輪實測），**所以併檔會發生很多次**。判讀工作單
    早就有這一支（``append_judgements``），理由一樣：⚠️ 一次一頁，而每次都要能
    接得回去。

    **每次都先把既有的與新來的一起驗過，全部通過才落盤**——
    🚨 半套寫入會讓清冊檔停在 ``load_drafts`` 讀不回來的狀態，
    而那時候前面幾頁讀的東西也一起卡住。
    """
    out_dir = _require_private(Path(out_dir))
    sheet = json.loads((out_dir / "worksheet.json").read_text(encoding="utf-8"))
    doc = json.loads((out_dir / "drafts.json").read_text(encoding="utf-8"))
    index = {it["report"]: it for it in sheet["items"]}
    seen: set[str] = set()
    existing = [_validate_entry(i, item, index, seen)
                for i, item in enumerate(doc.get("entries") or [])]
    added = [_validate_entry(len(existing) + i, item, index, seen)
             for i, item in enumerate(new_entries)]
    if read_by is not None:
        doc["readBy"] = read_by
    _require_readable_agent(doc.get("readBy"))
    doc["entries"] = existing + added
    atomic_write_json(out_dir / "drafts.json", doc)
    return {"added": len(added), "draftedCount": len(doc["entries"]),
            "remaining": sorted(set(index) - seen)}


def page(out_dir: Path, number: int) -> dict:
    """取第 ``number`` 頁。一輪讀一頁，故取頁這件事要有個名字。

    🚫 不回整份工作單：那是逐頁一檔的用意——⚠️ 讀第 3 頁的人不必先把 1、2 頁
    一起載進來。
    """
    out_dir = _require_private(Path(out_dir))
    path = out_dir / "pages" / ("page-%03d.json" % number)
    if not path.exists():
        raise WorksheetError("沒有第 %d 頁：%s" % (number, path.name))
    return json.loads(path.read_text(encoding="utf-8"))


def load_lane(out_dir: Path, lane: str) -> dict:
    """讀回某一道 lane 的清冊。**🚫 不驗完整、🚫 不進正式紀錄。**

    ⚠️ 第二位讀者多半只讀一部分（他讀得動多少算多少），**🚨 故「有洞」是常態**。
    """
    out_dir = _require_private(Path(out_dir))
    sheet = json.loads((out_dir / "worksheet.json").read_text(encoding="utf-8"))
    index = {it["report"]: it for it in sheet["items"]}
    seen: set[str] = set()
    entries: list[dict] = []
    read_by_pages: dict[str, dict] = {}
    for path in _page_draft_files(out_dir, lane):
        doc = json.loads(path.read_text(encoding="utf-8"))
        page_entries = doc.get("entries") or []
        if page_entries:
            _require_readable_agent(doc.get("readBy"))
        read_by_pages[str(doc.get("page"))] = doc.get("readBy")
        entries += [_validate_entry(f"{path.name}[{i}]", item, index, seen)
                    for i, item in enumerate(page_entries)]
    return {"lane": lane, "readByPages": read_by_pages,
            "drafts": {e["report"]: e for e in entries}}


def _labels(draft: dict) -> dict[str, str]:
    """結局標籤 → 正規化鍵。⚠️ 大小寫、前後空白、連續空白不計。"""
    out = {}
    for outcome in draft.get("reportedOutcomes") or []:
        raw = str(outcome.get("localLabel") or "")
        out[re.sub(r"\s+", " ", raw.strip().lower())] = raw
    return out


def agreement(primary: dict, second: dict) -> dict:
    """兩位讀者對**同一批論文**各自登錄了什麼，逐篇比。

    ## 🚨 這個數字量的是什麼，以及**不是**什麼

    ✅ 量的是：兩邊都登錄了、只有一邊登錄了的**標籤**（正規化後逐字比）。

    > **🚫 它不是正確率。** ⚠️ 兩位讀者可能把同一個結局叫成不同名字
    > （「fat-free mass」對「lean body mass」），**那會被算成兩邊各有一個**。
    > **🚨 故「只有一邊有」是一份要人看的清單，不是錯誤數。**

    🚫 亦不比 `sourceLocation`、不比數值——⚠️ 那些要逐欄對，而逐欄對之前
    得先確定兩邊講的是同一個結局，**🚨 那正是這一步還沒做到的事**。
    """
    shared = sorted(set(primary) & set(second))
    rows = []
    both = only_a = only_b = 0
    for report in shared:
        a, b = _labels(primary[report]), _labels(second[report])
        common = sorted(a.keys() & b.keys())
        rows.append({
            "report": report,
            "both": len(common),
            "onlyPrimary": sorted(a[k] for k in a.keys() - b.keys()),
            "onlySecond": sorted(b[k] for k in b.keys() - a.keys()),
        })
        both += len(common)
        only_a += len(a) - len(common)
        only_b += len(b) - len(common)
    return {
        "comparedReports": len(shared),
        "primaryOnlyReports": sorted(set(primary) - set(second)),
        "secondOnlyReports": sorted(set(second) - set(primary)),
        "labelsBoth": both,
        "labelsOnlyPrimary": only_a,
        "labelsOnlySecond": only_b,
        "rows": rows,
        "caveat": ("逐字比標籤。同一個結局被叫成不同名字時會算成兩邊各有一個，"
                   "故「只有一邊有」是待人看的清單，不是錯誤數。"),
    }


def reader_from(drafts: dict[str, dict]):
    """把收回來的清冊包成 `run_inventory` 收得下的 ``reader``。

    找不到就丟——**🚫 不回一份空的**。⚠️ 空清冊分不出「沒讀到」與「論文沒報告」，
    而 `run_inventory` 會把丟出來的那一筆記成 `call-reader` 失敗並列出來。

    綁定再驗一次：`load_drafts` 驗的是「清冊 vs 工作單」，這裡驗的是
    「清冊 vs **這一次真的組出來的請求**」。⚠️ 兩者之間文件可能又被重新解析過。
    """
    def read(request) -> dict:
        draft = drafts.get(request.report)
        if draft is None:
            raise WorksheetError(f"{request.report}：工作單收回來的清冊裡沒有這一篇")
        if draft.get("manifestation") != request.manifestation:
            raise WorksheetError(
                f"{request.report}：清冊綁的是 {draft.get('manifestation')!r}，"
                f"而這一次要讀的是 {request.manifestation!r}——"
                "文件在寫清冊之後又變過")
        return draft

    return read


__all__ = ["DEFAULT_PAGE_CHARS", "WorksheetError", "append_drafts",
           "build_worksheet", "load_drafts", "page", "paginate",
           "reader_from", "write_worksheet"]
