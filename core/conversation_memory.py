import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import gc
import json

class ConversationMemory:
    """對話記憶管理器 - 支援連續對話上下文"""
    
    def __init__(self, timeout_minutes: int = 30, max_conversation_length: int = 20, 
                 cleanup_interval_minutes: int = 5, max_context_tokens: int = 2000):
        """
        初始化對話記憶管理器
        
        Args:
            timeout_minutes: 對話逾時時間（分鐘）
            max_conversation_length: 最大對話長度（訊息數）
            cleanup_interval_minutes: 清理間隔（分鐘）
            max_context_tokens: 最大上下文 token 數
        """
        self.timeout_minutes = timeout_minutes
        self.max_conversation_length = max_conversation_length
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.max_context_tokens = max_context_tokens
        
        # 儲存對話資料：user_id -> conversation_data
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # 線程鎖，確保線程安全
        self._lock = threading.RLock()
        
        # 啟動背景清理任務
        self._cleanup_thread = None
        self._stop_cleanup = False
        self._start_cleanup_thread()
        
        print(f"✅ 對話記憶管理器已初始化")
        print(f"   - 逾時時間: {timeout_minutes} 分鐘")
        print(f"   - 最大對話長度: {max_conversation_length} 則訊息")
        print(f"   - 清理間隔: {cleanup_interval_minutes} 分鐘")
        print(f"   - 最大上下文: {max_context_tokens} tokens")
    
    def add_message(self, user_id: str, role: str, content: str) -> None:
        """
        新增對話訊息
        
        Args:
            user_id: 使用者 ID
            role: 角色 ('user' 或 'assistant')
            content: 訊息內容
        """
        with self._lock:
            current_time = datetime.now()
            
            # 如果是新用戶或對話已過期，建立新對話
            if user_id not in self.conversations or self._is_conversation_expired(user_id):
                self.conversations[user_id] = {
                    'messages': deque(maxlen=self.max_conversation_length),
                    'created_at': current_time,
                    'last_active': current_time
                }
                print(f"🆕 為用戶 {user_id} 建立新對話")
            
            # 新增訊息
            message = {
                'role': role,
                'content': content,
                'timestamp': current_time
            }
            
            self.conversations[user_id]['messages'].append(message)
            self.conversations[user_id]['last_active'] = current_time
            
            print(f"💬 用戶 {user_id} 新增 {role} 訊息: {content[:50]}...")
    
    def get_conversation(self, user_id: str) -> List[Dict[str, Any]]:
        """
        取得用戶的對話歷程
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            對話訊息列表
        """
        with self._lock:
            if user_id not in self.conversations or self._is_conversation_expired(user_id):
                return []
            
            return list(self.conversations[user_id]['messages'])
    
    def get_context_for_rag(self, user_id: str) -> str:
        """
        取得適合 RAG 引擎的上下文字串
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            格式化的上下文字串
        """
        with self._lock:
            messages = self.get_conversation(user_id)
            
            if not messages:
                return ""
            
            # 建立上下文字串
            context_parts = []
            total_tokens = 0
            
            # 從最新的訊息開始，逆向添加到上下文
            for message in reversed(messages):
                role_label = "用戶" if message['role'] == 'user' else "助手"
                content = message['content']
                
                # 簡單的 token 估算（中文字符 * 1.5）
                estimated_tokens = len(content) * 1.5
                
                if total_tokens + estimated_tokens > self.max_context_tokens:
                    break
                
                context_parts.insert(0, f"{role_label}: {content}")
                total_tokens += estimated_tokens
            
            if context_parts:
                context = "以下是對話歷程：\n" + "\n".join(context_parts) + "\n\n"
                print(f"📋 為用戶 {user_id} 建立上下文，包含 {len(context_parts)} 則訊息")
                return context
            
            return ""
    
    def clear_conversation(self, user_id: str) -> bool:
        """
        清除特定用戶的對話記憶
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            是否成功清除
        """
        with self._lock:
            if user_id in self.conversations:
                del self.conversations[user_id]
                print(f"🗑️ 已清除用戶 {user_id} 的對話記憶")
                return True
            return False
    
    def cleanup_expired(self) -> int:
        """
        清理過期的對話
        
        Returns:
            清理的對話數量
        """
        with self._lock:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, conversation in self.conversations.items():
                if self._is_conversation_expired(user_id, current_time):
                    expired_users.append(user_id)
            
            # 清理過期對話
            for user_id in expired_users:
                del self.conversations[user_id]
            
            if expired_users:
                print(f"🧹 清理了 {len(expired_users)} 個過期對話")
                # 執行記憶體回收
                gc.collect()
            
            return len(expired_users)
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        取得對話統計資訊
        
        Returns:
            統計資訊字典
        """
        with self._lock:
            total_conversations = len(self.conversations)
            total_messages = sum(len(conv['messages']) for conv in self.conversations.values())
            
            # 計算活躍對話（最近 5 分鐘內有活動）
            active_cutoff = datetime.now() - timedelta(minutes=5)
            active_conversations = sum(
                1 for conv in self.conversations.values() 
                if conv['last_active'] > active_cutoff
            )
            
            return {
                'total_conversations': total_conversations,
                'active_conversations': active_conversations,
                'total_messages': total_messages,
                'average_messages_per_conversation': total_messages / max(total_conversations, 1),
                'memory_usage_mb': self._estimate_memory_usage()
            }
    
    def _is_conversation_expired(self, user_id: str, current_time: Optional[datetime] = None) -> bool:
        """檢查對話是否已過期"""
        if user_id not in self.conversations:
            return True
        
        if current_time is None:
            current_time = datetime.now()
        
        last_active = self.conversations[user_id]['last_active']
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        
        return current_time - last_active > timeout_delta
    
    def _estimate_memory_usage(self) -> float:
        """估算記憶體使用量（MB）"""
        try:
            # 簡單估算：將對話資料轉為 JSON 計算大小
            data_size = len(json.dumps(
                {k: {
                    'messages': [{'role': m['role'], 'content': m['content']} for m in v['messages']],
                    'created_at': v['created_at'].isoformat(),
                    'last_active': v['last_active'].isoformat()
                } for k, v in self.conversations.items()}, 
                ensure_ascii=False
            ).encode('utf-8'))
            
            return data_size / (1024 * 1024)  # 轉換為 MB
        except Exception:
            return 0.0
    
    def _start_cleanup_thread(self):
        """啟動背景清理線程"""
        def cleanup_worker():
            while not self._stop_cleanup:
                try:
                    time.sleep(self.cleanup_interval_minutes * 60)  # 轉換為秒
                    if not self._stop_cleanup:
                        self.cleanup_expired()
                except Exception as e:
                    print(f"❌ 背景清理任務錯誤: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        print(f"🔄 背景清理任務已啟動，間隔: {self.cleanup_interval_minutes} 分鐘")
    
    def shutdown(self):
        """關閉記憶管理器"""
        self._stop_cleanup = True
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        print("🛑 對話記憶管理器已關閉")
    
    def __del__(self):
        """析構函數"""
        try:
            self.shutdown()
        except Exception:
            pass 