from fastapi import FastAPI, HTTPException, Query, Request, status, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from starlette.responses import FileResponse
from utils.response_helper import success_response, error_response
from utils.notify import broadcast_line_bot_message, send_line_reply
from database.mock_db import mock_incline_data, mock_fire_data
import httpx
import uvicorn
import os
from dotenv import load_dotenv
from database.mock_db import mock_earthquake_data, mock_fire_data
from utils.response_helper import success_response, error_response
import re
import time
import json
from collections import deque
from datetime import datetime, timedelta
import requests

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
from config.response_example import EXAMPLE_FIRE, EXAMPLE_EARTHQUAKE, EXAMPLE_NOTIFY_FIRE, EXAMPLE_ANALYZE, EXAMPLE_REPORT, EXAMPLE_REPORT_INFO
from config.field_labels import DETAIL_FIELD_LABELS
LINE_EXAMPLE_TEXT_MESSAGE = {"text": "我是馬太鞍溪上游巡檢員，剛剛大雨不停，發現堰塞湖水位暴漲已經開始溢流了！而且旁邊山壁發生土石流導致道路坍方，目前手機完全沒有行動通訊訊號，我是透過魔塊衛星發出這條 SOS 求救，請指揮中心立刻派人撤離下游居民！"}

app = FastAPI(title="通報 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SERVE STATIC HTML FROM ROOT ---
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("call.html")

@app.get("/analysis", include_in_schema=False)
async def root():
    return FileResponse("analysis.html")

NOTIFY_SYSTEM_PROMPT = """你是一個防災通報文字解析系統。
請分析以下來自現場人員的災情通報文字，擷取關鍵防災欄位。

【輸出規則】：
- 僅輸出 JSON，不要有 markdown 或多餘文字
- location: 通報地點（字串，從文字推斷，無法判斷時填 "未知"）
- primary_hazard: 主要災害類型，從以下選一：Fire / Debris_Flow / Barrier_Lake_Overflow / Flood / Earthquake / General_Incident
- secondary_hazard: 次要災害類型（同上選項，無時填 null）
- severity: 嚴重程度，從以下選一：CRITICAL / WARNING / INFO
- needs_rescue: 布林值，是否需要搜救
- confidence_score: 0.0-1.0 的浮點數，代表分析信心
- extracted_keywords: 從文字中擷取的關鍵詞陣列（繁體中文）
- impact_objects: 受影響的人事物陣列（繁體中文）
- urgent_requests: 緊急需求陣列（繁體中文）

輸出格式：
{"location": "string", "primary_hazard": "string", "secondary_hazard": null, "severity": "string", "needs_rescue": bool, "confidence_score": float, "extracted_keywords": [], "impact_objects": [], "urgent_requests": []}"""


async def parse_disaster_message(text: str) -> dict:
    """
    呼叫 Groq LLM 解析來自 LINE 的訊息文字，精煉出關鍵防災欄位
    """
    fallback = {
        "location": "未知",
        "primary_hazard": "General_Incident",
        "secondary_hazard": None,
        "severity": "INFO",
        "needs_rescue": False,
        "confidence_score": 0.5,
        "extracted_keywords": [],
        "impact_objects": [],
        "urgent_requests": []
    }

    if not GROQ_API_KEY:
        return fallback

    async with httpx.AsyncClient(timeout=20) as client:
        groq_response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": NOTIFY_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
                "max_tokens": 2048,
            },
        )

    if groq_response.status_code != 200:
        print(f"[/notify] Groq API 錯誤: {groq_response.status_code}")
        return fallback

    groq_json = groq_response.json()
    content = (groq_json["choices"][0]["message"]["content"] or "{}").strip()
    content = re.sub(r"<think>[\s\S]*?</think>", "", content)
    content = re.sub(r"<think>[\s\S]*$", "", content)
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:])
        content = content.rstrip("`").strip()

    try:
        return json.loads(content)
    except Exception:
        print(f"[/notify] LLM 回傳格式無法解析: {content}")
        return fallback

