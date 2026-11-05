/**
 * MAAPS API Client
 * TypeScript client for MAAPS REST API
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class MAAPSApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Effects Chain API
  async createEffectChain(data: any) {
    return this.client.post('/effects/chains', data);
  }

  async getEffectChains() {
    return this.client.get('/effects/chains');
  }

  async getEffectChain(chainId: string) {
    return this.client.get(`/effects/chains/${chainId}`);
  }

  async updateEffectParameters(chainId: string, effectId: string, parameters: any) {
    return this.client.patch(
      `/effects/chains/${chainId}/effects/${effectId}/parameters`,
      { parameters }
    );
  }

  async toggleEffectBypass(chainId: string, effectId: string, bypass: boolean) {
    return this.client.post(
      `/effects/chains/${chainId}/effects/${effectId}/bypass`,
      { bypass }
    );
  }

  // Live Looping API
  async createLoopTrack(data: any) {
    return this.client.post('/looping/tracks', data);
  }

  async getLoopTracks() {
    return this.client.get('/looping/tracks');
  }

  async startRecording(trackId: string, mode: string) {
    return this.client.post(`/looping/tracks/${trackId}/record/start`, { mode });
  }

  async stopRecording(trackId: string) {
    return this.client.post(`/looping/tracks/${trackId}/record/stop`);
  }

  async togglePlayback(trackId: string) {
    return this.client.post(`/looping/tracks/${trackId}/playback/toggle`);
  }

  async manipulateLoop(trackId: string, operation: string, parameters?: any) {
    return this.client.post(`/looping/tracks/${trackId}/manipulate`, {
      operation,
      parameters,
    });
  }

  // Sync & Clock API
  async setTempo(bpm: number, timeSignature: string) {
    return this.client.post('/sync/tempo/set', { bpm, time_signature: timeSignature });
  }

  async tapTempo() {
    return this.client.post('/sync/tempo/tap');
  }

  async transportPlay() {
    return this.client.post('/sync/transport/play');
  }

  async transportStop() {
    return this.client.post('/sync/transport/stop');
  }

  async transportPause() {
    return this.client.post('/sync/transport/pause');
  }

  async getClockStatus() {
    return this.client.get('/sync/status');
  }

  // Automation API
  async createScene(data: any) {
    return this.client.post('/automation/scenes', data);
  }

  async triggerScene(sceneId: string) {
    return this.client.post(`/automation/scenes/${sceneId}/trigger`);
  }

  async createMacro(data: any) {
    return this.client.post('/automation/macros', data);
  }

  async changeMacroValue(macroId: string, value: number) {
    return this.client.post(`/automation/macros/${macroId}/value`, { value });
  }

  // System API
  async getSystemHealth() {
    return this.client.get('/system/health');
  }

  async getSystemMetrics() {
    return this.client.get('/system/metrics');
  }

  async listAgents() {
    return this.client.get('/system/agents');
  }

  // Authentication
  async login(username: string, password: string) {
    return this.client.post('/auth/login', { username, password });
  }

  async verifyToken() {
    return this.client.get('/auth/verify');
  }
}

export const apiClient = new MAAPSApiClient();
