import json
import re

# 匹配類型的關鍵字
TYPE_KEYWORDS = {
    "手機": ["phone", "galaxy", "xperia", "pixel", "moto", "iphone"],
    "平板": ["tab", "pad"],
    "手錶": ["watch", "vivowatch"],
    "耳機": ["buds", "airpods", "ear"]
}

def detect_type(tag):
    """根據 tag 推斷產品類型"""
    for t, keywords in TYPE_KEYWORDS.items():
        if any(keyword in tag.lower() for keyword in keywords):
            return t
    return "手機"  # 預設類型是手機

def format_name(brand, model):
    """格式化完整名稱"""
    return f"{brand} {model}"

def extract_brand_model(tag):
    """從 tag 中解析出品牌與型號"""
    parts = tag.split('-')
    if len(parts) > 1:
        brand = parts[0].capitalize()
        model = ' '.join(parts[1:]).title()
        return brand, model
    return "Unknown", "Unknown"

# 載入 JSON 資料
with open('c-url-producturl.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 處理每一筆資料
new_data = []
for item in data:
    new_item = {
        "tag": item["tag"],
        "url": item["url"]
    }

    # 如果缺少 brand, model, name, type，自動解析
    if not all(key in item for key in ["brand", "model", "name", "type"]):
        brand, model = extract_brand_model(item["tag"])
        product_type = detect_type(item["tag"])
        new_item["brand"] = brand
        new_item["model"] = model
        new_item["name"] = format_name(brand, model)
        new_item["type"] = product_type
    else:
        new_item.update({
            "brand": item["brand"],
            "model": item["model"],
            "name": item["name"],
            "type": item["type"]
        })

    new_data.append(new_item)

# 寫回 JSON 檔案
with open('c-url-producturl.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print("✅ 資料格式轉換完成！")