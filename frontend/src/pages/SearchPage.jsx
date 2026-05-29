import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Clock } from 'lucide-react';
import { api } from '../services/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState('');
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setSearched(true);
    try {
      const body = {
        query: query || '*',
        time_from: 'now-24h',
        size: 100,
      };
      if (category) body.event_category = category;
      const data = await api.searchEvents(body);
      setResults(data);
    } catch (e) {
      console.error('Search error:', e);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    '', 'authentication_success', 'authentication_failure', 'privilege_escalation',
    'process_creation', 'account_management', 'kerberos_activity',
    'service_creation', 'sysmon_process_create',
  ];

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>
          <Search size={24} style={{ verticalAlign: 'middle', marginRight: 10 }} />
          Log Search
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Search across all ingested security events
        </p>
      </motion.div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search events... (e.g., powershell, 4625, administrator)"
              className="search-input"
            />
          </div>
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            style={{
              background: 'var(--bg-input)', border: '1px solid var(--border-primary)',
              borderRadius: 10, padding: '10px 14px', color: 'var(--text-primary)',
              fontSize: '0.85rem', outline: 'none', cursor: 'pointer',
              fontFamily: 'var(--font-primary)',
            }}
          >
            <option value="">All Categories</option>
            {categories.filter(c => c).map(c => (
              <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <button type="submit" className="btn btn-primary">
            <Search size={16} /> Search
          </button>
        </div>
      </form>

      {/* Results */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{
          padding: '12px 20px', borderBottom: '1px solid var(--border-primary)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
            {searched ? `${results.length} results` : 'Enter a search query'}
          </span>
        </div>

        <div style={{ maxHeight: 600, overflowY: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Event ID</th>
                <th>Category</th>
                <th>Host</th>
                <th>User</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {results.map((event, i) => (
                <tr key={event._id || i}>
                  <td style={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                    {event['@timestamp'] ? new Date(event['@timestamp']).toLocaleTimeString() : '—'}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{event.event_id}</td>
                  <td>
                    <span style={{
                      padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem',
                      background: 'var(--bg-elevated)', color: 'var(--text-secondary)',
                    }}>
                      {(event.event_category || '').replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{event.hostname || '—'}</td>
                  <td>{event.target_user || event.subject_user || '—'}</td>
                  <td style={{ fontSize: '0.78rem', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {event.message || event.command_line || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {loading && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
              Searching...
            </div>
          )}

          {searched && !loading && results.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
              No events found matching your query
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
