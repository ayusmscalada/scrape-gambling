import React, { useState, useEffect } from 'react';
import RawPlayersTable from '../components/RawPlayersTable';
import QualifiedLeadsTable from '../components/QualifiedLeadsTable';
import IdentityMatchesTable from '../components/IdentityMatchesTable';
import StatsPanel from '../components/StatsPanel';
import NotificationCenter from '../components/NotificationCenter';
import websocketService from '../services/websocket';
import './Dashboard.css';

function Dashboard() {
  const [activeTab, setActiveTab] = useState('raw-players');
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Connect WebSocket
    websocketService.connect();
    setWsConnected(websocketService.isConnected());

    // Listen for connection status
    const handleConnection = (connected) => {
      setWsConnected(connected);
    };

    // Listen for raw player updates
    const handleRawPlayerAdded = (data) => {
      setNotifications((prev) => [
        {
          id: Date.now(),
          type: 'info',
          message: `New player: ${data.username} from ${data.source_site}`,
          timestamp: new Date(),
        },
        ...prev.slice(0, 9), // Keep last 10 notifications
      ]);
    };

    // Listen for qualified lead updates
    const handleQualifiedLeadUpdated = (data) => {
      setNotifications((prev) => [
        {
          id: Date.now(),
          type: 'success',
          message: `Qualified lead: ${data.username} - ${data.confidence_label}`,
          timestamp: new Date(),
        },
        ...prev.slice(0, 9),
      ]);
    };

    // Listen for identity match updates
    const handleIdentityMatchAdded = (data) => {
      setNotifications((prev) => [
        {
          id: Date.now(),
          type: 'info',
          message: `Identity match: ${data.platform} @${data.social_handle}`,
          timestamp: new Date(),
        },
        ...prev.slice(0, 9),
      ]);
    };

    // Listen for stats updates
    const handleStatsUpdated = (data) => {
      setStats(data);
    };

    websocketService.on('connected', handleConnection);
    websocketService.on('raw_player_added', handleRawPlayerAdded);
    websocketService.on('qualified_lead_updated', handleQualifiedLeadUpdated);
    websocketService.on('identity_match_added', handleIdentityMatchAdded);
    websocketService.on('stats_updated', handleStatsUpdated);

    return () => {
      websocketService.off('connected', handleConnection);
      websocketService.off('raw_player_added', handleRawPlayerAdded);
      websocketService.off('qualified_lead_updated', handleQualifiedLeadUpdated);
      websocketService.off('identity_match_added', handleIdentityMatchAdded);
      websocketService.off('stats_updated', handleStatsUpdated);
      websocketService.disconnect();
    };
  }, []);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Enrichment Dashboard</h1>
        <div className="header-status">
          <div className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {wsConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </header>

      <StatsPanel stats={stats} />

      <div className="dashboard-content">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'raw-players' ? 'active' : ''}`}
            onClick={() => setActiveTab('raw-players')}
          >
            Raw Players
          </button>
          <button
            className={`tab ${activeTab === 'qualified-leads' ? 'active' : ''}`}
            onClick={() => setActiveTab('qualified-leads')}
          >
            Qualified Leads
          </button>
          <button
            className={`tab ${activeTab === 'identity-matches' ? 'active' : ''}`}
            onClick={() => setActiveTab('identity-matches')}
          >
            Identity Matches
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'raw-players' && <RawPlayersTable />}
          {activeTab === 'qualified-leads' && <QualifiedLeadsTable />}
          {activeTab === 'identity-matches' && <IdentityMatchesTable />}
        </div>
      </div>

      <NotificationCenter notifications={notifications} />
    </div>
  );
}

export default Dashboard;
