# MAAPS API & User Interface Specification
## Phases 1-3 Complete Integration

---

## Executive Summary

This document provides comprehensive API and UI specifications for the Multi-Agent Audio Processing System (MAAPS) covering Phases 1-3:

- **Phase 1**: Core infrastructure, audio enhancement, content generation, metadata management
- **Phase 2**: Live effects chain (15 DSP effects), live looping (8 tracks)
- **Phase 3**: Synchronization/clock, performance automation (scenes, macros, cues)

**Technology Stack**:
- **Backend API**: FastAPI (Python) with async/await
- **Real-time Communication**: WebSocket for live updates
- **Frontend**: React + TypeScript
- **State Management**: Redux Toolkit
- **Audio Visualization**: Web Audio API + Canvas/WebGL

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [REST API Specification](#rest-api-specification)
3. [WebSocket API](#websocket-api)
4. [User Interface Design](#user-interface-design)
5. [Data Schemas](#data-schemas)
6. [Authentication & Security](#authentication--security)
7. [Implementation Guide](#implementation-guide)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser                              │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              React Frontend (TypeScript)               │     │
│  │  - UI Components (Effects, Looping, Automation)       │     │
│  │  - State Management (Redux)                           │     │
│  │  - Audio Visualization (Web Audio API)                │     │
│  └───────────┬──────────────────────────┬─────────────────┘     │
│              │ HTTP/REST                │ WebSocket              │
└──────────────┼──────────────────────────┼─────────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                         │
│                                                                    │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              REST API Layer (FastAPI)                     │   │
│  │  - Endpoints for all agent operations                     │   │
│  │  - Request validation (Pydantic)                          │   │
│  │  - Response serialization                                 │   │
│  └─────────────────┬─────────────────────────────────────────┘   │
│                    │                                              │
│  ┌─────────────────┴─────────────────────────────────────────┐   │
│  │           WebSocket Manager (Real-time Updates)           │   │
│  │  - Broadcast agent events to connected clients            │   │
│  │  - Room-based subscriptions (per session)                 │   │
│  │  - Connection management                                  │   │
│  └─────────────────┬─────────────────────────────────────────┘   │
│                    │                                              │
│  ┌─────────────────┴─────────────────────────────────────────┐   │
│  │              Message Bus Adapter                          │   │
│  │  - Subscribe to agent topics                              │   │
│  │  - Publish API requests as messages                       │   │
│  │  - Convert messages to WebSocket events                   │   │
│  └─────────────────┬─────────────────────────────────────────┘   │
│                    │                                              │
└────────────────────┼──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                MAAPS Multi-Agent System (Existing)                │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Audio        │  │ Effects      │  │ Looping      │           │
│  │ Enhancement  │  │ Chain        │  │ Agent        │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Sync Clock   │  │ Performance  │  │ Metadata     │           │
│  │ Agent        │  │ Automation   │  │ Management   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│                    Message Bus                                    │
└──────────────────────────────────────────────────────────────────┘
```

### API Server Components

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import (
    effects,
    looping,
    sync,
    automation,
    audio,
    metadata,
    system
)
from api.websocket import websocket_manager

app = FastAPI(
    title="MAAPS API",
    version="1.0.0",
    description="Multi-Agent Audio Processing System API"
)

# CORS for web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(effects.router, prefix="/api/v1/effects", tags=["Effects"])
app.include_router(looping.router, prefix="/api/v1/looping", tags=["Looping"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Sync & Clock"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["Automation"])
app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio Processing"])
app.include_router(metadata.router, prefix="/api/v1/metadata", tags=["Metadata"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    # Handle messages...
```

---

## REST API Specification

### Base URL
```
http://localhost:8000/api/v1
```

### API Version
```
Version: 1.0.0
Content-Type: application/json
```

---

## 1. Effects Chain API

### 1.1 Create Effect Chain

**Endpoint**: `POST /effects/chains`

**Request Body**:
```json
{
  "chain_name": "Vocal Chain",
  "effects": [
    {
      "type": "gate",
      "parameters": {
        "threshold": -40.0,
        "attack": 5.0,
        "release": 50.0
      },
      "bypass": false,
      "wet_dry": 1.0
    },
    {
      "type": "compressor",
      "parameters": {
        "threshold": -18.0,
        "ratio": 4.0,
        "attack": 5.0,
        "release": 50.0,
        "knee": 2.0,
        "makeup_gain": 0.0
      },
      "bypass": false,
      "wet_dry": 1.0
    },
    {
      "type": "eq_parametric",
      "parameters": {
        "freq1": 100.0,
        "gain1": -3.0,
        "q1": 1.0,
        "freq2": 3000.0,
        "gain2": 2.5,
        "q2": 1.4
      },
      "bypass": false,
      "wet_dry": 1.0
    }
  ]
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "chain_id": "chain_vocal_001",
    "chain_name": "Vocal Chain",
    "num_effects": 3,
    "total_latency_ms": 9.2,
    "created_at": "2025-11-17T10:30:00Z"
  }
}
```

---

### 1.2 List Effect Chains

**Endpoint**: `GET /effects/chains`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "chains": [
      {
        "chain_id": "chain_vocal_001",
        "chain_name": "Vocal Chain",
        "num_effects": 3,
        "bypass": false,
        "total_latency_ms": 9.2
      },
      {
        "chain_id": "chain_drums_001",
        "chain_name": "Drum Bus",
        "num_effects": 5,
        "bypass": false,
        "total_latency_ms": 15.4
      }
    ],
    "total_chains": 2
  }
}
```

---

### 1.3 Get Effect Chain Details

**Endpoint**: `GET /effects/chains/{chain_id}`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "chain_id": "chain_vocal_001",
    "chain_name": "Vocal Chain",
    "bypass": false,
    "effects": [
      {
        "effect_id": "effect_001",
        "type": "gate",
        "bypass": false,
        "wet_dry": 1.0,
        "parameters": {
          "threshold": -40.0,
          "attack": 5.0,
          "release": 50.0
        },
        "latency_ms": 3.1
      },
      {
        "effect_id": "effect_002",
        "type": "compressor",
        "bypass": false,
        "wet_dry": 1.0,
        "parameters": {
          "threshold": -18.0,
          "ratio": 4.0,
          "attack": 5.0,
          "release": 50.0
        },
        "latency_ms": 3.1
      }
    ],
    "total_latency_ms": 9.2
  }
}
```

---

### 1.4 Update Effect Parameters

**Endpoint**: `PATCH /effects/chains/{chain_id}/effects/{effect_id}/parameters`

**Request Body**:
```json
{
  "parameters": {
    "threshold": -20.0,
    "ratio": 6.0
  }
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "effect_id": "effect_002",
    "parameters": {
      "threshold": -20.0,
      "ratio": 6.0,
      "attack": 5.0,
      "release": 50.0
    }
  }
}
```

---

### 1.5 Toggle Effect Bypass

**Endpoint**: `POST /effects/chains/{chain_id}/effects/{effect_id}/bypass`

**Request Body**:
```json
{
  "bypass": true
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "effect_id": "effect_002",
    "bypass": true
  }
}
```

---

### 1.6 Preset Management

**Endpoint**: `POST /effects/presets`

**Request Body** (Save Preset):
```json
{
  "preset_name": "Warm Vocal Compression",
  "chain_id": "chain_vocal_001"
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "preset_id": "preset_001",
    "preset_name": "Warm Vocal Compression",
    "created_at": "2025-11-17T10:35:00Z"
  }
}
```

**Endpoint**: `POST /effects/chains/{chain_id}/presets/{preset_id}/recall`

**Response**: `200 OK`
```json
{
  "status": "success",
  "message": "Preset 'Warm Vocal Compression' recalled"
}
```

---

### 1.7 Scene Management

**Endpoint**: `POST /effects/scenes`

**Request Body**:
```json
{
  "scene_name": "Verse 1",
  "description": "Clean, intimate vocal sound",
  "presets": [
    {
      "chain_id": "chain_vocal_001",
      "preset_id": "preset_001"
    },
    {
      "chain_id": "chain_drums_001",
      "preset_id": "preset_003"
    }
  ]
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "scene_id": "scene_001",
    "scene_name": "Verse 1",
    "num_presets": 2
  }
}
```

**Endpoint**: `POST /effects/scenes/{scene_id}/trigger`

**Response**: `200 OK`
```json
{
  "status": "success",
  "message": "Scene 'Verse 1' triggered"
}
```

---

### 1.8 A/B Comparison

**Endpoint**: `POST /effects/chains/{chain_id}/ab/compare`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "comparing": true,
    "state_a": "current",
    "state_b": "previous"
  }
}
```

---

## 2. Live Looping API

### 2.1 Create Loop Track

**Endpoint**: `POST /looping/tracks`

**Request Body**:
```json
{
  "track_name": "Drums",
  "length_beats": 4,
  "sync_to_tempo": true,
  "volume": 0.8,
  "pan": 0.0
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "track_name": "Drums",
    "length_beats": 4,
    "length_samples": 211680,
    "status": "empty",
    "sync_to_tempo": true
  }
}
```

---

### 2.2 Start Recording

**Endpoint**: `POST /looping/tracks/{track_id}/record/start`

**Request Body**:
```json
{
  "mode": "replace"  // "replace", "overdub", "multiply"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "recording": true,
    "mode": "replace",
    "started_at": "2025-11-17T10:40:00Z"
  }
}
```

---

### 2.3 Stop Recording

**Endpoint**: `POST /looping/tracks/{track_id}/record/stop`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "recording": false,
    "recorded_length_samples": 211680,
    "recorded_length_beats": 4,
    "status": "playing"
  }
}
```

