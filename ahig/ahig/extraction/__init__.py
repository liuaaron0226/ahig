"""萃取階段：把一份全文變成可稽核的結局清冊與結果。

M1 第四步。此前管線能搜尋、篩選、抽樣、取全文——然後就停了；
本套件補上「讀全文」與後續之間的那一段。

已存在而本套件直接沿用（不重造）：
  ahig.scope.matcher     ScopeMatcher：確定性範圍判定、backfill 候選
  ahig.scope.inventory   lifecycle、assert_scopable、harms 掃描與註冊比對之稽核

本套件補的是**橋**：sections 文件 → draft 清冊 → （既有確定性層）→ scoped 清冊。
"""

from .inventory_draft import (                      # noqa: F401
    DraftRequest,
    ReadingSeamNotImplemented,
    build_reading_request,
    validate_draft,
    draft_to_scoped,
)
