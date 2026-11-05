
import { ReactNode } from 'react';
import { GroundingChunk } from "@google/genai";

export enum AIMode {
  Live = 'live',
  Image = 'image',
  Chat = 'chat',
  Grounded = 'grounded',
  Complex = 'complex',
  Fast = 'fast',
  StemSeparation = 'stemSeparation',
  PluginBridge = 'pluginBridge',
  Theme = 'theme'
}

export type Theme = 'high-contrast' | 'modern-black' | 'studio-light' | 'vintage-warm' | 'neon-drive' | 'arctic-blue' | 'forest-green';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  groundingChunks?: GroundingChunk[];
}

export interface TranscriptionEntry {
  id: string;
  text: string;
  source: 'user' | 'ai';
}

export interface StemResult {
  id: string;
  name: string;
  url: string;
  parentName?: string;
  isSeparable: boolean;
  // Mixer controls
  solo: boolean;
  mute: boolean;
  volume: number;
  pan: number; // -1 (left) to 1 (right)
  eq: [number, number, number]; // [Low, Mid, High] gains, e.g., -1 to 1
}
