# 🚂 Railway News Monitor - 交付指南

**專案名稱**: 臺鐵公告監控系統
**交付日期**: 2025-10-24
**專案狀態**: ✅ 生產就緒 (Production Ready)
**GitHub Pages**: https://thinkercafe-tw.github.io/paomateng/
**GitHub Repo**: https://github.com/ThinkerCafe-tw/paomateng

---

## 📦 專案交付清單

### 1. 核心系統

| 組件 | 狀態 | 說明 |
|------|------|------|
| **自動化監控** | ✅ 運行中 | GitHub Actions（實際 3-4 小時/次）或 n8n（真正 5 分鐘/次） |
| **資料抓取** | ✅ 完成 | 已抓取 126 筆公告，共 133 個版本 |
| **時間提取** | ✅ 100% | Precision & Recall 均達 100% |
| **服務類型分類** | ✅ 完成 | 11 筆已分類（normal_train/shuttle_service/partial_operation） |
| **GitHub Pages** | ✅ 上線 | 研究導向互動式儀表板 |
| **文檔** | ✅ 完整 | README、使用指南、部署文檔、測試歷史、n8n 設定指南 |

### 2. 資料品質

- **總公告數**: 126 筆
- **資料量**: 676 KB (master.json)
- **預測恢復時間**: 12 筆
- **實際恢復時間**: 11 筆
- **服務類型標記**: 11 筆
- **總版本數**: 133 個（含變更追蹤）

### 3. 測試與驗證

- **測試輪次**: 7+ 輪完整測試（2025-10-21 至 2025-10-24）
- **時間提取準確度**: 100% Precision & Recall
- **自動化測試**: pytest 單元測試與整合測試
- **性能評估報告**: `data/PERFORMANCE_REPORT.md`
- **測試歷史文檔**: `TESTING_HISTORY.md`

---

## 🗂️ 專案結構

```
PaoMaTeng/
│
├── 📊 資料檔案
│   ├── data/
│   │   ├── master.json                    # 主要資料檔（126 筆公告）
│   │   ├── master.json.lock               # 檔案鎖定（防止並發寫入）
│   │   ├── backups/                       # 自動備份（每次寫入前）
│   │   ├── evaluation_report.json         # 性能評估報告（JSON）
│   │   └── PERFORMANCE_REPORT.md          # 性能評估報告（Markdown）
│
├── 🌐 GitHub Pages (公開展示)
│   └── docs/
│       ├── index.html                     # 互動式儀表板（研究場景篩選器）
│       ├── DATA_SCHEMA.md                 # 資料結構說明
│       └── DEPLOYMENT.md                  # 部署指南
│
├── 🐍 Python 核心系統
│   └── src/
│       ├── main.py                        # CLI 進入點
│       ├── models/
│       │   └── announcement.py            # Pydantic 資料模型
│       ├── scrapers/
│       │   ├── list_scraper.py            # 列表頁爬蟲
│       │   └── detail_scraper.py          # 詳細頁爬蟲
│       ├── parsers/
│       │   └── content_parser.py          # 內容解析（9 個欄位）
│       ├── classifiers/
│       │   └── announcement_classifier.py # 公告分類器
│       ├── storage/
│       │   └── json_storage.py            # JSON 儲存（原子寫入）
│       ├── orchestrator/
│       │   ├── historical_scraper.py      # 歷史抓取
│       │   ├── monitor.py                 # 持續監控
│       │   └── monitor_once.py            # 單次監控（GitHub Actions）
│       └── utils/
│           └── date_utils.py              # 日期解析工具
│
├── ⚙️ 設定檔
│   └── config/
│       ├── settings.yaml                  # 系統設定
│       ├── keywords.yaml                  # 分類關鍵字
│       └── regex_patterns.yaml            # 時間提取正則表達式
│
├── 🤖 GitHub Actions 自動化
│   └── .github/
│       └── workflows/
│           └── monitor.yml                # 每5分鐘執行一次
│
├── 🧪 測試與腳本
│   ├── tests/                             # pytest 測試
│   └── scripts/
│       ├── production/                    # 生產工具
│       │   ├── reparse_all_times.py       # 重新解析所有時間
│       │   ├── evaluate_full_dataset.py   # 完整資料集評估
│       │   └── validate_service_types.py  # 驗證服務類型
│       ├── archive/                       # 歷史腳本（參考用）
│       └── README.md                      # 腳本使用說明
│
├── 📚 文檔
│   ├── README.md                          # 專案總覽與快速開始
│   ├── TESTING_HISTORY.md                 # 測試歷程記錄
│   ├── PROJECT_CLEANUP_REPORT.md          # 專案結構收斂報告
│   ├── MONITORING_DIAGNOSIS.md            # GitHub Actions 執行頻率診斷
│   ├── N8N_SETUP_GUIDE.md                 # n8n 監控設定指南（穩定 5 分鐘監控）
│   ├── DELIVERY_GUIDE.md                  # 🎯 本文件
│   └── n8n-workflow-railway-monitor.json  # n8n Workflow 配置檔（可直接匯入）
│
└── 📊 研究文檔
    └── .spec-workflow/                    # Spec Workflow 文檔
        └── specs/railway-news-monitor/
            ├── requirements.md            # 需求文件
            ├── design.md                  # 設計文件
            └── tasks.md                   # 任務清單（全部完成）
```

