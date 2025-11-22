import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { createWebSocketConnection } from '../services/api';
import { useAuth } from './useAuth';

const WebSocketContext = createContext();

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [liveStats, setLiveStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [wsData, setWsData] = useState(null); // For passing WebSocket data to components
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    if (isAuthenticated && user) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, user]);

  const connect = () => {
    console.log('🚀 Attempting to connect WebSocket...');
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('ℹ️ WebSocket already connected');
      return;
    }

    console.log('📱 Setting connection status to connecting...');
    setConnectionStatus('connecting');

    wsRef.current = createWebSocketConnection(
      handleMessage,
      handleError,
      handleOpen,
      handleClose
    );
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
    reconnectAttempts.current = 0;
  };

  const handleOpen = () => {
    console.log('🎉 WebSocket handleOpen triggered');
    setIsConnected(true);
    setConnectionStatus('connected');
    reconnectAttempts.current = 0;
  };

  const handleClose = (event) => {
    console.log('WebSocket disconnected:', event.reason);
    setIsConnected(false);
    setConnectionStatus('disconnected');

    // Attempt to reconnect if authenticated and not intentionally closed
    if (isAuthenticated && event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
      const delay = Math.pow(2, reconnectAttempts.current) * 1000; // Exponential backoff
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);
      
      setConnectionStatus('reconnecting');
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttempts.current += 1;
        connect();
      }, delay);
    }
  };

  const handleError = (error) => {
    console.error('💥 WebSocket error occurred:', error);
    setConnectionStatus('error');
    
    addNotification({
      type: 'error',
      title: 'Connection Error',
      message: 'WebSocket connection error occurred'
    });
  };

  const handleMessage = (data) => {
    console.log('🔄 Handling WebSocket message:', data.type);
    
    switch (data.type) {
      case 'connection_confirmed':
        console.log('✅ WebSocket connection confirmed');
        break;

      case 'authentication_success':
        console.log('🔐 WebSocket authenticated successfully');
        break;

      case 'authentication_error':
        console.error('🚫 WebSocket authentication failed:', data.message);
        addNotification({
          type: 'error',
          title: 'Authentication Error',
          message: data.message || 'WebSocket authentication failed'
        });
        break;

      case 'live_stats':
        setLiveStats(data.data);
        break;

      case 'system_notification':
        addNotification({
          type: data.data.level || 'info',
          title: 'System Notification',
          message: data.data.message,
          component: data.data.component
        });
        break;

      case 'room_update':
        addNotification({
          type: 'info',
          title: 'Room Update',
          message: `Room "${data.data.room?.name}" was ${data.data.action}`
        });
        break;

      case 'channel_update':
        addNotification({
          type: 'info',
          title: 'Channel Update',
          message: `Channel ${data.data.channel?.guild_name}/#${data.data.channel?.channel_name} was ${data.data.action}`
        });
        break;

      case 'message_activity':
        // Handle real-time message activity updates
        console.log('Message activity:', data.data);
        break;

      case 'new_message':
        // Handle new chat messages for admin panel
        console.log('New message received:', data.data);
        setWsData({
          type: 'message',
          room_id: data.data.room_id,
          data: data.data,
          timestamp: data.timestamp
        });
        break;

      case 'pong':
        // Handle ping/pong for keep-alive
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  const addNotification = (notification) => {
    const id = Date.now().toString();
    const newNotification = {
      id,
      timestamp: new Date().toISOString(),
      ...notification
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 49)]); // Keep max 50 notifications

    // Auto-remove non-error notifications after 10 seconds
    if (notification.type !== 'error') {
      setTimeout(() => {
        removeNotification(id);
      }, 10000);
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  };

  const ping = () => {
    return sendMessage({
      type: 'ping',
      timestamp: Date.now()
    });
  };

  // Keep-alive ping every 30 seconds
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      ping();
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected]);

  const value = {
    isConnected,
    connectionStatus,
    liveStats,
    notifications,
    wsData,
    connect,
    disconnect,
    sendMessage,
    removeNotification,
    clearNotifications,
    addNotification
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};