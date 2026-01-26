import httpx
import os
import json
from typing import List, Dict, Any

class WebhookPusher:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("N8N_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("N8N_WEBHOOK_URL environment variable is not set")
        
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "SunoHydra/1.0"
        }

    async def push_batch(self, payload: List[Dict[str, Any]]) -> bool:
        """
        Push a batch of cleaned tracks to the n8n webhook.
        """
        if not payload:
            return True
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                print(f"Successfully pushed {len(payload)} tracks to n8n.")
                return True
            except httpx.HTTPError as e:
                print(f"Failed to push data to n8n: {e}")
                return False
