"""
Multi-camera capture management

Handles simultaneous capture from multiple camera sources using threading
for real-time low-latency performance.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Union
import threading
import time
import numpy as np
from loguru import logger

try:
    import cv2
except ImportError:
    logger.warning("OpenCV not installed - camera capture will not work")
    cv2 = None


@dataclass
class CameraFrame:
    """
    Single camera frame with metadata

    Attributes:
        camera_id: Camera identifier
        frame: BGR image array (H, W, 3)
        timestamp: Capture timestamp
        frame_number: Sequential frame number
        is_valid: Whether frame is valid
    """

    camera_id: str
    frame: Optional[np.ndarray]
    timestamp: float
    frame_number: int
    is_valid: bool

    @property
    def shape(self) -> Optional[tuple]:
        """Get frame shape (height, width, channels)"""
        return self.frame.shape if self.frame is not None else None


class CameraCapture:
    """
    Single camera capture thread

    Runs in background thread continuously capturing frames.
    Provides thread-safe access to latest frame.
    """

    def __init__(self, camera_id: str, source: Union[str, int]):
        """
        Initialize camera capture

        Args:
            camera_id: Camera identifier
            source: Camera source (device index, RTSP URL, or video file path)
        """
        self.camera_id = camera_id
        self.source = source

        # OpenCV VideoCapture
        self.cap: Optional[cv2.VideoCapture] = None

        # Thread control
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._frame_lock = threading.Lock()

        # Latest frame storage
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_number = 0
        self._capture_timestamp = 0.0

        # Statistics
        self._total_frames = 0
        self._dropped_frames = 0
        self._start_time = 0.0

    def start(self) -> bool:
        """
        Start capture thread

        Returns:
            True if started successfully, False otherwise
        """
        if cv2 is None:
            logger.error(f"[{self.camera_id}] OpenCV not available")
            return False

        # Open camera
        try:
            # Try to parse as integer (device index)
            try:
                source_int = int(self.source)
                self.cap = cv2.VideoCapture(source_int)
            except ValueError:
                # String source (URL or file)
                self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                logger.error(f"[{self.camera_id}] Failed to open camera: {self.source}")
                return False

            # Configure capture
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency

            logger.info(f"[{self.camera_id}] Camera opened: {self.source}")

        except Exception as e:
            logger.error(f"[{self.camera_id}] Error opening camera: {e}")
            return False

        # Start capture thread
        self._running.set()
        self._start_time = time.time()
        self._thread = threading.Thread(
            target=self._capture_loop,
            name=f"CameraCapture-{self.camera_id}",
            daemon=True,
        )
        self._thread.start()

        logger.info(f"[{self.camera_id}] Capture thread started")
        return True

    def _capture_loop(self) -> None:
        """
        Main capture loop (runs in thread)
        """
        while self._running.is_set():
            try:
                ret, frame = self.cap.read()

                if ret:
                    # Successfully captured frame
                    with self._frame_lock:
                        self._latest_frame = frame
                        self._frame_number += 1
                        self._capture_timestamp = time.time()
                        self._total_frames += 1

                else:
                    # Failed to read frame
                    self._dropped_frames += 1
                    logger.debug(f"[{self.camera_id}] Dropped frame")

                    # Try to reconnect if too many drops
                    if self._dropped_frames > 30:
                        logger.warning(
                            f"[{self.camera_id}] Too many dropped frames, attempting reconnect"
                        )
                        self._reconnect()

            except Exception as e:
                logger.error(f"[{self.camera_id}] Capture error: {e}")
                time.sleep(0.1)  # Avoid tight loop on persistent error

        # Cleanup
        if self.cap is not None:
            self.cap.release()
            logger.info(f"[{self.camera_id}] Camera released")

    def _reconnect(self) -> None:
        """
        Attempt to reconnect to camera
        """
        try:
            if self.cap is not None:
                self.cap.release()

            time.sleep(1.0)  # Wait before reconnecting

            # Reopen
            try:
                source_int = int(self.source)
                self.cap = cv2.VideoCapture(source_int)
            except ValueError:
                self.cap = cv2.VideoCapture(self.source)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self._dropped_frames = 0
                logger.info(f"[{self.camera_id}] Reconnected successfully")
            else:
                logger.error(f"[{self.camera_id}] Reconnection failed")

        except Exception as e:
            logger.error(f"[{self.camera_id}] Reconnection error: {e}")

    def get_latest_frame(self) -> Optional[CameraFrame]:
        """
        Get latest frame (thread-safe)

        Returns:
            CameraFrame if available, None otherwise
        """
        with self._frame_lock:
            if self._latest_frame is None:
                return None

            return CameraFrame(
                camera_id=self.camera_id,
                frame=self._latest_frame.copy(),  # Copy to avoid race conditions
                timestamp=self._capture_timestamp,
                frame_number=self._frame_number,
                is_valid=True,
            )

    def stop(self) -> None:
        """
        Stop capture thread
        """
        logger.info(f"[{self.camera_id}] Stopping capture...")
        self._running.clear()

        if self._thread is not None:
            self._thread.join(timeout=2.0)

        logger.info(f"[{self.camera_id}] Capture stopped")

    def get_stats(self) -> Dict:
        """
        Get capture statistics

        Returns:
            Dictionary of statistics
        """
        elapsed = time.time() - self._start_time if self._start_time > 0 else 0.0
        fps = self._total_frames / elapsed if elapsed > 0 else 0.0

        return {
            "camera_id": self.camera_id,
            "source": self.source,
            "total_frames": self._total_frames,
            "dropped_frames": self._dropped_frames,
            "fps": fps,
            "running": self._running.is_set(),
        }


class CameraManager:
    """
    Manages multiple camera captures

    Coordinates multiple CameraCapture instances for synchronized
    multi-camera operation.
    """

    def __init__(self, sources: Dict[str, Union[str, int]]):
        """
        Initialize camera manager

        Args:
            sources: Dictionary mapping camera_id to source
                    (e.g., {"camera_0": 0, "camera_1": "rtsp://..."})
        """
        self.sources = sources
        self.captures: Dict[str, CameraCapture] = {}

        # Create captures
        for camera_id, source in sources.items():
            self.captures[camera_id] = CameraCapture(camera_id, source)

    @classmethod
    def from_list(cls, sources: list) -> "CameraManager":
        """
        Create camera manager from list of sources

        Args:
            sources: List of sources (assigned camera_0, camera_1, etc.)

        Returns:
            CameraManager instance
        """
        sources_dict = {f"camera_{i}": source for i, source in enumerate(sources)}
        return cls(sources_dict)

    def start_all(self) -> Dict[str, bool]:
        """
        Start all camera captures

        Returns:
            Dictionary mapping camera_id to success status
        """
        logger.info(f"Starting {len(self.captures)} cameras...")

        results = {}
        for camera_id, capture in self.captures.items():
            success = capture.start()
            results[camera_id] = success

            if not success:
                logger.error(f"Failed to start camera: {camera_id}")

        # Wait for first frames
        time.sleep(0.5)

        successful = sum(1 for s in results.values() if s)
        logger.info(f"Started {successful}/{len(self.captures)} cameras successfully")

        return results

    def get_all_frames(self) -> Dict[str, CameraFrame]:
        """
        Get latest frame from each camera (synchronized)

        Returns:
            Dictionary mapping camera_id to CameraFrame
        """
        frames = {}

        for camera_id, capture in self.captures.items():
            frame = capture.get_latest_frame()
            if frame is not None:
                frames[camera_id] = frame

        return frames

    def get_frame(self, camera_id: str) -> Optional[CameraFrame]:
        """
        Get latest frame from specific camera

        Args:
            camera_id: Camera identifier

        Returns:
            CameraFrame if available, None otherwise
        """
        capture = self.captures.get(camera_id)
        if capture is None:
            return None

        return capture.get_latest_frame()

    def get_camera_count(self) -> int:
        """
        Get number of cameras

        Returns:
            Number of managed cameras
        """
        return len(self.captures)

    def get_active_count(self) -> int:
        """
        Get number of active cameras

        Returns:
            Number of cameras currently capturing
        """
        count = 0
        for capture in self.captures.values():
            stats = capture.get_stats()
            if stats["running"] and stats["total_frames"] > 0:
                count += 1
        return count

    def stop_all(self) -> None:
        """
        Stop all camera captures
        """
        logger.info("Stopping all cameras...")

        for camera_id, capture in self.captures.items():
            capture.stop()

        logger.info("All cameras stopped")

    def get_all_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all cameras

        Returns:
            Dictionary mapping camera_id to stats dictionary
        """
        return {
            camera_id: capture.get_stats()
            for camera_id, capture in self.captures.items()
        }

    def __enter__(self):
        """Context manager entry"""
        self.start_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_all()
