# Vercel Cron 自動觸發設定指南

## 🎯 目標

使用 Vercel Cron Jobs 每 5 分鐘自動觸發 GitHub Actions workflow，繞過 GitHub 免費版的 cron 限流。

## 📊 架構

```
Vercel Cron (每 5 分鐘)
  ↓
Serverless Function (/api/trigger-monitor)
  ↓
GitHub API (workflow_dispatch)
  ↓
GitHub Actions (執行監控)
  ↓
更新資料 & 推送
```

## 🚀 部署步驟

### 1. 準備 GitHub Token

1. 前往 https://github.com/settings/tokens
2. 點擊 "Generate new token (classic)"
3. 設定權限：
   - ✅ `repo` (完整權限)
   - ✅ `workflow` (觸發 workflow)
4. 複製 token（格式：`ghp_xxxxxxxxxxxx`）

### 2. 產生 Cron Secret

```bash
# 產生隨機 secret
openssl rand -base64 32
```

複製輸出的字串。

### 3. 連結 Vercel 專案

```bash
cd projects/paomateng

# 連結到 Vercel（如果還沒連結）
vercel link

# 或建立新專案
vercel
```

### 4. 設定環境變數

```bash
# 方法 1: 使用 Vercel CLI
vercel env add GITHUB_TOKEN
# 貼上你的 GitHub token

vercel env add CRON_SECRET
# 貼上剛才產生的 secret

# 方法 2: 在 Vercel Dashboard 設定
# https://vercel.com/[your-team]/paomateng/settings/environment-variables
```

**重要**: 兩個變數都要設定為 **Production** 環境！

### 5. 部署到 Vercel

```bash
# 部署到 production
vercel --prod
```

### 6. 驗證部署

部署完成後，檢查：

1. **Vercel Dashboard**
   - https://vercel.com/[your-team]/paomateng
   - Settings → Crons
   - 應該看到 `/api/trigger-monitor` (每 5 分鐘)

2. **測試 API endpoint**
   ```bash
   # 取得你的 CRON_SECRET
   export CRON_SECRET="your_secret_here"

   # 測試觸發
   curl -X GET \
     -H "Authorization: Bearer $CRON_SECRET" \
     https://your-project.vercel.app/api/trigger-monitor
   ```

   預期回應：
   ```json
   {
     "success": true,
     "message": "Workflow triggered successfully",
     "timestamp": "2025-11-08T10:00:00.000Z",
     "workflow": "monitor.yml"
   }
   ```

3. **檢查 GitHub Actions**
   - 前往 https://github.com/ThinkerCafe-tw/paomateng/actions
   - 應該會看到新的 workflow run

## 📊 監控與除錯

### 查看 Cron 執行日誌

1. Vercel Dashboard → Deployments → [最新部署]
2. Functions → `api/trigger-monitor.js`
3. Logs

### 常見問題

#### ❌ 401 Unauthorized
**原因**: `CRON_SECRET` 設定錯誤或未設定
**解決**: 檢查 Vercel 環境變數

#### ❌ 500 Configuration Error - GITHUB_TOKEN not set
**原因**: `GITHUB_TOKEN` 未設定
**解決**: 在 Vercel 設定環境變數

#### ❌ GitHub API Error (403/404)
**原因**: GitHub token 權限不足或已過期
**解決**: 重新產生 token，確認有 `repo` 和 `workflow` 權限

#### ⚠️ Cron 沒有每 5 分鐘執行
**原因**: Vercel 免費版可能有頻率限制
**檢查**: Vercel Dashboard → Settings → Crons
**說明**: Vercel Pro 才保證精準執行頻率

## 💰 成本分析

### Vercel 免費版限制
- ✅ Serverless Functions: 100GB-hours/月
- ✅ Invocations: 100,000 次/月
- ⚠️ Execution Time: 10 秒/次
- ⚠️ Cron Jobs: "Best effort" (不保證精準)

### 預估使用量
- **Cron 頻率**: 每 5 分鐘
- **每月執行**: 12 次/小時 × 24 小時 × 30 天 = 8,640 次
- **執行時間**: 約 0.5 秒/次
- **Function Hours**: (8,640 × 0.5) / 3600 = 1.2 GB-hours

**結論**: 免費版綽綽有餘！

### 升級到 Pro 的考量
如果需要**精準的 5 分鐘執行頻率**，考慮升級到 Vercel Pro ($20/月)。

## 🔄 替代方案

### 方案比較

| 方案 | 成本 | 執行頻率 | 穩定性 | 設定複雜度 |
|------|------|---------|--------|----------|
| **Vercel Cron (免費)** | $0 | ~5-10 分鐘 | 中 | 低 |
| **Vercel Cron (Pro)** | $20/月 | 精準 5 分鐘 | 高 | 低 |
| **n8n Cloud** | $0 (5000 次/月) | 精準 5-10 分鐘 | 高 | 中 |
| **GitHub Actions** | $0 | 3-4 小時 | 低（限流）| 低 |

### 推薦方案
- **研究用途**: Vercel Cron 免費版（夠用）
- **生產環境**: n8n Cloud 或 Vercel Pro

## 📝 維護

### 更新 API endpoint
修改 `api/trigger-monitor.js` 後：
```bash
vercel --prod
```

### 檢查執行統計
```bash
# 使用 Vercel CLI
vercel logs --follow

# 或在 Vercel Dashboard 查看
```

### 停用 Cron
刪除 `vercel.json` 中的 `crons` 區塊，然後重新部署。

---

**建立時間**: 2025-11-08
**維護者**: Cruz Tang
**狀態**: 待部署
