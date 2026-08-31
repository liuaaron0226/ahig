"""不另外花錢的那條讀論文路線：**論文由已經在跑的那個會話讀。**

擁有者的決定是「不要多花錢」。`read_sections` 那個接縫原本設想的是計量計費的
API 呼叫，而那正是他不要的東西。**但這個房間裡本來就有一個模型在跑**——它看得
到私有根裡的全文，讀一篇不會多產生一筆帳單。

缺的不是模型，是一個**放東西的地方**：讀完的清冊寫成檔案，整批跑的時候從那裡
取。`run_inventory` 的 ``reader`` 本來就是注入的，所以這條路線不必改鏈上任何一段
——驗收、範圍判定、存放處，全部照舊走同一條。

## 為什麼放檔案的地方不能在版控裡

清冊裡有 ``localLabel`` 與 ``sourceLocation``，那些是從論文裡抄出來的字。與全文
本身同一個理由：**不進版控**。故 ``DropReader`` 在建構時就擋掉任何位於 git 工作
樹底下的目錄——擋在寫進去之前，不是寫進去之後才發現。

## 「還沒讀」與「讀壞了」必須分得開

一批跑完只有 12 篇成功，可能是 29 篇還沒讀，也可能是 29 篇讀出來的東西收不下。
兩者要做的事完全不同，而若都記成同一種失敗，看起來會一樣。故本模組把「還沒讀」
獨立成 ``NotDrafted``，並提供 ``status()`` 讓人**在跑之前**就知道還差幾篇。

## 骨架為什麼把內容欄留空

``draft_skeleton`` 只填綁定（讀的是哪一份、對的是哪一份契約），內容欄一律留空。
**一份沒填的骨架必須過不了驗收**——若骨架先替模型填好章節清單，那份完整性聲明
就會變成「由程式碼保證為真」，而它要聲明的正是模型自己掃過什麼。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SHA_PREFIX = "sha256:"


class DropReaderError(Exception):
    """放置目錄本身的問題（位置不對、檔案讀不出來）。"""


class NotDrafted(Exception):
    """這一篇還沒有人讀。**不是讀壞了，是還沒讀。**"""


def _token(digest: str) -> str:
    if not digest or not digest.startswith(SHA_PREFIX):
        raise DropReaderError(f"不是可用的雜湊：{digest!r}")
    return digest.removeprefix(SHA_PREFIX)[:16]


def _inside_git_worktree(path: Path) -> Path | None:
    """回傳含 ``.git`` 的最近祖先；不在版控樹裡則回 ``None``。"""
    resolved = path.expanduser().resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def draft_skeleton(request) -> dict:
    """一份只填好綁定、內容全空的 draft。

    ``inventoryId`` 由綁定推出而不是隨機取——同一份文件對同一份契約重發骨架時
    必須是同一份，否則存放處會看到兩份「內容不同」的清冊而擋下來。
    """
    return {
        "inventoryId": (f"inv:{request.report}:"
                        f"{_token(request.manifestation)}"),
        "report": request.report,
        "manifestation": request.manifestation,
        "scopeContractHash": request.scope_contract_hash,
        "lifecycle": "draft",
        "reportedOutcomes": [],
        "registryComparison": {"status": "pending"},
        "createdBy": {"agentClass": "model"},
        "completenessAttestation": {
            "sectionsScanned": [],
            "supplementaryScanned": False,
            "harmsScan": {"performed": False},
            "attestedBy": {"agentClass": "model"}},
    }


@dataclass
class DropReader:
    """從一個目錄取回讀好的 draft。**本身不讀論文，也不含模型。**

    用法與 API 那條完全一樣：``run_inventory(contract, reader=DropReader(d))``。
    """

    directory: Path

    def __post_init__(self):
        self.directory = Path(self.directory)
        owner = _inside_git_worktree(self.directory)
        if owner is not None:
            raise DropReaderError(
                f"{self.directory} 位於版控樹 {owner} 之下——清冊含論文抄出來的字，"
                "與全文同一個理由不得進版控")

    def path_for(self, candidate_id: str, manifestation: str) -> Path:
        """檔名帶上 manifestation：讀的是哪一份，看檔名就知道。"""
        return self.directory / f"{candidate_id}-{_token(manifestation)}.json"

    def __call__(self, request) -> dict:
        path = self.path_for(request.report, request.manifestation)
        if not path.exists():
            raise NotDrafted(f"{path.name} 不存在——這一篇還沒讀")
        try:
            draft = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DropReaderError(f"{path.name} 讀不出來：{error}") from error

        # 擁有者讀不了英文文獻（ADR-0009），故一份自稱由人讀出來的清冊，
        # 在這個專案裡不可能為真。收下它等於把來源記錯。
        agent_class = (draft.get("createdBy") or {}).get("agentClass")
        if agent_class != "model":
            raise DropReaderError(
                f"{path.name} 的 createdBy.agentClass 為 {agent_class!r}——"
                "本專案唯一的人讀不了英文文獻，該來源記載不可能為真")
        return draft

    def status(self, candidate_ids, manifestations) -> tuple[list, list]:
        """跑之前先看還差幾篇：回傳 ``(已讀, 未讀)``。

        分開列而不是只給兩個數字——**要補的是哪幾篇，才是能拿去做事的東西。**
        """
        drafted, pending = [], []
        for candidate_id, manifestation in zip(candidate_ids, manifestations):
            target = drafted if self.path_for(candidate_id,
                                              manifestation).exists() else pending
            target.append(candidate_id)
        return drafted, pending

    def write_skeleton(self, request) -> Path:
        """把骨架寫進放置目錄，**已存在則不動**。

        不覆寫的理由與存放處同一個：已經填好的東西，不該被一次重發骨架抹掉。
        """
        path = self.path_for(request.report, request.manifestation)
        if path.exists():
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(draft_skeleton(request), ensure_ascii=False, indent=2)
            + "\n", encoding="utf-8")
        return path


__all__ = ["DropReader", "DropReaderError", "NotDrafted", "draft_skeleton"]
