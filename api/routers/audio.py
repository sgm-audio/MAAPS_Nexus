"""
Audio Processing API Router
Endpoints for audio enhancement and music generation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["Audio Processing"])


# Request Models
class AudioEnhanceRequest(BaseModel):
    audio_data: List[float] = Field(..., description="Audio samples as array of floats")
    sample_rate: int = Field(44100, description="Sample rate in Hz", ge=8000, le=192000)
    noise_reduction: float = Field(0.8, description="Noise reduction amount", ge=0.0, le=1.0)
    declicking_sensitivity: float = Field(0.5, description="Click removal sensitivity", ge=0.0, le=1.0)
    preserve_transients: bool = Field(True, description="Preserve sharp transients")


class MusicGenerateRequest(BaseModel):
    content_type: str = Field(..., description="Type: melody, harmony, drums, bass")
    key: str = Field("C major", description="Musical key")
    tempo: float = Field(120.0, description="Tempo in BPM", ge=60.0, le=200.0)
    time_signature: str = Field("4/4", description="Time signature")
    chord_progression: List[str] = Field(["C", "Am", "F", "G"], description="Chord progression")
    length_bars: int = Field(8, description="Length in bars", ge=1, le=64)


# Dependency to get system instance
def get_system():
    """Get the MAAPS system instance"""
    from api.main import system
    if system is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    return system


@router.post("/enhance")
async def enhance_audio(
    request: AudioEnhanceRequest,
    background_tasks: BackgroundTasks,
    system=Depends(get_system)
):
    """
    Enhance audio with noise reduction and restoration

    Returns enhanced audio data with processing metrics
    """
    try:
        logger.info(f"Audio enhancement request: {len(request.audio_data)} samples @ {request.sample_rate}Hz")

        result = system.enhance_audio(
            audio_data=request.audio_data,
            sample_rate=request.sample_rate,
            params={
                'noise_reduction_amount': request.noise_reduction,
                'declicking_sensitivity': request.declicking_sensitivity,
                'preserve_transients': request.preserve_transients
            }
        )

        logger.info(f"Enhancement complete: {result.get('processing_time_ms', 0):.1f}ms")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Audio enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_music(
    request: MusicGenerateRequest,
    system=Depends(get_system)
):
    """
    Generate AI music (melody, harmony, drums, or bass)

    Returns generated MIDI data and note events
    """
    try:
        if request.content_type not in ['melody', 'harmony', 'drums', 'bass']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content_type: {request.content_type}. Must be melody, harmony, drums, or bass"
            )

        logger.info(f"Music generation: {request.content_type} in {request.key} @ {request.tempo}BPM")

        musical_context = {
            'key': request.key,
            'tempo': request.tempo,
            'time_signature': request.time_signature,
            'chord_progression': request.chord_progression,
            'length_bars': request.length_bars
        }

        result = system.generate_music(request.content_type, musical_context)

        logger.info(f"Music generation complete: {len(result.get('notes', []))} notes")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported audio formats"""
    return {
        "input_formats": ["wav", "flac", "mp3", "ogg", "m4a"],
        "output_formats": ["wav", "flac", "mp3", "ogg"],
        "sample_rates": [8000, 16000, 22050, 44100, 48000, 88200, 96000, 192000],
        "bit_depths": [16, 24, 32]
    }


@router.get("/processing-stats")
async def get_processing_stats(system=Depends(get_system)):
    """Get audio processing statistics"""
    try:
        # This would typically come from telemetry
        return {
            "total_processed": 0,
            "average_processing_time_ms": 0,
            "active_jobs": 0
        }
    except Exception as e:
        logger.error(f"Failed to get processing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
