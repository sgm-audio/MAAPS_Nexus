
import React, { useEffect, useRef, useState } from 'react';
import { useLiveConversation } from '../hooks/useLiveConversation';
import { Bot, Mic, StopCircle, User } from './icons';
import { AudioControls } from './AudioControls';
import { AudioVisualizer } from './AudioVisualizer';

export const LiveConversation: React.FC = () => {
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);

  const {
    isConnected,
    isConnecting,
    error,
    transcription,
    startConversation,
    stopConversation,
    isSpeaking,
    analyserNode,
  } = useLiveConversation(volume, playbackRate);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcription]);

  return (
    <div className="flex flex-col h-full max-h-[85vh] rounded-lg overflow-hidden border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
      <div className="p-4 border-b space-y-3" style={{ borderColor: 'var(--border-primary)' }}>
        <div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--text-accent)' }}>Live Conversation</h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Talk with your AI mixing partner in real-time.
          </p>
        </div>
        
        <div className="h-10 flex items-center justify-center rounded-lg" style={{ backgroundColor: 'var(--bg-primary)' }}>
            {isSpeaking && analyserNode ? (
                <AudioVisualizer analyserNode={analyserNode} />
            ) : (
                <div className="w-full h-full border-2 border-dashed rounded-md flex items-center justify-center" style={{ borderColor: 'var(--border-primary)' }}>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>AI Voice Activity</p>
                </div>
            )}
        </div>

        <AudioControls 
            volume={volume}
            onVolumeChange={setVolume}
            playbackRate={playbackRate}
            onPlaybackRateChange={setPlaybackRate}
        />
      </div>

      <div ref={scrollRef} className="flex-1 p-4 space-y-4 overflow-y-auto">
        {transcription.length === 0 && !isConnecting && !isConnected &&(
            <div className="flex flex-col items-center justify-center h-full" style={{ color: 'var(--text-muted)' }}>
                <Mic className="w-16 h-16 mb-4"/>
                <p>Click "Start Conversation" to begin.</p>
            </div>
        )}
        {transcription.map((entry) => (
          <div
            key={entry.id}
            className={`flex items-start gap-3 ${
              entry.source === 'user' ? 'justify-end' : ''
            }`}
          >
            {entry.source === 'ai' && (
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--accent-primary)', opacity: '0.2' }}>
                <Bot className="w-5 h-5" style={{ color: 'var(--accent-primary)' }} />
              </div>
            )}
            <div
              className={`max-w-md p-3 rounded-lg`}
              style={{
                backgroundColor: entry.source === 'user' ? 'var(--special-user-message-bg)' : 'var(--bg-tertiary)',
                color: entry.source === 'user' ? 'var(--special-user-message-text)' : 'var(--text-primary)',
              }}
            >
              <p>{entry.text}</p>
            </div>
             {entry.source === 'user' && (
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--special-user-message-bg)', opacity: '0.2'}}>
                <User className="w-5 h-5" style={{ color: 'var(--special-user-message-bg)' }} />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="p-4 border-t" style={{ borderColor: 'var(--border-primary)', backgroundColor: 'var(--bg-primary)' }}>
        {error && <p className="text-center mb-2" style={{color: 'var(--special-negative)'}}>{error}</p>}
        {!isConnected ? (
          <button
            onClick={startConversation}
            disabled={isConnecting}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 font-semibold rounded-lg transition-colors"
            style={{ 
                backgroundColor: 'var(--accent-primary)', 
                color: 'var(--bg-primary)',
            }}
          >
            <Mic className="w-5 h-5" />
            {isConnecting ? 'Connecting...' : 'Start Conversation'}
          </button>
        ) : (
          <button
            onClick={stopConversation}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 text-white font-semibold rounded-lg transition-colors"
            style={{ backgroundColor: 'var(--special-negative)' }}
          >
            <StopCircle className="w-5 h-5" />
            Stop Conversation
          </button>
        )}
      </div>
    </div>
  );
};
