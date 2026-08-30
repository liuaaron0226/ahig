"""萃取階段。M1 第四步，也是 P1–P4 共用的最後一塊。

n+181 查明這個套件先前根本不存在：管線搜尋、篩選、抽樣、取全文之後就停了，
而看板寫了八輪的「待萃取期」讀起來像排程，實情是東西沒有被造出來。

第一塊是語料的讀取層（``corpus``）：把已取得的全文讀成可以被萃取的形狀，
並且**在讀之前先驗**。萃取讀到未經驗證的位元組，正是第 496 輪指出的那個缺口
——那時只有寫入路徑在驗，而萃取是純讀取的一端。
"""

from ahig.extraction.corpus import (  # noqa: F401
    AcquiredDocument,
    CorpusError,
    iter_acquired,
    load_document,
    sections_titled,
)
