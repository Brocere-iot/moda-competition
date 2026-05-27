import random
import time 
from utils.response_helper import populate_meta_data

def mock_incline_data(station_id):
    current_timestamp = int(time.time())
    mock_water_level_meter = random.uniform(0, 10)
    mock_soil_inclination_degree = random.uniform(0, 30)

    incline_data_dict = {
        "timestamp": current_timestamp,
        "water_level_meter": mock_water_level_meter,
        "soil_inclination_degree": mock_soil_inclination_degree,
        'station_id': f"Mataian_{station_id}"
    }
    incline_data_dict = populate_meta_data(incline_data_dict)

    return incline_data_dict

def mock_fire_data(station_id):
    current_timestamp = int(time.time())
    mock_temperature_celsius = random.uniform(15, 99)
    mock_co2_density = random.randint(0, 10000)

    fire_data_dict = {
        "timestamp": current_timestamp,
        "temp": mock_temperature_celsius,
        "co2": mock_co2_density,
        'station_id': f"Mataian_{station_id}"
    }
    fire_data_dict = populate_meta_data(fire_data_dict)

    return fire_data_dict