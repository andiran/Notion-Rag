import sys
import os
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

# 將專案根目錄加入路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.conversation_memory import ConversationMemory
from core.enhanced_rag_engine import EnhancedRAGEngine

# LINE Bot SDK v3
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage as LineTextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

class LineBotHandler:
    """LINE Bot 訊息處理器 - 整合對話記憶與 RAG 引擎"""
    
    def __init__(self, rag_engine: EnhancedRAGEngine, conversation_memory: ConversationMemory, 
                 line_channel_access_token: str):
        """
        初始化 LINE Bot 處理器
        
        Args:
            rag_engine: 增強版 RAG 引擎
            conversation_memory: 對話記憶管理器
            line_channel_access_token: LINE Channel Access Token
        """
        self.rag_engine = rag_engine
        self.conversation_memory = conversation_memory
        
        # 初始化 LINE Bot API
        try:
            configuration = Configuration(access_token=line_channel_access_token)
            api_client = ApiClient(configuration)
            self.line_bot_api = MessagingApi(api_client)
            print("✅ LINE Bot API 初始化成功")
        except Exception as e:
            print(f"❌ LINE Bot API 初始化失敗: {e}")
            raise
        
        # 預定義回應
        self.predefined_responses = {
            "greetings": [
                "你好", "hello", "hi", "嗨", "Hello", "Hi", "哈囉", "早安", "午安", "晚安"
            ],
            "help": [
                "幫助", "help", "指令", "怎麼用", "使用方法", "說明"
            ],
            "clear": [
                "清除記憶", "重新開始", "清空對話", "新對話"
            ]
        }
        
        print("🤖 LINE Bot 處理器已初始化")
    
    def handle_text_message(self, event: MessageEvent) -> None:
        """
        處理文字訊息事件
        
        Args:
            event: LINE 訊息事件
        """
        try:
            # 獲取用戶資訊
            user_id = event.source.user_id
            user_message = event.message.text.strip()
            
            print(f"📩 收到用戶 {user_id} 的訊息: {user_message}")
            
            # 檢查是否為特殊指令
            response = self._handle_special_commands(user_id, user_message)
            
            if response is None:
                # 一般問答處理
                response = self._handle_question(user_id, user_message)
            
            # 發送回應
            self._send_reply(event.reply_token, response)
            
            print(f"✅ 已回覆用戶 {user_id}")
            
        except Exception as e:
            print(f"❌ 處理訊息時發生錯誤: {e}")
            traceback.print_exc()
            
            # 發送錯誤訊息
            error_response = "抱歉，處理您的訊息時發生錯誤，請稍後再試。"
            try:
                self._send_reply(event.reply_token, error_response)
            except Exception as reply_error:
                print(f"❌ 發送錯誤訊息失敗: {reply_error}")
    
    def _handle_special_commands(self, user_id: str, message: str) -> Optional[str]:
        """
        處理特殊指令
        
        Args:
            user_id: 用戶 ID
            message: 訊息內容
            
        Returns:
            指令回應或 None（如果不是特殊指令）
        """
        message_lower = message.lower()
        
        # 招呼語
        if any(greeting in message for greeting in self.predefined_responses["greetings"]):
            # 記錄用戶訊息
            self.conversation_memory.add_message(user_id, "user", message)
            
            response = """您好！我是基於您的 Notion 文件的智慧問答助手 🤖

我可以幫您：
📚 回答 Notion 文件相關問題
💭 記住我們的對話內容
🔍 根據上下文理解您的問題

請隨時向我提問！"""
            
            # 記錄助手回應
            self.conversation_memory.add_message(user_id, "assistant", response)
            return response
        
        # 幫助指令
        if any(help_cmd in message_lower for help_cmd in self.predefined_responses["help"]):
            response = """📖 使用說明：

🔹 直接向我提問關於 Notion 文件的任何問題
🔹 我會記住我們的對話，可以理解上下文
🔹 支援的指令：
   • 「清除記憶」- 重新開始對話
   • 「狀態」- 查看系統狀態
   • 「統計」- 查看對話統計

💡 小貼士：您可以問「這個怎麼做？」之類需要上下文的問題！"""
            
            # 不記錄幫助指令的對話
            return response
        
        # 清除記憶指令
        if any(clear_cmd in message for clear_cmd in self.predefined_responses["clear"]):
            cleared = self.conversation_memory.clear_conversation(user_id)
            if cleared:
                return "✅ 已清除對話記憶，我們重新開始吧！"
            else:
                return "ℹ️ 沒有找到需要清除的對話記憶。"
        
        # 狀態查詢
        if "狀態" in message or "status" in message_lower:
            try:
                stats = self.conversation_memory.get_conversation_stats()
                rag_status = self.rag_engine.get_system_status()
                
                response = f"""📊 系統狀態：

💬 對話統計：
• 總對話數：{stats['total_conversations']}
• 活躍對話：{stats['active_conversations']}
• 總訊息數：{stats['total_messages']}
• 記憶體使用：{stats['memory_usage_mb']:.2f} MB

🗄️ 知識庫：
• 文件片段：{rag_status['vector_database']['total_documents']}
• 資料來源：{len(rag_status['vector_database'].get('source_stats', {}))}

✅ 系統運行正常！"""
                
                return response
            except Exception as e:
                return f"❌ 獲取系統狀態時發生錯誤：{str(e)}"
        
        # 統計查詢
        if "統計" in message:
            try:
                stats = self.conversation_memory.get_conversation_stats()
                conversation = self.conversation_memory.get_conversation(user_id)
                
                response = f"""📈 您的對話統計：

💭 本次對話：
• 訊息數：{len(conversation)}
• 開始時間：{conversation[0]['timestamp'].strftime('%H:%M') if conversation else '無'}

🌐 全域統計：
• 總對話數：{stats['total_conversations']}
• 活躍對話：{stats['active_conversations']}
• 平均對話長度：{stats['average_messages_per_conversation']:.1f} 則訊息"""
                
                return response
            except Exception as e:
                return f"❌ 獲取統計資訊時發生錯誤：{str(e)}"
        
        return None
    
    def _handle_question(self, user_id: str, question: str) -> str:
        """
        處理一般問答
        
        Args:
            user_id: 用戶 ID
            question: 問題內容
            
        Returns:
            回答內容
        """
        try:
            # 記錄用戶問題
            self.conversation_memory.add_message(user_id, "user", question)
            
            # 獲取對話上下文
            conversation_context = self.conversation_memory.get_context_for_rag(user_id)
            
            # 使用 RAG 引擎處理問題
            print(f"🔍 開始處理用戶 {user_id} 的問題...")
            answer = self.rag_engine.query_with_context(
                question=question,
                conversation_context=conversation_context,
                user_id=user_id
            )
            
            # 確保回應長度適合 LINE
            answer = self._format_line_response(answer)
            
            # 記錄助手回應
            self.conversation_memory.add_message(user_id, "assistant", answer)
            
            return answer
            
        except Exception as e:
            print(f"❌ 處理問答時發生錯誤: {e}")
            traceback.print_exc()
            
            error_response = "抱歉，處理您的問題時遇到了技術問題。請嘗試重新表述您的問題，或稍後再試。"
            
            # 仍然記錄用戶問題，但不記錄錯誤回應
            return error_response
    
    def _format_line_response(self, response: str) -> str:
        """
        格式化 LINE 回應（處理長度限制和格式）
        
        Args:
            response: 原始回應
            
        Returns:
            格式化後的回應
        """
        # LINE 訊息長度限制（實際約 5000 字元，我們保守設為 2000）
        max_length = 2000
        
        if len(response) <= max_length:
            return response
        
        # 如果太長，嘗試智慧截斷
        truncated = response[:max_length - 100]  # 保留 100 字元給後綴
        
        # 找到最後一個完整句子的結尾
        last_sentence_end = max(
            truncated.rfind('。'),
            truncated.rfind('！'),
            truncated.rfind('？'),
            truncated.rfind('\n\n')
        )
        
        if last_sentence_end > max_length // 2:  # 如果截斷點不會太短
            truncated = truncated[:last_sentence_end + 1]
        
        # 添加截斷提示
        truncated += "\n\n📝 回答內容較長，已省略部分內容。如需了解更多，請繼續提問相關問題。"
        
        return truncated
    
    def _send_reply(self, reply_token: str, message: str) -> None:
        """
        發送回覆訊息
        
        Args:
            reply_token: 回覆 token
            message: 訊息內容
        """
        try:
            reply_message_request = ReplyMessageRequest(
                reply_token=reply_token,
                messages=[LineTextMessage(text=message)]
            )
            self.line_bot_api.reply_message(reply_message_request)
            print(f"📤 回覆訊息已發送: {message[:50]}...")
            
        except Exception as e:
            print(f"❌ 發送回覆失敗: {e}")
            raise
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """
        獲取處理器統計資訊
        
        Returns:
            統計資訊字典
        """
        try:
            conversation_stats = self.conversation_memory.get_conversation_stats()
            rag_status = self.rag_engine.get_system_status()
            
            return {
                "conversation_memory": conversation_stats,
                "rag_engine": rag_status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 