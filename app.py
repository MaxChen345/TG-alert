import time
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 💡 允許跨來源資源共用 (CORS)
# 這樣你放在 GitHub Pages 的網頁才能順利發送 API 請求給本機電腦的後端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許任何前端網址呼叫
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],
)

# 定義接收前端資料的格式
class NotificationRequest(BaseModel):
    bark_key: str
    duration: int  # 1 代表溫和，6 代表奪命連環催

@app.get("/")
def read_root():
    return {"status": "success", "message": "FastAPI 後端運作中！"}

@app.post("/api/test-trigger")
def trigger_notification(data: NotificationRequest):
    """接收網頁請求，發送手機 Bark 警報"""
    bark_url = f"https://api.day.app/{data.bark_key}/"
    
    # 依據前端選擇的時長決定轟炸次數
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
        print(f"收到網頁指令！開始對金鑰 {data.bark_key} 發送 {bomb_count} 次警報...")
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
    # 啟動本地伺服器，監聽 port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)