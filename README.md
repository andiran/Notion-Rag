# Notion RAG

將 Notion 資料轉換為 RAG 智慧問答系統 | Convert Notion content into intelligent Q&A system

## 🚀 專案簡介

這是一個基於 Python 的智慧問答工具，專門用於將 Notion 內容轉換為檢索增強生成（RAG）系統。工具能夠智慧地理解和回答關於您的 Notion 文件內容的問題，支援繁體中文介面與自然語言問答。

### ✨ 主要功能
- 🔄 **即時同步** Notion 頁面內容
- 🧠 **智慧問答** 基於您的文件內容提供準確回答
- 🌐 **網頁介面** 美觀易用的 Streamlit 前端
- 🇹🇼 **繁體中文** 完整支援台灣用語
- 🔍 **智慧語意搜尋** 結合語意理解和關鍵字比對
- 🤖 **OpenAI 整合** 使用 GPT 模型產生高品質回答
- 📊 **查詢意圖理解** 自動分析問題類型並最佳化搜尋策略
- ⚡ **快取機制** 加速模型載入和回應速度

## 📁 專案結構

```
notion-rag/
├── config/                     # 設定檔案目錄
│   ├── settings.py            # 系統設定管理
│   └── .env                   # 環境變數設定 (需自行建立)
├── core/                       # 核心功能模組
│   ├── __init__.py
│   ├── embedder.py            # 文字向量化處理
│   ├── notion_client.py       # Notion API 客戶端
│   ├── rag_engine.py          # RAG 引擎核心
│   ├── text_processor.py      # 文字處理工具
│   ├── vector_store.py        # 向量儲存管理
│   └── query_processor.py     # 查詢處理與意圖理解
├── cache/                      # 模型快取目錄 (自動產生)
├── vector_db                   # FAISS 向量索引檔案 (自動產生)
├── .gitignore                  # Git 忽略檔案清單
├── app.py                      # Streamlit 網頁應用程式
├── main.py                     # 命令列主程式
├── requirements.txt            # 套件相依清單
├── metadata.db                 # SQLite 詮釋資料庫 (自動產生)
└── README.md                   # 專案說明文件
```

## 🔧 模組說明

### 核心模組

#### 1. **向量嵌入器** (`core/embedder.py`)
- 🤖 使用多語言 Sentence Transformers 模型
- ⚡ 支援批次處理提升效率
- 📏 384 維度向量嵌入
- 🔄 自動快取機制避免重複計算

#### 2. **Notion 客戶端** (`core/notion_client.py`)
- 🔗 Notion API 串接與認證
- 📄 頁面內容擷取與解析
- 🔄 支援分頁載入大型文件
- 📝 處理各種 Notion 區塊類型（標題、段落、清單等）

#### 3. **RAG 引擎** (`core/rag_engine.py`)
- 🧠 整合所有元件的核心引擎
- 🤖 OpenAI GPT 模型整合
- 💬 智慧上下文組裝
- 🎯 回答品質最佳化
- 📊 系統狀態監控

#### 4. **文字處理器** (`core/text_processor.py`)
- ✂️ 智慧文字分割，保持語意完整性
- 🧹 文字清理與格式化
- 📊 支援重疊分割提升檢索品質
- 🇹🇼 針對中文文字最佳化
- 📋 支援多種文件格式處理

#### 5. **向量儲存庫** (`core/vector_store.py`)
- 💾 使用 FAISS 進行高效向量搜尋
- 🗄️ SQLite 儲存詮釋資料
- 🔍 餘弦相似度搜尋
- 📊 支援相似度門檻過濾
- 🔄 增量更新功能

#### 6. **查詢處理器** (`core/query_processor.py`)
- 🎯 智慧查詢意圖理解
- 🔤 自動錯字修正與查詢重寫
- 🏷️ 實體識別（時間、地點、人物等）
- ⚖️ 語意搜尋與關鍵字搜尋權重配置
- 🌐 中英混用查詢處理

### 設定管理

#### **系統設定** (`config/settings.py`)
- 🔧 環境變數管理
- 📋 預設值設定
- 🔒 API 金鑰安全處理
- 🔄 支援完整 Notion URL 解析
- 📊 彈性參數調整

## 🛠️ 安裝與設定

### 1. 環境需求
- Python 3.8 或更新版本
- 8GB+ RAM（建議用於模型載入）
- 2GB+ 可用磁碟空間
- 穩定的網路連線（用於 API 呼叫）

### 2. 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/andiran/Notion-Rag.git
cd Notion-Rag

