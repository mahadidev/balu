import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { WebSocketProvider } from './hooks/useWebSocket';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Rooms from './pages/Rooms';
import RoomDetails from './pages/RoomDetails';
import Servers from './pages/Servers';
import ServerDetails from './pages/ServerDetails';
import BannedServers from './pages/BannedServers';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected Routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout>
                    <Navigate to="/dashboard" replace />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/rooms" element={
                <ProtectedRoute>
                  <Layout>
                    <Rooms />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/rooms/:roomId" element={
                <ProtectedRoute>
                  <Layout>
                    <RoomDetails />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/servers" element={
                <ProtectedRoute>
                  <Layout>
                    <Servers />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/servers/:guildId" element={
                <ProtectedRoute>
                  <Layout>
                    <ServerDetails />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/banned-servers" element={
                <ProtectedRoute>
                  <Layout>
                    <BannedServers />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/analytics" element={
                <ProtectedRoute>
                  <Layout>
                    <Analytics />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/settings" element={
                <ProtectedRoute>
                  <Layout>
                    <Settings />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </Router>
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;