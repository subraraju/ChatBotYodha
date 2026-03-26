/* ── Single message bubble ──────────────────────────────────────── */

import ReactMarkdown from 'react-markdown';
import type { Message } from '../types';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`bubble-row ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
      <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        )}
      </div>
    </div>
  );
}
