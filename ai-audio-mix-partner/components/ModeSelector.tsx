
import React from 'react';
import { AIMode } from '../types';
import { Bot, BrainCircuit, Live, Search, Sparkles, Image, Music, Plug } from './icons';

interface ModeSelectorProps {
  currentMode: AIMode;
  onModeChange: (mode: AIMode) => void;
}

const modes = [
  { id: AIMode.Live, label: 'Live Conversation', Icon: Live },
  { id: AIMode.Image, label: 'Image Generation', Icon: Image },
  { id: AIMode.StemSeparation, label: 'Stem Separation', Icon: Music },
  { id: AIMode.PluginBridge, label: 'Plugin Bridge', Icon: Plug },
  { id: AIMode.Chat, label: 'Chat Bot', Icon: Bot },
  { id: AIMode.Grounded, label: 'Grounded Search', Icon: Search },
  { id: AIMode.Complex, label: 'Deep Analysis', Icon: BrainCircuit },
  { id: AIMode.Fast, label: 'Quick Tips', Icon: Sparkles },
];

export const ModeSelector: React.FC<ModeSelectorProps> = ({ currentMode, onModeChange }) => {
  return (
    <nav className="flex md:flex-col gap-2">
      {modes.map(({ id, label, Icon }) => {
        const isActive = currentMode === id;
        return (
          <button
            key={id}
            onClick={() => onModeChange(id)}
            className={`flex items-center gap-3 p-3 rounded-lg text-sm font-medium transition-colors w-full text-left`}
            style={{
                backgroundColor: isActive ? 'var(--accent-primary)' : 'transparent',
                color: isActive ? 'var(--bg-primary)' : 'var(--text-secondary)',
            }}
            onMouseOver={(e) => {
              if (!isActive) {
                e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }
            }}
            onMouseOut={(e) => {
              if (!isActive) {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }
            }}
        >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <span className="hidden md:inline">{label}</span>
        </button>
        )
      })}
    </nav>
  );
};
