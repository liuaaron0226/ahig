# 09 b11-calibration-contract

Status: done
Blocked by: 03, 04, 05, 06, 07

## 目標

只凍結 B.11 PICO 與 60 篇分層抽樣框，不取得論文。

## 產出

- `ahig/calibration/b11-carbohydrate/scope-contract.draft.json`（來源）
- `ahig/calibration/b11-carbohydrate/scope-contract.json`（凍結產物，
  hash `sha256:e027825f…`，6 個 outcome、2 個 critical）
- `ahig/calibration/b11-carbohydrate/freeze_contract.py`（凍結腳本）
- `ahig/calibration/b11-carbohydrate/strata.json` ＋ `strata.md`（7 層、合計 60）
- `ahig/registry/quantity-kinds.b11-carbohydrate.json`（9 項量綱）
- `ahig/ahig/contracts/freeze.py` ＋ `tests/test_contract_freeze.py`（23 項）
- `tests/test_b11_calibration.py`（30 項）

## Comments

- 本票揭露一個真實缺陷：裁決層只讀單一 registry 檔，新增的 B.11 量綱看不到
  ——契約寫了 blockingConditions 但完全不生效。改為合併
  `registry/quantity-kinds.*.json` 並在 ID 碰撞時拋 `QuantityKindCollision`。
- 兩個「危險的相等」由量綱設計擋住：肝醣乾重／濕重 UCUM code 相同但相差
  四倍餘；TT 與 TTE 同為秒但構念不同、方向相反。
- 未取得任何文獻。所有 `midRef` 為 `null`。
