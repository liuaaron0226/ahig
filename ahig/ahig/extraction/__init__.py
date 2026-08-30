"""萃取階段。M1 第四步，也是 P1–P4 共用的最後一塊。

n+181 查明這個套件先前根本不存在：管線搜尋、篩選、抽樣、取全文之後就停了，
而看板寫了八輪的「待萃取期」讀起來像排程，實情是東西沒有被造出來。

兩室同時開工而**沒有撞在一起**，因為缺的兩塊各自要的東西不同：

  corpus            讀取層——把已取得的全文讀成可萃取的形狀，**且在讀之前先驗**。
                    這一塊要私有根，只有執行室做得到。
                    （萃取是純讀取的一端，而寫入路徑的驗證管不到它；第 496 輪之缺口。）

  inventory_draft   橋——sections 文件 → draft 清冊 → 既有確定性層 → scoped 清冊。
                    這一塊不需要私有根，故由協調者做。

已存在而本套件直接沿用（不重造）：
  ahig.scope.matcher     ScopeMatcher：確定性範圍判定、backfill 候選
  ahig.scope.inventory   lifecycle、assert_scopable、harms 掃描與註冊比對之稽核
"""

from ahig.extraction.corpus import (  # noqa: F401
    AcquiredDocument,
    CorpusError,
    iter_acquired,
    load_document,
    reading_request_for,
    sections_titled,
)
from ahig.extraction.inventory_draft import (  # noqa: F401
    DraftRequest,
    ReadingSeamNotImplemented,
    build_reading_request,
    validate_draft,
    draft_to_scoped,
)
from ahig.extraction.run import (  # noqa: F401
    InventoryRun,
    RecordOutcome,
    run_inventory,
)
