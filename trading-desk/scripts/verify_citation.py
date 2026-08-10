#!/usr/bin/env python3
"""
引用查證 — 用 Crossref + OpenAlex 確認一篇論文是否真實存在，並取回正確書目。

用法：
  python scripts/verify_citation.py "Returns to Buying Winners and Selling Losers"
  python scripts/verify_citation.py --file citations.txt     # 每行一筆，批次查

為什麼需要這支：
LLM 編造書目（作者對、年份錯；期刊對、卷期錯；甚至整篇不存在）是最危險的失效模式，
因為錯誤的引用看起來和正確的一模一樣。這支腳本讓「查證」變成機械動作而非信任問題。

Crossref 與 OpenAlex 都是免費、免金鑰的書目資料庫，不消耗任何搜尋額度。
實測於 2026-08-10。
"""
import json
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "TradingDeskResearch/1.0 (citation verification)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=25))


def crossref(query, rows=3):
    q = urllib.parse.quote(query)
    url = f"https://api.crossref.org/works?query.bibliographic={q}&rows={rows}"
    out = []
    try:
        for it in _get(url)["message"]["items"]:
            authors = "; ".join(
                f"{a.get('family', '')} {a.get('given', '')}".strip()
                for a in it.get("author", [])
            ) or "—"
            yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            out.append({
                "source": "Crossref",
                "title": (it.get("title") or ["—"])[0],
                "authors": authors,
                "journal": (it.get("container-title") or ["—"])[0],
                "year": yr,
                "volume": it.get("volume", ""),
                "issue": it.get("issue", ""),
                "pages": it.get("page", ""),
                "doi": it.get("DOI", ""),
                "cited_by": it.get("is-referenced-by-count", 0),
            })
    except Exception as e:
        out.append({"source": "Crossref", "error": str(e)[:100]})
    return out


def openalex(query, rows=3):
    q = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={q}&per-page={rows}"
    out = []
    try:
        for w in _get(url).get("results", []):
            authors = "; ".join(
                a["author"]["display_name"] for a in w.get("authorships", [])[:6]
            ) or "—"
            loc = (w.get("primary_location") or {}).get("source") or {}
            out.append({
                "source": "OpenAlex",
                "title": w.get("display_name", "—"),
                "authors": authors,
                "journal": loc.get("display_name", "—"),
                "year": w.get("publication_year"),
                "volume": (w.get("biblio") or {}).get("volume", ""),
                "issue": (w.get("biblio") or {}).get("issue", ""),
                "pages": f"{(w.get('biblio') or {}).get('first_page','')}-"
                         f"{(w.get('biblio') or {}).get('last_page','')}".strip("-"),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "cited_by": w.get("cited_by_count", 0),
            })
    except Exception as e:
        out.append({"source": "OpenAlex", "error": str(e)[:100]})
    return out


def show(query):
    print(f"\n\033[1;36m查詢：{query}\033[0m")
    print("─" * 78)
    hits = crossref(query, 2) + openalex(query, 2)
    found = False
    for h in hits:
        if "error" in h:
            print(f"  [{h['source']}] 查詢失敗：{h['error']}")
            continue
        found = True
        bib = f"{h['year']}"
        if h["volume"]:
            bib += f";{h['volume']}"
            if h["issue"]:
                bib += f"({h['issue']})"
        if h["pages"]:
            bib += f":{h['pages']}"
        print(f"  [{h['source']}] 被引用 {h['cited_by']:,} 次")
        print(f"    標題 {h['title']}")
        print(f"    作者 {h['authors']}")
        print(f"    出處 {h['journal']} {bib}")
        if h["doi"]:
            print(f"    DOI  {h['doi']}")
        print()
    if not found:
        print("  ⚠ 兩個資料庫都查不到 —— 這個引用很可能是編造的，或書目資訊嚴重錯誤。")
    print("  判讀：比對作者姓氏、年份、期刊名是否與原引用一致。")
    print("        被引用次數極低的『經典論文』是危險訊號。")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--file":
        with open(args[1], encoding="utf-8") as f:
            queries = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    else:
        queries = [" ".join(args)]
    for i, q in enumerate(queries):
        show(q)
        if i < len(queries) - 1:
            time.sleep(1)   # 尊重 Crossref 的速率限制


if __name__ == "__main__":
    main()
