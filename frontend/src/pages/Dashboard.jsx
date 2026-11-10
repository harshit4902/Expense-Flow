import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { formatRupees, formatDate } from '../services/utils';
import { 
  TrendingUp, 
  TrendingDown, 
  PiggyBank, 
  Scale, 
  Target, 
  ArrowUpRight,
  ArrowDownLeft,
  Calendar
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  LineChart, 
  Line 
} from 'recharts';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b'];

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

export default function Dashboard() {
  const today = new Date();
  const [summary, setSummary] = useState(null);
  const [categoryBreakdown, setCategoryBreakdown] = useState([]);
  const [monthlyTrends, setMonthlyTrends] = useState([]);
  const [savingsTrends, setSavingsTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  // Month & Year state for Category Expense Pie Chart
  const [pieMonth, setPieMonth] = useState(today.getMonth() + 1);
  const [pieYear, setPieYear] = useState(today.getFullYear());
  const [pieLoading, setPieLoading] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    fetchCategoryBreakdown(pieMonth, pieYear);
  }, [pieMonth, pieYear]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [sumRes, trendRes, savRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/monthly-trends?months=6'),
        api.get('/dashboard/savings-trends'),
      ]);
      setSummary(sumRes.data);
      setMonthlyTrends(trendRes.data);
      setSavingsTrends(savRes.data);
    } catch (err) {
      console.error("Dashboard error:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategoryBreakdown = async (m, y) => {
    try {
      setPieLoading(true);
      const res = await api.get(`/dashboard/category-breakdown?month=${m}&year=${y}`);
      setCategoryBreakdown(res.data);
    } catch (err) {
      console.error("Failed to load category breakdown:", err);
    } finally {
      setPieLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Income',
      amount: summary?.total_income,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
      border: 'border-emerald-100',
    },
    {
      title: 'Total Expenses',
      amount: summary?.total_expenses,
      icon: TrendingDown,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
      border: 'border-rose-100',
    },
    {
      title: 'Monthly Balance',
      amount: summary?.monthly_balance,
      icon: Scale,
      color: summary?.monthly_balance >= 0 ? 'text-indigo-600' : 'text-amber-600',
      bg: summary?.monthly_balance >= 0 ? 'bg-indigo-50' : 'bg-amber-50',
      border: 'border-indigo-100',
    },
    {
      title: 'Current Savings',
      amount: summary?.current_savings,
      icon: PiggyBank,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      border: 'border-purple-100',
    },
    {
      title: 'Budget Spent',
      amount: summary?.budget_spent,
      subText: `Limit: ${formatRupees(summary?.total_budget)}`,
      icon: Target,
      color: 'text-sky-600',
      bg: 'bg-sky-50',
      border: 'border-sky-100',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Overview of your income, expenses, savings & budgets</p>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {cards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className={`p-5 rounded-2xl bg-white border ${card.border} shadow-sm flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{card.title}</span>
                <div className={`p-2 rounded-xl ${card.bg} ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div>
                <span className="text-xl font-bold text-slate-900 tracking-tight">
                  {formatRupees(card.amount)}
                </span>
                {card.subText && (
                  <p className="text-xs text-slate-600 mt-1 font-medium">{card.subText}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Income vs Expense Chart */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
            Income vs. Expenses Trend
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyTrends}>
                <XAxis dataKey="month_name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `₹${v/100}`} />
                <Tooltip 
                  formatter={(val) => [formatRupees(val), '']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="income" name="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expense" name="Expense" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Pie Chart with Month Selector */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Expense Breakdown by Category
            </h2>

            {/* Month & Year Selectors */}
            <div className="flex items-center gap-2">
              <select
                value={pieMonth}
                onChange={(e) => setPieMonth(parseInt(e.target.value))}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 text-xs font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
              >
                {MONTH_NAMES.map((name, idx) => (
                  <option key={idx + 1} value={idx + 1}>
                    {name}
                  </option>
                ))}
              </select>

              <select
                value={pieYear}
                onChange={(e) => setPieYear(parseInt(e.target.value))}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 text-xs font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
              >
                {[2024, 2025, 2026, 2027].map((yr) => (
                  <option key={yr} value={yr}>
                    {yr}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {pieLoading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : categoryBreakdown.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-sm">
              <Calendar className="w-8 h-8 text-slate-300 mb-2" />
              <p>No expenses recorded for {MONTH_NAMES[pieMonth - 1]} {pieYear}.</p>
            </div>
          ) : (
            <div className="h-64 flex items-center">
              <ResponsiveContainer width="60%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryBreakdown}
                    dataKey="total_amount"
                    nameKey="category_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    innerRadius={50}
                    paddingAngle={3}
                  >
                    {categoryBreakdown.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val) => [formatRupees(val), 'Spent']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="w-[40%] space-y-2 overflow-y-auto max-h-56 pr-2">
                {categoryBreakdown.map((item, idx) => (
                  <div key={item.category_id} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 truncate">
                      <span 
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0" 
                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                      />
                      <span className="truncate font-medium text-slate-700">{item.category_name}</span>
                    </div>
                    <span className="font-semibold text-slate-900 ml-2">{item.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Transactions Table */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
          Recent Transactions
        </h2>
        {summary?.recent_transactions?.length === 0 ? (
          <p className="text-sm text-slate-600 py-4 text-center">No transactions recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-semibold text-slate-600 uppercase">
                  <th className="pb-3 font-semibold">Description</th>
                  <th className="pb-3 font-semibold">Category</th>
                  <th className="pb-3 font-semibold">Date</th>
                  <th className="pb-3 font-semibold text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {summary?.recent_transactions?.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3.5 font-medium text-slate-900 flex items-center gap-2.5">
                      <div className={`p-1.5 rounded-lg ${tx.type === 'income' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                        {tx.type === 'income' ? <ArrowDownLeft className="w-3.5 h-3.5" /> : <ArrowUpRight className="w-3.5 h-3.5" />}
                      </div>
                      {tx.description}
                    </td>
                    <td className="py-3.5 text-slate-600">{tx.category?.name || 'General'}</td>
                    <td className="py-3.5 text-slate-600">{formatDate(tx.transaction_date)}</td>
                    <td className={`py-3.5 text-right font-semibold ${tx.type === 'income' ? 'text-emerald-600' : 'text-slate-900'}`}>
                      {tx.type === 'income' ? '+' : '-'}{formatRupees(tx.amount)}
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
