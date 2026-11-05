
import React, { useState, useEffect, useRef } from 'react';
import { Plug } from './icons';

interface LogEntry {
  id: number;
  source: 'HOST' | 'SYNC' | 'AUDIO' | 'AI' | 'MIDI';
  message: string;
}

interface Track {
  name: string;
  solo: boolean;
  mute: boolean;
  // Audio characteristics for simulation
  profile: {
    spectrum: [number, number, number]; // Low, Mid, High
    loudness: number; // Contribution to overall loudness
    transientChance: number;
  }
}

const initialLog: LogEntry[] = [
  { id: 1, source: 'HOST', message: 'Initializing plugin bridge...' },
  { id: 2, source: 'HOST', message: 'Connected: VST3 on \'Master Bus\'' },
];

const simulatedMessages = [
  // SYNC Messages (Gray/Red/Green)
  { source: 'SYNC', message: () => `Playhead: ${Math.floor(Math.random() * 128) + 1}:${String(Math.floor(Math.random() * 4) + 1).padStart(2, '0')}.${String(Math.floor(Math.random() * 960)).padStart(3, '0')}` },
  { source: 'SYNC', message: 'Transport STOP.' },
  { source: 'SYNC', message: 'Transport PLAY.' },
  { source: 'SYNC', message: 'Loop region enabled: 9.1.000 -> 17.1.000' },
  { source: 'SYNC', message: 'Tempo change detected: 120 -> 122 BPM' },

  // AUDIO Streaming Messages (Blue)
  { source: 'AUDIO', message: 'Streaming \'Lead Vocals\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Bass DI\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Kick In\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Snare Top\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Hi-Hats\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Acoustic Gtr L\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Rhythm Gtr R\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Synth Pad\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Piano Chords\' for analysis...' },
  { source: 'AUDIO', message: 'Streaming \'Drums Bus\' for analysis...' },

  // AI Analysis & Suggestions (Cyan)
  { source: 'AI', message: 'Analysis: Detected harshness in 3-5kHz range on \'Lead Vocals\'.' },
  { source: 'AI', message: 'Suggestion: Apply dynamic EQ with a 2.5dB cut at 4.2kHz.' },
  { source: 'AI', message: 'Analysis: Bass and Kick frequencies are clashing at 80Hz.' },
  { source: 'AI', message: 'Suggestion: Sidechain compress \'Bass DI\' with \'Kick In\' trigger.' },
  { source: 'AI', message: 'Analysis: \'Acoustic Gtr L\' sounds muddy in the low-mids.' },
  { source: 'AI', message: 'Suggestion: Gentle cut around 250Hz on \'Acoustic Gtr L\'.' },
  { source: 'AI', message: 'Analysis: \'Snare Top\' is lacking body.' },
  { source: 'AI', message: 'Suggestion: Try a small boost around 200Hz to add weight.' },
  { source: 'AI', message: 'Analysis: Vocals seem overly dynamic.' },
  { source: 'AI', message: 'Suggestion: Apply light compression (2:1 ratio, 20ms attack).' },
  { source: 'AI', message: 'Analysis: \'Hi-Hats\' are very dry.' },
  { source: 'AI', message: 'Suggestion: Add a short, subtle reverb to give them space.' },
  { source: 'AI', message: 'Analysis: Stereo image is narrow.' },
  { source: 'AI', message: 'Suggestion: Pan guitars L/R to create width.' },
  
  // HOST Messages (Yellow)
  { source: 'HOST', message: 'Awaiting transport command...' },
  { source: 'HOST', message: 'Automation mode set to: Read' },
];

const initialTracks: Track[] = [
    { name: 'Lead Vocals', solo: false, mute: false, profile: { spectrum: [0.3, 0.8, 0.5], loudness: -18, transientChance: 0.2 } },
    { name: 'Bass DI', solo: false, mute: false, profile: { spectrum: [0.9, 0.4, 0.1], loudness: -19, transientChance: 0.1 } },
    { name: 'Drums Bus', solo: false, mute: false, profile: { spectrum: [0.7, 0.6, 0.8], loudness: -15, transientChance: 0.7 } },
    { name: 'Synth Pad', solo: false, mute: false, profile: { spectrum: [0.4, 0.6, 0.4], loudness: -22, transientChance: 0.05 } },
];


