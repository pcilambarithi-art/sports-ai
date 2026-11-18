import { useEffect, useRef, useState } from 'react';
import { Bot, Mic, MicOff, Send, User as UserIcon, Volume2, VolumeX } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';

const QUICK_PROMPTS = [
  'Explain my latest performance report and skill score',
  'What is on my weekly training schedule?',
  'Check my injury risk and recovery recommendations',
  'Predict calories for Running 45 minutes at 155 bpm',
];

export function VirtualCoachPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<any[]>([]);
  const [athletes, setAthletes] = useState<User[]>([]);
  const [selectedAthleteId, setSelectedAthleteId] = useState('');
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [voiceOutput, setVoiceOutput] = useState(false);
  const [listening, setListening] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const loadData = async () => {
    try {
      const [hist, aths] = await Promise.all([
        apiRequest<any[]>('/api/assistant/history'),
        apiRequest<User[]>('/api/users?role=athlete'),
      ]);
      setMessages(hist);
      setAthletes(aths);
    } catch {
      // handled gracefully
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const speakText = (text: string) => {
    if (!voiceOutput || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/\*\*/g, '').replace(/_/g, '');
    const utter = new SpeechSynthesisUtterance(clean);
    utter.rate = 1.02;
    window.speechSynthesis.speak(utter);
  };

  const sendMessage = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || sending) return;
    setSending(true);
    setInput('');
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), sender: 'user', message: trimmed, created_at: new Date().toISOString() },
    ]);
    try {
      const res = await apiRequest<any>('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: trimmed,
          athlete_id: selectedAthleteId ? Number(selectedAthleteId) : undefined,
        }),
      });
      setMessages((prev) => [
        ...prev,
        {
          id: res.id,
          sender: 'assistant',
          message: res.reply,
          sources: res.sources,
          created_at: res.created_at,
        },
      ]);
      speakText(res.reply);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          message: `Unable to reach assistant: ${err.message}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const toggleVoiceInput = () => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      alert('Voice input requires a browser supporting the Web Speech API (Chrome or Edge).');
      return;
    }
    const recognition = new SpeechRec();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    setListening(true);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setListening(false);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognition.start();
  };

  return (
    <div className="glass-card flex flex-col h-[calc(100vh-9rem)] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center text-white">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-extrabold">ApexPulse Virtual Coaching Assistant</div>
            <div className="text-[11px] text-slate-400">
              Grounded in your real database records &amp; live trained ExtraTreesRegressor model • Voice Enabled
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {user?.role !== 'athlete' && (
            <select
              className="input-field py-1.5 text-xs w-44"
              value={selectedAthleteId}
              onChange={(e) => setSelectedAthleteId(e.target.value)}
            >
              <option value="">Self ({user?.full_name})</option>
              {athletes.map((a) => (
                <option key={a.id} value={a.id}>{a.full_name}</option>
              ))}
            </select>
          )}
          <button
            type="button"
            onClick={() => setVoiceOutput((v) => !v)}
            className={`btn-secondary py-1.5 px-3 text-xs ${voiceOutput ? 'border-cyan-500 text-cyan-500' : ''}`}
            title="Toggle voice readout"
          >
            {voiceOutput ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            {voiceOutput ? 'Voice On' : 'Voice Off'}
          </button>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8 space-y-4">
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              Ask about your training plan, performance reports, injury-risk indicators, or run a live
              calorie prediction directly in chat.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {QUICK_PROMPTS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800/80 hover:bg-cyan-500/15 hover:text-cyan-500 border border-slate-200 dark:border-slate-700 text-xs font-medium transition-colors cursor-pointer"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3 ${m.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                m.sender === 'user'
                  ? 'bg-cyan-500 text-white'
                  : 'bg-slate-200 dark:bg-slate-800 text-emerald-500'
              }`}
            >
              {m.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div
              className={`max-w-2xl p-4 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
                m.sender === 'user'
                  ? 'bg-cyan-500 text-white rounded-tr-xs'
                  : 'bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-tl-xs'
              }`}
            >
              {m.message}
              {m.sources?.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-300/40 dark:border-slate-700/60 text-[10px] text-slate-400">
                  Sources: {m.sources.join(' · ')}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2"
      >
        <button
          type="button"
          onClick={toggleVoiceInput}
          className={`p-2.5 rounded-xl border transition-colors cursor-pointer ${
            listening
              ? 'bg-rose-500 text-white border-rose-500 animate-pulse'
              : 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300'
          }`}
          title="Voice input"
        >
          {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
        <input
          className="input-field flex-1"
          placeholder="Ask your AI Coach or say 'Predict calories for HIIT 30 minutes at 165 bpm'..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={!input.trim() || sending} className="btn-primary">
          <Send className="w-4 h-4" /> Send
        </button>
      </form>
    </div>
  );
}
