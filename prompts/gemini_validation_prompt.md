# 台鐵公告資料品質驗證提示詞

你是一個資料品質分析專家。請仔細分析以下台鐵公告監測系統的 JSON 資料，並進行完整性驗證。

## 資料結構說明

```json
{
  "id": "公告編號",
  "title": "公告標題",
  "publish_date": "發布日期 (YYYY/MM/DD)",
  "detail_url": "詳細頁面連結",
  "classification": {
    "category": "分類類別",
    "keywords": ["匹配的關鍵字"],
    "event_group_id": "事件群組ID"
  },
  "version_history": [
    {
      "scraped_at": "抓取時間",
      "content_html": "HTML內容",
      "content_text": "純文字內容",
      "content_hash": "內容雜湊值",
      "extracted_data": {
        "predicted_resumption_time": "預計復駛時間",
        "actual_resumption_time": "實際復駛時間",
        "affected_lines": ["受影響路線"],
        "affected_stations": ["受影響車站"],
        "cause": "原因",
        "impact_description": "影響描述",
        "additional_info": "額外資訊"
      }
    }
  ]
}
```

## 驗證重點

### 1. 時間邏輯驗證
- **預計復駛時間 (predicted_resumption_time)** 必須在 **發布日期 (publish_date)** 之後或同日
- 如果 `predicted_resumption_time` 在 `publish_date` 之前，這是 BUG
- 檢查是否有復駛公告 (標題含"恢復"、"復駛") 但 `predicted_resumption_time` 為 null

### 2. 分類邏輯驗證
分類定義：
- `Disruption_Suspension`: 停駛公告（關鍵字：停駛、暫停）
- `Disruption_Resumption`: 復駛公告（關鍵字：恢復通車、恢復行駛、復駛）
- `Disruption_Update`: 營運異動（關鍵字：異動、調整、取消）
- `Weather_Related`: 天氣相關（關鍵字：颱風、豪雨、地震）
- `General_Operation`: 一般營運

檢查：
- 標題明確含「恢復通車」但分類不是 `Disruption_Resumption`
- 標題明確含「停駛」但分類不是 `Disruption_Suspension`
- 標題含「颱風」或「豪雨」但分類不是 `Weather_Related`

### 3. 資料完整性檢查
- `affected_lines` 或 `affected_stations` 應該有值（至少其中之一）
- `cause` 是否合理提取（停駛/復駛公告應該有原因）
- `content_text` 和 `content_html` 是否都存在

### 4. 異常案例識別
找出以下異常：
- 同一個 `event_group_id` 下有多則公告，但時間邏輯不連貫
- `predicted_resumption_time` 提取的時間看起來是「發布時間」而非「復駛時間」
- 分類為 `General_Operation` 但內容明顯是停駛/復駛公告

## 輸出格式要求

### 第一部分：整體統計
```
總公告數: X
分類分布:
  - Disruption_Resumption: X (Y%)
  - Disruption_Suspension: X (Y%)
  - Weather_Related: X (Y%)
  - Disruption_Update: X (Y%)
  - General_Operation: X (Y%)

包含預計復駛時間: X/Y (Z%)
包含實際復駛時間: X/Y (Z%)
```

### 第二部分：錯誤清單（重要！）

#### 時間邏輯錯誤
```
ID: 公告編號
標題: 標題
問題: predicted_resumption_time (YYYY-MM-DD HH:MM) 早於 publish_date (YYYY-MM-DD)
```

#### 分類錯誤
```
ID: 公告編號
標題: 標題
當前分類: XXX
建議分類: YYY
原因: 標題明確含有「恢復通車」關鍵字
```

#### 資料遺漏
```
ID: 公告編號
標題: 標題
問題: 應有 predicted_resumption_time 但為 null（標題含復駛關鍵字）
內文片段: [顯示相關內文]
```

### 第三部分：品質建議
列出 3-5 項最需要改進的點，按優先級排序。

## 開始分析

請將以下 JSON 資料貼到這個提示詞下方，我會進行完整分析。