---

## 🎯 核心功能說明

### 1. 自動化監控

**兩種選項**:

#### 選項 A: GitHub Actions（零成本，適合研究用途）
- **配置**: 每 5 分鐘執行一次
- **實際**: 約每 3-4 小時執行一次（免費版限流）
- **優點**: 零成本、零維護、資料完整性保證
- **限制**: 執行頻率低於預期
- **適用**: 研究用途（幾小時延遲不影響資料品質）

#### 選項 B: n8n Workflow（穩定 5 分鐘監控）
- **執行頻率**: 真正的每 5 分鐘
- **優點**: 穩定頻率、內建日誌、視覺化介面
- **限制**: 需保持 n8n 運行
- **適用**: 需要即時監控的場景

**詳細比較**: 參見下方「⚙️ 監控頻率選項」章節

**查看狀態**:
- GitHub Actions 頁籤 → 綠色勾勾 = 成功
- 最新資料自動更新到 `data/master.json`
- GitHub Pages 自動刷新

### 2. 資料結構（9 個欄位）

每個公告的 `extracted_data` 包含：

1. **report_version**: 報告版次（"1", "2", "第3報"）
2. **event_type**: 事件類型（Typhoon, Heavy_Rain, Earthquake）
3. **status**: 營運狀態（Suspended, Partial_Operation, Resumed_Normal）
4. **affected_lines**: 受影響路線（["西部幹線", "東部幹線"]）
5. **affected_stations**: 受影響車站（["二水", "林內"]）
6. **predicted_resumption_time**: 預測恢復時間（ISO 8601）⭐ 核心研究欄位
7. **actual_resumption_time**: 實際恢復時間（ISO 8601）
8. **service_type**: 服務類型（normal_train, shuttle_service, partial_operation）⭐ NEW
9. **service_details**: 服務詳情（"單線雙向通車", "接駁公車"）⭐ NEW

### 3. GitHub Pages 研究場景篩選器

**設計理念**: 用研究目的（而非技術術語）來過濾資料

| 研究場景 | 說明 | 技術條件 |
|---------|------|----------|
| 🔴 停駛初報 | 首次宣布停駛 | `category === "Disruption_Suspension"` |
| 📢 停駛更新報 | 第2、3報等 | `category === "Disruption_Update"` |
| ✅ 恢復通車公告 | 宣布恢復行駛 | `category === "Disruption_Resumption"` |
| ⏸️ 當前仍在停駛中 | 內文提到停駛狀態 | `status === "Suspended"` |
| 🌧️ 氣象相關事件 | 颱風、豪雨、地震 | `category === "Weather_Related"` |
| 📊 完整停駛事件序列 | 初報+更新+恢復 | `category in [...]` |

