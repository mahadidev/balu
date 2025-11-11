import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import LoadingSpinner from '../components/LoadingSpinner';
import apiService from '../services/api';

function Analytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [analytics, setAnalytics] = useState({
    overview: {
      total_messages: 0,
      total_servers: 0,
      total_rooms: 0,
      active_users: 0
    },
    daily_stats: [],
    top_rooms: [],
    top_servers: [],
    hourly_activity: []
  });
  const { wsData } = useWebSocket();

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  useEffect(() => {
    if (wsData?.type === 'stats_update') {
      fetchAnalytics();
    }
  }, [wsData]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await apiService.get(`/api/analytics?range=${timeRange}`);
      setAnalytics(data);
      setError(null);
    } catch (err) {
      setError('Failed to load analytics');
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="flex space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">💬</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Messages
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatNumber(analytics.overview.total_messages)}
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
                <div className="text-2xl">🏢</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Connected Servers
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.overview.total_servers}
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
                <div className="text-2xl">🏠</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Rooms
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.overview.total_rooms}
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
                <div className="text-2xl">👥</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Users
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatNumber(analytics.overview.active_users)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Activity Chart */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Daily Message Activity</h2>
        </div>
        <div className="p-6">
          {analytics.daily_stats.length === 0 ? (
            <p className="text-center text-gray-500">No data available for the selected time range.</p>
          ) : (
            <div className="space-y-3">
              {analytics.daily_stats.map((day, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="w-20 text-sm text-gray-600 flex-shrink-0">
                    {formatDate(day.date)}
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.max(2, (day.message_count / Math.max(...analytics.daily_stats.map(d => d.message_count))) * 100)}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  <div className="w-16 text-sm text-gray-900 text-right flex-shrink-0">
                    {formatNumber(day.message_count)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Rooms */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Most Active Rooms</h2>
          </div>
          <div className="p-6">
            {analytics.top_rooms.length === 0 ? (
              <p className="text-center text-gray-500">No room data available.</p>
            ) : (
              <div className="space-y-3">
                {analytics.top_rooms.slice(0, 10).map((room, index) => (
                  <div key={room.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0 w-6 text-sm text-gray-500">
                        #{index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {room.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {room.channel_count} channels
                        </p>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-sm text-gray-900">
                      {formatNumber(room.message_count)} messages
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Top Servers */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Most Active Servers</h2>
          </div>
          <div className="p-6">
            {analytics.top_servers.length === 0 ? (
              <p className="text-center text-gray-500">No server data available.</p>
            ) : (
              <div className="space-y-3">
                {analytics.top_servers.slice(0, 10).map((server, index) => (
                  <div key={server.guild_id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0 w-6 text-sm text-gray-500">
                        #{index + 1}
                      </div>
                      <div className="flex items-center space-x-2">
                        {server.icon_url ? (
                          <img 
                            className="h-6 w-6 rounded-full" 
                            src={server.icon_url} 
                            alt={server.name}
                          />
                        ) : (
                          <div className="h-6 w-6 rounded-full bg-gray-300 flex items-center justify-center">
                            <span className="text-xs font-medium text-gray-700">
                              {server.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {server.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {server.member_count} members
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-sm text-gray-900">
                      {formatNumber(server.message_count)} messages
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hourly Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Hourly Activity Pattern</h2>
        </div>
        <div className="p-6">
          {analytics.hourly_activity.length === 0 ? (
            <p className="text-center text-gray-500">No hourly data available.</p>
          ) : (
            <div className="grid grid-cols-12 gap-2">
              {Array.from({ length: 24 }, (_, hour) => {
                const hourData = analytics.hourly_activity.find(h => h.hour === hour) || { message_count: 0 };
                const maxMessages = Math.max(...analytics.hourly_activity.map(h => h.message_count));
                const height = maxMessages > 0 ? (hourData.message_count / maxMessages) * 100 : 0;
                
                return (
                  <div key={hour} className="text-center">
                    <div className="h-20 flex items-end justify-center">
                      <div
                        className="w-6 bg-blue-500 rounded-t transition-all duration-500"
                        style={{ height: `${Math.max(2, height)}%` }}
                        title={`${hour}:00 - ${hourData.message_count} messages`}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {hour.toString().padStart(2, '0')}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Analytics;