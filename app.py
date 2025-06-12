import streamlit as st
import os
import sys
from datetime import datetime
from flask import Flask, request, abort

# 將專案根目錄加入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.notion_client import NotionClient
from core.text_processor import TextProcessor
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.rag_engine import RAGEngine

# 設定環境變數
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# 頁面設定
st.set_page_config(
    page_title="Notion RAG 智慧問答系統",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 樣式
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background-color: #2196F3;
        color: white;
        border-left: 4px solid #0D47A1;
        margin-left: 20px;
    }
    
    .bot-message {
        background-color: #4CAF50;
        color: white;
        border-left: 4px solid #1B5E20;
        margin-right: 20px;
    }
    
    .status-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    /* 輸入框樣式 */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        border: 3px solid #2196F3 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #000000 !important;
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #1976D2 !important;
        box-shadow: 0 0 0 4px rgba(33, 150, 243, 0.3) !important;
        background-color: #f8fbff !important;
        color: #000000 !important;
        outline: none !important;
    }
    
    /* 輸入框 placeholder 文字 */
    .stTextInput > div > div > input::placeholder {
        color: #666666 !important;
        opacity: 1 !important;
    }
    
    /* 輸入框標籤 */
    .stTextInput > label {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #1976D2 !important;
        margin-bottom: 8px !important;
    }
    
    /* 強制覆蓋Streamlit的默認樣式 */
    .stTextInput input[type="text"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 3px solid #2196F3 !important;
    }
    
    /* 提問按鈕強化 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(45deg, #2196F3, #21CBF3);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(33, 150, 243, 0.6);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_rag_system():
    """初始化RAG系統（使用快取避免重複載入）"""
    try:
        with st.spinner("正在初始化RAG系統..."):
            # 載入設定
            settings = Settings()
            
            # 建立組件
            notion_client = NotionClient(settings.NOTION_TOKEN)
            text_processor = TextProcessor(settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            embedder = Embedder(settings.EMBEDDING_MODEL)
            vector_store = VectorStore(
                settings.VECTOR_DB_PATH, 
                settings.METADATA_DB_PATH, 
                settings.EMBEDDING_DIMENSION
            )
            
            # 建立RAG引擎
            rag_engine = RAGEngine(
                notion_client, text_processor, embedder, vector_store, settings
            )
            
            # 檢查是否需要處理Notion內容
            status = rag_engine.get_system_status()
            if status['vector_database']['total_documents'] == 0:
                st.info("首次使用，正在處理Notion內容...")
                success = rag_engine.process_notion_page(settings.NOTION_PAGE_ID)
                if not success:
                    st.error("Notion內容處理失敗")
                    return None
                st.success("Notion內容處理完成！")
            
            return rag_engine
            
    except Exception as e:
        st.error(f"系統初始化失敗: {e}")
        st.info("請檢查 config/.env 檔案設定")
        return None

def main():
    """主程式"""
    
    # 標題
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Notion RAG 智慧問答系統</h1>
        <p>基於你的Notion文件，提供智慧問答服務</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 側邊欄
    with st.sidebar:
        st.header("⚙️ 系統控制")
        
        # 初始化按鈕
        if st.button("🔄 重新初始化系統", type="secondary"):
            st.cache_resource.clear()
            st.rerun()
        
        # 更新Notion內容按鈕
        if st.button("📄 更新Notion內容", type="secondary"):
            if "rag_engine" in st.session_state and st.session_state.rag_engine:
                with st.spinner("更新中..."):
                    success = st.session_state.rag_engine.update_notion_content()
                    if success:
                        st.success("更新成功！")
                    else:
                        st.error("更新失敗")
            else:
                st.warning("請先初始化系統")
        
        st.divider()
        
        # 範例問題
        st.header("💡 問題範例")
        example_questions = [
            "這次旅行的目的地是哪裡？",
            "飛機什麼時候起飛？", 
            "住在哪個飯店？",
            "第一天有什麼行程？",
            "有什麼美食推薦？",
            "總共幾天的行程？"
        ]
        
        for question in example_questions:
            if st.button(f"📝 {question}", key=f"example_{question}"):
                st.session_state.current_question = question
    
    # 主要內容區域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 問答對話")
        
        # 初始化RAG系統
        if "rag_engine" not in st.session_state:
            st.session_state.rag_engine = initialize_rag_system()
        
        if not st.session_state.rag_engine:
            st.error("無法初始化系統，請檢查設定")
            st.stop()
        
        # 初始化對話歷史
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 顯示對話歷史
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 你:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 系統:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
        
        # 問題輸入
        question = st.text_input(
            "請輸入你的問題：",
            value=st.session_state.get("current_question", ""),
            placeholder="例如：這次旅行的目的地是哪裡？",
            key="question_input"
        )
        
        col_ask, col_clear = st.columns([1, 1])
        
        with col_ask:
            ask_button = st.button("🚀 提問", type="primary", use_container_width=True)
        
        with col_clear:
            if st.button("🗑️ 清空對話", type="secondary", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        # 處理問題
        if ask_button and question.strip():
            # 添加用戶問題到對話歷史
            st.session_state.messages.append({"role": "user", "content": question})
            
            # 生成回答
            with st.spinner("🤔 思考中..."):
                try:
                    answer = st.session_state.rag_engine.query(question)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    error_msg = f"處理問題時發生錯誤: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # 清空輸入並重新載入
            st.session_state.current_question = ""
            st.rerun()
    
    with col2:
        st.header("📊 系統狀態")
        
        if st.session_state.rag_engine:
            status = st.session_state.rag_engine.get_system_status()
            
            # 資料庫狀態
            st.markdown("""
            <div class="status-card">
                <h4>📚 向量資料庫</h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.metric("文檔數量", status['vector_database']['total_documents'])
            st.metric("向量數量", status['vector_database']['total_vectors'])
            
            with st.expander("資料來源詳情"):
                for source, count in status['vector_database']['sources'].items():
                    st.write(f"• {source}: {count} 個片段")
            
            # AI設定
            st.markdown("""
            <div class="status-card">
                <h4>🤖 AI設定</h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**OpenAI**: {'✅ 啟用' if status['openai_enabled'] else '❌ 未啟用'}")
            if status['openai_enabled']:
                st.write(f"**模型**: {status['openai_model']}")
            st.write(f"**嵌入模型**: {status['embedding_model']}")
            
            # 系統參數
            with st.expander("系統參數"):
                for key, value in status['settings'].items():
                    st.write(f"• {key}: {value}")
        
        # 使用說明
        st.header("📖 使用說明")
        st.markdown("""
        1. **提問**: 在左側輸入框中輸入問題
        2. **範例**: 點擊側邊欄的範例問題快速提問
        3. **更新**: 如果Notion內容有變化，點擊更新按鈕
        4. **清空**: 可以清空對話歷史重新開始
        
        💡 **提示**: 問題越具體，回答越準確！
        """)

# 載入設定
settings = Settings()

# 檢查是否有 LINE Bot 設定
if hasattr(settings, 'LINE_CHANNEL_ACCESS_TOKEN') and settings.LINE_CHANNEL_ACCESS_TOKEN:
    try:
        # 使用 LINE Bot SDK v3
        from linebot.v3 import WebhookHandler
        from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
        from linebot.v3.webhooks import MessageEvent, TextMessageContent
        from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest
        
        # 初始化 Flask 應用
        app = Flask(__name__)
        
        # 初始化 Line Bot API v3
        configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
        api_client = ApiClient(configuration)
        line_bot_api = MessagingApi(api_client)
        handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        
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
            except Exception as e:
                abort(400)

            return 'OK'

        @handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            try:
                # 初始化 RAG 系統
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
                
                # 獲取用戶的問題
                user_question = event.message.text
                
                # 呼叫 RAG 問答流程
                response = rag_engine.query(user_question)
                
                # 回傳回應
                reply_message_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
                line_bot_api.reply_message(reply_message_request)
                
            except Exception as e:
                # 錯誤處理
                error_msg = f"抱歉，處理您的問題時發生錯誤：{str(e)}"
                reply_message_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=error_msg)]
                )
                line_bot_api.reply_message(reply_message_request)
                
    except ImportError:
        # 如果沒有安裝 LINE Bot SDK v3，跳過 LINE Bot 功能
        print("⚠️ LINE Bot SDK v3 未安裝，跳過 LINE Bot 功能")
        app = None
        line_bot_api = None
        handler = None
else:
    print("⚠️ 未設定 LINE Bot 憑證，跳過 LINE Bot 功能")
    app = None
    line_bot_api = None
    handler = None

if __name__ == "__main__":
    main()