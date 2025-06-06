# Notion RAG

將 Notion 資料轉換為 RAG 智慧型問答系統 | Convert Notion content into intelligent Q&A system

## 🚀 專案簡介

這是一個基於 Python 的智慧型問答工具，專門用於將 Notion 內容轉換為檢索增強生成（RAG）系統。工具能夠智慧地理解和回答關於你的 Notion 文件內容的問題，支援繁體中文介面與自然語言問答。

### ✨ 主要功能
- 🔄 **即時同步** Notion 頁面內容
- 🧠 **智慧問答** 基於你的文件內容提供準確回答
- 🌐 **網頁介面** 美觀易用的 Streamlit 前端
- 🇹🇼 **繁體中文** 完整支援台灣用語
- 🔍 **語義搜尋** 智慧理解問題意圖
- 🤖 **OpenAI 整合** 使用 GPT 模型生成高品質回答

## 📁 專案結構

```
notion-rag/
├── config/                     # 設定檔案目錄
│   ├── __init__.py
│   ├── settings.py            # 系統設定管理
│   └── .env                   # 環境變數設定 (需自行建立)
├── core/                       # 核心功能模組
│   ├── __init__.py
│   ├── embedder.py            # 文字向量化處理
│   ├── notion_client.py       # Notion API 客戶端
│   ├── rag_engine.py          # RAG 引擎核心
│   ├── text_processor.py      # 文字處理工具
│   └── vector_store.py        # 向量儲存管理
├── .gitignore                  # Git 忽略檔案清單
├── app.py                      # Streamlit 網頁應用程式
├── main.py                     # 命令列主程式
├── requirements.txt            # 套件相依清單
├── vector_db/                  # 向量資料庫檔案 (自動生成)
```

## 🔧 模組說明

### 核心模組

#### 1. **向量嵌入器** (`core/embedder.py`)
- 🤖 使用多語言 Sentence Transformers 模型
- ⚡ 支援批次處理提升效率
- 📏 384 維度向量嵌入
- 🔄 自動快取機制

#### 2. **Notion 客戶端** (`core/notion_client.py`)
- 🔗 Notion API 串接與認證
- 📄 頁面內容提取與解析
- 🔄 支援分頁載入大型文件
- 📝 處理各種 Notion 區塊類型（標題、段落、清單等）

#### 3. **RAG 引擎** (`core/rag_engine.py`)
- 🧠 整合所有組件的核心引擎
- 🤖 OpenAI GPT 模型整合
- 💬 智慧上下文組裝
- 🎯 回答品質最佳化

#### 4. **文字處理器** (`core/text_processor.py`)
- ✂️ 智慧文字分割，保持語義完整性
- 🧹 文字清理與格式化
- 📊 支援重疊分割提升檢索品質
- 🇹🇼 針對中文文本最佳化

#### 5. **向量儲存庫** (`core/vector_store.py`)
- 💾 使用 FAISS 進行高效向量搜尋
- 🗄️ SQLite 儲存元資料
- 🔍 餘弦相似度搜尋
- 📊 支援相似度閾值過濾

### 設定管理

#### **系統設定** (`config/settings.py`)
- 🔧 環境變數管理
- 📋 預設值設定
- 🔒 API 金鑰安全處理
- 🔄 支援完整 Notion URL 解析

## 🛠️ 安裝與設定

### 1. 環境需求
- Python 3.8 或更新版本
- 8GB+ RAM（推薦用於模型載入）
- 2GB+ 可用磁碟空間

### 2. 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/andiran/Notion-Rag.git
cd Notion-Rag

# 2. 建立虛擬環境 (推薦)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 建立設定檔
mkdir -p config
touch config/.env
```

### 3. 設定 Notion API

1. **建立 Notion Integration**：
   - 前往 [Notion Developers](https://www.notion.so/my-integrations)
   - 點選「New integration」
   - 填入名稱（例如：RAG Integration）
   - 選擇權限：**Read content**
   - 複製 **Integration Token**

2. **連接頁面到 Integration (使用 Connection)**：
   - 開啟你的 Notion 頁面
   - 點選右上角的「⋯」選單
   - 選擇「Connections」
   - 點選「Add connections」
   - 搜尋並選擇你剛建立的 Integration
   - 確認連接並給予「Read」權限

3. **獲取頁面 ID**：
   - 從頁面 URL 複製完整網址
   - 或提取 32 字元的頁面 ID

### 4. 環境變數設定

在 `config/.env` 檔案中加入：

```bash
# Notion API 設定
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=https://www.notion.so/your-workspace/page-title-32字元ID

