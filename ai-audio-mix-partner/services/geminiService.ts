
import { GoogleGenAI, GenerateContentResponse, Modality } from "@google/genai";
import { StemResult } from "../types";

// Assume process.env.API_KEY is available
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export async function generateStandardResponse(prompt: string): Promise<GenerateContentResponse> {
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
  });
  return response;
}

export async function generateFastResponse(prompt: string): Promise<GenerateContentResponse> {
  const response = await ai.models.generateContent({
    model: 'gemini-flash-lite-latest',
    contents: prompt,
  });
  return response;
}

export async function generateGroundedResponse(prompt: string): Promise<GenerateContentResponse> {
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
    config: {
      tools: [{ googleSearch: {} }],
    },
  });
  return response;
}

export async function generateComplexResponse(prompt: string): Promise<GenerateContentResponse> {
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-pro',
    contents: prompt,
    config: {
      thinkingConfig: { thinkingBudget: 32768 },
    },
  });
  return response;
}

export async function generateSpeech(text: string): Promise<string | undefined> {
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash-preview-tts",
    contents: [{ parts: [{ text: `Say this clearly: ${text}` }] }],
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: {
        voiceConfig: {
          prebuiltVoiceConfig: { voiceName: 'Kore' },
        },
      },
    },
  });
  const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
  return base64Audio;
}

export async function generateImage(prompt: string): Promise<string> {
  const response = await ai.models.generateImages({
    model: 'imagen-4.0-generate-001',
    prompt: prompt,
    config: {
      numberOfImages: 1,
      outputMimeType: 'image/jpeg',
      aspectRatio: '1:1',
    },
  });

  const base64ImageBytes: string = response.generatedImages[0].image.imageBytes;
  return base64ImageBytes;
}

// Helper function to create a silent WAV blob for mocking stem separation
const createSilentWav = (durationSeconds: number): Blob => {
  const sampleRate = 44100;
  const numChannels = 1;
  const bytesPerSample = 2;
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = Math.floor(durationSeconds * byteRate);

  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  // RIFF header
  view.setUint32(0, 0x52494646, false); // "RIFF"
  view.setUint32(4, 36 + dataSize, true);
  view.setUint32(8, 0x57415645, false); // "WAVE"

  // "fmt " sub-chunk
  view.setUint32(12, 0x666d7420, false); // "fmt "
  view.setUint32(16, 16, true); // Sub-chunk size
  view.setUint16(20, 1, true); // Audio format (1 = PCM)
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bytesPerSample * 8, true);

  // "data" sub-chunk
  view.setUint32(36, 0x64617461, false); // "data"
  view.setUint32(40, dataSize, true);
  
  // Audio data (silence) is already all zeros
  return new Blob([view], { type: 'audio/wav' });
};

const defaultMixerState = {
    solo: false,
    mute: false,
    volume: 0.7,
    pan: 0,
    eq: [0, 0, 0] as [number, number, number],
};


// Mock function to simulate INITIAL stem separation
export async function separateInitialStems(file: File): Promise<StemResult[]> {
  console.log(`Simulating initial stem separation for: ${file.name}`);
  await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 2000));
  
  const stems = [
    { id: `stem-${Date.now()}-1`, name: 'Vocals', url: URL.createObjectURL(createSilentWav(5)), isSeparable: false, ...defaultMixerState },
    { id: `stem-${Date.now()}-2`, name: 'Bass', url: URL.createObjectURL(createSilentWav(5)), isSeparable: false, ...defaultMixerState },
    { id: `stem-${Date.now()}-3`, name: 'Drums', url: URL.createObjectURL(createSilentWav(5)), isSeparable: true, ...defaultMixerState },
    { id: `stem-${Date.now()}-4`, name: 'Other', url: URL.createObjectURL(createSilentWav(5)), isSeparable: true, ...defaultMixerState },
  ];
  
  return stems;
}

// Mock function to simulate SUB stem separation for Drums
export async function separateSubStems(parentStemName: string): Promise<StemResult[]> {
    console.log(`Simulating sub-stem separation for: ${parentStemName}`);
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1500));

    let subStems: Omit<StemResult, 'id' | 'url'>[] = [];

    if (parentStemName === 'Drums') {
        subStems = [
            { name: 'Kick', isSeparable: false, parentName: 'Drums', ...defaultMixerState },
            { name: 'Snare', isSeparable: false, parentName: 'Drums', ...defaultMixerState },
            { name: 'Hi-Hats', isSeparable: false, parentName: 'Drums', ...defaultMixerState },
            { name: 'Cymbals', isSeparable: false, parentName: 'Drums', ...defaultMixerState },
        ];
    }

    return subStems.map(stem => ({
        ...stem,
        id: `substem-${Date.now()}-${Math.random()}`,
        url: URL.createObjectURL(createSilentWav(5)),
    }));
}

// Mock function to simulate AI-guided refinement of "Other" stem
export async function refineOtherStem(prompt: string): Promise<StemResult[]> {
    console.log(`Simulating AI-guided refinement for "Other" with prompt: ${prompt}`);
    await new Promise(resolve => setTimeout(resolve, 2500 + Math.random() * 2000));
    
    // Simple mock logic: create stems based on keywords in the prompt
    const instrumentNames = prompt.toLowerCase().match(/[a-zA-Z]+/g) || ['Instrument'];
    const uniqueInstruments = [...new Set(instrumentNames.filter(name => name.length > 2 && name !== 'and'))];

    return uniqueInstruments.map((name, index) => {
        const capitalizedName = name.charAt(0).toUpperCase() + name.slice(1);
        return {
            name: `${capitalizedName}`,
            isSeparable: false,
            parentName: 'Other',
            ...defaultMixerState,
            id: `substem-${Date.now()}-${index}`,
            url: URL.createObjectURL(createSilentWav(5)),
        };
    });
}

// Mock function to simulate an AI suggesting a mix
export async function suggestMix(stems: StemResult[]): Promise<StemResult[]> {
    console.log("Simulating AI mix suggestions...");
    await new Promise(resolve => setTimeout(resolve, 1500));

    return stems.map(stem => {
        const newStem = { ...stem };
        const name = stem.name.toLowerCase();

        if (name.includes('vocal')) {
            newStem.volume = 0.9;
            newStem.pan = 0;
            newStem.eq = [-0.1, 0.2, 0.3]; // Cut lows, boost mid/high
        } else if (name.includes('bass')) {
            newStem.volume = 0.8;
            newStem.pan = 0;
            newStem.eq = [0.4, -0.2, -0.1]; // Boost low, cut mid
        } else if (name.includes('drum') || name.includes('kick') || name.includes('snare')) {
            newStem.volume = 0.85;
            newStem.pan = 0;
            newStem.eq = [0.1, 0, 0.2]; // Smile curve
        } else if (name.includes('hat') || name.includes('cymbal')) {
            newStem.volume = 0.6;
            newStem.pan = Math.random() * 0.6 - 0.3; // Slight pan
            newStem.eq = [-0.5, 0.1, 0.4]; // Cut lows, boost highs
        } else if (stems.filter(s => s.parentName === 'Other').length > 1) {
            // Pan refined "Other" stems for width
             newStem.volume = 0.65;
             newStem.pan = stems.indexOf(stem) % 2 === 0 ? -0.5 : 0.5;
             newStem.eq = [-0.2, 0, 0]; // Cut some lows
        } else {
            newStem.volume = 0.7;
            newStem.pan = 0;
        }

        return newStem;
    });
}
