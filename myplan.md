# Taiwan Weather Forecast --- Antigravity 開發計畫

## 專案定位

本專案依照老師提供的「AI 創新微課程：Taiwan Weather
Forecast」流程，建立一個以中央氣象署（CWA）Open Data
為核心資料來源的全台天氣網站。

本版本將資料來源調整為：

**CWA O-A0003-001｜氣象觀測站－10分鐘綜觀氣象資料**

中央氣象署官方資料標準文件將 O-A0003-001
定義為「氣象觀測站-10分鐘綜觀氣象資料」。相較於原本規劃的預報資料，本資料集更適合做「全台即時／近期天氣觀測
Dashboard」，並可進一步延伸成觀測資料分析。 citeturn0search4

> 注意：CWA API Key 不得直接寫入本檔案、原始碼或 GitHub。實際 Key 應透過
> `.env` 的 `CWA_API_KEY` 管理。

核心資料流程：

``` text
CWA O-A0003-001
        ↓
Python / Requests
        ↓
JSON
        ↓
JSON Parser
        ↓
Data Validation
        ↓
SQLite
        ↓
SQL Query
        ↓
Streamlit
        ↓
全台天氣 Dashboard
        ├── 全台觀測地圖
        ├── 縣市天氣資訊
        ├── 溫度分析
        ├── 降雨／觀測資料
        └── 歷史觀測趨勢
```

------------------------------------------------------------------------

# 五大開發步驟

## Step 1｜CWA O-A0003-001 API 串接與全台觀測資料取得

### 目標

完成中央氣象署 O-A0003-001 API 串接，取得全台氣象站的 10
分鐘綜觀氣象觀測資料。

### 工作內容

-   建立 Antigravity 專案基本結構。
-   使用 Python `requests` 呼叫 CWA Open Data API。
-   Dataset 使用 `O-A0003-001`。
-   API Key 使用環境變數管理。
-   取得 JSON 格式資料。
-   解析氣象站基本資訊。
-   解析觀測時間。
-   解析可用的氣象觀測欄位。
-   建立 API 連線錯誤處理。
-   建立基本 Retry 機制。
-   記錄資料擷取時間。

### API Key 設計

`.env`

``` text
CWA_API_KEY=你的_CWA_API_KEY
```

程式：

``` python
import os

API_KEY = os.getenv("CWA_API_KEY")
```

`.gitignore` 必須包含：

``` text
.env
*.db
__pycache__/
```

### 重要資料概念

O-A0003-001 是「觀測資料」，因此網站中的文字應以：

-   即時天氣觀測
-   最新觀測
-   觀測時間
-   氣象站資料

為主。

不要把觀測資料誤稱為「CWA 官方預報」。

### 驗收條件

-   API 可以正常呼叫。
-   能取得 O-A0003-001 JSON。
-   能辨識不同氣象站。
-   能取得觀測時間。
-   能取得主要觀測欄位。
-   API Key 不會被 Git 追蹤。
-   API 失敗時網站不應直接崩潰。

------------------------------------------------------------------------

## Step 2｜JSON 解析、資料標準化與 SQLite

### 目標

將 CWA O-A0003-001 原始 JSON 轉換為適合分析的結構化資料，並儲存到
SQLite。

### 工作內容

-   建立 `weather_parser.py`。
-   解析 CWA JSON。
-   將氣象站資訊與觀測資訊拆分。
-   將數值欄位轉換為正確資料型態。
-   處理 CWA 缺值／異常值。
-   建立 SQLite Database。
-   建立氣象站資料表。
-   建立觀測資料表。
-   建立查詢 Index。
-   避免相同站點、相同觀測時間重複寫入。

### 建議資料庫

#### `weather_stations`

``` text
id
station_id
station_name
county
township
latitude
longitude
station_type
```

#### `weather_observations`

``` text
id
station_id
observation_time
temperature
relative_humidity
pressure
wind_speed
wind_direction
precipitation
weather
visibility
fetched_at
```

實際欄位必須以 O-A0003-001 API 回傳內容為準，不應自行假造不存在的欄位。

### 建議 Index

``` text
INDEX(station_id)
INDEX(observation_time)
INDEX(county)
```

### 驗收條件

-   JSON 可以正確解析。
-   SQLite 可以成功建立。
-   氣象站與觀測資料可以寫入。
-   可以依縣市查詢。
-   可以依氣象站查詢。
-   可以依觀測時間查詢。
-   缺值與異常值不會造成程式崩潰。

------------------------------------------------------------------------

## Step 3｜Streamlit 全台天氣 Dashboard

### 目標

建立主要 Web App，將 SQLite 的氣象觀測資料以容易理解的方式呈現。

### Dashboard 架構

``` text
Taiwan Weather Dashboard
│
├── 最新全台觀測概況
│
├── 縣市選擇
│
├── 氣象站資訊
│
├── 即時觀測數據
│
├── 溫度趨勢
│
└── 詳細資料表
```

### 第一區：全台觀測概況

顯示：

-   全台氣象站數量
-   最近一次資料更新時間
-   目前可取得資料的縣市
-   最新觀測時間

### 第二區：縣市選擇

``` text
請選擇縣市
[ 台中市 ▼ ]
```

選擇後顯示該縣市氣象站。

### 第三區：氣象觀測卡片

例如：

``` text
台中市

🌡️ 溫度：XX °C
💧 相對濕度：XX %
🌬️ 風速：XX m/s
🧭 風向：XX
🌧️ 降水量：XX mm
🕐 觀測時間：YYYY-MM-DD HH:MM
```

實際顯示項目必須依 API 回傳資料決定。

