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
LINE_EXAMPLE_TEXT_MESSAGE = {"text": "我是馬太鞍溪上游巡檢員，剛剛大雨不停，發現堰塞湖水位暴漲已經開始溢流了！而且旁邊山壁發生土石流導致道路坍方，目前手機完全沒有行動通訊訊號，我是透過魔塊衛星發出這條 SOS 求救，請指揮中心立刻派人撤離下游居民！"}

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
        "primary_hazard": "General_Incident",
        "secondary_hazard": None,
        "severity": "INFO",
        "needs_rescue": False,
        "extracted_keywords": [],
        "impact_objects": [],
        "urgent_requests": []
    }

    if "火" in text or "煙" in text or "燒" in text:
        parsed["primary_hazard"] = "Fire"
        parsed["severity"] = "CRITICAL"
    elif "堰塞湖" in text or "水位暴漲" in text or ("水" in text and ("暴漲" in text or "溢流" in text)):
        parsed["primary_hazard"] = "Barrier_Lake_Overflow"
        parsed["severity"] = "WARNING"
        if "土石" in text or "崩塌" in text or "坍方" in text:
            parsed["secondary_hazard"] = "Debris_Flow"
            parsed["severity"] = "CRITICAL"
    elif "土石" in text or "崩塌" in text or "坍方" in text:
        parsed["primary_hazard"] = "Debris_Flow"
        parsed["severity"] = "CRITICAL"

    if "救命" in text or "受困" in text or "有人" in text or "SOS" in text or "求救" in text:
        parsed["needs_rescue"] = True
        parsed["severity"] = "CRITICAL"

    kw_candidates = ["水位暴漲", "堰塞湖溢流", "堰塞湖", "發生土石流", "道路坍方",
                     "沒有行動通訊訊號", "SOS", "立刻派人", "救命", "受困", "溢流", "暴漲", "崩塌", "坍方"]
    parsed["extracted_keywords"] = [kw for kw in kw_candidates if kw in text]

    impact_candidates = ["下游居民", "居民", "聯外道路", "道路", "橋梁", "房屋"]
    parsed["impact_objects"] = [obj for obj in impact_candidates if obj in text]

    if "撤離" in text:
        parsed["urgent_requests"].append("人員撤離")
    if "搜救" in text or "救人" in text or "派人" in text or "求救" in text:
        parsed["urgent_requests"].append("搜救派遣")

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

        hazard_mapping = {"Fire": "火災", "Debris_Flow": "土石流/崩塌", "Barrier_Lake_Overflow": "堰塞湖溢流", "General_Incident": "一般災情"}
        hazard_chinese = hazard_mapping.get(analysis_result["primary_hazard"], "一般災情")
        location_chinese = "馬太鞍" if "馬太鞍" in raw_message else "馬太鞍溪地區"
        urgency_mapping = {"CRITICAL": "緊急", "WARNING": "警戒", "INFO": "一般"}
        urgency_chinese = urgency_mapping.get(analysis_result["severity"], "一般")
        report_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

        formatted_reply = f"已收到您的回報！\n通報時間：{report_time}\n案件類型：{hazard_chinese}\n地點：{location_chinese}\n警急性：{urgency_chinese}"

        if reply_token:
            send_line_reply(reply_token, formatted_reply)
        
        timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        confidence = 0.96 if analysis_result["severity"] == "CRITICAL" else 0.75

        standard_json_output = {
            "report_id": f"REPORT_{timestamp_str}",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_channel": payload.get("source_channel", "LINE_Webhook"),
            "network_telemetry": payload.get("network_telemetry", {
                "carrier": "Mobile_Network",
                "mode": "NB_IoT",
                "rssi": -118,
                "latency_ms": 650
            }),
            "raw_input_text": raw_message,
            "ai_nlp_analysis": {
                "primary_disaster_type": analysis_result["primary_hazard"],
                "secondary_disaster_type": analysis_result["secondary_hazard"],
                "threat_level": analysis_result["severity"],
                "confidence_score": confidence,
                "extracted_keywords": analysis_result["extracted_keywords"]
            },
            "extracted_entities": {
                "location": {
                    "reported_place": analysis_result["location"],
            "latitude": 23.6342,
            "longitude": 121.3856,
            "coordinate_accuracy": "GPS_High_Precision"
                },
                "impact_objects": analysis_result["impact_objects"],
                "urgent_requests": analysis_result["urgent_requests"]
            },
            "blockcraft_iot_fusion": {
                "trigger_hardware_cross_check": True,
                "target_sensor_modules": [
                    {
                        "sensor_type": "Radar_Water_Level_Gauge",
                        "action": "QUERY_GROUND_TRUTH",
                        "expected_field": "water_level_meter"
                    },
                    {
                        "sensor_type": "3D_Inclinometer_Vibration",
                        "action": "QUERY_GROUND_TRUTH",
                        "expected_field": "slope_displacement_deg"
                    }
                ],
                "edge_ai_camera_trigger": "CAPTURE_COMPRESSED_FEATURE_CODE"
            },
            "system_routing_action": {
                "next_component_api": "https://api.civictech.moda.gov.tw/v1/disaster/management/dispatch",
                "data_format_version": "v1.2.0-JSON-Schema",
                "broadcast_to_ncdr_cap": True
            }
        }

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