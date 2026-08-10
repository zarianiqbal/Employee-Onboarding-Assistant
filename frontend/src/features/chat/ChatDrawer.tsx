import { useEffect, useRef, useState } from 'react';

import { api } from '../../api/client';
import type { Citation } from '../../api/types';
import './ChatDrawer.css';

interface ChatDrawerProps {
  employeeId: number;
}

interface Turn {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

const QUICK_PROMPTS = [
  'What documents do I need to submit?',
  'Explain the leave policy.',
  'Summarize the company handbook.',
];

/** Floating AI assistant drawer with streaming responses and quick prompts. */
export function ChatDrawer({ employeeId }: ChatDrawerProps) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [streaming, setStreaming] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [turns, open]);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || streaming) return;
    setInput('');

    const history = turns.map((t) => ({ role: t.role, content: t.content }));
    setTurns((prev) => [...prev, { role: 'user', content: question }, { role: 'assistant', content: '' }]);
    setStreaming(true);

    try {
      await api.chatStream(
        employeeId,
        question,
        history,
        (delta) => {
          setTurns((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              ...next[next.length - 1],
              content: next[next.length - 1].content + delta,
            };
            return next;
          });
        },
        (citations) => {
          setTurns((prev) => {
            const next = [...prev];
            next[next.length - 1] = { ...next[next.length - 1], citations };
            return next;
          });
        },
      );
    } catch {
      setTurns((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          content: 'Sorry, I had trouble answering. Please try again.',
        };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <>
      <button
        className="chat-fab btn btn-primary"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="chat-panel"
      >
        {open ? 'Close assistant' : '💬 Ask the assistant'}
      </button>

      {open && (
        <div className="chat-panel card" id="chat-panel" role="dialog" aria-label="Onboarding assistant">
          <div className="chat-panel__head">
            <h2 className="chat-panel__title">Onboarding assistant</h2>
          </div>

          <div className="chat-log" ref={logRef} aria-live="polite">
            {turns.length === 0 && (
              <div className="chat-empty">
                <p>Hi! Ask me anything about your onboarding or company policies.</p>
              </div>
            )}
            {turns.map((turn, i) => (
              <div key={i} className={`chat-msg chat-msg--${turn.role}`}>
                <div className="chat-msg__bubble">
                  {turn.content || (streaming && i === turns.length - 1 ? '…' : '')}
                </div>
                {turn.citations && turn.citations.length > 0 && (
                  <ul className="chat-citations">
                    {turn.citations.map((c, ci) => (
                      <li key={ci} title={c.snippet}>
                        📎 {c.title}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          <div className="chat-quick">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                className="chat-quick__btn"
                onClick={() => void send(prompt)}
                disabled={streaming}
              >
                {prompt}
              </button>
            ))}
          </div>

          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              void send(input);
            }}
          >
            <label htmlFor="chat-text" className="sr-only">
              Type your question
            </label>
            <input
              id="chat-text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question…"
              disabled={streaming}
            />
            <button type="submit" className="btn btn-primary" disabled={streaming || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
