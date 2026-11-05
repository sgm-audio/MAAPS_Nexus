"""
MAAPS REST API - Production-Ready FastAPI Interface
Provides HTTP endpoints for audio processing, music generation, live performance, and system management

Usage:
    Development: uvicorn api.main:app --reload
    Production:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import numpy as np
import base64
import asyncio
from datetime import datetime
import logging
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from api.auth import router as auth_router, verify_token
from src.system import create_system

# Import routers
from api.routers import (
    audio,
    metadata,
    effects,
    looping,
    sync,
    automation,
    system as system_router
)
from api import auth
from api.dependencies import get_current_user, get_optional_user
from api.message_bus_adapter import get_message_bus_adapter
from api.websocket import websocket_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MAAPS API",
    description="Multi-Agent Audio Processing System REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - environment-based configuration
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include root routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(audio.router)      # /audio/*
app.include_router(metadata.router)   # /metadata/*

# Include /api/v1 routers (Phase 2 & 3 + UI client)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication V1"])
app.include_router(effects.router, prefix="/api/v1/effects", tags=["Effects Chain"])
app.include_router(looping.router, prefix="/api/v1/looping", tags=["Live Looping"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Sync & Clock"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["Performance Automation"])
app.include_router(system_router.router, prefix="/api/v1/system", tags=["System V1"])
app.include_router(audio.router, prefix="/api/v1")
app.include_router(metadata.router, prefix="/api/v1")

# Global system instance
system = None


def _ensure_system_ready() -> "MultiAgentSystem":
    """Return initialized system, initializing lazily if needed, or raise 503."""
    global system
    from src.system import MultiAgentSystem  # local import to avoid cycles

    if system is None or not isinstance(system, MultiAgentSystem):
        system = create_system()
    if not getattr(system, "initialized", False):
        system.start()
    return system


def get_system_dep():
    """FastAPI dependency to guarantee system availability."""
    return _ensure_system_ready()


# Request/Response Models
MAX_AUDIO_SAMPLES = 2_000_000  # ~45 seconds at 44.1kHz


class AudioEnhanceRequest(BaseModel):
    audio_data: List[float] = Field(..., description="Audio samples as array of floats")
    sample_rate: int = Field(44100, description="Sample rate in Hz", ge=8000, le=192000)
    noise_reduction: float = Field(
        0.8, description="Noise reduction amount", ge=0.0, le=1.0
    )
    declicking_sensitivity: float = Field(
        0.5, description="Click removal sensitivity", ge=0.0, le=1.0
    )
    preserve_transients: bool = Field(True, description="Preserve sharp transients")

    @classmethod
    def model_validate(cls, value):
        obj = super().model_validate(value)
        if len(obj.audio_data) > MAX_AUDIO_SAMPLES:
            raise ValueError(f"audio_data too large (max {MAX_AUDIO_SAMPLES} samples)")
        return obj


class MusicGenerateRequest(BaseModel):
    content_type: str = Field(..., description="Type: melody, harmony, drums, bass")
    key: str = Field("C major", description="Musical key")
    tempo: float = Field(120.0, description="Tempo in BPM", ge=60.0, le=200.0)
    time_signature: str = Field("4/4", description="Time signature")
    chord_progression: List[str] = Field(
        ["C", "Am", "F", "G"], description="Chord progression"
    )
    length_bars: int = Field(8, description="Length in bars", ge=1, le=64)


class MetadataExtractRequest(BaseModel):
    audio_data: List[float] = Field(..., description="Audio samples")
    sample_rate: int = Field(44100, description="Sample rate in Hz")
    deep_analysis: bool = Field(True, description="Perform deep analysis")

    @classmethod
    def model_validate(cls, value):
        obj = super().model_validate(value)
        if len(obj.audio_data) > MAX_AUDIO_SAMPLES:
            raise ValueError(f"audio_data too large (max {MAX_AUDIO_SAMPLES} samples)")
        return obj


class HealthResponse(BaseModel):
    health_score: float
    agents_healthy: int
    agents_total: int
    system_uptime_seconds: float
    timestamp: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    result: Optional[Dict] = None
    error: Optional[str] = None


# Background job storage
jobs = {}


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize MAAPS system on startup"""
    global system
    logger.info("Starting MAAPS system...")
    system = create_system()
    system.start()
    adapter = get_message_bus_adapter()
    await adapter.start()
    await websocket_manager.start()
    logger.info("MAAPS system started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown MAAPS system gracefully"""
    global system
    await websocket_manager.stop()
    adapter = get_message_bus_adapter()
    await adapter.stop()
    if system:
        logger.info("Shutting down MAAPS system...")
        system.stop()
        logger.info("MAAPS system stopped")


# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time event WebSocket endpoint"""
    client_id = await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await websocket_manager.handle_message(client_id, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        websocket_manager.disconnect(client_id)


# Health & Status Endpoints
@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "name": "MAAPS API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Get system health status"""
    try:
        sys = get_system_dep()
        health = sys.get_health()
        return HealthResponse(
            health_score=health["health_score"],
            agents_healthy=health["agents_healthy"],
            agents_total=health["agents_total"],
            system_uptime_seconds=health["system_uptime_seconds"],
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Get system resource metrics"""
    try:
        sys = get_system_dep()
        metrics = sys.get_resource_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", tags=["System"])
async def list_agents():
    """Get list of all agents and their status"""
    try:
        sys = get_system_dep()
        agents = sys.get_all_agents()
        return JSONResponse(content={"agents": agents})
    except Exception as e:
        logger.error(f"Agent list retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audio/metadata", tags=["Audio Processing"])
async def extract_metadata(
    request: MetadataExtractRequest,
    username: Optional[str] = Depends(get_optional_user),
    sys=Depends(get_system_dep)
):
    """
    Extract metadata from audio
    """
    try:
        user_context = f" (user: {username})" if username else " (anonymous)"
        logger.info(f"Metadata extraction{user_context}: {len(request.audio_data)} samples")

        metadata_res = sys.extract_metadata(
            audio_data=request.audio_data,
            sample_rate=request.sample_rate,
            deep_analysis=request.deep_analysis,
        )

        if username:
            metadata_res['authenticated_user'] = username

        logger.info("Metadata extraction complete")
        return JSONResponse(content=metadata_res)

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Music Generation Endpoints
@app.post("/music/generate", tags=["Music Generation"])
async def generate_music(
    request: MusicGenerateRequest,
    username: Optional[str] = Depends(get_optional_user),
    sys=Depends(get_system_dep)
):
    """
    Generate AI music (melody, harmony, drums, or bass)
    """
    try:
        if request.content_type not in ["melody", "harmony", "drums", "bass"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid content_type: {request.content_type}. "
                    "Must be melody, harmony, drums, or bass"
                ),
            )

        user_context = f" (user: {username})" if username else " (anonymous)"
        logger.info(f"Music generation{user_context}: {request.content_type} in {request.key} @ {request.tempo}BPM")

        musical_context = {
            "key": request.key,
            "tempo": request.tempo,
            "time_signature": request.time_signature,
            "chord_progression": request.chord_progression,
            "length_bars": request.length_bars,
        }

        result = sys.generate_music(request.content_type, musical_context)

        if username:
            result['authenticated_user'] = username

        logger.info(f"Music generation complete: {len(result.get('notes', []))} notes")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Batch Processing Endpoints
@app.post("/batch/enhance", tags=["Batch Processing"])
async def batch_enhance(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    username: str = Depends(verify_token),
):
    """
    Batch audio enhancement (async processing)
    """
    job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "total_files": len(files),
        "processed_files": 0,
        "results": [],
    }

    return JSONResponse(content={
        'job_id': job_id,
        'status': 'queued',
        'message': f'Batch job created with {len(files)} files'
    })


@app.get("/batch/{job_id}", response_model=JobStatusResponse, tags=["Batch Processing"])
async def get_batch_status(job_id: str, username: str = Depends(verify_token)):
    """Get status of batch processing job (authenticated)"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result=job.get("results"),
        error=job.get("error"),
    )


# Utility Endpoints
@app.post("/system/restart", tags=["System"])
async def restart_system(username: str = Depends(get_current_user)):
    """Restart the MAAPS system (requires authentication)"""
    try:
        logger.info(f"System restart requested by {username}")
        sys = get_system_dep()
        sys.stop()
        await asyncio.sleep(0.5)
        sys.start()
        logger.info("System restarted successfully")
        return {"status": "success", "message": "System restarted", "requested_by": username}
    except Exception as e:
        logger.error(f"System restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/version", tags=["System"])
async def get_version():
    """Get API and system version information"""
    return {
        "api_version": "1.0.0",
        "system_version": "1.0.0",
        "python_version": "3.11+",
        "agents": 10
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
    )


# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
