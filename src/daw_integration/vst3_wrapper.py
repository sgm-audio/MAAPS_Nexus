"""
VST3 Wrapper with Shared Memory IPC

Provides ultra-low latency communication between VST3 plugin (C++)
and Python audio processing engine using shared memory.

Architecture:
1. VST3 plugin (C++) runs in DAW process
2. Python engine runs as separate process
3. Communication via shared memory (mmap) for <10ms latency
4. Unix domain sockets for control messages
"""

import numpy as np
import mmap
import os
import struct
import time
import threading
import socket
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """IPC message types"""
    INITIALIZE = 0
    PROCESS_AUDIO = 1
    SET_PARAMETER = 2
    GET_PARAMETER = 3
    SHUTDOWN = 4
    HEARTBEAT = 5


@dataclass
class SharedMemoryConfig:
    """Configuration for shared memory communication"""
    shm_name: str = "/maaps_nexus_audio"
    shm_size: int = 1024 * 1024 * 4  # 4 MB (enough for ~23 seconds at 44.1kHz stereo)
    socket_path: str = "/tmp/maaps_nexus_vst.sock"
    max_block_size: int = 8192  # samples
    sample_rate: int = 44100
    num_channels: int = 2


@dataclass
class AudioBlock:
    """Represents an audio block in shared memory"""
    audio_data: np.ndarray  # Shape: (num_channels, num_samples)
    sample_rate: int
    num_samples: int
    timestamp: float
    block_id: int


