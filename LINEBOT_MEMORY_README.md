# LINE Bot 連續對話記憶功能

## 功能概述

這個專案為 Notion RAG 智慧問答系統增加了 LINE Bot 連續對話記憶功能，讓 Bot 能夠記住與用戶的對話歷程，提供更自然的連續對話體驗。

## 主要特色

### 🧠 智慧記憶管理
- **連續對話上下文**：記住對話歷程，理解代詞和指示詞
- **自動過期機制**：設定時間後自動清除記憶，節省資源
- **長度限制**：控制對話長度，避免 token 超限
- **記憶體最佳化**：定期清理過期對話，維持效能

### 🤖 增強版 RAG 引擎
- **上下文感知**：結合對話歷程進行查詢
- **智慧問題增強**：檢測需要上下文的問題
- **回答連貫性**：保持對話的一致性
- **多層次搜尋**：語義搜尋 + 關鍵字搜尋

### 📱 LINE Bot 整合
- **即時回應**：快速處理用戶訊息
- **特殊指令**：支援清除記憶、查看狀態等功能
- **錯誤處理**：優雅處理各種異常情況
- **長文本處理**：自動截斷過長回應

## 安裝與設定

### 1. 環境準備

```bash
# 安裝依賴
pip install -r requirements.txt

# 複製環境變數範例檔案
cp config/.env.example config/.env
```

### 2. 設定環境變數

編輯 `config/.env` 檔案：

```bash
# Notion 設定
NOTION_TOKEN=your_notion_integration_token
NOTION_PAGE_ID=your_notion_page_id_or_url

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# 對話記憶設定
CONVERSATION_TIMEOUT_MINUTES=30          # 對話逾時時間（分鐘）
MAX_CONVERSATION_LENGTH=20               # 最大對話長度（訊息數）
CLEANUP_INTERVAL_MINUTES=5               # 清理間隔（分鐘）
MAX_CONTEXT_TOKENS=2000                  # 最大上下文 token 數

# OpenAI 設定（可選）
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# 伺服器設定
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
```

### 3. 啟動服務

```bash
# 啟動 LINE Bot 服務
python linebot_app.py
```

服務啟動後會顯示：
- 📡 服務位址：http://localhost:5000
- 🔗 Webhook URL：http://localhost:5000/callback
- 💚 健康檢查：http://localhost:5000/health
- 📊 統計資訊：http://localhost:5000/stats

## 使用說明

### 基本對話

```
用戶：你好
Bot：您好！我是基於您的 Notion 文件的智慧問答助手 🤖

用戶：我想了解這個專案
Bot：這個專案是一個 Notion RAG 智慧問答系統...

用戶：那要怎麼安裝？
Bot：根據剛才提到的專案，安裝步驟如下...（參考上下文）

用戶：如果遇到錯誤怎麼辦？
Bot：關於您剛才詢問的安裝問題，如果遇到錯誤...（持續參考上下文）
```

### 特殊指令

| 指令 | 功能 |
|------|------|
| `幫助` / `help` | 顯示使用說明 |
| `清除記憶` / `重新開始` | 清除對話記憶 |
| `狀態` / `status` | 查看系統狀態 |
| `統計` | 查看對話統計 |

### 上下文理解

系統會自動檢測需要上下文的問題：
- 代詞：「這個」、「那個」、「它」
- 指示詞：「上面」、「剛才」、「之前」、「提到的」
- 連接詞：「還有」、「另外」、「繼續」

## API 端點

### 健康檢查
```bash
GET /health
```

回應：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "conversation_stats": {...},
  "rag_stats": {...},
  "message": "連續對話 RAG 系統運行正常"
}
```

### 統計資訊
```bash
GET /stats
```

### 清除所有記憶（管理員功能）
```bash
POST /admin/clear_memory
```

## 技術架構

### 核心模組

1. **ConversationMemory** (`core/conversation_memory.py`)
   - 對話記憶管理
   - 自動過期清理
   - 線程安全操作

2. **EnhancedRAGEngine** (`core/enhanced_rag_engine.py`)
   - 增強版 RAG 引擎
   - 上下文感知查詢
   - 智慧回答生成

3. **LineBotHandler** (`services/linebot_handler.py`)
   - LINE Bot 訊息處理
   - 特殊指令解析
   - 錯誤處理

### 對話記憶機制

```python
# 對話資料結構
conversation_data = {
    'user_id': 'U123456789',
    'messages': [
        {'role': 'user', 'content': '你好', 'timestamp': datetime},
        {'role': 'assistant', 'content': '您好！', 'timestamp': datetime}
    ],
    'last_active': datetime,
    'created_at': datetime
}
```

### 上下文管理策略

- **保留策略**：最近 N 組對話（可設定）
- **長度控制**：自動刪除最舊的對話
- **Token 限制**：控制上下文長度避免超限
- **時間管理**：定期清理過期對話

## 測試

### 執行所有測試
```bash
python test/run_tests.py
```

### 執行特定測試
```bash
# 測試對話記憶
python test/run_tests.py test.test_conversation_memory

# 測試 LINE Bot 處理器
python test/run_tests.py test.test_linebot_handler
```

### 測試涵蓋範圍
- ✅ 對話記憶管理
- ✅ 上下文生成
- ✅ 過期機制
- ✅ LINE Bot 處理
- ✅ 特殊指令
- ✅ 錯誤處理

## 效能監控

### 記憶體使用
- 對話數據自動清理
- 定期記憶體回收
- 使用量監控

### 回應時間
- 非同步處理
- 連線池管理
- 快取機制

### 錯誤處理
- Notion API 連線失敗
- OpenAI API 限制
- LINE Bot webhook 驗證失敗
- 記憶體不足處理

## 部署建議

### 生產環境設定
```bash
# 關閉除錯模式
FLASK_DEBUG=false

# 設定適當的逾時時間
CONVERSATION_TIMEOUT_MINUTES=60

# 使用 Redis（可選）
USE_REDIS=true
REDIS_URL=redis://redis-server:6379
```

### 使用 Docker（建議）
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "linebot_app.py"]
```

### 使用 Nginx 反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 常見問題

### Q: 對話記憶會一直增長嗎？
A: 不會，系統有自動過期機制和長度限制，會定期清理過期對話。

### Q: 如何調整記憶時間？
A: 修改 `CONVERSATION_TIMEOUT_MINUTES` 環境變數。

### Q: 支援多用戶嗎？
A: 是的，每個 LINE 用戶都有獨立的對話記憶。

### Q: 如何備份對話記憶？
A: 目前使用記憶體儲存，重啟會清空。生產環境建議使用 Redis。

### Q: 可以自訂特殊指令嗎？
A: 可以，修改 `LineBotHandler` 中的 `predefined_responses` 字典。

## 授權

本專案使用 MIT 授權條款。

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 更新日誌

### v1.0.0 (2024-01-01)
- ✨ 新增連續對話記憶功能
- 🚀 整合增強版 RAG 引擎
- 🤖 完整 LINE Bot 支援
- �� 完整測試覆蓋
- 📚 詳細文件說明 