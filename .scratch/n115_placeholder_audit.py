"""Cross-check every {{placeholder}} in the four M1 skeletons against its
appendix source table.

Purpose: build the 己類 delivery checklist from the files themselves rather
than by retyping (n+44: load the original, never retype).

Reports three things:
  UNSOURCED  - used in the body, absent from that file's appendix table
  UNUSED     - listed in the appendix table, never used in the body
  CLASS      - the 凍結/漂移 class each table assigns

Appendix rows may name several placeholders in one cell, either separated by
'／' or written as a `PREFIX_*` wildcard; both forms are expanded here.
"""

import re
from pathlib import Path

FILES = {
    "甲": "docs/m1-a-search-coverage-skeleton.md",
    "乙": "docs/m1-b-screening-limits-skeleton.md",
    "丙": "docs/m1-c-termination-skeleton.md",
    "丁": "docs/m1-d-audit-debt-skeleton.md",
}

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
# an appendix row: | `NAME`／`NAME2` | class | source |
ROW = re.compile(r"^\|\s*(`[^|]+`)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$")
CODE = re.compile(r"`([A-Z0-9_*]+)`")


def split_appendix(text):
    """Return (body, appendix) split at the source-table heading."""
    marker = "## 附：佔位符來源表"
    i = text.find(marker)
    if i < 0:
        return text, ""
    return text[:i], text[i:]


def expand(name, used):
    """Expand a `PREFIX_*` wildcard against the placeholders actually used."""
    if not name.endswith("*"):
        return [name]
    prefix = name[:-1]
    return sorted(u for u in used if u.startswith(prefix))


rows = []
problems = []

for sec, rel in FILES.items():
    text = Path(rel).read_text(encoding="utf-8")
    body, appendix = split_appendix(text)
    used = sorted(set(PLACEHOLDER.findall(body)))

    listed = {}
    for line in appendix.split("\n"):
        m = ROW.match(line)
        if not m:
            continue
        names_cell, klass, source = m.groups()
        if "佔位符" in names_cell or set(names_cell.strip()) <= set("`-| "):
            continue
        for raw in CODE.findall(names_cell):
            for name in expand(raw, used):
                listed[name] = (klass.strip(), source.strip())

    for name in used:
        if name in listed:
            klass, source = listed[name]
        else:
            klass, source = "❓未列", "❓ 該檔附表未列來源"
            problems.append(("UNSOURCED", sec, name))
        rows.append((sec, name, klass, source))

    for name in sorted(listed):
        if name not in used:
            problems.append(("UNUSED", sec, name))

print(f"placeholders used across four skeletons: {len(rows)}")
frozen = sum(1 for r in rows if "凍結" in r[2])
drift = sum(1 for r in rows if "漂移" in r[2])
print(f"  凍結 {frozen} / 漂移 {drift} / 未列 {len(rows) - frozen - drift}")
print()
for kind, sec, name in problems:
    print(f"{kind:10s} {sec}  {name}")
if not problems:
    print("no unsourced or unused placeholders")
print()
for sec, name, klass, source in rows:
    tag = "凍結" if "凍結" in klass else ("漂移" if "漂移" in klass else "❓")
    print(f"| {sec} | `{name}` | {tag} | {source} |")