---

### 2.4 Toggle Playback

**Endpoint**: `POST /looping/tracks/{track_id}/playback/toggle`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "playing": true
  }
}
```

---

### 2.5 Loop Manipulation

**Endpoint**: `POST /looping/tracks/{track_id}/manipulate`

**Request Body** (Reverse):
```json
{
  "operation": "reverse"
}
```

**Request Body** (Pitch Shift):
```json
{
  "operation": "pitch_shift",
  "parameters": {
    "semitones": 2.0
  }
}
```

**Request Body** (Time Stretch):
```json
{
  "operation": "time_stretch",
  "parameters": {
    "factor": 0.5  // Half speed
  }
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "operation": "pitch_shift",
    "applied": true,
    "processing_time_ms": 120
  }
}
```

---

### 2.6 Undo/Redo

**Endpoint**: `POST /looping/tracks/{track_id}/undo`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "undo_available": 2,
    "redo_available": 1
  }
}
```

---

### 2.7 Clear Loop

**Endpoint**: `POST /looping/tracks/{track_id}/clear`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "track_id": "loop_track_001",
    "status": "empty"
  }
}
```

---

### 2.8 Get All Loop Tracks

**Endpoint**: `GET /looping/tracks`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "tracks": [
      {
        "track_id": "loop_track_001",
        "track_name": "Drums",
        "status": "playing",
        "length_beats": 4,
        "volume": 0.8,
        "pan": 0.0,
        "undo_available": 3,
        "redo_available": 0
      },
      {
        "track_id": "loop_track_002",
        "track_name": "Bass",
        "status": "paused",
        "length_beats": 2,
        "volume": 0.7,
        "pan": -0.2,
        "undo_available": 1,
        "redo_available": 2
      }
    ],
    "total_tracks": 2
  }
}
```

