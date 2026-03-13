import React, { useState, useEffect } from 'react';
import { fetchRawPlayers } from '../services/api';
import websocketService from '../services/websocket';
import './Table.css';

function RawPlayersTable() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);

  const loadPlayers = async () => {
    setLoading(true);
    try {
      const response = await fetchRawPlayers(pageSize, (page - 1) * pageSize);
      if (response.success) {
        setPlayers(response.data);
        setTotal(response.total);
      }
    } catch (error) {
      console.error('Error loading players:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlayers();

    // Listen for new raw players via WebSocket
    const handleRawPlayerAdded = (data) => {
      setPlayers((prev) => [data, ...prev.slice(0, pageSize - 1)]);
      setTotal((prev) => prev + 1);
    };

    websocketService.on('raw_player_added', handleRawPlayerAdded);

    return () => {
      websocketService.off('raw_player_added', handleRawPlayerAdded);
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
        <h2>Raw Players ({total})</h2>
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
              <th>Captured At</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {players.length === 0 ? (
              <tr>
                <td colSpan="5" className="table-empty">
                  No players found
                </td>
              </tr>
            ) : (
              players.map((player) => (
                <tr key={player.id}>
                  <td>{player.id}</td>
                  <td className="username-cell">{player.username}</td>
                  <td>
                    <span className="platform-badge">{player.source_site || 'N/A'}</span>
                  </td>
                  <td>{formatDate(player.captured_at)}</td>
                  <td>{formatDate(player.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default RawPlayersTable;
