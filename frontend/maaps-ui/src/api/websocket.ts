/**
 * MAAPS WebSocket Client
 * Real-time event subscription and handling
 */

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private eventHandlers: Map<string, Function[]> = new Map();

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws');

    this.ws.onopen = () => {
      console.log('WebSocket connected');

      // Authenticate
      const token = localStorage.getItem('auth_token');
      if (token) {
        this.send({ type: 'auth', token });
      }

      // Subscribe to all topics
      this.send({
        type: 'subscribe',
        topics: [
          'effects.parameter.change',
          'effects.chain.created',
          'loop.record.started',
          'loop.record.stopped',
          'sync.clock.position',
          'sync.clock.tempo',
          'automation.scene.triggered',
          'system.agent.heartbeat',
        ],
      });
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      setTimeout(() => this.connect(), this.reconnectInterval);
    };
  }

  private handleMessage(message: any) {
    const { type, topic, data } = message;

    if (type === 'event') {
      // Trigger event handlers for this topic
      const handlers = this.eventHandlers.get(topic) || [];
      handlers.forEach((handler) => handler(data));
    }
  }

  on(topic: string, handler: Function) {
    if (!this.eventHandlers.has(topic)) {
      this.eventHandlers.set(topic, []);
    }
    this.eventHandlers.get(topic)!.push(handler);
  }

  off(topic: string, handler: Function) {
    const handlers = this.eventHandlers.get(topic);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export const wsClient = new WebSocketClient();
