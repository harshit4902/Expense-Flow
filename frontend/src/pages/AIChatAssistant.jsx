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
  AlertCircle,
  Mic,
  MicOff
} from 'lucide-react';

export default function AIChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    fetchChatHistory();
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
      // 'hi-IN' allows natural speech in Hindi, English, and Hinglish in Indian accents
      recognition.lang = 'hi-IN';

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
    } else {
      setSpeechSupported(false);
    }
  };

  const toggleListening = () => {
    if (!speechSupported) {
      alert('Speech Recognition is not supported in this browser. Please try Google Chrome, Brave, or Edge.');
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
        setMessages([{
          role: 'assistant',
          content: 'Namaste! Main aapka ExpenseFlow AI Assistant hoon. Aap bol kar ya type karke transactions add kar sakte hain (English, Hindi, Hinglish).\n\nExamples:\n• "Aaj maine 20 ka samosa khaya"\n• "Received 15000 salary"\n• "Savings mein 5000 dale"',
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

    if (isListening) {
      recognitionRef.current?.stop();
    }

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
            <p className="text-xs text-slate-500">Record expenses, income & savings by voice or text</p>
          </div>
        </div>

        {speechSupported && (
          <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full">
            <Mic className="w-3.5 h-3.5 text-indigo-600" />
            Mic enabled (Hindi / Hinglish / English)
          </span>
        )}
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
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-semibold ${
                isUser 
                  ? 'bg-indigo-600 text-white' 
                  : 'bg-purple-100 text-purple-700'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

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
                            <span className="text-emerald-700 text-[11px]">{tx.category?.name || 'Category'} • {tx.type} • {tx.transaction_date}</span>
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
                        <span className="text-purple-700 text-[11px] capitalize">{msg.savings.type.replace('_', ' ')} • {msg.savings.transaction_date}</span>
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

      {/* Input Box with Mic button */}
      <form onSubmit={handleSend} className="relative flex-shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isListening ? "Listening... boliyen..." : "E.g. Aaj maine 20 ka samosa khaya... or click mic to speak"}
          disabled={loading}
          className={`w-full pl-5 pr-24 py-3.5 rounded-2xl border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm disabled:opacity-50 transition-all ${
            isListening ? 'border-red-400 ring-2 ring-red-200 bg-red-50/20' : 'border-slate-200'
          }`}
        />

        <div className="absolute right-2 top-2 flex items-center gap-1.5">
          {/* Speech-to-Text Mic Button */}
          <button
            type="button"
            onClick={toggleListening}
            title={isListening ? "Listening (Click to stop)" : "Speak via Microphone"}
            className={`p-2 rounded-xl transition-all ${
              isListening
                ? 'bg-red-500 text-white animate-pulse shadow-md shadow-red-200'
                : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-100'
            }`}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
