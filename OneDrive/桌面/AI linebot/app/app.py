from flask import Flask, request, abort
from dotenv import load_dotenv
from crawler.crawler import get_product_info
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import os

# ✅ 載入 .env 檔案
load_dotenv()

app = Flask(__name__)

# ✅ 初始化 LINE 驗證
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

if not os.getenv("LINE_CHANNEL_SECRET") or not os.getenv("LINE_CHANNEL_ACCESS_TOKEN"):
    print("❌ 環境變數未正確設置")
    print("請確認 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 是否存在")
    exit(1)

# ✅ 設定 Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")
    
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK', 200

# 🟢 新增一個根路由，避免 404 Not Found 問題
@app.route("/", methods=['GET'])
def health_check():
    return "LINE Bot is running!", 200

# ✅ 設定訊息處理
@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        # 📌 取得使用者輸入的訊息
        user_input = event.message.text.strip()
        
        if not user_input:
            # 提供更詳細的使用說明
            reply_text = "請輸入想要搜尋的商品名稱，例如：\n\n📱 手機品牌：\n- Sony\n- Samsung\n- Motorola\n\n💻 平板：\n- Lenovo Yoga\n\n您也可以直接輸入型號或完整名稱進行搜尋"
        else:
            # ✅ 呼叫爬蟲函數獲取商品資訊
            result = get_product_info(user_input)
            
            if result["status"] == "success":
                data = result["data"]
                if isinstance(data, list) and data:
                    # 美化搜尋結果顯示
                    reply_text = f"🔍 找到 {len(data)} 項與「{user_input}」相關的商品：\n\n"
                    for idx, item in enumerate(data, start=1):
                        # 格式化顯示
                        product_name = f"{item['brand']} {item['model']}".strip()
                        reply_text += f"{idx}. {product_name}\n"
                        if item.get('type'):
                            reply_text += f"📱 類型：{item['type']}\n"
                        reply_text += f"🔗 連結：{item['url']}\n\n"
                    
                    if result.get("has_more"):
                        reply_text += "\n💡 提示：還有更多結果，請輸入更精確的關鍵字。"
                else:
                    reply_text = "抱歉，找不到符合的商品，請嘗試其他關鍵字。"
            else:
                reply_text = result["message"]

        # ✅ 回覆訊息給 LINE
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

    except Exception as e:
        app.logger.error(f"錯誤：{str(e)}")
        # 提供更友善的錯誤訊息
        error_message = "抱歉，系統暫時無法處理您的請求。\n請稍後再試，或嘗試其他關鍵字搜尋。"
        
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=error_message)]
                    )
                )
        except Exception as reply_error:
            app.logger.error(f"回覆錯誤訊息失敗：{str(reply_error)}")

# 預先載入商品資料
try:
    from crawler.crawler import load_product_url_map
    print("✅ 正在載入商品資料...")
    product_list = load_product_url_map()
    print(f"✅ 已載入 {len(product_list)} 筆商品資料")
except Exception as e:
    print(f"❌ 載入商品資料失敗：{str(e)}")

# 🟢 主程式啟動 - 適用於本地開發和 Vercel 部署
if __name__ == "__main__":
    # 啟動 Flask 應用
    print("✅ 啟動 LINE Bot 服務...")
    app.run(host='0.0.0.0', port=5000, debug=True)
