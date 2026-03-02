import { useState, useEffect } from 'react';

export default function Settings() {
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('apiKey') || '';
    setApiKey(stored);
  }, []);

  const handleSave = () => {
    localStorage.setItem('apiKey', apiKey);
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
          <button onClick={handleSave} className="terminal-button">
            save
          </button>
        </div>
        {saved && <div>&gt; Saved!</div>}
        <div className="terminal-hint">
          Hint: Get the API key from your backend .env file (DECIDUUM_API_KEY)
        </div>
      </div>
    </div>
  );
}
