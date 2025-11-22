import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import LoadingSpinner from '../components/LoadingSpinner';
import { roomsApi, serversApi } from '../services/api';

function RoomDetails() {
  const { roomId } = useParams();
  const [room, setRoom] = useState(null);
  const [channels, setChannels] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', max_servers: '', is_active: true });
  const [updating, setUpdating] = useState(false);
  const { wsData } = useWebSocket();

  useEffect(() => {
    fetchRoomDetails();
  }, [roomId]);

  useEffect(() => {
    if (wsData?.type === 'message' && wsData?.room_id === parseInt(roomId)) {
      // Add the new formatted message to the top of the list
      const newMessage = {
        ...wsData.data,
        id: wsData.data.message_id || Date.now(), // Ensure we have an ID for React key
      };
      setMessages(prev => [newMessage, ...prev].slice(0, 50)); // Keep last 50 messages
    }
  }, [wsData, roomId]);

  const fetchRoomDetails = async () => {
    try {
      setLoading(true);
      const [roomData, channelsData, messagesData] = await Promise.all([
        roomsApi.getById(roomId),
        roomsApi.getChannels(roomId),
        roomsApi.getMessages(roomId, 50, 0)
      ]);
      
      setRoom(roomData.data);
      setChannels(channelsData.data);
      setMessages(messagesData.data);
      setError(null);
      
      // Initialize edit form with current room data
      setEditForm({
        name: roomData.data.name,
        max_servers: roomData.data.max_servers,
        is_active: roomData.data.is_active
      });
    } catch (err) {
      setError('Failed to load room details');
      console.error('Error fetching room details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditRoom = () => {
    setShowEditModal(true);
  };

  const handleUpdateRoom = async (e) => {
    e.preventDefault();
    setUpdating(true);
    
    try {
      const response = await roomsApi.update(roomId, editForm);
      setRoom(response.data);
      setShowEditModal(false);
      setError(null);
    } catch (err) {
      setError('Failed to update room');
      console.error('Error updating room:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleRemoveChannel = async (channel) => {
    if (!window.confirm(`Are you sure you want to remove channel #${channel.channel_name} from this room?`)) {
      return;
    }
    
    try {
      await roomsApi.unregisterChannel(roomId, channel.guild_id, channel.channel_id);
      // Remove channel from local state
      setChannels(prev => prev.filter(c => 
        !(c.guild_id === channel.guild_id && c.channel_id === channel.channel_id)
      ));
    } catch (err) {
      setError('Failed to remove channel');
      console.error('Error removing channel:', err);
    }
  };

  const handleBanServer = async (channel) => {
    const reason = window.prompt(`Enter reason for banning server "${channel.guild_name}":`);
    if (reason === null) return; // User cancelled
    
    if (!window.confirm(`Are you sure you want to BAN the entire server "${channel.guild_name}"? This will prevent them from subscribing to ANY chat rooms until unbanned.`)) {
      return;
    }
    
    try {
      await serversApi.banServer({
        guild_id: channel.guild_id,
        guild_name: channel.guild_name,
        reason: reason.trim() || 'No reason provided'
      });
      
      // Remove all channels from this server from local state
      setChannels(prev => prev.filter(c => c.guild_id !== channel.guild_id));
      setError(null);
    } catch (err) {
      setError('Failed to ban server');
      console.error('Error banning server:', err);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const parseFormattedContent = (content) => {
    if (!content) return { __html: '' };
    
    // Convert Discord-style markdown to HTML
    let html = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
      .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *italic*
      .replace(/https:\/\/discord\.com\/channels\/\S+/g, '<a href="$&" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">Discord Message</a>')  // Discord links
      .replace(/\n/g, '<br/>');  // Line breaks
    
    return { __html: html };
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
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-500">Room ID: {room.id}</div>
            <div className={`text-sm font-medium ${room.is_active ? 'text-green-600' : 'text-gray-500'}`}>
              {room.is_active ? 'Active' : 'Inactive'}
            </div>
          </div>
          <button
            onClick={handleEditRoom}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            ✏️ Edit Room
          </button>
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
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
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleRemoveChannel(channel)}
                          className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-1 rounded text-sm"
                          title="Remove channel from room"
                        >
                          🗑️ Remove
                        </button>
                        <button
                          onClick={() => handleBanServer(channel)}
                          className="bg-red-700 hover:bg-red-800 text-white px-3 py-1 rounded text-sm"
                          title="Ban entire server from all chat rooms"
                        >
                          🚫 Ban Server
                        </button>
                      </div>
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
                      <div 
                        className="mt-1 text-gray-800 whitespace-pre-wrap"
                        dangerouslySetInnerHTML={parseFormattedContent(message.formatted_content || message.content)}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Edit Room Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Room</h3>
              <form onSubmit={handleUpdateRoom} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Room Name</label>
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Servers</label>
                  <input
                    type="number"
                    value={editForm.max_servers}
                    onChange={(e) => setEditForm(prev => ({ ...prev, max_servers: parseInt(e.target.value) }))}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                    min="1"
                    max="200"
                    required
                  />
                </div>
                
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editForm.is_active}
                      onChange={(e) => setEditForm(prev => ({ ...prev, is_active: e.target.checked }))}
                      className="mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700">Room is active</span>
                  </label>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={updating}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
                  >
                    {updating ? 'Updating...' : 'Update Room'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RoomDetails;