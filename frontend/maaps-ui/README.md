# MAAPS UI - React Frontend

Modern React + TypeScript frontend for the MAAPS API.

## Features

- **Dashboard**: System health and performance metrics
- **Effects Chain**: Real-time effect parameter control
- **Live Looping**: Loop track management
- **Sync & Clock**: Transport and tempo control
- **Performance Automation**: Scenes, macros, and cues

## Tech Stack

- React 18 + TypeScript
- Material-UI (MUI) components
- Redux Toolkit for state management
- Axios for HTTP requests
- WebSocket for real-time updates
- Vite for build tooling

## Quick Start

### Install Dependencies

```bash
cd frontend/maaps-ui
npm install
```

### Run Development Server

```bash
npm run dev
```

The UI will be available at http://localhost:3000

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
src/
├── api/
│   ├── client.ts          # REST API client
│   └── websocket.ts       # WebSocket client
├── components/
│   ├── Dashboard.tsx      # Dashboard view
│   ├── EffectsChain.tsx   # Effects chain view
│   ├── Looping.tsx        # Looping view (coming soon)
│   ├── Sync.tsx           # Sync & clock view (coming soon)
│   └── Automation.tsx     # Automation view (coming soon)
├── store/
│   ├── index.ts           # Redux store
│   └── slices/            # Redux slices
├── hooks/
│   └── useWebSocket.ts    # WebSocket hook
├── types/
│   └── index.ts           # TypeScript types
└── App.tsx                # Main app component
```

## API Integration

The frontend connects to the MAAPS API at `http://localhost:8000`.

### REST API Client

```typescript
import { apiClient } from './api/client';

// Create effect chain
await apiClient.createEffectChain({
  chain_name: 'Vocal Chain',
  effects: [...]
});

// Get system health
const health = await apiClient.getSystemHealth();
```

### WebSocket Client

```typescript
import { wsClient } from './api/websocket';

// Connect
wsClient.connect();

// Subscribe to events
wsClient.on('effects.parameter.change', (data) => {
  console.log('Parameter changed:', data);
});
```

## Development

### Add New Components

1. Create component in `src/components/`
2. Import in `App.tsx`
3. Add to sidebar navigation

### Add API Endpoints

1. Add method to `src/api/client.ts`
2. Use in components with `apiClient.methodName()`

### WebSocket Events

1. Subscribe in component `useEffect`
2. Handle events with `wsClient.on(topic, handler)`
3. Clean up with `wsClient.off(topic, handler)`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

Create `.env` file:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT
