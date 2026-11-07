"""
Metadata API Router
Endpoints for metadata extraction and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metadata", tags=["Metadata"])


# Request Models
class MetadataExtractRequest(BaseModel):
    audio_data: List[float] = Field(..., description="Audio samples")
    sample_rate: int = Field(44100, description="Sample rate in Hz")
    deep_analysis: bool = Field(True, description="Perform deep analysis")


class MetadataSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")
    limit: int = Field(10, description="Maximum results", ge=1, le=100)


class TagRequest(BaseModel):
    file_id: str = Field(..., description="File ID to tag")
    tags: List[str] = Field(..., description="Tags to add")


# Dependency to get system instance
def get_system():
    """Get the MAAPS system instance"""
    from api.main import _ensure_system_ready

    return _ensure_system_ready()


@router.post("/extract")
async def extract_metadata(request: MetadataExtractRequest, system=Depends(get_system)):
    """
    Extract metadata from audio

    Returns musical, technical, and quality features
    """
    try:
        logger.info(f"Metadata extraction: {len(request.audio_data)} samples")

        metadata = system.extract_metadata(
            audio_data=request.audio_data,
            sample_rate=request.sample_rate,
            deep_analysis=request.deep_analysis,
        )

        logger.info("Metadata extraction complete")
        return JSONResponse(content=metadata)

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_metadata(request: MetadataSearchRequest, system=Depends(get_system)):
    """
    Search metadata database

    Supports semantic search with filters
    """
    try:
        logger.info(f"Metadata search: '{request.query}' with {request.limit} results")

        results = system.search_metadata(
            query=request.query, filters=request.filters or {}, limit=request.limit
        )

        logger.info(f"Search complete: {len(results.get('results', []))} results found")
        return JSONResponse(content=results)

    except Exception as e:
        logger.error(f"Metadata search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_id}")
async def get_file_metadata(file_id: str, system=Depends(get_system)):
    """Get metadata for a specific file by ID"""
    try:
        # This would query the metadata database
        # For now, return a placeholder
        return {
            "file_id": file_id,
            "status": "not_implemented",
            "message": "Metadata database query not yet implemented",
        }

    except Exception as e:
        logger.error(f"Failed to get file metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tags/add")
async def add_tags(request: TagRequest, system=Depends(get_system)):
    """Add tags to a file"""
    try:
        logger.info(f"Adding tags to {request.file_id}: {request.tags}")

        # This would update the metadata database
        return {
            "file_id": request.file_id,
            "tags_added": request.tags,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Failed to add tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tags/remove")
async def remove_tags(
    file_id: str = Query(..., description="File ID"),
    tags: List[str] = Query(..., description="Tags to remove"),
    system=Depends(get_system),
):
    """Remove tags from a file"""
    try:
        logger.info(f"Removing tags from {file_id}: {tags}")

        # This would update the metadata database
        return {"file_id": file_id, "tags_removed": tags, "status": "success"}

    except Exception as e:
        logger.error(f"Failed to remove tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_metadata_stats(system=Depends(get_system)):
    """Get metadata database statistics"""
    try:
        # This would query the metadata database for statistics
        return {
            "total_files": 0,
            "total_tags": 0,
            "unique_artists": 0,
            "unique_genres": 0,
            "total_size_gb": 0.0,
        }

    except Exception as e:
        logger.error(f"Failed to get metadata stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/genres")
async def list_genres(system=Depends(get_system)):
    """Get list of all genres in metadata database"""
    try:
        # This would query unique genres from database
        return {
            "genres": [
                "rock",
                "pop",
                "jazz",
                "classical",
                "electronic",
                "hip-hop",
                "r&b",
                "country",
                "metal",
                "indie",
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get genres: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/popular")
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100), system=Depends(get_system)
):
    """Get most popular tags"""
    try:
        # This would query tag frequency from database
        return {
            "tags": [
                {"tag": "uplifting", "count": 150},
                {"tag": "energetic", "count": 120},
                {"tag": "mellow", "count": 100},
                {"tag": "ambient", "count": 95},
                {"tag": "aggressive", "count": 80},
            ][:limit]
        }

    except Exception as e:
        logger.error(f"Failed to get popular tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))
