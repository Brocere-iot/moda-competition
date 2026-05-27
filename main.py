from fastapi import FastAPI, HTTPException, status
from database.mock_db import mock_incline_data, mock_fire_data
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 8000))

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/notify/land_slide")
async def notify_land_slide():
    return {"message": "Land slide notification sent."}

@app.post("/notify/fire")
async def notify_land_slide():
    return {"message": "Land slide notification sent."}

@app.get("/data/incline/{station_id}")
async def get_incline_data(station_id: int):
    print('ID received:', station_id)  # Debugging statement to check the received ID
    if station_id < 0 or station_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Station ID must be a non-negative integer."
        )
    # 1. Fetch the data from your mock DB
    incline_data = mock_incline_data(station_id=station_id)
    
    # 2. Check if the database actually found data for that ID
    if not incline_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Station with ID {station_id} does not exist."
        )
    
    # 3. If data exists, return it. FastAPI automatically sends a real HTTP 200 status.
    return {"sensor_data": incline_data}

@app.get("/data/fire/{station_id}")
async def get_fire_data(station_id: int):
    print('ID received:', station_id)  # Debugging statement to check the received ID
    if station_id < 0 or station_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Station ID must be a non-negative integer."
        )
    # 1. Fetch the data from your mock DB
    fire_data = mock_fire_data(station_id=station_id)
    
    # 2. Check if the database actually found data for that ID
    if not fire_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Station with ID {station_id} does not exist."
        )
    
    # 3. If data exists, return it. FastAPI automatically sends a real HTTP 200 status.
    return {"sensor_data": fire_data}

if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)