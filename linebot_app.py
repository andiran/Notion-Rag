import os
import sys
import gc
import threading
import atexit
from flask import Flask, request, abort

# =====================================
# Render 部署記憶體最佳化設定
# =====================================
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['HF_HOME'] = '/tmp/hf_cache'
os.environ['TORCH_HOME'] = '/tmp/torch_cache'

def cleanup_memory():
    """定期清理記憶體"""
    gc.collect()
    print("🧹 記憶體清理完成")

def is_render_environment():
    """檢查是否在 Render 環境中"""
    return os.environ.get('RENDER') or os.environ.get('RENDER_SERVICE_ID')

# Render 環境檢測和最佳化
IS_RENDER_DEPLOYMENT = os.getenv("RENDER_DEPLOYMENT", "false").lower() == "true" or is_render_environment()
if IS_RENDER_DEPLOYMENT:
    print("🌐 檢測到 Render 環境，啟用記憶體最佳化...")
    # 創建必要的臨時目錄
    os.makedirs("/tmp/cache", exist_ok=True)
    os.makedirs("/tmp/hf_cache", exist_ok=True)
    os.makedirs("/tmp/torch_cache", exist_ok=True)

# 將專案根目錄加入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.notion_client import NotionClient
from core.text_processor import TextProcessor
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.enhanced_rag_engine import EnhancedRAGEngine
from core.conversation_memory import ConversationMemory
from services.linebot_handler import LineBotHandler

# 使用 Line Bot SDK v3
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 載入設定
try:
    settings = Settings()
    print("✅ 設定載入成功")
    
    # 驗證 LINE Bot 設定
    if not settings.validate_line_bot_settings():
        print("❌ LINE Bot 設定不完整，無法啟動")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 設定載入失敗: {e}")
    sys.exit(1)

# 初始化 Flask 應用
app = Flask(__name__)

# 全域變數
rag_engine = None
conversation_memory = None
linebot_handler = None
rag_lock = threading.RLock()

