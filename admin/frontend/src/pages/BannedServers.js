import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import LoadingSpinner from '../components/LoadingSpinner';
import { serversApi } from '../services/api';

function BannedServers() {
  const [bannedServers, setBannedServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeInactive, setIncludeInactive] = useState(false);
  const { wsData } = useWebSocket();

  useEffect(() => {
    fetchBannedServers();
  }, [includeInactive]);

  const fetchBannedServers = async () => {
    try {
      setLoading(true);
      const response = await serversApi.getBannedServers(includeInactive);
      setBannedServers(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load banned servers');
      console.error('Error fetching banned servers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUnbanServer = async (server) => {
    if (!window.confirm(`Are you sure you want to unban server "${server.guild_name}"? They will be able to subscribe to chat rooms again.`)) {
      return;
    }

    try {
      await serversApi.unbanServer(server.guild_id);
      // Remove from local state or mark as inactive
      setBannedServers(prev => prev.map(s => 
        s.guild_id === server.guild_id 
          ? { ...s, is_active: false, unbanned_at: new Date().toISOString(), unbanned_by: 'admin' }
          : s
      ));
      setError(null);
    } catch (err) {
      setError('Failed to unban server');
      console.error('Error unbanning server:', err);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/servers" className="text-blue-600 hover:text-blue-900 text-sm">
            ← Back to Servers
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2">Banned Servers</h1>
          <p className="text-gray-600 mt-1">Manage servers that are banned from chat rooms</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Show unbanned servers</span>
          </label>
          <button
            onClick={fetchBannedServers}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">🚫</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Currently Banned
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {bannedServers.filter(s => s.is_active).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">✅</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Unbanned
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {bannedServers.filter(s => !s.is_active).length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">📊</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Records
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {bannedServers.length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Banned Servers Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">
            {includeInactive ? 'All Ban Records' : 'Currently Banned Servers'}
          </h2>
        </div>
        {bannedServers.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>{includeInactive ? 'No ban records found.' : 'No servers are currently banned.'}</p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Server
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ban Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bannedServers.map((server) => (
                  <tr key={server.guild_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {server.guild_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {server.guild_id}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm text-gray-900">
                          Banned by: {server.banned_by}
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatTimestamp(server.banned_at)}
                        </div>
                        {server.unbanned_at && (
                          <div className="text-sm text-green-600 mt-1">
                            Unbanned by: {server.unbanned_by} at {formatTimestamp(server.unbanned_at)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs truncate" title={server.reason}>
                        {server.reason || 'No reason provided'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        server.is_active
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {server.is_active ? 'Banned' : 'Unbanned'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {server.is_active ? (
                        <button
                          onClick={() => handleUnbanServer(server)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          title="Unban this server"
                        >
                          ✅ Unban Server
                        </button>
                      ) : (
                        <span className="text-sm text-gray-500">Already unbanned</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default BannedServers;