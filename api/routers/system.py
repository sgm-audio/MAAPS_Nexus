"""
System API Router
Endpoints for system health, metrics, and agent management
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from api.message_bus_adapter import get_message_bus_adapter, MessageBusAdapter
from api.schemas.common import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=dict)
async def get_system_health(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Get overall system health"""
    try:
        response = await adapter.request(
            "system.health.get",
            {},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Get health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=dict)
async def get_system_metrics(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Get system resource metrics"""
    try:
        response = await adapter.request(
            "system.metrics.get",
            {},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/stats", response_model=dict)
async def get_agent_stats(
    agent_name: str,
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """Get specific agent statistics"""
    try:
        response = await adapter.request(
            "system.agent.stats",
            {"agent_name": agent_name},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"Get agent stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=dict)
async def list_agents(
    adapter: MessageBusAdapter = Depends(get_message_bus_adapter)
):
    """List all agents and their status"""
    try:
        response = await adapter.request(
            "system.agents.list",
            {},
            timeout=3.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        logger.error(f"List agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
