import { Routes, Route, useLocation, Link } from 'react-router-dom';
import Today from './pages/Today';
import Decisions from './pages/Decisions';
import Memos from './pages/Memos';
import Directions from './pages/Directions';
import Settings from './pages/Settings';

const navItems = [
  { path: '/', label: 'today' },
  { path: '/decisions', label: 'decisions' },
  { path: '/memos', label: 'memos' },
  { path: '/directions', label: 'directions' },
  { path: '/settings', label: 'settings' },
];

function App() {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="app">
      <nav className="nav">
        {navItems.map((item) => (
          <span key={item.path} className="nav-item">
            {isActive(item.path) ? (
              <span className="nav-active">&gt; {item.label}</span>
            ) : (
              <Link to={item.path} className="nav-link">[{item.label}]</Link>
            )}
          </span>
        ))}
      </nav>
      
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
