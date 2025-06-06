import os
import sys
from config.settings import Settings
from core.notion_client import NotionClient
from core.text_processor import TextProcessor
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.rag_engine import RAGEngine

def print_banner():
    """顯示系統橫幅"""
    print("=" * 60)
    print("🤖 Notion RAG 智慧問答系統")
    print("=" * 60)
    print("基於你的Notion文件內容，提供智慧問答服務")
    print("支援繁體中文，使用OpenAI GPT進行回答生成")
    print("=" * 60)

def print_help():
    """顯示幫助資訊"""
    help_text = """
💡 使用說明：
  - 直接輸入問題，系統會基於你的Notion內容回答
  - 輸入 'help' 或 '?' 顯示此幫助
  - 輸入 'status' 檢查系統狀態
  - 輸入 'update' 重新載入Notion內容
  - 輸入 'quit' 或 'exit' 退出系統

📝 問題範例：
  - "這次旅行的目的地是哪裡？"
  - "飛機什麼時候起飛？"
  - "住在哪個飯店？"
  - "第一天有什麼行程？"
  - "有什麼美食推薦？"
"""
    print(help_text)

def initialize_system():
    """初始化系統"""
    try:
        print("🔄 正在初始化系統...")
        
        # 載入設定
        print("📋 載入設定...")
        settings = Settings()
        
        # 建立各個組件
        print("🔧 建立系統組件...")
        notion_client = NotionClient(settings.NOTION_TOKEN)
        text_processor = TextProcessor(settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        embedder = Embedder(settings.EMBEDDING_MODEL)
        vector_store = VectorStore(
            settings.VECTOR_DB_PATH, 
            settings.METADATA_DB_PATH, 
            settings.EMBEDDING_DIMENSION
        )
        
        # 建立RAG引擎
        print("🤖 建立RAG引擎...")
        rag_engine = RAGEngine(
            notion_client, text_processor, embedder, vector_store, settings
        )
        
        # 檢查是否需要處理Notion內容
        status = rag_engine.get_system_status()
        if status['vector_database']['total_documents'] == 0:
            print("📄 首次使用，正在處理Notion內容...")
            success = rag_engine.process_notion_page(settings.NOTION_PAGE_ID)
            if not success:
                raise Exception("Notion內容處理失敗")
            print("✅ Notion內容處理完成")
        else:
            print(f"✅ 已載入 {status['vector_database']['total_documents']} 個文檔片段")
        
        print("🎉 系統初始化完成！")
        return rag_engine
        
    except Exception as e:
        print(f"❌ 系統初始化失敗: {e}")
        print("\n💡 請檢查:")
        print("1. config/.env 檔案是否正確設定")
        print("2. NOTION_TOKEN 和 NOTION_PAGE_ID 是否有效")
        print("3. 網路連接是否正常")
        return None

def handle_special_commands(user_input, rag_engine):
    """處理特殊指令"""
    command = user_input.lower().strip()
    
    if command in ['help', '?', 'h']:
        print_help()
        return True
    
    elif command == 'status':
        print("\n📊 系統狀態:")
        status = rag_engine.get_system_status()
        
        print(f"  📚 向量資料庫:")
        print(f"    - 文檔數量: {status['vector_database']['total_documents']}")
        print(f"    - 向量數量: {status['vector_database']['total_vectors']}")
        print(f"    - 資料來源: {status['vector_database']['sources']}")
        
        print(f"  🤖 AI設定:")
        print(f"    - OpenAI: {'啟用' if status['openai_enabled'] else '未啟用'}")
        if status['openai_enabled']:
            print(f"    - 模型: {status['openai_model']}")
        print(f"    - 嵌入模型: {status['embedding_model']}")
        
        print(f"  ⚙️ 系統參數:")
        for key, value in status['settings'].items():
            print(f"    - {key}: {value}")
        
        return True
    
    elif command == 'update':
        print("\n🔄 重新載入Notion內容...")
        success = rag_engine.update_notion_content()
        if success:
            print("✅ Notion內容更新完成")
        else:
            print("❌ Notion內容更新失敗")
        return True
    
    elif command in ['quit', 'exit', 'q']:
        print("\n👋 感謝使用 Notion RAG 系統！")
        return False
    
    return None

def main():
    """主程式"""
    # 設定環境變數（消除警告）
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    print_banner()
    
    # 初始化系統
    rag_engine = initialize_system()
    if not rag_engine:
        sys.exit(1)
    
    print_help()
    
    # 主要問答循環
    print("\n🚀 系統就緒！請開始提問...")
    
    while True:
        try:
            # 獲取用戶輸入
            user_input = input("\n❓ 請輸入你的問題: ").strip()
            
            if not user_input:
                continue
            
            # 處理特殊指令
            command_result = handle_special_commands(user_input, rag_engine)
            if command_result is False:  # quit指令
                break
            elif command_result is True:  # 其他指令
                continue
            
            # 處理一般問題
            print("\n🤔 思考中...")
            answer = rag_engine.query(user_input)
            
            print("\n💡 回答:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 系統中斷，再見！")
            break
        except Exception as e:
            print(f"\n❌ 處理問題時發生錯誤: {e}")
            print("請重試或輸入 'help' 查看使用說明")

if __name__ == "__main__":
    main()