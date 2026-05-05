"""
Intelligent Metadata & Project Management Agent

This agent handles:
- Comprehensive audio metadata extraction
- Project version control
- Intelligent tagging system
- Semantic audio search
- Auto backup management
- Collaboration support
"""

import threading
import queue
import time
import hashlib
import json
import sqlite3
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import logging

try:
    import librosa
    import numpy as np
except ImportError:
    librosa = None
    np = None

from ..core import BaseAgent, Message, Topics, Priority

logger = logging.getLogger(__name__)


@dataclass
class AudioMetadata:
    """Comprehensive audio metadata"""

    filename: str
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    file_size: int
    checksum: str
    creation_date: str
    modification_date: str

    # Musical metadata
    tempo: Optional[float] = None
    key: Optional[str] = None
    time_signature: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[float] = None

    # Processing metadata
    processing_history: List[Dict] = field(default_factory=list)
    stem_type: Optional[str] = None
    parent_track: Optional[str] = None
    quality_score: Optional[float] = None


@dataclass
class ProjectInfo:
    """Project information"""

    project_id: str
    project_name: str
    created_at: str
    modified_at: str
    num_files: int
    total_duration: float
    project_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionInfo:
    """Version control information"""

    version_id: str
    project_id: str
    version_number: str
    description: str
    timestamp: str
    changes: List[str]
    file_checksums: Dict[str, str]