# OpenAI API 設定 (可選)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
USE_OPENAI=true

# 系統參數 (可選，有預設值)
CHUNK_SIZE=500
CHUNK_OVERLAP=50
SIMILARITY_THRESHOLD=0.3
TOP_K=5
```

## 🚀 使用方式

### 網頁版 (推薦)

```bash
# 啟動 Streamlit 網頁應用
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`

**網頁功能：**
- 💬 即時問答對話介面
- 📊 系統狀態監控
- 🔄 一鍵更新 Notion 內容
- 💡 範例問題快速提問
- 📱 響應式設計，支援手機使用

### 命令列版

```bash
# 啟動命令列介面
python main.py
```

**命令列功能：**
- 📝 直接輸入問題進行問答
- `help` - 顯示使用說明
- `status` - 檢查系統狀態
- `update` - 更新 Notion 內容
- `quit` - 退出系統

## 💡 使用範例

### 旅遊行程管理
如果你的 Notion 頁面是旅遊行程：

```
問：這次旅行要去哪裡？
答：根據你的行程安排，這次旅行的目的地是...

問：航班資訊是什麼？
答：根據你的資料，航班安排如下...

問：住宿安排如何？
答：你預訂的住宿資訊包括...
```

### 專案管理
如果你的 Notion 頁面是專案文件：

```
問：這個專案的主要目標是什麼？
答：基於專案文件，主要目標包括...

問：專案時程如何安排？
答：根據時程表，專案分為以下階段...

問：團隊成員有哪些？
答：專案團隊包括...
```

### 學習筆記
如果你的 Notion 頁面是學習資料：

```
問：Python 的基本語法有哪些？
答：根據你的筆記，Python 基本語法包括...

問：這個概念的重點是什麼？
答：從你的學習資料來看，重點包括...

問：有沒有相關的練習題？
答：你的筆記中提到的練習包括...
```

### 會議記錄
如果你的 Notion 頁面是會議紀錄：

```
問：上次會議討論了什麼？
答：根據會議記錄，主要討論議題包括...

問：有哪些待辦事項？
答：會議中確認的行動項目有...

問：下次會議何時舉行？
答：根據記錄，下次會議安排在...
```

## ⚙️ 進階設定

### 模型選擇

```bash
# 使用不同的嵌入模型
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 調整向量維度 (需配合模型)
EMBEDDING_DIMENSION=384
```

### 效能調優

```bash
# 較大的 chunk 適合長文件
CHUNK_SIZE=800
CHUNK_OVERLAP=100

# 較低的相似度閾值會回傳更多結果
SIMILARITY_THRESHOLD=0.2

# 增加檢索的文檔數量
TOP_K=10
```

## 🚨 常見問題

### Notion API 問題

**Q: 出現 401 錯誤**
```
A: 檢查 NOTION_TOKEN 是否正確，確認 Integration 已建立
```

**Q: 出現 404 錯誤**
```
A: 確認頁面已透過 Connections 連接到 Integration，檢查頁面 ID 格式
   步驟：頁面選單 → Connections → Add connections → 選擇你的 Integration
```

**Q: Integration 找不到頁面**
```
A: 使用新版 Connections 功能而非舊版 Share：
   1. 開啟 Notion 頁面
   2. 點選右上角「⋯」選單
   3. 選擇「Connections」→「Add connections」
   4. 搜尋你的 Integration 名稱並連接
```

### OpenAI API 問題

**Q: OpenAI API 版本錯誤**
```bash
# 安裝正確版本
pip install openai>=1.0.0
```

**Q: API 金鑰無效**
```
A: 檢查 OPENAI_API_KEY 格式，確認帳戶有足夠額度
```

### 效能問題

**Q: 模型載入太慢**
```bash
# 設定快取目錄
export TRANSFORMERS_CACHE=/path/to/cache
```

**Q: 記憶體不足**
```bash
# 降低批次大小
BATCH_SIZE=16
```

---

⭐ 如果這個專案對你有幫助，歡迎給個星星支持！