
import { useState, useRef, useCallback, useEffect } from 'react';
// FIX: Removed 'LiveSession' from import as it is not an exported member of '@google/genai'.
import { GoogleGenAI, LiveServerMessage, Modality, Blob } from "@google/genai";
// FIX: Import 'createBlob' for efficient audio processing and remove unused 'encode'.
import { decode, decodeAudioData, createBlob } from '../services/audioUtils';
import { TranscriptionEntry } from '../types';

export const useLiveConversation = (volume: number, playbackRate: number) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [transcription, setTranscription] = useState<TranscriptionEntry[]>([]);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);

    // FIX: Replaced 'LiveSession' with 'any' because it is an internal, unexported type.
    const sessionPromiseRef = useRef<Promise<any> | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
    const outputAudioContextRef = useRef<AudioContext | null>(null);
    const gainNodeRef = useRef<GainNode | null>(null);
    const nextStartTimeRef = useRef<number>(0);
    const sourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());

    const currentInputTranscriptionRef = useRef('');
    const currentOutputTranscriptionRef = useRef('');
    const playbackRateRef = useRef(playbackRate);

    useEffect(() => {
        playbackRateRef.current = playbackRate;
    }, [playbackRate]);

    useEffect(() => {
        if (gainNodeRef.current) {
            gainNodeRef.current.gain.value = volume;
        }
    }, [volume]);


    const stopConversation = useCallback(() => {
        if (sessionPromiseRef.current) {
            sessionPromiseRef.current.then(session => session.close());
            sessionPromiseRef.current = null;
        }

        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => track.stop());
            mediaStreamRef.current = null;
        }

        if (scriptProcessorRef.current) {
            scriptProcessorRef.current.disconnect();
            scriptProcessorRef.current = null;
        }

        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        
        if (outputAudioContextRef.current) {
            outputAudioContextRef.current.close();
            outputAudioContextRef.current = null;
        }
        
        gainNodeRef.current = null;

        for (const source of sourcesRef.current.values()) {
            source.stop();
        }
        sourcesRef.current.clear();

        setIsConnected(false);
        setIsConnecting(false);
        setIsSpeaking(false);
        setAnalyserNode(null);

    }, []);

    const startConversation = useCallback(async () => {
        setIsConnecting(true);
        setError(null);
        setTranscription([]);
        currentInputTranscriptionRef.current = '';
        currentOutputTranscriptionRef.current = '';

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;

            // Setup input
            // FIX: Cast window to any to support webkitAudioContext for older browsers.
            const inputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
            audioContextRef.current = inputAudioContext;

            // Setup output
            // FIX: Cast window to any to support webkitAudioContext for older browsers.
            const outputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
            outputAudioContextRef.current = outputAudioContext;
            const outputNode = outputAudioContext.createGain();
            outputNode.gain.value = volume;
            gainNodeRef.current = outputNode;

            const analyser = outputAudioContext.createAnalyser();
            setAnalyserNode(analyser);

            outputNode.connect(analyser);
            analyser.connect(outputAudioContext.destination);

            nextStartTimeRef.current = 0;


            const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
            sessionPromiseRef.current = ai.live.connect({
                // FIX: Updated model to 'gemini-2.5-flash-native-audio-preview-09-2025' for real-time audio conversations as per guidelines.
                model: 'gemini-2.5-flash-native-audio-preview-09-2025',
                callbacks: {
                    onopen: () => {
                        setIsConnecting(false);
                        setIsConnected(true);

                        const source = inputAudioContext.createMediaStreamSource(stream);
                        const scriptProcessor = inputAudioContext.createScriptProcessor(4096, 1, 1);
                        scriptProcessorRef.current = scriptProcessor;

                        scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
                            const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
                            // FIX: Switched to using the 'createBlob' utility for more efficient audio data processing, following Gemini API guidelines.
                            const pcmBlob: Blob = createBlob(inputData);
                            if (sessionPromiseRef.current) {
                                sessionPromiseRef.current.then((session) => {
                                    session.sendRealtimeInput({ media: pcmBlob });
                                });
                            }
                        };
                        source.connect(scriptProcessor);
                        scriptProcessor.connect(inputAudioContext.destination);
                    },
                    onmessage: async (message: LiveServerMessage) => {
                        // Handle audio output
                        const base64EncodedAudioString = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
                        if (base64EncodedAudioString && outputAudioContextRef.current) {
                            setIsSpeaking(true);
                            nextStartTimeRef.current = Math.max(nextStartTimeRef.current, outputAudioContextRef.current.currentTime);
                            const audioBuffer = await decodeAudioData(decode(base64EncodedAudioString), outputAudioContextRef.current, 24000, 1);
                            const source = outputAudioContextRef.current.createBufferSource();
                            source.buffer = audioBuffer;
                            source.playbackRate.value = playbackRateRef.current;
                            source.connect(outputNode);
                            source.addEventListener('ended', () => {
                                sourcesRef.current.delete(source);
                                if (sourcesRef.current.size === 0) {
                                    setIsSpeaking(false);
                                }
                            });
                            source.start(nextStartTimeRef.current);
                            nextStartTimeRef.current += audioBuffer.duration / playbackRateRef.current;
                            sourcesRef.current.add(source);
                        }

                        // Handle transcription
                        if (message.serverContent?.inputTranscription) {
                            currentInputTranscriptionRef.current += message.serverContent.inputTranscription.text;
                        }
                        if (message.serverContent?.outputTranscription) {
                            currentOutputTranscriptionRef.current += message.serverContent.outputTranscription.text;
                        }

                        if (message.serverContent?.turnComplete) {
                            const userInput = currentInputTranscriptionRef.current.trim();
                            const aiResponse = currentOutputTranscriptionRef.current.trim();
                            
                            const newEntries: TranscriptionEntry[] = [];
                            if (userInput) {
                                newEntries.push({ id: `user-${Date.now()}`, text: userInput, source: 'user' });
                            }
                             if (aiResponse) {
                                newEntries.push({ id: `ai-${Date.now()}`, text: aiResponse, source: 'ai' });
                            }

                            if(newEntries.length > 0) {
                                setTranscription(prev => [...prev, ...newEntries]);
                            }

                            currentInputTranscriptionRef.current = '';
                            currentOutputTranscriptionRef.current = '';
                        }
                        
                        // Handle interruption
                        if (message.serverContent?.interrupted) {
                            for (const source of sourcesRef.current.values()) {
                                source.stop();
                            }
                            sourcesRef.current.clear();
                            nextStartTimeRef.current = 0;
                            setIsSpeaking(false);
                        }
                    },
                    onerror: (e: ErrorEvent) => {
                        setError(`An error occurred: ${e.message}`);
                        stopConversation();
                    },
                    onclose: (e: CloseEvent) => {
                        stopConversation();
                    },
                },
                config: {
                    responseModalities: [Modality.AUDIO],
                    speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } } },
                    systemInstruction: 'You are a friendly and helpful audio engineer. Provide clear, concise, and actionable advice. Keep your responses conversational.',
                    inputAudioTranscription: {},
                    outputAudioTranscription: {},
                },
            });

        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : 'Failed to start microphone.');
            setIsConnecting(false);
        }

    }, [stopConversation, volume]);

    return {
        isConnected,
        isConnecting,
        error,
        transcription,
        startConversation,
        stopConversation,
        isSpeaking,
        analyserNode,
    };
};
