import { Routes, Route, NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import Calendar from './pages/Calendar'
import Decisions from './pages/Decisions'
import Memos from './pages/Memos'
import Directions from './pages/Directions'
import Settings from './pages/Settings'
import { Compass, CheckSquare, FileText, CalendarDays, Settings as SettingsIcon } from 'lucide-react'

const navItems = [
  { to: "/", label: "Calendar", icon: CalendarDays },
  { to: "/decisions", label: "Decisions", icon: CheckSquare },
  { to: "/memos", label: "Memos", icon: FileText },
  { to: "/directions", label: "Directions", icon: Compass },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
]

function App() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-card">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center space-x-2">
            <Compass className="h-6 w-6 text-primary" />
            <span className="text-lg font-semibold">Deciduum</span>
            <div className="ml-auto flex items-center space-x-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-secondary text-secondary-foreground"
                        : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
                    )
                  }
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      </nav>
      <main className="container mx-auto px-4 py-6">
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