class SharedMemoryAudioBuffer:
    """
    Manages shared memory for audio data exchange.

    Memory layout:
    - Header (64 bytes):
      - Magic number (4 bytes): 0xMAPS
      - Version (4 bytes)
      - Write offset (8 bytes)
      - Read offset (8 bytes)
      - Block size (4 bytes)
      - Sample rate (4 bytes)
      - Num channels (4 bytes)
      - Block ID (8 bytes)
      - Status flags (8 bytes)
    - Audio data (remaining bytes):
      - Ring buffer of float32 samples
    """

    HEADER_SIZE = 64
    MAGIC_NUMBER = 0x4D415053  # 'MAPS'
    VERSION = 1

    def __init__(self, config: SharedMemoryConfig):
        self.config = config
        self.shm_fd: Optional[int] = None
        self.shm_buffer: Optional[mmap.mmap] = None
        self.is_creator = False

    def create(self):
        """Create shared memory segment (called by Python engine)"""
        try:
            # Create shared memory
            if hasattr(os, 'shm_open'):
                # POSIX shared memory
                try:
                    # Remove if exists
                    os.shm_unlink(self.config.shm_name)
                except FileNotFoundError:
                    pass

                self.shm_fd = os.open(
                    self.config.shm_name,
                    os.O_CREAT | os.O_RDWR,
                    0o666
                )
                os.ftruncate(self.shm_fd, self.config.shm_size)
                self.shm_buffer = mmap.mmap(self.shm_fd, self.config.shm_size)
            else:
                # Fallback to memory-mapped file
                shm_file = f"/tmp{self.config.shm_name}.bin"
                self.shm_fd = os.open(
                    shm_file,
                    os.O_CREAT | os.O_RDWR,
                    0o666
                )
                os.ftruncate(self.shm_fd, self.config.shm_size)
                self.shm_buffer = mmap.mmap(self.shm_fd, self.config.shm_size)

            # Initialize header
            self._write_header(
                magic=self.MAGIC_NUMBER,
                version=self.VERSION,
                write_offset=self.HEADER_SIZE,
                read_offset=self.HEADER_SIZE,
                block_size=self.config.max_block_size,
                sample_rate=self.config.sample_rate,
                num_channels=self.config.num_channels,
                block_id=0,
                status=0,
            )

            self.is_creator = True
            logger.info(f"Created shared memory: {self.config.shm_name}")

        except Exception as e:
            logger.error(f"Failed to create shared memory: {e}")
            raise

    def open(self):
        """Open existing shared memory segment (called by VST3 plugin)"""
        try:
            if hasattr(os, 'shm_open'):
                self.shm_fd = os.open(self.config.shm_name, os.O_RDWR)
                self.shm_buffer = mmap.mmap(self.shm_fd, self.config.shm_size)
            else:
                shm_file = f"/tmp{self.config.shm_name}.bin"
                self.shm_fd = os.open(shm_file, os.O_RDWR)
                self.shm_buffer = mmap.mmap(self.shm_fd, self.config.shm_size)

            # Verify header
            header = self._read_header()
            if header['magic'] != self.MAGIC_NUMBER:
                raise ValueError("Invalid shared memory magic number")

            logger.info(f"Opened shared memory: {self.config.shm_name}")

        except Exception as e:
            logger.error(f"Failed to open shared memory: {e}")
            raise

    def close(self):
        """Close shared memory"""
        if self.shm_buffer:
            self.shm_buffer.close()

        if self.shm_fd:
            os.close(self.shm_fd)

        if self.is_creator and hasattr(os, 'shm_unlink'):
            try:
                os.shm_unlink(self.config.shm_name)
            except Exception:
                pass

    def _write_header(
        self, magic: int, version: int, write_offset: int,
        read_offset: int, block_size: int, sample_rate: int,
        num_channels: int, block_id: int, status: int,
    ):
        """Write header to shared memory"""
        header = struct.pack(
            'IIQQQIIIQ',
            magic, version, write_offset, read_offset,
            block_size, sample_rate, num_channels, block_id, status
        )
        self.shm_buffer.seek(0)
        self.shm_buffer.write(header)
        self.shm_buffer.flush()

    def _read_header(self) -> Dict[str, int]:
        """Read header from shared memory"""
        self.shm_buffer.seek(0)
        header_bytes = self.shm_buffer.read(self.HEADER_SIZE)
        (
            magic, version, write_offset, read_offset, block_size,
            sample_rate, num_channels, block_id, status,
        ) = struct.unpack('IIQQQIIIQ', header_bytes[:48])

        return {
            'magic': magic,
            'version': version,
            'write_offset': write_offset,
            'read_offset': read_offset,
            'block_size': block_size,
            'sample_rate': sample_rate,
            'num_channels': num_channels,
            'block_id': block_id,
            'status': status,
        }

    def write_audio(self, audio: np.ndarray) -> bool:
        """
        Write audio block to shared memory.

        Args:
            audio: Audio data, shape (num_channels, num_samples)

        Returns:
            True if successful
        """
        try:
            num_channels, num_samples = audio.shape
            header = self._read_header()

            # Calculate size needed
            audio_size = num_channels * num_samples * 4  # float32

            # Check if there's space
            available_size = self.config.shm_size - self.HEADER_SIZE
            if audio_size > available_size:
                logger.warning(f"Audio block too large: {audio_size} > {available_size}")
                return False

            # Write audio data
            write_offset = header['write_offset']

            # Wrap around if necessary
            if write_offset + audio_size > self.config.shm_size:
                write_offset = self.HEADER_SIZE

            self.shm_buffer.seek(write_offset)
            audio_bytes = audio.astype(np.float32).tobytes()
            self.shm_buffer.write(audio_bytes)

            # Update header
            new_write_offset = write_offset + audio_size
            new_block_id = header['block_id'] + 1

            self._write_header(
                magic=header['magic'],
                version=header['version'],
                write_offset=new_write_offset,
                read_offset=header['read_offset'],
                block_size=num_samples,
                sample_rate=header['sample_rate'],
                num_channels=num_channels,
                block_id=new_block_id,
                status=1,  # Data available
            )

            return True

        except Exception as e:
            logger.error(f"Error writing audio to shared memory: {e}")
            return False

    def read_audio(self) -> Optional[AudioBlock]:
        """
        Read audio block from shared memory.

        Returns:
            AudioBlock or None if no data available
        """
        try:
            header = self._read_header()

            # Check if data is available
            if header['status'] == 0:
                return None

            read_offset = header['read_offset']
            num_channels = header['num_channels']
            num_samples = header['block_size']

            # Calculate size
            audio_size = num_channels * num_samples * 4

            # Read audio data
            self.shm_buffer.seek(read_offset)
            audio_bytes = self.shm_buffer.read(audio_size)

            # Convert to numpy array
            audio_flat = np.frombuffer(audio_bytes, dtype=np.float32)
            audio = audio_flat.reshape(num_channels, num_samples)

            # Update read offset
            new_read_offset = read_offset + audio_size
            if new_read_offset >= self.config.shm_size:
                new_read_offset = self.HEADER_SIZE

            self._write_header(
                magic=header['magic'],
                version=header['version'],
                write_offset=header['write_offset'],
                read_offset=new_read_offset,
                block_size=header['block_size'],
                sample_rate=header['sample_rate'],
                num_channels=header['num_channels'],
                block_id=header['block_id'],
                status=0,  # Data consumed
            )

            return AudioBlock(
                audio_data=audio,
                sample_rate=header['sample_rate'],
                num_samples=num_samples,
                timestamp=time.time(),
                block_id=header['block_id'],
            )

        except Exception as e:
            logger.error(f"Error reading audio from shared memory: {e}")
            return None


