import { useState, useEffect } from 'react';

export default function Settings() {
  const [apiKey, setApiKey] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const storedApiKey = localStorage.getItem('apiKey') || '';
    const storedSessionId = localStorage.getItem('sessionId') || 'default';
    setApiKey(storedApiKey);
    setSessionId(storedSessionId);
  }, []);

  const handleSave = () => {
    localStorage.setItem('apiKey', apiKey);
    localStorage.setItem('sessionId', sessionId);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleSwitchSession = (newSessionId: string) => {
    setSessionId(newSessionId);
    localStorage.setItem('sessionId', newSessionId);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="terminal">
      <div className="terminal-output">
        <div>&gt; Settings</div>
        <div>
          API Key: <input
            type="text"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="________________________"
            className="terminal-input"
          />
        </div>
        <div>
          Session ID: <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="default"
            className="terminal-input"
          />
        </div>
        <div>
          <button onClick={handleSave} className="terminal-button">
            save
          </button>
        </div>
        {saved && <div>&gt; Saved!</div>}
        <div className="terminal-hint">
          Hint: Get the API key from your backend .env file (DECIDUUM_API_KEY)
        </div>
        <div className="terminal-hint">
          Session ID: Use different sessions to manage separate databases
        </div>
        <div style={{ marginTop: '1rem' }}>
          <div>&gt; Quick Switch Session</div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button onClick={() => handleSwitchSession('default')} className="terminal-button">
              default
            </button>
            <button onClick={() => handleSwitchSession('work')} className="terminal-button">
              work
            </button>
            <button onClick={() => handleSwitchSession('personal')} className="terminal-button">
              personal
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
