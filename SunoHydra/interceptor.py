import json
from playwright.async_api import Response
from typing import List, Callable, Awaitable
from parser import SunoTrack, CleanedTrack

class SunoInterceptor:
    def __init__(self):
        self.captured_tracks: List[CleanedTrack] = []
        # Target endpoints that contain feed data
        self.target_patterns = [
            "/api/feed",
            "/api/trending",
            "studio-api.suno.ai/api/feed"
        ]

    async def handle_response(self, response: Response):
        """
        Callback for Playwright's 'response' event.
        Checks if the response is a relevant API call and extracts data.
        """
        url = response.url
        
        # Check if URL matches any target pattern
        if not any(pattern in url for pattern in self.target_patterns):
            return

        # Ensure we only process successful JSON responses
        if response.status != 200:
            return
            
        try:
            # Some responses might not be JSON, play safe
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return

            data = await response.json()
            self._process_data(data)
            
        except Exception as e:
            print(f"Error intercepting {url}: {e}")

    def _process_data(self, data: dict):
        """
        Extracts tracks from the raw JSON response.
        Handles different response structures (list vs dict with keys).
        """
        raw_list = []
        
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            # Try to find the list of items
            if "result" in data and isinstance(data["result"], list):
                raw_list = data["result"]
            elif "items" in data and isinstance(data["items"], list):
                raw_list = data["items"]
            elif "clips" in data and isinstance(data["clips"], list): # Suno often uses 'clips'
                 raw_list = data["clips"]

        for item in raw_list:
            try:
                # Convert to Pydantic model for validation
                track = SunoTrack(**item)
                
                # Extract tags properly. Suno puts them in metadata mostly.
                extracted_tags = []
                if track.tags:
                    # Sometimes tags is a string "tag1, tag2"
                    extracted_tags = [t.strip() for t in track.tags.split(",") if t.strip()]
                elif track.metadata and "tags" in track.metadata:
                     metadata_tags = track.metadata["tags"]
                     if isinstance(metadata_tags, str):
                         extracted_tags = [t.strip() for t in metadata_tags.split(",") if t.strip()]
                     elif isinstance(metadata_tags, list):
                         extracted_tags = metadata_tags

                # Create cleaned object
                cleaned = CleanedTrack(
                    track_id=track.id,
                    title=track.title or "Untitled",
                    play_count=track.play_count,
                    upvote_count=track.upvote_count,
                    raw_tags=extracted_tags,
                    model_version=track.major_model_version or "unknown"
                )

                if cleaned.is_high_status:
                    self.captured_tracks.append(cleaned)
                    print(f"Captured High-Status Track: {cleaned.title} ({cleaned.play_count} plays)")
                
            except Exception as e:
                # Silently fail on individual malformed items to keep the stream going
                continue

    def get_and_clear_buffer(self) -> List[dict]:
        """
        Returns the captured tracks as dicts and clears the buffer.
        """
        buffer = [t.model_dump() for t in self.captured_tracks]
        self.captured_tracks = []
        return buffer