---

## 3. Sync & Clock API

### 3.1 Set Tempo

**Endpoint**: `POST /sync/tempo/set`

**Request Body**:
```json
{
  "bpm": 128.0,
  "time_signature": "4/4"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "bpm": 128.0,
    "time_signature": "4/4"
  }
}
```

---

### 3.2 Tap Tempo

**Endpoint**: `POST /sync/tempo/tap`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "bpm": 126.5,
    "taps_recorded": 4,
    "confidence": 0.85
  }
}
```

---

### 3.3 Transport Control

**Endpoint**: `POST /sync/transport/play`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "playing": true,
    "position_seconds": 0.0,
    "position_beats": 1.0,
    "position_bars": 1
  }
}
```

**Endpoint**: `POST /sync/transport/stop`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "playing": false,
    "position_seconds": 0.0
  }
}
```

**Endpoint**: `POST /sync/transport/pause`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "playing": false,
    "position_seconds": 45.2,
    "position_beats": 97.0,
    "position_bars": 25
  }
}
```

---

### 3.4 Get Clock Status

**Endpoint**: `GET /sync/status`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "bpm": 128.0,
    "time_signature": "4/4",
    "playing": true,
    "position": {
      "seconds": 45.2,
      "beats": 97.0,
      "bars": 25,
      "beat_in_bar": 1
    },
    "midi_clock": {
      "enabled": false,
      "port": null
    },
    "ableton_link": {
      "enabled": false,
      "peers": 0
    }
  }
}
```

---

### 3.5 MIDI Clock Control

**Endpoint**: `POST /sync/midi-clock/enable`

**Request Body**:
```json
{
  "enable": true,
  "midi_port": "MIDI_OUT_1"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "midi_clock_enabled": true,
    "midi_port": "MIDI_OUT_1"
  }
}
```

---

### 3.6 Ableton Link Control

**Endpoint**: `POST /sync/link/enable`

**Request Body**:
```json
{
  "enable": true
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "link_enabled": true,
    "peers": 2,
    "session_tempo": 128.0
  }
}
```

---

## 4. Performance Automation API

### 4.1 Record Automation

**Endpoint**: `POST /automation/record/start`

**Request Body**:
```json
{
  "parameter_path": "effects.chain_vocal_001.effect_002.threshold"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "recording": true,
    "parameter_path": "effects.chain_vocal_001.effect_002.threshold",
    "lane_id": "lane_001"
  }
}
```

**Endpoint**: `POST /automation/record/stop`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "recording": false,
    "lane_id": "lane_001",
    "points_recorded": 45
  }
}
```

---

### 4.2 Enable Automation Playback

**Endpoint**: `POST /automation/playback/enable`

**Request Body**:
```json
{
  "enable": true
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "playback_enabled": true,
    "active_lanes": 3
  }
}
```

---

### 4.3 Create Scene

**Endpoint**: `POST /automation/scenes`

**Request Body**:
```json
{
  "scene_name": "Chorus Build",
  "parameter_snapshots": {
    "effects.chain_vocal_001.effect_002.threshold": -15.0,
    "effects.chain_drums_001.effect_001.threshold": -12.0,
    "looping.track_001.volume": 0.9
  },
  "transition_time": 2.0,
  "transition_curves": {
    "effects.chain_vocal_001.effect_002.threshold": "exponential",
    "effects.chain_drums_001.effect_001.threshold": "linear",
    "looping.track_001.volume": "logarithmic"
  }
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "scene_id": "scene_001",
    "scene_name": "Chorus Build",
    "num_parameters": 3,
    "transition_time": 2.0
  }
}
```

---

### 4.4 Trigger Scene

**Endpoint**: `POST /automation/scenes/{scene_id}/trigger`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "scene_id": "scene_001",
    "scene_name": "Chorus Build",
    "triggered_at": "2025-11-17T11:00:00Z"
  }
}
```

---

### 4.5 Create Macro

**Endpoint**: `POST /automation/macros`

**Request Body**:
```json
{
  "macro_name": "Energy Level",
  "target_parameters": [
    {
      "param": "effects.chain_vocal_001.effect_003.gain3",
      "min": 0.0,
      "max": 6.0,
      "curve": "exponential"
    },
    {
      "param": "effects.chain_drums_001.effect_002.ratio",
      "min": 2.0,
      "max": 8.0,
      "curve": "logarithmic"
    }
  ]
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "macro_id": "macro_001",
    "macro_name": "Energy Level",
    "num_targets": 2,
    "value": 0.0
  }
}
```

---

### 4.6 Change Macro Value

**Endpoint**: `POST /automation/macros/{macro_id}/value`

**Request Body**:
```json
{
  "value": 0.75
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "macro_id": "macro_001",
    "value": 0.75,
    "affected_parameters": [
      {
        "param": "effects.chain_vocal_001.effect_003.gain3",
        "value": 5.1
      },
      {
        "param": "effects.chain_drums_001.effect_002.ratio",
        "value": 6.2
      }
    ]
  }
}
```

---

### 4.7 Create Performance Cue

**Endpoint**: `POST /automation/cues`

**Request Body**:
```json
{
  "cue_name": "Drop at 2:30",
  "timecode": "00:02:30.000",
  "actions": [
    {
      "action_type": "scene_change",
      "parameters": {
        "scene_id": "scene_drop"
      }
    },
    {
      "action_type": "parameter_change",
      "parameters": {
        "parameter_path": "effects.chain_master.effect_filter.cutoff",
        "value": 20000.0
      }
    }
  ]
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "data": {
    "cue_id": "cue_001",
    "cue_name": "Drop at 2:30",
    "timecode": "00:02:30.000",
    "num_actions": 2
  }
}
```

---

### 4.8 Fire Cue Manually

**Endpoint**: `POST /automation/cues/{cue_id}/fire`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "cue_id": "cue_001",
    "cue_name": "Drop at 2:30",
    "fired_at": "2025-11-17T11:05:00Z",
    "actions_executed": 2
  }
}
```

