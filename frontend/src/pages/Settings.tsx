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
    <div className="settings-page">
      <h1>Settings</h1>
      <div className="form-group">
        <label>API Key</label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter your API key"
        />
        <button onClick={handleSave}>
          {saved ? 'Saved!' : 'Save'}
        </button>
      </div>
      <p className="hint">
        Get the API key from your backend .env file (DECIDUUM_API_KEY)
      </p>
    </div>
  );
}
