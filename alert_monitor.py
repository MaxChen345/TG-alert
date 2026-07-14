import json
import os
import time
import requests
from telethon import TelegramClient, events

print("🚀 正在嘗試啟動 alert_monitor.py...")

# ==========================================
# 💡 [設定區] 請填入你的 Telegram API 認證資訊
# ==========================================
API_ID = 36358041       # ➔ 這裡換成你的數字 api_id
API_HASH = '934fd41c0b1b1a4f86bc5954c1273d35'  # ➔ 這裡換成你的 api_hash 字串
# ==========================================

# 初始化 Telegram 用戶端
client = TelegramClient('my_tg_session', API_ID, API_HASH)

# 讀取網頁與 app.py 共同使用的設定檔
def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# 發送 Bark 警報的函式 (支援多渠道與多裝置)
def send_critical_alert(title, body):
    config = load_config()
    if not config:
        print("❌ 找不到 config.json，請先在網頁儲存設定！")
        return
        
    devices = config.get("devices", [])
    bomb_count = config.get("duration", 6)
    interval = 2 if bomb_count > 1 else 0

    # 💡 只挑選在網頁上被「勾選啟用」的裝置！
    active_devices = [dev for dev in devices if dev.get("enabled") is True]

    if not active_devices:
        print("⚠️ 目前沒有任何已啟用的 Bark 裝置，跳過推播。")
        return

    print(f"🚨 開始對以下 {len(active_devices)} 部啟用裝置進行 {bomb_count} 次轟炸...")

    # 執行連續轟炸邏輯
    for i in range(bomb_count):
        for dev in active_devices:
            clean_key = dev['key'].strip().replace("/", "")
            bark_url = f"https://api.day.app/{clean_key}/"
            
            payload = {
                'title': f"{title} ({i+1}/{bomb_count})",
                'body': body,
                'sound': 'alarm',
                'group': 'TG_Monitor',
                'level': 'critical',
                'volume': 10
            }
            try:
                response = requests.post(bark_url, json=payload, timeout=5)
                print(f"👉 成功發送給 {dev['name']}，狀態碼: {response.status_code}")
            except Exception as e:
                print(f"❌ 發送給 {dev['name']} 失敗: {e}")
        
        if interval > 0 and i < (bomb_count - 1):
            time.sleep(interval)

# 📡 監聽所有新訊息事件
@client.on(events.NewMessage)
async def my_event_handler(event):
    # 每次收到訊息時，即時去讀取 config.json 中的監控頻道
    config = load_config()
    if not config:
        return
        
    # 取得網頁上設定要監控的頻道 ID 列表 (並全部轉成 int 進行精確比對)
    monitored_channels = []
    for ch in config.get("channels", []):
        try:
            monitored_channels.append(int(ch["id"]))
        except ValueError:
            continue
            
    # 檢查當前發言的頻道 ID 是不是我們在網頁上新增的那些頻道之一
    current_chat_id = event.chat_id
    if current_chat_id in monitored_channels:
        # 找到對應的頻道名稱備註
        channel_info = next((ch for ch in config["channels"] if int(ch["id"]) == current_chat_id), None)
        channel_name = channel_info["name"] if channel_info else "監控頻道"
        
        message_text = event.message.message
        print(f"🔔 【偵測新訊息】頻道：{channel_name} (ID: {current_chat_id})")
        print(f"💬 內容：{message_text}")
        
        # 觸發發送給所有啟用裝置的連環警報
        send_critical_alert(f"🚨 {channel_name} 新訊通知", message_text)

# 🚀 啟動監聽器 (保證在最外層，不縮排)
if __name__ == "__main__":
    print("📢 開始連接 Telegram 伺服器並進行監聽...")
    client.start()
    print("✅ Telegram 監聽程式已成功在背景啟動！等待新訊息中...")
    client.run_until_disconnected()