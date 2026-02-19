import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import * as Tabs from '@radix-ui/react-tabs';
import Today from './pages/Today';
import Decisions from './pages/Decisions';
import Memos from './pages/Memos';
import Directions from './pages/Directions';
import Settings from './pages/Settings';

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Map routes to tab values
  const getTabValue = () => {
    switch (location.pathname) {
      case '/': return 'today';
      case '/decisions': return 'decisions';
      case '/memos': return 'memos';
      case '/directions': return 'directions';
      case '/settings': return 'settings';
      default: return 'today';
    }
  };

  const handleTabChange = (value: string) => {
    // Navigate to the corresponding route when tab changes
    const routes: Record<string, string> = {
      today: '/',
      decisions: '/decisions',
      memos: '/memos',
      directions: '/directions',
      settings: '/settings',
    };
    navigate(routes[value]);
  };

  return (
    <div className="app">
      <Tabs.Root 
        value={getTabValue()} 
        onValueChange={handleTabChange}
        className="tabs-root"
      >
        <Tabs.List className="tabs-list">
          <Tabs.Trigger value="today" className="tabs-trigger">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Today
          </Tabs.Trigger>
          <Tabs.Trigger value="decisions" className="tabs-trigger">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Decisions
          </Tabs.Trigger>
          <Tabs.Trigger value="memos" className="tabs-trigger">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Memos
          </Tabs.Trigger>
          <Tabs.Trigger value="directions" className="tabs-trigger">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            Directions
          </Tabs.Trigger>
          <Tabs.Trigger value="settings" className="tabs-trigger">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Settings
          </Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>
      
      <main className="main">
        <Routes>
          <Route path="/" element={<Today />} />
          <Route path="/decisions" element={<Decisions />} />
          <Route path="/memos" element={<Memos />} />
          <Route path="/directions" element={<Directions />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
