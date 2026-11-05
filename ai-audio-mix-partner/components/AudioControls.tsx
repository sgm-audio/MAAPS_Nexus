
import React from 'react';
import { Volume1, Volume2, VolumeX } from './icons';

interface AudioControlsProps {
    volume: number;
    onVolumeChange: (volume: number) => void;
    playbackRate: number;
    onPlaybackRateChange: (rate: number) => void;
}

const playbackRates = [0.75, 1, 1.5];

export const AudioControls: React.FC<AudioControlsProps> = ({
    volume,
    onVolumeChange,
    playbackRate,
    onPlaybackRateChange,
}) => {
    
    const VolumeIcon = volume === 0 ? VolumeX : volume < 0.5 ? Volume1 : Volume2;

    return (
        <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 flex-1">
                <label htmlFor="volume" title="Volume" style={{ color: 'var(--text-muted)' }}>
                    <VolumeIcon className="w-5 h-5" />
                </label>
                <input
                    id="volume"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={volume}
                    onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                    style={{ backgroundColor: 'var(--bg-tertiary)', accentColor: 'var(--accent-primary)' }}
                />
            </div>
            <div className="flex items-center gap-2">
                <span style={{ color: 'var(--text-muted)' }}>Speed:</span>
                <div className="flex items-center rounded-md" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    {playbackRates.map(rate => (
                        <button
                            key={rate}
                            onClick={() => onPlaybackRateChange(rate)}
                            className={`px-2 py-1 text-xs font-semibold rounded-md transition-colors`}
                            style={{
                                backgroundColor: playbackRate === rate ? 'var(--accent-primary)' : 'transparent',
                                color: playbackRate === rate ? 'var(--bg-primary)' : 'var(--text-secondary)'
                            }}
                        >
                            {rate}x
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};
