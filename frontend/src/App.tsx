/* ── Root layout — sidebar + chat + optional debug ──────────────── */

import { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import AdminPanel from './components/AdminPanel';
import type { SessionInfo, Message } from './types';
import { api } from './api';

type View = 'chat' | 'admin';

export default function App() {
  const [view, setView] = useState<View>('chat');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(false);

  /* Start a new chat session */
  const startSession = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.startSession();
      setSessionId(data.session_id);
      setMessages([{ role: 'assistant', content: data.welcome_message }]);
      setSession(null);
    } catch (err) {
      console.error('Failed to start session:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  /* Send a message */
  const sendMessage = useCallback(
    async (text: string) => {
      if (!sessionId) return;
      setMessages((prev) => [...prev, { role: 'user', content: text }]);
      setLoading(true);
      try {
        const data = await api.sendMessage(sessionId, text);
        setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
        setSession(data.session);
      } catch (err) {
        console.error('Message failed:', err);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '⚠️ Something went wrong. Please try again.' },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [sessionId],
  );

  /* Close session */
  const closeSession = useCallback(async () => {
    if (!sessionId) return;
    try {
      await api.closeSession(sessionId);
    } catch {
      /* ignore */
    }
    setSessionId(null);
    setMessages([]);
    setSession(null);
  }, [sessionId]);

  return (
    <div className="app-layout">
      <Sidebar
        view={view}
        onViewChange={setView}
        onNewChat={startSession}
        sessionActive={!!sessionId}
        onEndChat={closeSession}
        session={session}
      />

      <main className="main-content">
        {view === 'chat' ? (
          <ChatWindow
            messages={messages}
            onSend={sendMessage}
            loading={loading}
            sessionId={sessionId}
            onStart={startSession}
          />
        ) : (
          <AdminPanel />
        )}
      </main>
    </div>
  );
}
