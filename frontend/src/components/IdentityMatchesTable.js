import React, { useState, useEffect } from 'react';
import { fetchIdentityMatches } from '../services/api';
import websocketService from '../services/websocket';
import './Table.css';

function IdentityMatchesTable() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const response = await fetchIdentityMatches(null, pageSize, (page - 1) * pageSize);
      if (response.success) {
        setMatches(response.data);
        setTotal(response.total);
      }
    } catch (error) {
      console.error('Error loading matches:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatches();

    // Listen for identity match updates via WebSocket
    const handleIdentityMatchAdded = (data) => {
      setMatches((prev) => [data, ...prev.slice(0, pageSize - 1)]);
      setTotal((prev) => prev + 1);
    };

    websocketService.on('identity_match_added', handleIdentityMatchAdded);

    return () => {
      websocketService.off('identity_match_added', handleIdentityMatchAdded);
    };
  }, [page, pageSize]);

  const getPlatformIcon = (platform) => {
    const icons = {
      telegram: '✈️',
      instagram: '📷',
      x: '🐦',
      youtube: '📺',
    };
    return icons[platform.toLowerCase()] || '🔗';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="table-container">
        <div className="table-loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <div className="table-header">
        <h2>Identity Matches ({total})</h2>
        <div className="table-pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </button>
          <span>
            Page {page} of {Math.ceil(total / pageSize)}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * pageSize >= total}
          >
            Next
          </button>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Platform</th>
              <th>Social Handle</th>
              <th>Social URL</th>
              <th>Match Score</th>
              <th>Confidence</th>
              <th>Contact</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {matches.length === 0 ? (
              <tr>
                <td colSpan="9" className="table-empty">
                  No identity matches found
                </td>
              </tr>
            ) : (
              matches.map((match) => (
                <tr key={match.id}>
                  <td>{match.id}</td>
                  <td className="username-cell">{match.username}</td>
                  <td>
                    <span className="platform-badge">
                      {getPlatformIcon(match.platform)} {match.platform}
                    </span>
                  </td>
                  <td>@{match.social_handle}</td>
                  <td>
                    <a
                      href={match.social_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="social-link"
                    >
                      View Profile
                    </a>
                  </td>
                  <td>
                    <span className="score-badge">{match.match_score}</span>
                  </td>
                  <td>
                    <span className="confidence-badge">{match.confidence_label}</span>
                  </td>
                  <td className="contact-value">
                    {match.public_contact_type && match.public_contact_value ? (
                      <span>
                        {match.public_contact_type}: {match.public_contact_value}
                      </span>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td>{formatDate(match.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default IdentityMatchesTable;
