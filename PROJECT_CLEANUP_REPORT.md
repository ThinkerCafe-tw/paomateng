# 🧹 專案結構收斂報告

**日期**: 2025-10-24
**目的**: 整理散落文件、統一命名規則、優化專案結構

---

## 📊 現況分析

### 1. 散落的備份文件（Redundant Backups）

**data/ 目錄下的手動備份**（應移除）：
```
❌ data/master.json.backup                           (624 KB) - 無時間戳
❌ data/master.json.backup_before_actual_fix        (630 KB) - 舊版修復前備份
❌ data/master.json.backup_before_round6            (624 KB) - Round 6 前備份
❌ data/master.json.emergency_backup_20251022_155128 (641 KB) - 緊急備份
❌ data/master_old_20251021_170207.json             (621 KB) - 舊版本
```

**問題**：
- 系統已有自動備份機制 (`data/backups/`)，16MB 的自動備份
- 手動備份缺乏一致性命名規則
- 佔用約 2.9 MB 空間（加上 backups/ 共 19 MB）

**建議**：
- ✅ 保留最新的 `master.json.emergency_backup_20251022_155128` 作為最終人工備份
- ❌ 移除其他所有手動備份
- 📝 依賴自動備份系統（已在 .gitignore 中排除）

---

### 2. 散落的測試腳本（Test Scripts）

**scripts/ 目錄分析**（14 個文件，1307 行代碼）：

#### 一次性測試腳本（應歸檔）：
```
🔴 test_fixed_samples.py       (5043 行) - Round 1 修復測試
🔴 test_round2_samples.py      (4181 行) - Round 2 修復測試
🔴 validate_sample.py          (2592 行) - 隨機抽樣驗證
🔴 analyze_changes.py          (8160 行) - 變更分析
```
**總計**: ~20KB，一次性使用，已完成階段性任務

#### 遷移/恢復腳本（應歸檔）：
```
🔴 migrate_add_content_text.py (3218 行) - 內容文字遷移（已完成）
🔴 reclassify_data.py          (1649 行) - 重新分類（已完成）
🔴 recover_time_data.py        (5450 行) - 時間數據恢復（已完成）
🔴 reparse_data.py             (2641 行) - 舊版重新解析（已被 reparse_all_times.py 取代）
```
**總計**: ~13KB，歷史遷移用途

#### 保留腳本（Production）：
```
✅ reparse_all_times.py        (4117 行) - **主要工具**: 重新解析所有時間數據
✅ evaluate_full_dataset.py    (6174 行) - **評估工具**: 完整數據集評估
✅ validate_service_types.py   (3325 行) - **驗證工具**: 服務類型驗證
```
**總計**: ~14KB，生產環境工具

**建議目錄結構**：
```
scripts/
├── production/              # 生產環境工具
│   ├── reparse_all_times.py
│   ├── evaluate_full_dataset.py
│   └── validate_service_types.py
└── archive/                 # 歷史腳本歸檔
    ├── round1/
    │   ├── test_fixed_samples.py
    │   └── validate_sample.py
    ├── round2/
    │   ├── test_round2_samples.py
    │   └── analyze_changes.py
    └── migrations/
        ├── migrate_add_content_text.py
        ├── reclassify_data.py
        ├── recover_time_data.py
        └── reparse_data.py (deprecated)
```

---

### 3. macOS Icon 檔案（Metadata Pollution）

**發現**: 20+ 個 `Icon\r` 檔案散布在所有目錄

```
./Icon
./config/Icon
./.spec-workflow/Icon
./.spec-workflow/specs/Icon
./.spec-workflow/specs/railway-news-monitor/Icon
./.spec-workflow/templates/Icon
./.spec-workflow/steering/Icon
./.spec-workflow/approvals/Icon
./tests/Icon
./docs/Icon
./logs/Icon
./scripts/Icon
./.github/Icon
... (共 20+ 個)
```

**問題**: macOS 自定義圖標元數據，不應納入版本控制

**建議**:
- 全部刪除
- 更新 `.gitignore` 加入 `Icon\r` 和 `Icon?`

---

### 4. 根目錄散落文件

```
❌ check_data.py - 應移至 scripts/archive/ 或 scripts/production/
```

---

### 5. 空目錄結構

**spec-workflow 相關**：
```
.spec-workflow/archive/    - 空目錄（只有 Icon 檔案）
.spec-workflow/steering/   - 空目錄（只有 Icon 檔案）
```

**問題**:
- `archive/` 未被使用，建議移除或加入 .gitignore
- `steering/` 根據 spec workflow 規範是可選的，未使用可保留為空

---

### 6. .gitignore 分析

