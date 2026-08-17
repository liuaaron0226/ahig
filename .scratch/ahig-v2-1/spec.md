# AHIG v2.1 契約核心

Status: ready-for-agent

## 要解決的問題

AHIG v2 的 SHACL、OutcomeInventory、裁決、GRADE 與品質閘門存在已實測的 fail-open、介面漂移與數字宣稱不一致。v2.1 必須先讓公開契約可在 Windows 本機被完整驗證，之後才允許啟動第一個文獻校準集。

## 範圍

- 建立 repo 根目錄 `ahig/` 公開專案，與 `health/` 私密紀錄分離。
- 修復 UTF-8、原子狀態、SHACL canary、schema 條件、Inventory/Scope、裁決、GRADE 與品質閘門。
- 建立 B.11 碳水化合物策略與肝醣管理的凍結校準契約與 60 篇分層抽樣框。

## 明確不做

- 不搜尋、下載或上傳校準論文。
- 不建立 NotebookLM notebook。
- 不遷移個人健康資料。
- 不啟動 Jena、Fuseki、Qdrant、Tantivy。
- 不執行 F 槽備份、修復、格式化或加密。

## 成功條件

`python -m ahig.cli verify --all` 在原生 Windows 環境完成 schema、registry、SHACL canary、單元／整合測試、分析對帳與 B.11 虛構端到端流程；任何 fail-open canary 都必須被阻擋。
