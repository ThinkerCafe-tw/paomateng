---
inherits_from: ../../knowledge-base/CLAUDE_ROOT.md
project: paomateng
persona: Automation Monitor
project_type: research_automation
last_updated: 2025-11-11
---

# 🚂 Paomateng - 台鐵公告監控系統

> 台鐵即時公告追蹤與分析系統（學術研究用途）
> 繼承 ThinkerCafe 核心原則，專注於零成本自動化

---

## 🎯 專案概述

**一句話說明**: 自動監控台鐵公告，追蹤危機溝通演變模式（林教授研究）

**核心特色**:
- ✅ 完全自動化（Vercel Cron + GitHub Actions）
- ✅ 零成本運行（GitHub + Vercel 免費版）
- ✅ 每 5 分鐘執行監控（有變更時自動提交）
- ✅ 即時 Dashboard（GitHub Pages）

---

## 📊 當前狀態

### 運行狀態
- **執行方式**: ✅ **Vercel Cron** (每 5 分鐘) → GitHub Actions
- **資料儲存**: GitHub (data/master.json)
- **Dashboard**: https://thinkercafe-tw.github.io/paomateng/
- **Vercel API**: https://paomateng.vercel.app/api/trigger-monitor
- **執行模式**: 每 5 分鐘執行爬蟲，有變更時才產生 commit
- **整合時間**: 2025-11-08

### 最近完成 (2025-11-11)
- ✅ 整合進 ThinkerCafe monorepo
- ✅ **Vercel Cron 穩定運行**（每 5 分鐘執行）
- ✅ 驗證執行機制：每次執行爬蟲，僅在資料變更時提交
- ✅ 成功捕獲 11/11 東部幹線停駛事件（發布後 20 分鐘內）
- ✅ 建立完整文檔（包含實際執行流程分析）

### Vercel Cron 執行模式
- ✅ Vercel Cron 每 5 分鐘觸發 GitHub Actions
- ✅ GitHub Actions 每次都執行爬蟲（約 288 次/天）
- ✅ 僅在檢測到新公告或內容變更時產生 git commit
- 📄 Commit 間隔取決於台鐵網站更新頻率（通常數十分鐘到數小時）

---

## 🏗️ 技術架構

### 系統流程
```
Vercel Cron Job (每 5 分鐘)
  ↓
/api/trigger-monitor (Vercel Serverless Function)
  ↓
GitHub API (workflow_dispatch)
  ↓
GitHub Actions 執行 (每次都執行)
  ↓
Python Scraper → 台鐵網站
  ↓
解析 & 儲存 (data/master.json)
  ↓
Git Diff 檢查
  ├─ 有變更 → Git commit & push → GitHub Pages 更新
  └─ 無變更 → 僅記錄日誌，不產生 commit
```

### 技術棧
- **觸發**: Vercel Cron (每 5 分鐘)
- **API**: Vercel Serverless Function (Node.js)
- **執行**: GitHub Actions (Python 3.11)
- **爬蟲**: BeautifulSoup4 + Requests
- **儲存**: JSON (Atomic Write)
- **前端**: GitHub Pages (靜態 HTML)
- **成本**: $0/月 (Vercel + GitHub 免費額度)

### 研究價值
- 危機溝通演變模式
- 預估復駛時間準確性
- 公告更新頻率與事件嚴重性關係

---

## 🗂️ 重要檔案索引

### 技術文檔
- **執行流程分析**: @MONITORING_DIAGNOSIS.md (已更新為 Vercel Cron 實際執行)
- **Vercel 配置**: `vercel.json`, `api/trigger-monitor.js`
- **n8n 方案**: @N8N_SETUP_GUIDE.md (替代方案)
- **交付指南**: @DELIVERY_GUIDE.md

### 核心程式碼
- **Vercel API**: `api/trigger-monitor.js` (觸發 GitHub Actions)
- **GitHub Workflow**: `.github/workflows/monitor.yml`
- **爬蟲邏輯**: `src/orchestrator/monitor_once.py`
- **資料儲存**: `data/master.json`

