import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

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
    <div className="space-y-8 max-w-lg">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Configure your application preferences</p>
      </div>
      
      <Card className="shadow-sm border-border/50">
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>
            Configure your API key to authenticate with the backend.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 p-6">
          <div className="space-y-2">
            <Label htmlFor="apiKey">API Key</Label>
            <Input
              id="apiKey"
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
            />
          </div>
          
          <Button onClick={handleSave}>
            {saved ? 'Saved!' : 'Save'}
          </Button>
          
          <p className="text-sm text-muted-foreground">
            Get the API key from your backend .env file (DECIDUUM_API_KEY)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
