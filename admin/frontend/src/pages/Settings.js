import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import LoadingSpinner from '../components/LoadingSpinner';
import apiService from '../services/api';

function Settings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [settings, setSettings] = useState({
    system: {
      bot_status: 'online',
      max_message_length: 2000,
      rate_limit_messages: 5,
      rate_limit_window: 60,
      auto_moderation: true,
      log_level: 'INFO'
    },
    permissions: {
      allow_room_creation: true,
      require_admin_approval: false,
      max_rooms_per_server: 10,
      allow_dm_notifications: true
    },
    notifications: {
      webhook_url: '',
      notify_new_servers: true,
      notify_errors: true,
      notify_high_activity: false,
      activity_threshold: 1000
    }
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await apiService.get('/api/settings');
      setSettings(data);
      setError(null);
    } catch (err) {
      setError('Failed to load settings');
      console.error('Error fetching settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (section) => {
    setSaving(true);
    try {
      await apiService.put('/api/settings', {
        section,
        settings: settings[section]
      });
      setSuccess(`${section.charAt(0).toUpperCase() + section.slice(1)} settings saved successfully!`);
      setError(null);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to save settings');
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
        <div className="text-sm text-gray-500">
          Logged in as: {user?.username}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <p className="text-green-600">{success}</p>
        </div>
      )}

      {/* System Settings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">System Configuration</h2>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Bot Status
              </label>
              <select
                value={settings.system.bot_status}
                onChange={(e) => updateSetting('system', 'bot_status', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="online">Online</option>
                <option value="idle">Idle</option>
                <option value="dnd">Do Not Disturb</option>
                <option value="invisible">Invisible</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Message Length
              </label>
              <input
                type="number"
                value={settings.system.max_message_length}
                onChange={(e) => updateSetting('system', 'max_message_length', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                min="100"
                max="4000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Rate Limit (messages per window)
              </label>
              <input
                type="number"
                value={settings.system.rate_limit_messages}
                onChange={(e) => updateSetting('system', 'rate_limit_messages', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                min="1"
                max="20"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Rate Limit Window (seconds)
              </label>
              <input
                type="number"
                value={settings.system.rate_limit_window}
                onChange={(e) => updateSetting('system', 'rate_limit_window', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                min="30"
                max="300"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Log Level
              </label>
              <select
                value={settings.system.log_level}
                onChange={(e) => updateSetting('system', 'log_level', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="DEBUG">Debug</option>
                <option value="INFO">Info</option>
                <option value="WARNING">Warning</option>
                <option value="ERROR">Error</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.system.auto_moderation}
                onChange={(e) => updateSetting('system', 'auto_moderation', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">
                Enable Auto Moderation
              </label>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={() => handleSave('system')}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save System Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Permission Settings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Permissions</h2>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Rooms per Server
              </label>
              <input
                type="number"
                value={settings.permissions.max_rooms_per_server}
                onChange={(e) => updateSetting('permissions', 'max_rooms_per_server', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                min="1"
                max="50"
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.permissions.allow_room_creation}
                  onChange={(e) => updateSetting('permissions', 'allow_room_creation', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Allow Room Creation
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.permissions.require_admin_approval}
                  onChange={(e) => updateSetting('permissions', 'require_admin_approval', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Require Admin Approval for New Rooms
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.permissions.allow_dm_notifications}
                  onChange={(e) => updateSetting('permissions', 'allow_dm_notifications', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Allow DM Notifications
                </label>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={() => handleSave('permissions')}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Permission Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Notifications</h2>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Webhook URL (Optional)
              </label>
              <input
                type="url"
                value={settings.notifications.webhook_url}
                onChange={(e) => updateSetting('notifications', 'webhook_url', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="https://discord.com/api/webhooks/..."
              />
              <p className="mt-1 text-sm text-gray-500">
                Discord webhook URL for system notifications
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                High Activity Threshold
              </label>
              <input
                type="number"
                value={settings.notifications.activity_threshold}
                onChange={(e) => updateSetting('notifications', 'activity_threshold', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                min="100"
                max="10000"
              />
              <p className="mt-1 text-sm text-gray-500">
                Messages per hour to trigger high activity alert
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.notifications.notify_new_servers}
                  onChange={(e) => updateSetting('notifications', 'notify_new_servers', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Notify on New Servers
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.notifications.notify_errors}
                  onChange={(e) => updateSetting('notifications', 'notify_errors', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Notify on Errors
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.notifications.notify_high_activity}
                  onChange={(e) => updateSetting('notifications', 'notify_high_activity', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">
                  Notify on High Activity
                </label>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={() => handleSave('notifications')}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Notification Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white shadow rounded-lg border border-red-200">
        <div className="px-6 py-4 border-b border-red-200 bg-red-50">
          <h2 className="text-lg font-medium text-red-900">Danger Zone</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-sm font-medium text-gray-900">Reset All Settings</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Reset all system settings to their default values. This action cannot be undone.
                </p>
              </div>
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
                    // Handle reset
                  }
                }}
                className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Reset Settings
              </button>
            </div>

            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-sm font-medium text-gray-900">Clear All Data</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Delete all messages, rooms, and statistics. This will keep server and channel registrations.
                </p>
              </div>
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear all data? This will delete all messages and cannot be undone.')) {
                    // Handle data clear
                  }
                }}
                className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Clear Data
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;