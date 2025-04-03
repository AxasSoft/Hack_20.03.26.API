import os

import redis
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.api.api_v1.api import api_router
from app.core.config import settings

from datetime import datetime

from fastapi import FastAPI,  Request
from fastapi.middleware import Middleware
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.types import ASGIApp, Receive, Scope, Send
from app.crud.crud_dating_profile import dating_profile
import time

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"Request processed in {process_time} seconds")
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


scheduler = BackgroundScheduler()

# планировщик
# scheduler.add_job(dating_profile._recalculate_weights, CronTrigger.from_crontab('0 0 * * *')) 
# Планировщик
scheduler.add_job(dating_profile._recalculate_weights, IntervalTrigger(minutes=180))

scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

from . import errors
from app import tasks