**使用方式**:
1. 訪問 https://thinkercafe-tw.github.io/paomateng/
2. 選擇研究場景 → 自動過濾
3. 點擊標題 → 查看詳細資訊、JSON 數據
4. 點擊「🔍 查看此篩選器的技術條件」了解過濾邏輯

---

## 📋 交付給業主的步驟

### 方式一：直接使用 GitHub（推薦）

**業主無需任何安裝，直接使用**：

1. **訪問 GitHub Pages**
   https://thinkercafe-tw.github.io/paomateng/

2. **下載最新資料**
   https://github.com/ThinkerCafe-tw/paomateng/blob/main/data/master.json

3. **查看自動化狀態**
   https://github.com/ThinkerCafe-tw/paomateng/actions

**優點**:
- 零維護成本
- 資料自動更新
- 隨時可下載 JSON
- 網頁介面友善

### 方式二：轉移 GitHub Repo 所有權

如果業主希望擁有完整控制權：

1. **GitHub Settings** → **General** → **Transfer ownership**
2. 輸入業主的 GitHub 帳號
3. 業主接受轉移
4. GitHub Actions 和 Pages 自動保留

**優點**:
- 業主完全控制
- 可自行修改程式碼
- 保留所有歷史記錄

### 方式三：本地部署（進階使用）

如果業主希望在本地或自己的伺服器運行：

#### 1. 安裝環境

```bash
# Clone 專案
git clone https://github.com/ThinkerCafe-tw/paomateng.git
cd paomateng

# 安裝依賴
pip install -r requirements.txt
```

#### 2. 執行歷史抓取（首次）

```bash
python -m src.main --mode historical
```

#### 3. 執行持續監控

```bash
python -m src.main --mode monitor
```

#### 4. 使用生產工具

```bash
# 重新解析所有時間（更新提取邏輯後）
python3 scripts/production/reparse_all_times.py

# 生成完整評估報告
python3 scripts/production/evaluate_full_dataset.py

# 驗證服務類型分類
python3 scripts/production/validate_service_types.py
```

**詳細說明**: 參見 `docs/DEPLOYMENT.md`

---

## ⚙️ 監控頻率選項

### GitHub Actions（免費版限制說明）

**⚠️ 重要**: GitHub Actions 免費版會對高頻 cron job 進行限流

**配置**: 每 5 分鐘執行一次（`.github/workflows/monitor.yml`）
**實際**: 約每 3-4 小時執行一次（受限流影響）

**診斷報告**: 參見 `MONITORING_DIAGNOSIS.md`

**適用情況**:
- ✅ 研究用途（幾小時延遲不影響資料品質）
- ✅ 零成本零維護
- ✅ 資料完整性保證（所有公告最終都會抓到）

**不適用情況**:
- ❌ 需要即時監控（5分鐘級別）
- ❌ 需要穩定執行頻率

### n8n Workflow（推薦：穩定 5-10 分鐘監控）

**如果需要真正的穩定執行頻率**，推薦使用 **n8n + GitHub Actions**：

**架構**: n8n 定時器 → GitHub Actions API → 執行監控

**優勢**:
- ✅ 穩定的執行頻率（5-10 分鐘可選）
- ✅ n8n + GitHub 雙重日誌
- ✅ 視覺化介面，易於除錯
- ✅ 運算在 GitHub（免費資源）
- ✅ n8n Cloud 免費: 5000 executions/月

**快速設定** (10 分鐘):
1. 註冊 n8n Cloud: https://n8n.io/cloud
2. 連接 GitHub 帳號 (OAuth2)
3. 建立 2-node workflow:
   - Schedule Trigger (每 5-10 分鐘)
   - GitHub node (觸發 workflow_dispatch)
4. 啟用 Active

