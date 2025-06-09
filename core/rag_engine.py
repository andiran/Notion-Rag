from typing import List, Dict, Any
from datetime import datetime
from .query_processor import QueryProcessor

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
        
        # 初始化查詢處理器
        self.query_processor = QueryProcessor(self.openai_client if self.use_openai else None)
    
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
            
            # 使用查詢處理器分析問題
            query_analysis = self.query_processor.process_query(question)
            print(f"📊 查詢分析結果:")
            print(f"  - 意圖: {query_analysis.intent}")
            print(f"  - 關鍵詞: {query_analysis.keywords}")
            print(f"  - 置信度: {query_analysis.confidence:.2f}")
            print(f"  - 搜尋權重: {query_analysis.search_weights}")
            
            # 多階段檢索
            semantic_docs = []
            keyword_docs = []
            
            # 1. 語義搜尋
            semantic_weight = query_analysis.search_weights.get("semantic", query_analysis.search_weights.get("semantic_search", 0))
            keyword_weight = query_analysis.search_weights.get("keyword", query_analysis.search_weights.get("keyword_search", 0))
            if semantic_weight > 0:
                print("🔍 執行語義搜尋...")
                for rewritten_query in query_analysis.rewritten_queries:
                    question_embedding = self.embedder.encode_single(rewritten_query)
                    docs = self.vector_store.search(
                        question_embedding,
                        top_k=self.settings.TOP_K
                    )
                    semantic_docs.extend(docs)
            
            # 2. 關鍵字搜尋
            if keyword_weight > 0:
                print("🔍 執行關鍵字搜尋...")
                for keyword in query_analysis.keywords:
                    keyword_embedding = self.embedder.encode_single(keyword)
                    docs = self.vector_store.search(
                        keyword_embedding,
                        top_k=self.settings.TOP_K
                    )
                    keyword_docs.extend(docs)
            
            # 3. 合併和去重文檔
            all_docs = []
            seen_contents = set()
            
            # 處理語義搜尋結果
            for doc in semantic_docs:
                if doc['content'] not in seen_contents:
                    seen_contents.add(doc['content'])
                    doc['score'] *= semantic_weight
                    all_docs.append(doc)
            
            # 處理關鍵字搜尋結果
            for doc in keyword_docs:
                if doc['content'] not in seen_contents:
                    seen_contents.add(doc['content'])
                    doc['score'] *= keyword_weight
                    all_docs.append(doc)
                else:
                    # 如果文檔已存在，更新分數
                    for existing_doc in all_docs:
                        if existing_doc['content'] == doc['content']:
                            existing_doc['score'] += doc['score'] * keyword_weight
            
            # 按綜合分數排序
            all_docs.sort(key=lambda x: x['score'], reverse=True)
            relevant_docs = all_docs[:self.settings.TOP_K]
            
            if not relevant_docs:
                return "抱歉，我在你的Notion文件中找不到相關資訊。"
            
            print(f"📋 找到 {len(relevant_docs)} 個相關文件")
            for i, doc in enumerate(relevant_docs):
                print(f"  {i+1}. 綜合分數: {doc['score']:.3f}")
            
            # 組合上下文
            context = self._build_context(relevant_docs)
            
            # 生成回答
            if self.use_openai:
                answer = self._generate_openai_response(question, context, query_analysis)
            else:
                answer = self._generate_simple_response(question, context)
            
            return answer
            
        except Exception as e:
            print(f"❌ 處理問題時發生錯誤: {e}")
            return f"抱歉，處理問題時發生錯誤: {str(e)}"
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """計算關鍵詞匹配分數"""
        try:
            # 將查詢和內容轉換為小寫
            query = query.lower()
            content = content.lower()
            
            # 分詞（簡單實現，實際可以使用更複雜的分詞器）
            query_words = set(query.split())
            content_words = set(content.split())
            
            # 計算關鍵詞匹配度
            if not query_words:
                return 0.0
                
            matched_words = query_words.intersection(content_words)
            return len(matched_words) / len(query_words)
            
        except Exception as e:
            print(f"❌ 關鍵詞分數計算失敗: {e}")
            return 0.0
    
    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """建立上下文"""
        context_parts = []
        
        for i, doc in enumerate(relevant_docs):
            # 添加更多元資訊
            context_parts.append(
                f"參考資料 {i+1} (綜合分數: {doc['score']:.3f}):\n"
                f"來源: {doc['source']}\n"
                f"內容: {doc['content']}\n"
                f"時間: {doc['created_at']}"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_openai_response(self, question: str, context: str, query_analysis) -> str:
        """使用OpenAI生成回答"""
        try:
            prompt = f"""你是一個專業的助手，專門回答關於Notion文件內容的問題。請遵循以下步驟：

1. 查詢意圖理解：
   - 已識別的查詢意圖：{query_analysis.intent}
   - 關鍵詞：{', '.join(query_analysis.keywords)}
   - 實體信息：{query_analysis.entities}
   - 分析置信度：{query_analysis.confidence}
   - 搜尋權重配置：{query_analysis.search_weights}

2. 回答生成：
   - 只基於提供的參考資料來回答
   - 如果參考資料中沒有相關資訊，請明確說明
   - 用繁體中文回答
   - 回答要簡潔明瞭，重點突出
   - 根據查詢意圖調整回答風格：
     * 事實性查詢：直接、準確
     * 比較性查詢：對比分析
     * 時間相關查詢：時間順序
     * 地點相關查詢：空間關係
     * 程序性查詢：步驟清晰
     * 概念性查詢：深入解釋
   - 保持專業性和準確性
   - 適當引用參考資料中的具體內容
   - 如果信息不完整，請說明局限性

原始問題：{question}

參考資料：
{context}

請按照上述步驟處理並回答問題。回答時請注意：
1. 確保回答的準確性和完整性
2. 適當引用參考資料中的具體內容
3. 如果信息不足，請說明局限性
4. 保持專業、客觀的語氣
5. 使用清晰的結構組織回答"""

            response = self.openai_client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """你是一個專業的助手，專門回答關於Notion文件內容的問題。
請用繁體中文回答，並且只基於提供的資料來回答。
你具有強大的語義理解能力，可以處理：
- 錯字和同義詞
- 中英混用的查詢
- 不時態和語氣的提問
- 模糊或間接的問題表達
- 上下文相關的查詢
- 隱含的需求和意圖
- 多層次的語義理解"""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ OpenAI 回應生成失敗: {e}")
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