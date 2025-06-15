# Render 部署快速指南

> 🚀 快速部署 Notion RAG LINE Bot 到 Render 免費層

## 📋 部署前檢查

執行部署前檢查腳本：
```bash
python deploy/scripts/deploy_check.py
```

## 🔧 部署步驟

### 1. 準備 GitHub 儲存庫
```bash
git init
git add .
git commit -m "準備部署到 Render"
git remote add origin YOUR_GITHUB_REPO
git push -u origin main
```

### 2. 在 Render 建立服務
1. 登入 [Render](https://render.com/)
2. 點擊 "New Web Service"
3. 連接您的 GitHub 儲存庫
4. 使用以下設定：
   - **Environment**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python linebot_app.py`

### 3. 設定環境變數

#### 必要環境變數
```bash
NOTION_TOKEN=your_notion_token
NOTION_PAGE_ID=your_notion_page_id
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
```

#### Render 最佳化設定
```bash
RENDER_DEPLOYMENT=true
USE_MEMORY_STORAGE=true
MEMORY_LIMIT=450
BATCH_SIZE=4
FLASK_HOST=0.0.0.0
FLASK_PORT=10000
FLASK_DEBUG=false
TOKENIZERS_PARALLELISM=false
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

### 4. 更新 LINE Bot Webhook
部署完成後，更新 LINE Developers Console 中的 Webhook URL：
```
https://your-app-name.onrender.com/callback
```

### 5. 設定 UptimeRobot 監控
為了防止免費層的 30 分鐘閒置關閉：
1. 註冊 [UptimeRobot](https://uptimerobot.com/)
2. 新增 HTTP(s) 監控
3. URL: `https://your-app-name.onrender.com/health`
4. 間隔: 5-10 分鐘

## 🔍 監控與除錯

### 健康檢查端點
- `/health` - 基本健康狀態
- `/stats` - 記憶體使用統計
- `/admin/clear_memory` - 手動清理記憶體

### 記憶體監控
```bash
# 即時監控
python deploy/scripts/memory_monitor.py --status

# 持續監控
python deploy/scripts/memory_monitor.py --start
```

## ⚠️ 限制與注意事項

### Render 免費層限制
- **記憶體**: 512MB
- **CPU**: 0.1 vCPU
- **儲存**: 暫時性 (重啟時清除)
- **閒置關閉**: 30 分鐘後自動休眠
- **冷啟動**: 休眠後需要 30-60 秒啟動

### 效能最佳化
- 使用記憶體資料庫 (`:memory:`)
- 縮小批次處理大小
- 強制 CPU 運算 (不使用 GPU)
- 定期記憶體清理

## 🚨 故障排除

### 常見問題

#### 1. 記憶體不足錯誤
```bash
# 檢查記憶體使用
curl https://your-app-name.onrender.com/stats

# 手動清理
curl https://your-app-name.onrender.com/admin/clear_memory
```

#### 2. 應用程式無回應
- 檢查 Render 日誌
- 確認環境變數設定
- 檢查 Webhook URL 是否正確

#### 3. LINE Bot 無法回應
- 確認 LINE Channel 設定
- 檢查 Webhook URL
- 驗證環境變數

### 日誌檢查
在 Render Dashboard 中檢查應用程式日誌：
1. 進入您的服務頁面
2. 點擊 "Logs" 標籤
3. 即時檢視應用程式輸出

## 📈 升級選項

如需更好的效能，考慮升級到 Render 付費方案：
- **Starter Plan** ($7/月): 512MB RAM, 0.5 CPU, 無閒置關閉
- **Standard Plan** ($25/月): 2GB RAM, 1 CPU
- **Pro Plan** ($85/月): 4GB RAM, 2 CPU

---

> 💡 **提示**: 首次部署可能需要較長時間來下載和安裝依賴套件，請耐心等待。 