import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import { useWebSocket } from '../hooks/useWebSocket';
import { roomsApi } from '../services/api';

function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [creating, setCreating] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomDescription, setNewRoomDescription] = useState('');
  const [roomPermissions, setRoomPermissions] = useState({
    allow_urls: true,
    allow_files: true,
    allow_mentions: true,
    allow_emojis: true,
    enable_bad_word_filter: false,
    max_message_length: 2000,
    rate_limit_seconds: 5
  });
  const { wsData } = useWebSocket();

  useEffect(() => {
    fetchRooms();
  }, []);

  useEffect(() => {
    if (wsData?.type === 'room_update') {
      fetchRooms();
    }
  }, [wsData]);

  const fetchRooms = async () => {
    try {
      const response = await roomsApi.getAll();
      setRooms(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load rooms');
      console.error('Error fetching rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    if (!newRoomName.trim()) return;
    
    setCreating(true);
    try {
      await roomsApi.create({
        name: newRoomName.trim(),
        max_servers: 50,
        permissions: roomPermissions
      });
      setNewRoomName('');
      setNewRoomDescription('');
      setRoomPermissions({
        allow_urls: true,
        allow_files: true,
        allow_mentions: true,
        allow_emojis: true,
        enable_bad_word_filter: false,
        max_message_length: 2000,
        rate_limit_seconds: 5
      });
      fetchRooms();
    } catch (err) {
      setError('Failed to create room');
      console.error('Error creating room:', err);
    } finally {
      setCreating(false);
    }
  };

  const updatePermission = (key, value) => {
    setRoomPermissions(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Chat Rooms</h1>
        <div className="text-sm text-gray-500">
          Total: {rooms.length} rooms
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Create Room Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Create New Room</h2>
        <form onSubmit={handleCreateRoom} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Room Name
              </label>
              <input
                type="text"
                value={newRoomName}
                onChange={(e) => setNewRoomName(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter room name..."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description (Optional)
              </label>
              <input
                type="text"
                value={newRoomDescription}
                onChange={(e) => setNewRoomDescription(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter description..."
              />
            </div>
          </div>

          {/* Room Permissions */}
          <div className="border-t pt-4">
            <h3 className="text-md font-medium text-gray-900 mb-3">Room Permissions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center">
                  <input
                    id="allow_urls"
                    type="checkbox"
                    checked={roomPermissions.allow_urls}
                    onChange={(e) => updatePermission('allow_urls', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="allow_urls" className="ml-2 text-sm text-gray-700">
                    Allow URLs
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    id="allow_files"
                    type="checkbox"
                    checked={roomPermissions.allow_files}
                    onChange={(e) => updatePermission('allow_files', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="allow_files" className="ml-2 text-sm text-gray-700">
                    Allow Files
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    id="allow_mentions"
                    type="checkbox"
                    checked={roomPermissions.allow_mentions}
                    onChange={(e) => updatePermission('allow_mentions', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="allow_mentions" className="ml-2 text-sm text-gray-700">
                    Allow Mentions
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    id="allow_emojis"
                    type="checkbox"
                    checked={roomPermissions.allow_emojis}
                    onChange={(e) => updatePermission('allow_emojis', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="allow_emojis" className="ml-2 text-sm text-gray-700">
                    Allow Emojis
                  </label>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center">
                  <input
                    id="enable_bad_word_filter"
                    type="checkbox"
                    checked={roomPermissions.enable_bad_word_filter}
                    onChange={(e) => updatePermission('enable_bad_word_filter', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="enable_bad_word_filter" className="ml-2 text-sm text-gray-700">
                    Enable Bad Word Filter
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Max Message Length
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="4000"
                    value={roomPermissions.max_message_length}
                    onChange={(e) => updatePermission('max_message_length', parseInt(e.target.value) || 2000)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Rate Limit (seconds)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="60"
                    value={roomPermissions.rate_limit_seconds}
                    onChange={(e) => updatePermission('rate_limit_seconds', parseInt(e.target.value) || 5)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={creating || !newRoomName.trim()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create Room'}
            </button>
          </div>
        </form>
      </div>

      {/* Rooms List */}
      <div className="bg-white shadow rounded-lg">
        {rooms.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No rooms found. Create your first room to get started!</p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Room
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channels
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Messages Today
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
                {rooms.map((room) => (
                  <tr key={room.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {room.name}
                        </div>
                        {room.description && (
                          <div className="text-sm text-gray-500">
                            {room.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {room.channel_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {room.messages_today || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        room.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {room.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        to={`/rooms/${room.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View Details
                      </Link>
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

export default Rooms;