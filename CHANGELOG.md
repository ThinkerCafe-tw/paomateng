# Changelog

本檔案記錄 Paomateng 台鐵公告監控系統的重要變更與事件。

---

## [2025-12-19] 系統修復與分類邏輯改進

### 🔧 排程修復

**問題**：系統自 2025-11-26 起停止自動執行，約 23 天未察覺。

**根本原因**：GitHub Token 過期導致 Vercel API 呼叫 GitHub Actions 失敗。

**解決方案**：
1. 更新 Vercel 環境變數中的 `GITHUB_TOKEN`
2. 確認 Vercel Cron 仍無法自動觸發（平台問題）
3. **改用 cron-job.org 作為定時觸發器**

**新架構**：
```
cron-job.org (每 5 分鐘)
    ↓
Vercel API (/api/trigger-monitor)
    ↓
GitHub Actions (workflow_dispatch)
    ↓
Python Scraper → 資料更新
```

**監控機制**：cron-job.org 內建失敗 Email 通知

---

### 🏷️ 分類邏輯修復

**問題**：非停駛公告被誤判為 `Disruption_Update`。

**案例**：「臺鐵海風號與山嵐號觀光列車 榮獲2025金點設計大獎」

**根本原因**：
- `announcement_classifier.py` 將標題與內容合併後進行關鍵字匹配
- 內容中「持續優化設計」觸發了「持續」關鍵字

**解決方案**：實作「標題優先」兩層分類架構

```python
# 第一層：檢查標題是否包含停駛相關詞
disruption_indicators = ['停駛', '暫停', '中斷', '延誤', '故障', ...]

if not any(word in title for word in disruption_indicators):
    # 標題無停駛詞 → 直接分為 General_Operation
    return Classification(category="General_Operation", ...)

# 第二層：原有關鍵字匹配（只有標題含停駛詞才進入）
```

**修改檔案**：
- `src/classifiers/announcement_classifier.py`
- `config/keywords.yaml`（還原「持續」關鍵字）

**結果**：重新分類 181 筆公告，修正 31 筆誤判

---

### 🎨 Dashboard Badge 修復

**問題**：`Disruption_Resumption`（恢復通車公告）顯示紅色 badge，應為綠色。

**根本原因**：Badge 邏輯先檢查 `Disruption`，後檢查 `Resumption`

**解決方案**：調整檢查順序，先檢查 `Resumption`

**修改檔案**：`docs/index.html`

**結果**：

| 分類 | 修復前 | 修復後 |
|------|-------|-------|
| `Disruption_Resumption` | 🔴 紅色 | 🟢 綠色 |

---

### 📊 今日修復統計

| 項目 | 數量 |
|------|------|
| 修復 Bug 數 | 3 |
| 修改檔案數 | 4 |
| 重新分類公告 | 31 筆 |
| Git Commits | 4 |

---

## [2025-11-26] 系統停機（未察覺）

**事件**：GitHub Token 過期，系統停止自動執行。

**發現日期**：2025-12-19（由林教授發現）

**停機時間**：約 23 天

---

## [2025-11-08] Vercel Cron 測試失敗，改用本地 Cron

**事件**：Vercel Cron 配置正確但不自動觸發。

**解決方案**：暫時使用本地 macOS crontab 觸發 GitHub Actions。

**詳細報告**：`VERCEL_CRON_FINAL_REPORT.md`

---

## [2025-10-24] 時間提取準確度達 100%

**事件**：完成 7+ 輪測試，時間提取 Precision 與 Recall 均達 100%。

**詳細報告**：`data/PERFORMANCE_REPORT.md`、`TESTING_HISTORY.md`

---

## [2025-10-21] 專案啟動

**事件**：開始開發台鐵公告監控系統。

**目的**：追蹤危機溝通演變模式（林教授研究）
