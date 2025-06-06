import faiss
import sqlite3
import pickle
import os
from typing import List, Tuple, Dict, Any
import numpy as np
from datetime import datetime

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
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜尋相似文件"""
        if self.index.ntotal == 0:
            print("⚠️ 向量資料庫為空")
            return []
        
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # 搜尋
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # 獲取對應的文本內容
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # FAISS返回-1表示無效索引
                continue
                
            cursor.execute('''
                SELECT content, source, chunk_id, created_at 
                FROM documents 
                WHERE chunk_index = ?
            ''', (int(idx),))
            
            row = cursor.fetchone()
            if row:
                results.append({
                    'content': row[0],
                    'source': row[1],
                    'chunk_id': row[2],
                    'created_at': row[3],
                    'score': float(scores[0][i]),
                    'index': int(idx)
                })
        
        conn.close()
        
        # 按分數排序（分數越高越相似）
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
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
        
        # 刪除FAISS檔案
        if os.path.exists(self.vector_db_path):
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