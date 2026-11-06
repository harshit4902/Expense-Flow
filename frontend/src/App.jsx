import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import FloatingChatWidget from './components/FloatingChatWidget';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import AIChatAssistant from './pages/AIChatAssistant';
import Savings from './pages/Savings';
import Budgets from './pages/Budgets';
import Reports from './pages/Reports';
import Categories from './pages/Categories';

export default function App() {
  const { isAuthenticated, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [dataRefreshKey, setDataRefreshKey] = useState(0);

  const handleDataUpdated = () => {
    // Incrementing key re-renders and re-fetches current active view (Dashboard, Transactions, etc.)
    setDataRefreshKey(prev => prev + 1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <Dashboard key={dataRefreshKey} />;
      case 'transactions':
        return <Transactions key={dataRefreshKey} />;
      case 'ai-assistant':
        return <AIChatAssistant key={dataRefreshKey} />;
      case 'savings':
        return <Savings key={dataRefreshKey} />;
      case 'budgets':
        return <Budgets key={dataRefreshKey} />;
      case 'reports':
        return <Reports key={dataRefreshKey} />;
      case 'categories':
        return <Categories key={dataRefreshKey} />;
      default:
        return <Dashboard key={dataRefreshKey} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />

      {/* Main Content Area */}
      <main className="flex-1 ml-64 p-8 max-w-7xl">
        {renderContent()}
      </main>

      {/* Global Floating AI Chatbot Widget */}
      <FloatingChatWidget onDataUpdated={handleDataUpdated} />
    </div>
  );
}