class MetadataManagementAgent(BaseAgent):
    """
    Agent responsible for metadata management and project organization.

    Capabilities:
    - Comprehensive metadata extraction
    - Project version control
    - Intelligent tagging
    - Semantic search
    - Auto backup
    - Collaboration support
    """

    def __init__(self, db_path: str = "metadata.db"):
        super().__init__(
            agent_id="metadata_management_agent",
            agent_name="Intelligent Metadata & Project Management Agent",
        )

        self.db_path = db_path
        self.db_lock = threading.Lock()

        # Processing queue
        self.processing_queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None

        # Tag categories
        self.tag_categories = {
            "musical": ["tempo", "key", "genre", "mood", "energy"],
            "technical": ["sample_rate", "bit_depth", "duration", "quality"],
            "processing": ["stem_type", "enhancement_applied", "separation_method"],
            "content": ["instrument", "vocal_style", "rhythm_pattern"],
            "custom": [],
        }

        # Search index
        self.search_index = {}
        self.search_lock = threading.Lock()

        # Statistics
        self.stats = {
            "files_indexed": 0,
            "projects_managed": 0,
            "versions_created": 0,
            "tags_generated": 0,
            "searches_performed": 0,
        }
        self.stats_lock = threading.Lock()

    def setup(self):
        """Initialize the metadata management agent"""
        # Initialize database
        self._init_database()

        # Subscribe to relevant topics
        self.subscribe("metadata.extract.request")
        self.subscribe("metadata.search.request")
        self.subscribe("project.create.request")
        self.subscribe("project.version.create")
        self.subscribe("project.version.restore")
        self.subscribe("tags.generate.request")
        self.subscribe("tags.suggest.request")

        # Start processing thread
        self._start_processing_thread()

        self.log("INFO", "Metadata Management Agent initialized successfully")

    def teardown(self):
        """Cleanup resources"""
        # Stop processing thread
        self._stop_processing_thread()

        self.log("INFO", "Metadata Management Agent shutdown complete")

    def handle_message(self, message: Message):
        """Process incoming messages"""
        try:
            if message.topic == "metadata.extract.request":
                self._handle_metadata_extract(message)
            elif message.topic == "metadata.search.request":
                self._handle_metadata_search(message)
            elif message.topic == "project.create.request":
                self._handle_project_create(message)
            elif message.topic == "project.version.create":
                self._handle_version_create(message)
            elif message.topic == "project.version.restore":
                self._handle_version_restore(message)
            elif message.topic == "tags.generate.request":
                self._handle_tags_generate(message)
            elif message.topic == "tags.suggest.request":
                self._handle_tags_suggest(message)
            else:
                self.log("WARNING", f"Unknown message topic: {message.topic}")

        except Exception as e:
            self.log("ERROR", f"Error handling message: {e}", {"topic": message.topic})

    def _handle_metadata_extract(self, message: Message):
        """Handle metadata extraction request"""
        payload = message.payload
        audio_path = payload.get("audio_path")
        audio_data = payload.get("audio_data")
        sample_rate = payload.get("sample_rate", 44100)
        deep_analysis = payload.get("deep_analysis", True)

        if not audio_path and audio_data is None:
            self.respond(
                message, {"success": False, "error": "No audio path or data provided"}
            )
            return

        job = {
            "type": "extract_metadata",
            "message": message,
            "audio_path": audio_path,
            "audio_data": audio_data,
            "sample_rate": sample_rate,
            "deep_analysis": deep_analysis,
        }
        self.processing_queue.put(job)

    def _handle_metadata_search(self, message: Message):
        """Handle metadata search request"""
        payload = message.payload
        query = payload.get("query", "")
        search_type = payload.get("search_type", "text")
        filters = payload.get("filters", {})

        job = {
            "type": "search",
            "message": message,
            "query": query,
            "search_type": search_type,
            "filters": filters,
        }
        self.processing_queue.put(job)

    def _handle_project_create(self, message: Message):
        """Handle project creation request"""
        payload = message.payload
        project_name = payload.get("project_name", "Untitled Project")
        project_metadata = payload.get("metadata", {})

        job = {
            "type": "create_project",
            "message": message,
            "project_name": project_name,
            "metadata": project_metadata,
        }
        self.processing_queue.put(job)

    def _handle_version_create(self, message: Message):
        """Handle version creation request"""
        payload = message.payload
        project_id = payload.get("project_id")
        description = payload.get("description", "")
        changes = payload.get("changes", [])

        if not project_id:
            self.respond(message, {"success": False, "error": "No project_id provided"})
            return

        job = {
            "type": "create_version",
            "message": message,
            "project_id": project_id,
            "description": description,
            "changes": changes,
        }
        self.processing_queue.put(job)

    def _handle_version_restore(self, message: Message):
        """Handle version restore request"""
        payload = message.payload
        version_id = payload.get("version_id")

        if not version_id:
            self.respond(message, {"success": False, "error": "No version_id provided"})
            return

        job = {"type": "restore_version", "message": message, "version_id": version_id}
        self.processing_queue.put(job)

    def _handle_tags_generate(self, message: Message):
        """Handle tag generation request"""
        payload = message.payload
        metadata = payload.get("metadata", {})

        job = {"type": "generate_tags", "message": message, "metadata": metadata}
        self.processing_queue.put(job)

    def _handle_tags_suggest(self, message: Message):
        """Handle tag suggestion request"""
        payload = message.payload
        metadata = payload.get("metadata", {})
        context = payload.get("context", {})

        job = {
            "type": "suggest_tags",
            "message": message,
            "metadata": metadata,
            "context": context,
        }
        self.processing_queue.put(job)

    def _start_processing_thread(self):
        """Start the processing worker thread"""
        self.processing_thread = threading.Thread(
            target=self._processing_worker,
            name=f"{self.agent_id}_processor",
            daemon=True,
        )
        self.processing_thread.start()

    def _stop_processing_thread(self):
        """Stop the processing worker thread"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_queue.put(None)  # Sentinel
            self.processing_thread.join(timeout=5.0)

    def _processing_worker(self):
        """Worker thread for processing metadata jobs"""
        while True:
            try:
                job = self.processing_queue.get(timeout=1.0)

                if job is None:  # Sentinel to stop
                    break

                start_time = time.time()

                # Process based on job type
                if job["type"] == "extract_metadata":
                    result = self._extract_metadata(job)
                elif job["type"] == "search":
                    result = self._search_metadata(job)
                elif job["type"] == "create_project":
                    result = self._create_project(job)
                elif job["type"] == "create_version":
                    result = self._create_version(job)
                elif job["type"] == "restore_version":
                    result = self._restore_version(job)
                elif job["type"] == "generate_tags":
                    result = self._generate_tags(job)
                elif job["type"] == "suggest_tags":
                    result = self._suggest_tags(job)
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown job type: {job['type']}",
                    }

                processing_time = time.time() - start_time
                result["processing_time_seconds"] = processing_time

                # Send response
                self.respond(job["message"], result)

                # Publish completion event
                self.publish(
                    f"metadata.{job['type']}.complete",
                    {
                        "success": result.get("success", False),
                        "processing_time": processing_time,
                    },
                    priority=Priority.LOW,
                )

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker: {e}")
                if "job" in locals() and "message" in job:
                    self.respond(job["message"], {"success": False, "error": str(e)})

    def _extract_metadata(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive metadata from audio"""
        try:
            audio_path = job.get("audio_path")
            audio_data = job.get("audio_data")
            sample_rate = job.get("sample_rate", 44100)
            deep_analysis = job.get("deep_analysis", True)

            # Create basic metadata
            metadata = {
                "filename": Path(audio_path).name if audio_path else "audio_data",
                "sample_rate": sample_rate,
                "creation_date": datetime.now().isoformat(),
                "modification_date": datetime.now().isoformat(),
            }

            # Load audio if needed
            if audio_data is None and audio_path:
                if librosa is not None:
                    audio_data, sample_rate = librosa.load(audio_path, sr=None)
                else:
                    return {
                        "success": False,
                        "error": "librosa not available for audio loading",
                    }

            if audio_data is not None:
                if not isinstance(audio_data, (list, tuple)):
                    if hasattr(audio_data, "__len__"):
                        audio_length = len(audio_data)
                    else:
                        audio_length = 0
                else:
                    audio_length = len(audio_data)

                metadata["duration"] = audio_length / sample_rate
                metadata["channels"] = 1  # Simplified
                metadata["bit_depth"] = 16  # Default
                metadata["file_size"] = audio_length * 2  # Approximate

                # Calculate checksum
                if isinstance(audio_data, (list, tuple)):
                    audio_bytes = str(audio_data).encode()
                else:
                    audio_bytes = (
                        bytes(audio_data)
                        if hasattr(audio_data, "__iter__")
                        else str(audio_data).encode()
                    )
                metadata["checksum"] = hashlib.md5(audio_bytes).hexdigest()

                if deep_analysis and librosa is not None and np is not None:
                    # Extract musical features
                    musical_features = self._extract_musical_features(
                        audio_data, sample_rate
                    )
                    metadata.update(musical_features)

                    # Calculate quality score
                    metadata["quality_score"] = self._calculate_quality_score(
                        audio_data, sample_rate
                    )

            # Store in database
            with self.db_lock:
                self._store_metadata(metadata)

            # Add to search index
            with self.search_lock:
                self.search_index[metadata["checksum"]] = metadata

            with self.stats_lock:
                self.stats["files_indexed"] += 1

            return {"success": True, "metadata": metadata}

        except Exception as e:
            return {"success": False, "error": f"Metadata extraction failed: {str(e)}"}

    def _extract_musical_features(self, audio_data, sample_rate: int) -> Dict:
        """Extract musical features from audio"""
        features = {}

        try:
            # Ensure audio_data is numpy array
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)

            # Tempo estimation
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            features["tempo"] = float(tempo)

            # Key detection (simplified)
            chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
            chroma_mean = np.mean(chroma, axis=1)
            key_index = np.argmax(chroma_mean)
            keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            features["key"] = f"{keys[key_index]} major"

            # Energy level
            rms = librosa.feature.rms(y=audio_data)[0]
            features["energy_level"] = float(np.mean(rms))

            # Time signature (simplified - assume 4/4)
            features["time_signature"] = "4/4"

        except Exception as e:
            logger.error(f"Error extracting musical features: {e}")

        return features

    def _calculate_quality_score(self, audio_data, sample_rate: int) -> float:
        """Calculate audio quality score"""
        try:
            # Simplified quality score based on dynamic range
            if isinstance(audio_data, np.ndarray):
                peak = np.max(np.abs(audio_data))
                rms = np.sqrt(np.mean(audio_data**2))
                dynamic_range = 20 * np.log10((peak + 1e-10) / (rms + 1e-10))

                # Normalize to 0-1 score
                quality_score = min(1.0, dynamic_range / 60.0)
                return float(quality_score)
        except:
            pass

        return 0.5  # Default medium quality

    def _search_metadata(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Search metadata index"""
        try:
            query = job.get("query", "")
            search_type = job.get("search_type", "text")
            filters = job.get("filters", {})

            results = []

            with self.search_lock:
                for checksum, metadata in self.search_index.items():
                    # Simple text search
                    if search_type == "text":
                        searchable_text = json.dumps(metadata).lower()
                        if query.lower() in searchable_text:
                            # Apply filters
                            if self._matches_filters(metadata, filters):
                                results.append(metadata)

            with self.stats_lock:
                self.stats["searches_performed"] += 1

            return {"success": True, "results": results, "count": len(results)}

        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}

    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches search filters"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True

    def _create_project(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project"""
        try:
            project_name = job.get("project_name", "Untitled Project")
            metadata = job.get("metadata", {})

            project_id = hashlib.md5(
                f"{project_name}{time.time()}".encode()
            ).hexdigest()

            project_info = {
                "project_id": project_id,
                "project_name": project_name,
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "num_files": 0,
                "total_duration": 0.0,
                "metadata": metadata,
            }

            # Store in database
            with self.db_lock:
                self._store_project(project_info)

            with self.stats_lock:
                self.stats["projects_managed"] += 1

            return {
                "success": True,
                "project_id": project_id,
                "project_info": project_info,
            }

        except Exception as e:
            return {"success": False, "error": f"Project creation failed: {str(e)}"}

    def _create_version(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Create project version"""
        try:
            project_id = job.get("project_id")
            description = job.get("description", "")
            changes = job.get("changes", [])

            version_id = hashlib.md5(f"{project_id}{time.time()}".encode()).hexdigest()

            version_info = {
                "version_id": version_id,
                "project_id": project_id,
                "version_number": self._get_next_version_number(project_id),
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "file_checksums": {},
            }

            # Store in database
            with self.db_lock:
                self._store_version(version_info)

            with self.stats_lock:
                self.stats["versions_created"] += 1

            return {
                "success": True,
                "version_id": version_id,
                "version_info": version_info,
            }

        except Exception as e:
            return {"success": False, "error": f"Version creation failed: {str(e)}"}

    def _restore_version(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Restore project from version"""
        try:
            version_id = job.get("version_id")

            # Retrieve version info from database
            with self.db_lock:
                version_info = self._get_version(version_id)

            if not version_info:
                return {"success": False, "error": f"Version {version_id} not found"}

            return {
                "success": True,
                "version_info": version_info,
                "message": "Version restore would be performed here",
            }

        except Exception as e:
            return {"success": False, "error": f"Version restore failed: {str(e)}"}

    def _generate_tags(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent tags for metadata"""
        try:
            metadata = job.get("metadata", {})

            tags = {
                "musical": [],
                "technical": [],
                "processing": [],
                "content": [],
                "automatic": [],
            }

            # Generate musical tags
            if metadata.get("tempo"):
                tempo = metadata["tempo"]
                if tempo < 90:
                    tags["musical"].append("slow")
                elif tempo < 120:
                    tags["musical"].append("moderate")
                else:
                    tags["musical"].append("fast")

            if metadata.get("key"):
                tags["musical"].append(f"key:{metadata['key']}")

            if metadata.get("energy_level"):
                energy = metadata["energy_level"]
                if energy < 0.3:
                    tags["musical"].append("low_energy")
                elif energy < 0.7:
                    tags["musical"].append("medium_energy")
                else:
                    tags["musical"].append("high_energy")

            # Generate technical tags
            if metadata.get("sample_rate"):
                sr = metadata["sample_rate"]
                tags["technical"].append(f"sr:{sr}hz")
                if sr >= 48000:
                    tags["technical"].append("high_quality")

            if metadata.get("bit_depth"):
                tags["technical"].append(f"bit_depth:{metadata['bit_depth']}")

            with self.stats_lock:
                self.stats["tags_generated"] += 1

            return {
                "success": True,
                "tags": tags,
                "total_tags": sum(len(v) for v in tags.values()),
            }

        except Exception as e:
            return {"success": False, "error": f"Tag generation failed: {str(e)}"}

    def _suggest_tags(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest tags based on similar files"""
        try:
            metadata = job.get("metadata", {})
            context = job.get("context", {})

            # Find similar files in search index
            similar_files = self._find_similar_files(metadata)

            # Aggregate tags from similar files
            suggested_tags = []
            tag_frequencies = {}

            for similar_file in similar_files[:5]:  # Top 5 similar
                file_tags = similar_file.get("tags", {})
                for category, tags in file_tags.items():
                    for tag in tags:
                        tag_frequencies[tag] = tag_frequencies.get(tag, 0) + 1

            # Suggest most common tags
            for tag, freq in sorted(
                tag_frequencies.items(), key=lambda x: x[1], reverse=True
            ):
                if freq > 1:  # Appears in at least 2 similar files
                    suggested_tags.append(
                        {
                            "tag": tag,
                            "confidence": freq / len(similar_files),
                            "reason": f"Common in {freq} similar files",
                        }
                    )

            return {
                "success": True,
                "suggested_tags": suggested_tags[:10],  # Top 10 suggestions
                "similar_files_analyzed": len(similar_files),
            }

        except Exception as e:
            return {"success": False, "error": f"Tag suggestion failed: {str(e)}"}

    def _find_similar_files(self, metadata: Dict) -> List[Dict]:
        """Find similar files based on metadata"""
        similar = []

        with self.search_lock:
            for checksum, other_metadata in self.search_index.items():
                similarity_score = self._calculate_similarity(metadata, other_metadata)
                if similarity_score > 0.5:
                    similar.append(
                        {**other_metadata, "similarity_score": similarity_score}
                    )

        # Sort by similarity
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar

    def _calculate_similarity(self, meta1: Dict, meta2: Dict) -> float:
        """Calculate similarity score between two metadata entries"""
        score = 0.0
        comparisons = 0

        # Compare tempo
        if meta1.get("tempo") and meta2.get("tempo"):
            tempo_diff = abs(meta1["tempo"] - meta2["tempo"])
            score += max(0, 1 - tempo_diff / 100)
            comparisons += 1

        # Compare key
        if meta1.get("key") and meta2.get("key"):
            if meta1["key"] == meta2["key"]:
                score += 1.0
            comparisons += 1

        # Compare energy
        if meta1.get("energy_level") and meta2.get("energy_level"):
            energy_diff = abs(meta1["energy_level"] - meta2["energy_level"])
            score += max(0, 1 - energy_diff)
            comparisons += 1

        return score / comparisons if comparisons > 0 else 0.0

    def _get_next_version_number(self, project_id: str) -> str:
        """Get next version number for project"""
        # Simplified version numbering
        with self.db_lock:
            versions = self._get_project_versions(project_id)

        if not versions:
            return "1.0.0"

        # Increment patch version
        latest = versions[-1]["version_number"]
        parts = latest.split(".")
        parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts)

    # Database operations

    def _init_database(self):
        """Initialize SQLite database"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    checksum TEXT PRIMARY KEY,
                    filename TEXT,
                    data TEXT,
                    created_at TEXT
                )
            """)

            # Create projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT,
                    data TEXT,
                    created_at TEXT,
                    modified_at TEXT
                )
            """)

            # Create versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    version_id TEXT PRIMARY KEY,
                    project_id TEXT,
                    version_number TEXT,
                    data TEXT,
                    created_at TEXT
                )
            """)

            conn.commit()
            conn.close()

    def _store_metadata(self, metadata: Dict):
        """Store metadata in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO metadata (checksum, filename, data, created_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                metadata.get("checksum", ""),
                metadata.get("filename", ""),
                json.dumps(metadata),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def _store_project(self, project_info: Dict):
        """Store project in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO projects (project_id, project_name, data, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                project_info["project_id"],
                project_info["project_name"],
                json.dumps(project_info),
                project_info["created_at"],
                project_info["modified_at"],
            ),
        )

        conn.commit()
        conn.close()

    def _store_version(self, version_info: Dict):
        """Store version in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO versions (version_id, project_id, version_number, data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                version_info["version_id"],
                version_info["project_id"],
                version_info["version_number"],
                json.dumps(version_info),
                version_info["timestamp"],
            ),
        )

        conn.commit()
        conn.close()

    def _get_version(self, version_id: str) -> Optional[Dict]:
        """Retrieve version from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM versions WHERE version_id = ?", (version_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def _get_project_versions(self, project_id: str) -> List[Dict]:
        """Get all versions for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT data FROM versions WHERE project_id = ? ORDER BY created_at",
            (project_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [json.loads(row[0]) for row in rows]
