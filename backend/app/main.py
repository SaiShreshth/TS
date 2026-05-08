import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request # Added Request
from fastapi.responses import JSONResponse # Added JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

logger = logging.getLogger("app.env")

# Load environment variables from repo-root .env file
BASE_DIR = Path(__file__).resolve().parents[2]
DOTENV_PATH = BASE_DIR / ".env"
dotenv_loaded = load_dotenv(dotenv_path=DOTENV_PATH)

logger.info("Env load: %s", "loaded" if dotenv_loaded else "not found")
logger.info("Env path: %s", DOTENV_PATH)

test_value = os.getenv("test") or os.getenv("TEST")
if test_value is None:
    logger.warning("Env check: test variable missing. Set test=correct in .env.")
elif test_value != "correct":
    logger.warning("Env check: test variable mismatch. Expected 'correct', got '%s'.", test_value)
else:
    logger.info("Env check: test variable loaded correctly.")

logger.info(
    "Env check: GEMINI_API_KEY %s",
    "set" if os.getenv("GEMINI_API_KEY") else "missing",
)
logger.info("Env check: GEMINI_MODEL=%s", os.getenv("GEMINI_MODEL") or "<default>")

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
