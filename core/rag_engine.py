from typing import List, Dict, Any
from datetime import datetime

class RAGEngine:
    """RAG核心引擎"""
    
    def __init__(self, notion_client, text_processor, embedder, vector_store, settings):
        self.notion_client = notion_client
        self.text_processor = text_processor
        self.embedder = embedder
        self.vector_store = vector_store
        self.settings = settings
        
        # 設定OpenAI
        if settings.USE_OPENAI and settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.use_openai = True
                print(f"✅ OpenAI API 已設定，模型: {settings.OPENAI_MODEL}")
            except ImportError:
                print("❌ OpenAI 套件未安裝，使用簡單回應")
                self.use_openai = False
            except Exception as e:
                print(f"❌ OpenAI 設定失敗: {e}")
                self.use_openai = False
        else:
            self.use_openai = False
            print("⚠️ 未設定OpenAI API，將使用簡單的文本組合回應")
    
    def process_notion_page(self, page_id: str) -> bool:
        """處理Notion頁面並加入向量資料庫"""
        try:
            print(f"📄 開始處理Notion頁面: {page_id}")
            
            # 獲取頁面內容
            print("🔄 獲取頁面內容...")
            raw_text = self.notion_client.get_page_content(page_id)
            
            # 清理和分割文本
            print("🧹 清理和分割文本...")
            cleaned_text = self.text_processor.clean_text(raw_text)
            chunks = self.text_processor.split_text(cleaned_text)
            
            print(f"✂️ 文本分割完成，共 {len(chunks)} 個片段")
            
            # 檢查是否已有相同來源的資料
            source_name = f"notion_page_{page_id}"
            existing_stats = self.vector_store.get_stats()
            
            if source_name in existing_stats.get('source_stats', {}):
                print(f"⚠️ 發現現有資料，將清空後重新處理")
                self.vector_store.clear_database()
            
            # 生成向量嵌入
            print("🔄 生成向量嵌入...")
            embeddings = self.embedder.encode(chunks)
            
            # 儲存到向量資料庫
            print("💾 儲存到向量資料庫...")
            self.vector_store.add_documents(chunks, embeddings, source_name)
            
            # 顯示最終統計
            final_stats = self.vector_store.get_stats()
            print(f"✅ 處理完成！")
            print(f"📊 最終統計: {final_stats['total_documents']} 個文檔片段")
            
            return True
        
        except Exception as e:
            print(f"❌ 處理Notion頁面時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def query(self, question: str) -> str:
        """回答問題"""
        try:
            print(f"🤔 處理問題: {question}")
            
            # 生成問題的向量嵌入
            print("🔄 生成問題嵌入...")
            question_embedding = self.embedder.encode_single(question)
            
            # 搜尋相關文件
            print("🔍 搜尋相關內容...")
            similar_docs = self.vector_store.search(
                question_embedding, 
                top_k=self.settings.TOP_K
            )
            
            if not similar_docs:
                return "抱歉，我在你的Notion文件中找不到相關資訊。"
            
            # 過濾低相似度結果
            relevant_docs = [
                doc for doc in similar_docs 
                if doc['score'] >= self.settings.SIMILARITY_THRESHOLD
            ]
            
            if not relevant_docs:
                return f"抱歉，找到的內容相似度太低（最高分數: {similar_docs[0]['score']:.3f}），無法提供可靠答案。"
            
            print(f"📋 找到 {len(relevant_docs)} 個相關文檔")
            for i, doc in enumerate(relevant_docs):
                print(f"  {i+1}. 相似度: {doc['score']:.3f}")
            
            # 組合上下文
            context = self._build_context(relevant_docs)
            
            # 生成回答
            if self.use_openai:
                answer = self._generate_openai_response(question, context)
            else:
                answer = self._generate_simple_response(question, context)
            
            return answer
            
        except Exception as e:
            print(f"❌ 處理問題時發生錯誤: {e}")
            return f"抱歉，處理問題時發生錯誤: {str(e)}"
    
    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """建立上下文"""
        context_parts = []
        
        for i, doc in enumerate(relevant_docs):
            context_parts.append(f"參考資料 {i+1} (相似度: {doc['score']:.3f}):\n{doc['content']}")
        
        return "\n\n".join(context_parts)
    
    def _generate_openai_response(self, question: str, context: str) -> str:
        """使用OpenAI生成回答"""
        try:
            prompt = f"""你是一個有用的助手，專門回答關於Notion文件內容的問題。

請基於以下提供的內容來回答問題，並遵循這些規則：
1. 只基於提供的參考資料來回答
2. 如果參考資料中沒有相關資訊，請明確說明
3. 用繁體中文回答
4. 回答要簡潔明瞭，重點突出
5. 如果是行程相關問題，請包含具體的時間、地點等詳細資訊

參考資料：
{context}

問題：{question}

回答："""

            response = self.openai_client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一個專業的助手，專門回答關於旅行行程的問題。請用繁體中文回答，並且只基於提供的資料來回答。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            print("✅ OpenAI 回答生成完成")
            return answer
            
        except Exception as e:
            print(f"❌ OpenAI API 呼叫失敗: {e}")
            # 如果OpenAI失敗，回退到簡單回應
            return self._generate_simple_response(question, context)
    
    def _generate_simple_response(self, question: str, context: str) -> str:
        """生成簡單回應（不使用OpenAI時的備用方案）"""
        response_parts = [
            f"基於你的Notion內容，我找到以下相關資訊來回答「{question}」：",
            "",
            context,
            "",
            "以上是從你的Notion文件中找到的相關內容。"
        ]
        
        return "\n".join(response_parts)
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        stats = self.vector_store.get_stats()
        
        return {
            "vector_database": {
                "total_documents": stats['total_documents'],
                "total_vectors": stats['total_vectors'],
                "sources": stats['source_stats']
            },
            "embedding_model": self.settings.EMBEDDING_MODEL,
            "openai_enabled": self.use_openai,
            "openai_model": self.settings.OPENAI_MODEL if self.use_openai else None,
            "settings": {
                "chunk_size": self.settings.CHUNK_SIZE,
                "chunk_overlap": self.settings.CHUNK_OVERLAP,
                "top_k": self.settings.TOP_K,
                "similarity_threshold": self.settings.SIMILARITY_THRESHOLD
            }
        }
    
    def update_notion_content(self, page_id: str = None) -> bool:
        """更新Notion內容"""
        if page_id is None:
            page_id = self.settings.NOTION_PAGE_ID
        
        print("🔄 更新Notion內容...")
        return self.process_notion_page(page_id)