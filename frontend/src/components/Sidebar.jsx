import React from 'react';
import { 
  LayoutDashboard, 
  ArrowLeftRight, 
  PiggyBank, 
  Target, 
  BarChart3, 
  Tags, 
  Bot, 
  LogOut, 
  Wallet,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navigation = [
  { name: 'Dashboard', id: 'dashboard', icon: LayoutDashboard },
  { name: 'Transactions', id: 'transactions', icon: ArrowLeftRight },
  { name: 'AI Assistant', id: 'ai-assistant', icon: Bot, badge: 'New' },
  { name: 'Savings', id: 'savings', icon: PiggyBank },
  { name: 'Budgets', id: 'budgets', icon: Target },
  { name: 'Reports', id: 'reports', icon: BarChart3 },
  { name: 'Categories', id: 'categories', icon: Tags },
];

export default function Sidebar({ currentTab, setCurrentTab, isMobileOpen, setIsMobileOpen }) {
  const { user, logout } = useAuth();

  const handleNavClick = (id) => {
    setCurrentTab(id);
    if (setIsMobileOpen) {
      setIsMobileOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div 
          onClick={() => setIsMobileOpen(false)}
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      {/* Sidebar Container: Drawer on mobile/tablet, Fixed on desktop */}
      <aside className={`
        fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col h-full
        transition-transform duration-300 ease-in-out
        ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Brand Logo & Close button on mobile */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-100">
              <Wallet className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900 tracking-tight">ExpenseFlow</span>
              <span className="block text-[10px] font-semibold text-slate-500 tracking-wider uppercase">Finance Tracker</span>
            </div>
          </div>
          {/* Close button for small screens */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav Links */}
        <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-5 h-5 ${isActive ? 'text-indigo-600' : 'text-slate-500'}`} />
                  {item.name}
                </div>
                {item.badge && (
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* User profile & Logout */}
        <div className="p-4 border-t border-slate-100 bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 font-semibold flex items-center justify-center text-xs flex-shrink-0">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="truncate">
                <p className="text-sm font-semibold text-slate-800 truncate">{user?.name || 'User'}</p>
                <p className="text-xs text-slate-500 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
