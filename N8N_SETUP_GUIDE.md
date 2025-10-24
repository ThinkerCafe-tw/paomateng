# 🔄 n8n 自動監控設定指南

**目的**: 使用 n8n 實現穩定的 5 分鐘監控週期，解決 GitHub Actions 免費版限流問題

**最終方案**: n8n Schedule Trigger → GitHub API → 觸發 GitHub Actions 執行監控

---

## 📊 為什麼選擇 n8n？

| 項目 | GitHub Actions (免費版) | n8n + GitHub Actions |
|------|------------------------|---------------------|
| **執行頻率** | 實際 3-4 小時 (限流) | 真正每 5 分鐘 ✅ |
| **日誌查看** | 需下載 Artifacts | n8n + GitHub 雙重日誌 ✅ |
| **設定複雜度** | YAML 配置 | 視覺化拖拉 (2 nodes) ✅ |
| **運算資源** | GitHub 免費額度 | GitHub 免費額度 (不變) ✅ |
| **觸發穩定性** | 不穩定 (限流) | 穩定 (n8n 控制) ✅ |
| **成本** | 免費 | 免費 (n8n: 5000 executions/月) |

**結論**: n8n 作為穩定的時鐘，通過 API 觸發 GitHub Actions，結合兩者優勢

---

## 🎯 最簡架構：2 個 Nodes

```
[Schedule Trigger] → [GitHub node]
     每5分鐘         觸發 GitHub Actions API
                            ↓
                    GitHub Actions 執行監控
                            ↓
                    抓取 → 更新 → Push
```

### 優勢

✅ **n8n Cloud 可用** - 不需要本地環境或伺服器
✅ **運算在 GitHub** - 使用 GitHub 的免費運算資源
✅ **OAuth2 認證** - 安全且易於管理
✅ **雙重日誌** - n8n 執行歷史 + GitHub Actions logs
✅ **真正每 5 分鐘** - 不受 GitHub Actions 限流影響

---

## 🛠️ 設定步驟（10 分鐘完成）

### 步驟 1: 註冊 n8n Cloud

1. 訪問: https://n8n.io/cloud
2. 註冊免費帳號
3. 免費方案: **5000 executions/月**（足夠每 5 分鐘執行，每月約 8640 次）

---

### 步驟 2: 連接 GitHub 帳號

1. 在 n8n 介面，點擊左側 **"Credentials"**
2. 點擊 **"Add Credential"**
3. 搜尋 **"GitHub"** → 選擇 **"GitHub OAuth2 API"**
4. 點擊 **"Connect my account"**
5. 登入 GitHub 並授權 n8n（需要 `repo` 權限）
6. 儲存 credential

---

### 步驟 3: 建立 Workflow

#### 3.1 新增 Schedule Trigger Node

1. 建立新 Workflow，命名為 `Railway Monitor`
2. 點擊 **"+"** 新增 node
3. 搜尋 **"Schedule Trigger"**
4. 設定：
   - **Trigger Interval**: `Minutes`
   - **Minutes Between Triggers**: `5`

#### 3.2 新增 GitHub Node

1. 點擊 **"+"** 新增 node
2. 搜尋 **"GitHub"**
3. 設定：
   - **Credential**: 選擇剛才建立的 GitHub OAuth2
   - **Resource**: `Workflow`
   - **Operation**: `Dispatch a workflow event`
   - **Owner**: `ThinkerCafe-tw` (您的 GitHub 用戶名/組織)
   - **Repository**: `paomateng`
   - **Workflow ID**: 選擇 `Railway News Monitor` (或輸入 ID: 199586742)
   - **Ref**: `main`

#### 3.3 連接 Nodes

拖動 **Schedule Trigger** 右側的圓點到 **GitHub** node

```
[Schedule Trigger] ──→ [GitHub]
```

---

### 步驟 4: 測試 Workflow

1. **不要先啟用 Active**
2. 點擊 **"Test Workflow"** 按鈕（右上角）
3. 應該看到執行成功
4. 前往 GitHub Actions 確認：
   ```
   https://github.com/ThinkerCafe-tw/paomateng/actions
   ```
   應該看到一個新的 "Manually run by [your-username]"

---

### 步驟 5: 啟用自動執行

測試成功後：
1. 點擊右上角 **"Active"** 開關（切換為綠色）
2. Workflow 開始自動每 5 分鐘執行

🎉 **完成！** 系統現在每 5 分鐘穩定執行一次

---

## 📝 完整 Workflow JSON (可直接匯入)

匯入檔案位置：`n8n-workflow-trigger-github-actions.json`

