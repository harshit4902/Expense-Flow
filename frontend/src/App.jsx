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
import { Menu, Wallet } from 'lucide-react';

export default function App() {
  const { isAuthenticated, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [isMobileOpen, setIsMobileOpen] = useState(false);
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
    <div className="min-h-screen bg-slate-50 flex flex-col lg:flex-row">
      {/* Mobile Top Header */}
      <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsMobileOpen(true)}
            aria-label="Open Navigation Menu"
            className="p-2 -ml-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
            <Wallet className="w-4 h-4" />
          </div>
          <span className="font-bold text-base text-slate-900 tracking-tight">ExpenseFlow</span>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 capitalize">
          {currentTab.replace('-', ' ')}
        </span>
      </header>

      {/* Sidebar (Responsive drawer on mobile/tablet, fixed column on desktop) */}
      <Sidebar 
        currentTab={currentTab} 
        setCurrentTab={setCurrentTab}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full lg:ml-64 p-3 sm:p-5 md:p-6 lg:p-8 max-w-7xl mx-auto overflow-x-hidden">
        {renderContent()}
      </main>

      {/* Global Floating AI Chatbot Widget */}
      <FloatingChatWidget onDataUpdated={handleDataUpdated} />
    </div>
  );
}