class VST3Backend:
    """
    Python backend for VST3 plugin.

    Receives audio from VST3 via shared memory, processes it through
    the multi-agent system, and returns processed audio.
    """

    def __init__(self, config: SharedMemoryConfig,
                 audio_processor: Optional[Callable] = None):
        self.config = config
        self.audio_processor = audio_processor
        self.shm_buffer = SharedMemoryAudioBuffer(config)
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.processing_thread: Optional[threading.Thread] = None

        # Statistics
        self.blocks_processed = 0
        self.total_latency = 0.0
        self.max_latency = 0.0

    def start(self):
        """Start the backend"""
        try:
            # Create shared memory
            self.shm_buffer.create()

            # Create Unix domain socket for control
            self._create_control_socket()

            # Start processing thread
            self.running = True
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.start()

            logger.info("VST3 Backend started")

        except Exception as e:
            logger.error(f"Failed to start VST3 backend: {e}")
            raise

    def stop(self):
        """Stop the backend"""
        self.running = False

        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)

        self.shm_buffer.close()

        if self.socket:
            self.socket.close()

        # Remove socket file
        try:
            os.unlink(self.config.socket_path)
        except Exception:
            pass

        logger.info("VST3 Backend stopped")

    def _create_control_socket(self):
        """Create Unix domain socket for control messages"""
        # Remove existing socket
        try:
            os.unlink(self.config.socket_path)
        except FileNotFoundError:
            pass

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.config.socket_path)
        self.socket.listen(1)
        self.socket.settimeout(1.0)  # Non-blocking with timeout

        logger.info(f"Control socket created: {self.config.socket_path}")

    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Read audio from shared memory
                audio_block = self.shm_buffer.read_audio()

                if audio_block is not None:
                    start_time = time.time()

                    # Process audio
                    if self.audio_processor:
                        processed_audio = self.audio_processor(audio_block.audio_data)
                    else:
                        # Pass-through if no processor
                        processed_audio = audio_block.audio_data

                    # Write back to shared memory
                    self.shm_buffer.write_audio(processed_audio)

                    # Update statistics
                    latency = (time.time() - start_time) * 1000  # ms
                    self.blocks_processed += 1
                    self.total_latency += latency
                    self.max_latency = max(self.max_latency, latency)

                    if self.blocks_processed % 100 == 0:
                        avg_latency = self.total_latency / self.blocks_processed
                        logger.debug(
                            f"Processed {self.blocks_processed} blocks, "
                            f"avg latency={avg_latency:.2f}ms, "
                            f"max={self.max_latency:.2f}ms"
                        )

                else:
                    # No data available, sleep briefly
                    time.sleep(0.001)  # 1ms

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.01)

    def set_audio_processor(self, processor: Callable):
        """Set the audio processing function"""
        self.audio_processor = processor


# Example usage and integration
def create_vst3_backend_for_hgo(hgo_coordinator_id: str, message_bus) -> VST3Backend:
    """
    Create VST3 backend integrated with HGO coordinator.

    Args:
        hgo_coordinator_id: ID of HGO coordinator agent
        message_bus: Message bus for agent communication

    Returns:
        VST3Backend instance
    """

    def process_audio_with_hgo(audio: np.ndarray) -> np.ndarray:
        """Process audio through HGO coordinator"""
        try:
            from src.core.types import Message as AgentMessage, MessageType as AgentMessageType, Topics

            response = message_bus.request(
                AgentMessage(
                    topic=Topics.agent_request(hgo_coordinator_id),
                    sender="vst3_backend",
                    message_type=AgentMessageType.COORDINATION_UPDATE,
                    payload={
                        'audio': audio,
                        'training': False,  # Inference mode in VST
                        'max_steps': 1,  # Low latency - single step
                    },
                )
            )

            if response and response.payload.get('status') == 'success':
                return response.payload.get('processed_audio', audio)
            else:
                logger.warning("HGO coordination failed, returning original audio")
                return audio

        except Exception as e:
            logger.error(f"Error processing audio with HGO: {e}")
            return audio

    config = SharedMemoryConfig()
    backend = VST3Backend(config, audio_processor=process_audio_with_hgo)

    return backend
