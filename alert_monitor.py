import json
import os
import time
import requests

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def send_critical_alert(title, body):
    config = load_config()
    if not config:
        print("❌ 尚未讀取到 config.json！")
        return
        
    devices = config.get("devices", [])
    bomb_count = config.get("duration", 6)
    interval = 2 if bomb_count > 1 else 0

    # 💡 關鍵過濾：只挑選被勾選「啟用（enabled == True）」的裝置！
    active_devices = [dev for dev in devices if dev.get("enabled") is True]

    if not active_devices:
        print("⚠️ 目前沒有任何已啟用的 Bark 裝置，跳過推播。")
        return

    print(f"🚨 [監聽中] 偵測到目標訊息！開始對以下 {len(active_devices)} 部啟用裝置進行 {bomb_count} 次轟炸...")
    for dev in active_devices:
        print(f"👉 正在對「{dev['name']}」發送...")

    # 執行連環催邏輯
    for i in range(bomb_count):
        for dev in active_devices:
            bark_url = f"https://api.day.app/{dev['key']}/"
            payload = {
                'title': f"{title} ({i+1}/{bomb_count})",
                'body': body,
                'sound': 'alarm',
                'group': 'TG_Monitor',
                'level': 'critical',
                'volume': 10
            }
            try:
                # 異步發送，不互相卡頓
                requests.post(bark_url, json=payload, timeout=5)
            except Exception as e:
                print(f"發送給 {dev['name']} 失敗: {e}")
        
        if interval > 0 and i < (bomb_count - 1):
            time.sleep(interval)