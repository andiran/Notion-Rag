import faiss
import sqlite3
import pickle
import os
from typing import List, Tuple, Dict, Any
import numpy as np
from datetime import datetime
import shutil

class VectorStore:
    """向量資料庫"""
    
    def __init__(self, vector_db_path: str, metadata_db_path: str, dimension: int = 384):
        self.vector_db_path = vector_db_path
        self.metadata_db_path = metadata_db_path
        self.dimension = dimension
        
        print(f"🗄️ 初始化向量資料庫...")
        print(f"  向量資料庫路徑: {vector_db_path}")
        print(f"  元資料庫路徑: {metadata_db_path}")
        print(f"  向量維度: {dimension}")
        
        # 初始化FAISS索引
        self.index = faiss.IndexFlatIP(dimension)  # 使用內積相似度
        
        # 初始化SQLite元資料庫
        self._init_metadata_db()
        
        # 載入現有資料
        self._load_existing_data()
        
        print(f"✅ 向量資料庫初始化完成")
        print(f"  當前向量數量: {self.index.ntotal}")
    
    def _init_metadata_db(self):
        """初始化元資料庫"""
        # 如果是 :memory: 路徑，跳過創建目錄
        if self.metadata_db_path != ":memory:":
            os.makedirs(os.path.dirname(self.metadata_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE,
                content TEXT,
                source TEXT,
                chunk_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 建立索引提升查詢效能
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chunk_id ON documents(chunk_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source ON documents(source)
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 元資料庫初始化完成")
    
    def add_documents(self, texts: List[str], embeddings: np.ndarray, source: str = "notion"):
        """添加文件到向量資料庫"""
        if len(texts) != len(embeddings):
            raise ValueError(f"文本數量({len(texts)})與嵌入數量({len(embeddings)})不匹配")
        
        print(f"📝 添加 {len(texts)} 個文檔到向量資料庫...")
        
        # 正規化向量（對於內積相似度很重要）
        faiss.normalize_L2(embeddings)
        
        # 獲取當前索引數量（用於計算新的向量ID）
        start_vector_id = self.index.ntotal
        
        # 添加到FAISS索引
        self.index.add(embeddings)
        
        # 添加元資料到SQLite
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        for i, text in enumerate(texts):
            chunk_id = f"{source}_{start_vector_id + i}_{hash(text) % 100000}"
            cursor.execute('''
                INSERT OR REPLACE INTO documents 
                (chunk_id, content, source, chunk_index, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (chunk_id, text, source, start_vector_id + i))
        
        conn.commit()
        conn.close()
        
        # 儲存FAISS索引
        self._save_faiss_index()
        
        print(f"✅ 文檔添加完成，總向量數: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5, settings: Dict = None, _recursion_depth: int = 0) -> List[Dict[str, Any]]:
        """搜尋相似文件
        Args:
            query_embedding: 查詢向量
            top_k: 返回結果數量
            settings: 相似度設定（可選）
            _recursion_depth: 遞迴深度（內部用）
        """
        if self.index.ntotal == 0:
            print("⚠️ 向量資料庫為空（防呆提示）")
            return [{
                'content': '目前資料庫沒有任何內容，請先同步 Notion 資料。',
                'source': '',
                'chunk_id': '',
                'created_at': '',
                'score': 0,
                'recency_score': 0,
                'length_score': 0,
                'index': -1
            }]
        
        # 使用預設設定或傳入的設定
        settings = settings or {}
        base_threshold = settings.get("BASE_THRESHOLD", 0.3)
        dynamic_settings = settings.get("DYNAMIC_THRESHOLD", {})
        filter_settings = settings.get("FILTER_SETTINGS", {})
        min_threshold = dynamic_settings.get("MIN_THRESHOLD", 0.25) if dynamic_settings.get("ENABLED", False) else 0.01
        max_recursion = 5
        
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # 計算動態閾值
        if dynamic_settings.get("ENABLED", False):
            all_scores, _ = self.index.search(query_embedding, self.index.ntotal)
            scores = all_scores[0]
            
            # 計算分數分佈
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # 使用加權方式計算動態閾值
            score_distribution = dynamic_settings.get("SCORE_DISTRIBUTION", {})
            mean_weight = score_distribution.get("MEAN_WEIGHT", 0.6)
            std_weight = score_distribution.get("STD_WEIGHT", 0.4)
            
            dynamic_threshold = (
                mean_score * mean_weight + 
                (mean_score + std_score * dynamic_settings.get("ADJUSTMENT_FACTOR", 0.15)) * std_weight
            )
            
            # 確保閾值在合理範圍內
            threshold = max(
                min(dynamic_threshold, dynamic_settings.get("MAX_THRESHOLD", 0.45)),
                min_threshold
            )
        else:
            threshold = base_threshold
        
        # 執行搜尋
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        results = []
        
        # 獲取長度懲罰設定
        length_penalty = filter_settings.get("LENGTH_PENALTY", {})
        apply_length_penalty = length_penalty.get("ENABLED", True)
        min_length = length_penalty.get("MIN_LENGTH", 10)
        max_length = length_penalty.get("MAX_LENGTH", 500)
        penalty_factor = length_penalty.get("PENALTY_FACTOR", 0.1)
        
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
                
            score = float(scores[0][i])
            if score < threshold:
                continue
                
            cursor.execute('''
                SELECT content, source, chunk_id, created_at 
                FROM documents 
                WHERE chunk_index = ?
            ''', (int(idx),))
            row = cursor.fetchone()
            
            if row:
                content = row[0]
                created_at = datetime.fromisoformat(row[3].replace('Z', '+00:00'))
                time_diff = datetime.now() - created_at
                
                # 計算時間衰減分數
                recency_score = 1.0 / (1.0 + time_diff.days * filter_settings.get("SCORE_DECAY", 0.15))
                
                # 計算長度懲罰
                length_score = 1.0
                if apply_length_penalty:
                    content_length = len(content)
                    if content_length < min_length:
                        length_score = 1.0 - (min_length - content_length) * penalty_factor
                    elif content_length > max_length:
                        length_score = 1.0 - (content_length - max_length) * penalty_factor
                
                # 綜合評分（確保不超過原始閾值）
                bonus_factor = 0.1  # 額外加分因子
                final_score = score * (1.0 + (recency_score + length_score - 1.0) * bonus_factor)
                
                # 確保分數不超過閾值
                if dynamic_settings.get("ENABLED", False):
                    final_score = min(final_score, dynamic_settings.get("MAX_THRESHOLD", 0.45))
                else:
                    final_score = min(final_score, base_threshold)
                
                results.append({
                    'content': content,
                    'source': row[1],
                    'chunk_id': row[2],
                    'created_at': row[3],
                    'score': final_score,
                    'recency_score': recency_score,
                    'length_score': length_score,
                    'index': int(idx)
                })
        
        conn.close()
        
        # 按綜合分數排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 應用結果過濾
        min_results = filter_settings.get("MIN_RESULTS", 1)
        max_results = filter_settings.get("MAX_RESULTS", 8)
        
        # 遞迴終止條件：
        # 1. 已達最大遞迴深度
        # 2. 閾值已經低於 min_threshold
        # 3. 結果數已等於資料庫總數
        if (len(results) < min_results and len(results) > 0 and
            threshold > min_threshold and _recursion_depth < max_recursion and
            len(results) < self.index.ntotal):
            return self.search(query_embedding, top_k=max_results, settings={
                **settings,
                "BASE_THRESHOLD": threshold * 0.8
            }, _recursion_depth=_recursion_depth+1)
            
        return results[:max_results]
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """獲取所有文檔"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT chunk_id, content, source, chunk_index, created_at, updated_at
            FROM documents 
            ORDER BY chunk_index
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'chunk_id': row[0],
                'content': row[1],
                'source': row[2],
                'chunk_index': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        conn.close()
        return results
    
    def clear_database(self):
        """清空資料庫"""
        print("🗑️ 清空向量資料庫...")
        # 重新初始化FAISS索引
        self.index = faiss.IndexFlatIP(self.dimension)
        # 清空SQLite
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents')
        conn.commit()
        conn.close()
        # 刪除FAISS檔案或資料夾
        if os.path.isdir(self.vector_db_path):
            shutil.rmtree(self.vector_db_path)
        elif os.path.exists(self.vector_db_path):
            os.remove(self.vector_db_path)
        print("✅ 資料庫已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取資料庫統計資訊"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        # 總文檔數
        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]
        
        # 按來源統計
        cursor.execute('SELECT source, COUNT(*) FROM documents GROUP BY source')
        source_stats = dict(cursor.fetchall())
        
        # 平均文檔長度
        cursor.execute('SELECT AVG(LENGTH(content)) FROM documents')
        avg_length = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_documents': doc_count,
            'total_vectors': self.index.ntotal,
            'source_stats': source_stats,
            'avg_content_length': round(avg_length, 2),
            'vector_dimension': self.dimension
        }
    
    def _save_faiss_index(self):
        """儲存FAISS索引"""
        # 如果是 :memory: 路徑，跳過儲存
        if self.vector_db_path == ":memory:":
            return
        
        os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
        faiss.write_index(self.index, self.vector_db_path)
    
    def _load_existing_data(self):
        """載入現有資料"""
        if os.path.exists(self.vector_db_path):
            try:
                self.index = faiss.read_index(self.vector_db_path)
                print(f"✅ 載入現有向量索引，包含 {self.index.ntotal} 個向量")
            except Exception as e:
                print(f"⚠️ 載入向量索引失敗: {e}")
                print("將建立新的索引")
                self.index = faiss.IndexFlatIP(self.dimension)