"""
Metadata API Router
Endpoints for metadata extraction and management
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from api.message_bus_adapter import get_message_bus_adapter, MessageBusAdapter
from api.schemas.common import success_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Note: Using the existing endpoints from main.py
# This router can be expanded with additional metadata capabilities