---

## 5. Audio Processing API (Phase 1)

### 5.1 Enhance Audio

**Endpoint**: `POST /audio/enhance`

**Request Body**:
```json
{
  "audio_data": [0.1, 0.2, -0.1, ...],  // Array of samples
  "sample_rate": 44100,
  "parameters": {
    "noise_reduction_amount": 0.8,
    "declicking_sensitivity": 0.5,
    "declipping_threshold": 0.95
  }
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "enhanced_audio": [0.08, 0.18, -0.09, ...],
    "processing_time_ms": 150,
    "improvements": {
      "noise_reduction_db": -12.5,
      "clicks_removed": 15,
      "clipping_restored": 8
    }
  }
}
```

---

### 5.2 Generate Music

**Endpoint**: `POST /audio/generate`

**Request Body**:
```json
{
  "content_type": "melody",
  "musical_context": {
    "key": "C major",
    "tempo": 120.0,
    "time_signature": "4/4",
    "chord_progression": ["C", "Am", "F", "G"],
    "length_bars": 8
  }
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "generated_audio": [0.1, 0.15, ...],
    "sample_rate": 44100,
    "duration_seconds": 16.0,
    "metadata": {
      "key": "C major",
      "scale": "major pentatonic",
      "notes_generated": 32
    }
  }
}
```

---

## 6. Metadata API

### 6.1 Extract Metadata

**Endpoint**: `POST /metadata/extract`

**Request Body**:
```json
{
  "audio_data": [...],
  "sample_rate": 44100,
  "deep_analysis": true
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "musical": {
      "tempo": 128.0,
      "key": "A minor",
      "time_signature": "4/4"
    },
    "technical": {
      "duration": 180.5,
      "sample_rate": 44100,
      "bit_depth": 24,
      "lufs": -14.2,
      "peak_db": -0.3,
      "dynamic_range": 8.5
    },
    "quality": {
      "overall_score": 0.82,
      "noise_floor_db": -65.0,
      "spectral_balance": "good"
    }
  }
}
```

---

## 7. System API

### 7.1 Get System Health

**Endpoint**: `GET /system/health`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "health_score": 92,
    "agents": {
      "live_effects_chain": "running",
      "live_looping": "running",
      "synchronization_clock": "running",
      "performance_automation": "running",
      "audio_enhancement": "running",
      "metadata_management": "running"
    },
    "resources": {
      "cpu_usage_percent": 45.2,
      "memory_usage_percent": 62.1,
      "message_bus_queue_depth": 5
    }
  }
}
```

---

### 7.2 Get Resource Metrics

**Endpoint**: `GET /system/metrics`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 62.1,
    "memory_usage_mb": 512.3,
    "message_bus": {
      "queue_depth": 5,
      "messages_per_second": 120,
      "average_latency_ms": 2.5
    },
    "timestamp": "2025-11-17T11:10:00Z"
  }
}
```

---

### 7.3 Get Agent Statistics

**Endpoint**: `GET /system/agents/{agent_name}/stats`

**Response**: `200 OK`
```json
{
  "status": "success",
  "data": {
    "agent_name": "live_effects_chain",
    "status": "running",
    "uptime_seconds": 3600,
    "messages_processed": 1523,
    "messages_published": 856,
    "errors": 0,
    "statistics": {
      "chains_active": 3,
      "effects_active": 12,
      "total_latency_ms": 35.6,
      "cpu_percent": 15.2
    }
  }
}
```

---

## WebSocket API

### Connection

**Endpoint**: `ws://localhost:8000/ws`

### Authentication

```javascript
// Send authentication token after connection
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token_here'
  }));
};
```

---

### Subscription Model

