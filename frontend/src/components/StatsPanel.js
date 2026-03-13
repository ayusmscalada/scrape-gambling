import React from 'react';
import './StatsPanel.css';

function StatsPanel({ stats }) {
  if (!stats) {
    return (
      <div className="stats-panel">
        <div className="stat-card loading">
          <div className="stat-skeleton"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="stats-panel">
      <div className="stat-card">
        <div className="stat-icon">👥</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_raw_players || 0}</div>
          <div className="stat-label">Raw Players</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">⭐</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_qualified_leads || 0}</div>
          <div className="stat-label">Qualified Leads</div>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">🔗</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_identity_matches || 0}</div>
          <div className="stat-label">Identity Matches</div>
        </div>
      </div>

      {stats.by_platform && Object.keys(stats.by_platform).length > 0 && (
        <div className="stat-card platforms">
          <div className="stat-icon">🌐</div>
          <div className="stat-content">
            <div className="stat-label">By Platform</div>
            <div className="platform-list">
              {Object.entries(stats.by_platform).map(([platform, count]) => (
                <div key={platform} className="platform-item">
                  <span className="platform-name">{platform}</span>
                  <span className="platform-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StatsPanel;
