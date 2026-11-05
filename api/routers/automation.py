"""
Performance Automation API Router
Endpoints for automation recording, scenes, macros, and cues
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from api.schemas.automation import (
    StartRecordingRequest,
    RecordingResponse,
    EnablePlaybackRequest,
    PlaybackResponse,
    CreateSceneRequest,
    SceneResponse,
    TriggerSceneResponse,
    CreateMacroRequest,
    MacroResponse,
    ChangeMacroRequest,
    MacroValueResponse,
    CreateCueRequest,
    CueResponse,
    FireCueResponse,
)
from api.schemas.common import success_response
from api.message_bus_adapter import get_message_bus_adapter, MessageBusAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/record/start", response_model=dict)
async def start_automation_recording(
    request: StartRecordingRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Start automation recording"""
    try:
        response = await adapter.request(
            "automation.record.start", request.dict(), timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Start recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record/stop", response_model=dict)
async def stop_automation_recording(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Stop automation recording"""
    try:
        response = await adapter.request("automation.record.stop", {}, timeout=2.0)

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Stop recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playback/enable", response_model=dict)
async def enable_automation_playback(
    request: EnablePlaybackRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Enable/disable automation playback"""
    try:
        response = await adapter.request(
            "automation.playback.enable", request.dict(), timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Enable playback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenes", response_model=dict, status_code=201)
async def create_scene(
    request: CreateSceneRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Create automation scene"""
    try:
        response = await adapter.request(
            "automation.scene.create", request.dict(), timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Create scene error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenes/{scene_id}/trigger", response_model=dict)
async def trigger_scene(
    scene_id: str, adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Trigger automation scene"""
    try:
        response = await adapter.request(
            "automation.scene.trigger", {"scene_id": scene_id}, timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Trigger scene error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/macros", response_model=dict, status_code=201)
async def create_macro(
    request: CreateMacroRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Create macro control"""
    try:
        response = await adapter.request(
            "automation.macro.create", request.dict(), timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Create macro error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/macros/{macro_id}/value", response_model=dict)
async def change_macro_value(
    macro_id: str,
    request: ChangeMacroRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Change macro value"""
    try:
        response = await adapter.request(
            "automation.macro.change",
            {"macro_id": macro_id, "value": request.value},
            timeout=2.0,
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Change macro error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cues", response_model=dict, status_code=201)
async def create_cue(
    request: CreateCueRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter),
):
    """Create performance cue"""
    try:
        response = await adapter.request(
            "automation.cue.create", request.dict(), timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Create cue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cues/{cue_id}/fire", response_model=dict)
async def fire_cue(
    cue_id: str, adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Fire performance cue manually"""
    try:
        response = await adapter.request(
            "automation.cue.fire", {"cue_id": cue_id}, timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Fire cue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
