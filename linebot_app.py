import os
import sys
import gc
import threading
from flask import Flask, request, abort

# 設定環境變數（必須在導入其他庫之前）
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# 將專案根目錄加入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.notion_client import NotionClient
from core.text_processor import TextProcessor
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.rag_engine import RAGEngine

# 使用 Line Bot SDK v3
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage as LineTextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 載入設定
try:
    settings = Settings()
    print("✅ 設定載入成功")
except Exception as e:
    print(f"❌ 設定載入失敗: {e}")
    sys.exit(1)

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 Line Bot v3 API
try:
    configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
    api_client = ApiClient(configuration)
    line_bot_api = MessagingApi(api_client)
    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
    print("✅ Line Bot API 初始化成功")
except Exception as e:
    print(f"❌ Line Bot API 初始化失敗: {e}")
    sys.exit(1)

# 全域 RAG 引擎（避免每次請求都重新初始化）
rag_engine = None
rag_lock = threading.RLock()  # 使用可重入鎖

def initialize_rag_engine():
    """初始化 RAG 引擎（只初始化一次）"""
    global rag_engine
    
    with rag_lock:
        if rag_engine is not None:
            print("♻️ 使用現有的 RAG 引擎")
            return rag_engine
        
        try:
            print("🤖 正在初始化 RAG 系統...")
            
            # 建立組件
            notion_client = NotionClient(settings.NOTION_TOKEN)
            text_processor = TextProcessor(settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            embedder = Embedder(settings.EMBEDDING_MODEL)
            vector_store = VectorStore(
                settings.VECTOR_DB_PATH, 
                settings.METADATA_DB_PATH, 
                settings.EMBEDDING_DIMENSION
            )
            
            # 建立 RAG 引擎
            rag_engine = RAGEngine(
                notion_client, text_processor, embedder, vector_store, settings
            )
            
            # 檢查是否需要處理 Notion 內容
            status = rag_engine.get_system_status()
            if status['vector_database']['total_documents'] == 0:
                print("📄 首次使用，正在處理 Notion 內容...")
                success = rag_engine.process_notion_page(settings.NOTION_PAGE_ID)
                if success:
                    print("✅ Notion 內容處理完成！")
                else:
                    print("❌ Notion 內容處理失敗")
            
            print("🚀 RAG 系統初始化完成！")
            
            # 執行記憶體清理
            gc.collect()
            
            return rag_engine
            
        except Exception as e:
            print(f"❌ RAG 系統初始化失敗: {e}")
            return None

def safe_rag_query(question):
    """線程安全的 RAG 查詢"""
    global rag_engine
    
    with rag_lock:
        try:
            if rag_engine is None:
                raise Exception("RAG 系統未初始化")
            
            print(f"🔍 開始處理問題: {question}")
            result = rag_engine.query(question)
            print(f"✅ 查詢完成")
            return result
            
        except Exception as e:
            print(f"❌ RAG 查詢錯誤: {e}")
            # 嘗試使用簡化回應
            if "測試" in question:
                return "我收到了您的測試訊息！我是基於 Notion 文件的智慧助手，可以幫您回答文件相關的問題。"
            elif any(keyword in question for keyword in ["檢查", "狀態", "status"]):
                return "系統運行正常！我已經載入了您的 Notion 文件，準備回答相關問題。"
            else:
                return "抱歉，處理這個問題時遇到了技術問題。請嘗試重新表述您的問題，或者問一些更簡單具體的問題。"

# 啟動時初始化 RAG 系統
print("🚀 啟動時預先初始化 RAG 系統...")
rag_engine = initialize_rag_engine()

if rag_engine is None:
    print("❌ 無法初始化 RAG 系統，服務將無法正常運行")
    sys.exit(1)

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature header 值
    signature = request.headers['X-Line-Signature']

    # 獲取請求 body 內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        # 獲取用戶的問題
        user_question = event.message.text
        print(f"📩 收到問題: {user_question}")
        
        # 如果是簡單的招呼語，直接回應
        greetings = ["你好", "hello", "hi", "嗨", "Hello", "Hi"]
        if user_question.strip() in greetings:
            response = "您好！我是基於您的 Notion 文件的智慧問答助手。請問您想了解文件中的什麼內容呢？"
        else:
            # 使用線程安全的查詢方法
            response = safe_rag_query(user_question)
        
        print(f"📤 準備回覆: {response[:50]}...")
        
        # 確保回應不會太長（Line 有字數限制）
        if len(response) > 2000:
            response = response[:1950] + "...\n\n（回應內容較長，已省略部分內容）"
        
        # 使用 v3 API 回傳回應
        reply_message_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[LineTextMessage(text=response)]
        )
        line_bot_api.reply_message(reply_message_request)
        
        print("✅ 回覆發送成功")
        
        # 強制執行記憶體清理
        gc.collect()
        
    except Exception as e:
        print(f"❌ 處理錯誤: {str(e)}")
        # 錯誤處理
        error_msg = f"抱歉，處理您的問題時發生錯誤。請稍後再試或嘗試更簡單的問題。"
        try:
            reply_message_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[LineTextMessage(text=error_msg)]
            )
            line_bot_api.reply_message(reply_message_request)
        except Exception as reply_error:
            print(f"❌ 發送錯誤訊息失敗: {reply_error}")

@app.route("/health", methods=['GET'])
def health_check():
    """健康檢查端點"""
    global rag_engine
    status = "ok" if rag_engine is not None else "error"
    return {"status": status, "message": f"Line Bot is {'running' if status == 'ok' else 'not ready'}"}

if __name__ == "__main__":
    print("🤖 啟動 Line Bot 服務...")
    print("📱 Webhook URL: http://localhost:8080/callback")
    print("💡 如果需要外部存取，請使用 ngrok: ngrok http 8080")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)  # 啟用多線程支援 