### 第四區：趨勢圖

從 SQLite 取得同一氣象站近期觀測資料，繪製：

-   溫度趨勢
-   濕度趨勢
-   風速趨勢
-   降水量趨勢

### 第五區：詳細資料表

顯示：

-   氣象站
-   縣市
-   觀測時間
-   溫度
-   濕度
-   風速
-   風向
-   降水量

### 驗收條件

-   Streamlit 可以正常啟動。
-   使用者可以選擇縣市。
-   可以選擇氣象站。
-   所有資料主要由 SQLite 提供。
-   圖表會依選擇的站點更新。
-   顯示最新觀測時間。
-   不把觀測資料誤標示為預報資料。

------------------------------------------------------------------------

## Step 4｜Folium 全台氣象站地圖與資料分析

### 目標

加入老師圖片中的 Folium + Streamlit
互動地圖，將全台氣象站的空間資訊視覺化。

### A. 台灣互動地圖

使用 Folium：

``` text
Taiwan Map
   ↓
氣象站 Marker
   ↓
點擊 Marker
   ↓
顯示最新觀測資料
```

Marker Popup 顯示：

``` text
氣象站名稱
縣市
最新觀測時間
溫度
濕度
風速
降水量
```

### B. 溫度空間分析

以目前最新觀測資料：

-   顯示各站溫度。
-   依溫度區間分類。
-   觀察北、中、南、東部的溫度差異。

### C. 時間序列分析

選擇氣象站後：

``` text
最近 6 小時
最近 12 小時
最近 24 小時
```

分析：

-   溫度變化
-   濕度變化
-   風速變化
-   降水變化

實際時間範圍依資料庫目前累積資料量決定。

### D. 基本統計

可計算：

``` text
平均溫度
最高觀測溫度
最低觀測溫度
平均濕度
平均風速
累積降水量
```

所有統計必須由實際 SQLite 資料計算，不可手動填入。

### 驗收條件

-   Folium 地圖可以正常顯示。
-   氣象站位置正確。
-   Marker 可以顯示觀測資訊。
-   地圖資料與 SQLite 查詢結果一致。
-   趨勢圖與地圖使用相同資料來源。
-   統計結果可以由資料重新計算。

------------------------------------------------------------------------

## Step 5｜測試、程式優化、GitHub 與成果展示

### 目標

將系統整理成可以提交、展示與說明的完整專案。

### 建議專案架構

``` text
Taiwan-Weather-Dashboard/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── database/
│   └── weather.db
│
├── services/
│   ├── cwa_api.py
│   ├── weather_parser.py
│   ├── database.py
│   └── weather_service.py
│
├── components/
│   ├── weather_cards.py
│   ├── charts.py
│   └── weather_map.py
│
├── data/
│   └── sample.json
│
└── tests/
    ├── test_api.py
    ├── test_parser.py
    └── test_database.py
```

### 錯誤處理

必須處理：

-   API Key 不存在
-   API 連線失敗
-   API 回傳錯誤
-   JSON 格式異常
-   CWA 欄位缺值
-   SQLite 無資料
-   查詢不到氣象站
-   網路中斷
-   Streamlit 元件錯誤

### 測試

至少測試：

-   CWA API 連線
-   JSON Parser
-   缺值處理
-   SQLite 寫入
-   SQL 查詢
-   溫度統計
-   趨勢資料
-   地圖資料
-   Streamlit 啟動
-   API 失敗情境

### GitHub

-   建立 Repository。
-   `.env` 不得上傳。
-   API Key 不得出現在程式碼。
-   `.env.example` 提供欄位名稱即可。
-   撰寫 README。
-   說明資料來源。
-   說明系統架構。
-   說明安裝方式。
-   說明執行方式。
-   說明 Dashboard 功能。

### 最終展示資料流

``` text
CWA O-A0003-001
        ↓
Python Requests
        ↓
JSON
        ↓
JSON Parser
        ↓
Data Validation
        ↓
SQLite
        ↓
SQL Query
        ↓
Streamlit
        ↓
┌──────────────────────────┐
│ Taiwan Weather Dashboard │
├──────────────────────────┤
│ 全台最新觀測             │
│ 縣市／氣象站選擇         │
│ 溫度／濕度／風速         │
│ 趨勢分析                 │
│ Folium 全台地圖          │
│ 資料表格                 │
└──────────────────────────┘
```

------------------------------------------------------------------------

# Antigravity 執行規則

請嚴格按照以下順序：

**Step 1 → Step 2 → Step 3 → Step 4 → Step 5**

每完成一個 Step：

1.  先執行程式。
2.  實際測試功能。
3.  檢查錯誤。
4.  修正錯誤。
5.  確認既有功能沒有被破壞。
6.  再進入下一個 Step。

不要一次跳過多個 Step。

不要在核心資料流程尚未驗證前加入大量額外功能。

如果 CWA API 實際回傳欄位與本計畫假設不同，**以 O-A0003-001 實際 API
Schema 為準**，並同步更新 Parser、SQLite Schema 與 Dashboard。

------------------------------------------------------------------------

# 最終專案目標

建立：

**Taiwan Weather Dashboard**

以 CWA O-A0003-001 的 10 分鐘綜觀氣象觀測資料為核心，整合：

-   CWA Open Data API
-   Python Requests
-   JSON Parsing
-   Data Validation
-   SQLite
-   SQL
-   Streamlit
-   Folium
-   時間序列分析
-   空間資料視覺化
-   GitHub

形成完整的：

**「公開氣象資料 → 資料處理 → 資料庫 → 分析 → Web Dashboard」**

資料分析與 IoT 應用流程。