**匯入方式**:
1. n8n 介面 → 右上角選單 → **"Import from file"**
2. 選擇 `n8n-workflow-trigger-github-actions.json`
3. 點擊 GitHub node → 設定 GitHub OAuth2 credential
4. 測試並啟用

---

## 📝 停用 GitHub Actions Schedule (重要)

為避免重複執行，需停用 GitHub Actions 的 cron schedule：

**`.github/workflows/monitor.yml`** 已修改為：

```yaml
on:
  # 已停用 schedule (改用 n8n 觸發)
  # schedule:
  #   - cron: '*/5 * * * *'

  # n8n 通過此方式觸發
  workflow_dispatch:  ✅

  # 代碼更新時執行
  push:
    branches: [ main ]
```

**說明**:
- ❌ **Schedule cron** - 已註解停用
- ✅ **workflow_dispatch** - 保留給 n8n API 觸發
- ✅ **push** - 代碼更新時測試用

---

## 🔍 監控與日誌

### 1. n8n 執行歷史

訪問 n8n 介面 → **Executions**

**可以看到**:
- ✅ 每次執行的時間
- ✅ 執行結果 (成功/失敗)
- ✅ GitHub API 回應
- ✅ 執行時長

**範例**:
```
Execution #12345
Started: 2025-10-24 15:35:00
Duration: 0.8s
Status: Success

[GitHub node] Output:
Status: 204 No Content (成功觸發)
```

### 2. GitHub Actions 日誌

訪問: https://github.com/ThinkerCafe-tw/paomateng/actions

**可以看到**:
- ✅ 每次監控執行的完整日誌
- ✅ Python 腳本輸出
- ✅ 資料更新情況
- ✅ Git commit 記錄

**識別 n8n 觸發**:
- 標記為 "Manually run by [username]"
- 每 5 分鐘執行一次

---

## 🔧 故障排除

### 問題 1: GitHub node 無法連接

**症狀**: "Authentication failed"

**解決**:
1. 重新建立 GitHub OAuth2 credential
2. 確認授權時勾選了 `repo` 權限
3. 測試 credential 連接

### 問題 2: Workflow 未觸發

**症狀**: n8n 執行成功，但 GitHub Actions 沒有執行

**解決**:
1. 檢查 Workflow ID 是否正確
2. 確認 Ref 是 `main`（不是 `master`）
3. 檢查 `.github/workflows/monitor.yml` 是否有 `workflow_dispatch`

### 問題 3: 執行頻率不正確

**症狀**: 沒有每 5 分鐘執行

**解決**:
1. 檢查 Schedule Trigger 設定
2. 確認 Workflow 已啟用 Active
3. 查看 n8n Executions 頁面確認觸發歷史

---

## 📊 執行頻率計算

**設定**: 每 5 分鐘執行一次

**每日執行次數**: 24 小時 × 60 分鐘 ÷ 5 = **288 次/天**
**每月執行次數**: 288 次/天 × 30 天 = **8640 次/月**

**n8n 免費額度**: 5000 executions/月
**超出**: 8640 - 5000 = **3640 次** ⚠️

### 建議調整

如果要在免費額度內：
- **10 分鐘/次**: 4320 次/月 ✅ (在額度內)
- **7 分鐘/次**: 6171 次/月 ⚠️ (稍微超出)

**修改方式**:
- Schedule Trigger → Minutes Between Triggers 改為 `10`

---

## 📞 技術支援

### n8n 相關
- 官方文檔: https://docs.n8n.io/
- 社群論壇: https://community.n8n.io/
- Discord: https://discord.gg/n8n

### 專案相關
- `MONITORING_DIAGNOSIS.md` - GitHub Actions 診斷
- `DELIVERY_GUIDE.md` - 專案交付指南
- `README.md` - 專案使用說明

---

## 🎯 Self-hosted n8n (可選)

如果希望完全免費且無執行次數限制：

### 安裝方式

```bash
# 使用 Docker (推薦)
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# 訪問: http://localhost:5678
```

### 持續運行 (使用 Docker Compose)

創建 `docker-compose.yml`:

```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    volumes:
      - ~/.n8n:/home/node/.n8n
```

啟動:
```bash
docker-compose up -d
```

**優點**:
- 無執行次數限制
- 完全免費
- 本地控制

**缺點**:
- 需要維護伺服器
- 需要確保持續運行

---

**最後更新**: 2025-10-24
**建議方案**: n8n Cloud (10分鐘/次) 或 Self-hosted (5分鐘/次)
**預期效果**: 穩定的定時執行 + 完整日誌記錄
