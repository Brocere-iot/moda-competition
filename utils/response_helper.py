import time
import random
from datetime import datetime
from typing import Any
import pytz

TAIWAN_TZ = pytz.timezone("Asia/Taipei")

secure_rand = random.SystemRandom()

def populate_meta_data(incline_data_dict):
    current_timestamp = int(time.time())
    tw_time = datetime.now(TAIWAN_TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Simulate a timestamp from one hour ago
    tw_time = tw_time[:-4]  # Remove milliseconds for cleaner output
    random_rsrq_value = secure_rand.randint(-90, -70)  # Simulated RSRQ value
    random_vbat_value = secure_rand.randint(3000, 4200)  # Simulated battery voltage in mV

    updated_incline_data_dict = {
        "timestamp": current_timestamp,
        "tw_time": tw_time,
        "rsrq_index": random_rsrq_value,
        "vbat": random_vbat_value,
        **incline_data_dict
    }
    # Depreciated fields (for future use if needed):
    # "network_status": {
    #     "current_mode": "TN_NB_IoT",
    #     "rssi": random_rssi_value,
    #     },
    # "sensor_data": incline_data_dict
    return updated_incline_data_dict

def get_fft_figure_url(axis):
    axis = axis.upper() # Ensure the axis is in uppercase (X, Y, or Z)
    base_url = "https://d82xcsxd0ol35.cloudfront.net/04702154614/"
    # Hardcode timestamp with existing (for X and Y axes) data.
    # Note: image might 'expire' after a certain time
    timestamp = 1779849793
    return f"{base_url}{timestamp}_{axis}_freq.png"

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