**現有規則**：
- ✅ 正確排除 Python cache、虛擬環境
- ✅ 正確排除 logs/*.log
- ✅ 正確排除 data/backups/*.json
- ✅ 正確排除 *.lock 檔案

**缺少規則**：
```
# macOS 檔案
Icon\r
Icon?
.DS_Store  # 已有，但未涵蓋 Icon

# 臨時備份（手動）
data/*.backup
data/*.backup_*
data/*_old_*.json

# 測試報告
data/evaluation_report.json  # 應考慮是否納入版本控制

# 腳本歸檔
scripts/archive/
```

---

## 🎯 建議行動清單

### Phase 1: 清理（立即執行）

1. **移除 Icon 檔案**
```bash
find . -name "Icon\r" -delete
find . -name "Icon?" -delete
```

2. **清理手動備份**（保留一個最新緊急備份）
```bash
cd data/
mkdir -p backups/manual/
mv master.json.emergency_backup_20251022_155128 backups/manual/
rm -f master.json.backup*
rm -f master_old_*.json
```

3. **更新 .gitignore**
```gitignore
# macOS 檔案
Icon\r
Icon?

# 手動備份
data/*.backup
data/*.backup_*
data/*_old_*.json

# 腳本歸檔
scripts/archive/
```

### Phase 2: 重組（結構優化）

4. **整理 scripts/ 目錄**
```bash
cd scripts/
mkdir -p production archive/round1 archive/round2 archive/migrations

# 保留生產工具
mv reparse_all_times.py production/
mv evaluate_full_dataset.py production/
mv validate_service_types.py production/

# 歸檔測試腳本
mv test_fixed_samples.py archive/round1/
mv validate_sample.py archive/round1/
mv test_round2_samples.py archive/round2/
mv analyze_changes.py archive/round2/

# 歸檔遷移腳本
mv migrate_add_content_text.py archive/migrations/
mv reclassify_data.py archive/migrations/
mv recover_time_data.py archive/migrations/
mv reparse_data.py archive/migrations/
```

5. **移動根目錄散落文件**
```bash
mv check_data.py scripts/archive/
```

6. **清理空目錄**
```bash
# spec-workflow/archive 可選擇保留或移除
# spec-workflow/steering 保留（spec workflow 規範允許空存在）
```

### Phase 3: 文檔更新

7. **創建 scripts/README.md**
```markdown
# Scripts Directory

## Production Tools (`production/`)
- `reparse_all_times.py` - 使用最新邏輯重新解析所有時間數據
- `evaluate_full_dataset.py` - 生成完整數據集性能評估報告
- `validate_service_types.py` - 驗證服務類型分類準確性

## Archive (`archive/`)
歷史腳本，已完成任務，保留供參考。

### Round 1 修復測試
### Round 2 修復測試
### 資料遷移腳本
```

8. **更新 README.md**
   - 移除過時的 TODO 章節（已完成）
   - 更新評估工具路徑: `scripts/evaluate_full_dataset.py` → `scripts/production/evaluate_full_dataset.py`

---

## 📏 命名規則檢查

### Python 檔案命名 ✅

**現狀分析**：
- ✅ 模組: `snake_case` (date_utils.py, content_parser.py)
- ✅ 腳本: `snake_case` (reparse_all_times.py, evaluate_full_dataset.py)
- ✅ 類別: `PascalCase` (ContentParser, ExtractedData)
- ✅ 函數: `snake_case` (_extract_predicted_time, parse_resumption_time)

**一致性**: 完全符合 PEP 8 規範 ✅

### 數據檔案命名 ⚠️

**現狀**：
```
✅ master.json                    - 生產數據
⚠️  master.json.backup            - 無時間戳
⚠️  master_old_20251021_170207.json - 不一致格式
✅ master.json.emergency_backup_20251022_155128 - 清楚標註
```

**建議規則**：
```
master.json                           # 生產數據
backups/manual/master_YYYYMMDD_HHMMSS_[label].json  # 手動備份
backups/master_backup_YYYYMMDD_HHMMSS.json           # 自動備份
```

---

## 📦 最終專案結構（建議）

```
PaoMaTeng/
├── .github/workflows/
├── .spec-workflow/
│   ├── specs/railway-news-monitor/
│   ├── templates/
│   └── approvals/
├── config/
├── data/
│   ├── master.json
│   ├── PERFORMANCE_REPORT.md
│   ├── evaluation_report.json
│   └── backups/
│       ├── manual/
│       │   └── master_20251022_155128_emergency.json
│       └── (自動備份 - gitignored)
├── docs/
├── logs/
├── prompts/
├── scripts/
│   ├── README.md
│   ├── production/
│   │   ├── reparse_all_times.py
│   │   ├── evaluate_full_dataset.py
│   │   └── validate_service_types.py
│   └── archive/
│       ├── round1/
│       ├── round2/
│       └── migrations/
├── src/
│   ├── classifiers/
│   ├── models/
│   ├── orchestrator/
│   ├── parsers/
│   ├── scrapers/
│   ├── storage/
│   └── utils/
├── tests/
├── .gitignore
├── README.md
├── requirements.txt
└── PROJECT_CLEANUP_REPORT.md (本文檔)
```

---

## ✅ 預期效果

### 空間節省
- 移除重複備份: ~2.9 MB
- 移除 Icon 檔案: ~20 KB
- **總計節省**: ~3 MB

### 結構清晰度
- ✅ scripts/ 分為 production/ 和 archive/
- ✅ 生產工具易於找到
- ✅ 歷史腳本保留供參考但不干擾

### 版本控制
- ✅ .gitignore 涵蓋所有臨時文件
- ✅ 只追蹤必要檔案
- ✅ 減少 git status 雜訊

### 符合規範
- ✅ 遵循 spec workflow 結構
- ✅ 遵循 Python PEP 8 命名規範
- ✅ 清楚的目錄職責劃分

---

## 🚀 執行建議

**優先級**：
1. **高**: 移除 Icon 檔案、更新 .gitignore
2. **中**: 整理 scripts/ 目錄、移除重複備份
3. **低**: 創建文檔、優化目錄結構

**執行時機**：
- 建議在完成當前功能開發後執行
- 執行前先 commit 當前變更
- 執行後進行測試確保無破壞性影響

---

**報告生成時間**: 2025-10-24
**分析工具**: Claude Code
