from typing import List, Dict, Any, Optional
from datetime import datetime
from .query_processor import QueryProcessor
from .rag_engine import RAGEngine

class EnhancedRAGEngine(RAGEngine):
    """增強版 RAG 引擎 - 支援對話上下文"""
    
    def __init__(self, notion_client, text_processor, embedder, vector_store, settings):
        """初始化增強版 RAG 引擎"""
        super().__init__(notion_client, text_processor, embedder, vector_store, settings)
        print("🚀 增強版 RAG 引擎已初始化，支援對話上下文")
    
    def query_with_context(self, question: str, conversation_context: str = "", user_id: str = None) -> str:
        """
        帶上下文的問答查詢
        
        Args:
            question: 用戶問題
            conversation_context: 對話上下文
            user_id: 用戶ID（用於日誌）
            
        Returns:
            回答字串
        """
        try:
            if user_id:
                print(f"🤔 處理用戶 {user_id} 的問題: {question}")
            else:
                print(f"🤔 處理問題: {question}")
            
            # 如果有對話上下文，先分析是否需要結合上下文
            context_enhanced_question = self._enhance_question_with_context(question, conversation_context)
            
            # 使用查詢處理器分析問題（使用增強後的問題）
            query_analysis = self.query_processor.process_query(context_enhanced_question)
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
                return self._generate_no_result_response(question, conversation_context)
            
            print(f"📋 找到 {len(relevant_docs)} 個相關文件")
            for i, doc in enumerate(relevant_docs):
                print(f"  {i+1}. 綜合分數: {doc['score']:.3f}")
            
            # 組合上下文
            document_context = self._build_context(relevant_docs)
            
            # 生成回答
            if self.use_openai:
                answer = self._generate_context_aware_response(
                    question, document_context, conversation_context, query_analysis
                )
            else:
                answer = self._generate_simple_context_response(
                    question, document_context, conversation_context
                )
            
            return answer
            
        except Exception as e:
            print(f"❌ 處理問題時發生錯誤: {e}")
            return f"抱歉，處理問題時發生錯誤: {str(e)}"
    
    def _enhance_question_with_context(self, question: str, conversation_context: str) -> str:
        """
        結合對話上下文增強問題
        
        Args:
            question: 原始問題
            conversation_context: 對話上下文
            
        Returns:
            增強後的問題
        """
        if not conversation_context:
            return question
        
        # 檢查問題是否包含代詞或指示詞，需要上下文理解
        context_indicators = [
            "這個", "那個", "它", "他", "她", "上面", "剛才", "之前", "提到的",
            "這樣", "那樣", "如何", "怎麼", "為什麼", "還有", "另外", "繼續"
        ]
        
        needs_context = any(indicator in question for indicator in context_indicators)
        
        if needs_context:
            # 結合上下文創建增強問題（僅供內部查詢使用）
            enhanced_question = f"{conversation_context}\n當前問題: {question}"
            print(f"🔗 問題需要上下文理解，已增強查詢")
            return enhanced_question
        
        return question
    
    def _generate_context_aware_response(self, question: str, document_context: str, 
                                       conversation_context: str, query_analysis) -> str:
        """
        生成考慮對話上下文的 OpenAI 回答
        """
        try:
            # 建立系統提示
            system_prompt = """你是一個基於 Notion 文件的智慧助手，專門回答與文件內容相關的問題。

請遵循以下規則：
1. 主要基於提供的文件內容回答問題
2. 考慮對話歷程，保持對話的連貫性
3. 如果問題涉及之前的對話內容，請適當引用
4. 使用繁體中文回答
5. 回答要準確、有幫助且友善
6. 如果文件中沒有相關資訊，請誠實說明
7. 可以適當推理，但不要編造資訊

對話上下文將幫助你理解問題的背景和用戶的意圖。"""
            
            # 建立用戶提示
            user_prompt = f"""參考文件內容：
{document_context}

{conversation_context}

請根據以上資訊回答問題：{question}"""
            
            # 呼叫 OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # 添加置信度資訊
            if query_analysis.confidence < 0.5:
                answer += f"\n\n💡 提示：我對這個問題的理解置信度較低（{query_analysis.confidence:.1%}），如果回答不夠準確，請嘗試重新表述問題。"
            
            return answer
            
        except Exception as e:
            print(f"❌ OpenAI API 呼叫失敗: {e}")
            return self._generate_simple_context_response(question, document_context, conversation_context)
    
    def _generate_simple_context_response(self, question: str, document_context: str, 
                                        conversation_context: str) -> str:
        """
        生成簡單的上下文回答（不使用 OpenAI）
        """
        response_parts = []
        
        # 如果有對話上下文，添加上下文參考
        if conversation_context:
            response_parts.append("根據我們之前的對話和文件內容：\n")
        else:
            response_parts.append("根據文件內容：\n")
        
        # 添加文件內容摘要
        response_parts.append(document_context)
        
        # 添加針對問題的建議
        response_parts.append(f"\n關於您的問題「{question}」，以上內容應該能提供相關資訊。")
        
        if conversation_context:
            response_parts.append("如果您需要更詳細的解釋或有其他相關問題，請繼續詢問。")
        
        return "\n".join(response_parts)
    
    def _generate_no_result_response(self, question: str, conversation_context: str) -> str:
        """
        生成找不到結果時的回答
        """
        base_response = "抱歉，我在您的 Notion 文件中找不到直接相關的資訊。"
        
        if conversation_context:
            base_response += "雖然我們之前有討論過一些內容，但對於這個具體問題，文件中沒有足夠的資訊。"
        
        suggestions = [
            "您可以嘗試：",
            "• 重新表述問題，使用不同的關鍵詞",
            "• 提供更多背景資訊",
            "• 檢查 Notion 文件是否包含相關內容",
            "• 詢問更具體或更一般的問題"
        ]
        
        return base_response + "\n\n" + "\n".join(suggestions)
    
    # 繼承父類的其他方法，保持向後相容性
    def query(self, question: str) -> str:
        """
        向後相容的查詢方法（無上下文）
        """
        return self.query_with_context(question, "", None) 