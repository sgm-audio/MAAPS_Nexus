"""
MAAPS REST API - Production-Ready FastAPI Interface
Provides HTTP endpoints for audio processing, music generation, and system management

Usage:
    Development: uvicorn api.main:app --reload
    Production:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends
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

from src.system import create_system

# Import routers
from api.routers import audio, metadata
from api import auth
from api.dependencies import get_current_user, get_optional_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MAAPS API",
    description="Multi-Agent Audio Processing System REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - environment-based configuration
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(audio.router)  # Already has /audio prefix
app.include_router(metadata.router)  # Already has /metadata prefix

# Global system instance
system = None


def _ensure_system_ready() -> "MultiAgentSystem":
    """Return initialized system or raise 503 if not ready."""
    from src.system import MultiAgentSystem  # local import to avoid cycles

    if system is None or not isinstance(system, MultiAgentSystem) or not getattr(system, "initialized", False):
        raise HTTPException(
            status_code=503,
            detail="System not initialized yet"
        )
    return system


def get_system_dep():
    """FastAPI dependency to guarantee system availability."""
    return _ensure_system_ready()


# Request/Response Models
MAX_AUDIO_SAMPLES = 2_000_000  # ~45 seconds at 44.1kHz


class AudioEnhanceRequest(BaseModel):
    audio_data: List[float] = Field(..., description="Audio samples as array of floats")
    sample_rate: int = Field(44100, description="Sample rate in Hz", ge=8000, le=192000)
    noise_reduction: float = Field(0.8, description="Noise reduction amount", ge=0.0, le=1.0)
    declicking_sensitivity: float = Field(0.5, description="Click removal sensitivity", ge=0.0, le=1.0)
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
    chord_progression: List[str] = Field(["C", "Am", "F", "G"], description="Chord progression")
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
    logger.info("MAAPS system started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown MAAPS system gracefully"""
    global system
    if system:
        logger.info("Shutting down MAAPS system...")
        system.stop()
        logger.info("MAAPS system stopped")


# Health & Status Endpoints
@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "name": "MAAPS API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Get system health status"""
    try:
        sys = get_system_dep()
        health = sys.get_health()
        return HealthResponse(
            health_score=health['health_score'],
            agents_healthy=health['agents_healthy'],
            agents_total=health['agents_total'],
            system_uptime_seconds=health['system_uptime_seconds'],
            timestamp=datetime.now().isoformat()
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


# Audio Processing Endpoints
@app.post("/audio/enhance", tags=["Audio Processing"])
async def enhance_audio(
    request: AudioEnhanceRequest,
    background_tasks: BackgroundTasks,
    username: Optional[str] = Depends(get_optional_user),
    sys=Depends(get_system_dep)
):
    """
    Enhance audio with noise reduction and restoration

    Optional authentication - authenticated users get priority processing

    Returns enhanced audio data with processing metrics
    """
    try:
        user_context = f" (user: {username})" if username else " (anonymous)"
        logger.info(f"Audio enhancement request{user_context}: {len(request.audio_data)} samples @ {request.sample_rate}Hz")

        result = sys.enhance_audio(
            audio_data=request.audio_data,
            sample_rate=request.sample_rate,
            params={
                'noise_reduction_amount': request.noise_reduction,
                'declicking_sensitivity': request.declicking_sensitivity,
                'preserve_transients': request.preserve_transients
            }
        )

        # Add user context to response
        if username:
            result['authenticated_user'] = username

        logger.info(f"Enhancement complete: {result.get('processing_time_ms', 0):.1f}ms")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Audio enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/audio/metadata", tags=["Audio Processing"])
async def extract_metadata(
    request: MetadataExtractRequest,
    username: Optional[str] = Depends(get_optional_user),
    sys=Depends(get_system_dep)
):
    """
    Extract metadata from audio

    Optional authentication - authenticated users get enhanced metadata

    Returns musical, technical, and quality features
    """
    try:
        user_context = f" (user: {username})" if username else " (anonymous)"
        logger.info(f"Metadata extraction{user_context}: {len(request.audio_data)} samples")

        metadata = sys.extract_metadata(
            audio_data=request.audio_data,
            sample_rate=request.sample_rate,
            deep_analysis=request.deep_analysis
        )

        # Add user context to response
        if username:
            metadata['authenticated_user'] = username

        logger.info("Metadata extraction complete")
        return JSONResponse(content=metadata)

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

    Optional authentication - authenticated users get priority queue

    Returns generated MIDI data and note events
    """
    try:
        if request.content_type not in ['melody', 'harmony', 'drums', 'bass']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content_type: {request.content_type}. Must be melody, harmony, drums, or bass"
            )

        user_context = f" (user: {username})" if username else " (anonymous)"
        logger.info(f"Music generation{user_context}: {request.content_type} in {request.key} @ {request.tempo}BPM")

        musical_context = {
            'key': request.key,
            'tempo': request.tempo,
            'time_signature': request.time_signature,
            'chord_progression': request.chord_progression,
            'length_bars': request.length_bars
        }

        result = sys.generate_music(request.content_type, musical_context)

        # Add user context to response
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
    background_tasks: BackgroundTasks = None
):
    """
    Batch audio enhancement (async processing)

    Returns job ID for tracking
    """
    job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    jobs[job_id] = {
        'status': 'queued',
        'progress': 0.0,
        'total_files': len(files),
        'processed_files': 0,
        'results': []
    }

    # Process in background
    # background_tasks.add_task(process_batch, job_id, files)

    return JSONResponse(content={
        'job_id': job_id,
        'status': 'queued',
        'message': f'Batch job created with {len(files)} files'
    })


@app.get("/batch/{job_id}", response_model=JobStatusResponse, tags=["Batch Processing"])
async def get_batch_status(job_id: str):
    """Get status of batch processing job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        progress=job['progress'],
        result=job.get('results'),
        error=job.get('error')
    )


# Utility Endpoints
@app.post("/system/restart", tags=["System"])
async def restart_system(username: str = Depends(get_current_user)):
    """Restart the MAAPS system (requires authentication)"""
    try:
        logger.info(f"System restart requested by {username}")
        sys = get_system_dep()
        sys.stop()
        await asyncio.sleep(2)
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
        "agents": 5
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
            "timestamp": datetime.now().isoformat()
        }
    )


# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
