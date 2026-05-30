/**
 * App — Root component with routing and global socket connection.
 */
import { useState, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Brands from './pages/Brands';
import Chat from './pages/Chat';
import useSocket from './hooks/useSocket';

function App() {
  const [kpiData, setKpiData] = useState(null);
  const handleKPIUpdate = useCallback((data) => setKpiData(data), []);
  const { isConnected } = useSocket(handleKPIUpdate);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)' }}>
      <Navbar isConnected={isConnected} />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/brands" element={<Brands />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/chat/:roomId" element={<Chat />} />
      </Routes>
    </div>
  );
}

export default App;
