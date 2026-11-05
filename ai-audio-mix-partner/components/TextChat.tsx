
import React, { useState, useRef, useEffect } from 'react';
import { GenerateContentResponse } from '@google/genai';
import { Message } from '../types';
import { Bot, Link, Send, User, Volume2 } from './icons';
import { generateSpeech } from '../services/geminiService';
import { decode, decodeAudioData } from '../services/audioUtils';
import { AudioControls } from './AudioControls';
import { AudioVisualizer } from './AudioVisualizer';

interface TextChatProps {
  title: string;
  description: string;
  placeholder: string;
  apiCall: (prompt: string) => Promise<GenerateContentResponse>;
  Icon: React.ElementType;
}

export const TextChat: React.FC<TextChatProps> = ({ title, description, placeholder, apiCall, Icon }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);


  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = volume;
    }
  }, [volume]);
  
  const playAudio = async (text: string, messageId: string) => {
    try {
        const base64Audio = await generateSpeech(text);
        if (base64Audio) {
            if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
                // FIX: Cast window to any to support webkitAudioContext for older browsers.
                const newAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({sampleRate: 24000});
                audioContextRef.current = newAudioContext;
                const newGainNode = newAudioContext.createGain();
                gainNodeRef.current = newGainNode;
            }
            const audioContext = audioContextRef.current;
            const gainNode = gainNodeRef.current;
            
            if(!gainNode) return;

            gainNode.disconnect();
            
            const analyser = audioContext.createAnalyser();
            analyserRef.current = analyser;

            gainNode.gain.value = volume;
            gainNode.connect(analyser);
            analyser.connect(audioContext.destination);
            
            const audioBuffer = await decodeAudioData(decode(base64Audio), audioContext, 24000, 1);
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.playbackRate.value = playbackRate;
            source.connect(gainNode);
            source.start();
            setPlayingMessageId(messageId);

            source.onended = () => {
                setPlayingMessageId(null);
            };
        }
    } catch (e) {
        console.error("Failed to play audio", e);
        setPlayingMessageId(null);
    }
  };


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: `user-${Date.now()}`, text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiCall(input);
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        text: response.text,
        sender: 'ai',
        groundingChunks: response.candidates?.[0]?.groundingMetadata?.groundingChunks,
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(errorMessage);
       const aiError: Message = {
        id: `ai-error-${Date.now()}`,
        text: `Sorry, I encountered an error: ${errorMessage}`,
        sender: 'ai',
      };
      setMessages(prev => [...prev, aiError]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[85vh] rounded-lg overflow-hidden border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
      <div className="p-4 border-b space-y-3" style={{ borderColor: 'var(--border-primary)' }}>
        <div>
            <h2 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--text-accent)' }}>
                <Icon className="w-6 h-6"/> {title}
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{description}</p>
        </div>
        <AudioControls 
            volume={volume}
            onVolumeChange={setVolume}
            playbackRate={playbackRate}
            onPlaybackRateChange={setPlaybackRate}
        />
      </div>

      <div ref={scrollRef} className="flex-1 p-4 space-y-4 overflow-y-auto">
         {messages.length === 0 && (
             <div className="flex flex-col items-center justify-center h-full" style={{ color: 'var(--text-muted)' }}>
                <Icon className="w-16 h-16 mb-4"/>
                <p>Ask me anything!</p>
            </div>
         )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
            {msg.sender === 'ai' && (
               <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--accent-primary)', opacity: '0.2' }}>
                <Bot className="w-5 h-5" style={{ color: 'var(--accent-primary)' }} />
              </div>
            )}
            <div className={`max-w-xl p-3 rounded-lg`} style={{
                 backgroundColor: msg.sender === 'user' ? 'var(--special-user-message-bg)' : 'var(--bg-tertiary)',
                 color: msg.sender === 'user' ? 'var(--special-user-message-text)' : 'var(--text-primary)',
            }}>
              <div className="prose prose-invert prose-sm" dangerouslySetInnerHTML={{ __html: msg.text.replace(/\n/g, '<br/>') }}/>
              
              {msg.groundingChunks && msg.groundingChunks.length > 0 && (
                  <div className="mt-3 pt-3 border-t" style={{borderColor: 'var(--border-primary)'}}>
                      <h4 className="text-xs font-semibold mb-2" style={{color: 'var(--text-muted)'}}>Sources:</h4>
                      <div className="flex flex-wrap gap-2">
                          {msg.groundingChunks.map((chunk, index) => (
                              <a href={chunk.web?.uri} key={index} target="_blank" rel="noopener noreferrer" 
                                className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full transition-colors"
                                style={{ backgroundColor: 'var(--bg-interactive)', color: 'var(--text-accent)' }}
                                >
                                  <Link className="w-3 h-3"/>
                                  <span>{chunk.web?.title || new URL(chunk.web.uri).hostname}</span>
                              </a>
                          ))}
                      </div>
                  </div>
              )}
               {msg.sender === 'ai' && (
                <div className="mt-2 h-10 flex items-center">
                    {playingMessageId === msg.id && analyserRef.current ? (
                        <AudioVisualizer analyserNode={analyserRef.current} />
                    ) : (
                        <button title="Play audio" onClick={() => playAudio(msg.text, msg.id)} className="transition-colors p-1 rounded-full" style={{ color: 'var(--text-accent)'}}>
                            <Volume2 className="w-5 h-5" />
                        </button>
                    )}
                 </div>
               )}
            </div>
            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--special-user-message-bg)', opacity: '0.2'}}>
                <User className="w-5 h-5" style={{ color: 'var(--special-user-message-bg)' }} />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--accent-primary)', opacity: '0.2' }}>
                    <Bot className="w-5 h-5 text-cyan-300 animate-pulse" style={{ color: 'var(--accent-primary)' }}/>
                </div>
                <div className="max-w-xl p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-tertiary)'}}>
                    <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 rounded-full animate-bounce [animation-delay:-0.3s]" style={{ backgroundColor: 'var(--accent-primary)' }}></div>
                        <div className="w-2 h-2 rounded-full animate-bounce [animation-delay:-0.15s]" style={{ backgroundColor: 'var(--accent-primary)' }}></div>
                        <div className="w-2 h-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--accent-primary)' }}></div>
                    </div>
                </div>
            </div>
        )}
        {error && <p className="text-center" style={{color: 'var(--special-negative)'}}>{error}</p>}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t" style={{ borderColor: 'var(--border-primary)', backgroundColor: 'var(--bg-primary)' }}>
        <div className="flex items-center gap-2 rounded-lg p-1" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            className="flex-1 bg-transparent p-2 focus:outline-none"
            style={{ color: 'var(--text-primary)' }}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 rounded-md transition-colors"
            style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)'}}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
};
