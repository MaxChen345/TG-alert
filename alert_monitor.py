import json
import os
import time
import requests

def load_config():
    # 確保讀取的是跟你 app.py 同一個資料夾下的 config.json
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def send_critical_alert(title, body):
    config = load_config()
    if not config:
        print("❌ 找不到 config.json，請先在網頁儲存設定！")
        return
        
    devices = config.get("devices", [])
    bomb_count = config.get("duration", 6)
    interval = 2 if bomb_count > 1 else 0

    # 💡 關鍵過濾：只挑選在網頁上被「勾選啟用（enabled == True）」的裝置！
    active_devices = [dev for dev in devices if dev.get("enabled") is True]

    if not active_devices:
        print("⚠️ 目前沒有任何已啟用的 Bark 裝置，跳過推播。")
        return

    print(f"🚨 [監聽中] 偵測到目標訊息！開始對以下 {len(active_devices)} 部啟用裝置進行 {bomb_count} 次轟炸...")

    # 執行連續轟炸邏輯
    for i in range(bomb_count):
        for dev in active_devices:
            # 確保金鑰後面沒有多餘的斜線
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
                # 使用 timeout 避免其中一個裝置網路卡住，拖累其他裝置
                response = requests.post(bark_url, json=payload, timeout=5)
                print(f"👉 成功發送給 {dev['name']}，狀態碼: {response.status_code}")
            except Exception as e:
                print(f"❌ 發送給 {dev['name']} 失敗: {e}")
        
        if interval > 0 and i < (bomb_count - 1):
            time.sleep(interval)