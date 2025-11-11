import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Server, 
  BarChart3, 
  Settings, 
  LogOut,
  Menu,
  X,
  Wifi,
  WifiOff,
  Bell
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useWebSocket } from '../hooks/useWebSocket';
import NotificationDropdown from './NotificationDropdown';

const Layout = ({ children }) => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { isConnected, connectionStatus, notifications } = useWebSocket();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Rooms', href: '/rooms', icon: MessageSquare },
    { name: 'Servers', href: '/servers', icon: Server },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (href) => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  const handleLogout = () => {
    logout();
  };

  const unreadNotifications = notifications.filter(n => !n.read).length;

  return (
    <div className="h-screen flex bg-gray-100">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
        </div>
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-gray-800 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-4 bg-gray-900">
          <h1 className="text-white text-lg font-semibold">
            Global Chat Admin
          </h1>
          <button
            className="lg:hidden text-gray-300 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`
                      flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors
                      ${isActive(item.href)
                        ? 'bg-primary-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }
                    `}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Connection Status */}
        <div className="absolute bottom-20 left-4 right-4">
          <div className="flex items-center px-4 py-2 text-sm">
            {isConnected ? (
              <div className="flex items-center text-green-400">
                <Wifi className="h-4 w-4 mr-2" />
                <span>Connected</span>
              </div>
            ) : (
              <div className="flex items-center text-red-400">
                <WifiOff className="h-4 w-4 mr-2" />
                <span className="capitalize">{connectionStatus}</span>
              </div>
            )}
          </div>
        </div>

        {/* User menu */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="flex items-center">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.username || 'Admin'}
              </p>
              <p className="text-xs text-gray-300 truncate">
                {user?.is_superuser ? 'Super Admin' : 'Admin'}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="ml-3 p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center">
              <button
                className="lg:hidden p-2 text-gray-500 hover:text-gray-600"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="h-6 w-6" />
              </button>
              <h1 className="ml-4 lg:ml-0 text-xl font-semibold text-gray-900">
                {navigation.find(item => isActive(item.href))?.name || 'Dashboard'}
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <NotificationDropdown 
                notifications={notifications} 
                unreadCount={unreadNotifications}
              />

              {/* Connection indicator */}
              <div className="flex items-center">
                {isConnected ? (
                  <div className="flex items-center text-green-600">
                    <div className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                    <span className="text-sm font-medium">Live</span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-600">
                    <div className="h-2 w-2 bg-red-500 rounded-full mr-2" />
                    <span className="text-sm font-medium">Offline</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto bg-gray-50 custom-scrollbar">
          <div className="p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;