### 專案根文件
- **README**: @README.md

---

## 🔧 常用指令

### 監控狀態查看
```bash
# 查看最近的 commits（只顯示有變更的執行）
git log --grep="Auto-update" --oneline -10

# 查看今天的所有更新
git log --grep="Auto-update" --since="today" --format="%ci | %s"

# 計算 commit 時間間隔
git log --grep="Auto-update" --since="1 day ago" --format="%ci"
```

### GitHub Actions
```bash
# 查看執行歷史（包含所有執行，不只是有 commit 的）
# 注意：大部分執行不會產生 commit（無變更時）
gh run list --repo ThinkerCafe-tw/paomateng --limit 20

# 查看最新執行的詳細資訊
gh run view --repo ThinkerCafe-tw/paomateng

# 手動觸發（測試用）
gh workflow run monitor.yml --repo ThinkerCafe-tw/paomateng
```

### Vercel 管理
```bash
# 測試 Vercel API（手動觸發一次）
curl -X POST https://paomateng.vercel.app/api/trigger-monitor

# 查看 Vercel 部署狀態
vercel ls paomateng
```

### 本地測試
```bash
cd /path/to/paomateng

# 執行單次監控（模擬 GitHub Actions 執行）
python -m src.orchestrator.monitor_once

# 執行測試
pytest tests/
```

---

## 🔗 相關連結

### Production
- **Dashboard**: https://thinkercafe-tw.github.io/paomateng/
- **API**: https://paomateng.vercel.app/api/trigger-monitor
- **GitHub**: https://github.com/ThinkerCafe-tw/paomateng
- **Actions**: https://github.com/ThinkerCafe-tw/paomateng/actions

### 開發資源
- **台鐵公告網站**: https://www.railway.gov.tw/tra-tip-web/tip
- **Vercel Dashboard**: https://vercel.com/cruz-5538s-projects/paomateng

---

## 💡 維護注意事項

### 監控檢查
1. ✅ Vercel Cron 執行狀態（Vercel Dashboard → Functions → Logs）
2. ✅ GitHub Actions 成功率（Actions 頁面，每天應有 ~288 次執行）
3. ✅ 資料更新時間（檢查 master.json commit，間隔取決於台鐵更新）
4. ✅ Dashboard 顯示正常（https://thinkercafe-tw.github.io/paomateng/）

### 成本追蹤
- Vercel Cron: $0（免費額度：100 GB-Hours/月）
- GitHub Actions: $0（免費額度：2000 分鐘/月，實際使用 <500 分鐘/月）
- 總成本: **$0/月**

### 執行特性理解
- **執行頻率**: Vercel Cron 每 5 分鐘觸發（約 288 次/天）
- **Commit 頻率**: 僅在資料變更時產生（通常 3-8 次/天）
- **正常現象**: Git log 顯示的 commit 間隔數十分鐘到數小時
- **異常判斷**: 如果超過 24 小時無 commit，檢查 GitHub Actions 是否執行

### 故障排除
**症狀：超過 24 小時無新 commit**
1. 訪問 Actions 頁面，確認是否有執行記錄
2. 若有執行但無 commit → 正常（表示台鐵無新公告）
3. 若完全無執行 → 檢查 Vercel Cron 或 GitHub token

**症狀：GitHub Actions 執行失敗**
1. 查看 Actions logs
2. 常見問題：台鐵網站無法訪問、Python 依賴問題
3. 解決後會在下次執行自動恢復

### 備選方案
如需更換執行環境：
- 方案 1: n8n Cloud（參考 N8N_SETUP_GUIDE.md，更好的日誌）
- 方案 2: 自架伺服器 + cron（完全控制）
- 方案 3: GitHub Actions schedule（但會被限流到 3-4 小時）

---

**Generated by**: Claude Code
**Last Updated**: 2025-11-11
**Maintainer**: Cruz Tang
**Status**: Production - Vercel Cron 穩定運行中（每 5 分鐘執行）
