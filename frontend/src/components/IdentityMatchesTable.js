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
    const handleIdentityMatchCreated = (data) => {
      setMatches((prev) => [data, ...prev.slice(0, pageSize - 1)]);
      setTotal((prev) => prev + 1);
    };

    websocketService.on('identity_match_created', handleIdentityMatchCreated);

    return () => {
      websocketService.off('identity_match_created', handleIdentityMatchCreated);
    };
  }, [page, pageSize]);

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
              <th>Username</th>
              <th>Telegram URL</th>
              <th>Instagram URL</th>
              <th>X URL</th>
              <th>YouTube URL</th>
              <th>Total Score</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {matches.length === 0 ? (
              <tr>
                <td colSpan="7" className="table-empty">
                  No identity matches found
                </td>
              </tr>
            ) : (
              matches.map((match) => (
                <tr key={match.id}>
                  <td className="username-cell">{match.username}</td>
                  <td>
                    {match.telegram_url ? (
                      <a
                        href={match.telegram_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="social-link"
                      >
                        {match.telegram_url}
                      </a>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {match.instagram_url ? (
                      <a
                        href={match.instagram_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="social-link"
                      >
                        {match.instagram_url}
                      </a>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {match.x_url ? (
                      <a
                        href={match.x_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="social-link"
                      >
                        {match.x_url}
                      </a>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {match.youtube_url ? (
                      <a
                        href={match.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="social-link"
                      >
                        {match.youtube_url}
                      </a>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    <span className="score-badge">{match.total_score}</span>
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
