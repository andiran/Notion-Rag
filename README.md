# Notion RAG 智慧問答系統

將 Notion 資料轉換為 RAG 智慧問答系統 | 基於台灣繁體中文最佳化的智慧問答平台

## 🚀 專案簡介

這是一個專為台灣使用者設計的智慧問答工具，能夠將您的 Notion 內容轉換為功能強大的檢索增強生成（RAG）系統。本系統支援多種使用方式，包括網頁版、命令列版以及 LINE Bot，讓您能隨時隨地查詢您的 Notion 文件內容。

### ✨ 主要功能
- 🔄 **即時同步** Notion 頁面內容
- 🧠 **智慧問答** 基於您的文件內容提供準確回答
- 🌐 **多介面支援** Streamlit 網頁版、命令列版、LINE Bot 三種使用方式
- 🇹🇼 **繁體中文最佳化** 完整支援台灣用語和語法
- 🔍 **混合搜尋引擎** 結合語意理解和關鍵字比對的智慧搜尋
- 🤖 **OpenAI 整合** 使用 GPT 模型產生高品質自然語言回答
- 📊 **智慧查詢分析** 自動分析問題類型並最佳化搜尋策略
- ⚡ **高效能快取** 加速模型載入和回應速度
- 📱 **LINE Bot 支援** 透過 LINE 進行即時問答（使用最新 SDK v3）
- 🔒 **本地化部署** 資料安全，完全在本地運行

## 📁 專案架構

```
Notion-RAG/
├── 📂 config/                  # 設定檔案目錄
│   ├── settings.py            # 系統設定管理
│   └── .env                   # 環境變數設定 (需自行建立)
├── 📂 core/                    # 核心功能模組
│   ├── __init__.py
│   ├── embedder.py            # 文字向量化處理
│   ├── notion_client.py       # Notion API 客戶端
│   ├── rag_engine.py          # RAG 引擎核心
│   ├── text_processor.py      # 文字處理工具
│   ├── vector_store.py        # 向量儲存管理
│   └── query_processor.py     # 查詢處理與意圖理解
├── 📂 cache/                   # 模型快取目錄 (自動產生)
├── 📂 test/                    # 測試檔案目錄
├── 📄 vector_db                # FAISS 向量索引檔案 (自動產生)
├── 📄 metadata.db              # SQLite 詮釋資料庫 (自動產生)
├── 🌐 app.py                   # Streamlit 網頁應用程式  
├── 📱 linebot_app.py           # LINE Bot 應用程式 (SDK v3)
├── 💻 main.py                  # 命令列主程式
├── 📋 requirements.txt         # 套件相依清單
├── 🚫 .gitignore              # Git 忽略檔案清單
└── 📖 README.md               # 專案說明文件
```

## 🔧 核心模組說明

### 🤖 向量嵌入器 (core/embedder.py)
- **多語言支援**：使用 Sentence Transformers 模型，專為中文最佳化
- **批次處理**：支援大量文字的高效處理
- **向量維度**：預設 384 維度，平衡效能與準確度
- **智慧快取**：避免重複計算，提升處理速度

### 🔗 Notion 客戶端 (core/notion_client.py)
- **API 整合**：完整的 Notion API v2 支援
- **內容解析**：處理各種 Notion 區塊類型（標題、段落、清單、表格等）
- **分頁處理**：支援大型文件的自動分頁載入
- **錯誤處理**：完善的錯誤處理和重試機制

### 🧠 RAG 引擎 (core/rag_engine.py)
- **智慧整合**：統合所有元件的核心引擎
- **GPT 整合**：OpenAI GPT 模型深度整合
- **上下文組裝**：智慧組合相關內容提供精確回答
- **品質控制**：多重驗證確保回答品質
- **狀態監控**：即時監控系統運行狀態

### ✂️ 文字處理器 (core/text_processor.py)
- **智慧分割**：保持語意完整性的文字分割
- **中文最佳化**：針對繁體中文的特殊處理
- **重疊處理**：支援重疊分割提升檢索準確度
- **格式清理**：自動處理 Notion 格式標記
- **多格式支援**：支援多種文件格式解析

