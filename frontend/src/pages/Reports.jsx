import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { formatRupees, formatDate } from '../services/utils';
import { BarChart3, TrendingUp, PiggyBank, ArrowDownRight } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

export default function Reports() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());

  useEffect(() => {
    fetchReport();
  }, [month, year]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/reports/monthly?month=${month}&year=${year}`);
      setReport(res.data);
    } catch (err) {
      console.error('Error fetching report:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Monthly Financial Report</h1>
          <p className="text-sm text-slate-500 mt-0.5">Detailed analytics, savings rate, and daily spending velocity</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Income</span>
          <p className="text-xl font-bold text-emerald-600 mt-2">{formatRupees(report?.total_income)}</p>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Expenses</span>
          <p className="text-xl font-bold text-rose-600 mt-2">{formatRupees(report?.total_expenses)}</p>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Net Savings</span>
          <p className="text-xl font-bold text-indigo-600 mt-2">{formatRupees(report?.net_savings)}</p>
        </div>
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Savings Rate</span>
          <p className="text-xl font-bold text-purple-600 mt-2">{report?.savings_rate_percentage}%</p>
        </div>
      </div>

      {/* Daily Spending Distribution */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
          Daily Spending Distribution
        </h2>
        {report?.daily_spending?.length === 0 ? (
          <p className="text-sm text-slate-500 py-6 text-center">No expenses recorded for this month.</p>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={report?.daily_spending}>
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickFormatter={(d) => formatDate(d)} />
                <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `₹${v/100}`} />
                <Tooltip 
                  formatter={(val) => [formatRupees(val), 'Spent']}
                  labelFormatter={(d) => formatDate(d)}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="amount" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Category Breakdown Table */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 tracking-tight mb-4">
          Category Spending Breakdown
        </h2>
        {report?.category_breakdown?.length === 0 ? (
          <p className="text-sm text-slate-500 py-4 text-center">No expense categories to display.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase">
                <tr>
                  <th className="pb-3 font-semibold">Category</th>
                  <th className="pb-3 font-semibold text-right">Percentage</th>
                  <th className="pb-3 font-semibold text-right">Total Spent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report?.category_breakdown?.map((cat) => (
                  <tr key={cat.category_id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3.5 font-medium text-slate-900">{cat.category_name}</td>
                    <td className="py-3.5 text-right font-medium text-slate-600">{cat.percentage}%</td>
                    <td className="py-3.5 text-right font-semibold text-slate-900">{formatRupees(cat.total_amount)}</td>
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

