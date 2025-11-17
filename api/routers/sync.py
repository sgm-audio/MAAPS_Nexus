"""
Sync & Clock API Router
Endpoints for tempo, transport, and synchronization control
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from api.schemas.sync import (
    SetTempoRequest, TempoResponse,
    TapTempoResponse, TransportResponse,
    ClockStatusResponse,
    EnableMIDIClockRequest, MIDIClockResponse,
    EnableLinkRequest, AbletonLinkResponse
)
from api.schemas.common import success_response
from api.message_bus_adapter import get_message_bus_adapter, MessageBusAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tempo/set", response_model=dict)
async def set_tempo(
    request: SetTempoRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Set tempo and time signature"""
    try:
        response = await adapter.request(
            "sync.tempo.set",
            request.dict(),
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Set tempo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tempo/tap", response_model=dict)
async def tap_tempo(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Tap tempo"""
    try:
        response = await adapter.request(
            "sync.tap.tempo",
            {},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Tap tempo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transport/play", response_model=dict)
async def transport_play(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Start transport playback"""
    try:
        response = await adapter.request(
            "sync.transport.play",
            {},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Transport play error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transport/stop", response_model=dict)
async def transport_stop(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Stop transport playback"""
    try:
        response = await adapter.request(
            "sync.transport.stop",
            {},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Transport stop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transport/pause", response_model=dict)
async def transport_pause(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Pause transport playback"""
    try:
        response = await adapter.request(
            "sync.transport.pause",
            {},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Transport pause error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=dict)
async def get_clock_status(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Get clock status"""
    try:
        response = await adapter.request(
            "sync.status.get",
            {},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/midi-clock/enable", response_model=dict)
async def enable_midi_clock(
    request: EnableMIDIClockRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Enable/disable MIDI clock output"""
    try:
        response = await adapter.request(
            "sync.midi.clock.enable",
            request.dict(),
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"MIDI clock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link/enable", response_model=dict)
async def enable_ableton_link(
    request: EnableLinkRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Enable/disable Ableton Link"""
    try:
        response = await adapter.request(
            "sync.link.enable",
            request.dict(),
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Ableton Link error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
