import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import LoadingSpinner from '../components/LoadingSpinner';
import apiService from '../services/api';

function RoomDetails() {
  const { roomId } = useParams();
  const [room, setRoom] = useState(null);
  const [channels, setChannels] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { wsData } = useWebSocket();

  useEffect(() => {
    fetchRoomDetails();
  }, [roomId]);

  useEffect(() => {
    if (wsData?.type === 'message' && wsData?.room_id === parseInt(roomId)) {
      setMessages(prev => [wsData.data, ...prev].slice(0, 50)); // Keep last 50 messages
    }
  }, [wsData, roomId]);

  const fetchRoomDetails = async () => {
    try {
      setLoading(true);
      const [roomData, channelsData, messagesData] = await Promise.all([
        apiService.get(`/api/rooms/${roomId}`),
        apiService.get(`/api/rooms/${roomId}/channels`),
        apiService.get(`/api/rooms/${roomId}/messages?limit=50`)
      ]);
      
      setRoom(roomData);
      setChannels(channelsData);
      setMessages(messagesData);
      setError(null);
    } catch (err) {
      setError('Failed to load room details');
      console.error('Error fetching room details:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
        <Link to="/rooms" className="text-blue-600 hover:text-blue-900">
          ← Back to Rooms
        </Link>
      </div>
    );
  }

  if (!room) return <div>Room not found</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/rooms" className="text-blue-600 hover:text-blue-900 text-sm">
            ← Back to Rooms
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-2">{room.name}</h1>
          {room.description && (
            <p className="text-gray-600 mt-1">{room.description}</p>
          )}
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Room ID: {room.id}</div>
          <div className={`text-sm font-medium ${room.is_active ? 'text-green-600' : 'text-gray-500'}`}>
            {room.is_active ? 'Active' : 'Inactive'}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">📺</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Connected Channels
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {channels.length}
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
                <div className="text-2xl">💬</div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Messages
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {room.message_count || 0}
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
                    Messages Today
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {room.messages_today || 0}
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
                    Unique Servers
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {new Set(channels.map(c => c.guild_id)).size}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Channels List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Connected Channels</h2>
        </div>
        {channels.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No channels connected to this room yet.</p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Server
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Activity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {channels.map((channel) => (
                  <tr key={channel.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          #{channel.channel_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {channel.channel_id}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {channel.guild_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {channel.guild_id}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {channel.last_message_at 
                        ? formatTimestamp(channel.last_message_at)
                        : 'No messages'
                      }
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        channel.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {channel.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Messages */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Messages</h2>
        </div>
        {messages.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No messages in this room yet.</p>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <div className="divide-y divide-gray-200">
              {messages.map((message, index) => (
                <div key={message.id || index} className="p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">
                          {message.username}
                        </span>
                        <span className="text-sm text-gray-500">
                          #{message.channel_name || 'unknown'}
                        </span>
                        <span className="text-xs text-gray-400">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      </div>
                      {message.reply_to_username && (
                        <div className="mt-1 text-sm text-gray-600 bg-gray-50 rounded px-2 py-1">
                          ↳ Replying to {message.reply_to_username}: {message.reply_to_content}
                        </div>
                      )}
                      <div className="mt-1 text-gray-800">
                        {message.content}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RoomDetails;