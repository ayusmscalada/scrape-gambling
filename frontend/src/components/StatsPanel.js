import React, { useEffect, useRef } from 'react';
import './StatsPanel.css';

function StatsPanel({ stats }) {
  const platformListRef = useRef(null);
  const platformCardRef = useRef(null);

  useEffect(() => {
    // #region agent log
    if (platformListRef.current && platformCardRef.current) {
      const listHeight = platformListRef.current.offsetHeight;
      const cardHeight = platformCardRef.current.offsetHeight;
      const platformCount = stats?.by_platform ? Object.keys(stats.by_platform).length : 0;
      fetch('http://127.0.0.1:7242/ingest/2b59062e-40f8-4751-af77-57bad3db4ade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'StatsPanel.js:useEffect',message:'Platform list dimensions',data:{listHeight,cardHeight,platformCount},timestamp:Date.now(),hypothesisId:'A'})}).catch(()=>{});
    }
    // #endregion
  }, [stats?.by_platform]);
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

      {/* <div className="stat-card">
        <div className="stat-icon">⭐</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_qualified_leads || 0}</div>
          <div className="stat-label">Qualified Leads</div>
        </div>
      </div> */}

      <div className="stat-card">
        <div className="stat-icon">🔗</div>
        <div className="stat-content">
          <div className="stat-value">{stats.total_identity_matches || 0}</div>
          <div className="stat-label">Identity Matches</div>
        </div>
      </div>

      {stats.by_platform && Object.keys(stats.by_platform).length > 0 && (
        <div className="stat-card platforms" ref={platformCardRef}>
          <div className="stat-icon">🌐</div>
          <div className="stat-content">
            <div className="stat-label">By Platform</div>
            <div className="platform-list" ref={platformListRef}>
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
