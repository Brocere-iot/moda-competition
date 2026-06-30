from pydantic import BaseModel, Field
from typing import List


class AnalyzeRequest(BaseModel):
    iot_sensors: List[dict] = Field(default_factory=list, description="IoT 感測器原始資料列表")
    human_reports: List[dict] = Field(default_factory=list, description="現場人員白話文通報列表")
    external_data: List[dict] = Field(default_factory=list, description="外部開放資料（氣象、地震等）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "iot_sensors": [
                    {
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