### 💾 向量儲存庫 (core/vector_store.py)
- **FAISS 引擎**：使用 Facebook AI 的高效向量搜尋引擎
- **SQLite 整合**：結合 SQLite 儲存文件詮釋資料
- **相似度搜尋**：餘弦相似度計算和門檻過濾
- **增量更新**：支援文件的新增、修改和刪除
- **索引最佳化**：智慧索引管理提升搜尋效能

### 🎯 查詢處理器 (core/query_processor.py)
- **意圖理解**：自動識別查詢意圖（事實性、概念性、時間性等）
- **實體識別**：提取時間、地點、人物等關鍵實體
- **查詢重寫**：自動錯字修正和查詢最佳化
- **權重配置**：根據查詢類型動態調整搜尋權重
- **中英混用**：完美處理中英文混合查詢

### ⚙️ 系統設定 (config/settings.py)
- **環境管理**：安全的環境變數處理
- **彈性設定**：支援多種參數調整
- **URL 解析**：智慧解析完整 Notion URL
- **預設配置**：合理的預設值設定

## 🛠️ 安裝與設定指南

### 📋 環境需求
- **Python 版本**：3.8 或更新版本
- **記憶體需求**：建議 8GB+ RAM（用於模型載入）
- **儲存空間**：至少 2GB 可用磁碟空間
- **網路環境**：穩定的網際網路連線（用於 API 呼叫）
- **作業系統**：支援 Windows、macOS、Linux

### 🔧 安裝步驟

#### 1. 取得專案原始碼
```bash
# 複製專案
git clone https://github.com/andiran/Notion-Rag.git
cd Notion-Rag
```

#### 2. 建立虛擬環境（強烈建議）
```bash
# 建立虛擬環境
python -m venv venvnotion

# 啟用虛擬環境
# macOS/Linux
source venvnotion/bin/activate

# Windows
venvnotion\Scripts\activate
```

#### 3. 安裝相依套件
```bash
# 安裝所有必要套件
pip install -r requirements.txt

# 若遇到安裝問題，可分別安裝
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 📦 相依套件說明

| 套件名稱 | 版本需求 | 用途說明 |
|---------|----------|----------|
| `requests` | ≥2.31.0 | HTTP 請求處理，用於 Notion API 呼叫 |
| `sentence-transformers` | ≥2.2.2 | 多語言文字向量化模型 |
| `faiss-cpu` | ≥1.7.4 | 高效向量相似度搜尋引擎 |
| `numpy` | ≥1.24.3 | 數值計算和陣列處理 |
| `python-dotenv` | ≥1.0.0 | 環境變數安全管理 |
| `openai` | ≥1.3.0 | OpenAI GPT API 整合 |
| `torch` | ≥2.0.0 | 深度學習框架與 GPU 支援 |
| `streamlit` | ≥1.28.0 | 網頁介面框架 |
| `line-bot-sdk` | ≥3.0.0 | LINE Bot SDK v3（最新版本） |
| `flask` | ≥2.3.0 | LINE Bot Web Server 框架 |

### 🔐 Notion API 設定

#### 1. 建立 Notion Integration
1. 前往 [Notion Developer Portal](https://www.notion.so/my-integrations)
2. 點選「**+ New integration**」
3. 填寫必要資訊：
   - **Name**：RAG 智慧問答系統（或您偏好的名稱）
   - **Associated workspace**：選擇您的工作區
   - **Type**：Internal
4. 在 **Capabilities** 中勾選：
   - ✅ **Read content**
   - ✅ **Read user information**（選用）
5. 點選「**Submit**」建立
6. 複製 **Internal Integration Token**（格式：`secret_xxxxxxxxx`）

#### 2. 連接頁面到 Integration
> ⚠️ **重要**：Notion 2023年後採用新的 Connections 機制，不再使用舊版的 Share 功能

1. 開啟您要使用的 Notion 頁面
2. 點選頁面右上角的「**⋯**」（更多選項）
3. 選擇「**Connections**」
4. 點選「**Add connections**」
5. 搜尋並選擇您剛建立的 Integration
6. 確認連接並給予適當權限

#### 3. 取得頁面 ID
**方法一：從 URL 取得（建議）**
```
完整 URL 範例：
https://www.notion.so/your-workspace/頁面標題-abc123def456...

