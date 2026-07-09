import random
import time 
from utils.response_helper import populate_meta_data, get_fft_figure_url

# Instantiate the cryptographically secure OS-driven random engine
secure_rand = random.SystemRandom()


def mock_incline_data(station_id):
    current_timestamp = int(time.time())
    mock_water_level_meter = secure_rand.uniform(0, 10)
    mock_soil_inclination_degree = secure_rand.uniform(0, 30)

    incline_data_dict = {
        "timestamp": current_timestamp,
        "water_level_meter": mock_water_level_meter,
        "soil_inclination_degree": mock_soil_inclination_degree,
        'station_id': f"Mataian_{station_id}"
    }
    incline_data_dict = populate_meta_data(incline_data_dict)

    return incline_data_dict

"""
 {
    "temp":"31.7",
    "humi":"62.2",
    "co2":"-3108",
    "url":"https://d65hb6cahdqvu.cloudfront.net/04702154615/1779353739.png",
}
"""
def mock_fire_data():
    current_timestamp = int(time.time())
    mock_temp = round(secure_rand.uniform(20.0, 100.0), 1)  # Simulate a temperature between 20.0 and 40.0 degrees Celsius
    mock_humi = round(secure_rand.uniform(30.0, 90.0), 1)  # Simulate a humidity between 30.0 and 90.0 percent
    mock_co2 = secure_rand.randint(-5000, -2000)  # Simulate a CO2 level between -5000 and -2000 ppm

    fire_data_dict = {
        "timestamp": current_timestamp,
        "temp": mock_temp,
        "humi": mock_humi,
        "co2": mock_co2,
        # Hardcode the URL with real data
        "url": "https://d65hb6cahdqvu.cloudfront.net/04702154615/1779353739.png",
    }
    fire_data_dict = populate_meta_data(fire_data_dict)

    return fire_data_dict

"""
    {
        "x_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1760604191_X_freq.png",
        "y_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1760604191_Y_freq.png",
        "z_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1760604191_Z_freq.png",
        "x_rms": "7",
        "y_rms": "276",
        "z_rms": "5",
        "P_wave":"0",
        "S_wave":"1",
        "timestamp": 1760604221,
        "tw_time": "2025-10-16 16:43:41",
        "rsrq_index": 0,
        "vbat": "4156"
    }
"""

def mock_earthquake_data():
    current_timestamp = int(time.time())
    x_rms = secure_rand.randint(0, 10)
    y_rms = secure_rand.randint(0, 300)
    z_rms = secure_rand.randint(0, 10)
    P_wave = secure_rand.choice([0, 1])
    S_wave = secure_rand.choice([0, 1])

    earthquake_data_dict = {
        "timestamp": current_timestamp,
        "x_freq_fft_figure": get_fft_figure_url("X"),
        "y_freq_fft_figure": get_fft_figure_url("Y"),
        "z_freq_fft_figure": get_fft_figure_url("Z"),
        "x_rms": x_rms,
        "y_rms": y_rms,
        "z_rms": z_rms,
        "P_wave": P_wave,
        "S_wave": S_wave,
    }
    earthquake_data_dict = populate_meta_data(earthquake_data_dict)

    return earthquake_data_dict

def mock_report_data(report_id):
    cities = [
        "連江縣","金門縣","宜蘭縣","新竹縣","苗栗縣","彰化縣","南投縣","雲林縣",
        "嘉義縣","屏東縣","臺東縣","花蓮縣","澎湖縣","基隆市","新竹市","嘉義市",
        "臺北市","高雄市","新北市","臺中市","臺南市","桃園市"
    ]
    detail = [
        {
            "city_name": city,
            "amber_rivers": "0", "amber_rivers_twp": "0", "amber_rivers_vil": "0",
            "red_rivers": "0", "red_rivers_twp": "0", "red_rivers_vil": "0",
            "amber_collapse": "0", "amber_collapse_twp": "0", "amber_collapse_vil": "0",
            "red_collapse": "0", "red_collapse_twp": "0", "red_collapse_vil": "0",
            "total_amber_twp": "0", "total_amber_vil": "0",
            "total_red_twp": "0", "total_red_vil": "0",
            "total_rivers": "0", "total_collapse": "0",
            "status": None, "no_data_mark": None
        }
        for city in cities
    ]
    return {
        "maincmt": {
            "prj_no": "專案代號", "org_name": "填報機關", "rpt_approval": "核定人",
            "rpt_phone": "聯絡電話", "rpt_mobile_phone": "行動電話",
            "rpt_no": "通報別", "rpt_user": "通報人", "rpt_time": "通報時間"
        },
        "main": {
            "prj_no": "2014375598",
            "org_name": "農業部農村發展及水土保持署",
            "rpt_approval": "趙彥勛",
            "rpt_phone": "0937-685859",
            "rpt_mobile_phone": "0937-685859",
            "rpt_no": str(report_id),
            "rpt_user": "趙彥勛",
            "rpt_time": "2026-04-04T06:31:04.0000000+08:00"
        },
        "detailcmt": {
            "city_name": "縣市別",
            "amber_rivers": "黃色警戒土石流潛勢溪流數",
            "amber_rivers_twp": "黃色警戒土石流潛勢溪流數坐落鄉鎮數",
            "amber_rivers_vil": "黃色警戒土石流潛勢溪流數坐落村里數",
            "red_rivers": "紅色警戒土石流潛勢溪流數",
            "red_rivers_twp": "紅色警戒土石流潛勢溪流數坐落鄉鎮數",
            "red_rivers_vil": "紅色警戒土石流潛勢溪流數坐落村里數",
            "amber_collapse": "黃色警戒大規模崩塌潛勢區數",
            "amber_collapse_twp": "黃色警戒大規模崩塌潛勢區數坐落鄉鎮數",
            "amber_collapse_vil": "黃色警戒大規模崩塌潛勢區數坐落村里數",
            "red_collapse": "紅色警戒大規模崩塌潛勢區數",
            "red_collapse_twp": "紅色警戒大規模崩塌潛勢區數坐落鄉鎮數",
            "red_collapse_vil": "紅色警戒大規模崩塌潛勢區數坐落村里數",
            "total_amber_twp": "黃色警戒座落鄉鎮數合計",
            "total_amber_vil": "黃色警戒座落村里數合計",
            "total_red_twp": "紅色警戒座落鄉鎮數合計",
            "total_red_vil": "紅色警戒座落村里數合計",
            "total_rivers": "土石流潛勢溪流數合計",
            "total_collapse": "大規模崩塌潛勢區處數合計",
            "status": "狀態",
            "no_data_mark": "無資料可填寫"
        },
        "detail": detail
    }