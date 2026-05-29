def _ex(example):
    return {"content": {"application/json": {"example": example}}}


EXAMPLE_FIRE = _ex({
    "success": True, "message": "Fire data for station 1 retrieved successfully.", "timestamp": 1748390400,
    "data": {"station_id": 1, "timestamp": 1748390400, "tw_time": "2026-05-28 14:00:00", "rsrq_index": -82, "vbat": 3750,
             "temp": 87.3, "humi": 38.1, "co2": -3108,
             "url": "https://d65hb6cahdqvu.cloudfront.net/04702154615/1779353739.png"}
})

EXAMPLE_EARTHQUAKE = _ex({
    "success": True, "message": "Earthquake data for station 23 retrieved successfully.", "timestamp": 1748390400,
    "data": {"station_id": 23, "timestamp": 1779951869, "tw_time": "2026-05-28 15:04:29", "rsrq_index": -70, "vbat": 4141,
             "x_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_X_freq.png",
             "y_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_Y_freq.png",
             "z_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_Z_freq.png",
             "x_rms": 6, "y_rms": 197, "z_rms": 5, "P_wave": 0, "S_wave": 0}
})

EXAMPLE_NOTIFY_FIRE = _ex({
	"success": True,
	"message": "災情通報接收並處理成功",
	"data": {
		"report_id": "MATAIA_20260527_0012",
    "timestamp": "2026-05-27T19:15:30Z",
    "source_channel": "Satellite_SMS_Bridge",
    "network_telemetry": {
        "carrier": "Brocere_NTN_Network",
        "mode": "NTN_GEO_SATELLITE",
        "rssi": -118,
        "latency_ms": 650
    },
    "raw_input_text": "我是馬太鞍溪上游巡檢員，剛剛大雨不停，發現堰塞湖水位暴漲已經開始溢流了！而且旁邊山壁發生土石流導致道路坍方，目前手機完全沒有行動通訊訊號，我是透過魔塊衛星發出這條 SOS 求救，請指揮中心立刻派人撤離下游居民！",
    "ai_nlp_analysis": {
        "primary_disaster_type": "Barrier_Lake_Overflow",
        "secondary_disaster_type": "Debris_Flow",
        "threat_level": "CRITICAL",
        "confidence_score": 0.96,
        "extracted_keywords": [
            "水位暴漲",
            "堰塞湖溢流",
            "發生土石流",
            "道路坍方",
            "沒有行動通訊訊號",
            "SOS",
            "立刻派人"
        ]
    },
    "extracted_entities": {
        "location": {
            "reported_place": "花蓮縣馬太鞍溪上游堰塞湖",
            "latitude": 23.6342,
            "longitude": 121.3856,
            "coordinate_accuracy": "GPS_High_Precision"
        },
        "impact_objects": [
            "下游居民",
            "聯外道路"
        ],
        "urgent_requests": [
            "人員撤離",
            "搜救派遣"
        ]
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
	},
	"timestamp": 1780024258
})

EXAMPLE_REPORT = _ex({
    "success": True, "message": "民生物聯網災情通報資料擷取成功", "timestamp": 1748390400,
    "data": [{"city_name": "花蓮縣", "amber_rivers": "3", "red_rivers": "1", "amber_collapse": "2", "red_collapse": "1",
              "total_amber_twp": "3", "total_amber_vil": "6", "total_red_twp": "2", "total_red_vil": "3",
              "total_rivers": "4", "total_collapse": "3", "status": 1, "no_data_mark": None,
              "rpt_time": "2026-05-28T06:31:04.0000000+08:00"}]
})

EXAMPLE_REPORT_INFO = _ex({
    "success": True, "message": "民生物聯網通報欄位說明擷取成功", "timestamp": 1748390400,
    "data": {
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
        "no_data_mark": "無資料可填寫",
        "rpt_time": "通報時間",
    }
})
