"""
VST3 Wrapper for MAAPS - DAW Integration

This module provides the bridge between DAW (via VST3 plugin) and the Python
multi-agent system. Uses shared memory for <10ms latency audio processing.

Communication flow:
1. VST3 plugin writes audio buffer to shared memory
2. Python reads from shared memory
3. Agents process audio (fast, using Ray)
4. Python writes result to shared memory
5. VST3 plugin reads processed audio

Uses Unix sockets (Linux/Mac) or Named Pipes (Windows) for control signals.
"""

import numpy as np
import mmap
import struct
import threading
import queue
import time
import logging
from typing import Optional, Tuple, Dict
import os
import platform

logger = logging.getLogger(__name__)


class SharedMemoryAudioBuffer:
    """
    Shared memory buffer for audio exchange with VST3 plugin.
    Lock-free ring buffer for real-time audio.
    """

    def __init__(
        self,
        buffer_name: str,
        buffer_size: int = 8192,
        num_channels: int = 2,
        sample_rate: int = 44100,
    ):
        """
        Initialize shared memory buffer.

        Args:
            buffer_name: Name for shared memory
            buffer_size: Buffer size in samples (per channel)
            num_channels: Number of audio channels
            sample_rate: Sample rate
        """
        self.buffer_name = buffer_name
        self.buffer_size = buffer_size
        self.num_channels = num_channels
        self.sample_rate = sample_rate

        # Calculate memory size
        # Header: [read_pos(8), write_pos(8), processing_flag(4)]
        # Audio data: buffer_size * num_channels * sizeof(float)
        self.header_size = 20
        self.audio_data_size = buffer_size * num_channels * 4  # 4 bytes per float
        self.total_size = self.header_size + self.audio_data_size

        # Create or open shared memory
        self._initialize_shared_memory()

        logger.info(f"Initialized shared memory buffer: {buffer_name}")

    def _initialize_shared_memory(self):
        """Initialize platform-specific shared memory."""
        system = platform.system()

        if system == "Windows":
            self._initialize_windows()
        else:
            self._initialize_posix()

    def _initialize_windows(self):
        """Initialize Windows named shared memory."""
        try:
            # Try to open existing
            self.shm_handle = mmap.mmap(
                -1, self.total_size, tagname=self.buffer_name, access=mmap.ACCESS_WRITE
            )
            logger.info(f"Opened existing shared memory: {self.buffer_name}")
        except FileNotFoundError:
            # Create new
            self.shm_handle = mmap.mmap(
                -1, self.total_size, tagname=self.buffer_name, access=mmap.ACCESS_WRITE
            )
            # Initialize header to zeros
            self.shm_handle.seek(0)
            self.shm_handle.write(b"\x00" * self.header_size)
            logger.info(f"Created new shared memory: {self.buffer_name}")

    def _initialize_posix(self):
        """Initialize POSIX shared memory."""
        import posix_ipc

        try:
            # Try to create new
            self.shm = posix_ipc.SharedMemory(
                self.buffer_name, flags=posix_ipc.O_CREAT, size=self.total_size
            )
            # Map to memory
            self.shm_handle = mmap.mmap(
                self.shm.fd, self.total_size, access=mmap.ACCESS_WRITE
            )
            # Initialize header
            self.shm_handle.seek(0)
            self.shm_handle.write(b"\x00" * self.header_size)
            logger.info(f"Created new shared memory: {self.buffer_name}")
        except posix_ipc.ExistentialError:
            # Already exists, open it
            self.shm = posix_ipc.SharedMemory(self.buffer_name)
            self.shm_handle = mmap.mmap(
                self.shm.fd, self.total_size, access=mmap.ACCESS_WRITE
            )
            logger.info(f"Opened existing shared memory: {self.buffer_name}")

    def read_header(self) -> Tuple[int, int, int]:
        """
        Read header from shared memory.

        Returns:
            (read_pos, write_pos, processing_flag)
        """
        self.shm_handle.seek(0)
        data = self.shm_handle.read(self.header_size)
        read_pos, write_pos, processing_flag = struct.unpack("QQI", data)
        return read_pos, write_pos, processing_flag

    def write_header(self, read_pos: int, write_pos: int, processing_flag: int):
        """Write header to shared memory."""
        self.shm_handle.seek(0)
        data = struct.pack("QQI", read_pos, write_pos, processing_flag)
        self.shm_handle.write(data)

    def read_audio(self, num_samples: int) -> Optional[np.ndarray]:
        """
        Read audio from shared memory.

        Args:
            num_samples: Number of samples to read

        Returns:
            Audio array (num_samples, num_channels) or None if not enough data
        """
        read_pos, write_pos, _ = self.read_header()

        # Calculate available samples
        if write_pos >= read_pos:
            available = write_pos - read_pos
        else:
            available = self.buffer_size - read_pos + write_pos

        if available < num_samples:
            return None

        # Read audio data
        audio = np.zeros((num_samples, self.num_channels), dtype=np.float32)

        for i in range(num_samples):
            pos = (read_pos + i) % self.buffer_size
            offset = self.header_size + pos * self.num_channels * 4

            self.shm_handle.seek(offset)
            data = self.shm_handle.read(self.num_channels * 4)
            audio[i, :] = struct.unpack(f"{self.num_channels}f", data)

        # Update read position
        new_read_pos = (read_pos + num_samples) % self.buffer_size
        self.write_header(new_read_pos, write_pos, 0)

        return audio

    def write_audio(self, audio: np.ndarray):
        """
        Write audio to shared memory.

        Args:
            audio: Audio array (num_samples, num_channels)
        """
        num_samples = audio.shape[0]
        read_pos, write_pos, _ = self.read_header()

        # Write audio data
        for i in range(num_samples):
            pos = (write_pos + i) % self.buffer_size
            offset = self.header_size + pos * self.num_channels * 4

            self.shm_handle.seek(offset)
            data = struct.pack(f"{self.num_channels}f", *audio[i, :])
            self.shm_handle.write(data)

        # Update write position
        new_write_pos = (write_pos + num_samples) % self.buffer_size
        self.write_header(read_pos, new_write_pos, 0)

    def close(self):
        """Close shared memory."""
        if hasattr(self, "shm_handle"):
            self.shm_handle.close()
        logger.info(f"Closed shared memory: {self.buffer_name}")


