/* ── Sidebar — navigation + session info ────────────────────────── */

import type { SessionInfo } from '../types';

interface Props {
  view: 'chat' | 'admin';
  onViewChange: (v: 'chat' | 'admin') => void;
  onNewChat: () => void;
  sessionActive: boolean;
  onEndChat: () => void;
  session: SessionInfo | null;
}

export default function Sidebar({
  view,
  onViewChange,
  onNewChat,
  sessionActive,
  onEndChat,
  session,
}: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>🤖 Yodha</h1>
      </div>

      <nav className="sidebar-nav">
        <button
          className={view === 'chat' ? 'active' : ''}
          onClick={() => onViewChange('chat')}
        >
          💬 Chat
        </button>
        <button
          className={view === 'admin' ? 'active' : ''}
          onClick={() => onViewChange('admin')}
        >
          ⚙️ Admin
        </button>
      </nav>

      <div className="sidebar-actions">
        <button className="btn-primary" onClick={onNewChat}>
          + New Chat
        </button>
        {sessionActive && (
          <button className="btn-danger" onClick={onEndChat}>
            End Chat
          </button>
        )}
      </div>

      {session && (
        <div className="session-info">
          <h3>Session</h3>
          <p><strong>State:</strong> {session.customer_state}</p>
          {session.customer_info?.first_name && (
            <p><strong>Customer:</strong> {String(session.customer_info.first_name)}</p>
          )}
          {session.selected_product && (
            <p><strong>Product:</strong> {session.selected_product.product_name}</p>
          )}
          <p><strong>Messages:</strong> {session.messages.length}</p>
        </div>
      )}
    </aside>
  );
}
