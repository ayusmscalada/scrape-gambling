import React, { useState, useEffect } from 'react';
import { fetchQualifiedLeads } from '../services/api';
import websocketService from '../services/websocket';
import './Table.css';

function QualifiedLeadsTable() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);

  const loadLeads = async () => {
    setLoading(true);
    try {
      const response = await fetchQualifiedLeads(pageSize, (page - 1) * pageSize);
      if (response.success) {
        setLeads(response.data);
        setTotal(response.total);
      }
    } catch (error) {
      console.error('Error loading leads:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads();

    // Listen for qualified lead updates via WebSocket
    const handleQualifiedLeadUpdated = (data) => {
      setLeads((prev) => {
        const existing = prev.findIndex((l) => l.id === data.id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = data;
          return updated;
        }
        return [data, ...prev.slice(0, pageSize - 1)];
      });
    };

    websocketService.on('qualified_lead_updated', handleQualifiedLeadUpdated);

    return () => {
      websocketService.off('qualified_lead_updated', handleQualifiedLeadUpdated);
    };
  }, [page, pageSize]);

  const getConfidenceColor = (label) => {
    switch (label) {
      case 'usable lead':
        return '#10b981';
      case 'weak lead':
        return '#f59e0b';
      case 'no lead':
        return '#94a3b8';
      default:
        return '#94a3b8';
    }
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
        <h2>Qualified Leads ({total})</h2>
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
              <th>Contact Type</th>
              <th>Contact Value</th>
              <th>Confidence</th>
              <th>Label</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {leads.length === 0 ? (
              <tr>
                <td colSpan="8" className="table-empty">
                  No qualified leads found
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr key={lead.id}>
                  <td>{lead.id}</td>
                  <td className="username-cell">{lead.username}</td>
                  <td>
                    <span className="platform-badge">{lead.source_site || 'N/A'}</span>
                  </td>
                  <td>{lead.best_contact_type || 'N/A'}</td>
                  <td className="contact-value">{lead.best_contact_value || 'N/A'}</td>
                  <td>{lead.confidence || 'N/A'}</td>
                  <td>
                    <span
                      className="confidence-badge"
                      style={{ color: getConfidenceColor(lead.confidence_label) }}
                    >
                      {lead.confidence_label}
                    </span>
                  </td>
                  <td>{formatDate(lead.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default QualifiedLeadsTable;