**Subscribe to Topics**:
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  topics: [
    'effects.parameter.change',
    'sync.clock.position',
    'loop.record.stopped',
    'automation.scene.triggered'
  ]
}));
```

**Unsubscribe**:
```javascript
ws.send(JSON.stringify({
  type: 'unsubscribe',
  topics: ['effects.parameter.change']
}));
```

---

### Event Messages

#### 1. Parameter Change Event

```json
{
  "type": "event",
  "topic": "effects.parameter.change",
  "timestamp": "2025-11-17T11:15:00.123Z",
  "data": {
    "chain_id": "chain_vocal_001",
    "effect_id": "effect_002",
    "parameter": "threshold",
    "value": -18.5,
    "source": "automation"
  }
}
```

#### 2. Clock Position Event

```json
{
  "type": "event",
  "topic": "sync.clock.position",
  "timestamp": "2025-11-17T11:15:01.500Z",
  "data": {
    "position_seconds": 65.5,
    "position_beats": 140.0,
    "position_bars": 35,
    "beat_in_bar": 1,
    "bpm": 128.0
  }
}
```

#### 3. Loop Recorded Event

```json
{
  "type": "event",
  "topic": "loop.record.stopped",
  "timestamp": "2025-11-17T11:15:05.000Z",
  "data": {
    "track_id": "loop_track_001",
    "track_name": "Drums",
    "length_samples": 211680,
    "length_beats": 4,
    "status": "playing"
  }
}
```

#### 4. Scene Triggered Event

```json
{
  "type": "event",
  "topic": "automation.scene.triggered",
  "timestamp": "2025-11-17T11:15:10.000Z",
  "data": {
    "scene_id": "scene_001",
    "scene_name": "Chorus Build",
    "transition_time": 2.0
  }
}
```

#### 5. Tempo Changed Event

```json
{
  "type": "event",
  "topic": "sync.clock.tempo",
  "timestamp": "2025-11-17T11:15:15.000Z",
  "data": {
    "bpm": 132.0,
    "time_signature": "4/4",
    "source": "tap_tempo"
  }
}
```

#### 6. System Health Event

```json
{
  "type": "event",
  "topic": "system.health",
  "timestamp": "2025-11-17T11:15:20.000Z",
  "data": {
    "health_score": 88,
    "cpu_usage_percent": 52.3,
    "memory_usage_percent": 65.4,
    "warnings": [
      "CPU usage approaching threshold"
    ]
  }
}
```

---

### Heartbeat

**Client → Server**:
```json
{
  "type": "ping"
}
```

**Server → Client**:
```json
{
  "type": "pong",
  "timestamp": "2025-11-17T11:15:25.000Z"
}
```

---

## User Interface Design

### Technology Stack

**Frontend**:
- React 18+ with TypeScript
- Redux Toolkit for state management
- Material-UI (MUI) or Ant Design for components
- Web Audio API for audio visualization
- Canvas/WebGL for waveforms and meters
- Socket.IO client for WebSocket

**Development**:
- Vite for build tooling
- ESLint + Prettier
- Jest + React Testing Library

---

### Application Layout

```
┌────────────────────────────────────────────────────────────────┐
│  MAAPS Control Center                        [?] [Settings] [X]│
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐   │
│ │  🎚️ Dashboard  |  🎛️ Effects  |  🔁 Looping  |  ⏱️ Sync  │   │
│ │                |  🎭 Automation  |  📊 Analytics          │   │
│ └──────────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│                  [Active View Content]                          │
│                                                                  │
│                                                                  │
├────────────────────────────────────────────────────────────────┤
│ Transport: [◀◀][▶][■][▶▶]  BPM: 128.0  Bar: 35.1  CPU: 45%   │
│ Status: All systems operational ●                              │
└────────────────────────────────────────────────────────────────┘
```

---

### 1. Dashboard View

**Purpose**: System overview, quick access, real-time monitoring

```
┌─────────────────────────────────────────────────────────────┐
│ System Status                                                │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│ │ Effects     │  │ Looping     │  │ Sync Clock  │          │
│ │ ● Running   │  │ ● Running   │  │ ● Running   │          │
│ │ 3 chains    │  │ 2 tracks    │  │ 128 BPM     │          │
│ │ 12 effects  │  │ 4 bars      │  │ Playing     │          │
│ └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                               │
│ Performance Metrics                                          │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ CPU Usage:    [████████████░░░░░░░░░░░] 45%          │   │
│ │ Memory:       [██████████░░░░░░░░░░░░░░] 62%          │   │
│ │ Latency:      2.5 ms (Target: <10ms)                  │   │
│ │ Messages/sec: 120                                      │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Active Sessions                                              │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Session 1: "Live Performance"         [Load] [Save]   │   │
│ │   - 3 effect chains, 2 loops, 5 scenes                │   │
│ │   - Created: 2025-11-17 10:30                         │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Quick Actions                                                │
│ [New Session] [Load Session] [Save Session] [Export]        │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. Effects Chain View

```
┌─────────────────────────────────────────────────────────────┐
│ Chain: [Vocal Chain ▼]                      [+ Add Chain]   │
├─────────────────────────────────────────────────────────────┤
│ Effect Chain Pipeline                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │  ┌──────────┐   ┌──────────┐   ┌──────────┐  [+]      │ │
│ │  │  Gate    │ → │Compressor│ → │    EQ    │           │ │
│ │  │  -40 dB  │   │  4:1     │   │  Bright  │           │ │
│ │  │  [BP]    │   │  [BP]    │   │  [BP]    │           │ │
│ │  └──────────┘   └──────────┘   └──────────┘           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ Selected Effect: Compressor                                  │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ┌───────────┐  ┌───────────┐  ┌───────────┐          │   │
│ │ │ Threshold │  │   Ratio   │  │  Attack   │          │   │
│ │ │   -18 dB  │  │   4.0:1   │  │   5 ms    │          │   │
│ │ │    ●──    │  │   ──●─    │  │  ●────    │          │   │
│ │ └───────────┘  └───────────┘  └───────────┘          │   │
│ │                                                        │   │
│ │ ┌───────────┐  ┌───────────┐  ┌───────────┐          │   │
│ │ │  Release  │  │   Knee    │  │  Makeup   │          │   │
│ │ │   50 ms   │  │   2.0 dB  │  │  Auto ☑   │          │   │
│ │ │   ───●─   │  │   ●───    │  │           │          │   │
│ │ └───────────┘  └───────────┘  └───────────┘          │   │
│ │                                                        │   │
│ │ Wet/Dry: [━━━━━━━━━━━━━━━━━━━●] 100%                 │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Meters:                                                      │
│ Input:  [████████████████░░] -6 dB                           │
│ GR:     [█████░░░░░░░░░░░░] -3 dB                           │
│ Output: [█████████████░░░░░] -9 dB                           │
│                                                               │
│ Presets: [Studio Vocal ▼]  [Save] [A/B]                     │
└─────────────────────────────────────────────────────────────┘
```

