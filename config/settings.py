import os
from typing import Optional

class Settings:
    """系統設定管理"""
    
    def __init__(self):
        # 從環境變數或設定檔讀取Notion設定
        self.NOTION_TOKEN = self._get_setting("NOTION_TOKEN")
        raw_page_id = self._get_setting("NOTION_PAGE_ID")
        self.NOTION_PAGE_ID = self._process_page_id(raw_page_id)
        
        # 檢查必要設定
        if not self.NOTION_TOKEN:
            raise ValueError("請設定 NOTION_TOKEN 環境變數或在 config/.env 檔案中設定")
        if not self.NOTION_PAGE_ID:
            raise ValueError("請設定 NOTION_PAGE_ID 環境變數或在 config/.env 檔案中設定（可使用完整URL）")
        
        # 向量嵌入設定
        self.EMBEDDING_MODEL = self._get_setting("EMBEDDING_MODEL") or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.EMBEDDING_DIMENSION = int(self._get_setting("EMBEDDING_DIMENSION") or "384")
        
        # 文本分割設定
        self.CHUNK_SIZE = int(self._get_setting("CHUNK_SIZE") or "500")
        self.CHUNK_OVERLAP = int(self._get_setting("CHUNK_OVERLAP") or "50")
        
        # 檢索設定
        self.TOP_K = int(self._get_setting("TOP_K") or "5")
        self.SIMILARITY_THRESHOLD = float(self._get_setting("SIMILARITY_THRESHOLD") or "0.7")
        
        # LLM設定（可選擇OpenAI或本地模型）
        self.USE_OPENAI = self._get_setting("USE_OPENAI", "true").lower() == "true"
        self.OPENAI_API_KEY = self._get_setting("OPENAI_API_KEY")
        self.OPENAI_MODEL = self._get_setting("OPENAI_MODEL") or "gpt-3.5-turbo"
        
        # 資料庫路徑
        self.VECTOR_DB_PATH = self._get_setting("VECTOR_DB_PATH") or "./vector_db"
        self.METADATA_DB_PATH = self._get_setting("METADATA_DB_PATH") or "./metadata.db"
        self.CACHE_PATH = self._get_setting("CACHE_PATH") or "./cache"
        
        # 更新設定
        self.UPDATE_INTERVAL = int(self._get_setting("UPDATE_INTERVAL") or "3600")  # 秒（1小時）
        
        # LINE Bot 設定
        self.LINE_CHANNEL_SECRET = self._get_setting("LINE_CHANNEL_SECRET")
        self.LINE_CHANNEL_ACCESS_TOKEN = self._get_setting("LINE_CHANNEL_ACCESS_TOKEN")
        
        # 對話記憶設定
        self.CONVERSATION_TIMEOUT_MINUTES = int(self._get_setting("CONVERSATION_TIMEOUT_MINUTES") or "30")
        self.MAX_CONVERSATION_LENGTH = int(self._get_setting("MAX_CONVERSATION_LENGTH") or "20")
        self.CLEANUP_INTERVAL_MINUTES = int(self._get_setting("CLEANUP_INTERVAL_MINUTES") or "5")
        self.MAX_CONTEXT_TOKENS = int(self._get_setting("MAX_CONTEXT_TOKENS") or "2000")
        
        # Redis 設定（可選，用於分佈式對話記憶）
        self.REDIS_URL = self._get_setting("REDIS_URL")
        self.USE_REDIS = self._get_setting("USE_REDIS", "false").lower() == "true"
        
        # Flask 伺服器設定
        self.FLASK_HOST = self._get_setting("FLASK_HOST") or "0.0.0.0"
        self.FLASK_PORT = int(self._get_setting("FLASK_PORT") or "5000")
        self.FLASK_DEBUG = self._get_setting("FLASK_DEBUG", "false").lower() == "true"
        
        # 檢查 LINE Bot 設定完整性
        self.LINE_BOT_ENABLED = bool(self.LINE_CHANNEL_SECRET and self.LINE_CHANNEL_ACCESS_TOKEN)
        
        if self.LINE_BOT_ENABLED:
            print("✅ LINE Bot 設定已啟用")
        else:
            print("⚠️ LINE Bot 設定未完整，將僅啟用基本功能")
    
    def _process_page_id(self, page_id_input):
        """處理頁面ID（支援URL）"""
        if not page_id_input:
            return None
        
        page_id = str(page_id_input).strip()
        
        # 如果是URL，提取ID
        if 'notion.so' in page_id:
            if '?' in page_id:
                page_id = page_id.split('?')[0]
            parts = page_id.split('/')
            last_part = parts[-1]
            if len(last_part) >= 32:
                page_id = last_part[-32:]
        
        # 格式化為UUID
        clean_id = page_id.replace('-', '')
        if len(clean_id) == 32:
            formatted = f"{clean_id[0:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:32]}"
            return formatted.lower()
        
        return page_id
    
    def _get_setting(self, key: str, default: str = None) -> Optional[str]:
        """從環境變數或config/.env檔案讀取設定"""
        # 優先從環境變數讀取
        value = os.getenv(key)
        if value:
            return value
        
        # 嘗試從config/.env檔案讀取
        try:
            from dotenv import load_dotenv
            # 載入config目錄下的.env檔案
            config_env_path = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(config_env_path)
            value = os.getenv(key)
            if value:
                return value
        except ImportError:
            # 如果沒有安裝python-dotenv，手動讀取
            config_env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(config_env_path):
                with open(config_env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            env_key, env_value = line.split('=', 1)
                            if env_key.strip() == key:
                                return env_value.strip().strip('"').strip("'")
        
        return default
    
    def get_conversation_settings(self) -> dict:
        """獲取對話記憶相關設定"""
        return {
            'timeout_minutes': self.CONVERSATION_TIMEOUT_MINUTES,
            'max_conversation_length': self.MAX_CONVERSATION_LENGTH,
            'cleanup_interval_minutes': self.CLEANUP_INTERVAL_MINUTES,
            'max_context_tokens': self.MAX_CONTEXT_TOKENS,
            'use_redis': self.USE_REDIS,
            'redis_url': self.REDIS_URL
        }
    
    def validate_line_bot_settings(self) -> bool:
        """驗證 LINE Bot 設定是否完整"""
        required_settings = [
            ('LINE_CHANNEL_ACCESS_TOKEN', self.LINE_CHANNEL_ACCESS_TOKEN),
            ('LINE_CHANNEL_SECRET', self.LINE_CHANNEL_SECRET)
        ]
        
        missing_settings = [name for name, value in required_settings if not value]
        
        if missing_settings:
            print(f"❌ 缺少必要的 LINE Bot 設定: {', '.join(missing_settings)}")
            return False
        
        return True