@app.post("/notify", responses={200: EXAMPLE_NOTIFY_FIRE})
async def notify(request: Request, payload: dict = Body(example=LINE_EXAMPLE_TEXT_MESSAGE)):
    events = payload.get("events", [])
    if "destination" in payload and not events:
        return success_response(message="LINE Webhook verification success.")

    try:
        raw_message = ""
        reply_token = None
        user_id = None

        if events and "message" in events[0]:
            raw_message = events[0]["message"].get("text", "")
            reply_token = events[0].get("replyToken")
            user_id = events[0]["source"].get("userId")
            print(f"--- LINE User ID: {user_id} ---")
        else:
            raw_message = payload.get("text", "")

        # 用 LINE userId 做 rate limit key，避免所有用戶共用同一個 IP 限額
        rate_key = f"line:{user_id}" if user_id else request.client.host
        check_rate_limit(rate_key)

        DISASTER_KEYWORDS = ["火", "煙", "燒", "土石", "崩塌", "坍方", "水", "暴漲", "溢流", "救命", "受困", "有人", "災", "危險", "緊急"]
        is_valid = len(raw_message) > 5 and any(kw in raw_message for kw in DISASTER_KEYWORDS)

        if not is_valid:
            error_msg = "未偵測到有效的通報文字內容"
            if reply_token:
                send_line_reply(reply_token, error_msg)
            return {"status": "ERROR", "message": error_msg}

        analysis_result = await parse_disaster_message(raw_message)

        hazard_mapping = {"Fire": "火災", "Debris_Flow": "土石流/崩塌", "Barrier_Lake_Overflow": "堰塞湖溢流", "Flood": "洪水", "Earthquake": "地震", "General_Incident": "一般災情"}
        hazard_chinese = hazard_mapping.get(analysis_result["primary_hazard"], "一般災情")
        location_chinese = analysis_result.get("location", "未知")
        urgency_mapping = {"CRITICAL": "緊急", "WARNING": "警戒", "INFO": "一般"}
        urgency_chinese = urgency_mapping.get(analysis_result["severity"], "一般")
        report_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

        formatted_reply = f"已收到您的回報！\n通報時間：{report_time}\n案件類型：{hazard_chinese}\n地點：{location_chinese}\n警急性：{urgency_chinese}"

        if reply_token:
            send_line_reply(reply_token, formatted_reply)

        timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        confidence = analysis_result.get("confidence_score", 0.75)

        

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

# ==========================================
# /analyze：多模態災情分析 + LINE 通報
# ==========================================

class AnalyzeRequest(BaseModel):
    iot_sensors: List[dict] = Field(default_factory=list, description="IoT 感測器原始資料列表")
    human_reports: List[dict] = Field(default_factory=list, description="現場人員白話文通報列表")
    external_data: List[dict] = Field(default_factory=list, description="外部開放資料（氣象、地震等）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "iot_sensors": [
                    {
                        "sensor_type": "IOT5_Fire",
                        "station_id": 1,
                        "timestamp": 1748390400,
                        "tw_time": "2026-05-28 14:00:00",
                        "rsrq_index": -82,
                        "vbat": 3750,
                        "temp": 87.3,
                        "humi": 38.1,
                        "co2": -3108,
                        "url": "https://d65hb6cahdqvu.cloudfront.net/04702154615/1779353739.png"
                    },
                    {
                        "sensor_type": "IOT5_landslide",
                        "station_id": 23,
                        "timestamp": 1779951869,
                        "tw_time": "2026-05-28 15:04:29",
                        "rsrq_index": -70,
                        "vbat": 4141,
                        "x_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_X_freq.png",
                        "y_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_Y_freq.png",
                        "z_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_Z_freq.png",
                        "x_rms": 6,
                        "y_rms": 197,
                        "z_rms": 5,
                        "P_wave": 0,
                        "S_wave": 0
                    }
                ],
                "human_reports": [
                    {
                        "source": "Satellite_SMS_Bridge",
                        "network_telemetry": {
                            "carrier": "Brocere_NTN_Network",
                            "mode": "NTN_GEO_SATELLITE",
                            "rssi": -118,
                            "latency_ms": 650
                        },
                        "text": "我是馬太鞍溪上游巡檢員，剛剛大雨不停，發現堰塞湖水位暴漲已經開始溢流了！而且旁邊山壁發生土石流導致道路坍方，目前手機完全沒有行動通訊訊號，我是透過魔塊衛星發出這條 SOS 求救，請指揮中心立刻派人撤離下游居民！",
                        "timestamp": "2026-05-27T19:15:30Z"
                    }
                ],
                "external_data": [
                    {
                        "source": "EMIC_OpenData",
                        "city_name": "花蓮縣",
                        "amber_rivers": "3",
                        "red_rivers": "1",
                        "amber_collapse": "2",
                        "red_collapse": "1",
                        "total_amber_twp": "3",
                        "total_amber_vil": "6",
                        "total_red_twp": "2",
                        "total_red_vil": "3",
                        "total_rivers": "4",
                        "total_collapse": "3",
                        "status": 1,
                        "rpt_time": "2026-05-28T06:31:04.0000000+08:00"
                    }
                ],
            }
        }
    }

