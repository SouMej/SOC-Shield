import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useWebSocket } from './hooks/useWebSocket';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import AlertsPage from './pages/AlertsPage';
import SearchPage from './pages/SearchPage';
import MitrePage from './pages/MitrePage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';
import Chatbot from './components/chat/Chatbot';

export default function App() {
  const { isConnected, alerts } = useWebSocket();
  const unackCount = alerts.filter(a => !a.acknowledged).length;

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout isConnected={isConnected} alertCount={unackCount} />}>
          <Route path="/" element={<DashboardPage wsAlerts={alerts} />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/mitre" element={<MitrePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <Chatbot />
    </BrowserRouter>
  );
}
