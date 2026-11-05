import React, { useState, useEffect, useRef } from 'react';
import { separateInitialStems, separateSubStems, refineOtherStem, suggestMix } from '../services/geminiService';
import { Music, UploadCloud, FileAudio, Sparkles, Download, Layers, LetterS, LetterM, Wand } from './icons';
import { StemResult } from '../types';

// A new component for the 3-band EQ visualizer and controls
const EQVisualizer: React.FC<{ eq: [number, number, number], onChange: (newEq: [number, number, number]) => void }> = ({ eq, onChange }) => {
    const bands = ['Lows', 'Mids', 'Highs'];
    return (
        <div className="flex items-end h-20 gap-2 p-2 rounded-md" style={{ backgroundColor: 'var(--bg-primary)', opacity: '0.5' }}>
            {bands.map((label, index) => (
                <div key={label} className="flex-1 flex flex-col items-center justify-end">
                     <input
                        type="range"
                        min="-1" max="1" step="0.1"
                        value={eq[index]}
                        onChange={(e) => {
                            const newEq = [...eq] as [number, number, number];
                            newEq[index] = parseFloat(e.target.value);
                            onChange(newEq);
                        }}
                        className="w-16 h-1 rounded-lg appearance-none cursor-pointer"
                        // FIX: Cast 'slider-vertical' to 'any' to resolve TypeScript error for non-standard CSS property value.
                        style={{
                            'appearance': 'slider-vertical' as any,
                            accentColor: 'var(--accent-primary)',
                            backgroundColor: 'var(--bg-tertiary)'
                        }}
                    />
                    <p className="text-xs mt-1" style={{color: 'var(--text-muted)'}}>{label[0]}</p>
                </div>
            ))}
        </div>
    );
};