頁面 ID 就是最後的 32 字元長度的字串
```

**方法二：使用完整 URL**
```
可直接使用完整的 Notion 頁面 URL
系統會自動解析出頁面 ID
```

### 🔑 環境變數設定

在專案根目錄建立 `config/.env` 檔案：

```bash
# 建立設定檔案
mkdir -p config
touch config/.env
```

將以下內容加入 `config/.env` 檔案：

```bash
# ========================================
# 必要設定（務必填寫）
# ========================================

# Notion API 設定
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=https://www.notion.so/your-workspace/page-title-32字元ID

# ========================================
# OpenAI 設定（選用）
# ========================================

# OpenAI API 金鑰（若要使用 GPT 生成回答）
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
USE_OPENAI=true

# ========================================
# LINE Bot 設定（選用）
# ========================================

# LINE Bot 設定（若要使用 LINE Bot 功能）
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token

# ========================================
# 進階設定（有預設值，可不填）
# ========================================

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

# 系統設定
UPDATE_INTERVAL=3600
```

### ✅ 設定驗證

```bash
# 驗證 Python 環境
python --version

# 驗證套件安裝
python -c "import sentence_transformers, faiss, openai, streamlit; print('✅ 所有套件安裝成功')"

# 驗證設定檔案
python -c "from config.settings import Settings; s=Settings(); print('✅ 設定檔案載入成功')"
```

## 🚀 使用方式

### 🌐 網頁版（推薦使用）

網頁版提供最完整的功能和最佳的資料瀏覽體驗：

```bash
# 啟動 Streamlit 網頁應用
streamlit run app.py

# 指定連接埠（若預設埠號被佔用）
streamlit run app.py --server.port 8502
```

瀏覽器會自動開啟 `http://localhost:8501`

#### 🎨 網頁版功能特色
- 💬 **即時問答介面**：支援連續對話，保持上下文
- 📊 **系統狀態儀表板**：即時顯示資料庫和系統狀態
- 🔄 **一鍵更新功能**：手動更新 Notion 內容
- 💡 **智慧提問建議**：提供範例問題快速開始
- 📱 **響應式設計**：完美支援手機、平板和桌機
- 🎨 **現代化 UI**：漸層色彩和直覺式操作介面
- ⚙️ **側邊管理面板**：系統管理和設定調整
- 📈 **查詢歷史記錄**：追蹤您的提問和回答

### 💻 命令列版

適合開發者和進階使用者：

```bash
# 啟動命令列介面
python main.py
```

#### 📝 命令列指令
- **直接提問**：輸入任何問題立即獲得回答
- `help` 或 `?`：顯示詳細使用說明
- `status`：檢查系統狀態和詳細統計資訊
- `update`：手動更新 Notion 內容
- `clear`：清空螢幕顯示
- `quit` 或 `exit`：優雅退出系統

#### 💫 系統啟動畫面
```
============================================================
🤖 Notion RAG 智慧問答系統 v2.0
============================================================
✅ 基於您的 Notion 文件內容，提供智慧問答服務
✅ 支援繁體中文，使用 OpenAI GPT 進行回答生成
✅ 系統已完成初始化，準備回答您的問題
============================================================
請輸入您的問題，或輸入 'help' 查看使用說明：
```

### 📱 LINE Bot 版

透過 LINE 隨時隨地進行問答：

```bash
# 啟動 LINE Bot 服務
python linebot_app.py

# 指定連接埠（預設 8080）
python linebot_app.py --port 8081
```

#### 🔧 LINE Bot 設定步驟

