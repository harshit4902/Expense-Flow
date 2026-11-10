import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { formatRupees, rupeesToPaise, formatDate } from '../services/utils';
import { 
  PiggyBank, 
  ArrowUpRight, 
  ArrowDownLeft, 
  SlidersHorizontal, 
  History, 
  PlusCircle, 
  MinusCircle, 
  X 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip 
} from 'recharts';

export default function Savings() {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [trends, setSavingsTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [activeModal, setActiveModal] = useState(null); // 'initialize', 'deposit', 'withdraw', 'adjust'
  const [amountInput, setAmountInput] = useState('');
  const [descInput, setDescInput] = useState('');
  const [modalError, setModalError] = useState('');

  useEffect(() => {
    fetchSavingsData();
  }, []);

  const fetchSavingsData = async () => {
    try {
      setLoading(true);
      const [sumRes, histRes, trendRes] = await Promise.all([
        api.get('/savings/summary'),
        api.get('/savings/history'),
        api.get('/dashboard/savings-trends'),
      ]);
      setSummary(sumRes.data);
      setHistory(histRes.data.items);
      setSavingsTrends(trendRes.data);
    } catch (err) {
      console.error('Error fetching savings data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleModalSubmit = async (e) => {
    e.preventDefault();
    setModalError('');
    const paise = rupeesToPaise(amountInput);

    try {
      if (activeModal === 'initialize') {
        await api.post('/savings/initialize', { amount: paise, description: descInput });
      } else if (activeModal === 'deposit') {
        if (paise <= 0) { setModalError('Amount must be positive'); return; }
        await api.post('/savings/deposit', { amount: paise, description: descInput });
      } else if (activeModal === 'withdraw') {
        if (paise <= 0) { setModalError('Amount must be positive'); return; }
        await api.post('/savings/withdraw', { amount: paise, description: descInput });
      } else if (activeModal === 'adjust') {
        await api.patch('/savings/balance', { target_balance: paise, description: descInput });
      }

      setActiveModal(null);
      setAmountInput('');
      setDescInput('');
      fetchSavingsData();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Operation failed.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Current Savings',
      amount: summary?.current_savings,
      icon: PiggyBank,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
    {
      title: 'Initial Savings',
      amount: summary?.initial_savings,
      icon: History,
      color: 'text-slate-600',
      bg: 'bg-slate-50',
    },
    {
      title: 'Total Deposits',
      amount: summary?.total_deposits,
      icon: ArrowDownLeft,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      title: 'Total Withdrawals',
      amount: summary?.total_withdrawals,
      icon: ArrowUpRight,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header & Quick Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Savings Management</h1>
          <p className="text-sm text-slate-500 mt-0.5">Track your savings reserve independently from everyday spending</p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {!summary?.has_initial_balance && (
            <button
              onClick={() => { setActiveModal('initialize'); setDescInput('Initial savings setup'); setModalError(''); }}
              className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-medium text-sm transition-colors shadow-sm"
            >
              Set Initial Savings
            </button>
          )}
          <button
            onClick={() => { setActiveModal('deposit'); setDescInput('Savings deposit'); setModalError(''); }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <PlusCircle className="w-4 h-4" /> Deposit
          </button>
          <button
            onClick={() => { setActiveModal('withdraw'); setDescInput('Savings withdrawal'); setModalError(''); }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <MinusCircle className="w-4 h-4" /> Withdraw
          </button>
          <button
            onClick={() => { setActiveModal('adjust'); setDescInput('True-up balance to match actual savings'); setModalError(''); }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium text-sm transition-colors"
          >
            <SlidersHorizontal className="w-4 h-4" /> Adjust Balance
          </button>
        </div>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div key={i} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{c.title}</span>
                <div className={`p-2 rounded-xl ${c.bg} ${c.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <span className="text-2xl font-bold text-slate-900 tracking-tight">
                {formatRupees(c.amount)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Savings Growth Chart */}
      {trends.length > 0 && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
            Savings Growth Over Time
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends}>
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickFormatter={(d) => formatDate(d)} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `₹${v/100}`} />
                <Tooltip 
                  formatter={(val) => [formatRupees(val), 'Balance']}
                  labelFormatter={(d) => formatDate(d)}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Line type="monotone" dataKey="running_balance" stroke="#9333ea" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* History Ledger Table */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
          Savings Ledger History
        </h2>
        {history.length === 0 ? (
          <p className="text-sm text-slate-500 py-6 text-center">No savings activities recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase">
                <tr>
                  <th className="pb-3 font-semibold">Activity</th>
                  <th className="pb-3 font-semibold">Type</th>
                  <th className="pb-3 font-semibold">Date</th>
                  <th className="pb-3 font-semibold text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3.5 font-medium text-slate-900">{tx.description}</td>
                    <td className="py-3.5">
                      <span className="capitalize px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                        {tx.type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 text-slate-500">{formatDate(tx.transaction_date)}</td>
                    <td className={`py-3.5 text-right font-semibold ${
                      tx.type === 'deposit' || (tx.type === 'balance_adjustment' && tx.amount >= 0) || tx.type === 'initial_balance'
                        ? 'text-emerald-600'
                        : 'text-rose-600'
                    }`}>
                      {tx.amount >= 0 ? '+' : ''}{formatRupees(tx.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Action Modal */}
      {activeModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-xl border border-slate-100 max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 capitalize">
                {activeModal === 'adjust' ? 'Correct / Adjust Savings Balance' : `${activeModal} Savings`}
              </h2>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="my-3 p-3 rounded-xl bg-rose-50 text-rose-700 text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleModalSubmit} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  {activeModal === 'adjust' ? 'Actual Current Savings (in Rupees ₹)' : 'Amount (in Rupees ₹)'}
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 50000"
                  value={amountInput}
                  onChange={(e) => setAmountInput(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Note / Description
                </label>
                <input
                  type="text"
                  placeholder="Optional description"
                  value={descInput}
                  onChange={(e) => setDescInput(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm"
                >
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

