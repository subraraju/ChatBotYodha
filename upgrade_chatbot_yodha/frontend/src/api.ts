/* ── API client — all backend calls go through here ────────────── */

import type { StartSessionResponse, MessageResponse, ConfigResponse } from './types';

const API_BASE = import.meta.env.VITE_API_URL || '';

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  startSession: () => post<StartSessionResponse>('/chat/start', {}),

  sendMessage: (sessionId: string, message: string) =>
    post<MessageResponse>(`/chat/${sessionId}/message`, { message }),

  closeSession: (sessionId: string) =>
    post<{ closing_message: string; stored: boolean }>(`/chat/${sessionId}/close`, {}),

  getConfig: () => get<ConfigResponse>('/admin/config'),

  health: () => get<{ status: string }>('/health'),
};

/* ── WebSocket helper ──────────────────────────────────────────── */

export function createChatSocket(sessionId: string): WebSocket {
  const wsBase = import.meta.env.VITE_WS_URL || `ws://${location.host}`;
  return new WebSocket(`${wsBase}/chat/ws/${sessionId}`);
}
