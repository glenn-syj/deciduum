import { Routes, Route, Link } from 'react-router-dom'
import Calendar from './pages/Calendar'
import Decisions from './pages/Decisions'
import Memos from './pages/Memos'
import Directions from './pages/Directions'
import Settings from './pages/Settings'

function App() {
  return (
    <div className="app">
      <nav className="nav">
        <Link to="/">Calendar</Link>
        <Link to="/decisions">Decisions</Link>
        <Link to="/memos">Memos</Link>
        <Link to="/directions">Directions</Link>
        <Link to="/settings">Settings</Link>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Calendar />} />
          <Route path="/decisions" element={<Decisions />} />
          <Route path="/memos" element={<Memos />} />
          <Route path="/directions" element={<Directions />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
