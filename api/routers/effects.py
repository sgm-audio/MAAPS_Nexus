"""
Effects Chain API Router
Endpoints for managing live effects chains, presets, and scenes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from api.schemas.effects import (
    CreateChainRequest, EffectChainResponse, ChainDetailResponse,
    UpdateParametersRequest, BypassRequest,
    SavePresetRequest, PresetResponse,
    CreateSceneRequest, SceneResponse
)
from api.schemas.common import success_response
from api.message_bus_adapter import get_message_bus_adapter, MessageBusAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chains", response_model=dict, status_code=201)
async def create_effect_chain(
    request: CreateChainRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Create a new effect chain"""
    try:
        response = await adapter.request(
            "effects.chain.create",
            {
                "chain_name": request.chain_name,
                "effects": [e.dict() for e in request.effects]
            },
            timeout=5.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Create chain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains", response_model=dict)
async def list_effect_chains(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """List all effect chains"""
    try:
        response = await adapter.request(
            "effects.chain.list",
            {},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"List chains error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/{chain_id}", response_model=dict)
async def get_effect_chain(
    chain_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Get effect chain details"""
    try:
        response = await adapter.request(
            "effects.chain.get",
            {"chain_id": chain_id},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Get chain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/chains/{chain_id}/effects/{effect_id}/parameters", response_model=dict)
async def update_effect_parameters(
    chain_id: str,
    effect_id: str,
    request: UpdateParametersRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Update effect parameters"""
    try:
        response = await adapter.request(
            "effects.parameter.change",
            {
                "chain_id": chain_id,
                "effect_id": effect_id,
                "parameters": request.parameters
            },
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Update parameters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chains/{chain_id}/effects/{effect_id}/bypass", response_model=dict)
async def toggle_effect_bypass(
    chain_id: str,
    effect_id: str,
    request: BypassRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Toggle effect bypass"""
    try:
        response = await adapter.request(
            "effects.bypass.toggle",
            {
                "chain_id": chain_id,
                "effect_id": effect_id,
                "bypass": request.bypass
            },
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Toggle bypass error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chains/{chain_id}", response_model=dict)
async def delete_effect_chain(
    chain_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Delete an effect chain"""
    try:
        response = await adapter.request(
            "effects.chain.delete",
            {"chain_id": chain_id},
            timeout=3.0
        )

        return success_response(response, message=f"Chain {chain_id} deleted")

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Delete chain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets", response_model=dict, status_code=201)
async def save_preset(
    request: SavePresetRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Save effect chain as preset"""
    try:
        response = await adapter.request(
            "effects.preset.save",
            {
                "preset_name": request.preset_name,
                "chain_id": request.chain_id
            },
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Save preset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chains/{chain_id}/presets/{preset_id}/recall", response_model=dict)
async def recall_preset(
    chain_id: str,
    preset_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Recall a preset for an effect chain"""
    try:
        response = await adapter.request(
            "effects.preset.recall",
            {
                "chain_id": chain_id,
                "preset_id": preset_id
            },
            timeout=3.0
        )

        return success_response(response, message=f"Preset recalled")

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Recall preset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenes", response_model=dict, status_code=201)
async def create_scene(
    request: CreateSceneRequest,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Create a new scene"""
    try:
        response = await adapter.request(
            "effects.scene.create",
            {
                "scene_name": request.scene_name,
                "description": request.description,
                "presets": [p.dict() for p in request.presets]
            },
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Create scene error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenes/{scene_id}/trigger", response_model=dict)
async def trigger_scene(
    scene_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Trigger a scene"""
    try:
        response = await adapter.request(
            "effects.scene.change",
            {"scene_id": scene_id},
            timeout=3.0
        )

        return success_response(response, message=f"Scene triggered")

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Trigger scene error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chains/{chain_id}/ab/compare", response_model=dict)
async def ab_compare(
    chain_id: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Toggle A/B comparison"""
    try:
        response = await adapter.request(
            "effects.ab.compare",
            {"chain_id": chain_id},
            timeout=2.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"A/B compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
