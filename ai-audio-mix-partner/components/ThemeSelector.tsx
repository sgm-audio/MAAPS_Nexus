import React from 'react';
import { Theme } from '../types';
import { Palette } from './icons';

interface ThemeSelectorProps {
  currentTheme: Theme;
  onThemeChange: (theme: Theme) => void;
}

const themes: { id: Theme; label: string }[] = [
  { id: 'high-contrast', label: 'High Contrast' },
  { id: 'modern-black', label: 'Modern Black' },
  { id: 'studio-light', label: 'Studio Light' },
  { id: 'vintage-warm', label: 'Vintage Warm' },
  { id: 'neon-drive', label: 'Neon Drive' },
  { id: 'arctic-blue', label: 'Arctic Blue' },
  { id: 'forest-green', label: 'Forest Green' },
];

export const ThemeSelector: React.FC<ThemeSelectorProps> = ({ currentTheme, onThemeChange }) => {
  return (
    <div className="mt-4">
      <label htmlFor="theme-select" className="flex items-center gap-2 text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
        <Palette className="w-5 h-5" />
        <span className="hidden md:inline">Theme</span>
      </label>
      <select
        id="theme-select"
        value={currentTheme}
        onChange={(e) => onThemeChange(e.target.value as Theme)}
        className="w-full p-2 rounded-lg text-sm border transition-colors focus:outline-none focus:ring-2"
        style={{
          backgroundColor: 'var(--bg-tertiary)',
          color: 'var(--text-primary)',
          borderColor: 'var(--border-primary)',
          // FIX: Replaced invalid 'ringColor' property with '--tw-ring-color' CSS variable for Tailwind's focus ring.
          '--tw-ring-color': 'var(--accent-primary)',
        }}
      >
        {themes.map(({ id, label }) => (
          <option key={id} value={id}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );
};
