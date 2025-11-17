"""
Live Looping API Router
Endpoints for managing loop tracks, recording, and manipulation
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from api.schemas.looping import (
    CreateTrackRequest, TrackResponse,
    StartRecordingRequest, RecordingStartedResponse, RecordingStoppedResponse,
    PlaybackResponse, ManipulateRequest, ManipulationResponse,
    UndoResponse, TrackStatusResponse, TrackListResponse
)
from api.schemas.common import success_response
from api.message_bus_adapter import get_message_bus_adapter, MessageBusAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tracks", response_model=dict, status_code=201)
async def create_loop_track(
    request: CreateTrackRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Create a new loop track"""
    try:
        response = await adapter.request(
            "loop.track.create",
            request.dict(),
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Create track error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracks", response_model=dict)
async def list_loop_tracks(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """List all loop tracks"""
    try:
        response = await adapter.request(
            "loop.track.list",
            {},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"List tracks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracks/{track_id}", response_model=dict)
async def get_loop_track(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Get loop track details"""
    try:
        response = await adapter.request(
            "loop.track.get",
            {"track_id": track_id},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Get track error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/record/start", response_model=dict)
async def start_recording(
    track_id: str,
    request: StartRecordingRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Start recording on a loop track"""
    try:
        response = await adapter.request(
            "loop.record.start",
            {
                "track_id": track_id,
                "mode": request.mode
            },
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Start recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/record/stop", response_model=dict)
async def stop_recording(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Stop recording on a loop track"""
    try:
        response = await adapter.request(
            "loop.record.stop",
            {"track_id": track_id},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Stop recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/playback/toggle", response_model=dict)
async def toggle_playback(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Toggle playback on a loop track"""
    try:
        response = await adapter.request(
            "loop.playback.toggle",
            {"track_id": track_id},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Toggle playback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/manipulate", response_model=dict)
async def manipulate_loop(
    track_id: str,
    request: ManipulateRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Manipulate loop (reverse, pitch shift, time stretch, etc.)"""
    try:
        response = await adapter.request(
            "loop.manipulate",
            {
                "track_id": track_id,
                "operation": request.operation,
                "parameters": request.parameters or {}
            },
            timeout=10.0  # Longer timeout for processing
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Manipulate loop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/undo", response_model=dict)
async def undo_loop(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Undo last operation on loop track"""
    try:
        response = await adapter.request(
            "loop.undo",
            {"track_id": track_id},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Undo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/redo", response_model=dict)
async def redo_loop(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Redo last undone operation on loop track"""
    try:
        response = await adapter.request(
            "loop.redo",
            {"track_id": track_id},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Redo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracks/{track_id}/clear", response_model=dict)
async def clear_loop(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Clear loop track"""
    try:
        response = await adapter.request(
            "loop.clear",
            {"track_id": track_id},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Clear loop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tracks/{track_id}", response_model=dict)
async def delete_loop_track(
    track_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Delete a loop track"""
    try:
        response = await adapter.request(
            "loop.track.delete",
            {"track_id": track_id},
            timeout=3.0
        )

        return success_response(response, message=f"Track {track_id} deleted")

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Delete track error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