**Workflow 結構**:
```
n8n Schedule Trigger (每5-10分鐘)
         ↓
   GitHub API 觸發
         ↓
  GitHub Actions 執行監控
         ↓
   抓取 → 更新 → Push
```

**詳細指南**: 參見 `N8N_SETUP_GUIDE.md`
**Workflow 檔案**: `n8n-workflow-trigger-github-actions.json`

**比較表**:

| 項目 | GitHub Actions (免費) | n8n + GitHub Actions |
|------|----------------------|---------------------|
| **執行頻率** | 3-4 小時 (限流) | 5-10 分鐘（穩定） ✅ |
| **日誌查看** | 需下載 Artifacts | 雙重日誌（n8n + GitHub） ✅ |
| **運算資源** | GitHub 免費額度 | GitHub 免費額度（相同） |
| **成本** | 免費 | 免費 (n8n: 5000 executions/月) |
| **維護** | 零維護 ✅ | n8n Cloud 託管 |
| **適用場景** | 研究用途 | 研究 + 即時監控 ✅ |

### 推薦配置

**僅研究用途**（可接受數小時延遲）:
- 保持 GitHub Actions（零成本零維護）

**需要穩定監控**（5-10分鐘級別）:
- **推薦**: n8n Cloud (10分鐘/次) - 在免費額度內
- **進階**: Self-hosted n8n (5分鐘/次) - 無限制

**當前配置** ✅:
- GitHub Actions schedule 已停用
- n8n 通過 API 觸發 GitHub Actions
- 執行頻率: 每 5 分鐘（已設定並運行中）

---

## 🔧 維護與更新

### 日常維護（自動）

- ✅ **GitHub Actions 自動執行**，無需人工介入
- ✅ **資料自動備份**到 `data/backups/`
- ✅ **GitHub Pages 自動更新**

### 偶爾需要（手動）

#### 更新提取邏輯後重新解析

```bash
# 修改 src/parsers/content_parser.py 或 src/utils/date_utils.py 後
python3 scripts/production/reparse_all_times.py
```

#### 驗證資料品質

```bash
# 生成完整性能報告
python3 scripts/production/evaluate_full_dataset.py

# 查看報告
cat data/PERFORMANCE_REPORT.md
```

#### 驗證服務類型分類

```bash
python3 scripts/production/validate_service_types.py
```

### 監控健康狀態

1. **GitHub Actions 頁面**
   https://github.com/ThinkerCafe-tw/paomateng/actions

2. **查看最新 commit**
   應該每 5 分鐘有自動 commit（如果有變更）

3. **檢查錯誤**
   如果有紅色 X，點擊查看 logs

---

## 📊 性能指標

### 時間提取準確度（2025-10-24）

| 指標 | 數值 |
|------|------|
| **Precision** | 100% |
| **Recall** | 100% |
| **F1 Score** | 100% |
| **測試輪次** | 7+ 輪 |
| **測試案例** | 50+ 個手動驗證案例 |

**詳細報告**: `data/PERFORMANCE_REPORT.md`

### 服務類型分類（NEW!）

| 服務類型 | 數量 |
|---------|------|
| normal_train | 5 個 |
| partial_operation | 4 個 |
| shuttle_service | 2 個 |

**驗證方式**: `python3 scripts/production/validate_service_types.py`

---

## 📚 關鍵文檔對照表

| 文檔 | 路徑 | 用途 |
|------|------|------|
| **專案總覽** | `README.md` | 快速開始、功能說明 |
| **交付指南** | `DELIVERY_GUIDE.md` | 🎯 本文件 |
| **資料結構** | `docs/DATA_SCHEMA.md` | JSON 結構說明 |
| **部署指南** | `docs/DEPLOYMENT.md` | 本地/伺服器部署 |
| **測試歷史** | `TESTING_HISTORY.md` | 7 輪測試完整記錄 |
| **性能報告** | `data/PERFORMANCE_REPORT.md` | 100% 準確度驗證 |
| **專案清理報告** | `PROJECT_CLEANUP_REPORT.md` | 結構收斂說明 |
| **腳本說明** | `scripts/README.md` | 生產工具使用指南 |

