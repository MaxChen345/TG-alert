import json
import os
import time
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# 允許前端跨網域呼叫
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "config.json"

# 初始化設定檔 (用 JSON 模擬資料庫)
def load_config():
    if not os.path.exists(DB_FILE):
        default_config = {
            "bark_key": "Fgrz2C9PXKGiXNZTRr8h3D",
            "duration": 6,
            "channels": [
                {"id": "-1003794809401", "name": "Polymarket Signal"}
            ]
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 定義接收前端設定的格式
class SettingsRequest(BaseModel):
    bark_key: str
    duration: int

# 定義新增頻道的格式
class ChannelModel(BaseModel):
    id: str
    name: str

@app.get("/")
def read_root():
    return {"status": "success", "message": "FastAPI 控制台後端已啟動"}

# ➔ 1. 取得目前所有設定與頻道清單
@app.get("/api/config")
def get_config():
    return load_config()

# ➔ 2. 儲存 Bark 設定
@app.post("/api/save-settings")
def save_settings(data: SettingsRequest):
    config = load_config()
    config["bark_key"] = data.bark_key
    config["duration"] = data.duration
    save_config(config)
    return {"status": "success", "message": "參數設定儲存成功！"}

# ➔ 3. 新增監控頻道
@app.post("/api/channels")
def add_channel(channel: ChannelModel):
    config = load_config()
    # 檢查是否已存在
    if any(c["id"] == channel.id for c in config["channels"]):
        raise HTTPException(status_code=400, detail="此頻道已在監控清單中")
    
    config["channels"].append({"id": channel.id, "name": channel.name})
    save_config(config)
    return {"status": "success", "message": "成功新增監控頻道！", "channels": config["channels"]}

# ➔ 4. 刪除監控頻道
@app.delete("/api/channels/{channel_id}")
def delete_channel(channel_id: str):
    config = load_config()
    original_len = len(config["channels"])
    config["channels"] = [c for c in config["channels"] if c["id"] != channel_id]
    
    if len(config["channels"]) == original_len:
        raise HTTPException(status_code=404, detail="找不到該頻道")
        
    save_config(config)
    return {"status": "success", "message": "已移除監控頻道", "channels": config["channels"]}

# ➔ 5. 測試推播按鈕
class NotificationRequest(BaseModel):
    bark_key: str
    duration: int

@app.post("/api/test-trigger")
def trigger_notification(data: NotificationRequest):
    bark_url = f"https://api.day.app/{data.bark_key}/"
    bomb_count = data.duration
    interval_seconds = 2 if bomb_count > 1 else 0
    
    payload = {
        'title': '🚨 監控控制台測試通知',
        'body': '這是來自你親手設計的全端網頁控制面板的測試訊號！',
        'sound': 'alarm',       
        'group': 'TG_Monitor',
        'level': 'critical',    
        'volume': 10            
    }
    
    try:
        for i in range(bomb_count):
            payload['title'] = f"🚨 網頁測試通知 ({i+1}/{bomb_count})"
            response = requests.post(bark_url, json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Bark 伺服器拒絕連線")
            if interval_seconds > 0 and i < (bomb_count - 1):
                time.sleep(interval_seconds)
        return {"status": "success", "message": f"成功發送 {bomb_count} 次推播！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)