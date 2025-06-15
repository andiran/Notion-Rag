import sys
import os
import traceback
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading
import time

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
            ],
            "update": [
                "更新", "update", "更新內容", "更新notion"
            ],
            "confirm": [
                "確定", "是", "yes", "y", "確認", "ok"
            ],
            "cancel": [
                "取消", "否", "no", "n", "不要", "cancel"
            ]
        }
        
        # 會話狀態管理
        self.pending_updates = {}  # {user_id: {"timestamp": datetime, "confirmed": bool}}
        self.update_lock = threading.Lock()  # 確保同時只有一個更新操作
        self.is_updating = False  # 全域更新狀態
        self.update_timeout = 300  # 確認狀態超時時間（5分鐘）
        
        # 啟動狀態清理定時器
        self._start_cleanup_timer()
        
        print("🤖 LINE Bot 處理器已初始化")
    
    def _start_cleanup_timer(self):
        """啟動定時清理過期的確認狀態"""
        def cleanup_expired_confirmations():
            while True:
                try:
                    current_time = datetime.now()
                    expired_users = []
                    
                    for user_id, status in self.pending_updates.items():
                        if current_time - status["timestamp"] > timedelta(seconds=self.update_timeout):
                            expired_users.append(user_id)
                    
                    for user_id in expired_users:
                        del self.pending_updates[user_id]
                        print(f"🧹 清理過期的確認狀態: {user_id}")
                    
                    time.sleep(60)  # 每分鐘檢查一次
                except Exception as e:
                    print(f"❌ 清理確認狀態時發生錯誤: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_expired_confirmations, daemon=True)
        cleanup_thread.start()
        print("🧹 狀態清理定時器已啟動")

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
        
        # 檢查是否為確認更新的回覆
        if user_id in self.pending_updates:
            return self._handle_update_confirmation(user_id, message)
        
        # 招呼語
        if any(greeting in message for greeting in self.predefined_responses["greetings"]):
            # 記錄用戶訊息
            self.conversation_memory.add_message(user_id, "user", message)
            
            response = """您好！我是基於您的 Notion 文件的智慧問答助手 🤖

我可以幫您：
📚 回答 Notion 文件相關問題
💭 記住我們的對話內容
🔍 根據上下文理解您的問題
🔄 更新 Notion 內容（輸入「更新」）

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
   • 「更新」- 更新 Notion 內容
   • 「強制更新」- 跳過確認直接更新（管理員）

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
        
        # 更新指令
        if any(update_cmd in message_lower for update_cmd in self.predefined_responses["update"]):
            return self._handle_update_request(user_id, message)
        
        # 強制更新指令（管理員功能）
        if "強制更新" in message or "force update" in message_lower:
            return self._handle_force_update(user_id)
        
        # 狀態查詢
        if "狀態" in message or "status" in message_lower:
            try:
                stats = self.conversation_memory.get_conversation_stats()
                rag_status = self.rag_engine.get_system_status()
                
                update_status = "🔄 更新中" if self.is_updating else "✅ 空閒"
                pending_count = len(self.pending_updates)
                
                response = f"""📊 系統狀態：

💬 對話統計：
• 總對話數：{stats['total_conversations']}
• 活躍對話：{stats['active_conversations']}
• 總訊息數：{stats['total_messages']}
• 記憶體使用：{stats['memory_usage_mb']:.2f} MB

🗄️ 知識庫：
• 文件片段：{rag_status['vector_database']['total_documents']}
• 資料來源：{len(rag_status['vector_database'].get('source_stats', {}))}

🔄 更新狀態：{update_status}
• 等待確認：{pending_count} 個請求

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
    
    def _handle_update_request(self, user_id: str, message: str) -> str:
        """
        處理更新請求（第一階段：發送確認訊息）
        
        Args:
            user_id: 用戶 ID
            message: 訊息內容
            
        Returns:
            確認訊息
        """
        # 檢查是否已經在更新中
        if self.is_updating:
            return """⚠️ 系統目前正在進行更新，請稍後再試。

更新期間問答功能可能會受到影響，請耐心等候更新完成。"""
        
        # 記錄用戶訊息
        self.conversation_memory.add_message(user_id, "user", message)
        
        # 設置等待確認狀態
        self.pending_updates[user_id] = {
            "timestamp": datetime.now(),
            "confirmed": False
        }
        
        response = """⚠️ 確認更新 Notion 內容

更新將會：
• 重新載入您的 Notion 頁面內容
• 清空現有的知識庫資料
• 重新建立向量索引

此過程需要 1-3 分鐘，期間問答功能可能暫時受影響。

請回覆「確定」或「是」來確認更新
回覆「取消」或「否」來取消操作

⏰ 此確認將在 5 分鐘後自動過期"""
        
        # 記錄助手回應
        self.conversation_memory.add_message(user_id, "assistant", response)
        
        print(f"📋 用戶 {user_id} 請求更新，等待確認")
        return response
    
    def _handle_update_confirmation(self, user_id: str, message: str) -> str:
        """
        處理更新確認回覆（第二階段：處理確認）
        
        Args:
            user_id: 用戶 ID
            message: 確認訊息
            
        Returns:
            處理結果
        """
        message_lower = message.lower()
        
        # 檢查確認狀態是否過期
        if user_id not in self.pending_updates:
            return "⏰ 確認請求已過期，請重新輸入「更新」來開始更新流程。"
        
        # 記錄用戶回覆
        self.conversation_memory.add_message(user_id, "user", message)
        
        # 處理確認回覆
        if any(confirm in message_lower for confirm in self.predefined_responses["confirm"]):
            # 用戶確認更新
            del self.pending_updates[user_id]  # 清除確認狀態
            return self._execute_notion_update(user_id)
            
        elif any(cancel in message_lower for cancel in self.predefined_responses["cancel"]):
            # 用戶取消更新
            del self.pending_updates[user_id]  # 清除確認狀態
            response = "❌ 已取消更新操作。如需更新，請重新輸入「更新」指令。"
            self.conversation_memory.add_message(user_id, "assistant", response)
            return response
        else:
            # 無效回覆
            response = """❓ 請回覆「確定」或「是」來確認更新
或回覆「取消」或「否」來取消操作

⏰ 此確認將在 5 分鐘後自動過期"""
            return response
    
    def _handle_force_update(self, user_id: str) -> str:
        """
        處理強制更新指令（管理員功能，跳過確認）
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            更新結果
        """
        # 檢查是否已經在更新中
        if self.is_updating:
            return """⚠️ 系統目前正在進行更新，請稍後再試。"""
        
        print(f"🚨 用戶 {user_id} 執行強制更新")
        return self._execute_notion_update(user_id, is_force=True)
    
    def _execute_notion_update(self, user_id: str, is_force: bool = False) -> str:
        """
        執行 Notion 內容更新
        
        Args:
            user_id: 用戶 ID
            is_force: 是否為強制更新
            
        Returns:
            更新結果訊息
        """
        try:
            # 獲取更新鎖
            with self.update_lock:
                if self.is_updating:
                    return "⚠️ 系統目前正在進行更新，請稍後再試。"
                
                self.is_updating = True
                print(f"🔄 開始執行 Notion 更新 - 用戶: {user_id}, 強制: {is_force}")
            
            # 發送開始更新的訊息
            start_message = "🔄 開始更新 Notion 內容，請稍候...\n\n這可能需要 1-3 分鐘的時間。"
            self.conversation_memory.add_message(user_id, "assistant", start_message)
            
            # 記錄更新開始時間
            update_start_time = datetime.now()
            
            # 執行實際更新
            try:
                if hasattr(self.rag_engine, 'update_notion_content'):
                    update_result = self.rag_engine.update_notion_content()
                else:
                    # 如果沒有 update_notion_content 方法，使用其他可用的更新方法
                    # 這裡需要根據實際的 RAG 引擎 API 調整
                    update_result = {"success": False, "error": "更新方法未實作"}
                
                # 計算更新時間
                update_duration = datetime.now() - update_start_time
                duration_str = f"{update_duration.total_seconds():.0f} 秒"
                if update_duration.total_seconds() > 60:
                    minutes = int(update_duration.total_seconds() // 60)
                    seconds = int(update_duration.total_seconds() % 60)
                    duration_str = f"{minutes} 分 {seconds} 秒"
                
                # 處理更新結果 - 確保 update_result 是字典類型
                if not isinstance(update_result, dict):
                    # 如果返回的是布林值或其他類型，轉換為標準格式
                    if update_result is True:
                        update_result = {"success": True, "stats": {}}
                    elif update_result is False:
                        update_result = {"success": False, "error": "更新失敗"}
                    else:
                        update_result = {"success": False, "error": f"未預期的返回值類型: {type(update_result)}"}
                
                # 安全地獲取更新結果
                success = update_result.get("success", False)
                
                if success:
                    # 更新成功
                    stats = update_result.get("stats", {})
                    documents_count = stats.get("documents", "未知") if isinstance(stats, dict) else "未知"
                    
                    response = f"""✅ Notion 內容更新完成！

📊 更新統計：
• 載入文件：{documents_count} 個片段
• 處理時間：{duration_str}
• 狀態：成功

現在可以詢問最新的內容了！"""
                    
                    print(f"✅ Notion 更新成功 - 用戶: {user_id}")
                else:
                    # 更新失敗
                    error_msg = update_result.get("error", "未知錯誤") if isinstance(update_result, dict) else "未知錯誤"
                    response = f"""❌ Notion 內容更新失敗

錯誤原因：{error_msg}
處理時間：{duration_str}

請稍後再試，或聯繫管理員協助處理。"""
                    
                    print(f"❌ Notion 更新失敗 - 用戶: {user_id}, 錯誤: {error_msg}")
                
            except Exception as update_error:
                # 更新過程中發生異常
                duration_str = f"{(datetime.now() - update_start_time).total_seconds():.0f} 秒"
                response = f"""❌ 更新過程中發生錯誤

錯誤訊息：{str(update_error)}
處理時間：{duration_str}

請稍後再試，或聯繫管理員協助處理。"""
                
                print(f"❌ Notion 更新異常 - 用戶: {user_id}, 異常: {update_error}")
                traceback.print_exc()
            
            # 記錄更新結果
            self.conversation_memory.add_message(user_id, "assistant", response)
            return response
            
        except Exception as e:
            error_response = f"❌ 執行更新時發生系統錯誤：{str(e)}"
            print(f"❌ 系統錯誤 - 更新執行失敗: {e}")
            traceback.print_exc()
            return error_response
        
        finally:
            # 確保釋放更新鎖
            self.is_updating = False
            print(f"🔓 更新操作完成，釋放更新鎖")

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
                "update_status": {
                    "is_updating": self.is_updating,
                    "pending_updates": len(self.pending_updates),
                    "pending_users": list(self.pending_updates.keys())
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 