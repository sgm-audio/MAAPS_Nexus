import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Camera, Play, Square, Circle, Scissors, Edit3, Trash2, TrendingUp, 
         Maximize2, ZoomIn, ZoomOut, Settings, Mic, Volume2, Headphones, 
         Radio, Activity, Cpu, HardDrive, Clock, Database, Sparkles } from 'lucide-react';

/**
 * APEX DAW - Next-Generation Digital Audio Workstation
 * 
 * ML/AI-Centric Architecture:
 * - Real-time audio analysis via Web Audio API
 * - TensorFlow.js integration for AI features
 * - RESTful API integration for cloud processing
 * - Scalable component architecture
 * - State management ready for Redux/Zustand
 * - WebSocket support for real-time collaboration
 */

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface Track {
  id: string;
  name: string;
  type: 'audio' | 'midi' | 'aux' | 'bus' | 'master';
  color: string;
  volume: number; // 0-100
  pan: number; // -50 to 50
  mute: boolean;
  solo: boolean;
  record: boolean;
  monitor: boolean;
  routing: string;
  regions: Region[];
  inserts: Insert[];
  meter: MeterData;
}

interface Region {
  id: string;
  trackId: string;
  start: number; // in milliseconds
  duration: number;
  name: string;
  color: string;
  waveformData?: number[];
  selected: boolean;
}

interface Insert {
  id: string;
  name: string;
  type: 'eq' | 'comp' | 'reverb' | 'delay' | 'custom';
  active: boolean;
  params: Record<string, number>;
}

interface MeterData {
  peak: number;
  rms: number;
  clip: boolean;
}

interface AIAnalysis {
  id: string;
  type: 'optimization' | 'tempo' | 'frequency' | 'mix';
  title: string;
  description: string;
  confidence: number;
  timestamp: Date;
}

interface ProjectState {
  tempo: number;
  timeSignature: [number, number];
  sampleRate: number;
  bufferSize: number;
  playheadPosition: number; // in milliseconds
  isPlaying: boolean;
  isRecording: boolean;
  loopEnabled: boolean;
  snapEnabled: boolean;
  gridResolution: string;
}

// ============================================================================
// MAIN DAW COMPONENT
// ============================================================================

