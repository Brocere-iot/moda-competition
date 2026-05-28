def _ex(example):
    return {"content": {"application/json": {"example": example}}}


EXAMPLE_FIRE = _ex({
    "statusCode": 200, "message": "Fire data for station 1 retrieved successfully.", "station_id": 1,
    "data": {"timestamp": 1748390400, "tw_time": "2026-05-28 14:00:00", "rsrq_index": -82, "vbat": 3750,
             "temp": 87.3, "humi": 38.1, "co2": -3108,
             "url": "https://d65hb6cahdqvu.cloudfront.net/04702154615/1779353739.png"}
})

EXAMPLE_EARTHQUAKE = _ex({
    "statusCode": 200, "message": "Earthquake data for station 23 retrieved successfully.", "station_id": 23,
    "data": {"timestamp": 1779951869, "tw_time": "2026-05-28 15:04:29", "rsrq_index": -70, "vbat": 4141,
             "x_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_X_freq.png",
             "y_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_Y_freq.png",
             "z_freq_fft_figure": "https://d82xcsxd0ol35.cloudfront.net/04702154614/1779849793_Z_freq.png",
             "x_rms": 6, "y_rms": 197, "z_rms": 5, "P_wave": 0, "S_wave": 0}
})

EXAMPLE_NOTIFY_FIRE = _ex({
    "success": True,
    "message": "已收到您的回報！\n通報時間：2026-05-28 14:00\n案件類型：土石流/崩塌\n地點：馬太鞍溪地區\n警急性：緊急",
    "data": {"station_id": "LINE_CITIZEN_REPORT_01", "timestamp": "2026-05-28T06:00:00Z",
             "raw_content": "我是馬太鞍溪上游巡檢員，發現堰塞湖水位暴漲，土石流導致道路坍方，請立刻撤離！",
             "structured_data": {"location": "花蓮縣馬太鞍溪地區 (經確認)", "hazard_type": "LANDSLIDE", "danger_level": "CRITICAL"},
             "human_readable_reply": "已收到您的回報！\n通報時間：2026-05-28 14:00\n案件類型：土石流/崩塌\n地點：馬太鞍溪地區\n警急性：緊急"},
    "timestamp": 1748390400
})

EXAMPLE_REPORT = _ex({
    "success": True, "message": "Success", "timestamp": 1748390400,
    "data": [{"city_name": "花蓮縣", "amber_rivers": "3", "red_rivers": "1", "amber_collapse": "2", "red_collapse": "1",
              "total_amber_twp": "3", "total_amber_vil": "6", "total_red_twp": "2", "total_red_vil": "3",
              "total_rivers": "4", "total_collapse": "3", "status": "應變一級警戒", "no_data_mark": None,
              "rpt_time": "2026-05-28T06:31:04.0000000+08:00"}]
})

EXAMPLE_REPORT_INFO = _ex({
    "success": True, "message": "Success", "timestamp": 1748390400,
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
