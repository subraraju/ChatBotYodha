/* ── Chat window — message list + input ─────────────────────────── */

import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import type { Message } from '../types';

interface Props {
  messages: Message[];
  onSend: (text: string) => void;
  loading: boolean;
  sessionId: string | null;
  onStart: () => void;
}

export default function ChatWindow({ messages, onSend, loading, sessionId, onStart }: Props) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    onSend(text);
  };

  if (!sessionId) {
    return (
      <div className="chat-empty">
        <h2>ChatBot Yodha</h2>
        <p>Customer Service &amp; Meeting Scheduler</p>
        <button className="btn-primary" onClick={onStart}>
          Start New Chat
        </button>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="messages-list">
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {loading && (
          <div className="typing-indicator">
            <span /><span /><span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        className="chat-input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          placeholder="Type your message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
