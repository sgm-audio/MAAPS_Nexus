# AI Mix Partner Integration Guide

Complete guide to integrating the AI Mix Partner into your website.

---

## Table of Contents

1. [Quick Overview](#quick-overview)
2. [Integration Options](#integration-options)
3. [Option 1: Iframe Embed (Easiest)](#option-1-iframe-embed-easiest)
4. [Option 2: Direct React Integration](#option-2-direct-react-integration)
5. [Option 3: Build and Host Separately](#option-3-build-and-host-separately)
6. [Option 4: API-Only Integration](#option-4-api-only-integration)
7. [Customization Options](#customization-options)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

---

## Quick Overview

**AI Mix Partner** is a React + Vite application powered by Google Gemini AI that provides:

- 🎙️ **Live Audio Conversation** - Real-time voice chat with AI
- 💬 **Text Chat** - Standard text-based AI assistance
- 🖼️ **Image Generation** - AI-generated visual content
- 🎵 **Stem Separation** - Audio stem extraction
- 🔌 **Plugin Bridge** - DAW plugin integration
- 🔍 **Grounded Search** - Google Search-powered responses
- 🧠 **Deep Analysis** - Complex query processing
- ⚡ **Quick Tips** - Fast, low-latency responses

**Tech Stack:**
- React 19
- TypeScript
- Vite 6
- Google Gemini API

---

## Integration Options

| Option | Difficulty | Best For | Pros | Cons |
|--------|------------|----------|------|------|
| **Iframe Embed** | Easy | Quick integration | No code changes needed | Limited customization |
| **React Integration** | Medium | React/Next.js sites | Full customization | Requires build setup |
| **Separate Hosting** | Medium | Any framework | Complete control | Separate deployment |
| **API Only** | Hard | Custom UI | Total flexibility | Need to build UI |

---

## Option 1: Iframe Embed (Easiest)

### Step 1: Build the AI Mix Partner

```bash
cd ai-audio-mix-partner

# Install dependencies
npm install

# Set your Gemini API key in .env.local
echo "GEMINI_API_KEY=your-api-key-here" > .env.local

# Build for production
npm run build
```

### Step 2: Deploy the Built Files

The build creates a `dist/` folder. Deploy this to:
- **Vercel/Netlify**: Drag and drop the `dist` folder
- **Your own server**: Upload to a subdomain (e.g., `https://mixer.yourdomain.com`)
- **GitHub Pages**: Push `dist/` contents to gh-pages branch

### Step 3: Embed in Your Website

**Basic Embed:**
```html
<iframe
  src="https://mixer.yourdomain.com"
  width="100%"
  height="800px"
  frameborder="0"
  allow="microphone"
  style="border: none; border-radius: 8px;"
></iframe>
```

**Responsive Embed:**
```html
<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden;">
  <iframe
    src="https://mixer.yourdomain.com"
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
    frameborder="0"
    allow="microphone"
  ></iframe>
</div>
```

**Modal/Popup Integration:**
```html
<button onclick="openMixPartner()">Open AI Mix Partner</button>

<div id="mixPartnerModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999;">
  <div style="position: relative; width: 90%; height: 90%; margin: 5% auto; background: white; border-radius: 8px; overflow: hidden;">
    <button onclick="closeMixPartner()" style="position: absolute; top: 10px; right: 10px; z-index: 10000;">Close</button>
    <iframe
      src="https://mixer.yourdomain.com"
      width="100%"
      height="100%"
      frameborder="0"
      allow="microphone"
    ></iframe>
  </div>
</div>

<script>
function openMixPartner() {
  document.getElementById('mixPartnerModal').style.display = 'block';
}
function closeMixPartner() {
  document.getElementById('mixPartnerModal').style.display = 'none';
}
</script>
```

**Pros:**
- ✅ Works with any website (WordPress, Wix, custom HTML)
- ✅ No code changes to your site
- ✅ Isolated environment (no conflicts)

**Cons:**
- ❌ Limited styling control
- ❌ Cross-origin communication needed for advanced features
- ❌ Requires separate deployment

---

## Option 2: Direct React Integration

For **React, Next.js, or Vite** projects.

### Step 1: Copy Source Files

```bash
# From your website project root
mkdir -p src/components/AIAudioMixPartner

# Copy AI Mix Partner source
cp -r ../ai-audio-mix-partner/components src/components/AIAudioMixPartner/
cp -r ../ai-audio-mix-partner/services src/components/AIAudioMixPartner/
cp -r ../ai-audio-mix-partner/hooks src/components/AIAudioMixPartner/
cp ../ai-audio-mix-partner/App.tsx src/components/AIAudioMixPartner/
cp ../ai-audio-mix-partner/types.ts src/components/AIAudioMixPartner/
```

### Step 2: Install Dependencies

```bash
npm install @google/genai
```

### Step 3: Set Environment Variable

**Create/Update `.env.local`:**
```bash
VITE_GEMINI_API_KEY=your-api-key-here
# or for Next.js:
NEXT_PUBLIC_GEMINI_API_KEY=your-api-key-here
```

### Step 4: Update Import Paths

Edit `src/components/AIAudioMixPartner/services/geminiService.ts`:

```typescript
// Change this line:
const apiKey = process.env.GEMINI_API_KEY;

// To (for Vite):
const apiKey = import.meta.env.VITE_GEMINI_API_KEY;

// Or (for Next.js):
const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;
```

### Step 5: Import and Use

**In your page component:**
```tsx
import AIAudioMixPartner from '@/components/AIAudioMixPartner/App';

export default function MixingPage() {
  return (
    <div>
      <h1>AI Mixing Assistant</h1>
      <AIAudioMixPartner />
    </div>
  );
}
```

**Embed in a specific section:**
```tsx
<section className="ai-mixer-section">
  <div className="container">
    <AIAudioMixPartner />
  </div>
</section>
```

**Pros:**
- ✅ Full control over styling and behavior
- ✅ Shared state with your application
- ✅ No separate deployment needed

**Cons:**
- ❌ Requires React framework
- ❌ Increases bundle size
- ❌ Need to manage dependencies

---

## Option 3: Build and Host Separately

Best for **non-React sites** that want to keep the AI Mix Partner separate.

### Step 1: Build Production Version

```bash
cd ai-audio-mix-partner

# Install dependencies
npm install

# Configure API key
echo "GEMINI_API_KEY=your-api-key-here" > .env.local

# Build for production
npm run build
```

This creates a `dist/` folder with optimized static files.

### Step 2: Deploy to Hosting

**Option A: Vercel (Recommended)**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd dist
vercel

# Follow prompts to deploy
```

**Option B: Netlify**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd dist
netlify deploy --prod

# Follow prompts
```

**Option C: Your Own Server**
```bash
# Upload dist/ contents to your server
scp -r dist/* user@yourserver.com:/var/www/mixer/

# Configure Nginx/Apache to serve from that directory
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name mixer.yourdomain.com;

    root /var/www/mixer;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Enable CORS if needed
    add_header Access-Control-Allow-Origin "https://yourdomain.com";
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
}
```

### Step 3: Link from Your Website

```html
<a href="https://mixer.yourdomain.com" target="_blank" class="mixer-button">
  Open AI Mix Partner
</a>
```

Or use iframe as shown in Option 1.

**Pros:**
- ✅ Works with any website technology
- ✅ Independent deployment and updates
- ✅ Can be used across multiple sites

**Cons:**
- ❌ Requires separate hosting
- ❌ Opens in new tab (unless using iframe)

---

## Option 4: API-Only Integration

Use the **Gemini AI API directly** and build your own UI.

### Step 1: Reference the Service Layer

Copy only the API service:
```bash
cp ai-audio-mix-partner/services/geminiService.ts src/services/
```

### Step 2: Install Gemini SDK

```bash
npm install @google/genai
```

### Step 3: Use in Your Code

```typescript
import * as geminiService from './services/geminiService';

// Text chat
async function askQuestion(question: string) {
  const response = await geminiService.generateStandardResponse(question);
  console.log(response);
}

// Live conversation (requires audio)
import { useLiveConversation } from './hooks/useLiveConversation';

function MyComponent() {
  const { isConnected, connect, disconnect, sendAudio } = useLiveConversation();

  return (
    <div>
      <button onClick={connect}>Start Conversation</button>
      {/* Your custom UI */}
    </div>
  );
}
```

### Step 4: Build Your Own UI

Create your own interface using the service functions:

```tsx
import { useState } from 'react';
import * as geminiService from './services/geminiService';

export function CustomMixAssistant() {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    try {
      const answer = await geminiService.generateStandardResponse(input);
      setResponse(answer);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div className="mix-assistant">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about mixing..."
      />
      <button onClick={handleAsk} disabled={loading}>
        {loading ? 'Thinking...' : 'Ask AI'}
      </button>
      {response && <div className="response">{response}</div>}
    </div>
  );
}
```

**Pros:**
- ✅ Complete UI control
- ✅ Smaller bundle size (only what you need)
- ✅ Match your website's design perfectly

**Cons:**
- ❌ More development work
- ❌ Need to implement all features yourself
- ❌ Responsible for UX design

---

## Customization Options

### Theme Customization

The AI Mix Partner has 4 built-in themes. To customize:

**1. Modify CSS Variables** (if using iframe):

```html
<style>
  iframe {
    /* Override theme colors via postMessage */
  }
</style>
```

**2. Edit Theme in Source** (if using direct integration):

Edit `ai-audio-mix-partner/index.tsx` and modify CSS variables:

```css
:root[data-theme="custom"] {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --text-primary: #eee;
  --text-secondary: #94a1b2;
  --accent-primary: #0f3460;
  --accent-secondary: #533483;
  --border-primary: #2a2d3a;
  --border-secondary: #3d3d5c;
}
```

### Feature Selection

To show only specific features, modify `App.tsx`:

```tsx
// Show only Chat and Live modes
const AVAILABLE_MODES = [AIMode.Chat, AIMode.Live];

// In ModeSelector, filter modes:
const modes = ALL_MODES.filter(mode => AVAILABLE_MODES.includes(mode.id));
```

### Branding

**Change Logo and Title:**

```tsx
// In App.tsx, replace:
<h1 className="text-2xl font-bold">AI Mix Partner</h1>

// With:
<h1 className="text-2xl font-bold">Your Brand Name</h1>
```

**Custom Icon:**
```tsx
import YourLogo from './assets/logo.svg';

// Replace:
<Headphones className="w-10 h-10" />

// With:
<img src={YourLogo} alt="Logo" className="w-10 h-10" />
```

---

## Security Considerations

### 🔐 API Key Protection

**CRITICAL:** Never expose your Gemini API key in client-side code!

#### **For Iframe/Static Deployment:**

The API key is embedded in the build. To secure it:

**Option A: Backend Proxy (Recommended)**

Create a backend endpoint that proxies Gemini API calls:

```typescript
// backend/api/gemini.ts
import { GoogleGenerativeAI } from '@google/generative-ai';

export async function POST(req: Request) {
  const apiKey = process.env.GEMINI_API_KEY; // Server-side only
  const genAI = new GoogleGenerativeAI(apiKey);

  const { message } = await req.json();

  const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });
  const result = await model.generateContent(message);

  return Response.json({ response: result.response.text() });
}
```

Then update `geminiService.ts` to call your backend:

```typescript
// Instead of calling Gemini directly:
const response = await fetch('/api/gemini', {
  method: 'POST',
  body: JSON.stringify({ message: prompt })
});
```

**Option B: Environment-Based Restrictions**

In Google Cloud Console:
1. Go to API credentials
2. Add HTTP referrer restrictions
3. Only allow your domain: `https://yourdomain.com/*`

#### **For Direct Integration:**

Use environment variables correctly:

```bash
# .env.local (NEVER commit this file!)
VITE_GEMINI_API_KEY=your-key-here
```

Add to `.gitignore`:
```
.env.local
.env.*.local
```

### CORS Configuration

If AI Mix Partner is on a different domain:

```javascript
// vite.config.ts
export default defineConfig({
  server: {
    cors: {
      origin: 'https://yourdomain.com',
      credentials: true
    }
  }
});
```

---

## Troubleshooting

### Issue 1: "API Key Not Found"

**Problem:** Application shows "API key not defined" error

**Solutions:**
```bash
# 1. Check .env.local exists
ls -la .env.local

# 2. Verify key is set
cat .env.local | grep GEMINI_API_KEY

# 3. Restart dev server
npm run dev
```

### Issue 2: Microphone Not Working

**Problem:** Live conversation mode can't access microphone

**Solutions:**
- Ensure site is HTTPS (required for microphone access)
- Check browser permissions
- Add `allow="microphone"` to iframe

### Issue 3: CORS Errors

**Problem:** Cross-origin errors when using iframe

**Solutions:**
```javascript
// vite.config.ts
server: {
  cors: {
    origin: '*', // For development
    credentials: true
  }
}
```

For production, set specific origins:
```javascript
origin: ['https://yourdomain.com', 'https://www.yourdomain.com']
```

### Issue 4: Build Fails

**Problem:** `npm run build` errors

**Solutions:**
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Update dependencies
npm update

# Check Node version (requires 18+)
node --version
```

### Issue 5: Iframe Content Not Loading

**Problem:** Blank iframe or loading spinner forever

**Solutions:**
1. Check browser console for errors
2. Verify URL is accessible: `curl https://mixer.yourdomain.com`
3. Check for HTTPS mixed content warnings
4. Verify CORS headers are correct

---

## Integration Checklist

- [ ] Choose integration method (iframe, React, separate, API)
- [ ] Get Google Gemini API key from [ai.google.dev](https://ai.google.dev)
- [ ] Set API key in `.env.local`
- [ ] Test locally with `npm run dev`
- [ ] Build for production with `npm run build`
- [ ] Deploy to hosting (Vercel/Netlify/own server)
- [ ] Configure CORS if needed
- [ ] Set up API key restrictions in Google Cloud Console
- [ ] Test microphone permissions (for live mode)
- [ ] Customize branding/theme
- [ ] Add to your website
- [ ] Test on mobile devices
- [ ] Monitor API usage in Google Cloud Console

---

## Quick Start Examples

### WordPress Integration

```html
<!-- Add to page/post HTML block -->
<div style="max-width: 1200px; margin: 0 auto;">
  <iframe
    src="https://mixer.yourdomain.com"
    width="100%"
    height="800px"
    frameborder="0"
    allow="microphone"
    style="border: 2px solid #ddd; border-radius: 12px;"
  ></iframe>
</div>
```

### Next.js Integration

```tsx
// app/mixer/page.tsx
import dynamic from 'next/dynamic';

const AIAudioMixPartner = dynamic(
  () => import('@/components/AIAudioMixPartner/App'),
  { ssr: false }
);

export default function MixerPage() {
  return (
    <main className="container mx-auto py-8">
      <AIAudioMixPartner />
    </main>
  );
}
```

### Gatsby Integration

```jsx
// src/pages/mixer.js
import React from 'react';
import AIAudioMixPartner from '../components/AIAudioMixPartner/App';

export default function MixerPage() {
  return (
    <div>
      <h1>AI Mixing Assistant</h1>
      <AIAudioMixPartner />
    </div>
  );
}
```

---

## Next Steps

1. **Start Simple**: Begin with iframe embed (Option 1)
2. **Test Thoroughly**: Verify all features work
3. **Customize**: Adjust theme and branding
4. **Monitor Usage**: Track API calls in Google Cloud Console
5. **Optimize**: Consider backend proxy for API key security

For advanced customization or integration help, refer to:
- [Vite Documentation](https://vitejs.dev)
- [React Documentation](https://react.dev)
- [Google Gemini API Docs](https://ai.google.dev/docs)

---

**Integration Guide Version:** 1.0
**Last Updated:** December 2025
**AI Mix Partner Version:** 0.0.0
