"""清冊的存放處：**同一份文件、同一份契約，不要付第二次錢。**

讀一篇論文要花錢，而整批跑很可能會跑不只一次——中途壞掉、加一篇、改一段程式。
若每次重跑都把 41 篇重讀一遍，帳單會隨重跑次數線性成長，而多出來的那些讀取
一個字都不會不一樣。

判斷「這篇已經做過了」用的是清冊自己的兩個綁定欄位：``manifestation``
（被讀的是哪一份 content）與 ``scopeContractHash``（對的是哪一份契約）。兩者
其中一個變了就不算做過——那時候重讀是應該的，因為讀的東西或判準真的變了。

## 為什麼清冊寫進私有根

清冊裡有 ``localLabel``、``sourceLocation``，那些是從論文裡抄出來的字。
與全文本身同一個理由：**不進版控**。

## 覆寫這件事

同一個鍵已經有檔而內容不同時，這裡**丟錯而不是覆寫**。內容不同代表同一份
文件對同一份契約產生了兩份不同的清冊，那是需要有人看一眼的事，不是後寫的
自動贏。
"""

from __future__ import annotations

import json
from pathlib import Path

from ahig.contracts.freeze import file_hash
from ahig.search.fulltext import (_candidate_directory_name, _require_private,
                                  private_root)
from ahig.state import atomic_write_bytes, atomic_write_json

SHA_PREFIX = "sha256:"


class StoreError(Exception):
    """存放處自己的錯誤。"""


def _token(digest: str) -> str:
    if not digest or not digest.startswith(SHA_PREFIX):
        raise StoreError(f"不是可用的雜湊：{digest!r}")
    return digest.removeprefix(SHA_PREFIX)[:16]


def inventory_dir(candidate_id: str) -> Path:
    return (private_root() / "extraction"
            / _candidate_directory_name(candidate_id))


def inventory_path(candidate_id: str, manifestation: str,
                   contract_hash: str) -> Path:
    """檔名即綁定。看檔名就知道它是「哪一份文件、對哪一份契約」的清冊。"""
    return (inventory_dir(candidate_id)
            / f"inventory-{_token(manifestation)}-{_token(contract_hash)}.json")


def _binding_of(scoped: dict) -> tuple[str, str, str]:
    report = scoped.get("report") or ""
    manifestation = scoped.get("manifestation") or ""
    contract_hash = scoped.get("scopeContractHash") or ""
    if not (report and manifestation and contract_hash):
        raise StoreError("清冊缺 report／manifestation／scopeContractHash，"
                         "無從決定它是誰的、讀的是哪一份、對的是哪一份契約")
    return report, manifestation, contract_hash


def save(scoped: dict) -> Path:
    """寫入清冊。已存在而內容不同時丟錯，🚫 不覆寫。"""
    report, manifestation, contract_hash = _binding_of(scoped)
    path = inventory_path(report, manifestation, contract_hash)
    _require_private(path.parent.parent)
    body = (json.dumps(scoped, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() != body:
        raise StoreError(
            f"{path.name} 已存在且內容不同——同一份文件對同一份契約產生了兩份"
            "不同的清冊，需要有人看一眼，不是後寫的自動贏")
    if not path.exists():
        atomic_write_bytes(path, body)
    return path


def load_if_current(candidate_id: str, manifestation: str,
                    contract_hash: str) -> dict | None:
    """有做過就回它，沒有就回 ``None``。

    綁定不符不叫「沒做過」，而是「做過的是別的東西」——兩者在這裡的行為一樣
    （都要重讀），但呼叫端若要分辨，看得出檔名不同。
    """
    path = inventory_path(candidate_id, manifestation, contract_hash)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StoreError(f"{path.name} 讀不出來：{error}") from error


def reference(path: Path) -> dict:
    """指向一份存下的清冊：路徑（相對私有根）＋**檔案位元組**的雜湊。

    ⚠️ 這裡刻意用位元組雜湊而不是正規化雜湊。批次紀錄要能被拿去核對「磁碟上
    那個檔是不是這一份」，而正規化雜湊在重排版之後仍然相同——那是另一個問題的
    答案。取得層的 batch 也是這樣記的（``manifestSha256`` 取自 manifest 的原始
    位元組），此處照它。
    """
    return {"inventoryPath": path.relative_to(private_root()).as_posix(),
            "inventorySha256": file_hash(path.read_bytes())}


def batch_path(batch_id: str) -> Path:
    return private_root() / "extraction" / "batches" / f"{batch_id}.json"


def save_batch(record: dict) -> Path:
    """寫下一次整批跑的紀錄。已存在而內容不同時丟錯，🚫 不覆寫。

    批次 id 由內容雜湊導出，故「同 id 不同內容」代表導出方式壞了，不是撞名。
    """
    batch_id = record.get("batchId") or ""
    if not batch_id:
        raise StoreError("批次紀錄缺 batchId")
    path = batch_path(batch_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    _require_private(path.parent)
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != record:
        raise StoreError(f"{path.name} 已存在且內容不同——批次 id 由內容導出，"
                         "同 id 不同內容代表導出方式壞了")
    if not path.exists():
        atomic_write_json(path, record)
    return path


__all__ = ["StoreError", "batch_path", "inventory_dir", "inventory_path",
           "load_if_current", "reference", "save", "save_batch"]
