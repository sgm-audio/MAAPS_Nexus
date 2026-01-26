# api/routers/telemetry.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import psutil

router = APIRouter()

@router.websocket("/ws/monitor")
async def monitor_agents(websocket: WebSocket, system_bus):
    await websocket.accept()
    try:
        while True:
            # Aggregate system state
            metrics = {
                "cpu_load": psutil.cpu_percent(),
                "agents": [
                    {
                        "id": agent.id,
                        "status": agent.circuit_breaker.state.value,
                        "queue_depth": agent.inbox.qsize(),
                        "latency_ms": agent.last_execution_time
                    } for agent in system_bus.get_registered_agents()
                ]
            }
            await websocket.send_json(metrics)
            await asyncio.sleep(1/60) # 60Hz refresh rate
    except WebSocketDisconnect:
        pass