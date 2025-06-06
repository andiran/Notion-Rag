import re
from typing import List

class TextProcessor:
    """文本處理器"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、數字、基本標點）
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()（）「」【】""''•✅❌☐☑️]', '', text)
        
        return text.strip()
    
    def split_text(self, text: str) -> List[str]:
        """分割文本為chunks"""
        if not text:
            return []
        
        # 先按段落分割
        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果段落太長，需要進一步分割
            if len(paragraph) > self.chunk_size:
                # 先保存當前chunk（如果有內容）
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 分割長段落
                sub_chunks = self._split_long_paragraph(paragraph)
                chunks.extend(sub_chunks)
            else:
                # 檢查加入這個段落是否會超過chunk大小
                if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:  # +2 for \n\n
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # 保存當前chunk，開始新的chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
        
        # 保存最後一個chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 添加重疊
        return self._add_overlap(chunks)
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """將文本分割為段落"""
        # 按雙換行符分割段落
        paragraphs = text.split('\n\n')
        
        # 清理空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割過長的段落"""
        # 嘗試按句子分割
        sentences = self._split_into_sentences(paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果單個句子就超過chunk_size，強制分割
                if len(sentence) > self.chunk_size:
                    force_chunks = self._force_split(sentence)
                    chunks.extend(force_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """將文本分割為句子"""
        # 中英文句子分割
        sentence_endings = r'[.!?。！？]'
        sentences = re.split(sentence_endings, text)
        
        # 清理空句子並重新添加標點
        result = []
        for i, sentence in enumerate(sentences[:-1]):  # 最後一個通常是空的
            sentence = sentence.strip()
            if sentence:
                # 找回原來的標點符號
                original_pos = text.find(sentence) + len(sentence)
                if original_pos < len(text):
                    punctuation = text[original_pos]
                    result.append(sentence + punctuation)
                else:
                    result.append(sentence)
        
        # 處理最後一個句子（如果有內容且沒有標點）
        if sentences[-1].strip():
            result.append(sentences[-1].strip())
        
        return result
    
    def _force_split(self, text: str) -> List[str]:
        """強制分割過長的文本"""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """為chunks添加重疊"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            # 獲取前一個chunk的結尾部分作為重疊
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # 計算重疊文本（取前一個chunk的最後部分）
            overlap_text = ""
            if len(prev_chunk) > self.chunk_overlap:
                # 嘗試從句子邊界開始重疊
                words = prev_chunk.split()
                overlap_words = []
                char_count = 0
                
                for word in reversed(words):
                    if char_count + len(word) + 1 <= self.chunk_overlap:
                        overlap_words.insert(0, word)
                        char_count += len(word) + 1
                    else:
                        break
                
                if overlap_words:
                    overlap_text = " ".join(overlap_words)
            
            # 組合重疊chunk
            if overlap_text:
                overlapped_chunk = overlap_text + " " + curr_chunk
            else:
                overlapped_chunk = curr_chunk
                
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def get_chunk_info(self, chunks: List[str]) -> dict:
        """獲取分割統計資訊"""
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_length": 0,
                "max_length": 0,
                "min_length": 0,
                "total_chars": 0
            }
        
        lengths = [len(chunk) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_length": sum(lengths) // len(lengths),
            "max_length": max(lengths),
            "min_length": min(lengths),
            "total_chars": sum(lengths)
        }