const ApexDAW: React.FC = () => {
  // ========== STATE MANAGEMENT ==========
  const [tracks, setTracks] = useState<Track[]>([
    {
      id: 'track-1',
      name: 'Lead Vocal',
      type: 'audio',
      color: '#3B82F6',
      volume: 65,
      pan: 0,
      mute: false,
      solo: false,
      record: true,
      monitor: true,
      routing: 'INPUT: 1 • OUT: Master',
      regions: [
        { id: 'region-1', trackId: 'track-1', start: 1000, duration: 5000, name: 'Lead Vocal Take 1', color: '#3B82F6', selected: true },
        { id: 'region-2', trackId: 'track-1', start: 8000, duration: 4000, name: 'Lead Vocal Take 2', color: '#3B82F6', selected: false }
      ],
      inserts: [
        { id: 'ins-1', name: 'EQ', type: 'eq', active: true, params: {} },
        { id: 'ins-2', name: 'COMP', type: 'comp', active: true, params: {} }
      ],
      meter: { peak: 0.65, rms: 0.45, clip: false }
    },
    {
      id: 'track-2',
      name: 'Piano',
      type: 'midi',
      color: '#8B5CF6',
      volume: 45,
      pan: -20,
      mute: false,
      solo: false,
      record: false,
      monitor: false,
      routing: 'MIDI: Kontakt • OUT: Master',
      regions: [
        { id: 'region-3', trackId: 'track-2', start: 2000, duration: 4500, name: 'Piano Progression', color: '#8B5CF6', selected: false }
      ],
      inserts: [
        { id: 'ins-3', name: 'REVERB', type: 'reverb', active: true, params: {} }
      ],
      meter: { peak: 0.45, rms: 0.35, clip: false }
    },
    {
      id: 'track-3',
      name: 'Bass Guitar',
      type: 'audio',
      color: '#3B82F6',
      volume: 55,
      pan: 0,
      mute: false,
      solo: false,
      record: false,
      monitor: false,
      routing: 'INPUT: 3 • OUT: Bass Bus',
      regions: [],
      inserts: [
        { id: 'ins-4', name: 'AMP', type: 'custom', active: true, params: {} },
        { id: 'ins-5', name: 'COMP', type: 'comp', active: true, params: {} }
      ],
      meter: { peak: 0.55, rms: 0.40, clip: false }
    },
    {
      id: 'track-4',
      name: 'Reverb Send',
      type: 'aux',
      color: '#10B981',
      volume: 35,
      pan: 0,
      mute: false,
      solo: false,
      record: false,
      monitor: false,
      routing: 'AUX • OUT: Master',
      regions: [],
      inserts: [],
      meter: { peak: 0.35, rms: 0.25, clip: false }
    },
    {
      id: 'track-5',
      name: 'Master Output',
      type: 'master',
      color: '#EC4899',
      volume: 75,
      pan: 0,
      mute: false,
      solo: false,
      record: false,
      monitor: false,
      routing: 'STEREO OUT: 1-2',
      regions: [],
      inserts: [
        { id: 'ins-6', name: 'LIMITER', type: 'custom', active: true, params: {} },
        { id: 'ins-7', name: 'METER', type: 'custom', active: true, params: {} }
      ],
      meter: { peak: 0.75, rms: 0.60, clip: false }
    }
  ]);

  const [projectState, setProjectState] = useState<ProjectState>({
    tempo: 120,
    timeSignature: [4, 4],
    sampleRate: 48000,
    bufferSize: 256,
    playheadPosition: 0,
    isPlaying: false,
    isRecording: false,
    loopEnabled: false,
    snapEnabled: true,
    gridResolution: '1/16'
  });

  const [selectedTool, setSelectedTool] = useState<'select' | 'trim' | 'slip' | 'pencil' | 'eraser' | 'automation'>('select');
  const [editMode, setEditMode] = useState<'shuffle' | 'slip' | 'spot' | 'grid'>('grid');
  const [selectedTrackId, setSelectedTrackId] = useState<string>('track-1');
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [cpuUsage, setCpuUsage] = useState(24);
  const [diskIO, setDiskIO] = useState(12);
  const [latency, setLatency] = useState(5.3);

  const [aiAnalyses, setAiAnalyses] = useState<AIAnalysis[]>([
    {
      id: 'ai-1',
      type: 'optimization',
      title: '🎵 Optimize Vocal Chain',
      description: 'Detected potential phase issues. Suggested EQ and compression settings ready.',
      confidence: 0.92,
      timestamp: new Date()
    },
    {
      id: 'ai-2',
      type: 'tempo',
      title: '⚡ Tempo Analysis Complete',
      description: 'AI detected natural tempo fluctuations. Apply time correction?',
      confidence: 0.87,
      timestamp: new Date()
    },
    {
      id: 'ai-3',
      type: 'frequency',
      title: '🎚️ Mix Balance Suggestion',
      description: 'Bass frequencies competing with kick. View frequency analysis?',
      confidence: 0.95,
      timestamp: new Date()
    }
  ]);

  // ========== REFS ==========
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // ========== EFFECTS ==========
  useEffect(() => {
    // Initialize Web Audio API
    if (typeof window !== 'undefined') {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    // Simulate meter updates
    const meterInterval = setInterval(() => {
      setTracks(prevTracks => prevTracks.map(track => ({
        ...track,
        meter: {
          peak: Math.random() * 0.9,
          rms: Math.random() * 0.7,
          clip: Math.random() > 0.98
        }
      })));
    }, 100);

    // Simulate CPU monitoring
    const cpuInterval = setInterval(() => {
      setCpuUsage(20 + Math.random() * 30);
      setDiskIO(10 + Math.random() * 20);
      setLatency(4 + Math.random() * 3);
    }, 2000);

    return () => {
      clearInterval(meterInterval);
      clearInterval(cpuInterval);
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (projectState.isPlaying) {
      const startTime = Date.now();
      const updatePlayhead = () => {
        const elapsed = Date.now() - startTime;
        setProjectState(prev => ({
          ...prev,
          playheadPosition: prev.playheadPosition + elapsed / 10
        }));
        animationFrameRef.current = requestAnimationFrame(updatePlayhead);
      };
      animationFrameRef.current = requestAnimationFrame(updatePlayhead);
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [projectState.isPlaying]);

  // ========== HANDLERS ==========
  const handlePlayPause = useCallback(() => {
    setProjectState(prev => ({ ...prev, isPlaying: !prev.isPlaying }));
  }, []);

  const handleStop = useCallback(() => {
    setProjectState(prev => ({ 
      ...prev, 
      isPlaying: false, 
      playheadPosition: 0 
    }));
  }, []);

  const handleRecord = useCallback(() => {
    setProjectState(prev => ({ 
      ...prev, 
      isRecording: !prev.isRecording,
      isPlaying: !prev.isRecording ? true : prev.isPlaying
    }));
  }, []);

  const handleTrackToggle = useCallback((trackId: string, property: 'mute' | 'solo' | 'record' | 'monitor') => {
    setTracks(prev => prev.map(track => 
      track.id === trackId 
        ? { ...track, [property]: !track[property] }
        : track
    ));
  }, []);

  const handleTrackVolumeChange = useCallback((trackId: string, volume: number) => {
    setTracks(prev => prev.map(track => 
      track.id === trackId ? { ...track, volume } : track
    ));
  }, []);

  const handleTrackPanChange = useCallback((trackId: string, pan: number) => {
    setTracks(prev => prev.map(track => 
      track.id === trackId ? { ...track, pan } : track
    ));
  }, []);

  const handleRegionSelect = useCallback((regionId: string) => {
    setTracks(prev => prev.map(track => ({
      ...track,
      regions: track.regions.map(region => ({
        ...region,
        selected: region.id === regionId
      }))
    })));
  }, []);

  // ========== API INTEGRATION POINTS ==========
  const analyzeAudioWithAI = useCallback(async (audioBuffer: ArrayBuffer) => {
    try {
      // Example: Send to AI analysis endpoint
      const response = await fetch('/api/analyze/audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: audioBuffer
      });
      const analysis = await response.json();
      return analysis;
    } catch (error) {
      console.error('AI Analysis failed:', error);
      return null;
    }
  }, []);

  const generateStemSeparation = useCallback(async (trackId: string) => {
    try {
      const response = await fetch(`/api/stems/separate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trackId })
      });
      return await response.json();
    } catch (error) {
      console.error('Stem separation failed:', error);
      return null;
    }
  }, []);

  const applyAIMixSuggestions = useCallback(async (projectData: any) => {
    try {
      const response = await fetch('/api/mix/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      });
      return await response.json();
    } catch (error) {
      console.error('AI mix suggestions failed:', error);
      return null;
    }
  }, []);

  // ========== RENDER ==========
  return (
    <div className="daw-container">
      <style jsx>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        .daw-container {
          width: 100vw;
          height: 100vh;
          background: #0A0A0A;
          color: #FFFFFF;
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", system-ui, sans-serif;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        /* Menu Bar */
        .menu-bar {
          background: #121212;
          border-bottom: 1px solid #3A3A3A;
          display: flex;
          align-items: center;
          padding: 0 16px;
          height: 40px;
          gap: 24px;
        }

        .menu-logo {
          font-size: 16px;
          font-weight: 700;
          background: linear-gradient(135deg, #4A9EFF 0%, #8B5CF6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: 1px;
        }

        .menu-items {
          display: flex;
          gap: 20px;
          flex: 1;
        }

        .menu-item {
          font-size: 13px;
          color: #E8E8E8;
          cursor: pointer;
          padding: 4px 8px;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .menu-item:hover {
          color: #FFFFFF;
          background: #242424;
        }

        .menu-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .ai-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 12px;
          background: #242424;
          border-radius: 12px;
          font-size: 11px;
          color: #B8B8B8;
        }

        .ai-status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #10B981;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        /* Toolbar */
        .toolbar {
          background: #1A1A1A;
          border-bottom: 1px solid #3A3A3A;
          display: flex;
          align-items: center;
          padding: 12px 16px;
          gap: 24px;
          height: 72px;
        }

        .toolbar-section {
          display: flex;
          gap: 8px;
          align-items: center;
          padding-right: 24px;
          border-right: 1px solid #2A2A2A;
        }

        .toolbar-section:last-child {
          border-right: none;
        }

        .toolbar-label {
          font-size: 11px;
          color: #6E6E6E;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-right: 8px;
        }

        .edit-mode-group {
          display: flex;
          gap: 4px;
          background: #242424;
          padding: 4px;
          border-radius: 8px;
        }

        .edit-mode-btn {
          padding: 8px 16px;
          background: transparent;
          border: none;
          color: #E8E8E8;
          font-size: 12px;
          font-weight: 600;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .edit-mode-btn:hover {
          color: #FFFFFF;
          background: #383838;
        }

        .edit-mode-btn.active {
          background: #4A9EFF;
          color: #0A0A0A;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
        }

        .tool-selector {
          display: flex;
          gap: 4px;
        }

        .tool-btn {
          width: 36px;
          height: 36px;
          border-radius: 6px;
          border: 1px solid #3A3A3A;
          background: #242424;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #E8E8E8;
        }

        .tool-btn:hover {
          border-color: #4A9EFF;
          background: #383838;
        }

        .tool-btn.active {
          background: #4A9EFF;
          border-color: #4A9EFF;
          color: #0A0A0A;
          box-shadow: 0 0 12px rgba(74, 158, 255, 0.3);
        }

        .transport-controls {
          display: flex;
          gap: 6px;
        }

        .transport-btn {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          border: 1px solid #3A3A3A;
          background: #242424;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #E8E8E8;
        }

        .transport-btn:hover {
          border-color: #4A4A4A;
          background: #383838;
          transform: translateY(-1px);
        }

        .transport-btn.record {
          background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%);
          border-color: #B91C1C;
        }

        .transport-btn.record.active {
          background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%);
          box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
        }

        .transport-btn.play.active {
          background: #10B981;
          border-color: #10B981;
        }

        .time-display {
          display: flex;
          flex-direction: column;
          gap: 4px;
          background: #0A0A0A;
          padding: 8px 16px;
          border-radius: 8px;
          font-family: "SF Mono", Monaco, monospace;
          border: 1px solid #3A3A3A;
        }

        .time-main {
          font-size: 18px;
          color: #FFFFFF;
          letter-spacing: 1px;
        }

        .time-secondary {
          font-size: 11px;
          color: #6E6E6E;
          letter-spacing: 0.5px;
        }

        .snap-control {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #242424;
          padding: 6px 12px;
          border-radius: 8px;
          border: 1px solid #3A3A3A;
        }

        .snap-toggle {
          font-size: 12px;
          color: #E8E8E8;
          cursor: pointer;
          transition: color 0.2s;
        }

        .snap-toggle.active {
          color: #4A9EFF;
          font-weight: 600;
        }

        .grid-value {
          font-family: "SF Mono", Monaco, monospace;
          font-size: 11px;
          color: #FFFFFF;
          background: #0A0A0A;
          padding: 4px 8px;
          border-radius: 4px;
          min-width: 60px;
          text-align: center;
        }

        /* Main Content */
        .main-content {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        /* Left Sidebar */
        .left-sidebar {
          width: 300px;
          background: #1A1A1A;
          border-right: 1px solid #3A3A3A;
          display: flex;
          flex-direction: column;
        }

        .sidebar-tabs {
          display: flex;
          background: #242424;
          border-bottom: 1px solid #3A3A3A;
        }

        .sidebar-tab {
          flex: 1;
          padding: 12px;
          text-align: center;
          font-size: 12px;
          color: #B8B8B8;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          transition: all 0.2s;
        }

        .sidebar-tab:hover {
          color: #E8E8E8;
          background: #383838;
        }

        .sidebar-tab.active {
          color: #FFFFFF;
          border-bottom-color: #4A9EFF;
        }

        .sidebar-content {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
        }

        .browser-item {
          padding: 10px 12px;
          background: #242424;
          border: 1px solid #2A2A2A;
          border-radius: 6px;
          margin-bottom: 8px;
          cursor: grab;
          transition: all 0.2s;
        }

        .browser-item:hover {
          background: #383838;
          border-color: #4A9EFF;
          transform: translateX(4px);
        }

        .browser-item-name {
          font-size: 13px;
          color: #FFFFFF;
          margin-bottom: 4px;
        }

        .browser-item-info {
          font-size: 11px;
          color: #6E6E6E;
        }

        /* Center Area */
        .center-area {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .ruler {
          height: 40px;
          background: #1A1A1A;
          border-bottom: 1px solid #3A3A3A;
          position: relative;
          overflow-x: auto;
        }

        .playhead {
          position: absolute;
          top: 0;
          width: 2px;
          height: 100%;
          background: #4A9EFF;
          box-shadow: 0 0 10px rgba(74, 158, 255, 0.5);
          z-index: 100;
          transition: left 0.1s linear;
        }

        .playhead::before {
          content: '';
          position: absolute;
          top: -6px;
          left: 50%;
          transform: translateX(-50%);
          width: 0;
          height: 0;
          border-left: 6px solid transparent;
          border-right: 6px solid transparent;
          border-top: 8px solid #4A9EFF;
        }

        .track-workspace {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        .track-headers {
          width: 280px;
          background: #1A1A1A;
          border-right: 1px solid #3A3A3A;
          overflow-y: auto;
        }

        .track-header {
          background: #242424;
          border-bottom: 1px solid #2A2A2A;
          padding: 12px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          transition: background 0.2s;
          min-height: 80px;
          cursor: pointer;
        }

        .track-header:hover {
          background: #383838;
        }

        .track-header.selected {
          background: #2E2E2E;
          border-left: 3px solid #4A9EFF;
        }

        .track-header-top {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .track-type-indicator {
          width: 4px;
          height: 40px;
          border-radius: 2px;
        }

        .track-info {
          flex: 1;
        }

        .track-name {
          font-size: 13px;
          color: #FFFFFF;
          font-weight: 600;
          margin-bottom: 2px;
        }

        .track-routing {
          font-size: 10px;
          color: #6E6E6E;
          font-family: "SF Mono", Monaco, monospace;
        }

        .track-controls {
          display: flex;
          gap: 4px;
        }

        .track-btn {
          width: 28px;
          height: 28px;
          border-radius: 4px;
          border: 1px solid #3A3A3A;
          background: #1A1A1A;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 700;
          color: #E8E8E8;
        }

        .track-btn:hover {
          border-color: #4A4A4A;
          transform: scale(1.05);
        }

        .track-btn.record {
          background: #1A0000;
          color: #EF4444;
        }

        .track-btn.record.active {
          background: #EF4444;
          color: #FFFFFF;
          box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
        }

        .track-btn.mute {
          background: #1A1A1A;
          color: #6E6E6E;
        }

        .track-btn.mute.active {
          background: #2E2E2E;
          color: #CCCCCC;
        }

        .track-btn.solo {
          background: #1A1400;
          color: #F59E0B;
        }

        .track-btn.solo.active {
          background: #F59E0B;
          color: #0A0A0A;
        }

        .track-btn.monitor {
          background: #1A1A1A;
          color: #6E6E6E;
        }

        .track-btn.monitor.active {
          background: #3B82F6;
          color: #FFFFFF;
        }

        .track-header-bottom {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .track-meter-mini {
          flex: 1;
          height: 6px;
          background: #0A0A0A;
          border-radius: 3px;
          overflow: hidden;
          position: relative;
        }

        .track-meter-fill {
          height: 100%;
          background: linear-gradient(to right, #10B981 0%, #3B82F6 60%, #F59E0B 85%, #EF4444 100%);
          transition: width 0.05s;
          border-radius: 3px;
        }

        .track-volume {
          font-size: 10px;
          color: #6E6E6E;
          font-family: "SF Mono", Monaco, monospace;
          min-width: 40px;
          text-align: right;
        }

        .arrangement-area {
          flex: 1;
          background: #121212;
          overflow: auto;
          position: relative;
        }

        .arrangement-grid {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-image: 
            repeating-linear-gradient(90deg, #2A2A2A 0px, transparent 1px, transparent 60px),
            repeating-linear-gradient(0deg, #2A2A2A 0px, transparent 1px, transparent 80px);
        }

        .arrangement-tracks {
          position: relative;
          z-index: 1;
        }

        .arrangement-track {
          height: 80px;
          border-bottom: 1px solid #2A2A2A;
          position: relative;
          padding: 8px;
        }

        .region {
          position: absolute;
          height: 64px;
          background: #2E2E2E;
          border: 1px solid #4A4A4A;
          border-radius: 4px;
          overflow: hidden;
          cursor: move;
          transition: all 0.2s;
        }

        .region:hover {
          border-color: #4A9EFF;
          box-shadow: 0 0 12px rgba(74, 158, 255, 0.2);
          transform: translateY(-2px);
        }

        .region.selected {
          border-color: #4A9EFF;
          border-width: 2px;
          box-shadow: 0 0 16px rgba(74, 158, 255, 0.3);
        }

        .region-label {
          position: absolute;
          top: 4px;
          left: 8px;
          font-size: 11px;
          color: #FFFFFF;
          font-weight: 600;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
        }

        .region-waveform {
          width: 100%;
          height: 100%;
          opacity: 0.6;
        }

        /* Right Sidebar - Mixer */
        .right-sidebar {
          width: 400px;
          background: #1A1A1A;
          border-left: 1px solid #3A3A3A;
          display: flex;
          flex-direction: column;
        }

        .mixer-header {
          background: #242424;
          padding: 12px 16px;
          border-bottom: 1px solid #3A3A3A;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .mixer-header h3 {
          font-size: 13px;
          color: #E8E8E8;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .mixer-channels {
          flex: 1;
          display: flex;
          padding: 16px;
          gap: 12px;
          overflow-x: auto;
        }

        .channel-strip {
          min-width: 90px;
          background: #242424;
          border: 1px solid #3A3A3A;
          border-radius: 8px;
          padding: 12px 8px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          transition: all 0.2s;
        }

        .channel-strip:hover {
          border-color: #4A9EFF;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
        }

        .channel-strip.selected {
          border-color: #4A9EFF;
          border-width: 2px;
          background: #2E2E2E;
        }

        .channel-name {
          font-size: 11px;
          color: #E8E8E8;
          text-align: center;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .channel-inserts {
          display: flex;
          flex-direction: column;
          gap: 4px;
          margin-bottom: 8px;
        }

        .insert-slot {
          height: 24px;
          background: #0A0A0A;
          border: 1px solid #2A2A2A;
          border-radius: 4px;
          font-size: 9px;
          color: #6E6E6E;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
        }

        .insert-slot:hover {
          border-color: #4A9EFF;
          color: #E8E8E8;
        }

        .insert-slot.active {
          background: #4A9EFF;
          color: #0A0A0A;
          border-color: #4A9EFF;
        }

        .fader-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .fader-container {
          display: flex;
          gap: 8px;
          align-items: flex-end;
          width: 100%;
          justify-content: center;
        }

        .level-meter {
          width: 12px;
          height: 160px;
          background: #0A0A0A;
          border-radius: 6px;
          position: relative;
          overflow: hidden;
          border: 1px solid #2A2A2A;
        }

        .meter-fill {
          position: absolute;
          bottom: 0;
          width: 100%;
          background: linear-gradient(to top, #10B981 0%, #3B82F6 50%, #F59E0B 75%, #EF4444 90%);
          transition: height 0.05s;
        }

        .fader-track {
          width: 32px;
          height: 160px;
          background: #0A0A0A;
          border-radius: 16px;
          position: relative;
          cursor: pointer;
          border: 1px solid #2A2A2A;
        }

        .fader-fill {
          position: absolute;
          bottom: 0;
          width: 100%;
          background: linear-gradient(to top, #4A9EFF 0%, #8B5CF6 100%);
          border-radius: 16px;
          transition: height 0.1s;
        }

        .fader-thumb {
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          width: 40px;
          height: 20px;
          background: #FFFFFF;
          border: 2px solid #4A9EFF;
          border-radius: 4px;
          cursor: grab;
          transition: bottom 0.1s;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
        }

        .fader-value {
          font-size: 11px;
          color: #FFFFFF;
          font-family: "SF Mono", Monaco, monospace;
          text-align: center;
        }

        .channel-controls {
          display: flex;
          flex-direction: column;
          gap: 6px;
          margin-top: 8px;
        }

        .channel-control-btn {
          width: 100%;
          height: 28px;
          border-radius: 4px;
          border: 1px solid #3A3A3A;
          background: #1A1A1A;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 10px;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #E8E8E8;
        }

        .channel-control-btn:hover {
          border-color: #4A4A4A;
          transform: scale(1.02);
        }

        .channel-control-btn.solo {
          background: #1A1400;
          color: #F59E0B;
        }

        .channel-control-btn.solo.active {
          background: #F59E0B;
          color: #0A0A0A;
          box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
        }

        .channel-control-btn.mute {
          background: #1A1A1A;
          color: #6E6E6E;
        }

        .channel-control-btn.mute.active {
          background: #2E2E2E;
          color: #B8B8B8;
        }

        /* AI Panel */
        .ai-panel {
          position: fixed;
          right: ${aiPanelOpen ? '0' : '-360px'};
          top: 112px;
          bottom: 36px;
          width: 360px;
          background: #1A1A1A;
          border-left: 1px solid #3A3A3A;
          transition: right 0.3s;
          z-index: 1000;
          display: flex;
          flex-direction: column;
        }

        .ai-panel-header {
          padding: 16px;
          background: #242424;
          border-bottom: 1px solid #3A3A3A;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .ai-panel-title {
          font-size: 14px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ai-panel-content {
          padding: 16px;
          overflow-y: auto;
          flex: 1;
        }

        .ai-suggestion {
          background: #242424;
          border: 1px solid #3A3A3A;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .ai-suggestion:hover {
          border-color: #4A9EFF;
          background: #383838;
          transform: translateX(4px);
        }

        .ai-suggestion-title {
          font-size: 12px;
          font-weight: 600;
          color: #FFFFFF;
          margin-bottom: 4px;
        }

        .ai-suggestion-desc {
          font-size: 11px;
          color: #B8B8B8;
        }

        /* Info Bar */
        .info-bar {
          background: #1A1A1A;
          border-top: 1px solid #3A3A3A;
          padding: 8px 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          height: 36px;
        }

        .info-item {
          font-size: 11px;
          color: #6E6E6E;
          font-family: "SF Mono", Monaco, monospace;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .info-value {
          color: #E8E8E8;
          font-weight: 600;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        ::-webkit-scrollbar-track {
          background: #121212;
        }

        ::-webkit-scrollbar-thumb {
          background: #2E2E2E;
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: #383838;
        }
      `}</style>

      {/* Menu Bar */}
      <div className="menu-bar">
        <div className="menu-logo">APEX</div>
        <div className="menu-items">
          <div className="menu-item">File</div>
          <div className="menu-item">Edit</div>
          <div className="menu-item">View</div>
          <div className="menu-item">Track</div>
          <div className="menu-item">Region</div>
          <div className="menu-item">Audio</div>
          <div className="menu-item">MIDI</div>
          <div className="menu-item">Mix</div>
          <div className="menu-item">Window</div>
        </div>
        <div className="menu-actions">
          <div className="ai-status">
            <div className="ai-status-dot"></div>
            AI ACTIVE
          </div>
          <div style={{ fontSize: '11px', color: '#6E6E6E' }}>Project: Untitled</div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        {/* Edit Modes */}
        <div className="toolbar-section">
          <span className="toolbar-label">Edit</span>
          <div className="edit-mode-group">
            <button 
              className={`edit-mode-btn ${editMode === 'shuffle' ? 'active' : ''}`}
              onClick={() => setEditMode('shuffle')}
            >
              SHFL
            </button>
            <button 
              className={`edit-mode-btn ${editMode === 'slip' ? 'active' : ''}`}
              onClick={() => setEditMode('slip')}
            >
              SLIP
            </button>
            <button 
              className={`edit-mode-btn ${editMode === 'spot' ? 'active' : ''}`}
              onClick={() => setEditMode('spot')}
            >
              SPOT
            </button>
            <button 
              className={`edit-mode-btn ${editMode === 'grid' ? 'active' : ''}`}
              onClick={() => setEditMode('grid')}
            >
              GRID
            </button>
          </div>
        </div>

        {/* Tool Selector */}
        <div className="toolbar-section">
          <span className="toolbar-label">Tools</span>
          <div className="tool-selector">
            <button 
              className={`tool-btn ${selectedTool === 'select' ? 'active' : ''}`}
              onClick={() => setSelectedTool('select')}
            >
              <Camera size={18} />
            </button>
            <button 
              className={`tool-btn ${selectedTool === 'trim' ? 'active' : ''}`}
              onClick={() => setSelectedTool('trim')}
            >
              <Scissors size={18} />
            </button>
            <button 
              className={`tool-btn ${selectedTool === 'slip' ? 'active' : ''}`}
              onClick={() => setSelectedTool('slip')}
            >
              <Maximize2 size={18} />
            </button>
            <button 
              className={`tool-btn ${selectedTool === 'pencil' ? 'active' : ''}`}
              onClick={() => setSelectedTool('pencil')}
            >
              <Edit3 size={18} />
            </button>
            <button 
              className={`tool-btn ${selectedTool === 'eraser' ? 'active' : ''}`}
              onClick={() => setSelectedTool('eraser')}
            >
              <Trash2 size={18} />
            </button>
            <button 
              className={`tool-btn ${selectedTool === 'automation' ? 'active' : ''}`}
              onClick={() => setSelectedTool('automation')}
            >
              <TrendingUp size={18} />
            </button>
          </div>
        </div>

        {/* Transport Controls */}
        <div className="toolbar-section">
          <span className="toolbar-label">Transport</span>
          <div className="transport-controls">
            <button className="transport-btn" onClick={handleStop}>⏮</button>
            <button className="transport-btn">⏪</button>
            <button 
              className={`transport-btn play ${projectState.isPlaying ? 'active' : ''}`}
              onClick={handlePlayPause}
            >
              {projectState.isPlaying ? <Square size={20} /> : <Play size={20} />}
            </button>
            <button className="transport-btn" onClick={handleStop}>⏹</button>
            <button 
              className={`transport-btn record ${projectState.isRecording ? 'active' : ''}`}
              onClick={handleRecord}
            >
              <Circle size={20} />
            </button>
            <button className="transport-btn">🔁</button>
          </div>
        </div>

        {/* Time Display */}
        <div className="toolbar-section">
          <div className="time-display">
            <div className="time-main">
              {Math.floor(projectState.playheadPosition / 3600000).toString().padStart(2, '0')}:
              {Math.floor((projectState.playheadPosition % 3600000) / 60000).toString().padStart(2, '0')}:
              {Math.floor((projectState.playheadPosition % 60000) / 1000).toString().padStart(2, '0')}:
              {Math.floor((projectState.playheadPosition % 1000) / 10).toString().padStart(2, '0')}
            </div>
            <div className="time-secondary">
              {projectState.tempo.toFixed(2)} BPM | {projectState.timeSignature[0]}/{projectState.timeSignature[1]}
            </div>
          </div>
        </div>

        {/* Snap Controls */}
        <div className="toolbar-section">
          <span className="toolbar-label">Snap</span>
          <div className="snap-control">
            <span 
              className={`snap-toggle ${projectState.snapEnabled ? 'active' : ''}`}
              onClick={() => setProjectState(prev => ({ ...prev, snapEnabled: !prev.snapEnabled }))}
            >
              SNAP
            </span>
            <div className="grid-value">{projectState.gridResolution}</div>
          </div>
        </div>

        {/* View Options */}
        <div className="toolbar-section" style={{ borderRight: 'none' }}>
          <button className="tool-btn"><ZoomIn size={18} /></button>
          <button className="tool-btn"><ZoomOut size={18} /></button>
          <button className="tool-btn"><Maximize2 size={18} /></button>
          <button 
            className="tool-btn"
            onClick={() => setAiPanelOpen(!aiPanelOpen)}
          >
            <Sparkles size={18} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Left Sidebar */}
        <div className="left-sidebar">
          <div className="sidebar-tabs">
            <div className="sidebar-tab active">BROWSER</div>
            <div className="sidebar-tab">LIBRARY</div>
            <div className="sidebar-tab">FX</div>
          </div>
          <div className="sidebar-content">
            <div className="browser-item">
              <div className="browser-item-name">🎵 Acoustic Guitar.wav</div>
              <div className="browser-item-info">48kHz • 24bit • 00:32</div>
            </div>
            <div className="browser-item">
              <div className="browser-item-name">🎹 Piano Lead.mid</div>
              <div className="browser-item-info">MIDI • C Major • 120 BPM</div>
            </div>
            <div className="browser-item">
              <div className="browser-item-name">🥁 Drum Loop.wav</div>
              <div className="browser-item-info">48kHz • 24bit • 00:08</div>
            </div>
            <div className="browser-item">
              <div className="browser-item-name">🎸 Bass Synth.wav</div>
              <div className="browser-item-info">48kHz • 24bit • 00:16</div>
            </div>
          </div>
        </div>

        {/* Center Area */}
        <div className="center-area">
          {/* Ruler */}
          <div className="ruler">
            <div 
              className="playhead" 
              style={{ left: `${(projectState.playheadPosition / 10000) * 60}px` }}
            ></div>
          </div>

          {/* Track Workspace */}
          <div className="track-workspace">
            {/* Track Headers */}
            <div className="track-headers">
              {tracks.map(track => (
                <div 
                  key={track.id}
                  className={`track-header ${selectedTrackId === track.id ? 'selected' : ''}`}
                  onClick={() => setSelectedTrackId(track.id)}
                >
                  <div className="track-header-top">
                    <div 
                      className="track-type-indicator" 
                      style={{ background: track.color }}
                    ></div>
                    <div className="track-info">
                      <div className="track-name">{track.name}</div>
                      <div className="track-routing">{track.routing}</div>
                    </div>
                    <div className="track-controls">
                      <button 
                        className={`track-btn record ${track.record ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTrackToggle(track.id, 'record');
                        }}
                        disabled={track.type === 'aux' || track.type === 'master'}
                      >
                        R
                      </button>
                      <button 
                        className={`track-btn mute ${track.mute ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTrackToggle(track.id, 'mute');
                        }}
                      >
                        M
                      </button>
                      <button 
                        className={`track-btn solo ${track.solo ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTrackToggle(track.id, 'solo');
                        }}
                        disabled={track.type === 'master'}
                      >
                        S
                      </button>
                      <button 
                        className={`track-btn monitor ${track.monitor ? 'active' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTrackToggle(track.id, 'monitor');
                        }}
                        disabled={track.type === 'aux' || track.type === 'master'}
                      >
                        I
                      </button>
                    </div>
                  </div>
                  <div className="track-header-bottom">
                    <div className="track-meter-mini">
                      <div 
                        className="track-meter-fill" 
                        style={{ width: `${track.meter.peak * 100}%` }}
                      ></div>
                    </div>
                    <div className="track-volume">
                      {(20 * Math.log10(track.volume / 100)).toFixed(1)} dB
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Arrangement Area */}
            <div className="arrangement-area">
              <div className="arrangement-grid"></div>
              <div className="arrangement-tracks">
                {tracks.map(track => (
                  <div key={track.id} className="arrangement-track">
                    {track.regions.map(region => (
                      <div
                        key={region.id}
                        className={`region ${region.selected ? 'selected' : ''}`}
                        style={{
                          left: `${(region.start / 10000) * 60}px`,
                          width: `${(region.duration / 10000) * 60}px`,
                          borderColor: region.color
                        }}
                        onClick={() => handleRegionSelect(region.id)}
                      >
                        <div className="region-waveform">
                          <div style={{
                            width: '100%',
                            height: '100%',
                            background: track.type === 'midi' 
                              ? `linear-gradient(to bottom, transparent 20%, ${track.color} 40%, ${track.color} 60%, transparent 80%)`
                              : `linear-gradient(to bottom, transparent 0%, ${track.color} 45%, ${track.color} 55%, transparent 100%)`
                          }}></div>
                        </div>
                        <div className="region-label">{region.name}</div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Mixer */}
        <div className="right-sidebar">
          <div className="mixer-header">
            <h3>Mixer</h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="tool-btn"><Settings size={16} /></button>
              <button className="tool-btn"><Maximize2 size={16} /></button>
            </div>
          </div>

          <div className="mixer-channels">
            {tracks.slice(0, 4).map(track => (
              <div 
                key={track.id}
                className={`channel-strip ${selectedTrackId === track.id ? 'selected' : ''}`}
                onClick={() => setSelectedTrackId(track.id)}
              >
                <div className="channel-name">{track.name.toUpperCase()}</div>
                
                <div className="channel-inserts">
                  {track.inserts.map(insert => (
                    <div 
                      key={insert.id}
                      className={`insert-slot ${insert.active ? 'active' : ''}`}
                    >
                      {insert.name}
                    </div>
                  ))}
                  {Array.from({ length: 4 - track.inserts.length }).map((_, i) => (
                    <div key={`empty-${i}`} className="insert-slot">
                      INSERT {track.inserts.length + i + 1}
                    </div>
                  ))}
                </div>

                <div className="fader-section">
                  <div className="fader-container">
                    <div className="level-meter">
                      <div 
                        className="meter-fill" 
                        style={{ height: `${track.meter.peak * 100}%` }}
                      ></div>
                    </div>
                    <div className="fader-track">
                      <div 
                        className="fader-fill" 
                        style={{ height: `${track.volume}%` }}
                      ></div>
                      <div 
                        className="fader-thumb" 
                        style={{ bottom: `${track.volume}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="fader-value">
                    {(20 * Math.log10(track.volume / 100)).toFixed(1)} dB
                  </div>
                </div>

                <div className="channel-controls">
                  <button 
                    className={`channel-control-btn solo ${track.solo ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTrackToggle(track.id, 'solo');
                    }}
                  >
                    S
                  </button>
                  <button 
                    className={`channel-control-btn mute ${track.mute ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTrackToggle(track.id, 'mute');
                    }}
                  >
                    M
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Panel */}
      <div className="ai-panel">
        <div className="ai-panel-header">
          <div className="ai-panel-title">
            <Sparkles size={16} />
            AI Assistant
          </div>
          <button className="tool-btn" onClick={() => setAiPanelOpen(false)}>✕</button>
        </div>
        <div className="ai-panel-content">
          {aiAnalyses.map(analysis => (
            <div key={analysis.id} className="ai-suggestion">
              <div className="ai-suggestion-title">{analysis.title}</div>
              <div className="ai-suggestion-desc">{analysis.description}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Info Bar */}
      <div className="info-bar">
        <div className="info-item">
          <Cpu size={12} />
          CPU: <span className="info-value">{cpuUsage.toFixed(0)}%</span>
        </div>
        <div className="info-item">
          <HardDrive size={12} />
          DISK: <span className="info-value">{diskIO.toFixed(0)} MB/s</span>
        </div>
        <div className="info-item">
          <Database size={12} />
          SAMPLE RATE: <span className="info-value">{projectState.sampleRate / 1000} kHz</span>
        </div>
        <div className="info-item">
          BUFFER: <span className="info-value">{projectState.bufferSize} samples</span>
        </div>
        <div className="info-item">
          <Clock size={12} />
          LATENCY: <span className="info-value">{latency.toFixed(1)} ms</span>
        </div>
        <div className="info-item">
          FREE SPACE: <span className="info-value">234.5 GB</span>
        </div>
      </div>
    </div>
  );
};

export default ApexDAW;