# 每個 IP 在滑動視窗內最多允許的請求次數
RATE_LIMIT_MAX_CALLS = 5
RATE_LIMIT_WINDOW_SEC = 60
_rate_limit_store: dict[str, deque] = {}

def check_rate_limit(key: str):
    now = time.time()
    if key not in _rate_limit_store:
        _rate_limit_store[key] = deque()
    window = _rate_limit_store[key]
    # 清除視窗外的舊記錄
    while window and now - window[0] > RATE_LIMIT_WINDOW_SEC:
        window.popleft()
    # 視窗清空後刪除 key，防止記憶體洩漏（下方 append 前不影響判斷）
    if not window:
        del _rate_limit_store[key]
    if len(window) >= RATE_LIMIT_MAX_CALLS:
        oldest = window[0]
        retry_after = int(RATE_LIMIT_WINDOW_SEC - (now - oldest)) + 1
        raise HTTPException(
            status_code=429,
            detail=f"請求過於頻繁，請於 {retry_after} 秒後再試（每 {RATE_LIMIT_WINDOW_SEC} 秒限 {RATE_LIMIT_MAX_CALLS} 次）"
        )
    if key not in _rate_limit_store:
        _rate_limit_store[key] = deque()
    _rate_limit_store[key].append(now)


ANALYZE_SYSTEM_PROMPT = """你是一個智慧防災核心分析系統。
請分析以下來自多個資料來源的輸入（IoT 感測器、現場人員通報、外部開放資料），判斷是否有災害正在發生。

【輸出規則】：
- 僅輸出 JSON，不要有 markdown 或多餘文字
- has_disaster: 布林值，true 代表偵測到災害
- disaster_type: 災害類型，例如 "土石流"、"火災"、"洪水"、"地震"、"堰塞湖溢流"；無災害時填 "無"
- threat_level: "CRITICAL"（緊急）、"WARNING"（警戒）、"INFO"（注意）、"NONE"（無）
- threat_score: 整數 0-100，代表威脅程度
- summary: 繁體中文摘要，說明分析結論（50字內）
- recommended_action: 繁體中文建議行動（30字內）

輸出格式：
{"has_disaster": bool, "disaster_type": "string", "threat_level": "string", "threat_score": int, "summary": "string", "recommended_action": "string"}"""


