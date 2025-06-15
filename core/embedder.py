from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import torch

class Embedder:
    """向量嵌入器"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", batch_size: int = 16):
        self.model_name = model_name
        self.batch_size = batch_size
        print(f"🔄 載入嵌入模型: {model_name}")
        print(f"📦 批次大小: {batch_size}")
        
        # 檢查設備 (Render 環境通常只有 CPU)
        self.device = "cpu"  # 強制使用 CPU 以避免記憶體問題
        if torch.cuda.is_available():
            print("🚀 CUDA 可用，但在 Render 環境中使用 CPU 以節省記憶體")
        print(f"🖥️ 使用設備: {self.device}")
        
        try:
            # 載入模型時使用記憶體最佳化設定
            self.model = SentenceTransformer(model_name, device=self.device)
            print(f"✅ 模型載入成功")
            
            # 獲取模型資訊
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            print(f"📏 嵌入維度: {self.embedding_dimension}")
            
            # Render 環境記憶體最佳化
            import os
            if os.getenv("RENDER_DEPLOYMENT", "false").lower() == "true":
                print("🌐 Render 環境檢測到，執行記憶體最佳化...")
                self._optimize_for_render()
            
        except Exception as e:
            print(f"❌ 模型載入失敗: {e}")
            raise
    
    def encode(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """將文本列表編碼為向量"""
        if not texts:
            return np.zeros((0, self.embedding_dimension), dtype=np.float32)
        print(f"🔄 編碼 {len(texts)} 個文本片段...")
        try:
            # 過濾空文本
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                print("⚠️ 沒有有效的文本可以編碼")
                return np.zeros((0, self.embedding_dimension), dtype=np.float32)
            
            # 編碼文本 (使用動態批次大小)
            embeddings = self.model.encode(
                valid_texts, 
                convert_to_numpy=True,
                show_progress_bar=show_progress,
                batch_size=self.batch_size,  # 使用實例變數
                normalize_embeddings=True   # 預先正規化以節省後續計算
            )
            
            # 強制型別與 shape
            embeddings = np.asarray(embeddings, dtype=np.float32)
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            print(f"✅ 編碼完成，形狀: {embeddings.shape}")
            
            # Render 環境下執行記憶體清理
            import os
            if os.getenv("RENDER_DEPLOYMENT", "false").lower() == "true":
                import gc
                gc.collect()
            
            return embeddings
        except Exception as e:
            print(f"❌ 編碼失敗: {e}")
            return np.zeros((0, self.embedding_dimension), dtype=np.float32)
    
    def encode_single(self, text: str) -> np.ndarray:
        """將單個文本編碼為向量"""
        if not text.strip():
            return np.zeros((self.embedding_dimension,), dtype=np.float32)
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            embedding = np.asarray(embedding, dtype=np.float32)
            embedding = embedding.reshape(-1)
            return embedding
        except Exception as e:
            print(f"❌ 單文本編碼失敗: {e}")
            return np.zeros((self.embedding_dimension,), dtype=np.float32)
    
    def encode_query(self, query: str) -> np.ndarray:
        """編碼查詢文本（與encode_single相同，但語義上更清楚）"""
        return self.encode_single(query)
    
    def get_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """計算兩個向量的餘弦相似度"""
        try:
            # 正規化向量
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 計算餘弦相似度
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            print(f"❌ 相似度計算失敗: {e}")
            return 0.0
    
    def test_embedding(self, test_text: str = "這是一個測試句子") -> bool:
        """測試嵌入功能是否正常"""
        try:
            print(f"🧪 測試嵌入功能...")
            print(f"測試文本: {test_text}")
            
            embedding = self.encode_single(test_text)
            
            print(f"✅ 測試成功")
            print(f"嵌入形狀: {embedding.shape}")
            print(f"嵌入範圍: [{embedding.min():.4f}, {embedding.max():.4f}]")
            
            return True
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            return False
    
    def _optimize_for_render(self):
        """Render 環境記憶體最佳化"""
        try:
            import gc
            
            # 執行垃圾回收
            gc.collect()
            
            # 如果有 torch，設定記憶體最佳化
            import torch
            if hasattr(torch, 'set_num_threads'):
                torch.set_num_threads(1)  # 限制線程數
            
            print("✅ Render 環境記憶體最佳化完成")
            
        except Exception as e:
            print(f"⚠️ Render 最佳化警告: {e}")
    
    def get_memory_usage(self):
        """獲取當前記憶體使用情況"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except ImportError:
            return None
        except Exception as e:
            print(f"⚠️ 無法獲取記憶體資訊: {e}")
            return None