import json
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import random

# HTTP 請求標頭，模擬一般瀏覽器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 商品URL對照表的 JSON 檔案路徑
PRODUCT_URL_JSON = os.path.join(os.path.dirname(__file__), 'c-url-producturl.json')

def load_product_url_map():
    """載入商品 URL 對照表(JSON 格式)"""
    with open(PRODUCT_URL_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_input(user_input):
    """將使用者輸入標準化為搜尋格式"""
    if not user_input or not isinstance(user_input, str):
        return ""
    normalized = user_input.strip().lower()
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    return normalized

def fetch_product_price(url):
    """從網頁抓取商品價格"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 根據網頁結構找到價格元素
        price_element = soup.find('div', class_='price')
        if price_element:
            price_text = price_element.text.strip()
            # 移除非數字字符並轉換為整數
            price = int(re.sub(r'[^0-9]', '', price_text))
            return price
        return None
    except Exception as e:
        print(f"抓取價格時發生錯誤：{str(e)}")
        return None

def get_product_info(user_input):
    normalized_input = normalize_input(user_input)
    if not normalized_input:
        return {
            "status": "error",
            "message": "請輸入有效的商品名稱"
        }

    product_list = load_product_url_map()
    search_terms = normalized_input.split()
    matched = []

    for item in product_list:
        # 改進：使用更靈活的搜尋邏輯
        search_text = f"{item.get('brand', '')} {item.get('model', '')} {item.get('name', '')} {item.get('type', '')}".lower()
        
        # 改進：計算匹配度分數
        match_score = 0
        for term in search_terms:
            # 完全匹配給予更高分數
            if term in item.get('brand', '').lower() or term in item.get('model', '').lower():
                match_score += 3
            # 部分匹配也給予分數
            elif term in search_text:
                match_score += 1
        
        # 只要有任何匹配就加入結果
        if match_score > 0:
            item['match_score'] = match_score
            matched.append(item)

    if not matched:
        # 改進：提供更有幫助的錯誤訊息和建議
        similar_products = get_similar_products(user_input)
        suggestion_text = "\n- " + "\n- ".join(similar_products) if similar_products else ""
        return {
            "status": "error",
            "message": f"找不到與「{user_input}」相關的商品，請嘗試以下建議：{suggestion_text}"
        }

    # 改進：根據匹配度排序
    matched.sort(key=lambda x: (-x['match_score'], x.get('name', '')))
    result_list = matched[:5]
    has_more = len(matched) > 5

    return {
        "status": "success",
        "data": result_list,
        "has_more": has_more
    }

def get_similar_products(user_input):
    """取得相似商品建議"""
    product_list = load_product_url_map()
    suggestions = set()
    
    # 收集常見品牌和型號
    brands = {}
    types = {}
    
    for item in product_list:
        brand = item.get('brand', '')
        type_ = item.get('type', '')
        
        if brand:
            brands[brand] = brands.get(brand, 0) + 1
        if type_:
            types[type_] = types.get(type_, 0) + 1
    
    # 取得最常見的品牌和類型
    popular_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:3]
    popular_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:2]
    
    for brand, _ in popular_brands:
        suggestions.add(f"{brand} 系列商品")
    
    for type_, _ in popular_types:
        suggestions.add(f"{type_}類商品")
    
    return list(suggestions)