**Effect Library Sidebar**:
```
┌─────────────────────────┐
│ Effect Library          │
├─────────────────────────┤
│ 🔊 Dynamics             │
│  - Compressor           │
│  - Limiter              │
│  - Gate                 │
│  - Expander             │
│                         │
│ 🎛️ EQ                   │
│  - Parametric EQ        │
│  - Graphic EQ           │
│                         │
│ ⏰ Time-Based           │
│  - Reverb               │
│  - Delay                │
│  - Chorus               │
│  - Flanger              │
│                         │
│ 🌀 Modulation           │
│  - Phaser               │
│  - Tremolo              │
│  - Vibrato              │
│                         │
│ 🎸 Distortion           │
│  - Distortion           │
│  - Saturation           │
└─────────────────────────┘
```

---

### 3. Live Looping View

```
┌─────────────────────────────────────────────────────────────┐
│ Loop Tracks                                [+ Add Track]     │
├─────────────────────────────────────────────────────────────┤
│ Track 1: Drums        [●][▶][■]  Vol: [━━●━━] Pan: [━●━]   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│ │ 4 bars │ 128 BPM │ Synced  [⟲ Undo: 3] [⟳ Redo: 0]  │   │
│ └───────────────────────────────────────────────────────┘   │
│ [Overdub] [Replace] [Reverse] [Pitch ±] [Stretch] [Clear]  │
│                                                               │
│ Track 2: Bass         [●][▶][■]  Vol: [━━●━━] Pan: [━●━]   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│ │ 2 bars │ 128 BPM │ Synced  [⟲ Undo: 1] [⟳ Redo: 2]  │   │
│ └───────────────────────────────────────────────────────┘   │
│ [Overdub] [Replace] [Reverse] [Pitch ±] [Stretch] [Clear]  │
│                                                               │
│ Track 3: Empty        [●][▶][■]  Vol: [━━●━━] Pan: [━●━]   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Click [●] to start recording...                       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Global Controls                                              │
│ Sync to Clock: [☑]  Quantize: [☑]  Master: [━━━━━●━━━━]   │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Sync & Clock View

```
┌─────────────────────────────────────────────────────────────┐
│ Transport Control                                            │
│ ┌───────────────────────────────────────────────────────┐   │
│ │       [◀◀]      [▶]      [■]      [▶▶]               │   │
│ │     Rewind     Play     Stop    Forward               │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Tempo & Time                                                 │
│ ┌───────────────────────────────────────────────────────┐   │
│ │  BPM:  [  128.0  ]  [-] [+]  [Tap Tempo]             │   │
│ │  Time Signature: [4] / [4]                            │   │
│ │                                                        │   │
│ │  Position:                                             │   │
│ │    Bars:  35  |  Beats: 1.0  |  Time: 00:01:05.250   │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Timeline Visualization                                       │
│ ┌───────────────────────────────────────────────────────┐   │
│ │  |----|----|----|----|----|----|----|----|----|----|  │   │
│ │  31   32   33   34   35   36   37   38   39   40     │   │
│ │                      ▲ Playhead                       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Synchronization                                              │
│ ┌───────────────────────────────────────────────────────┐   │
│ │  MIDI Clock:     [☐] Enable  Port: [MIDI OUT 1 ▼]    │   │
│ │  Ableton Link:   [☐] Enable  Peers: 0                │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Performance Automation View

```
┌─────────────────────────────────────────────────────────────┐
│ ┌─ Scenes ─────┐  ┌─ Macros ────┐  ┌─ Cues ──────┐        │
│ │ [1] Intro    │  │ Energy      │  │ Drop 2:30   │        │
│ │ [2] Verse    │  │ [━━━━━●━━━] │  │ ● 00:02:30  │        │
│ │►[3] Chorus   │  │  Value: 0.5 │  │ [Fire Now]  │        │
│ │ [4] Breakdown│  │             │  │             │        │
│ │ [5] Outro    │  │ Brightness  │  │ Build 1:45  │        │
│ │ [+ New]      │  │ [━━━●━━━━━] │  │ ○ 00:01:45  │        │
│ │              │  │  Value: 0.3 │  │ [Fire Now]  │        │
│ └──────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│ Automation Recording                                        │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Parameter: effects.filter.cutoff                      │  │
│ │ Recording: ● [■ Stop]  Playback: [▶ Enable]          │  │
│ │                                                        │  │
│ │ Timeline:                                              │  │
│ │ ┌───────────────────────────────────────────────────┐ │  │
│ │ │     ●───────●────────●──────────●                 │ │  │
│ │ │   0.0     1.0      2.0        3.0      (bars)     │ │  │
│ │ │                                                    │ │  │
│ │ │  Value                                             │ │  │
│ │ │  20kHz ┤                 ●─────                   │ │  │
│ │ │        │           ●────╯                          │ │  │
│ │ │  10kHz ┤      ●───╯                               │ │  │
│ │ │        │ ●───╯                                     │ │  │
│ │ │   5kHz ┼──────────────────────────────────        │ │  │
│ │ └───────────────────────────────────────────────────┘ │  │
│ │                                                        │  │
│ │ Curve: [Exponential ▼]  [Clear] [Smooth]             │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### 6. Analytics View (Bonus)

```
┌─────────────────────────────────────────────────────────────┐
│ System Analytics                       [Last Hour ▼]        │
├─────────────────────────────────────────────────────────────┤
│ Performance Trends                                           │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ CPU Usage (%)                                         │   │
│ │ 100┤                                                  │   │
│ │  75┤           ╭──╮                                   │   │
│ │  50┤     ╭─────╯  ╰────╮                             │   │
│ │  25┤─────╯            ╰──────                        │   │
│ │   0└─────────────────────────────────────────────    │   │
│ │     10:00   10:15   10:30   10:45   11:00           │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Message Bus Activity                                         │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Messages/sec                                          │   │
│ │ 200┤              ╭╮                                  │   │
│ │ 150┤         ╭────╯╰─╮                               │   │
│ │ 100┤    ╭────╯       ╰──╮                            │   │
│ │  50┤────╯               ╰────                        │   │
│ │   0└─────────────────────────────────────────────    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Agent Statistics                                             │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Agent                  Messages  Errors  CPU%   Mem%  │   │
│ │ ───────────────────────────────────────────────────   │   │
│ │ Effects Chain          1,523     0       15.2   12.5  │   │
│ │ Looping                  856     0        8.1    9.2  │   │
│ │ Sync Clock               342     0        2.5    1.8  │   │
│ │ Automation               689     0        5.3    4.1  │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Schemas

