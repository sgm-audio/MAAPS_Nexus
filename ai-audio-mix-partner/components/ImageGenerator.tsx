
import React, { useState } from 'react';
import { generateImage } from '../services/geminiService';
import { Image as ImageIcon, Sparkles, Send } from './icons';

export const ImageGenerator: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setImageUrl(null);

    try {
      const base64Data = await generateImage(prompt);
      setImageUrl(`data:image/jpeg;base64,${base64Data}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[85vh] rounded-lg overflow-hidden border" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--border-primary)' }}>
        <h2 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--text-accent)' }}>
          <ImageIcon className="w-6 h-6" /> Image Generation
        </h2>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Create stunning visuals with Imagen. Describe what you want to see.</p>
      </div>

      <div className="flex-1 p-4 flex items-center justify-center">
        <div className="w-full max-w-md aspect-square rounded-lg flex items-center justify-center overflow-hidden" style={{ backgroundColor: 'var(--bg-primary)' }}>
          {isLoading && (
            <div className="flex flex-col items-center" style={{ color: 'var(--text-accent)' }}>
              <Sparkles className="w-16 h-16 animate-pulse" />
              <p className="mt-2 text-lg font-semibold">Generating...</p>
            </div>
          )}
          {error && (
            <div className="p-4 text-center" style={{ color: 'var(--special-negative)' }}>
              <p>Sorry, something went wrong:</p>
              <p className="text-sm mt-2 font-mono">{error}</p>
            </div>
          )}
          {!isLoading && !error && imageUrl && (
            <img src={imageUrl} alt={prompt} className="w-full h-full object-cover" />
          )}
          {!isLoading && !error && !imageUrl && (
            <div className="text-center" style={{ color: 'var(--text-muted)' }}>
              <ImageIcon className="w-24 h-24 mx-auto" />
              <p className="mt-2">Your generated image will appear here.</p>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t" style={{ borderColor: 'var(--border-primary)', backgroundColor: 'var(--bg-primary)' }}>
        <div className="flex items-center gap-2 rounded-lg p-1" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., A vintage microphone in a futuristic recording studio"
            className="flex-1 bg-transparent p-2 focus:outline-none"
             style={{ color: 'var(--text-primary)' }}
          />
          <button
            type="submit"
            disabled={isLoading || !prompt.trim()}
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
