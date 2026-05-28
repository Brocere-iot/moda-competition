from fastapi import FastAPI, HTTPException, Query, status
from typing import Liste
import httpx
import uvicorn
import os
from dotenv import load_dotenv
from database.mock_db import mock_earthquake_data, mock_fire_data
from utils.response_helper import success_response, error_response

load_dotenv()

PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="通報 API")


@app.get("/")
async def root():
    return success_response(message="Hello World")

@app.post("/notify/land_slide")
async def notify_land_slide():
    return success_response(message="Land slide notification sent.")

@app.post("/notify/fire")
async def notify_fire():
    return success_response(message="Fire notification sent.")

@app.get("/data/fire/{station_id}")
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
    return {
        "statusCode": 200,
        "message": f"Fire data for station {station_id} retrieved successfully.",
        "station_id": station_id,
        "data": fire_data,
        }

@app.get("/data/earthquake/{station_id}")
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
    return {
        "statusCode": 200,
        "message": f"Earthquake data for station {station_id} retrieved successfully.",
        "station_id": station_id,
        "data": earthquake_data,
        }


@app.get("/data/report")
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
    return success_response(data=flattened)

if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)