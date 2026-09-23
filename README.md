# 🇹🇼 Taiwan Weather Forecast Dashboard (全台天氣預報與即時觀測系統)

本專案遵循 `myplan.md` 開發規範，建立一個結合中央氣象署 (CWA) Open Data API、SQLite 資料庫、Streamlit Web Dashboard 與 Folium 互動地圖的全台天氣系統。

---

## 🌟 系統特色與核心架構

本系統涵蓋完整的資料處理與展示流程：

```text
中央氣象署 CWA Open Data API (O-A0003-001 / F-C0032-001)
                    │
                    ▼
          requests (自動重試 + TLS / Fallback)
                    │
                    ▼
         JSON Parser (weather_parser.py)
                    │
                    ▼
          SQLite Database (database/weather.db)
                    │
                    ▼
          Weather Service (weather_service.py)
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   Streamlit UI   Plotly圖表  Folium地圖 (363測站)
```

1. **CWA API 串接 (`O-A0003-001` & `F-C0032-001`)**
   - 支援自動氣象站實測資料 (`O-A0003-001`) 與今明 36 小時天氣預報 (`F-C0032-001`)。
   - 使用 `.env` 安全管理 API Key，不上傳私密資料。
   - 包含離線備份資料庫 (`data/sample.json`)，無網路或 API Key 遺失時自動降級備用。

2. **JSON 資料結構化與 SQLite 資料庫**
   - 建立 `forecast_records` 與 `observation_records` 資料表。
   - 自動去重與建立 `city` / `start_time` / `obs_time` 索引，避免無上限重複數據。

3. **Streamlit 互動視覺化 Dashboard**
   - **全台觀測概況與縣市卡片**：即時顯示高溫、低溫、累積雨量、舒適度與天氣現象。
   - **溫度趨勢折線圖**：Plotly 呈現 36 小時最高溫與最低溫變化趨勢。
   - **縣市氣象資料查詢**：選單自由切換 22 縣市。

4. **Folium 台灣互動天氣地圖**
   - 全台 363 個氣象測站 Marker 標記。
   - 依據雨量與氣溫自動呈現動態顏色與圖示。
   - 點擊氣象站可開啟 Popup 查看即時氣溫、日高/低溫、相對濕度與氣象描述。

5. **資料分析與規則分類**
   - 日夜溫差計算 (`溫差 = 最高溫 - 最低溫`)。
   - 降雨機率規則化分類 (`<30% 低降雨`, `30%~60% 中降雨`, `>=60% 高降雨`)。

---

## 📁 專案檔案結構

```text
HW1/
├── app.py                      # Streamlit Web App 主程式
├── config.py                   # 系統與 API 相關組態設定
├── requirements.txt            # Python 套件相依清單
├── README.md                   # 本說明文件
├── myplan.md                   # 課程開發計畫需求
├── .env                        # API Key 環境變數 (Git 排除)
├── .env.example                # API Key 範本
├── .gitignore                  # Git 忽略設定
│
├── database/
│   └── weather.db              # SQLite 資料庫儲存檔
│
├── services/
│   ├── cwa_api.py              # CWA API 請求與 Retry 模組
│   ├── weather_parser.py       # CWA JSON 解析與正規化
│   ├── database.py             # SQLite CRUD 與 Table 索引管理
│   └── weather_service.py      # 業務邏輯與氣象分析服務
│
├── components/
│   ├── weather_cards.py        # Streamlit 氣象卡片與指標
│   ├── charts.py               # Plotly 趨勢圖與縣市比較圖
│   └── weather_map.py          # Folium 台灣互動地圖
│
├── data/
│   └── sample.json             # 離線備用氣象 JSON 數據
│
└── tests/
    └── test_weather_pipeline.py# 單元測試套件 (API/Parser/DB/Service)
```

---

## 🚀 快速開始與執行方式

### 1. 安裝套件相依
建議使用 Python 3.10+ 環境：

```bash
pip install -r requirements.txt
```

### 2. 設定 API Key
將 `.env.example` 複製為 `.env` 並填入您的中央氣象署 API Key：

```env
CWA_API_KEY=YOUR_CWA_API_KEY
```

### 3. 執行單元測試
驗證 API 串接、JSON 解析、SQLite 寫入與氣象分析邏輯：

```bash
python -m unittest discover tests
```

### 4. 啟動 Streamlit Dashboard 網站

```bash
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`。

---

## 🧪 自動化測試結果

執行 `python -m unittest discover tests` 輸出：
- `test_01_api_fetch`: API 連線與數據取得測試 🟢
- `test_02_json_parsing`: CWA JSON 結構轉換測試 🟢
- `test_03_sqlite_database_crud`: SQLite CRUD 與去重機制測試 🟢
- `test_04_pop_classification`: 降雨機率規則分類測試 🟢
- `test_05_service_sync`: 全流程同步與分析計算測試 🟢

**Ran 5 tests: OK**
