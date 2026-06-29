import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

from config.settings import PORT
from routers import notify, data, analyze

app = FastAPI(title="通報 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("call.html")

@app.get("/analysis", include_in_schema=False)
async def analysis_page():
    return FileResponse("analysis.html")

app.include_router(notify.router)
app.include_router(data.router)
app.include_router(analyze.router)

if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
