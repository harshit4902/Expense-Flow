import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { formatRupees } from '../services/utils';
import { 
  Bot, 
  Send, 
  User, 
  Sparkles, 
  X, 
  MessageCircle, 
  CheckCircle2, 
  PiggyBank,
  Mic,
  MicOff
} from 'lucide-react';

export default function FloatingChatWidget({ onDataUpdated }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    setupSpeechRecognition();
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const setupSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSpeechSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'hi-IN'; // Recognizes Hindi, English and Hinglish in Indian accents

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  };

  const toggleListening = () => {
    if (!speechSupported) {
      alert('Speech Recognition is not supported in this browser. Please use Google Chrome, Brave, or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      try {
        recognitionRef.current?.start();
      } catch (err) {
        console.error('Failed to start speech recognition:', err);
      }
    }
  };

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      fetchChatHistory();
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, isOpen]);

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
        setMessages([{
          role: 'assistant',
          content: 'Namaste! Main aapka AI assistant hoon. Bol kar ya type karke add karein:\n• "Aaj maine 20 ka samosa khaya"\n• "5000 salary aayi"\n• "Savings mein 2000 dale"',
        }]);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const userText = input.trim();
    if (!userText || loading) return;

    if (isListening) {
      recognitionRef.current?.stop();
    }

    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/ai/chat', { message: userText });
      const data = res.data;

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply,
        transactions: data.recorded_transactions,
        savings: data.recorded_savings,
        requires_clarification: data.requires_clarification,
      }]);

      if (onDataUpdated) {
        onDataUpdated();
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Message process nahi ho saka. Kripya dobara try karein.',
        isError: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 p-3.5 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-xl hover:shadow-2xl hover:scale-105 transition-all flex items-center justify-center gap-2 group"
        title="Open AI Finance Chatbot"
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <>
            <Sparkles className="w-5 h-5 animate-pulse" />
            <span className="text-sm font-semibold pr-1 hidden sm:inline">Ask AI</span>
          </>
        )}
      </button>

      {/* Floating Chat Modal */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 max-w-[calc(100vw-3rem)] h-[540px] bg-white rounded-3xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-tight">ExpenseFlow AI</h3>
                <p className="text-[11px] text-white/80">Voice & text transaction tracker</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 text-xs">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] ${
                    isUser ? 'bg-indigo-600 text-white' : 'bg-purple-100 text-purple-700'
                  }`}>
                    {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                  </div>

                  <div className={`max-w-[85%] space-y-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
                    <div className={`p-3 rounded-2xl leading-relaxed whitespace-pre-wrap ${
                      isUser
                        ? 'bg-indigo-600 text-white rounded-tr-none shadow-sm'
                        : msg.isError
                        ? 'bg-rose-50 text-rose-700 border border-rose-200 rounded-tl-none'
                        : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none shadow-sm'
                    }`}>
                      {msg.content}
                    </div>

                    {/* Transaction Card */}
                    {msg.transactions && msg.transactions.length > 0 && (
                      <div className="space-y-1">
                        {msg.transactions.map((tx, i) => (
                          <div
                            key={i}
                            className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-[11px]"
                          >
                            <div className="flex items-center gap-1.5 truncate">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                              <span className="font-medium text-emerald-900 truncate">{tx.description}</span>
                            </div>
                            <span className="font-bold text-emerald-700 flex-shrink-0">
                              {tx.type === 'income' ? '+' : '-'}{formatRupees(tx.amount)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Savings Card */}
                    {msg.savings && (
                      <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-xl flex items-center justify-between text-[11px]">
                        <div className="flex items-center gap-1.5 truncate">
                          <PiggyBank className="w-3.5 h-3.5 text-purple-600 flex-shrink-0" />
                          <span className="font-medium text-purple-900 truncate">{msg.savings.description}</span>
                        </div>
                        <span className="font-bold text-purple-700 flex-shrink-0">
                          {formatRupees(msg.savings.amount)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <div className="p-2.5 rounded-2xl bg-white border border-slate-200 rounded-tl-none flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.4s]"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar with Mic button */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-100 flex items-center gap-1.5">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isListening ? "Listening... boliyen..." : "e.g. 20 ka samosa khaya"}
              disabled={loading}
              className={`flex-1 px-3.5 py-2 rounded-xl bg-slate-50 border text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
                isListening ? 'border-red-400 ring-2 ring-red-200 bg-red-50/20' : 'border-slate-200'
              }`}
            />

            {/* Speech to Text Microphone */}
            <button
              type="button"
              onClick={toggleListening}
              title={isListening ? "Stop listening" : "Speak via Microphone"}
              className={`p-2 rounded-xl transition-all ${
                isListening
                  ? 'bg-red-500 text-white animate-pulse shadow-md shadow-red-200'
                  : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-100'
              }`}
            >
              {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 transition-colors shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
