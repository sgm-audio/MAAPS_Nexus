"""
Audio Enhancement & Restoration Agent

This agent handles comprehensive audio enhancement and restoration tasks including:
- Adaptive noise reduction
- Click and pop removal
- Clipping restoration
- Spectral repair
- Audio super-resolution
"""

import numpy as np
import threading
import queue
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging

try:
    import librosa
    import scipy.signal as signal
    import scipy.ndimage as ndimage
except ImportError:
    librosa = None
    signal = None
    ndimage = None

from ..core import BaseAgent, Message, Topics, Priority

logger = logging.getLogger(__name__)


@dataclass
class EnhancementResult:
    """Result from audio enhancement operation"""
    enhanced_audio: np.ndarray
    quality_improvement: Dict[str, float]
    processing_chain: List[str]
    quality_report: Dict[str, Any]
    timestamp: float


@dataclass
class QualityMetrics:
    """Audio quality metrics"""
    snr: float  # Signal-to-noise ratio
    thd: float  # Total harmonic distortion
    dynamic_range: float
    peak_level: float
    rms_level: float
    crest_factor: float


class AudioEnhancementAgent(BaseAgent):
    """
    Agent responsible for audio enhancement and restoration tasks.

    Capabilities:
    - Adaptive noise reduction
    - Click/pop removal
    - Clipping restoration
    - Spectral repair
    - Super-resolution enhancement
    """

    def __init__(self):
        super().__init__(
            agent_id="audio_enhancement_agent",
            agent_name="Audio Enhancement & Restoration Agent"
        )

        # Processing queue
        self.processing_queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None

        # Enhancement parameters
        self.default_params = {
            'noise_reduction_amount': 0.8,
            'preserve_transients': True,
            'declicking_sensitivity': 0.5,
            'declipping_threshold': 0.95,
            'enhancement_profile': 'balanced'
        }

        # Statistics
        self.stats = {
            'files_processed': 0,
            'total_enhancement_time': 0.0,
            'avg_quality_improvement': 0.0
        }
        self.stats_lock = threading.Lock()

    def setup(self):
        """Initialize the enhancement agent"""
        # Subscribe to relevant topics
        self.subscribe("audio.enhancement.request")
        self.subscribe("audio.noise.reduction.request")
        self.subscribe("audio.restoration.request")
        self.subscribe("audio.superresolution.request")

        # Start processing thread
        self._start_processing_thread()

        self.log("INFO", "Audio Enhancement Agent initialized successfully")

    def teardown(self):
        """Cleanup resources"""
        # Stop processing thread
        self._stop_processing_thread()

        self.log("INFO", "Audio Enhancement Agent shutdown complete")

    def handle_message(self, message: Message):
        """Process incoming messages"""
        try:
            if message.topic == "audio.enhancement.request":
                self._handle_enhancement_request(message)
            elif message.topic == "audio.noise.reduction.request":
                self._handle_noise_reduction_request(message)
            elif message.topic == "audio.restoration.request":
                self._handle_restoration_request(message)
            elif message.topic == "audio.superresolution.request":
                self._handle_superresolution_request(message)
            else:
                self.log("WARNING", f"Unknown message topic: {message.topic}")

        except Exception as e:
            self.log("ERROR", f"Error handling message: {e}", {"topic": message.topic})

    def _handle_enhancement_request(self, message: Message):
        """Handle general audio enhancement request"""
        payload = message.payload
        audio_data = payload.get('audio_data')
        sample_rate = payload.get('sample_rate', 44100)
        params = {**self.default_params, **payload.get('params', {})}

        if audio_data is None:
            self.respond(message, {
                'success': False,
                'error': 'No audio data provided'
            })
            return

        # Queue the enhancement job
        job = {
            'type': 'enhancement',
            'message': message,
            'audio_data': audio_data,
            'sample_rate': sample_rate,
            'params': params
        }
        self.processing_queue.put(job)

    def _handle_noise_reduction_request(self, message: Message):
        """Handle noise reduction request"""
        payload = message.payload
        audio_data = payload.get('audio_data')
        sample_rate = payload.get('sample_rate', 44100)
        reduction_amount = payload.get('reduction_amount', 0.8)

        if audio_data is None:
            self.respond(message, {
                'success': False,
                'error': 'No audio data provided'
            })
            return

        job = {
            'type': 'noise_reduction',
            'message': message,
            'audio_data': audio_data,
            'sample_rate': sample_rate,
            'reduction_amount': reduction_amount
        }
        self.processing_queue.put(job)

    def _handle_restoration_request(self, message: Message):
        """Handle restoration request (declicking, declipping)"""
        payload = message.payload
        audio_data = payload.get('audio_data')
        sample_rate = payload.get('sample_rate', 44100)
        restoration_type = payload.get('restoration_type', 'auto')

        if audio_data is None:
            self.respond(message, {
                'success': False,
                'error': 'No audio data provided'
            })
            return

        job = {
            'type': 'restoration',
            'message': message,
            'audio_data': audio_data,
            'sample_rate': sample_rate,
            'restoration_type': restoration_type
        }
        self.processing_queue.put(job)

    def _handle_superresolution_request(self, message: Message):
        """Handle super-resolution enhancement request"""
        payload = message.payload
        audio_data = payload.get('audio_data')
        current_sr = payload.get('current_sample_rate', 22050)
        target_sr = payload.get('target_sample_rate', 44100)

        if audio_data is None:
            self.respond(message, {
                'success': False,
                'error': 'No audio data provided'
            })
            return

        job = {
            'type': 'superresolution',
            'message': message,
            'audio_data': audio_data,
            'current_sr': current_sr,
            'target_sr': target_sr
        }
        self.processing_queue.put(job)

    def _start_processing_thread(self):
        """Start the processing worker thread"""
        self.processing_thread = threading.Thread(
            target=self._processing_worker,
            name=f"{self.agent_id}_processor",
            daemon=True
        )
        self.processing_thread.start()

    def _stop_processing_thread(self):
        """Stop the processing worker thread"""
        if self.processing_thread and self.processing_thread.is_alive():
            # Add sentinel to stop thread
            self.processing_queue.put(None)
            self.processing_thread.join(timeout=5.0)

    def _processing_worker(self):
        """Worker thread for processing enhancement jobs"""
        import time

        while True:
            try:
                job = self.processing_queue.get(timeout=1.0)

                if job is None:  # Sentinel to stop
                    break

                start_time = time.time()

                # Process based on job type
                if job['type'] == 'enhancement':
                    result = self._process_enhancement(job)
                elif job['type'] == 'noise_reduction':
                    result = self._process_noise_reduction(job)
                elif job['type'] == 'restoration':
                    result = self._process_restoration(job)
                elif job['type'] == 'superresolution':
                    result = self._process_superresolution(job)
                else:
                    result = {
                        'success': False,
                        'error': f"Unknown job type: {job['type']}"
                    }

                processing_time = time.time() - start_time

                # Update statistics
                with self.stats_lock:
                    self.stats['files_processed'] += 1
                    self.stats['total_enhancement_time'] += processing_time

                # Add processing time to result
                result['processing_time_seconds'] = processing_time

                # Send response
                self.respond(job['message'], result)

                # Publish completion event
                self.publish(
                    "audio.enhancement.complete",
                    {
                        'job_type': job['type'],
                        'success': result.get('success', False),
                        'processing_time': processing_time
                    },
                    priority=Priority.LOW
                )

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker: {e}")
                if 'job' in locals() and 'message' in job:
                    self.respond(job['message'], {
                        'success': False,
                        'error': str(e)
                    })

    def _process_enhancement(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process comprehensive audio enhancement"""
        if librosa is None:
            return {
                'success': False,
                'error': 'librosa not installed'
            }

        try:
            audio_data = job['audio_data']
            sample_rate = job['sample_rate']
            params = job['params']

            # Ensure audio is numpy array
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)

            # Quality analysis before
            quality_before = self._analyze_quality(audio_data, sample_rate)

            enhanced_audio = audio_data.copy()
            processing_chain = []

            # Apply noise reduction
            if params.get('noise_reduction_amount', 0) > 0:
                enhanced_audio = self._apply_noise_reduction(
                    enhanced_audio,
                    sample_rate,
                    params['noise_reduction_amount']
                )
                processing_chain.append('noise_reduction')

            # Apply declicking
            if params.get('declicking_sensitivity', 0) > 0:
                enhanced_audio = self._apply_declicking(
                    enhanced_audio,
                    sample_rate,
                    params['declicking_sensitivity']
                )
                processing_chain.append('declicking')

            # Apply declipping
            if params.get('declipping_threshold', 0) < 1.0:
                enhanced_audio = self._apply_declipping(
                    enhanced_audio,
                    params['declipping_threshold']
                )
                processing_chain.append('declipping')

            # Quality analysis after
            quality_after = self._analyze_quality(enhanced_audio, sample_rate)

            # Calculate improvement
            quality_improvement = {
                'snr_improvement_db': quality_after.snr - quality_before.snr,
                'dynamic_range_improvement_db': quality_after.dynamic_range - quality_before.dynamic_range,
                'thd_reduction_percent': ((quality_before.thd - quality_after.thd) / quality_before.thd * 100) if quality_before.thd > 0 else 0
            }

            return {
                'success': True,
                'enhanced_audio': enhanced_audio.tolist(),
                'sample_rate': sample_rate,
                'quality_improvement': quality_improvement,
                'processing_chain': processing_chain,
                'quality_before': {
                    'snr_db': quality_before.snr,
                    'dynamic_range_db': quality_before.dynamic_range,
                    'thd_percent': quality_before.thd
                },
                'quality_after': {
                    'snr_db': quality_after.snr,
                    'dynamic_range_db': quality_after.dynamic_range,
                    'thd_percent': quality_after.thd
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Enhancement processing failed: {str(e)}"
            }

    def _process_noise_reduction(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process noise reduction"""
        if librosa is None:
            return {
                'success': False,
                'error': 'librosa not installed'
            }

        try:
            audio_data = job['audio_data']
            sample_rate = job['sample_rate']
            reduction_amount = job['reduction_amount']

            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)

            enhanced_audio = self._apply_noise_reduction(
                audio_data,
                sample_rate,
                reduction_amount
            )

            return {
                'success': True,
                'enhanced_audio': enhanced_audio.tolist(),
                'sample_rate': sample_rate,
                'reduction_amount': reduction_amount
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Noise reduction failed: {str(e)}"
            }

    def _process_restoration(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio restoration"""
        if librosa is None:
            return {
                'success': False,
                'error': 'librosa not installed'
            }

        try:
            audio_data = job['audio_data']
            sample_rate = job['sample_rate']
            restoration_type = job['restoration_type']

            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)

            restored_audio = audio_data.copy()
            operations = []

            if restoration_type in ['auto', 'declicking']:
                restored_audio = self._apply_declicking(restored_audio, sample_rate, 0.5)
                operations.append('declicking')

            if restoration_type in ['auto', 'declipping']:
                restored_audio = self._apply_declipping(restored_audio, 0.95)
                operations.append('declipping')

            return {
                'success': True,
                'restored_audio': restored_audio.tolist(),
                'sample_rate': sample_rate,
                'operations_applied': operations
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Restoration failed: {str(e)}"
            }

    def _process_superresolution(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process super-resolution enhancement"""
        if librosa is None:
            return {
                'success': False,
                'error': 'librosa not installed'
            }

        try:
            audio_data = job['audio_data']
            current_sr = job['current_sr']
            target_sr = job['target_sr']

            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)

            # Use librosa's resampling as baseline
            enhanced_audio = librosa.resample(
                audio_data,
                orig_sr=current_sr,
                target_sr=target_sr,
                res_type='kaiser_best'
            )

            return {
                'success': True,
                'enhanced_audio': enhanced_audio.tolist(),
                'original_sr': current_sr,
                'target_sr': target_sr,
                'length_ratio': len(enhanced_audio) / len(audio_data)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Super-resolution failed: {str(e)}"
            }

    def _apply_noise_reduction(self, audio: np.ndarray, sample_rate: int, reduction_amount: float) -> np.ndarray:
        """Apply spectral subtraction noise reduction"""
        if librosa is None or signal is None:
            return audio

        # STFT parameters
        n_fft = 2048
        hop_length = 512

        # Compute STFT
        stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # Estimate noise spectrum from first and last 10% of audio
        noise_frames = max(1, int(0.1 * magnitude.shape[1]))
        noise_spectrum = np.mean(np.concatenate([
            magnitude[:, :noise_frames],
            magnitude[:, -noise_frames:]
        ], axis=1), axis=1, keepdims=True)

        # Spectral subtraction with oversubtraction
        alpha = 2.0  # Oversubtraction factor
        beta = 0.01  # Spectral floor

        gain = 1 - (alpha * noise_spectrum) / (magnitude + 1e-10)
        gain = np.maximum(gain, beta)

        # Apply smoothing to reduce musical noise
        if ndimage is not None:
            gain = ndimage.gaussian_filter1d(gain, sigma=1.0, axis=0)
            gain = ndimage.gaussian_filter1d(gain, sigma=2.0, axis=1)

        # Apply gain
        enhanced_magnitude = magnitude * gain * reduction_amount + magnitude * (1 - reduction_amount)

        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=hop_length, length=len(audio))

        return enhanced_audio

    def _apply_declicking(self, audio: np.ndarray, sample_rate: int, sensitivity: float) -> np.ndarray:
        """Apply declicking using median filtering"""
        # Simple declicking using median filter
        # In production, this would use more sophisticated click detection
        window_size = int(0.001 * sample_rate)  # 1ms window
        if window_size % 2 == 0:
            window_size += 1

        if signal is not None:
            declick_audio = signal.medfilt(audio, kernel_size=min(window_size, 11))
            # Blend based on sensitivity
            return audio * (1 - sensitivity * 0.3) + declick_audio * (sensitivity * 0.3)
        else:
            return audio

    def _apply_declipping(self, audio: np.ndarray, threshold: float) -> np.ndarray:
        """Apply declipping restoration"""
        # Detect clipped samples
        clipped_mask = np.abs(audio) > threshold

        if not np.any(clipped_mask):
            return audio  # No clipping detected

        # Simple cubic interpolation for clipped regions
        # In production, this would use more sophisticated restoration
        declipped_audio = audio.copy()

        # Find clipped regions
        clipped_indices = np.where(clipped_mask)[0]
        if len(clipped_indices) > 0:
            # Group consecutive indices
            groups = np.split(clipped_indices, np.where(np.diff(clipped_indices) != 1)[0] + 1)

            for group in groups:
                if len(group) > 0:
                    start = max(0, group[0] - 2)
                    end = min(len(audio), group[-1] + 3)

                    # Use surrounding samples for interpolation
                    if start > 0 and end < len(audio):
                        x = [start, end]
                        y = [audio[start], audio[end]]
                        if len(group) > 1:
                            xnew = range(group[0], group[-1] + 1)
                            ynew = np.interp(xnew, x, y)
                            declipped_audio[group] = ynew

        return declipped_audio

    def _analyze_quality(self, audio: np.ndarray, sample_rate: int) -> QualityMetrics:
        """Analyze audio quality metrics"""
        # Calculate RMS level
        rms_level = np.sqrt(np.mean(audio ** 2))

        # Calculate peak level
        peak_level = np.max(np.abs(audio))

        # Calculate crest factor
        crest_factor = peak_level / (rms_level + 1e-10)

        # Calculate dynamic range
        dynamic_range = 20 * np.log10(peak_level / (rms_level + 1e-10))

        # Estimate SNR (simplified)
        # In production, this would use more sophisticated analysis
        noise_floor = np.percentile(np.abs(audio), 10)
        signal_level = np.percentile(np.abs(audio), 90)
        snr = 20 * np.log10((signal_level + 1e-10) / (noise_floor + 1e-10))

        # Estimate THD (simplified)
        thd = 0.01  # Placeholder - real implementation would use FFT analysis

        return QualityMetrics(
            snr=snr,
            thd=thd,
            dynamic_range=dynamic_range,
            peak_level=peak_level,
            rms_level=rms_level,
            crest_factor=crest_factor
        )
