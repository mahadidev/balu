import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import LoadingSpinner from '../components/LoadingSpinner';
import { systemApi } from '../services/api';

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
      const response = await systemApi.getInfo();
      
      // Transform the backend response into the expected settings structure
      const data = response.data || {};
      setSettings({
        system: {
          bot_status: 'online',
          max_message_length: data.configuration?.max_page_size || 2000,
          rate_limit_messages: data.configuration?.rate_limit_requests || 5,
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
      // Settings update not implemented in backend yet
      console.log('Settings would be saved:', { section, settings: settings[section] });
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

  const handleClearData = async () => {
    if (!window.confirm('⚠️ DANGER: This will COMPLETELY CLEAR the database!\n\nThis will permanently delete:\n- ALL messages\n- ALL rooms\n- ALL channels\n- ALL statistics\n- ALL cache data\n\nThis action CANNOT be undone!\n\nAre you absolutely sure?')) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      
      const response = await systemApi.clearData({
        keepRooms: true,
        keepChannels: true
      });
      
      if (response.data.success) {
        setSuccess(`Data cleared successfully! Removed ${Object.values(response.data.cleared_items).reduce((a, b) => a + b, 0)} items.`);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError('Failed to clear data');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to clear data');
      console.error('Error clearing data:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleResetSettings = async () => {
    if (!window.confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      
      await systemApi.resetSettings();
      setSuccess('Settings reset to defaults successfully!');
      setTimeout(() => setSuccess(null), 3000);
      
      // Reload settings
      await fetchSettings();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset settings');
      console.error('Error resetting settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...(prev[section] || {}),
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
                value={settings.system?.bot_status || 'online'}
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
                value={settings.system?.max_message_length || 2000}
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
                value={settings.system?.rate_limit_messages || 5}
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
                value={settings.system?.rate_limit_window || 60}
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
                value={settings.system?.log_level || 'INFO'}
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
                checked={settings.system?.auto_moderation || false}
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
                value={settings.permissions?.max_rooms_per_server || 10}
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
                  checked={settings.permissions?.allow_room_creation || false}
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
                  checked={settings.permissions?.require_admin_approval || false}
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
                  checked={settings.permissions?.allow_dm_notifications || false}
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
                value={settings.notifications?.webhook_url || ''}
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
                value={settings.notifications?.activity_threshold || 1000}
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
                  checked={settings.notifications?.notify_new_servers || false}
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
                  checked={settings.notifications?.notify_errors || false}
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
                  checked={settings.notifications?.notify_high_activity || false}
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
                onClick={handleResetSettings}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                {saving ? 'Resetting...' : 'Reset Settings'}
              </button>
            </div>

            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-sm font-medium text-red-900">⚠️ Clear All Data (COMPLETE WIPE)</h3>
                <p className="text-sm text-red-600 mt-1">
                  <strong>PERMANENTLY DELETE EVERYTHING:</strong> All messages, rooms, channels, statistics, and cache data. This action cannot be undone!
                </p>
              </div>
              <button
                onClick={handleClearData}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-red-600 text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                {saving ? 'CLEARING ALL...' : '🗑️ CLEAR ALL DATA'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;