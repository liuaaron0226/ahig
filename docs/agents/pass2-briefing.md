# Safety Lane 第二遍判讀簡報（無菌室版）

**本檔是你唯一的指示來源。禁止讀 `COORDINATION.md`、禁止 `git log`
翻看板歷史、禁止查閱任何先前判讀結果**——你是雙模型盲判的第二位
審查者，讀到第一位的答案即污染盲性，整遍作廢。心跳與提問一律寫
`docs/agents/pass2-heartbeat.md`（用附加方式 `cat >>`，不要開檔閱讀
舊內容）並隨 commit 推送；協調者會讀你的心跳並把回覆**附加到本檔
末尾的「協調者回覆區」**，你每輪只讀本檔。

## 任務

對 `AHIG_PRIVATE_ROOT` run 之 screening queue 中
`screeningLane == "safety-review"` 的全部 2,316 筆候選做題摘層判讀
（第二遍盲判）。

- 工作單：`python -m ahig.search.judgement_worksheet worksheet <RUN> \
  --out-name safety-full-screen-pass-2 --from-file <lane 清單>`，
  候選順序＝**lane 內 candidateId 字典序**（`sorted(lane_ids)`），
  page_size 25——與既有慣例一致，不需比對任何先前產物。
- 判讀模型＝本 session harness 實際回報的模型；首次 append 帶
  `--model-id <harness 回報值>`。**若回報值是 `claude-sonnet-5`
  立即停手**，在心跳檔回報，不開判。
- 節奏：時間盒——每輪判滿約 12 分鐘再收尾（約 5-6 頁）；每頁 append
  前程式化核對頁面候選數與判讀檔筆數一致（25/25）。
- 收尾：每輪跑 `cd ahig && python tests/run_tests.py`（應全綠；你不
  改程式碼）、附加心跳、commit（訊息帶累計進度數字）、push 到分支
  `claude/safety-pass-2`。

## 判讀規約（全部規則，無案例）

依據＝凍結契約 `calibration/b11-carbohydrate/scope-contract.json`
（自行讀取，PICO 以它為準）。逐軸核對，任一軸明確違反即 exclude，
理由必寫明是哪一軸；資訊不足以判定則 unclear（不硬猜）；符合全部
軸即 advance。補充慣例（協調者已裁定，有拘束力）：

1. **族群排除是絕對軸**：糖尿病（含前期/妊娠）、<18 或 >45 歲、
   臨床疾病族群——介入設計再吻合也不豁免。
2. **時序**：僅「單次運動**中**攝取」在範圍內；運動前負荷、運動後
   回填、兩回合間恢復期攝取、多日/慢性飲食策略（CHO 週期化、
   sleep-low、生酮適應比較等）一律 exclude。**細則**：同一連續運動
   方案的段落之間攝取、段落間歇 ≤30 分鐘且結局量測於同事件後續
   段落者，視為運動中（in-exercise）；間歇 30–60 分鐘灰帶給
   unclear；以小時計或明為恢復期回補者 exclude。
3. **同總劑量、不同醣類組成/型態之對照**（如葡萄糖+果糖 vs 等量
   葡萄糖）：判 advance，理由前綴 `[cho-type-comparison]`。
4. **CHO vs 等熱量非醣營養素**（脂肪/蛋白對照）：不屬第 3 條；
   依契約對照 allowlist 處理（無合格對照臂即 exclude）。
5. **registry-record**（試驗登錄）：有正面出局證據才 exclude，
   資訊不足給 unclear，不硬套 publication 標準。
6. 每筆理由即 rawResponse，必須非空且具體（ADR-0009）；判讀檔
   judgedBy 由 append 自動記錄，不得手填他值。

## 心跳格式（附加到 pass2-heartbeat.md）

`第 N 輪｜累計 X/2316（page a–b）｜本輪 Y 筆｜advance 累計 Z｜
邊界案例：無／<candidateId 前 8 碼＋一句卡點>`

邊界案例只描述卡點與你的暫判，等協調者在本檔回覆區裁定後再定案。

---

## 協調者回覆區（由協調者附加，執行室每輪讀取）

**回覆 R1（對第 1 輪）**：
1. 「設計吻合但糖尿病族群」8 筆——**規約第 1 條維持，排除正確，
   不需回頭重判**。介入再吻合也不豁免族群軸，你的理由寫法（明載
   吻合但不豁免）正是要的格式。
2. `0dcd55b5` 與系統性回顧的處置照准；回顧類請在理由中保留
   「可作原始研究線索」註記即可。
3. 節奏與心跳格式照現行；unclear 0 屬本 lane 特性（臨床族群密集），
   不是異常。繼續。


（目前無回覆）
