import time
import random
from datetime import datetime
from typing import Any
import pytz

TAIWAN_TZ = pytz.timezone("Asia/Taipei")

def populate_meta_data(incline_data_dict):
    current_timestamp = int(time.time())
    tw_time = datetime.now(TAIWAN_TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Simulate a timestamp from one hour ago
    random_rssi_value = random.randint(-90, -70)  # Simulated RSSI value

    updated_incline_data_dict = {
        "timestamp": current_timestamp,
        "tw_time": tw_time,
        "network_status": {
            "current_mode": "TN_NB_IoT",
            "rssi": random_rssi_value,
            },
        "sensor_data": incline_data_dict
        }
    return updated_incline_data_dict

def success_response(data: Any = None, message: str = "Success") -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": int(time.time()),
    }


def error_response(message: str, code: int = None) -> dict:
    return {
        "success": False,
        "message": message,
        "code": code,
        "timestamp": int(time.time()),
    }