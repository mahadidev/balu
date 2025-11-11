import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageSquare, 
  Server, 
  Users, 
  Activity, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  RefreshCw
} from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { useWebSocket } from '../hooks/useWebSocket';
import { analyticsApi, systemApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

const Dashboard = () => {
  const { liveStats, isConnected } = useWebSocket();
  const [messageStats, setMessageStats] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [messageStatsResponse, healthResponse] = await Promise.all([
        analyticsApi.getMessageStats(7),
        analyticsApi.getSystemHealth()
      ]);

      setMessageStats(messageStatsResponse.data);
      setSystemHealth(healthResponse.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  // Stats cards data
  const statsCards = [
    {
      title: 'Active Rooms',
      value: liveStats?.active_rooms || 0,
      icon: MessageSquare,
      color: 'blue',
      change: '+12%',
      changeType: 'increase'
    },
    {
      title: 'Connected Servers',
      value: liveStats?.active_channels || 0,
      icon: Server,
      color: 'green',
      change: '+8%',
      changeType: 'increase'
    },
    {
      title: 'Messages Today',
      value: liveStats?.messages_last_day || 0,
      icon: Activity,
      color: 'purple',
      change: '+24%',
      changeType: 'increase'
    },
    {
      title: 'Messages/Hour',
      value: liveStats?.messages_last_hour || 0,
      icon: TrendingUp,
      color: 'orange',
      change: '+5%',
      changeType: 'increase'
    }
  ];

  // Chart data
  const chartData = {
    labels: messageStats?.daily_stats?.map(stat => 
      new Date(stat.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ) || [],
    datasets: [
      {
        label: 'Messages',
        data: messageStats?.daily_stats?.map(stat => stat.count) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Overview of your global chat system</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Connection status */}
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <div className="flex items-center text-green-600">
                <CheckCircle className="h-4 w-4 mr-1" />
                <span className="text-sm font-medium">Live Updates</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600">
                <AlertTriangle className="h-4 w-4 mr-1" />
                <span className="text-sm font-medium">Offline</span>
              </div>
            )}
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn btn-secondary btn-sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="card">
              <div className="card-body">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value.toLocaleString()}</p>
                    <p className={`text-sm ${
                      stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                    } flex items-center mt-1`}>
                      <ArrowUpRight className="h-3 w-3 mr-1" />
                      {stat.change} vs last week
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${
                    stat.color === 'blue' ? 'bg-blue-100' :
                    stat.color === 'green' ? 'bg-green-100' :
                    stat.color === 'purple' ? 'bg-purple-100' : 'bg-orange-100'
                  }`}>
                    <Icon className={`h-6 w-6 ${
                      stat.color === 'blue' ? 'text-blue-600' :
                      stat.color === 'green' ? 'text-green-600' :
                      stat.color === 'purple' ? 'text-purple-600' : 'text-orange-600'
                    }`} />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Message Activity Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Message Activity</h3>
            <p className="text-sm text-gray-600">Last 7 days</p>
          </div>
          <div className="card-body">
            <div className="chart-container">
              {messageStats?.daily_stats ? (
                <Line data={chartData} options={chartOptions} />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <LoadingSpinner text="Loading chart..." />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
            <p className="text-sm text-gray-600">Current status</p>
          </div>
          <div className="card-body space-y-4">
            {systemHealth ? (
              <>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className={`h-3 w-3 rounded-full mr-3 ${
                      systemHealth.database_status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm font-medium">Database</span>
                  </div>
                  <span className={`text-sm ${
                    systemHealth.database_status === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {systemHealth.database_status}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className={`h-3 w-3 rounded-full mr-3 ${
                      systemHealth.cache_status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm font-medium">Cache</span>
                  </div>
                  <span className={`text-sm ${
                    systemHealth.cache_status === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {systemHealth.cache_status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{systemHealth.total_rooms}</p>
                    <p className="text-sm text-gray-600">Total Rooms</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{systemHealth.total_channels}</p>
                    <p className="text-sm text-gray-600">Active Channels</p>
                  </div>
                </div>
              </>
            ) : (
              <LoadingSpinner text="Loading system health..." />
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          <p className="text-sm text-gray-600">Common administrative tasks</p>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/rooms" className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <MessageSquare className="h-8 w-8 text-blue-600 mr-4" />
              <div>
                <h4 className="font-medium text-gray-900">Manage Rooms</h4>
                <p className="text-sm text-gray-600">Create and configure chat rooms</p>
              </div>
            </Link>

            <Link to="/servers" className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <Server className="h-8 w-8 text-green-600 mr-4" />
              <div>
                <h4 className="font-medium text-gray-900">View Servers</h4>
                <p className="text-sm text-gray-600">Monitor connected Discord servers</p>
              </div>
            </Link>

            <Link to="/analytics" className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <Activity className="h-8 w-8 text-purple-600 mr-4" />
              <div>
                <h4 className="font-medium text-gray-900">View Analytics</h4>
                <p className="text-sm text-gray-600">Detailed usage statistics</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;