# 2. 建立虛擬環境 (建議)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 3. 安裝相依套件
pip install -r requirements.txt
```

#### 相依套件說明
- `requests` - HTTP 請求處理
- `sentence-transformers` - 多語言文字向量化（包含 transformers 依賴）
- `faiss-cpu` - 高效向量搜尋
- `numpy` - 數值計算
- `python-dotenv` - 環境變數管理
- `openai` - OpenAI API 整合
- `torch` - 深度學習框架與 GPU 支援
- `streamlit` - 網頁介面框架

### 3. 設定 Notion API

1. **建立 Notion Integration**：
   - 前往 [Notion Developers](https://www.notion.so/my-integrations)
   - 點選「New integration」
   - 填入名稱（例如：RAG Integration）
   - 選擇權限：**Read content**
   - 複製 **Integration Token**

2. **連接頁面到 Integration (使用 Connection)**：
   - 開啟您的 Notion 頁面
   - 點選右上角的「⋯」選單
   - 選擇「Connections」
   - 點選「Add connections」
   - 搜尋並選擇您剛建立的 Integration
   - 確認連接並給予「Read」權限

3. **取得頁面 ID**：
   - 從頁面 URL 複製完整網址
   - 或擷取 32 字元的頁面 ID

### 4. 環境變數設定

建立 `config/.env` 檔案並加入以下設定：

```bash
# === 必要設定 ===
# Notion API 設定
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=https://www.notion.so/your-workspace/page-title-32字元ID

# === 可選設定 (有預設值) ===
# OpenAI API 設定
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
USE_OPENAI=true

# 向量嵌入設定
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384

# 文字處理設定
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# 搜尋設定
SIMILARITY_THRESHOLD=0.7
TOP_K=5

# 檔案路徑設定
VECTOR_DB_PATH=./vector_db
METADATA_DB_PATH=./metadata.db
CACHE_PATH=./cache

# 更新設定
UPDATE_INTERVAL=3600
```

## 🚀 使用方式

### 網頁版 (建議)

```bash
# 啟動 Streamlit 網頁應用
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`

**網頁功能：**
- 💬 **即時問答對話介面** - 支援連續對話
- 📊 **系統狀態監控** - 即時顯示資料庫和系統狀態
- 🔄 **一鍵更新** Notion 內容
- 💡 **範例問題** 快速提問
- 📱 **響應式設計** - 支援手機和平板使用
- 🎨 **美觀界面** - 漸變色彩和現代化設計
- ⚙️ **側邊控制面板** - 系統管理功能

### 命令列版

```bash
# 啟動命令列介面
python main.py
```

**命令列功能：**
- 📝 **直接問答** - 輸入問題立即獲得回答
- `help` 或 `?` - 顯示使用說明
- `status` - 檢查系統狀態和統計資訊
- `update` - 手動更新 Notion 內容
- `quit` 或 `exit` - 退出系統

**系統橫幅範例：**
```
============================================================
🤖 Notion RAG 智慧問答系統
============================================================
基於您的Notion文件內容，提供智慧問答服務
支援繁體中文，使用OpenAI GPT進行回答生成
============================================================
```

## 💡 使用範例

### 旅遊行程管理
如果您的 Notion 頁面是旅遊行程：

```
問：這次旅行要去哪裡？
答：根據您的行程安排，這次旅行的目的地是日本東京，預定停留7天6夜...

問：航班資訊是什麼？
答：根據您的資料，航班安排如下：
- 去程：10月15日 TPE → NRT，長榮航空 BR198
- 回程：10月22日 NRT → TPE，長榮航空 BR197

問：住宿安排如何？
答：您預訂的住宿資訊包括：
- 新宿王子大飯店（10/15-10/18，3晚）
- 淺草VIEW飯店（10/18-10/21，3晚）
```

### 專案管理
如果您的 Notion 頁面是專案文件：

```
問：這個專案的主要目標是什麼？
答：基於專案文件，主要目標包括：
1. 開發智慧客服系統
2. 提升客戶滿意度至90%以上
3. 降低人工服務成本30%

問：專案時程如何安排？
答：根據時程表，專案分為以下階段：
- 第一階段：需求分析（2週）
- 第二階段：系統設計（3週）
- 第三階段：開發實作（8週）
- 第四階段：測試部署（2週）

問：團隊成員有哪些？
答：專案團隊包括：
- 專案經理：王小明
- 系統架構師：李小華
- 前端工程師：張小美
- 後端工程師：陳小強
```

### 學習筆記
如果您的 Notion 頁面是學習資料：

```
問：Python 的基本語法有哪些？
答：根據您的筆記，Python 基本語法包括：
1. 變數宣告：name = "Hello"
2. 條件判斷：if, elif, else
3. 迴圈結構：for, while
4. 函數定義：def function_name():

問：這個概念的重點是什麼？
答：從您的學習資料來看，機器學習的重點包括：
- 資料預處理的重要性
- 特徵工程技巧
- 模型選擇與評估
- 過度配適的預防

問：有沒有相關的練習題？
答：您的筆記中提到的練習包括：
1. 線性迴歸預測房價
2. 分類演算法識別手寫數字
3. 聚類分析客戶分群
```

### 會議記錄
如果您的 Notion 頁面是會議紀錄：

```
問：上次會議討論了什麼？
答：根據會議記錄，主要討論議題包括：
1. Q3財務報告檢討
2. 新產品上市策略
3. 人力資源配置調整
4. 下季度預算規劃

