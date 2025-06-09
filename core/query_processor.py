from typing import Dict, Any, List
import re
from dataclasses import dataclass
from enum import Enum
import json

class QueryIntent(Enum):
    """查詢意圖類型"""
    FACTUAL = "factual"  # 事實性查詢
    COMPARATIVE = "comparative"  # 比較性查詢
    TEMPORAL = "temporal"  # 時間相關查詢
    LOCATION = "location"  # 地點相關查詢
    PERSON = "person"  # 人物相關查詢
    PROCEDURAL = "procedural"  # 程序性查詢
    CONCEPTUAL = "conceptual"  # 概念性查詢
    UNKNOWN = "unknown"  # 未知類型

@dataclass
class QueryAnalysis:
    """查詢分析結果"""
    original_query: str
    intent: QueryIntent
    keywords: List[str]
    entities: Dict[str, Any]
    rewritten_queries: List[str]
    confidence: float
    search_weights: Dict[str, float]  # 新增：搜尋權重配置

class QueryProcessor:
    """查詢處理器：負責查詢意圖理解和重寫"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.use_openai = openai_client is not None
        
        # 常見的錯字映射表
        self.typo_mapping = {
            "行程": ["行成", "形成"],
            "會議": ["會意", "會義"],
            "專案": ["專按", "專暗"],
            "報告": ["報高", "報告"],
            "時間": ["時見", "時建"],
            # 可以根據需要擴充
        }
        
        # 常見的中英對照
        self.en_zh_mapping = {
            "meeting": "會議",
            "project": "專案",
            "report": "報告",
            "schedule": "行程",
            "time": "時間",
            # 可以根據需要擴充
        }
    
    def process_query(self, query: str) -> QueryAnalysis:
        """處理查詢：包含意圖理解和重寫"""
        try:
            # 1. 基礎清理
            cleaned_query = self._clean_query(query)
            
            # 2. 使用 OpenAI 進行深度分析（如果可用）
            if self.use_openai:
                analysis = self._analyze_with_openai(cleaned_query)
            else:
                analysis = self._analyze_with_rules(cleaned_query)
            
            # 3. 生成重寫查詢
            rewritten_queries = self._generate_rewritten_queries(analysis)
            
            return QueryAnalysis(
                original_query=query,
                intent=analysis["intent"],
                keywords=analysis["keywords"],
                entities=analysis["entities"],
                rewritten_queries=rewritten_queries,
                confidence=analysis["confidence"],
                search_weights=analysis.get("search_weights", {"semantic": 0.7, "keyword": 0.3})
            )
            
        except Exception as e:
            print(f"❌ 查詢處理失敗: {e}")
            # 返回基本分析結果
            return QueryAnalysis(
                original_query=query,
                intent=QueryIntent.UNKNOWN,
                keywords=[],
                entities={},
                rewritten_queries=[query],
                confidence=0.0,
                search_weights={"semantic": 0.7, "keyword": 0.3}
            )
    
    def _clean_query(self, query: str) -> str:
        """清理查詢文本"""
        # 1. 移除多餘空白
        query = re.sub(r'\s+', ' ', query.strip())
        
        # 2. 修正常見錯字
        for correct, typos in self.typo_mapping.items():
            for typo in typos:
                query = query.replace(typo, correct)
        
        # 3. 處理中英混用
        for en, zh in self.en_zh_mapping.items():
            query = query.replace(en, zh)
        
        return query
    
    def _analyze_with_openai(self, query: str) -> Dict[str, Any]:
        """使用 OpenAI 進行深度查詢分析"""
        prompt = f"""請分析以下查詢的意圖和關鍵信息：\n\n查詢：{query}\n\n請提供以下分析：\n1. 查詢意圖（factual/comparative/temporal/location/person/procedural/conceptual）\n2. 關鍵詞列表\n3. 實體信息（時間、地點、人物等）\n4. 分析置信度（0-1）\n5. 搜尋權重配置（語義搜尋和關鍵字搜尋的權重，總和為1）\n\n請以JSON格式返回結果。"""

        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """你是一個專業的查詢分析助手。\n請根據查詢的性質，合理分配語義搜尋和關鍵字搜尋的權重：\n- 對於需要理解上下文和語義的查詢，給予較高的語義搜尋權重\n- 對於包含具體關鍵詞的查詢，給予較高的關鍵字搜尋權重\n- 權重總和必須為1"""},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        # 解析 OpenAI 回應
        try:
            print("=== OpenAI 回傳內容 ===")
            print(response.choices[0].message.content)
            analysis_json = json.loads(response.choices[0].message.content)
            analysis = analysis_json["analysis"]
            print("=== 解析後的 analysis ===")
            print(analysis)
            # 防呆：檢查必要欄位
            required_keys = ["intent", "keywords", "entities", "confidence"]
            for k in required_keys:
                if k not in analysis:
                    print(f"❌ 缺少欄位: {k}")
                    raise KeyError(k)
            return {
                "intent": QueryIntent(analysis["intent"]),
                "keywords": analysis["keywords"],
                "entities": analysis["entities"],
                "confidence": analysis["confidence"],
                "search_weights": analysis.get("search_weight", {"semantic": 0.7, "keyword": 0.3})
            }
        except Exception as e:
            print(f"❌ OpenAI 分析結果解析失敗: {e}")
            return self._analyze_with_rules(query)
    
    def _analyze_with_rules(self, query: str) -> Dict[str, Any]:
        """使用規則進行基本查詢分析"""
        # 簡單的規則基礎分析
        intent = QueryIntent.UNKNOWN
        keywords = query.split()
        entities = {}
        
        # 時間相關詞彙
        time_keywords = ["時間", "日期", "幾點", "什麼時候", "何時", "多久"]
        if any(kw in query for kw in time_keywords):
            intent = QueryIntent.TEMPORAL
        
        # 地點相關詞彙
        location_keywords = ["地點", "在哪", "位置", "哪裡", "何處"]
        if any(kw in query for kw in location_keywords):
            intent = QueryIntent.LOCATION
        
        # 程序相關詞彙
        procedural_keywords = ["如何", "怎麼", "步驟", "流程", "方法"]
        if any(kw in query for kw in procedural_keywords):
            intent = QueryIntent.PROCEDURAL
        
        # 概念相關詞彙
        conceptual_keywords = ["什麼是", "定義", "概念", "解釋", "說明"]
        if any(kw in query for kw in conceptual_keywords):
            intent = QueryIntent.CONCEPTUAL
        
        # 根據意圖類型設定搜尋權重
        search_weights = {
            "semantic": 0.7,
            "keyword": 0.3
        }
        
        if intent in [QueryIntent.CONCEPTUAL, QueryIntent.PROCEDURAL]:
            search_weights = {"semantic": 0.8, "keyword": 0.2}
        elif intent in [QueryIntent.TEMPORAL, QueryIntent.LOCATION]:
            search_weights = {"semantic": 0.5, "keyword": 0.5}
        
        return {
            "intent": intent,
            "keywords": keywords,
            "entities": entities,
            "confidence": 0.5,
            "search_weights": search_weights
        }
    
    def _generate_rewritten_queries(self, analysis: Dict[str, Any]) -> List[str]:
        """生成重寫查詢"""
        rewritten = []
        original = analysis.get("original_query", "")
        
        # 1. 保留原始查詢
        rewritten.append(original)
        
        # 2. 基於意圖生成變體
        if analysis["intent"] == QueryIntent.TEMPORAL:
            rewritten.extend([
                f"關於{original}的時間安排",
                f"{original}的具體時間",
                f"{original}什麼時候",
                f"{original}的時程"
            ])
        elif analysis["intent"] == QueryIntent.LOCATION:
            rewritten.extend([
                f"{original}的地點",
                f"{original}在哪裡",
                f"{original}的位置",
                f"{original}的場所"
            ])
        elif analysis["intent"] == QueryIntent.PROCEDURAL:
            rewritten.extend([
                f"如何{original}",
                f"{original}的步驟",
                f"{original}的流程",
                f"{original}的方法"
            ])
        elif analysis["intent"] == QueryIntent.CONCEPTUAL:
            rewritten.extend([
                f"什麼是{original}",
                f"{original}的定義",
                f"{original}的概念",
                f"{original}的解釋"
            ])
        
        # 3. 基於關鍵詞生成變體
        keywords = analysis.get("keywords", [])
        if keywords:
            rewritten.append(" ".join(keywords))
            # 生成關鍵詞組合
            if len(keywords) > 1:
                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        rewritten.append(f"{keywords[i]} {keywords[j]}")
        
        return list(set(rewritten))  # 去重 