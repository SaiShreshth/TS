import os
from fastapi import FastAPI, Request # Added Request
from fastapi.responses import JSONResponse # Added JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI()

# 1. Define origins
allow_origins = ["*","http://localhost:4173/","http://localhost:3000/","http://172.19.0.4:4173/","http://172.19.0.4:3000/"]  # Adjust as needed for your frontend development server

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Exception Handler (Catches server crashes and adds CORS headers)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*", 
        }
    )

# 4. Include Router
app.include_router(router)
