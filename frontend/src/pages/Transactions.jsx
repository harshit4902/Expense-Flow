import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { formatRupees, rupeesToPaise, formatDate } from '../services/utils';
import { 
  Plus, 
  Search, 
  Filter, 
  Trash2, 
  Edit2, 
  ArrowUpRight, 
  ArrowDownLeft, 
  X 
} from 'lucide-react';

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTx, setEditingTx] = useState(null);
  const [modalType, setModalType] = useState('expense');
  const [modalCategoryId, setModalCategoryId] = useState('');
  const [modalAmount, setModalAmount] = useState('');
  const [modalDescription, setModalDescription] = useState('');
  const [modalDate, setModalDate] = useState(new Date().toISOString().split('T')[0]);
  const [modalError, setModalError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [page, typeFilter, categoryFilter, startDate, endDate]);

  const fetchCategories = async () => {
    try {
      const res = await api.get('/categories');
      setCategories(res.data);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  };

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      let query = `/transactions?page=${page}&page_size=15`;
      if (typeFilter) query += `&type=${typeFilter}`;
      if (categoryFilter) query += `&category_id=${categoryFilter}`;
      if (startDate) query += `&start_date=${startDate}`;
      if (endDate) query += `&end_date=${endDate}`;
      if (search) query += `&search=${encodeURIComponent(search)}`;

      const res = await api.get(query);
      setTransactions(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      console.error('Failed to fetch transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTransactions();
  };

  const openAddModal = (type = 'expense') => {
    setEditingTx(null);
    setModalType(type);
    const defaultCat = categories.find(c => c.type === type);
    setModalCategoryId(defaultCat ? defaultCat.id : '');
    setModalAmount('');
    setModalDescription('');
    setModalDate(new Date().toISOString().split('T')[0]);
    setModalError('');
    setIsModalOpen(true);
  };

  const openEditModal = (tx) => {
    setEditingTx(tx);
    setModalType(tx.type);
    setModalCategoryId(tx.category_id);
    setModalAmount((tx.amount / 100.0).toString());
    setModalDescription(tx.description);
    setModalDate(tx.transaction_date);
    setModalError('');
    setIsModalOpen(true);
  };

  const handleSaveTransaction = async (e) => {
    e.preventDefault();
    setModalError('');

    if (!modalCategoryId) {
      setModalError('Please select a category.');
      return;
    }
    const paise = rupeesToPaise(modalAmount);
    if (paise <= 0) {
      setModalError('Amount must be greater than zero.');
      return;
    }

    try {
      if (editingTx) {
        await api.put(`/transactions/${editingTx.id}`, {
          category_id: parseInt(modalCategoryId),
          amount: paise,
          type: modalType,
          description: modalDescription,
          transaction_date: modalDate,
        });
      } else {
        await api.post('/transactions', {
          category_id: parseInt(modalCategoryId),
          amount: paise,
          type: modalType,
          description: modalDescription,
          transaction_date: modalDate,
        });
      }
      setIsModalOpen(false);
      fetchTransactions();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save transaction.');
    }
  };

  const handleDeleteTransaction = async (id) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) return;
    try {
      await api.delete(`/transactions/${id}`);
      fetchTransactions();
    } catch (err) {
      console.error('Failed to delete transaction:', err);
    }
  };

  const filteredCategories = categories.filter(c => c.type === modalType);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Transactions</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage and record your income and expenses</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => openAddModal('expense')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" /> Add Expense
          </button>
          <button
            onClick={() => openAddModal('income')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" /> Add Income
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transactions..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Types</option>
            <option value="expense">Expenses Only</option>
            <option value="income">Income Only</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Categories</option>
            {categories.map(c => (
              <option key={c.id} value={c.id}>{c.name} ({c.type})</option>
            ))}
          </select>

          <input
            type="date"
            value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <span className="text-slate-400 text-xs">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden">
        {transactions.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No transactions found matching your criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50/75 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-6 font-semibold">Description</th>
                  <th className="py-3 px-6 font-semibold">Category</th>
                  <th className="py-3 px-6 font-semibold">Date</th>
                  <th className="py-3 px-6 font-semibold text-right">Amount</th>
                  <th className="py-3 px-6 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-6 font-medium text-slate-900 flex items-center gap-3">
                      <div className={`p-2 rounded-xl flex-shrink-0 ${tx.type === 'income' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                        {tx.type === 'income' ? <ArrowDownLeft className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                      </div>
                      <span className="truncate">{tx.description}</span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                        {tx.category?.name || 'General'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-slate-500">{formatDate(tx.transaction_date)}</td>
                    <td className={`py-4 px-6 text-right font-semibold ${tx.type === 'income' ? 'text-emerald-600' : 'text-slate-900'}`}>
                      {tx.type === 'income' ? '+' : '-'}{formatRupees(tx.amount)}
                    </td>
                    <td className="py-4 px-6 text-right space-x-2">
                      <button
                        onClick={() => openEditModal(tx)}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                        title="Edit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteTransaction(tx.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Showing page {page} of {totalPages} ({total} items)
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 disabled:opacity-40 hover:bg-slate-50"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 disabled:opacity-40 hover:bg-slate-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add / Edit Transaction Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-xl border border-slate-100 max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">
                {editingTx ? 'Edit Transaction' : `Add ${modalType === 'income' ? 'Income' : 'Expense'}`}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="my-3 p-3 rounded-xl bg-rose-50 text-rose-700 text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleSaveTransaction} className="space-y-4 mt-4">
              {/* Type Switcher */}
              <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
                <button
                  type="button"
                  onClick={() => {
                    setModalType('expense');
                    const def = categories.find(c => c.type === 'expense');
                    if (def) setModalCategoryId(def.id);
                  }}
                  className={`py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    modalType === 'expense' ? 'bg-white text-rose-600 shadow-sm' : 'text-slate-600'
                  }`}
                >
                  Expense
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setModalType('income');
                    const def = categories.find(c => c.type === 'income');
                    if (def) setModalCategoryId(def.id);
                  }}
                  className={`py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    modalType === 'income' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-600'
                  }`}
                >
                  Income
                </button>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Amount (in Rupees ₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 250.50"
                  value={modalAmount}
                  onChange={(e) => setModalAmount(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Category
                </label>
                <select
                  required
                  value={modalCategoryId}
                  onChange={(e) => setModalCategoryId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  {filteredCategories.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Lunch at cafe"
                  value={modalDescription}
                  onChange={(e) => setModalDescription(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Date
                </label>
                <input
                  type="date"
                  required
                  value={modalDate}
                  onChange={(e) => setModalDate(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm"
                >
                  Save Transaction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

