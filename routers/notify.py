import json
from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Body

from utils.llm import parse_disaster_message, _run_analyze, _build_alert_message
from utils.notify import send_line_reply, broadcast_line_bot_message
from utils.rate_limit import check_rate_limit
from utils.response_helper import success_response
from config.response_example import EXAMPLE_NOTIFY_FIRE
from config.settings import LLM_API_KEY

router = APIRouter()

LINE_EXAMPLE_TEXT_MESSAGE = {"text": "我是馬太鞍溪上游巡檢員，剛剛大雨不停，發現堰塞湖水位暴漲已經開始溢流了！而且旁邊山壁發生土石流導致道路坍方，目前手機完全沒有行動通訊訊號，我是透過魔塊衛星發出這條 SOS 求救，請指揮中心立刻派人撤離下游居民！"}


async def _analyze_and_broadcast(raw_message: str):
    """背景任務：只用人為通報文字分析，若有災害則推播給指定使用者"""
    if not LLM_API_KEY:
        print("[背景分析] LLM_API_KEY 未設定，略過")
        return
    try:
        input_summary = {
            "human_reports": [{"text": raw_message}],
            # "iot_sensors": [],    # 暫時關閉，待整合感測器資料
            # "external_data": [],  # 暫時關閉，待整合外部開放資料
        }
        analysis = await _run_analyze(input_summary)
        print(f"[背景分析] has_disaster={analysis.get('has_disaster')}")
        if analysis.get("has_disaster"):
            broadcast_line_bot_message(_build_alert_message(analysis))
            print(f"[背景分析] 已推播 LINE 警報：{analysis.get('disaster_type')}")
    except Exception as e:
        print(f"[背景分析] 執行錯誤: {e}")


@router.post("/notify", responses={200: EXAMPLE_NOTIFY_FIRE})
async def notify(request: Request, background_tasks: BackgroundTasks, payload: dict = Body(example=LINE_EXAMPLE_TEXT_MESSAGE)):
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

        rate_key = f"line:{user_id}" if user_id else request.client.host
        try:
            check_rate_limit(rate_key)  # 第一次 LLM 呼叫（parse_disaster_message）
            check_rate_limit(rate_key)  # 第二次 LLM 呼叫（_analyze_and_broadcast）
        except HTTPException as e:
            if reply_token:
                send_line_reply(reply_token, e.detail)
            return {"status": "RATE_LIMITED", "message": e.detail}

        if len(raw_message.strip()) < 3:
            send_line_reply(reply_token, "回報訊息需大於三個字才能處理喔")
            return {"status": "IGNORED", "message": "訊息過短，略過"}

        try:
            analysis_result = await parse_disaster_message(raw_message)
        except ValueError as e:
            error_msg = f"您的訊息過長，系統無法處理，請縮短訊息後重新輸入。"
            if reply_token:
                send_line_reply(reply_token, error_msg)
            return {"status": "ERROR", "message": str(e)}

        if analysis_result["severity"] == "INFO" and not analysis_result.get("needs_rescue", False):
            return success_response(message="非緊急訊息，不處理")

        hazard_mapping = {"Fire": "火災", "Debris_Flow": "土石流/崩塌", "Barrier_Lake_Overflow": "堰塞湖溢流", "Flood": "洪水", "Earthquake": "地震", "General_Incident": "一般災情"}
        hazard_chinese = hazard_mapping.get(analysis_result["primary_hazard"], "一般災情")
        location_chinese = analysis_result.get("location", "未知")
        urgency_mapping = {"CRITICAL": "緊急", "WARNING": "警戒", "INFO": "一般"}
        urgency_chinese = urgency_mapping.get(analysis_result["severity"], "一般")

        report_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

        location_hint = "\n\n📌 請補充事發地點，以便救援單位盡快抵達！" if location_chinese == "未知" else ""
        formatted_reply = (
            f"✅ 已收到您的回報！\n"
            f"🕐 通報時間：{report_time}\n"
            f"⚡ 案件類型：{hazard_chinese}\n"
            f"📍 地點：{location_chinese}\n"
            f"⚠️ 緊急性：{urgency_chinese}"
            f"{location_hint}"
        )

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
                    {"sensor_type": "Radar_Water_Level_Gauge", "action": "QUERY_GROUND_TRUTH", "expected_field": "water_level_meter"},
                    {"sensor_type": "3D_Inclinometer_Vibration", "action": "QUERY_GROUND_TRUTH", "expected_field": "slope_displacement_deg"}
                ],
                "edge_ai_camera_trigger": "CAPTURE_COMPRESSED_FEATURE_CODE"
            },
            "system_routing_action": {
                "next_component_api": "https://api.civictech.moda.gov.tw/v1/disaster/management/dispatch",
                "data_format_version": "v1.2.0-JSON-Schema",
                "broadcast_to_ncdr_cap": True
            }
        }

        background_tasks.add_task(_analyze_and_broadcast, raw_message)

        return success_response(message="災情通報接收並處理成功", data=standard_json_output)

    except Exception as e:
        return {"status": "ERROR", "message": f"系統內部執行錯誤: {str(e)}"}
