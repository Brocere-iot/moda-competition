from fastapi import FastAPI, HTTPException, Query, status, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from utils.response_helper import success_response, error_response
from database.mock_db import mock_incline_data, mock_fire_data
import httpx
import uvicorn
import os
from dotenv import load_dotenv
from database.mock_db import mock_earthquake_data, mock_fire_data
from utils.response_helper import success_response, error_response
import json
from datetime import datetime, timedelta
import requests

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
from config.response_example import EXAMPLE_FIRE, EXAMPLE_EARTHQUAKE, EXAMPLE_NOTIFY_FIRE, EXAMPLE_REPORT, EXAMPLE_REPORT_INFO
from config.field_labels import DETAIL_FIELD_LABELS
LINE_EXAMPLE_TEXT_MESSAGE = {"text": "馬太鞍溪上游發生土石崩塌，旁邊有人受困！"}

app = FastAPI(title="通報 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_disaster_message(text: str) -> dict:
    """
    解析來自 LINE 的訊息文字，精煉出關鍵防災欄位
    (MVP 階段先以關鍵字比對實作，未來可無縫升級為生成式 AI API)
    """
    parsed = {
        "location": "花蓮縣馬太鞍溪地區 (經確認)",
        "inferred_hazard": "GENERAL",
        "severity": "INFO",
        "needs_rescue": False
    }

    if "火" in text or "煙" in text or "燒" in text:
        parsed["inferred_hazard"] = "FIRE"
        parsed["severity"] = "CRITICAL"
    elif "土石" in text or "崩塌" in text or "坍方" in text:
        parsed["inferred_hazard"] = "LANDSLIDE"
        parsed["severity"] = "CRITICAL"
    elif "水" in text or "暴漲" in text or "溢流" in text:
        parsed["inferred_hazard"] = "FLOOD"
        parsed["severity"] = "WARNING"
        
    if "救命" in text or "受困" in text or "有人" in text:
        parsed["needs_rescue"] = True
        parsed["severity"] = "CRITICAL"
        
    return parsed

def send_line_reply(reply_token: str, reply_text: str):
    LINE_API_URL = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": reply_text
            }
        ]
    }
    # 發送 POST 請求給 LINE 
    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    print(f"--- LINE status code: {response.status_code} ---")

@app.post("/notify", responses={200: EXAMPLE_NOTIFY_FIRE})
async def notify(payload: dict = Body(example=LINE_EXAMPLE_TEXT_MESSAGE)):
    events = payload.get("events", [])
    if "destination" in payload and not events:
        return success_response(message="LINE Webhook verification success.")

    try:
        raw_message = ""
        reply_token = None 
        
        if events and "message" in events[0]:
            raw_message = events[0]["message"].get("text", "")
            reply_token = events[0].get("replyToken")
        else:
            raw_message = payload.get("text", "")

        DISASTER_KEYWORDS = ["火", "煙", "燒", "土石", "崩塌", "坍方", "水", "暴漲", "溢流", "救命", "受困", "有人", "災", "危險", "緊急"]
        is_valid = len(raw_message) > 5 and any(kw in raw_message for kw in DISASTER_KEYWORDS)

        if not is_valid:
            error_msg = "未偵測到有效的通報文字內容"
            if reply_token:
                send_line_reply(reply_token, error_msg)
            return {"status": "ERROR", "message": error_msg}

        analysis_result = parse_disaster_message(raw_message)

        hazard_mapping = {"FIRE": "火災", "LANDSLIDE": "土石流/崩塌", "FLOOD": "水災/溪水暴漲", "GENERAL": "一般災情"}
        hazard_chinese = hazard_mapping.get(analysis_result["inferred_hazard"], "一般災情")
        location_chinese = "馬太鞍" if "馬太鞍" in raw_message else "馬太鞍溪地區"
        urgency_mapping = {"CRITICAL": "緊急", "WARNING": "警戒", "INFO": "一般"}
        urgency_chinese = urgency_mapping.get(analysis_result["severity"], "一般")
        report_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

        formatted_reply = f"已收到您的回報！\n通報時間：{report_time}\n案件類型：{hazard_chinese}\n地點：{location_chinese}\n警急性：{urgency_chinese}"

        if reply_token:
            send_line_reply(reply_token, formatted_reply)
        
        standard_json_output = {
            "station_id": payload.get("station_id", "LINE_CITIZEN_REPORT_01"),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "raw_content": raw_message,
            "structured_data": {
                "location": analysis_result["location"],
                "hazard_type": analysis_result["inferred_hazard"],
                "danger_level": analysis_result["severity"]
            },
            "human_readable_reply": formatted_reply
        }

        # timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # with open(f"disaster_report_{timestamp_str}.json", "w", encoding="utf-8") as f:
        #     json.dump(standard_json_output, f, ensure_ascii=False, indent=2)

        return success_response(message="災情通報接收並處理成功", data=standard_json_output)

    except Exception as e:
        return {"status": "ERROR", "message": f"系統內部執行錯誤: {str(e)}"}

@app.get("/data/fire/{station_id}", responses={200: EXAMPLE_FIRE})
async def get_fire_data(station_id: int):
    print('ID received:', station_id)  # Debugging statement to check the received ID
    if station_id < 0 or station_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Station ID must be a non-negative integer."
        )
    # 1. Fetch the data from your mock DB
    fire_data = mock_fire_data()
    
    # 2. Check if the database actually found data for that ID
    if not fire_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Station with ID {station_id} does not exist."
        )
    
    # 3. If data exists, return it. FastAPI automatically sends a real HTTP 200 status.
    return success_response(
        message=f"Fire data for station {station_id} retrieved successfully.",
        data={"station_id": station_id, **fire_data}
    )

@app.get("/data/earthquake/{station_id}", responses={200: EXAMPLE_EARTHQUAKE})
async def get_earthquake_data(station_id: int):
    print('ID received:', station_id)  # Debugging statement to check the received ID
    if station_id < 0 or station_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Station ID must be a non-negative integer."
        )
    # 1. Fetch the data from your mock DB
    earthquake_data = mock_earthquake_data()
    
    # 2. Check if the database actually found data for that ID
    if not earthquake_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Station with ID {station_id} does not exist."
        )
    
    # 3. If data exists, return it. FastAPI automatically sends a real HTTP 200 status.
    return success_response(
        message=f"Earthquake data for station {station_id} retrieved successfully.",
        data={"station_id": station_id, **earthquake_data}
    )


@app.get("/data/report", responses={200: EXAMPLE_REPORT})
async def get_report_data(city_name: List[str] = Query(default=None)):
    # 民生物聯網資料
    url = "https://portal2.emic.gov.tw/Pub/ERA2/OpenData/ERA2_C4.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_response(f"Failed to fetch report data: upstream returned {response.status_code}", code=502)
        )
    data = response.json()
    detail = data.get("detail", [])
    if city_name:
        detail = [city for city in detail if city.get("city_name") in city_name]
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(f"No data found for cities: {city_name}", code=404)
            )
    rpt_time = data.get("main", {}).get("rpt_time")
    flattened = [{**city, "rpt_time": rpt_time} for city in detail]
    return success_response(message="民生物聯網災情通報資料擷取成功", data=flattened)

@app.get("/data/report/info", summary="民生物聯網通報欄位說明", responses={200: EXAMPLE_REPORT_INFO})
async def get_report_field_info():
    return success_response(message="民生物聯網通報欄位說明擷取成功", data=DETAIL_FIELD_LABELS)

if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)