def initialize_system():
    """初始化整個系統（Render 最佳化版本）"""
    global rag_engine, conversation_memory, linebot_handler
    
    with rag_lock:
        if rag_engine is not None and conversation_memory is not None and linebot_handler is not None:
            print("♻️ 使用現有的系統組件")
            return True
        
        try:
            print("🚀 正在初始化連續對話 RAG 系統...")
            
            # Render 環境記憶體最佳化
            if IS_RENDER_DEPLOYMENT:
                print("🌐 檢測到 Render 環境，啟用記憶體最佳化模式")
                # 強制垃圾回收
                cleanup_memory()
            
            # 1. 建立基礎組件（記憶體最佳化）
            print("📦 初始化基礎組件...")
            notion_client = NotionClient(settings.NOTION_TOKEN)
            text_processor = TextProcessor(settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            
            # 使用輕量級模型
            embedding_model = settings.EMBEDDING_MODEL
            if IS_RENDER_DEPLOYMENT:
                embedding_model = "sentence-transformers/all-MiniLM-L6-v2"  # 最小模型
                print(f"🔧 Render 環境使用輕量級模型: {embedding_model}")
            
            embedder = Embedder(embedding_model, settings.BATCH_SIZE)
            
            # 記憶體清理
            cleanup_memory()
            
            vector_store = VectorStore(
                ":memory:" if IS_RENDER_DEPLOYMENT else settings.VECTOR_DB_PATH,  # Render 環境使用記憶體儲存
                ":memory:" if IS_RENDER_DEPLOYMENT else settings.METADATA_DB_PATH, 
                settings.EMBEDDING_DIMENSION
            )
            
            # 2. 建立增強版 RAG 引擎
            print("🧠 初始化增強版 RAG 引擎...")
            rag_engine = EnhancedRAGEngine(
                notion_client, text_processor, embedder, vector_store, settings
            )
            
            # 3. 初始化對話記憶管理器（降低記憶體使用）
            print("💭 初始化對話記憶管理器...")
            conversation_settings = settings.get_conversation_settings()
            
            # Render 環境降低記憶體使用
            if IS_RENDER_DEPLOYMENT:
                conversation_settings['timeout_minutes'] = 10  # 縮短逾時
                conversation_settings['max_conversation_length'] = 5  # 減少對話長度
                conversation_settings['cleanup_interval_minutes'] = 2  # 頻繁清理
            
            conversation_memory = ConversationMemory(
                timeout_minutes=conversation_settings['timeout_minutes'],
                max_conversation_length=conversation_settings['max_conversation_length'],
                cleanup_interval_minutes=conversation_settings['cleanup_interval_minutes'],
                max_context_tokens=conversation_settings['max_context_tokens']
            )
            
            # 4. 初始化 LINE Bot 處理器
            print("🤖 初始化 LINE Bot 處理器...")
            linebot_handler = LineBotHandler(
                rag_engine=rag_engine,
                conversation_memory=conversation_memory,
                line_channel_access_token=settings.LINE_CHANNEL_ACCESS_TOKEN
            )
            
            # 5. 處理 Notion 內容（記憶體最佳化）
            print("📄 檢查 Notion 內容...")
            status = rag_engine.get_system_status()
            if status['vector_database']['total_documents'] == 0:
                print("📚 首次使用，正在處理 Notion 內容...")
                success = rag_engine.process_notion_page(settings.NOTION_PAGE_ID)
                if success:
                    print("✅ Notion 內容處理完成！")
                    # 立即清理記憶體
                    cleanup_memory()
                else:
                    print("❌ Notion 內容處理失敗")
                    return False
            else:
                print(f"📊 已載入 {status['vector_database']['total_documents']} 個文件片段")
            
            print("🎉 連續對話 RAG 系統初始化完成！")
            
            # 最終記憶體清理
            cleanup_memory()
            
            # 執行記憶體清理
            gc.collect()
            
            # Render 環境啟動記憶體監控
            if IS_RENDER_DEPLOYMENT:
                try:
                    from scripts.memory_monitor import MemoryMonitor
                    memory_limit = int(os.getenv('MEMORY_LIMIT', '450'))
                    monitor = MemoryMonitor(memory_limit_mb=memory_limit)
                    monitor.start_monitoring()
                    print("🔍 Render 記憶體監控已啟動")
                except Exception as e:
                    print(f"⚠️ 記憶體監控啟動失敗: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 系統初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

def cleanup_system():
    """清理系統資源"""
    global conversation_memory
    print("🧹 正在清理系統資源...")
    
    if conversation_memory:
        try:
            conversation_memory.shutdown()
            print("✅ 對話記憶管理器已關閉")
        except Exception as e:
            print(f"❌ 關閉對話記憶管理器時發生錯誤: {e}")
    
    print("👋 系統清理完成")

# 註冊清理函數
atexit.register(cleanup_system)

# 初始化 LINE Bot Webhook Handler
try:
    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
    print("✅ LINE Bot Webhook Handler 初始化成功")
except Exception as e:
    print(f"❌ LINE Bot Webhook Handler 初始化失敗: {e}")
    sys.exit(1)

# 啟動時初始化系統
print("🚀 啟動時預先初始化系統...")
if not initialize_system():
    print("❌ 無法初始化系統，服務將無法正常運行")
    sys.exit(1)

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Bot Webhook 回調端點"""
    # 獲取 X-Line-Signature header 值
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        print("❌ 缺少 X-Line-Signature header")
        abort(400)

    # 獲取請求 body 內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 簽名驗證失敗，請檢查 Channel Secret")
        abort(400)
    except Exception as e:
        print(f"❌ 處理 webhook 請求時發生錯誤: {e}")
        abort(500)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息事件（Render 最佳化版本）"""
    global linebot_handler
    
    try:
        # 確保系統已初始化
        if not linebot_handler:
            print("⚠️ 系統未完全初始化，嘗試重新初始化...")
            if not initialize_system():
                raise Exception("系統初始化失敗")
        
        # 使用 LINE Bot 處理器處理訊息
        linebot_handler.handle_text_message(event)
        
        # Render 環境記憶體清理
        if IS_RENDER_DEPLOYMENT:
            cleanup_memory()
        
        # 執行記憶體清理 (Render 環境更積極清理)
        if IS_RENDER_DEPLOYMENT:
            # 積極的記憶體清理
            for _ in range(2):
                gc.collect()
        else:
            gc.collect()
        
    except Exception as e:
        print(f"❌ 處理訊息時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # 發送錯誤訊息給用戶
        try:
            if linebot_handler:
                error_msg = "抱歉，系統目前遇到技術問題，請稍後再試。"
                linebot_handler._send_reply(event.reply_token, error_msg)
        except Exception as reply_error:
            print(f"❌ 發送錯誤訊息失敗: {reply_error}")

@app.route("/health", methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        if not rag_engine or not conversation_memory or not linebot_handler:
            return {"status": "error", "message": "系統未完全初始化"}, 503
        
        # 獲取系統狀態
        handler_stats = linebot_handler.get_handler_stats()
        
        return {
            "status": "healthy",
            "timestamp": handler_stats["timestamp"],
            "conversation_stats": handler_stats.get("conversation_memory", {}),
            "rag_stats": handler_stats.get("rag_engine", {}),
            "message": "連續對話 RAG 系統運行正常"
        }, 200
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"健康檢查失敗: {str(e)}"
        }, 500

@app.route("/stats", methods=['GET'])
def get_stats():
    """獲取詳細統計資訊"""
    try:
        if not linebot_handler:
            return {"error": "系統未初始化"}, 503
        
        stats = linebot_handler.get_handler_stats()
        return stats, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/admin/clear_memory", methods=['POST'])
def clear_all_memory():
    """管理員功能：清除所有對話記憶"""
    try:
        if not conversation_memory:
            return {"error": "對話記憶管理器未初始化"}, 503
        
        # 獲取清理前的統計
        before_stats = conversation_memory.get_conversation_stats()
        
        # 清理所有對話
        cleared_count = 0
        user_ids = list(conversation_memory.conversations.keys())
        for user_id in user_ids:
            if conversation_memory.clear_conversation(user_id):
                cleared_count += 1
        
        # 強制執行記憶體清理
        gc.collect()
        
        return {
            "message": f"已清除 {cleared_count} 個對話記憶",
            "before_stats": before_stats,
            "after_stats": conversation_memory.get_conversation_stats()
        }, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    print("🚀 啟動連續對話 LINE Bot 服務...")
    
    # 檢查環境
    if IS_RENDER_DEPLOYMENT:
        print("🌐 Render 環境模式啟動")
        # Render 環境特殊設定
        port = int(os.environ.get('PORT', 10000))
        host = '0.0.0.0'
        debug = False
    else:
        print("💻 本地開發環境模式啟動")
        # 本地環境設定
        port = settings.FLASK_PORT
        host = settings.FLASK_HOST
        debug = settings.FLASK_DEBUG
    
    print(f"📡 服務位址: http://{host}:{port}")
    print(f"🔗 Webhook URL: http://{host}:{port}/callback")
    print(f"💚 健康檢查: http://{host}:{port}/health")
    print(f"📊 統計資訊: http://{host}:{port}/stats")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,  # 啟用多線程支援
            use_reloader=False  # Render 環境避免重載器
        )
    except KeyboardInterrupt:
        print("\n👋 收到停止信號，正在關閉服務...")
        cleanup_system()
    except Exception as e:
        print(f"❌ 服務啟動失敗: {e}")
        cleanup_system()
        sys.exit(1) 