import { useEffect, useRef, useState } from 'react';
import { BookOpen, Bot, Mic, MicOff, PlusCircle, Send, User as UserIcon, Volume2, VolumeX } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';

const QUICK_PROMPTS = [
  'How do I improve my 5K running endurance and speed?',
  'Explain my latest performance report and skill score',
  'What is ACWR and how do I prevent overuse injuries?',
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

  const [showTrainDrawer, setShowTrainDrawer] = useState(false);
  const [kbForm, setKbForm] = useState({
    category: 'strategy',
    sport: 'General',
    question_pattern: '',
    answer: '',
    tags: '',
  });
  const [kbMsg, setKbMsg] = useState<string | null>(null);
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

  const handleAddKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    setKbMsg(null);
    try {
      const res = await apiRequest<any>('/api/assistant/knowledge', {
        method: 'POST',
        body: JSON.stringify(kbForm),
      });
      setKbMsg(
        `Added to database & retrained Semantic Coaching AI (${res.retrained_metrics.knowledge_documents} docs, ${res.retrained_metrics.vocabulary_size} bi-grams).`
      );
      setKbForm({ category: 'strategy', sport: 'General', question_pattern: '', answer: '', tags: '' });
    } catch (err: any) {
      setKbMsg(`Error: ${err.message}`);
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
    <div className="space-y-4">
      {showTrainDrawer && (
        <form onSubmit={handleAddKnowledge} className="glass-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-fuchsia-400" /> Teach &amp; Retrain Virtual Coach AI (Saved to Database)
            </h3>
            <button
              type="button"
              onClick={() => setShowTrainDrawer(false)}
              className="text-xs text-purple-300 hover:underline cursor-pointer"
            >
              Close
            </button>
          </div>
          {kbMsg && (
            <div className="p-2.5 rounded-xl bg-emerald-500/15 border border-emerald-400/30 text-emerald-300 text-xs">
              {kbMsg}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <select
              className="input-field"
              value={kbForm.category}
              onChange={(e) => setKbForm({ ...kbForm, category: e.target.value })}
            >
              <option value="endurance">Endurance</option>
              <option value="strength">Strength &amp; Power</option>
              <option value="injury_prevention">Injury Prevention</option>
              <option value="recovery">Recovery &amp; Nutrition</option>
              <option value="strategy">Game Strategy</option>
              <option value="video_biomechanics">Video &amp; Biomechanics</option>
              <option value="mental_performance">Mental Performance</option>
            </select>
            <input
              className="input-field"
              placeholder="Sport (e.g., Football, Cricket, Running)"
              value={kbForm.sport}
              onChange={(e) => setKbForm({ ...kbForm, sport: e.target.value })}
              required
            />
            <input
              className="input-field"
              placeholder="Tags (comma separated)"
              value={kbForm.tags}
              onChange={(e) => setKbForm({ ...kbForm, tags: e.target.value })}
            />
          </div>
          <input
            className="input-field"
            required
            placeholder="Coaching question or topic (e.g., How should wingers press in a 4-3-3?)"
            value={kbForm.question_pattern}
            onChange={(e) => setKbForm({ ...kbForm, question_pattern: e.target.value })}
          />
          <textarea
            className="input-field min-h-[72px]"
            required
            placeholder="Detailed coaching guidance or team playbook answer..."
            value={kbForm.answer}
            onChange={(e) => setKbForm({ ...kbForm, answer: e.target.value })}
          />
          <button type="submit" className="btn-primary text-xs">
            <PlusCircle className="w-4 h-4" /> Save to Database &amp; Retrain AI
          </button>
        </form>
      )}

      <div className="glass-card flex flex-col h-[calc(100vh-9.5rem)] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-purple-200/60 dark:border-purple-500/25 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 via-fuchsia-500 to-cyan-400 flex items-center justify-center text-white shadow-[0_0_16px_rgba(192,38,211,0.6)]">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-extrabold">ApexPulse Virtual Coaching Assistant</div>
              <div className="text-[11px] text-purple-500 dark:text-purple-300/75">
                Trained Semantic NLP AI + Authorized DB Context + Live 300-Tree Calorie Model • Voice Enabled
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setShowTrainDrawer((s) => !s)}
              className="btn-secondary py-1.5 px-3 text-xs"
            >
              <BookOpen className="w-3.5 h-3.5 text-fuchsia-400" /> Train Knowledge
            </button>
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
              className={`btn-secondary py-1.5 px-3 text-xs ${voiceOutput ? 'border-fuchsia-400 text-fuchsia-400' : ''}`}
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
              <p className="text-xs text-slate-500 dark:text-purple-200/70 max-w-md mx-auto">
                Ask any sports training, biomechanics, recovery, or tactical question, review your DB performance
                reports, or run a live calorie burn prediction directly inside chat.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {QUICK_PROMPTS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="px-3 py-2 rounded-xl bg-purple-100/70 dark:bg-[#160A2B] hover:bg-purple-500/25 border border-purple-300/60 dark:border-purple-500/35 text-xs font-medium transition-all cursor-pointer"
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
                    ? 'bg-gradient-to-br from-purple-600 to-fuchsia-600 text-white shadow-[0_0_12px_rgba(192,38,211,0.5)]'
                    : 'bg-[#190B31] border border-purple-500/40 text-cyan-300'
                }`}
              >
                {m.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              <div
                className={`max-w-2xl p-4 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
                  m.sender === 'user'
                    ? 'bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-700 text-white rounded-tr-xs shadow-[0_0_18px_-6px_rgba(192,38,211,0.7)]'
                    : 'bg-purple-50/90 dark:bg-[#120724]/90 border border-purple-200 dark:border-purple-500/30 rounded-tl-xs'
                }`}
              >
                {m.message}
                {m.sources?.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-purple-300/40 dark:border-purple-500/25 text-[10px] text-purple-500 dark:text-cyan-300/80">
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
          className="p-4 border-t border-purple-200/60 dark:border-purple-500/25 flex items-center gap-2"
        >
          <button
            type="button"
            onClick={toggleVoiceInput}
            className={`p-2.5 rounded-xl border transition-colors cursor-pointer ${
              listening
                ? 'bg-fuchsia-600 text-white border-fuchsia-400 animate-pulse'
                : 'bg-purple-100/80 dark:bg-[#170A2C] border-purple-300/60 dark:border-purple-500/35 text-purple-600 dark:text-purple-200'
            }`}
            title="Voice input"
          >
            {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
          <input
            className="input-field flex-1"
            placeholder="Ask your AI Coach anything about training, recovery, tactics, or say 'Predict calories for HIIT 30 min at 165 bpm'..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" disabled={!input.trim() || sending} className="btn-primary">
            <Send className="w-4 h-4" /> Send
          </button>
        </form>
      </div>
    </div>
  );
}