export const PluginBridge: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>(initialLog);
  const logContainerRef = useRef<HTMLDivElement>(null);
  
  const [spectrumData, setSpectrumData] = useState([0.5, 0.7, 0.4]);
  const [loudness, setLoudness] = useState(-14.5);
  const [transientDetected, setTransientDetected] = useState(false);
  const [tracks, setTracks] = useState<Track[]>(initialTracks);
  const [beatDetected, setBeatDetected] = useState(false);
  const [isMidiPlaying, setIsMidiPlaying] = useState(false);

  // Function to add a new log entry
  const addLog = (entry: Omit<LogEntry, 'id'>) => {
    setLogs(prev => {
        const newLog = { ...entry, id: Date.now() };
        const newLogs = [...prev, newLog];
        return newLogs.slice(Math.max(newLogs.length - 100, 0));
    });
  };

  // Effect for live communication log simulation
  useEffect(() => {
    const interval = setInterval(() => {
      const nextMessageTemplate = simulatedMessages[Math.floor(Math.random() * simulatedMessages.length)];
      addLog({
        source: nextMessageTemplate.source as any,
        message: typeof nextMessageTemplate.message === 'function' ? nextMessageTemplate.message() : nextMessageTemplate.message,
      });
    }, 2500);
    return () => clearInterval(interval);
  }, []);
  
  // Effect for Beat Detection Simulation
  useEffect(() => {
    const beatInterval = setInterval(() => {
        setBeatDetected(true);
        addLog({ source: 'AI', message: 'Beat detected!' });
        setTimeout(() => setBeatDetected(false), 100);
    }, 500); // 120 BPM
    return () => clearInterval(beatInterval);
  }, []);

  // Effect for real-time analysis simulation based on track state
  useEffect(() => {
    const analysisInterval = setInterval(() => {
      const soloedTracks = tracks.filter(t => t.solo);
      const activeTracks = soloedTracks.length > 0 ? soloedTracks : tracks.filter(t => !t.mute);

      if (activeTracks.length === 0) {
        setSpectrumData([0, 0, 0]);
        setLoudness(-Infinity);
        setTransientDetected(false);
        return;
      }

      // Calculate combined profile of active tracks
      const combinedProfile = activeTracks.reduce((acc, track) => {
        return {
          spectrum: [
            acc.spectrum[0] + track.profile.spectrum[0],
            acc.spectrum[1] + track.profile.spectrum[1],
            acc.spectrum[2] + track.profile.spectrum[2],
          ],
          loudness: acc.loudness + Math.pow(10, track.profile.loudness / 20), // Sum loudness in linear scale
          transientChance: acc.transientChance + track.profile.transientChance,
        };
      }, { spectrum: [0, 0, 0] as [number, number, number], loudness: 0, transientChance: 0 });

      // Normalize spectrum
      const avgSpectrum: [number, number, number] = [
        (combinedProfile.spectrum[0] / activeTracks.length) * (0.8 + Math.random() * 0.4),
        (combinedProfile.spectrum[1] / activeTracks.length) * (0.8 + Math.random() * 0.4),
        (combinedProfile.spectrum[2] / activeTracks.length) * (0.8 + Math.random() * 0.4),
      ];
      setSpectrumData(avgSpectrum);

      // Convert loudness back to dB and add variation
      const avgLoudness = 20 * Math.log10(combinedProfile.loudness) + (Math.random() * 3 - 1.5);
      setLoudness(avgLoudness);
      
      // Calculate transient chance
      const avgTransientChance = combinedProfile.transientChance / activeTracks.length;
      if (Math.random() < avgTransientChance) {
        setTransientDetected(true);
        setTimeout(() => setTransientDetected(false), 100);
      }

    }, 300); // Update roughly 3 times a second

    return () => clearInterval(analysisInterval);
  }, [tracks]);


  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleMute = (trackName: string) => {
    setTracks(prevTracks => {
      const newTracks = prevTracks.map(t =>
        t.name === trackName ? { ...t, mute: !t.mute } : t
      );
      const track = newTracks.find(t => t.name === trackName);
      if (track) {
        addLog({ source: 'HOST', message: `${track.mute ? 'Muted' : 'Unmuted'} '${trackName}'` });
      }
      return newTracks;
    });
  };

  const handleSolo = (trackName: string) => {
    setTracks(prevTracks => {
      const isCurrentlySoloed = prevTracks.find(t => t.name === trackName)?.solo;
      const newTracks = prevTracks.map(t => ({
        ...t,
        solo: t.name === trackName ? !isCurrentlySoloed : false,
      }));
       addLog({ source: 'HOST', message: `${!isCurrentlySoloed ? 'Solo enabled on' : 'Solo disabled for'} '${trackName}'` });
      return newTracks;
    });
  };

  const handleMidiTrigger = () => {
    if (isMidiPlaying) return;
    setIsMidiPlaying(true);
    addLog({ source: 'MIDI', message: 'Playing sequence...' });

    const notes = [60, 64, 67, 72]; // C4, E4, G4, C5
    let noteIndex = 0;
    
    const playNextNote = () => {
        if (noteIndex >= notes.length) {
            setIsMidiPlaying(false);
            addLog({ source: 'MIDI', message: 'Sequence finished.' });
            return;
        }

        const note = notes[noteIndex];
        const velocity = Math.floor(80 + Math.random() * 20);
        addLog({ source: 'MIDI', message: `Note On: ${note}, Vel: ${velocity}` });
        
        // Simulate audio reaction to MIDI note
        setTransientDetected(true);
        setLoudness(prev => Math.min(-6, prev + 3));
        setSpectrumData(prev => [prev[0]*1.1, prev[1]*1.2, prev[2]*1.1]);
        setTimeout(() => setTransientDetected(false), 100);

        setTimeout(() => {
            addLog({ source: 'MIDI', message: `Note Off: ${note}` });
            noteIndex++;
            playNextNote();
        }, 200);
    };
    playNextNote();
  };
  
  const getLogColor = (source: LogEntry['source']) => {
      switch (source) {
          case 'HOST': return 'var(--special-warning)';
          case 'SYNC': return 'var(--text-muted)';
          case 'AUDIO': return 'var(--accent-primary)';
          case 'AI': return 'var(--text-accent)';
          case 'MIDI': return 'var(--special-ai-suggestion)';
          default: return 'var(--text-primary)';
      }
  }

  return (
    <div className="flex flex-col h-full max-h-[85vh] rounded-lg overflow-hidden border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <h2 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--text-accent)' }}>
          <Plug className="w-6 h-6" /> DAW Plugin Bridge
        </h2>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Simulating real-time integration with your favorite DAW.</p>
      </div>
      
      {/* Mock DAW Chrome */}
      <div className="p-2 flex items-center justify-between text-xs flex-shrink-0" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
        <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--special-negative)' }}></div>
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--special-warning)' }}></div>
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--special-positive)' }}></div>
        </div>
        <div className="font-mono">AI Mix Partner (Insert 1) - Master Bus</div>
        <div className="flex items-center gap-2">
            <span className="font-bold">Bypass</span>
        </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 rounded-lg space-y-3" style={{ backgroundColor: 'var(--bg-primary)' }}>
                 <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Connection Status</h3>
                <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--special-positive)' }}>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: 'var(--special-positive)' }}></div>
                    <span>Connected to VST3 Host (Simulated)</span>
                </div>
                <h3 className="font-semibold pt-2" style={{ color: 'var(--text-primary)' }}>Supported Formats</h3>
                <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-1 rounded" style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)'}}>VST3</span>
                    <span className="px-2 py-1 rounded" style={{ backgroundColor: 'var(--special-ai-suggestion)', color: 'var(--text-primary)'}}>AU</span>
                    <span className="px-2 py-1 rounded" style={{ backgroundColor: 'var(--special-warning)', color: 'var(--bg-primary)'}}>AAX</span>
                </div>
            </div>

             <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-primary)' }}>
                <h3 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Track Controls</h3>
                <div className="space-y-2">
                    {tracks.map(track => (
                        <div key={track.name} className="flex items-center justify-between p-1.5 rounded-md" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            <span className={`text-sm ${track.mute ? 'line-through' : ''}`} style={{ color: track.mute ? 'var(--text-muted)' : 'var(--text-secondary)'}}>{track.name}</span>
                            <div className="flex items-center gap-2">
                                <button onClick={() => handleSolo(track.name)} className={`w-6 h-6 flex items-center justify-center rounded text-xs font-bold transition-colors`} style={{ backgroundColor: track.solo ? 'var(--special-warning)' : 'var(--bg-interactive)', color: 'var(--text-primary)'}}>S</button>
                                <button onClick={() => handleMute(track.name)} className={`w-6 h-6 flex items-center justify-center rounded text-xs font-bold transition-colors`} style={{ backgroundColor: track.mute ? 'var(--special-negative)' : 'var(--bg-interactive)', color: 'var(--text-primary)'}}>M</button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-primary)' }}>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>Real-Time Audio Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Frequency Spectrum */}
                <div className="lg:col-span-2">
                    <p className="text-xs mb-1" style={{color: 'var(--text-muted)'}}>Frequency Spectrum</p>
                    <div className="flex items-end h-20 gap-2 p-2 rounded-md" style={{ backgroundColor: 'rgba(0,0,0,0.3)' }}>
                        {['Lows', 'Mids', 'Highs'].map((label, index) => (
                            <div key={label} className="flex-1 flex flex-col items-center justify-end">
                                <div
                                    className="w-full rounded-t-sm transition-all duration-150"
                                    style={{ height: `${Math.min(1, spectrumData[index]) * 100}%`, backgroundColor: 'var(--accent-primary)' }}
                                    title={`${label}: ${Math.round(spectrumData[index] * 100)}%`}
                                ></div>
                                <p className="text-xs mt-1" style={{color: 'var(--text-muted)'}}>{label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Loudness & Transients */}
                <div className="space-y-3">
                     <div>
                        <p className="text-xs mb-1 flex justify-between" style={{color: 'var(--text-muted)'}}>
                            <span>Loudness (LUFS)</span>
                            <span className="font-mono">{isFinite(loudness) ? loudness.toFixed(1) : '-inf'}</span>
                        </p>
                        <div className="w-full rounded-full h-4 p-0.5" style={{ backgroundColor: 'rgba(0,0,0,0.3)' }}>
                            <div
                                className={`h-full rounded-full transition-all duration-150`}
                                style={{ 
                                    backgroundColor: loudness > -6 ? 'var(--special-negative)' : loudness > -14 ? 'var(--special-warning)' : 'var(--special-positive)',
                                    width: `${isFinite(loudness) ? Math.max(0, (loudness + 48) / 50 * 100) : 0}%` 
                                }}
                            ></div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <p className="text-xs" style={{color: 'var(--text-muted)'}}>Transients:</p>
                        <div className={`w-3 h-3 rounded-full transition-all`} style={{ backgroundColor: transientDetected ? 'var(--special-warning)' : 'var(--bg-interactive)' }}></div>
                         <span className={`text-xs font-mono`} style={{ color: transientDetected ? 'var(--special-warning)' : 'var(--text-muted)' }}>
                            {transientDetected ? 'DETECT' : '––'}
                        </span>
                    </div>
                     <div className="flex items-center gap-2">
                        <p className="text-xs" style={{color: 'var(--text-muted)'}}>Beat:</p>
                        <div className={`w-3 h-3 rounded-full transition-all`} style={{ backgroundColor: beatDetected ? 'var(--text-accent)' : 'var(--bg-interactive)' }}></div>
                         <span className={`text-xs font-mono`} style={{ color: beatDetected ? 'var(--text-accent)' : 'var(--text-muted)' }}>
                            {beatDetected ? 'PULSE' : '––'}
                        </span>
                    </div>
                </div>

                {/* MIDI Input */}
                <div className="p-3 rounded-lg flex flex-col justify-center items-center" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    <h4 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>MIDI Input</h4>
                    <button onClick={handleMidiTrigger} disabled={isMidiPlaying} className="px-3 py-2 text-sm text-white font-semibold rounded-lg transition-colors w-full" style={{ backgroundColor: 'var(--special-ai-suggestion)' }}>
                        {isMidiPlaying ? 'Playing...' : 'Trigger MIDI Sequence'}
                    </button>
                </div>
            </div>
        </div>

        <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-primary)' }}>
            <h3 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Live Communication Log</h3>
            <div ref={logContainerRef} className="h-48 rounded-md p-2 font-mono text-xs overflow-y-auto" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                {logs.map(log => (
                    <div key={log.id} className="flex gap-2 animate-fade-in-fast">
                        <span className={`flex-shrink-0`} style={{color: getLogColor(log.source)}}>{`[${log.source}]`.padEnd(7)}</span>
                        <span className="flex-1 break-words" style={{color: 'var(--text-secondary)'}}>{log.message}</span>
                    </div>
                ))}
            </div>
        </div>
      </div>
    </div>
  );
};