### TypeScript Interfaces

```typescript
// Effect Chain Types
interface EffectChain {
  chain_id: string;
  chain_name: string;
  bypass: boolean;
  effects: Effect[];
  total_latency_ms: number;
}

interface Effect {
  effect_id: string;
  type: EffectType;
  bypass: boolean;
  wet_dry: number;
  parameters: Record<string, number>;
  latency_ms: number;
}

type EffectType =
  | 'gate' | 'compressor' | 'limiter' | 'expander'
  | 'eq_parametric' | 'eq_graphic'
  | 'reverb' | 'delay' | 'chorus' | 'flanger'
  | 'phaser' | 'tremolo' | 'vibrato'
  | 'distortion' | 'saturation';

// Loop Track Types
interface LoopTrack {
  track_id: string;
  track_name: string;
  status: 'empty' | 'recording' | 'playing' | 'paused';
  length_beats: number;
  length_samples: number;
  volume: number;
  pan: number;
  sync_to_tempo: boolean;
  undo_available: number;
  redo_available: number;
}

// Sync Clock Types
interface ClockStatus {
  bpm: number;
  time_signature: string;
  playing: boolean;
  position: {
    seconds: number;
    beats: number;
    bars: number;
    beat_in_bar: number;
  };
  midi_clock: {
    enabled: boolean;
    port: string | null;
  };
  ableton_link: {
    enabled: boolean;
    peers: number;
  };
}

// Automation Types
interface AutomationScene {
  scene_id: string;
  scene_name: string;
  parameter_snapshots: Record<string, number>;
  transition_time: number;
  transition_curves: Record<string, CurveType>;
}

type CurveType = 'linear' | 'exponential' | 'logarithmic' | 'step' | 'bezier';

interface Macro {
  macro_id: string;
  macro_name: string;
  value: number;
  target_parameters: MacroTarget[];
}

interface MacroTarget {
  param: string;
  min: number;
  max: number;
  curve: CurveType;
}

interface PerformanceCue {
  cue_id: string;
  cue_name: string;
  timecode: string;
  actions: CueAction[];
}

interface CueAction {
  action_type: 'scene_change' | 'parameter_change' | 'macro_change';
  parameters: Record<string, any>;
}
```

---

## Authentication & Security

### JWT Authentication

**Login**:
```
POST /auth/login
{
  "username": "user",
  "password": "password"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

**Protected Endpoints**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/effects/chains")
@limiter.limit("10/minute")
async def create_chain(...):
    ...
```

---

## Implementation Guide

### Backend Implementation (FastAPI)

#### 1. Project Structure

```
api/
├── main.py                 # FastAPI app
├── dependencies.py         # Shared dependencies
├── auth.py                 # Authentication
├── websocket.py            # WebSocket manager
├── message_bus_adapter.py  # Message bus integration
│
├── routers/
│   ├── __init__.py
│   ├── effects.py          # Effects chain endpoints
│   ├── looping.py          # Looping endpoints
│   ├── sync.py             # Sync/clock endpoints
│   ├── automation.py       # Automation endpoints
│   ├── audio.py            # Audio processing endpoints
│   ├── metadata.py         # Metadata endpoints
│   └── system.py           # System endpoints
│
├── schemas/
│   ├── __init__.py
│   ├── effects.py          # Pydantic models
│   ├── looping.py
│   ├── sync.py
│   ├── automation.py
│   └── common.py
│
└── utils/
    ├── __init__.py
    └── response.py         # Response formatters
```

#### 2. Sample Router Implementation

```python
# api/routers/effects.py
from fastapi import APIRouter, HTTPException, Depends
from api.schemas.effects import CreateChainRequest, EffectChainResponse
from api.message_bus_adapter import get_message_bus_adapter
from api.utils.response import success_response, error_response

router = APIRouter()

@router.post("/chains", response_model=EffectChainResponse, status_code=201)
async def create_effect_chain(
    request: CreateChainRequest,
    adapter = Depends(get_message_bus_adapter)
):
    """Create a new effect chain"""
    try:
        # Publish to message bus
        response = await adapter.request(
            "effects.chain.create",
            {
                "chain_name": request.chain_name,
                "effects": [e.dict() for e in request.effects]
            },
            timeout=5.0
        )

        return success_response(response)

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 3. WebSocket Manager

```python
# api/websocket.py
from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of client IDs

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        # Remove from all subscriptions
        for topic_subs in self.subscriptions.values():
            topic_subs.discard(client_id)

    async def subscribe(self, client_id: str, topics: list):
        for topic in topics:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)

    async def broadcast_event(self, topic: str, data: dict):
        """Broadcast event to all subscribers"""
        if topic in self.subscriptions:
            message = {
                "type": "event",
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }

            # Send to all subscribers
            for client_id in self.subscriptions[topic]:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_json(message)
                    except:
                        self.disconnect(client_id)