**1. 建立 LINE Developer Account**
- 前往 [LINE Developer Console](https://developers.line.biz/console/)
- 使用您的 LINE 帳號登入或註冊

**2. 建立 Messaging API Channel**
- 點選「Create」→「Provider」
- 輸入 Provider 名稱：`RAG 智慧問答`
- 點選「Create」→「Messaging API」
- 填寫 Channel 資訊：
  - **Channel name**：RAG 智慧問答機器人
  - **Channel description**：基於 Notion 內容的智慧問答助手
  - **Category**：選擇「工具」或相關分類

**3. 取得認證資訊**
- **Channel Secret**：在 Basic settings 頁面取得
- **Channel Access Token**：在 Messaging API 頁面點選 Issue 產生

**4. 設定 Webhook（使用 ngrok）**
```bash
# 安裝 ngrok（若尚未安裝）
# macOS: brew install ngrok
# Windows: 從 https://ngrok.com/download 下載

# 在新的終端視窗啟動 ngrok
ngrok http 8080
```

複製 ngrok 提供的 HTTPS URL（例如：`https://abc123.ngrok-free.app`）

**5. 設定 LINE Webhook URL**
- 回到 LINE Developer Console
- 進入 Messaging API 頁面
- 在 Webhook settings 中：
  - **Webhook URL**：`https://abc123.ngrok-free.app/callback`
  - 點選「Verify」驗證連線
  - 開啟「Use webhook」

**6. 關閉自動回覆**
- 在「LINE Official Account features」中
- 將「Auto-reply messages」設為 Disabled
- 將「Greeting messages」設為 Disabled（選用）

#### 📱 LINE Bot 使用範例
```
使用者：你好
機器人：您好！我是基於您的 Notion 文件的智慧問答助手。請問您想了解文件中的什麼內容呢？

使用者：這份文件的主要內容是什麼？
機器人：根據您的 Notion 文件內容分析...（基於實際內容的智慧回答）

使用者：有沒有關於專案時程的資訊？
機器人：根據文件中的專案資訊...（相關內容的摘要與分析）
```

## 💡 使用範例與應用場景

### 📝 專案管理應用
**適用場景**：專案文件、會議紀錄、任務追蹤

```
❓ 使用者提問：這個專案的主要里程碑有哪些？
🤖 智慧回答：根據您的專案文件，主要里程碑包括：
   1. 需求分析完成（第2週）
   2. 系統設計確認（第5週）  
   3. 原型開發完成（第10週）
   4. 測試階段開始（第12週）
   5. 正式上線部署（第16週）

❓ 使用者提問：目前專案進度如何？有什麼風險需要注意？
🤖 智慧回答：根據最新的專案狀態更新...
```

### 🎓 學習筆記管理
**適用場景**：課程筆記、研究資料、知識庫

```
❓ 使用者提問：機器學習的監督式學習有哪些演算法？
🤖 智慧回答：根據您的學習筆記，監督式學習主要包括：
   • 分類演算法：決策樹、隨機森林、SVM、神經網路
   • 迴歸演算法：線性迴歸、多項式迴歸、嶺回歸
   • 整體學習：AdaBoost、Gradient Boosting、XGBoost

❓ 使用者提問：深度學習和傳統機器學習的差異是什麼？
🤖 智慧回答：基於您的筆記整理...
```

### 🏖️ 旅遊行程規劃
**適用場景**：旅遊計畫、景點資訊、住宿安排

```
❓ 使用者提問：這次日本行程總共幾天？主要去哪些城市？
🤖 智慧回答：根據您的旅遊計畫，此次日本之旅為期8天7夜，
   主要造訪城市包括：
   • 東京（4天）：淺草、新宿、涉谷、台場
   • 京都（2天）：清水寺、金閣寺、嵐山
   • 大阪（2天）：大阪城、道頓堀、環球影城

❓ 使用者提問：住宿安排和預算如何？
🤖 智慧回答：住宿安排如下...
```

### 📊 企業知識庫
**適用場景**：公司政策、作業流程、FAQ

```
❓ 使用者提問：員工請假的申請流程是什麼？
🤖 智慧回答：根據公司政策文件，請假申請流程如下：
   1. 提前3天提出申請（緊急情況除外）
   2. 填寫線上請假表單
   3. 直屬主管審核批准
   4. 人資部門備查
   5. 系統自動更新出勤記錄

❓ 使用者提問：遠距工作的相關規定有哪些？
🤖 智慧回答：遠距工作政策規定...
```

### 🏥 會議記錄查詢
**適用場景**：會議紀錄、決議事項、行動計畫

```
❓ 使用者提問：上次董事會會議的主要決議有哪些？
🤖 智慧回答：根據董事會會議記錄，主要決議包括：
   • 批准2024年度預算案
   • 同意新產品線投資計畫
   • 核准人力資源擴編方案
   • 確認永續發展策略方向

❓ 使用者提問：有哪些待辦事項需要追蹤？
🤖 智慧回答：需要追蹤的行動項目包括...
```

## ⚙️ 進階設定與調優

### 🎛️ 模型選擇與調整

#### 嵌入模型選擇
```bash
# 中文最佳化模型（推薦）
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384

# 更高精度模型（需要更多記憶體）
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_DIMENSION=768

# OpenAI 嵌入模型（需要 API 費用）
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_DIMENSION=1536
```

#### OpenAI 模型設定
```bash
# 成本效益平衡（推薦）
OPENAI_MODEL=gpt-3.5-turbo

# 更高品質回答
OPENAI_MODEL=gpt-4

# 新版模型
OPENAI_MODEL=gpt-3.5-turbo-1106
```

### 📏 文字處理最佳化

#### 短文件設定
```bash
CHUNK_SIZE=300          # 適合短篇文章、筆記
CHUNK_OVERLAP=30        # 10% 重疊
SIMILARITY_THRESHOLD=0.8 # 高精確度
TOP_K=3                 # 少量但精準的結果
```

#### 長文件設定
```bash
CHUNK_SIZE=800          # 適合長篇文件、報告
CHUNK_OVERLAP=100       # 12.5% 重疊
SIMILARITY_THRESHOLD=0.6 # 較寬鬆的門檻
TOP_K=8                 # 更多相關內容
```

#### 技術文件設定
```bash
CHUNK_SIZE=600          # 平衡內容完整性
CHUNK_OVERLAP=80        # 保持技術細節連貫
SIMILARITY_THRESHOLD=0.7 # 中等門檻
TOP_K=5                 # 標準數量
```

### 🔍 搜尋策略調整

系統會根據問題類型自動調整搜尋權重：

| 問題類型 | 語意搜尋權重 | 關鍵字搜尋權重 | 適用場景 |
|---------|-------------|---------------|----------|
| 概念性問題 | 80% | 20% | 「什麼是...」、「如何理解...」 |
| 事實性問題 | 70% | 30% | 「誰是...」、「什麼時候...」 |
| 時間性問題 | 50% | 50% | 「何時...」、「期限...」 |
| 位置性問題 | 50% | 50% | 「在哪裡...」、「地點...」 |

### 🚀 效能最佳化

#### 記憶體使用最佳化
```bash
# 降低批次處理大小
BATCH_SIZE=8

# 使用 CPU 版本（節省記憶體）
pip install faiss-cpu

# 清理快取
export TRANSFORMERS_CACHE=/tmp/transformers_cache
```

#### 速度最佳化
```bash
# 使用較小但高效的模型
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# 降低檢索數量
TOP_K=3

# 提高相似度門檻
SIMILARITY_THRESHOLD=0.8
```

#### GPU 加速（選用）
```bash
# 安裝 GPU 版本
pip uninstall faiss-cpu
pip install faiss-gpu

# 安裝 CUDA 支援的 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🚨 常見問題與疑難排解

### 🔐 Notion API 相關問題

**❓ 問題：出現 401 未授權錯誤**
```
💡 解決方案：
1. 檢查 NOTION_TOKEN 是否正確設定在 config/.env 中
2. 確認 Integration Token 格式：secret_xxxxxxxxxxxxxxxxx
3. 驗證 Integration 是否已正確建立且未過期
4. 重新產生 Integration Token 並更新設定
```

**❓ 問題：出現 404 找不到頁面錯誤**
```
💡 解決方案：
確認頁面已透過 Connections 連接到 Integration：
1. 開啟 Notion 頁面
2. 點選右上角「⋯」選單
3. 選擇「Connections」→「Add connections」
4. 搜尋並選擇您的 Integration
5. 確認連接成功且權限正確

⚠️ 重要：不要使用舊版的 Share 功能，請使用新版 Connections
```

**❓ 問題：Integration 無法讀取頁面內容**
```
💡 解決方案：
1. 確認使用新版 Connections 機制
2. 檢查 Integration 權限是否包含「Read content」
3. 確認頁面與 Integration 的連接狀態
4. 嘗試重新連接 Integration
```

**❓ 問題：頁面 ID 格式錯誤**
```
💡 解決方案：
支援兩種格式：
- 完整 URL：https://www.notion.so/workspace/page-title-32字元ID
- 純 ID：32 字元長度的字串（包含數字和字母）

系統會自動解析 URL 中的頁面 ID
```

### 🤖 OpenAI API 相關問題

**❓ 問題：OpenAI API 版本相容性錯誤**
```bash
💡 解決方案：
# 確保安裝正確版本
pip install --upgrade openai>=1.3.0

# 如果仍有問題，重新安裝
pip uninstall openai
pip install openai>=1.3.0
```

**❓ 問題：API 金鑰無效或額度不足**
```
💡 解決方案：
1. 檢查 OPENAI_API_KEY 格式：sk-xxxxxxxxxxxxxxxxxxxxxxxx
2. 前往 OpenAI 官網確認帳戶額度
3. 檢查 API 金鑰是否有正確的權限設定
4. 確認金鑰未過期或被撤銷
```

**❓ 問題：不想使用 OpenAI 服務**
```bash
💡 解決方案：
在 config/.env 中設定：
USE_OPENAI=false

系統會使用內建的規則式查詢分析，
雖然回答品質可能略降，但仍可正常運作
```

**❓ 問題：OpenAI 回應太慢或超時**
```bash
💡 解決方案：
# 使用較快的模型
OPENAI_MODEL=gpt-3.5-turbo

# 或設定不使用 OpenAI
USE_OPENAI=false
```

### 🔧 LINE Bot 相關問題

**❓ 問題：LINE Bot 無法接收訊息**
```
💡 解決方案：
1. 檢查 ngrok 是否正常運行：curl https://your-url.ngrok.io/health
2. 確認 Webhook URL 設定正確且已驗證
3. 檢查 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN
4. 確認已關閉 LINE 官方帳號的自動回覆功能
```

**❓ 問題：LINE Bot 回覆錯誤訊息**
```
💡 解決方案：
1. 查看 linebot_app.py 的終端輸出日誌
2. 確認 RAG 系統是否正常初始化
3. 檢查 Notion 內容是否已成功載入
4. 測試發送簡單訊息如「你好」
```

**❓ 問題：ngrok 連線不穩定**
```
💡 解決方案：
1. 重新啟動 ngrok：ngrok http 8080
2. 更新 LINE Developer Console 中的 Webhook URL
3. 考慮升級 ngrok 付費版本以獲得穩定的 URL
4. 或部署到雲端平台（Heroku、AWS、GCP 等）
```

### ⚡ 效能與記憶體問題

**❓ 問題：模型載入速度太慢**
```bash
💡 解決方案：
# 設定快取目錄加速後續載入
export TRANSFORMERS_CACHE=./cache
CACHE_PATH=./cache

# 使用較小的模型
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**❓ 問題：記憶體使用量過高**
```bash
💡 解決方案：
# 降低批次處理大小
BATCH_SIZE=4

# 使用 CPU 版本
pip install faiss-cpu

# 關閉並行處理
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
```

**❓ 問題：搜尋回應速度慢**
```bash
💡 解決方案：
# 降低檢索文件數量
TOP_K=3

# 提高相似度門檻
SIMILARITY_THRESHOLD=0.8

# 減少文字分塊大小
CHUNK_SIZE=300
```

**❓ 問題：Streamlit 介面載入慢**
```bash
💡 解決方案：
# 清理 Streamlit 快取
streamlit cache clear

# 使用較小的模型
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# 重新啟動服務
```

### 🗄️ 資料庫與檔案問題

**❓ 問題：向量資料庫損壞或無法載入**
```bash
💡 解決方案：
# 刪除現有資料庫檔案
rm -rf vector_db/ metadata.db

# 重新啟動系統，會自動重建
python main.py
# 或
streamlit run app.py
```

**❓ 問題：Notion 內容更新後搜尋結果未改變**
```bash
💡 解決方案：
# 方法一：使用更新指令
python main.py
> update

# 方法二：手動刪除資料庫重建
rm -rf vector_db/ metadata.db
python main.py

# 方法三：在網頁版點選「更新Notion內容」按鈕
```

**❓ 問題：磁碟空間不足**
```bash
💡 解決方案：
# 清理模型快取
rm -rf cache/

# 清理系統快取
pip cache purge

# 使用較小的模型
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 🔍 搜尋品質問題

**❓ 問題：搜尋結果不準確**
```bash
💡 解決方案：
# 降低相似度門檻
SIMILARITY_THRESHOLD=0.6

# 增加檢索結果數量
TOP_K=8

# 調整文字分塊設定
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

**❓ 問題：中文搜尋效果不佳**
```bash
💡 解決方案：
# 使用中文最佳化模型
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 或使用多語言模型
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

### 🔧 系統維護

**❓ 如何更新 Notion 內容？**
```
💡 三種更新方式：
1. 網頁版：點選「更新Notion內容」按鈕
2. 命令列：輸入 'update' 指令
3. 自動更新：系統根據 UPDATE_INTERVAL 設定自動更新（預設1小時）
```

**❓ 如何清理快取和重置系統？**
```bash
💡 完整重置步驟：
# 停止所有相關程序
pkill -f "streamlit\|python.*app.py\|python.*main.py\|python.*linebot_app.py"

# 刪除資料檔案
rm -rf vector_db/ cache/ metadata.db

# 清理 Python 快取
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# 重新啟動系統
python main.py
```

**❓ 如何備份重要資料？**
```bash
💡 備份指令：
# 建立備份目錄
mkdir -p backup/$(date +%Y%m%d_%H%M%S)

# 備份重要檔案
cp -r vector_db/ backup/$(date +%Y%m%d_%H%M%S)/
cp metadata.db backup/$(date +%Y%m%d_%H%M%S)/
cp config/.env backup/$(date +%Y%m%d_%H%M%S)/

# 備份完成
echo "✅ 備份完成至 backup/ 目錄"
```

## 📊 系統監控與狀態檢查

### 💻 命令列狀態檢查

使用 `status` 指令可查看詳細系統狀態：

```bash
python main.py
> status
```

**輸出範例：**
```
📊 系統狀態報告
════════════════════════════════════════════════

📚 向量資料庫狀態:
  ✅ 資料庫路徑: ./vector_db
  ✅ 文件數量: 1,234 筆
  ✅ 向量維度: 384
  ✅ 資料來源: notion_page_abc123...
  ✅ 最後更新: 2024-06-09 14:30:25

🤖 AI 模型設定:
  ✅ OpenAI 狀態: 已啟用
  ✅ GPT 模型: gpt-3.5-turbo
  ✅ 嵌入模型: paraphrase-multilingual-MiniLM-L12-v2
  ✅ 向量維度: 384

⚙️ 系統參數設定:
  📏 文字分塊大小: 500 字元
  🔄 重疊長度: 50 字元
  🎯 相似度門檻: 0.70
  📊 檢索數量: 5 筆

🔗 Notion 連接狀態:
  ✅ API Token: 已設定
  ✅ 頁面 ID: abc123...
  ✅ 連接測試: 成功
  ✅ 權限檢查: 讀取權限正常

💾 系統資源使用:
  💽 磁碟使用: 256 MB
  🧠 記憶體使用: 1.2 GB
  ⏱️ 平均查詢時間: 850 ms
════════════════════════════════════════════════
```

### 🌐 網頁版系統監控

網頁版提供即時的系統狀態儀表板：

- **📊 資料庫統計**：文件數量、向量數量、最後更新時間
- **🤖 AI 模型狀態**：當前使用的模型和設定
- **⚙️ 系統參數**：即時顯示所有重要參數
- **🔄 更新控制**：一鍵更新 Notion 內容
- **📈 效能指標**：查詢回應時間、系統資源使用

### 📱 LINE Bot 健康檢查

```bash
# 檢查 LINE Bot 服務狀態
curl http://localhost:8080/health

# 預期回應
{
  "status": "ok", 
  "message": "Line Bot is running",
  "rag_status": "initialized",
  "timestamp": "2024-06-09T14:30:25Z"
}
```

### 🔧 疑難排解檢查清單

當系統出現問題時，請依序檢查：

1. **✅ 環境設定檢查**
   ```bash
   python -c "from config.settings import Settings; print('設定載入成功')"
   ```

2. **✅ 套件相依性檢查**
   ```bash
   python -c "import sentence_transformers, faiss, openai; print('套件正常')"
   ```

3. **✅ Notion 連線檢查**
   ```bash
   python -c "from core.notion_client import NotionClient; from config.settings import Settings; nc = NotionClient(Settings().NOTION_TOKEN); print('Notion 連線正常')"
   ```

4. **✅ 資料庫檔案檢查**
   ```bash
   ls -la vector_db/ metadata.db
   ```

5. **✅ 權限檢查**
   ```bash
   # 檢查檔案寫入權限
   touch test_write.tmp && rm test_write.tmp && echo "✅ 寫入權限正常"
   ```

## 🔄 版本更新與維護

### 📊 檢查更新

定期檢查專案是否有新版本：

```bash
# 檢查遠端版本
git fetch origin main
git log HEAD..origin/main --oneline

# 查看版本差異
git diff HEAD origin/main

# 更新到最新版本
git pull origin main
```

### 📦 更新套件相依性

```bash
# 檢查過期套件
pip list --outdated

# 更新所有套件到最新版本
pip install -r requirements.txt --upgrade

# 更新特定套件
pip install --upgrade openai sentence-transformers streamlit

# 驗證更新後的相容性
python -c "from config.settings import Settings; print('✅ 更新成功')"
```

### 🔧 資料庫升級

當系統有重大更新時，可能需要重建向量資料庫：

```bash
# 備份現有資料
mkdir -p backup/pre_update_$(date +%Y%m%d)
cp -r vector_db/ metadata.db backup/pre_update_$(date +%Y%m%d)/

# 刪除舊資料庫
rm -rf vector_db/ metadata.db

# 重新初始化系統
python main.py
```

### 📝 更新日誌追蹤

建議在每次更新後記錄：

```bash
# 建立更新記錄
echo "$(date): 更新到版本 X.X.X" >> update_log.txt
echo "變更內容: [描述主要變更]" >> update_log.txt
echo "---" >> update_log.txt
```

## 🤝 聯絡與支援

### 💬 技術支援

如有使用上的問題或建議，歡迎透過以下方式聯絡：

- **技術問題**：關於安裝、設定、使用方面的疑問
- **功能建議**：對系統功能的改進建議
- **錯誤回報**：發現程式錯誤或異常行為

### 📧 聯絡方式

- **Email**：技術問題和使用諮詢

## 📜 使用聲明

本專案為個人開發的學習專案，主要用於展示 RAG 技術的實際應用。

**使用注意事項：**
- 本軟體僅供學習和個人使用
- 使用者需自行承擔使用風險
- 建議在正式環境使用前進行充分測試
- API 使用費用（如 OpenAI）由使用者自行承擔

## 🙏 技術致謝

本專案使用了以下優秀的開源技術和服務：

- **OpenAI**：提供強大的 GPT 模型和 API 服務
- **Notion**：優秀的知識管理平台和開放 API
- **Sentence Transformers**：高品質的文字嵌入模型庫
- **Facebook AI Research**：FAISS 高效向量搜尋引擎
- **Streamlit**：簡潔優雅的 Python 網頁應用框架
- **LINE**：便利的即時通訊平台和 Messaging API

感謝這些技術讓個人開發者也能輕鬆建立強大的 AI 應用。

---

## 🎯 快速開始檢查清單

準備開始使用？請確認以下步驟：

- [ ] ✅ Python 3.8+ 已安裝
- [ ] ✅ 虛擬環境已建立並啟用
- [ ] ✅ 相依套件已安裝 (`pip install -r requirements.txt`)
- [ ] ✅ Notion Integration 已建立
- [ ] ✅ Notion 頁面已連接到 Integration
- [ ] ✅ `config/.env` 檔案已設定
- [ ] ✅ 環境設定驗證通過
- [ ] 🚀 準備啟動系統！

```bash
# 開始您的智慧問答之旅
streamlit run app.py
```

---

⭐ **如果這個專案對您有幫助，歡迎分享給朋友！**

📱 **適用場景**：個人知識管理、學習筆記整理、專案文件查詢

💡 **技術學習**：RAG 架構、向量搜尋、自然語言處理應用

---

*最後更新：2024年6月*

*本文件使用繁體中文編寫，專為台灣使用者最佳化*