class VST3Communicator:
    """
    Communicates with VST3 plugin via shared memory and control pipe.
    Runs in separate thread to meet real-time constraints.
    """

    def __init__(
        self,
        buffer_name: str = "maaps_nexus_buffer",
        control_pipe_name: str = "maaps_nexus_control",
        buffer_size: int = 2048,
        num_channels: int = 2,
        sample_rate: int = 44100,
    ):
        """
        Initialize VST3 communicator.

        Args:
            buffer_name: Shared memory buffer name
            control_pipe_name: Control pipe name
            buffer_size: Audio buffer size
            num_channels: Number of channels
            sample_rate: Sample rate
        """
        self.buffer_name = buffer_name
        self.control_pipe_name = control_pipe_name
        self.buffer_size = buffer_size
        self.num_channels = num_channels
        self.sample_rate = sample_rate

        # Initialize shared memory
        self.input_buffer = SharedMemoryAudioBuffer(
            f"{buffer_name}_input", buffer_size, num_channels, sample_rate
        )

        self.output_buffer = SharedMemoryAudioBuffer(
            f"{buffer_name}_output", buffer_size, num_channels, sample_rate
        )

        # Audio processing queue
        self.audio_queue = queue.Queue(maxsize=10)
        self.processed_queue = queue.Queue(maxsize=10)

        # Processing thread
        self.running = False
        self.processing_thread = None

        # Latency tracking
        self.latency_samples = 0
        self.latency_ms = 0.0

        logger.info("VST3 Communicator initialized")

    def start(self):
        """Start processing thread."""
        if self.running:
            logger.warning("Already running")
            return

        self.running = True
        self.processing_thread = threading.Thread(
            target=self._processing_loop, daemon=True
        )
        self.processing_thread.start()
        logger.info("Started processing thread")

    def stop(self):
        """Stop processing thread."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        logger.info("Stopped processing thread")

    def _processing_loop(self):
        """Main processing loop running in separate thread."""
        logger.info("Processing loop started")

        while self.running:
            try:
                # Read from input buffer
                audio = self.input_buffer.read_audio(self.buffer_size)

                if audio is not None:
                    # Track latency
                    start_time = time.perf_counter()

                    # Put in queue for agent processing
                    try:
                        self.audio_queue.put(audio, timeout=0.001)
                    except queue.Full:
                        logger.warning("Audio queue full, dropping frame")
                        continue

                    # Get processed audio
                    try:
                        processed = self.processed_queue.get(timeout=0.005)
                    except queue.Empty:
                        logger.warning("No processed audio available, using input")
                        processed = audio

                    # Write to output buffer
                    self.output_buffer.write_audio(processed)

                    # Update latency
                    elapsed = time.perf_counter() - start_time
                    self.latency_samples = int(elapsed * self.sample_rate)
                    self.latency_ms = elapsed * 1000.0

                    if self.latency_ms > 10.0:
                        logger.warning(
                            f"Latency exceeded 10ms: {self.latency_ms:.2f}ms"
                        )

                else:
                    # No audio available, sleep briefly
                    time.sleep(0.0001)

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.001)

        logger.info("Processing loop stopped")

    def get_audio_for_processing(self, timeout: float = 0.01) -> Optional[np.ndarray]:
        """
        Get audio buffer for agent processing.

        Args:
            timeout: Timeout in seconds

        Returns:
            Audio array or None
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_processed_audio(self, audio: np.ndarray):
        """
        Send processed audio back to VST3.

        Args:
            audio: Processed audio array
        """
        try:
            self.processed_queue.put(audio, timeout=0.001)
        except queue.Full:
            logger.warning("Processed queue full, dropping frame")

    def get_latency_info(self) -> Dict:
        """Get latency information."""
        return {
            "latency_samples": self.latency_samples,
            "latency_ms": self.latency_ms,
            "buffer_size": self.buffer_size,
            "sample_rate": self.sample_rate,
        }

    def close(self):
        """Close communicator."""
        self.stop()
        self.input_buffer.close()
        self.output_buffer.close()
        logger.info("VST3 Communicator closed")


if __name__ == "__main__":
    # Test shared memory communication
    logging.basicConfig(level=logging.INFO)

    communicator = VST3Communicator(buffer_size=512)
    communicator.start()

    # Simulate processing
    try:
        for i in range(10):
            audio = communicator.get_audio_for_processing(timeout=1.0)
            if audio is not None:
                # Dummy processing
                processed = audio * 0.5
                communicator.send_processed_audio(processed)
                print(f"Processed frame {i}, latency: {communicator.latency_ms:.2f}ms")
            time.sleep(0.01)
    finally:
        communicator.close()
