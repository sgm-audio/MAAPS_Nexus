from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SunoTrack(BaseModel):
    id: str = Field(..., alias="id")
    title: Optional[str] = ""
    handle: Optional[str] = None # User handle
    display_name: Optional[str] = None # User display name
    major_model_version: Optional[str] = None
    model_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_video: bool = False
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    play_count: int = 0
    upvote_count: int = 0
    is_public: bool = True
    
    # These will be extracted from metadata or tags
    tags: Optional[str] = None 

    class Config:
        populate_by_name = True
        extra = "ignore" # Ignore extra fields from Suno API
        protected_namespaces = ()

class CleanedTrack(BaseModel):
    track_id: str
    title: str
    play_count: int
    upvote_count: int
    raw_tags: List[str]
    model_version: str
    
    @property
    def is_high_status(self) -> bool:
        return self.play_count > 1000
