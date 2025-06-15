# 使用 Python 3.9 輕量版基礎映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數以最佳化記憶體使用
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV RENDER_DEPLOYMENT=true
ENV USE_MEMORY_STORAGE=true

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立必要的目錄
RUN mkdir -p cache

# 設定健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# 暴露端口
EXPOSE 10000

# 啟動應用
CMD ["python", "linebot_app.py"] 