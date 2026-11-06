import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { formatRupees } from '../services/utils';
import { 
  Bot, 
  Send, 
  User, 
  Sparkles, 
  ArrowDownLeft, 
  ArrowUpRight, 
  PiggyBank, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function AIChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchChatHistory = async () => {
    try {
      const res = await api.get('/ai/history');
      if (res.data && res.data.length > 0) {
        setMessages(res.data.map(m => ({
          role: m.role,
          content: m.message,
          created_at: m.created_at,
        })));
      } else {
        // Welcome message
        setMessages([{
          role: 'assistant',
          content: 'Namaste! Main aapka ExpenseFlow AI Assistant hoon. Aap mujhse kisi bhi bhasha mein baat kar sakte hain (English, Hindi, Hinglish).\n\nExamples:\n• "Aaj maine 20 ka samosa khaya"\n• "Received 15000 salary"\n• "Savings mein 5000 dale"',
        }]);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const userText = input.trim();
    if (!userText || loading) return;

    // Append user message immediately
    const newMsg = { role: 'user', content: userText };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/ai/chat', { message: userText });
      const data = res.data;

      const botReply = {
        role: 'assistant',
        content: data.reply,
        transactions: data.recorded_transactions,
        savings: data.recorded_savings,
        requires_clarification: data.requires_clarification,
      };

      setMessages(prev => [...prev, botReply]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Maaf kijiye, message process karne mein dikkat aayi. Kripya dobara try karein.',
        isError: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto h-[calc(100vh-6rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-100">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Financial Assistant</h1>
            <p className="text-xs text-slate-500">Record expenses, income & savings in English, Hindi, or Hinglish</p>
          </div>
        </div>
      </div>

      {/* Chat Messages Box */}
      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 overflow-y-auto space-y-4">
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={idx}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-semibold ${
                isUser 
                  ? 'bg-indigo-600 text-white' 
                  : 'bg-purple-100 text-purple-700'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble & Cards */}
              <div className={`max-w-[80%] space-y-2.5 ${isUser ? 'items-end' : 'items-start'}`}>
                <div className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-tr-none shadow-sm'
                    : msg.isError
                    ? 'bg-rose-50 text-rose-700 border border-rose-200 rounded-tl-none'
                    : 'bg-slate-100 text-slate-800 rounded-tl-none'
                }`}>
                  {msg.content}
                </div>

                {/* Transaction Recorded Cards */}
                {msg.transactions && msg.transactions.length > 0 && (
                  <div className="space-y-2">
                    {msg.transactions.map((tx, i) => (
                      <div
                        key={i}
                        className="p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-xl flex items-center justify-between text-xs gap-3"
                      >
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                          <div>
                            <span className="font-semibold text-emerald-900 block">{tx.description}</span>
                            <span className="text-emerald-700 text-[11px]">{tx.category?.name || 'Category'} • {tx.type}</span>
                          </div>
                        </div>
                        <span className="font-bold text-sm text-emerald-700">
                          {tx.type === 'income' ? '+' : '-'}{formatRupees(tx.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Savings Recorded Card */}
                {msg.savings && (
                  <div className="p-3.5 bg-purple-50/80 border border-purple-200 rounded-xl flex items-center justify-between text-xs gap-3">
                    <div className="flex items-center gap-2">
                      <PiggyBank className="w-4 h-4 text-purple-600 flex-shrink-0" />
                      <div>
                        <span className="font-semibold text-purple-900 block">{msg.savings.description}</span>
                        <span className="text-purple-700 text-[11px] capitalize">{msg.savings.type.replace('_', ' ')}</span>
                      </div>
                    </div>
                    <span className="font-bold text-sm text-purple-700">
                      {formatRupees(msg.savings.amount)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-100 text-slate-500 rounded-tl-none flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="relative flex-shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="E.g. Aaj maine 20 ka samosa khaya... or Received 5000 freelance"
          disabled={loading}
          className="w-full pl-5 pr-14 py-3.5 rounded-2xl border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="absolute right-2.5 top-2 p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
