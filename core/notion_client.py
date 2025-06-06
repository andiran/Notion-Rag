import requests
from typing import Dict, List, Any
from datetime import datetime

class NotionClient:
    """Notion API客戶端"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """獲取頁面資訊"""
        url = f"{self.base_url}/pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """獲取區塊子內容"""
        all_blocks = []
        has_more = True
        start_cursor = None
        
        while has_more:
            url = f"{self.base_url}/blocks/{block_id}/children"
            params = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            all_blocks.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return all_blocks
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """從區塊中提取文本"""
        text_content = []
        
        for block in blocks:
            block_type = block.get("type")
            
            if block_type == "paragraph":
                text = self._extract_rich_text(block["paragraph"]["rich_text"])
                if text:
                    text_content.append(text)
            
            elif block_type == "heading_1":
                text = self._extract_rich_text(block["heading_1"]["rich_text"])
                if text:
                    text_content.append(f"# {text}")
            
            elif block_type == "heading_2":
                text = self._extract_rich_text(block["heading_2"]["rich_text"])
                if text:
                    text_content.append(f"## {text}")
            
            elif block_type == "heading_3":
                text = self._extract_rich_text(block["heading_3"]["rich_text"])
                if text:
                    text_content.append(f"### {text}")
            
            elif block_type == "bulleted_list_item":
                text = self._extract_rich_text(block["bulleted_list_item"]["rich_text"])
                if text:
                    text_content.append(f"• {text}")
            
            elif block_type == "numbered_list_item":
                text = self._extract_rich_text(block["numbered_list_item"]["rich_text"])
                if text:
                    text_content.append(f"1. {text}")
            
            elif block_type == "to_do":
                text = self._extract_rich_text(block["to_do"]["rich_text"])
                checked = block["to_do"].get("checked", False)
                checkbox = "☑️" if checked else "☐"
                if text:
                    text_content.append(f"{checkbox} {text}")
        
        return "\n\n".join(text_content)
    
    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """提取富文本內容"""
        return "".join([text.get("plain_text", "") for text in rich_text])
    
    def get_page_content(self, page_id: str) -> str:
        """獲取完整頁面內容"""
        try:
            # 獲取頁面基本資訊
            page_info = self.get_page(page_id)
            
            # 獲取頁面標題
            title = "未知標題"
            if 'properties' in page_info:
                for prop_name, prop_data in page_info['properties'].items():
                    if prop_data.get('type') == 'title':
                        title_array = prop_data.get('title', [])
                        if title_array:
                            title = title_array[0].get('plain_text', '未知標題')
                        break
            
            # 獲取頁面內容區塊
            blocks = self.get_block_children(page_id)
            content = self.extract_text_from_blocks(blocks)
            
            # 組合完整內容
            full_content = f"# {title}\n\n{content}"
            
            print(f"✅ 成功獲取頁面內容，共 {len(content)} 字符")
            return full_content
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Notion API 請求失敗: {e}")
            raise
        except Exception as e:
            print(f"❌ 處理頁面內容時發生錯誤: {e}")
            raise