websocket_manager = WebSocketManager()
```

---

### Frontend Implementation (React)

#### 1. Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts           # API client
│   │   ├── websocket.ts        # WebSocket client
│   │   └── endpoints/
│   │       ├── effects.ts
│   │       ├── looping.ts
│   │       ├── sync.ts
│   │       └── automation.ts
│   │
│   ├── components/
│   │   ├── Dashboard/
│   │   ├── Effects/
│   │   ├── Looping/
│   │   ├── Sync/
│   │   ├── Automation/
│   │   └── Common/
│   │       ├── Knob.tsx
│   │       ├── Slider.tsx
│   │       ├── VUMeter.tsx
│   │       └── Waveform.tsx
│   │
│   ├── store/
│   │   ├── index.ts            # Redux store
│   │   ├── slices/
│   │   │   ├── effects.ts
│   │   │   ├── looping.ts
│   │   │   ├── sync.ts
│   │   │   └── automation.ts
│   │   └── middleware/
│   │       └── websocket.ts    # WebSocket middleware
│   │
│   ├── hooks/
│   │   ├── useEffects.ts
│   │   ├── useLooping.ts
│   │   ├── useSync.ts
│   │   └── useAutomation.ts
│   │
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   │
│   └── App.tsx
│
└── package.json
```

#### 2. API Client

```typescript
// src/api/client.ts
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// src/api/endpoints/effects.ts
import { apiClient } from '../client';
import { EffectChain, CreateChainRequest } from '../../types';

export const effectsAPI = {
  createChain: async (data: CreateChainRequest): Promise<EffectChain> => {
    const response = await apiClient.post('/effects/chains', data);
    return response.data.data;
  },

  getChains: async (): Promise<EffectChain[]> => {
    const response = await apiClient.get('/effects/chains');
    return response.data.data.chains;
  },

  updateParameter: async (
    chainId: string,
    effectId: string,
    parameters: Record<string, number>
  ) => {
    const response = await apiClient.patch(
      `/effects/chains/${chainId}/effects/${effectId}/parameters`,
      { parameters }
    );
    return response.data.data;
  },
};
```

#### 3. WebSocket Client

```typescript
// src/api/websocket.ts
import { store } from '../store';
import { updateParameter } from '../store/slices/effects';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws');

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      // Authenticate
      const token = localStorage.getItem('auth_token');
      this.send({ type: 'auth', token });

      // Subscribe to topics
      this.send({
        type: 'subscribe',
        topics: [
          'effects.parameter.change',
          'sync.clock.position',
          'loop.record.stopped',
          'automation.scene.triggered'
        ]
      });
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      setTimeout(() => this.connect(), this.reconnectInterval);
    };
  }

  private handleMessage(message: any) {
    switch (message.topic) {
      case 'effects.parameter.change':
        store.dispatch(updateParameter(message.data));
        break;
      case 'sync.clock.position':
        // Update clock position in store
        break;
      // ... handle other messages
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export const wsClient = new WebSocketClient();
```

#### 4. Redux Store

```typescript
// src/store/slices/effects.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { effectsAPI } from '../../api/endpoints/effects';
import { EffectChain } from '../../types';

interface EffectsState {
  chains: EffectChain[];
  loading: boolean;
  error: string | null;
}

const initialState: EffectsState = {
  chains: [],
  loading: false,
  error: null,
};

export const fetchChains = createAsyncThunk(
  'effects/fetchChains',
  async () => {
    return await effectsAPI.getChains();
  }
);

const effectsSlice = createSlice({
  name: 'effects',
  initialState,
  reducers: {
    updateParameter: (state, action) => {
      const { chain_id, effect_id, parameter, value } = action.payload;
      const chain = state.chains.find(c => c.chain_id === chain_id);
      if (chain) {
        const effect = chain.effects.find(e => e.effect_id === effect_id);
        if (effect) {
          effect.parameters[parameter] = value;
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChains.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchChains.fulfilled, (state, action) => {
        state.loading = false;
        state.chains = action.payload;
      })
      .addCase(fetchChains.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch chains';
      });
  },
});

export const { updateParameter } = effectsSlice.actions;
export default effectsSlice.reducer;
```

---

## Deployment

### Backend Deployment

```bash
# Install dependencies
pip install fastapi uvicorn python-jose[cryptography] slowapi

# Run development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment

```bash
# Install dependencies
npm install

# Development
npm run dev

# Production build
npm run build
npm run preview
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  maaps-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/maaps
    depends_on:
      - db

  maaps-frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - maaps-backend

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: maaps
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## Conclusion

This specification provides a complete API and UI design for MAAPS Phases 1-3, including:

✅ **REST API**: 50+ endpoints for all agent operations
✅ **WebSocket API**: Real-time event streaming
✅ **UI Design**: 6 main views with detailed layouts
✅ **TypeScript Types**: Full type safety
✅ **Implementation Guide**: Backend (FastAPI) and Frontend (React)
✅ **Security**: JWT authentication, CORS, rate limiting
✅ **Deployment**: Docker, production-ready configuration

**Next Steps**:
1. Implement FastAPI backend with message bus adapter
2. Build React frontend with WebSocket integration
3. Create comprehensive API tests
4. Develop UI component library
5. Deploy to staging environment

---

**Document Version**: 1.0
**Date**: 2025-11-17
**Status**: Complete Specification
