#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion RAG 憑證設定助手
"""

import os

def setup_credentials():
    print("🔧 Notion RAG 憑證設定助手")
    print("=" * 50)
    
    # 讀取當前設定
    env_file = "config/.env"
    current_settings = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    current_settings[key.strip()] = value.strip()
    
    print("📋 當前設定：")
    for key, value in current_settings.items():
        if 'TOKEN' in key and value != 'demo_token_for_testing':
            print(f"  {key}: {value[:20]}..." if len(value) > 20 else f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    
    print("\n🔑 請提供您的 Notion 憑證：")
    print("取得方式：https://www.notion.so/my-integrations")
    print()
    
    # 獲取 Notion Token
    while True:
        token = input("請輸入 Notion Integration Token (secret_xxx...): ").strip()
        if not token:
            print("❌ Token 不能為空")
            continue
        if not token.startswith('secret_'):
            print("❌ Token 必須以 'secret_' 開頭")
            continue
        break
    
    # 獲取 Page ID
    while True:
        page_id = input("請輸入 Notion 頁面 URL 或 ID: ").strip()
        if not page_id:
            print("❌ 頁面 ID 不能為空")
            continue
        break
    
    # 儲存設定
    new_settings = {
        'USE_OPENAI': current_settings.get('USE_OPENAI', 'false'),
        'NOTION_TOKEN': token,
        'NOTION_PAGE_ID': page_id
    }
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# Notion RAG 設定檔\n")
        f.write("# 由設定助手自動生成\n\n")
        for key, value in new_settings.items():
            f.write(f"{key}={value}\n")
    
    print(f"\n✅ 憑證已儲存至 {env_file}")
    print("\n🚀 現在您可以：")
    print("1. 測試憑證：python -c \"from config.settings import Settings; s=Settings(); print('✅ 設定成功')\"")
    print("2. 啟動系統：streamlit run app.py")

if __name__ == "__main__":
    setup_credentials() 