問：有哪些待辦事項？
答：會議中確認的行動項目有：
- 完成市場調研報告（負責人：行銷部，期限：10/31）
- 準備產品原型展示（負責人：研發部，期限：11/15）
- 提交預算提案（負責人：財務部，期限：11/30）

問：下次會議何時舉行？
答：根據記錄，下次會議安排在11月8日下午2:00，地點在3樓會議室
```

## ⚙️ 進階設定

### 模型調整

```bash
# 使用不同的嵌入模型（更好的中文支援）
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 使用更大的模型（需要更多記憶體但效果更好）
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_DIMENSION=768

# 使用OpenAI的嵌入模型（需要API費用）
EMBEDDING_MODEL=text-embedding-ada-002
```

### 文字處理調優

```bash
# 適用於長文件的設定
CHUNK_SIZE=800
CHUNK_OVERLAP=100

# 適用於短文件的設定
CHUNK_SIZE=300
CHUNK_OVERLAP=30

# 提高檢索精確度
SIMILARITY_THRESHOLD=0.8
TOP_K=3

# 提高檢索覆蓋率
SIMILARITY_THRESHOLD=0.5
TOP_K=10
```

### 查詢處理最佳化

系統會根據問題類型自動調整搜尋策略：

- **概念性問題**：語意搜尋權重 80%，關鍵字搜尋 20%
- **事實性問題**：語意搜尋權重 70%，關鍵字搜尋 30%
- **時間/地點問題**：語意搜尋權重 50%，關鍵字搜尋 50%

## 🚨 常見問題

### Notion API 問題

**Q: 出現 401 未授權錯誤**
```
A: 請檢查以下項目：
1. NOTION_TOKEN 是否正確設定
2. Integration 是否已正確建立
3. Token 是否已過期（需重新產生）
```

**Q: 出現 404 找不到頁面錯誤**
```
A: 確認頁面已透過 Connections 連接到 Integration：
步驟：頁面選單 → Connections → Add connections → 選擇您的 Integration
注意：新版 Notion 使用 Connections，不是舊版的 Share 功能
```

**Q: Integration 找不到頁面內容**
```
A: 使用新版 Connections 功能：
1. 開啟 Notion 頁面
2. 點選右上角「⋯」選單
3. 選擇「Connections」→「Add connections」
4. 搜尋您的 Integration 名稱並連接
5. 確保給予「Read content」權限
```

### OpenAI API 問題

**Q: OpenAI API 版本相容性錯誤**
```bash
# 確保安裝正確版本
pip install openai>=1.3.0
```

**Q: API 金鑰無效或額度不足**
```
A: 請檢查：
1. OPENAI_API_KEY 格式是否正確
2. 帳戶是否有足夠的使用額度
3. API 金鑰是否有正確的權限設定
```

**Q: 不使用 OpenAI 的設定**
```bash
# 在 .env 檔案中設定
USE_OPENAI=false
# 系統會使用內建的規則式查詢分析
```

### 效能最佳化

**Q: 模型載入速度太慢**
```bash
# 設定快取目錄加速後續載入
export TRANSFORMERS_CACHE=/path/to/cache
CACHE_PATH=./cache
```

**Q: 記憶體使用量過高**
```bash
# 降低批次處理大小
BATCH_SIZE=8

# 使用較小的模型
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

**Q: 搜尋回應速度慢**
```bash
# 降低檢索文件數量
TOP_K=3

# 提高相似度門檻
SIMILARITY_THRESHOLD=0.8
```

### 系統維護

**Q: 如何更新 Notion 內容？**
```
A: 三種方式：
1. 在網頁版點選「更新Notion內容」按鈕
2. 在命令列輸入 'update' 指令
3. 系統會根據 UPDATE_INTERVAL 設定自動更新
```

**Q: 如何清理快取和重置系統？**
```bash
# 刪除向量資料庫和快取
rm -rf vector_db/ cache/ metadata.db

# 重新啟動系統會自動重建
```

**Q: 如何備份資料？**
```bash
# 備份重要檔案
cp -r vector_db/ backup/
cp metadata.db backup/
cp config/.env backup/
```

## 📊 系統監控

使用 `status` 指令可以查看詳細的系統狀態：

```
📊 系統狀態:
  📚 向量資料庫:
    - 文檔數量: 1,234
    - 向量數量: 1,234
    - 資料來源: ['notion_page_xxx']

  🤖 AI設定:
    - OpenAI: 啟用
    - 模型: gpt-3.5-turbo
    - 嵌入模型: paraphrase-multilingual-MiniLM-L12-v2

  ⚙️ 系統參數:
    - CHUNK_SIZE: 500
    - TOP_K: 5
    - SIMILARITY_THRESHOLD: 0.7
```

## 🔄 版本更新

定期檢查專案更新：

```bash
# 檢查遠端更新
git fetch origin main

# 更新到最新版本
git pull origin main

# 更新套件依賴
pip install -r requirements.txt --upgrade
```

---

⭐ 如果這個專案對您有幫助，歡迎給個星星支持！
