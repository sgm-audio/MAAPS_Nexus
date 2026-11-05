
import React, { useState, useEffect } from 'react';
import { LiveConversation } from './components/LiveConversation';
import { TextChat } from './components/TextChat';
import { ModeSelector } from './components/ModeSelector';
import * as geminiService from './services/geminiService';
import { AIMode, Theme } from './types';
import { Bot, BrainCircuit, Headphones, Image as ImageIcon, Music, Search, Sparkles, Plug } from './components/icons';
import { ImageGenerator } from './components/ImageGenerator';
import { StemSeparator } from './components/StemSeparator';
import { PluginBridge } from './components/PluginBridge';
import { ThemeSelector } from './components/ThemeSelector';

const App: React.FC = () => {
  const [mode, setMode] = useState<AIMode>(AIMode.Live);
  const [theme, setTheme] = useState<Theme>('high-contrast');

  useEffect(() => {
    document.body.style.backgroundColor = `var(--bg-primary)`;
    document.body.style.color = `var(--text-primary)`;
    document.body.dataset.theme = theme;
  }, [theme]);

  const renderContent = () => {
    switch (mode) {
      case AIMode.Live:
        return <LiveConversation />;
      case AIMode.Image:
        return <ImageGenerator />;
      case AIMode.StemSeparation:
        return <StemSeparator />;
      case AIMode.PluginBridge:
        return <PluginBridge />;
      case AIMode.Chat:
        return (
          <TextChat
            title="Chat Bot"
            description="Ask general questions and get fast responses from Gemini Flash."
            placeholder="e.g., What is a compressor?"
            apiCall={geminiService.generateStandardResponse}
            Icon={Bot}
          />
        );
      case AIMode.Grounded:
        return (
          <TextChat
            title="Grounded Search"
            description="Ask about recent trends or up-to-date information, grounded in Google Search."
            placeholder="e.g., What are the latest vocal mixing trends in 2024?"
            apiCall={geminiService.generateGroundedResponse}
            Icon={Search}
          />
        );
      case AIMode.Complex:
        return (
          <TextChat
            title="Deep Analysis"
            description="For your most complex queries. Gemini Pro will use its thinking budget to provide in-depth answers."
            placeholder="e.g., Explain the physics of room acoustics for a small studio."
            apiCall={geminiService.generateComplexResponse}
            Icon={BrainCircuit}
          />
        );
      case AIMode.Fast:
        return (
          <TextChat
            title="Quick Tips"
            description="Get ultra-fast, low-latency responses from Gemini Flash Lite."
            placeholder="e.g., Give me a quick tip for mixing bass."
            apiCall={geminiService.generateFastResponse}
            Icon={Sparkles}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen font-sans flex flex-col md:flex-row" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)'}}>
      <header className="md:hidden flex items-center justify-between p-4 border-b" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
        <div className="flex items-center gap-2">
          <Headphones className="w-8 h-8" style={{ color: 'var(--accent-primary)' }} />
          <h1 className="text-xl font-bold tracking-tighter">AI Mix Partner</h1>
        </div>
      </header>
      <aside className="w-full md:w-64 p-4 flex-shrink-0 border-r-0 md:border-r" style={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-primary)' }}>
         <div className="hidden md:flex items-center gap-3 mb-8">
            <Headphones className="w-10 h-10" style={{ color: 'var(--accent-primary)' }}/>
            <h1 className="text-2xl font-bold tracking-tighter">AI Mix Partner</h1>
        </div>
        <div className="flex flex-col h-full justify-between">
            <ModeSelector currentMode={mode} onModeChange={setMode} />
            <ThemeSelector currentTheme={theme} onThemeChange={setTheme} />
        </div>
      </aside>
      <main className="flex-1 p-4 md:p-6 overflow-auto">
        {renderContent()}
      </main>
    </div>
  );
};

export default App;