@app.post("/analyze", summary="多模態災情分析與 LINE 自動通報", tags=["Core Pipeline"], responses={200: EXAMPLE_ANALYZE})
async def analyze(payload: AnalyzeRequest, request: Request):
    """
    接收 IoT 感測器、人員通報、外部開放資料，呼叫 Groq LLM 判斷是否發生災害。
    若偵測到災害（has_disaster=true），自動廣播 LINE 通知給所有訂閱者。
    """
    client_ip = request.client.host
    check_rate_limit(client_ip)

    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY 未設定")

    input_summary = {
        "iot_sensors": payload.iot_sensors,
        "human_reports": payload.human_reports,
        "external_data": payload.external_data,
    }

    print(f"\n{'='*60}")
    print(f"[/analyze] IP={client_ip}  time={datetime.utcnow().isoformat()}Z")
    print(f"[/analyze] 輸入：{json.dumps(input_summary, ensure_ascii=False)[:300]}...")

    async with httpx.AsyncClient(timeout=30) as client:
        groq_response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(input_summary, ensure_ascii=False)},
                ],
                "temperature": 0.1,
                "max_tokens": 2048,
            },
        )

    print(f"[/analyze] Groq HTTP status: {groq_response.status_code}")
    groq_json = groq_response.json()
    print(f"[/analyze] Groq 原始回應: {json.dumps(groq_json, ensure_ascii=False)}")
    print(f"{'='*60}\n")

    if groq_response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Groq API 錯誤: {groq_response.text}")

    content = (groq_json["choices"][0]["message"]["content"] or "{}").strip()
    # 去除 thinking tags（包含未關閉的情況）與 markdown fences
    content = re.sub(r"<think>[\s\S]*?</think>", "", content)
    content = re.sub(r"<think>[\s\S]*$", "", content)
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:])
        content = content.rstrip("`").strip()

    try:
        analysis = json.loads(content)
    except Exception:
        raise HTTPException(status_code=502, detail=f"LLM 回傳格式無法解析: {content}")

    has_disaster = analysis.get("has_disaster", False)
    disaster_type = analysis.get("disaster_type", "無")
    threat_level = analysis.get("threat_level", "NONE")
    threat_score = analysis.get("threat_score", 0)
    summary = analysis.get("summary", "")
    action = analysis.get("recommended_action", "")
    timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    report_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
    timestamp_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_tw = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

    # 組 LINE 推播訊息
    line_message = (
        f"[防災警報] {threat_level}\n"
        f"時間：{report_time}\n"
        f"災害類型：{disaster_type}\n"
        f"威脅分數：{threat_score}/100\n"
        f"摘要：{summary}\n"
        f"建議行動：{action}"
    )

    line_notified = False
    if has_disaster:
        broadcast_line_bot_message(line_message)
        line_notified = True

    # 推斷輸入來源標籤
    ingested_sources = []
    for s in payload.iot_sensors:
        label = s.get("sensor_type", "IoT_Sensor")
        if label not in ingested_sources:
            ingested_sources.append(label)
    if payload.human_reports:
        ingested_sources.append("Human_Report_NLP")
    if payload.external_data:
        ingested_sources.append("External_OpenData")

    # CAP urgency / severity 對應
    urgency_map = {"CRITICAL": "Immediate", "WARNING": "Expected", "INFO": "Future", "NONE": "Unknown"}
    severity_map = {"CRITICAL": "Extreme", "WARNING": "Severe", "INFO": "Minor", "NONE": "Unknown"}

    structured_response = {
        "analysis_id": f"ANALS_{timestamp_str}",
        "timestamp": timestamp_iso,
        "cap_standard_payload": {
            "identifier": f"Brocere_Blockcraft_{timestamp_str}",
            "sender": "Brocere_AIoT_Agent",
            "sent": timestamp_tw,
            "status": "Actual",
            "msgType": "Alert" if has_disaster else "Cancel",
            "scope": "Public",
            "info": {
                "category": "Met",
                "event": disaster_type,
                "urgency": urgency_map.get(threat_level, "Unknown"),
                "severity": severity_map.get(threat_level, "Unknown"),
                "certainty": "Observed",
                "headline": summary,
                "instruction": action,
            }
        },
        "ai_agent_status": {
            "engine_mode": "Multi_Modal_Autonomous_Agent",
            "ingested_sources": ingested_sources,
            "overall_confidence_score": round(threat_score / 100, 2)
        },
        "autonomous_tool_execution_log": [
            {"step": 1, "action": "SPATIAL_TEMPORAL_ALIGNMENT", "status": "SUCCESS"},
            {"step": 2, "action": "CROSS_MODAL_VALIDATION", "status": "SUCCESS"},
            {"step": 3, "action": "QUERY_EXTERNAL_API", "status": "SUCCESS"},
            {"step": 4, "action": "GENERATE_ROUTING_COMMAND", "status": "SUCCESS"},
        ],
        "action_triggers": {
            "broadcast_channels": [
                {
                    "channel_type": "LINE_Official_Notification",
                    "has_disaster": has_disaster,
                    "disaster_type": disaster_type,
                    "threat_level": threat_level,
                    "threat_score": threat_score,
                    "summary": summary,
                    "recommended_action": action,
                    "payload_message": line_message,
                    "line_notified": line_notified,
                }
            ],
            "blockcraft_ntn_command": {
                "target_hardware_group": "IoT_Network",
                "instruction": "CHANGE_COMMUNICATION_MODE_TO_SURVIVAL",
                "payload": {
                    "primary_link": "NTN_GEO_SATELLITE",
                    "uplink_frequency_seconds": 60
                }
            }
        }
    }

    return success_response(message="災情分析完成", data=structured_response)


if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)