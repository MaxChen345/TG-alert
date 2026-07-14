import json
import os
import time
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "config.json"

# 初始化設定檔 (支援多裝置)
def load_config():
    if not os.path.exists(DB_FILE):
        default_config = {
            "duration": 6,
            "devices": [
                {"id": "dev_1", "name": "我的 iPhone", "key": "Fgrz2C9PXKGiXNZTRr8h3D", "enabled": True}
            ],
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

# Pydantic 資料結構
class DeviceModel(BaseModel):
    id: str = None
    name: str
    key: str
    enabled: bool = True

class SaveConfigPayload(BaseModel):
    duration: int
    devices: List[DeviceModel]

class ChannelModel(BaseModel):
    id: str
    name: str

@app.get("/")
def read_root():
    return {"status": "success", "message": "FastAPI 多裝置控制台後端已啟動"}

# 1. 取得最新設定
@app.get("/api/config")
def get_config():
    return load_config()

# 2. 儲存全局設定 (含多個裝置狀態與轟炸時長)
@app.post("/api/save-settings")
def save_settings(data: SaveConfigPayload):
    config = load_config()
    config["duration"] = data.duration
    # 將 Pydantic 模型轉成 dict 儲存
    config["devices"] = [dev.dict() for dev in data.devices]
    save_config(config)
    return {"status": "success", "message": "裝置設定與參數已儲存！"}

# 3. 新增監控頻道
@app.post("/api/channels")
def add_channel(channel: ChannelModel):
    config = load_config()
    if any(c["id"] == channel.id for c in config["channels"]):
        raise HTTPException(status_code=400, detail="此頻道已在監控清單中")
    config["channels"].append({"id": channel.id, "name": channel.name})
    save_config(config)
    return {"status": "success", "message": "成功新增監控頻道！", "channels": config["channels"]}

# 4. 刪除監控頻道
@app.delete("/api/channels/{channel_id}")
def delete_channel(channel_id: str):
    config = load_config()
    config["channels"] = [c for c in config["channels"] if c["id"] != channel_id]
    save_config(config)
    return {"status": "success", "message": "已移除監控頻道", "channels": config["channels"]}

# 5. 測試單一裝置推播
class TestTriggerRequest(BaseModel):
    key: str
    duration: int

@app.post("/api/test-trigger")
def trigger_notification(data: TestTriggerRequest):
    bark_url = f"https://api.day.app/{data.key}/"
    bomb_count = data.duration
    interval_seconds = 2 if bomb_count > 1 else 0
    
    payload = {
        'title': '🚨 裝置測試通知',
        'body': '這是一條來自全端控制台的裝置測試推播！',
        'sound': 'alarm',       
        'group': 'TG_Monitor',
        'level': 'critical',    
        'volume': 10            
    }
    
    try:
        for i in range(bomb_count):
            payload['title'] = f"🚨 測試通知 ({i+1}/{bomb_count})"
            response = requests.post(bark_url, json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Bark 伺服器拒絕連線")
            if interval_seconds > 0 and i < (bomb_count - 1):
                time.sleep(interval_seconds)
        return {"status": "success", "message": f"成功對該裝置發送 {bomb_count} 次推播！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)