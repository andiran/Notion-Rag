# 📦 部署相關檔案

本目錄包含 Notion RAG LINE Bot 系統的所有部署相關檔案和工具。

## 📁 目錄結構

```
deploy/
├── scripts/         # 部署輔助腳本
│   ├── deploy_check.py    # 部署前相容性檢查
│   └── memory_monitor.py  # 記憶體監控工具
├── docs/           # 部署文件
│   └── RENDER_DEPLOYMENT.md  # Render 部署指南
├── Dockerfile      # Docker 容器設定
└── README.md       # 本說明檔案

# Render 部署設定檔案（必須位於專案根目錄）
render.yaml         # Render 服務設定檔（Render 平台要求）
```

## 🚀 快速開始

### 1. 部署前檢查
```bash
# 檢查系統是否準備好部署
python deploy/scripts/deploy_check.py
```

### 2. Render 部署
```bash
# 詳細步驟請參考
cat deploy/docs/RENDER_DEPLOYMENT.md
```

### 3. 記憶體監控
```bash
# 檢查記憶體使用狀況
python deploy/scripts/memory_monitor.py --status

# 啟動持續監控
python deploy/scripts/memory_monitor.py --start
```

## 📋 檔案說明

### Dockerfile
- **Dockerfile**: Docker 容器映像設定，針對 Render 環境最佳化（現在位於 deploy/ 目錄）

### 根目錄檔案（平台限制）
- **render.yaml**: Render 平台的服務設定檔（Render 平台要求必須位於根目錄）

### scripts/
- **deploy_check.py**: 部署前系統檢查工具
  - 檢查 Python 版本相容性
  - 驗證必要套件是否安裝
  - 確認環境變數設定
  - 檢查檔案結構完整性
  
- **memory_monitor.py**: 記憶體監控和管理工具
  - 即時記憶體使用監控
  - 自動記憶體清理機制
  - 記憶體統計和報告
  - 支援背景監控模式

### docs/
- **RENDER_DEPLOYMENT.md**: Render 平台部署的詳細指南
  - 逐步部署說明
  - 環境變數設定指引
  - 常見問題解決方案
  - 監控和維護建議

## 🔧 使用方式

### 本地測試
```bash
# 在本地測試部署設定
docker build -f deploy/Dockerfile -t notion-rag-test .
docker run -p 10000:10000 notion-rag-test
```

### Render 部署
1. 將檔案推送到 GitHub
2. 在 Render 建立新的 Web Service
3. 連接 GitHub 儲存庫
4. Render 會自動讀取根目錄的 `render.yaml`

### 記憶體最佳化
```bash
# 檢查當前記憶體狀況
curl https://your-app.onrender.com/stats

# 手動清理記憶體
curl -X POST https://your-app.onrender.com/admin/clear_memory
```

## ⚡ 最佳實踐

1. **部署前必做**：執行 `deploy_check.py` 檢查系統
2. **監控記憶體**：定期使用 `memory_monitor.py` 檢查
3. **設定監控**：使用 UptimeRobot 等服務防止自動休眠
4. **版本控制**：部署前確保所有變更已提交到 Git

## 🆘 故障排除

### 部署失敗
```bash
# 重新檢查系統
python deploy/scripts/deploy_check.py

# 檢查 Render 日誌
# 在 Render Dashboard → Your Service → Logs
```

### 記憶體問題
```bash
# 監控記憶體使用
python deploy/scripts/memory_monitor.py --status

# 執行記憶體清理
python deploy/scripts/memory_monitor.py --cleanup
```

### 服務無回應
```bash
# 檢查健康狀態
curl https://your-app.onrender.com/health

# 檢查記憶體統計
curl https://your-app.onrender.com/stats
```

---

> 💡 **提示**: 部署到生產環境前，建議先在本地充分測試，並確保所有環境變數都已正確設定。 