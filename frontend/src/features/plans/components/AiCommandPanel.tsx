import { type FormEvent, useState } from 'react';

export type AiMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
};

type AiCommandPanelProps = {
  history: AiMessage[];
  isSending: boolean;
  error: string | null;
  onSend: (message: string) => void;
};

export function AiCommandPanel({ history, isSending, error, onSend }: AiCommandPanelProps) {
  const [message, setMessage] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || isSending) {
      return;
    }
    onSend(trimmed);
    setMessage('');
  }

  return (
    <section className="ai-panel" aria-label="AI command panel">
      <div className="ai-panel-header">
        <p className="eyebrow">AI assistant</p>
        <h2>Ask for a plan change</h2>
      </div>
      <div className="ai-panel-history" aria-live="polite">
        {history.length === 0 ? (
          <p className="ai-panel-placeholder">Try: Move QA testing after Integration</p>
        ) : (
          <ul className="ai-message-list">
            {history.map((item) => (
              <li key={item.id} className={`ai-message ai-message-${item.role}`}>
                {item.text}
              </li>
            ))}
          </ul>
        )}
      </div>
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      <form className="ai-panel-form" onSubmit={handleSubmit}>
        <label htmlFor="ai-command-input" className="sr-only">
          AI command
        </label>
        <textarea
          id="ai-command-input"
          placeholder="Try: Move QA testing after Integration"
          value={message}
          onChange={(event) => setMessage(event.currentTarget.value)}
          disabled={isSending}
          rows={3}
        />
        <button className="primary-button" type="submit" disabled={isSending || !message.trim()}>
          {isSending ? 'Sending' : 'Send'}
        </button>
      </form>
    </section>
  );
}
