# Scripts Directory

This directory contains tools for managing and validating the Railway News Monitor system.

---

## 📁 Directory Structure

```
scripts/
├── production/      # Production-ready tools (use these)
│   ├── reparse_all_times.py
│   ├── evaluate_full_dataset.py
│   └── validate_service_types.py
└── archive/         # Historical scripts (reference only)
    ├── testing/     # Testing scripts from optimization rounds
    ├── analysis/    # Analysis tools
    └── migrations/  # Data migration scripts
```

---

## 🚀 Production Tools

### `production/reparse_all_times.py`

**用途**: 使用最新提取邏輯重新解析所有公告的時間數據

**使用場景**:
- 更新 `date_utils.py` 或 `content_parser.py` 後
- 需要應用新的時間提取規則到歷史數據
- 修復 bug 後重新生成完整數據集

**執行**:
```bash
python3 scripts/production/reparse_all_times.py
```

**輸出**:
- 更新 `data/master.json`
- 顯示變更統計（有多少公告的時間數據被更新）
- 記錄錯誤數量

**範例輸出**:
```
總公告數: 123
已更新: 123
有變更: 10
錯誤數: 0
```

---

### `production/evaluate_full_dataset.py`

**用途**: 生成完整數據集的性能評估報告

**使用場景**:
- 驗證時間提取的準確性
- 生成學術研究所需的性能指標
- 修復後確認系統性能

**執行**:
```bash
python3 scripts/production/evaluate_full_dataset.py
```

**輸出文件**:
- `data/evaluation_report.json` - 機器可讀的評估結果
- `data/PERFORMANCE_REPORT.md` - 人類可讀的詳細報告

**指標包含**:
- Predicted Resumption Time: Precision, Recall, F1 Score
- Actual Resumption Time: Precision, Recall, Time Accuracy
- 數據集分布統計
- 修復前後對比

---

### `production/validate_service_types.py`

**用途**: 驗證服務類型分類的準確性

**使用場景**:
- 驗證 `service_type` 和 `service_details` 欄位
- 檢查服務類型分布是否合理
- 確認接駁服務、部分營運、正常列車的分類正確

**執行**:
```bash
python3 scripts/production/validate_service_types.py
```

**輸出**:
- 服務類型統計（shuttle_service, partial_operation, normal_train）
- 服務詳情分布
- 詳細列表（每個類型的公告標題）

**範例輸出**:
```
服務類型分布:
  normal_train: 5
  partial_operation: 4
  shuttle_service: 2
```

---

## 📦 Archive (歷史腳本)

### `archive/testing/` - 測試腳本

這些腳本用於時間提取優化過程中的測試驗證（2025-10-21 至 2025-10-24）。

#### `test_fixed_samples.py`
- **測試輪次**: Round 5
- **案例數**: 10 個
- **目的**: 驗證初步修復（事件時間、接駁時間、停駛時間等）
- **狀態**: ✅ 所有案例已修復

#### `test_round2_samples.py`
- **測試輪次**: Round 2 (後期)
- **案例數**: 5 個隨機抽樣
- **目的**: False Positive 批量修復驗證
- **狀態**: ✅ 所有案例已修復

#### `validate_sample.py`
- **用途**: 隨機抽樣工具
- **功能**: 從數據集中隨機抽取 N 個案例供人工驗證
- **使用**: 手動驗證時間提取質量

---

### `archive/analysis/` - 分析工具

#### `analyze_changes.py`
- **用途**: 分析修復前後的數據變更
- **使用時機**: Round 2 修復後
- **輸出**: 變更案例詳細列表

---

### `archive/migrations/` - 資料遷移

這些腳本用於歷史數據遷移，已完成任務。

#### `migrate_add_content_text.py`
- **用途**: 為舊數據添加 `content_text` 欄位
- **狀態**: ✅ 已完成

#### `reclassify_data.py`
- **用途**: 使用新分類規則重新分類公告
- **狀態**: ✅ 已完成

#### `recover_time_data.py`
- **用途**: 恢復時間數據（從備份或重新提取）
- **狀態**: ✅ 已完成

#### `reparse_data.py` ⚠️ DEPRECATED
- **狀態**: 已被 `production/reparse_all_times.py` 取代
- **保留原因**: 歷史參考

---

## 📊 測試歷程

完整的測試記錄請參考專案根目錄的 **`TESTING_HISTORY.md`**

**測試摘要**:
- 總測試輪次: 7+ 輪
- 測試時間: 2025-10-21 至 2025-10-24
- 最終性能: 100% Precision & Recall
- 數據規模: 123 條公告

---

## 🔧 使用建議

### 日常使用
推薦使用 `production/` 下的工具。

### 參考歷史
`archive/` 下的腳本供參考，不建議修改或執行（除非你知道自己在做什麼）。

### 新增工具
如果要新增腳本：
- 生產工具 → 放在 `production/`
- 一次性測試 → 放在 `archive/testing/`
- 分析工具 → 放在 `archive/analysis/`

---

## 📝 相關文檔

- **`TESTING_HISTORY.md`** - 完整測試歷程記錄
- **`PROJECT_CLEANUP_REPORT.md`** - 專案結構收斂報告
- **`data/PERFORMANCE_REPORT.md`** - 性能評估詳細報告
- **`README.md`** - 專案主文檔

---

**最後更新**: 2025-10-24
**維護者**: Railway News Monitor Team
