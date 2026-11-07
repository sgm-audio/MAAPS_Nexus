"""
System API Router
Endpoints for system health, metrics, and agent management
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from api.schemas.common import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


def get_system():
    from api.main import _ensure_system_ready

    return _ensure_system_ready()


@router.get("/health", response_model=dict)
async def get_system_health(system=Depends(get_system)):
    """Get overall system health"""
    try:
        health = system.get_health()
        return success_response(health)
    except Exception as e:
        logger.error(f"Get health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=dict)
async def get_system_metrics(system=Depends(get_system)):
    """Get system resource metrics"""
    try:
        resource_res = system.get_resource_metrics()
        metrics = dict(resource_res.get("metrics", {}))
        health = system.get_health()
        bus_metrics = health.get("message_bus_metrics", {})
        uptime = max(health.get("system_uptime_seconds", 1.0), 1.0)
        queue_depth = (
            bus_metrics.get("queue_depth_high", 0)
            + bus_metrics.get("queue_depth_medium", 0)
            + bus_metrics.get("queue_depth_low", 0)
        )
        msgs_per_sec = round(bus_metrics.get("messages_delivered", 0) / uptime, 2)
        metrics["message_bus"] = {
            "queue_depth": queue_depth,
            "messages_per_second": msgs_per_sec,
            **bus_metrics,
        }
        return success_response(metrics)
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/stats", response_model=dict)
async def get_agent_stats(agent_name: str, system=Depends(get_system)):
    """Get specific agent statistics"""
    try:
        status = system.get_agent_status(agent_name)
        if not status:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        return success_response(status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get agent stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=dict)
async def list_agents(system=Depends(get_system)):
    """List all agents and their status"""
    try:
        agents = system.get_all_agents()
        return success_response({"agents": agents, "total_agents": len(agents)})
    except Exception as e:
        logger.error(f"List agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
