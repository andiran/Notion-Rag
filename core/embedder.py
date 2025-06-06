from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import torch

class Embedder:
    """向量嵌入器"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        print(f"🔄 載入嵌入模型: {model_name}")
        
        # 檢查設備
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ 使用設備: {self.device}")
        
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            print(f"✅ 模型載入成功")
            
            # 獲取模型資訊
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            print(f"📏 嵌入維度: {self.embedding_dimension}")
            
        except Exception as e:
            print(f"❌ 模型載入失敗: {e}")
            raise
    
    def encode(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """將文本列表編碼為向量"""
        if not texts:
            return np.array([])
        
        print(f"🔄 編碼 {len(texts)} 個文本片段...")
        
        try:
            # 過濾空文本
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                print("⚠️ 沒有有效的文本可以編碼")
                return np.array([])
            
            # 編碼文本
            embeddings = self.model.encode(
                valid_texts, 
                convert_to_numpy=True,
                show_progress_bar=show_progress,
                batch_size=32  # 設定批次大小
            )
            
            print(f"✅ 編碼完成，形狀: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            print(f"❌ 編碼失敗: {e}")
            raise
    
    def encode_single(self, text: str) -> np.ndarray:
        """將單個文本編碼為向量"""
        if not text.strip():
            return np.array([])
        
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            return embedding
            
        except Exception as e:
            print(f"❌ 單文本編碼失敗: {e}")
            raise
    
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