---

## 🎓 研究使用範例

### Python 腳本分析

```python
import json

# 載入資料
with open('data/master.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 範例 1: 找出所有停駛初報
suspension_initial = [
    ann for ann in data
    if ann['classification']['category'] == 'Disruption_Suspension'
]
print(f'停駛初報數量: {len(suspension_initial)}')

# 範例 2: 分析預測時間演變
for ann in data:
    if len(ann['version_history']) > 1:
        print(f"\n公告: {ann['title']}")
        for i, ver in enumerate(ann['version_history'], 1):
            predicted = ver['extracted_data'].get('predicted_resumption_time')
            if predicted:
                print(f"  版本 {i}: {predicted}")

# 範例 3: 服務類型分布
service_types = {}
for ann in data:
    service_type = ann['version_history'][0]['extracted_data'].get('service_type')
    if service_type:
        service_types[service_type] = service_types.get(service_type, 0) + 1

print('\n服務類型分布:')
for stype, count in service_types.items():
    print(f'  {stype}: {count}')
```

### 直接使用 GitHub Pages

1. 訪問 https://thinkercafe-tw.github.io/paomateng/
2. 選擇「🔴 停駛初報」
3. 點擊任一標題查看詳細資訊
4. 點擊「顯示 JSON」查看原始資料

---

## ✅ 交付檢查清單

### 給業主的檢查清單

- [ ] 能訪問 GitHub Pages: https://thinkercafe-tw.github.io/paomateng/
- [ ] 能下載 master.json
- [ ] 能看到研究場景篩選器正常運作
- [ ] 能點擊標題查看詳細資訊
- [ ] 能查看 JSON 原始資料
- [ ] GitHub Actions 每 5 分鐘自動執行
- [ ] 資料自動更新

### 技術交付清單

- [x] ✅ 核心系統完成（抓取、解析、分類、儲存）
- [x] ✅ GitHub Actions 自動化部署
- [x] ✅ GitHub Pages 互動式儀表板
- [x] ✅ 時間提取 100% 準確度
- [x] ✅ 服務類型分類功能
- [x] ✅ 完整測試與驗證（7+ 輪）
- [x] ✅ 性能評估報告
- [x] ✅ 文檔完整（README、DEPLOYMENT、TESTING_HISTORY）
- [x] ✅ 生產工具（reparse、evaluate、validate）
- [x] ✅ 排序問題已修復（最新在前）

---

## 🆘 故障排除

### GitHub Actions 執行失敗

1. 檢查 Actions 頁面的錯誤 log
2. 常見問題：
   - TRA 網站無法訪問 → 等待下一次執行
   - Rate limiting → 調整 `config/settings.yaml` 中的 `rate_limit_delay`
   - 權限問題 → 確認 GitHub Actions 有寫入權限

### 本地執行錯誤

```bash
# 檢查 log
cat logs/railway_monitor.log

# 重新安裝依賴
pip install -r requirements.txt --upgrade

# 驗證設定
cat config/settings.yaml
```

### 資料異常

```bash
# 從備份恢復
cp data/backups/master_*.json data/master.json

# 重新解析
python3 scripts/production/reparse_all_times.py
```

---

## 📞 聯絡資訊

**專案維護者**: ThinkerCafe
**GitHub**: https://github.com/ThinkerCafe-tw/paomateng
**Issues**: https://github.com/ThinkerCafe-tw/paomateng/issues

---

## 📝 授權說明

本專案為學術研究用途。所有資料來自台灣鐵路管理局公開網站。

**注意事項**:
- 遵守 TRA robots.txt 規範
- Rate limiting: 1 request/second
- 僅抓取公開資訊
- 不做任何商業用途

---

**交付日期**: 2025-10-24
**專案狀態**: ✅ Production Ready
**資料量**: 126 筆公告，133 個版本，676 KB
**性能**: 100% Precision & Recall