export const StemSeparator: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [results, setResults] = useState<StemResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubSeparating, setIsSubSeparating] = useState<{ [key: string]: boolean }>({});
  const [isSuggestingMix, setIsSuggestingMix] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [otherRefinePrompt, setOtherRefinePrompt] = useState('');
  
  const audioRefs = useRef<{ [key: string]: HTMLAudioElement | null }>({});
  const audioContextRef = useRef<AudioContext | null>(null);
  const trackNodesRef = useRef<{ [key: string]: { source: MediaElementAudioSourceNode, pan: StereoPannerNode, gain: GainNode } }>({});
  
  // Initialize AudioContext
  useEffect(() => {
    if (!audioContextRef.current) {
        // FIX: Cast window to any to support webkitAudioContext for older browsers.
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
  }, []);

  // Effect to manage Web Audio API graph
  useEffect(() => {
    const audioContext = audioContextRef.current;
    if (!audioContext) return;
    
    const isAnySolo = results.some(r => r.solo);

    results.forEach(result => {
      const audioEl = audioRefs.current[result.id];
      if (audioEl && !trackNodesRef.current[result.id]) {
        const source = audioContext.createMediaElementSource(audioEl);
        const pan = audioContext.createStereoPanner();
        const gain = audioContext.createGain();
        source.connect(pan).connect(gain).connect(audioContext.destination);
        trackNodesRef.current[result.id] = { source, pan, gain };
      }
      
      const nodes = trackNodesRef.current[result.id];
      if (nodes) {
          nodes.pan.pan.value = result.pan;
          nodes.gain.gain.value = (isAnySolo ? (result.solo ? 1 : 0) : (result.mute ? 0 : 1)) * result.volume;
      }
    });
  }, [results]);


  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResults([]);
      setError(null);
    }
  };

  const handleInitialSeparate = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError(null);
    setResults([]);
    try {
      const separatedStems = await separateInitialStems(selectedFile);
      setResults(separatedStems);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSubSeparate = async (parentStem: StemResult) => {
    setIsSubSeparating(prev => ({...prev, [parentStem.id]: true}));
    try {
      const subStems = await separateSubStems(parentStem.name);
      setResults(prev => [
          ...prev.filter(s => s.id !== parentStem.id),
          ...subStems
      ]);
    } catch (err) {
       setError(`Failed to separate ${parentStem.name}.`);
    } finally {
        setIsSubSeparating(prev => ({...prev, [parentStem.id]: false}));
    }
  };

  const handleRefineOther = async (parentStem: StemResult) => {
    if (!otherRefinePrompt.trim()) return;
    setIsSubSeparating(prev => ({...prev, [parentStem.id]: true}));
    try {
        const refinedStems = await refineOtherStem(otherRefinePrompt);
        setResults(prev => [
            ...prev.filter(s => s.id !== parentStem.id),
            ...refinedStems
        ]);
        setOtherRefinePrompt('');
    } catch(err) {
        setError(`Failed to refine 'Other' stem.`);
    } finally {
        setIsSubSeparating(prev => ({...prev, [parentStem.id]: false}));
    }
  }

  const handleSuggestMix = async () => {
    setIsSuggestingMix(true);
    try {
        const mixedStems = await suggestMix(results);
        setResults(mixedStems);
    } catch(err) {
        setError("Failed to generate mix suggestion.");
    } finally {
        setIsSuggestingMix(false);
    }
  }

  const handleMixerChange = (id: string, newValues: Partial<Pick<StemResult, 'solo' | 'mute' | 'volume' | 'pan' | 'eq'>>) => {
    setResults(prev => {
        let newResults = [...prev];
        if (newValues.solo) {
            newResults = newResults.map(r => r.id === id ? r : {...r, solo: false});
        }
        return newResults.map(r => r.id === id ? {...r, ...newValues} : r);
    });
  }

  useEffect(() => {
    return () => {
      results.forEach(result => URL.revokeObjectURL(result.url));
      Object.values(trackNodesRef.current).forEach(nodes => {
        nodes.source.disconnect();
        nodes.pan.disconnect();
        nodes.gain.disconnect();
      });
      trackNodesRef.current = {};
    };
  }, [results]);

  const topLevelStems = results.filter(r => !r.parentName);
  const subStems = results.filter(r => r.parentName);

  return (
    <div className="flex flex-col h-full max-h-[85vh] rounded-lg overflow-hidden border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <h2 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--text-accent)' }}><Music className="w-6 h-6" /> Stem Separation & Mixer</h2>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Separate audio, refine with AI, and create a quick mix.</p>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        {!selectedFile ? (
          <div className="flex flex-col items-center justify-center h-full border-2 border-dashed rounded-lg p-8" style={{ borderColor: 'var(--border-primary)' }}>
            <UploadCloud className="w-16 h-16 mb-4" style={{ color: 'var(--text-muted)' }} />
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Upload your audio file</h3>
            <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>Supports .wav, .mp3, .flac</p>
            <input id="file-upload" type="file" accept="audio/wav, audio/mpeg, audio/flac" onChange={handleFileChange} className="hidden" />
            <label htmlFor="file-upload" className="px-4 py-2 font-semibold rounded-lg cursor-pointer transition-colors" style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)'}}>Choose File</label>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 rounded-lg flex items-center justify-between" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                <div className="flex items-center gap-3"><FileAudio className="w-6 h-6" style={{color: 'var(--text-accent)'}}/><span className="font-medium" style={{color: 'var(--text-primary)'}}>{selectedFile.name}</span></div>
                <button onClick={() => { setSelectedFile(null); setResults([]); }} className="text-sm" style={{color: 'var(--text-muted)'}}>Clear</button>
            </div>
            <button onClick={handleInitialSeparate} disabled={isLoading} className="w-full flex items-center justify-center gap-2 px-4 py-3 font-semibold rounded-lg transition-colors" style={{backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)'}}><Sparkles className="w-5 h-5"/>{isLoading ? 'Separating...' : 'Separate Stems'}</button>
          </div>
        )}

        {isLoading && (
            <div className="mt-8 flex flex-col items-center justify-center" style={{color: 'var(--text-accent)'}}>
                <Sparkles className="w-12 h-12 animate-pulse"/>
                <p className="mt-2 text-lg font-semibold">AI is working its magic...</p>
                <p className="text-sm" style={{color: 'var(--text-muted)'}}>This might take a moment.</p>
            </div>
        )}
        
        {error && <p className="mt-4 text-center" style={{color: 'var(--special-negative)'}}>{error}</p>}
        
        {results.length > 0 && (
            <div className="mt-6 space-y-6">
                 <button onClick={handleSuggestMix} disabled={isSuggestingMix} className="w-full flex items-center justify-center gap-2 px-4 py-3 text-white font-semibold rounded-lg transition-colors" style={{backgroundColor: 'var(--special-ai-suggestion)'}}>
                    <Sparkles className="w-5 h-5"/>
                    {isSuggestingMix ? 'Thinking...' : 'Suggest a Mix'}
                </button>

                <div>
                    <h3 className="text-lg font-semibold mb-3" style={{color: 'var(--text-primary)'}}>Mixer</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[...topLevelStems, ...subStems].map((stem) => (
                            <div key={stem.id} className="p-3 rounded-lg space-y-3 flex flex-col" style={{backgroundColor: 'var(--bg-tertiary)'}}>
                                <div>
                                    {stem.parentName && <span className="text-xs px-2 py-0.5 rounded-full" style={{backgroundColor: 'var(--bg-interactive)', color: 'var(--text-secondary)'}}>{stem.parentName}</span>}
                                    <h4 className={`font-semibold ${stem.parentName ? 'mt-1' : ''}`} style={{color: 'var(--text-accent)'}}>{stem.name}</h4>
                                </div>

                                <div className="flex-1 flex gap-4">
                                    <div className="w-2/3 space-y-3">
                                        <audio controls src={stem.url} className="w-full h-10" loop ref={el => { audioRefs.current[stem.id] = el; }}></audio>
                                        <div className="space-y-2">
                                            {/* Pan Control */}
                                            <div>
                                                <label className="text-xs flex justify-between" style={{color: 'var(--text-muted)'}}><span>L</span><span>Pan</span><span>R</span></label>
                                                <input type="range" min="-1" max="1" step="0.05" value={stem.pan} onChange={(e) => handleMixerChange(stem.id, { pan: parseFloat(e.target.value) })} className="w-full h-2 rounded-lg appearance-none cursor-pointer" style={{backgroundColor: 'var(--bg-primary)', accentColor: 'var(--accent-primary)'}} />
                                            </div>
                                            {/* Volume Fader */}
                                            <input type="range" min="0" max="1.2" step="0.01" value={stem.volume} onChange={(e) => handleMixerChange(stem.id, { volume: parseFloat(e.target.value)})} className="w-full h-2 rounded-lg appearance-none cursor-pointer" style={{backgroundColor: 'var(--bg-primary)', accentColor: 'var(--accent-primary)'}}/>
                                        </div>
                                    </div>
                                    <div className="w-1/3 flex flex-col justify-between">
                                        <EQVisualizer eq={stem.eq} onChange={(newEq) => handleMixerChange(stem.id, { eq: newEq })}/>
                                        <div className="flex justify-around">
                                            <button title="Solo" onClick={() => handleMixerChange(stem.id, { solo: !stem.solo })} className={`w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold transition-colors ${stem.solo ? '' : ''}`} style={{ backgroundColor: stem.solo ? 'var(--special-warning)' : 'var(--bg-interactive)', color: stem.solo ? 'var(--bg-primary)' : 'var(--text-primary)'}}><LetterS className="w-4 h-4"/></button>
                                            <button title="Mute" onClick={() => handleMixerChange(stem.id, { mute: !stem.mute })} className={`w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold transition-colors`} style={{ backgroundColor: stem.mute ? 'var(--special-negative)' : 'var(--bg-interactive)', color: 'var(--text-primary)'}}><LetterM className="w-4 h-4"/></button>
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="space-y-2">
                                    {stem.name !== 'Other' && (
                                        <a href={stem.url} download={`${selectedFile?.name.split('.')[0]}_${stem.name.toLowerCase()}.wav`} className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-semibold rounded-lg transition-colors" style={{backgroundColor: 'var(--bg-interactive)', color: 'var(--text-primary)'}}><Download className="w-4 h-4" />Download</a>
                                    )}
                                    {stem.isSeparable && stem.name === 'Drums' && (
                                        <button onClick={() => handleSubSeparate(stem)} disabled={isSubSeparating[stem.id]} className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-semibold rounded-lg transition-colors" style={{backgroundColor: 'var(--accent-secondary)', color: 'var(--text-primary)'}}><Layers className="w-4 h-4" />{isSubSeparating[stem.id] ? 'Separating...' : 'Separate Further'}</button>
                                    )}
                                    {stem.isSeparable && stem.name === 'Other' && (
                                        <div className="p-2 rounded-md space-y-2" style={{backgroundColor: 'var(--bg-primary)'}}>
                                            <input type="text" value={otherRefinePrompt} onChange={(e) => setOtherRefinePrompt(e.target.value)} placeholder="e.g., a lead guitar and a piano" className="w-full text-sm p-2 rounded-md focus:outline-none focus:ring-2" style={{backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', '--tw-ring-color': 'var(--accent-primary)'} as React.CSSProperties}/>
                                            <button onClick={() => handleRefineOther(stem)} disabled={isSubSeparating[stem.id] || !otherRefinePrompt.trim()} className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-white font-semibold rounded-lg transition-colors" style={{backgroundColor: 'var(--special-ai-suggestion)'}}><Wand className="w-4 h-4" />{isSubSeparating[stem.id] ? 'Refining...' : 'Refine with AI'}</button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )}
      </div>
    </div>
  );
};