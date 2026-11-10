import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { formatRupees, rupeesToPaise } from '../services/utils';
import { 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  Plus, 
  Trash2, 
  Edit2, 
  X 
} from 'lucide-react';

export default function Budgets() {
  const [budgetSummary, setBudgetSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [isOverall, setIsOverall] = useState(true);
  const [categoryId, setCategoryId] = useState('');
  const [amount, setAmount] = useState('');
  const [modalError, setModalError] = useState('');

  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());

  useEffect(() => {
    fetchExpenseCategories();
  }, []);

  useEffect(() => {
    fetchBudgets();
  }, [month, year]);

  const fetchExpenseCategories = async () => {
    try {
      const res = await api.get('/categories?type=expense');
      setCategories(res.data);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const fetchBudgets = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/budgets?month=${month}&year=${year}`);
      setBudgetSummary(res.data);
    } catch (err) {
      console.error('Error fetching budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveBudget = async (e) => {
    e.preventDefault();
    setModalError('');
    const paise = rupeesToPaise(amount);
    if (paise <= 0) {
      setModalError('Budget amount must be greater than zero.');
      return;
    }

    try {
      if (editingBudget) {
        await api.put(`/budgets/${editingBudget.id}`, { amount: paise });
      } else {
        await api.post('/budgets', {
          amount: paise,
          month: parseInt(month),
          year: parseInt(year),
          category_id: isOverall ? null : parseInt(categoryId),
        });
      }
      setIsModalOpen(false);
      fetchBudgets();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to save budget.');
    }
  };

  const handleDeleteBudget = async (id) => {
    if (!window.confirm('Are you sure you want to delete this budget?')) return;
    try {
      await api.delete(`/budgets/${id}`);
      fetchBudgets();
    } catch (err) {
      console.error('Failed to delete budget:', err);
    }
  };

  const openAddModal = () => {
    setEditingBudget(null);
    setIsOverall(true);
    setCategoryId(categories[0]?.id || '');
    setAmount('');
    setModalError('');
    setIsModalOpen(true);
  };

  const openEditModal = (b) => {
    setEditingBudget(b);
    setIsOverall(b.is_overall);
    setCategoryId(b.category_id || '');
    setAmount((b.amount / 100.0).toString());
    setModalError('');
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Monthly Budgets</h1>
          <p className="text-sm text-slate-500 mt-0.5">Plan spending limits and monitor threshold warnings</p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" /> Create Budget
        </button>
      </div>

      {/* Warnings Banner */}
      {budgetSummary?.has_exceeded_any && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <span><strong>Budget Exceeded!</strong> You have exceeded one or more of your set spending limits for this month.</span>
        </div>
      )}

      {/* Overall Budget Card */}
      {budgetSummary?.overall_budget && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900">Overall Monthly Budget</h3>
                <p className="text-xs text-slate-500">Total expenditure limit across all categories</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                budgetSummary.overall_budget.warning_status === 'exceeded'
                  ? 'bg-rose-100 text-rose-700'
                  : budgetSummary.overall_budget.warning_status === 'warning'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}>
                {budgetSummary.overall_budget.percentage_used}% Used
              </span>
              <button
                onClick={() => openEditModal(budgetSummary.overall_budget)}
                className="p-1 text-slate-400 hover:text-indigo-600"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDeleteBudget(budgetSummary.overall_budget.id)}
                className="p-1 text-slate-400 hover:text-rose-600"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                budgetSummary.overall_budget.warning_status === 'exceeded'
                  ? 'bg-rose-500'
                  : budgetSummary.overall_budget.warning_status === 'warning'
                  ? 'bg-amber-500'
                  : 'bg-indigo-600'
              }`}
              style={{ width: `${Math.min(100, budgetSummary.overall_budget.percentage_used)}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Spent: {formatRupees(budgetSummary.overall_budget.spent)}</span>
            <span>Limit: {formatRupees(budgetSummary.overall_budget.amount)}</span>
            <span>Remaining: {formatRupees(budgetSummary.overall_budget.remaining)}</span>
          </div>
        </div>
      )}

      {/* Category Budgets Grid */}
      <div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
          Category Budgets
        </h2>
        {budgetSummary?.category_budgets?.length === 0 ? (
          <div className="p-8 rounded-2xl bg-white border border-slate-200 text-center text-slate-500 text-sm">
            No category budgets set for this month.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {budgetSummary?.category_budgets?.map((b) => (
              <div key={b.id} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 text-sm">{b.category_name}</span>
                  <div className="flex items-center gap-1.5">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                      b.warning_status === 'exceeded'
                        ? 'bg-rose-100 text-rose-700'
                        : b.warning_status === 'warning'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-emerald-100 text-emerald-700'
                    }`}>
                      {b.percentage_used}%
                    </span>
                    <button onClick={() => openEditModal(b)} className="p-1 text-slate-400 hover:text-indigo-600">
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => handleDeleteBudget(b.id)} className="p-1 text-slate-400 hover:text-rose-600">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      b.warning_status === 'exceeded'
                        ? 'bg-rose-500'
                        : b.warning_status === 'warning'
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, b.percentage_used)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500">
                  <span>Spent: {formatRupees(b.spent)}</span>
                  <span>Limit: {formatRupees(b.amount)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-xl border border-slate-100 max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">
                {editingBudget ? 'Edit Budget' : 'Create Monthly Budget'}
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

            <form onSubmit={handleSaveBudget} className="space-y-4 mt-4">
              {!editingBudget && (
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
                  <button
                    type="button"
                    onClick={() => setIsOverall(true)}
                    className={`py-1.5 text-xs font-semibold rounded-lg transition-all ${
                      isOverall ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600'
                    }`}
                  >
                    Overall Budget
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsOverall(false)}
                    className={`py-1.5 text-xs font-semibold rounded-lg transition-all ${
                      !isOverall ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600'
                    }`}
                  >
                    Category Budget
                  </button>
                </div>
              )}

              {!isOverall && !editingBudget && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    Expense Category
                  </label>
                  <select
                    required
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                  >
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Budget Limit (in Rupees ₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 15000"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
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
                  Save Budget
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

