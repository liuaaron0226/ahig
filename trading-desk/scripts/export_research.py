#!/usr/bin/env python3
"""
把工作流研究成果（journal.jsonl）匯出成 markdown 證據庫。

用法：python scripts/export_research.py <journal.jsonl 路徑> <輸出目錄>

每條主張會標註查證狀態：
  ✅ CONFIRMED  — 對抗式查證通過
  ⚠️ CORRECTED — 查證發現錯誤，已附更正
  ❌ REFUTED    — 來源不存在或主張與來源實質不符
  ❓ 未查證      — 查證階段未跑到，**不可當結論使用**
"""
import json
import io
import os
import sys
import collections

BADGE = {"CONFIRMED": "✅", "CORRECTED": "⚠️", "REFUTED": "❌"}


def _norm(s):
    return "".join(ch for ch in (s or "") if ch.isalnum())


def load(path):
    """查證代理回傳的 claim 文字常被改寫或截斷，故用模糊比對而非精確比對。"""
    research, verdict_sets = [], []
    for line in io.open(path, encoding="utf-8"):
        j = json.loads(line)
        if j.get("type") != "result":
            continue
        r = j.get("result") or {}
        if "claims" in r:
            research.append(r)
        elif "results" in r:
            verdict_sets.append(r["results"])

    # 把每組查證結果指派給文字重疊度最高的研究主題
    import difflib
    assigned = {}          # id(topic) -> {claim_index: verdict}
    for vs in verdict_sets:
        vnorm = [_norm(x.get("claim"))[:60] for x in vs]
        best, best_score = None, 0
        for topic in research:
            if id(topic) in assigned:
                continue
            cnorm = [_norm(c.get("claim"))[:60] for c in topic.get("claims") or []]
            score = sum(
                max((difflib.SequenceMatcher(None, v, c).ratio() for c in cnorm),
                    default=0)
                for v in vnorm
            )
            if score > best_score:
                best, best_score = topic, score
        if best is None:
            continue
        cnorm = [_norm(c.get("claim"))[:60] for c in best.get("claims") or []]
        mapping = {}
        for x, v in zip(vs, vnorm):
            ratios = [difflib.SequenceMatcher(None, v, c).ratio() for c in cnorm]
            if ratios:
                i = max(range(len(ratios)), key=lambda k: ratios[k])
                if ratios[i] > 0.55 and i not in mapping:
                    mapping[i] = x
        assigned[id(best)] = mapping
    return research, assigned


def render(topic, assigned):
    lines = [f"## {topic['topic']}", ""]
    claims = topic.get("claims") or []
    mapping = assigned.get(id(topic), {})
    matched = len(mapping)
    if matched == 0:
        lines += [
            "> ❓ **本主題的對抗式查證未完成。**",
            "> 以下主張尚未經獨立查證，**不可當作結論使用**。",
            "> 已查證主題的錯誤率約 39%，故未查證內容的可靠度應假定同等偏低。",
            "",
        ]
    for i, c in enumerate(claims, 1):
        v = mapping.get(i - 1)
        badge = BADGE.get(v.get("verdict"), "❓") if v else "❓"
        conf = c.get("confidence", "?")
        lines.append(f"### {badge} [{i}] {c.get('claim', '')}")
        lines.append("")
        lines.append(f"- **證據等級**：{c.get('evidence_type', '?')} · 研究者信心：{conf}")
        if c.get("key_numbers"):
            lines.append(f"- **關鍵數字**：{c['key_numbers']}")
        if c.get("boundary"):
            lines.append(f"- **適用邊界／何時會害人賠錢**：{c['boundary']}")
        if c.get("citation"):
            lines.append(f"- **來源**：{c['citation']}")
        if v and v.get("verdict") == "CORRECTED" and v.get("corrections"):
            lines.append("")
            lines.append(f"> ⚠️ **查證更正**：{v['corrections']}")
        elif v and v.get("verdict") == "REFUTED":
            lines.append("")
            lines.append(f"> ❌ **查證推翻**：{v.get('corrections', '來源不成立')}")
            lines.append("> **此條不可使用。**")
        lines.append("")
    return "\n".join(lines)


def main():
    journal = sys.argv[1]
    outdir = sys.argv[2]
    research, assigned = load(journal)
    os.makedirs(outdir, exist_ok=True)

    hist_kw = ("台股歷史", "日本", "美國股市", "韓國")
    hist = [r for r in research if any(k in r["topic"] for k in hist_kw)]
    acad = [r for r in research if r not in hist]

    stats = collections.Counter()
    for r in research:
        mapping = assigned.get(id(r), {})
        for i, c in enumerate(r.get("claims") or []):
            v = mapping.get(i)
            stats[v.get("verdict") if v else "未查證"] += 1

    header = f"""> **自動產生** — 來源：workflow `trading-desk-evidence-base`，7 個並行研究代理 + 對抗式查證。
> 重新產生：`python scripts/export_research.py <journal> <outdir>`
>
> **查證統計**：共 {sum(stats.values())} 條主張 —
> ✅ 通過 {stats['CONFIRMED']} · ⚠️ 更正 {stats['CORRECTED']} · ❌ 推翻 {stats['REFUTED']} · ❓ 未查證 {stats['未查證']}
>
> 已查證的 {stats['CONFIRMED']+stats['CORRECTED']+stats['REFUTED']} 條中，
> **{round(100*(stats['CORRECTED']+stats['REFUTED'])/max(1,stats['CONFIRMED']+stats['CORRECTED']+stats['REFUTED']))}% 需要更正或被推翻**。
> 這個比率本身就是最重要的結論：**未經查證的研究產出不可信任。**

---
"""

    with io.open(os.path.join(outdir, "history-casebook.md"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write("# 歷史事件案例庫 — 台 / 日 / 韓 / 美\n\n")
        f.write(header)
        for r in hist:
            f.write(render(r, assigned) + "\n---\n\n")

    with io.open(os.path.join(outdir, "evidence-base-research.md"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write("# 學術依據庫 — 研究代理產出\n\n")
        f.write(header)
        for r in acad:
            f.write(render(r, assigned) + "\n---\n\n")

    print(f"已匯出至 {outdir}")
    print(f"  history-casebook.md        {sum(len(r['claims']) for r in hist)} 條")
    print(f"  evidence-base-research.md  {sum(len(r['claims']) for r in acad)} 條")
    print(f"查證統計: {dict(stats)}")


if __name__ == "__main__":
    main()
