from fastapi import APIRouter, HTTPException, Query, status
from typing import List
import httpx

from database.mock_db import mock_fire_data, mock_earthquake_data
from utils.response_helper import success_response, error_response
from config.response_example import EXAMPLE_FIRE, EXAMPLE_EARTHQUAKE, EXAMPLE_REPORT, EXAMPLE_REPORT_INFO
from config.field_labels import DETAIL_FIELD_LABELS

router = APIRouter(prefix="/data")


@router.get("/fire/{station_id}", responses={200: EXAMPLE_FIRE})
async def get_fire_data(station_id: int):
    if station_id < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Station ID must be a non-negative integer.")
    fire_data = mock_fire_data()
    if not fire_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Station with ID {station_id} does not exist.")
    return success_response(
        message=f"Fire data for station {station_id} retrieved successfully.",
        data={"station_id": station_id, **fire_data}
    )


@router.get("/earthquake/{station_id}", responses={200: EXAMPLE_EARTHQUAKE})
async def get_earthquake_data(station_id: int):
    if station_id < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Station ID must be a non-negative integer.")
    earthquake_data = mock_earthquake_data()
    if not earthquake_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Station with ID {station_id} does not exist.")
    return success_response(
        message=f"Earthquake data for station {station_id} retrieved successfully.",
        data={"station_id": station_id, **earthquake_data}
    )


@router.get("/report", responses={200: EXAMPLE_REPORT})
async def get_report_data(city_name: List[str] = Query(default=None)):
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
    flattened = [{"source": "EMIC_OpenData", **city, "rpt_time": rpt_time} for city in detail]
    return success_response(message="民生物聯網災情通報資料擷取成功", data=flattened)


@router.get("/report/info", summary="民生物聯網通報欄位說明", responses={200: EXAMPLE_REPORT_INFO})
async def get_report_field_info():
    return success_response(message="民生物聯網通報欄位說明擷取成功", data=DETAIL_FIELD_LABELS)
