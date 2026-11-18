import React, { useEffect, useState } from 'react';
import { Calendar, CheckCircle2, Flame, RefreshCw, Sparkles } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { EXPERIENCE_LEVELS, FITNESS_GOALS } from '../types';
import type { User } from '../types';
import { EmptyState } from '../components/EmptyState';

export function TrainingProgramsPage() {
  const { user } = useAuth();
  const [programs, setPrograms] = useState<any[]>([]);
  const [athletes, setAthletes] = useState<User[]>([]);
  const [generating, setGenerating] = useState(false);
  const [adaptingId, setAdaptingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    athlete_id: '',
    sport: '',
    goal: 'Endurance',
    experience_level: 'Intermediate',
    weekly_sessions: 4,
  });

  const [rpeMap, setRpeMap] = useState<Record<number, number>>({});

  const loadData = async () => {
    try {
      const [progs, athList] = await Promise.all([
        apiRequest<any[]>('/api/training/programs'),
        apiRequest<User[]>('/api/users?role=athlete'),
      ]);
      setPrograms(progs);
      setAthletes(athList);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    try {
      await apiRequest('/api/training/generate', {
        method: 'POST',
        body: JSON.stringify({
          athlete_id: form.athlete_id ? Number(form.athlete_id) : undefined,
          sport: form.sport || undefined,
          goal: form.goal,
          experience_level: form.experience_level,
          weekly_sessions: Number(form.weekly_sessions),
        }),
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleSession = async (sessionId: number, currentDone: boolean) => {
    try {
      await apiRequest(`/api/training/sessions/${sessionId}/complete`, {
        method: 'PATCH',
        body: JSON.stringify({
          is_completed: !currentDone,
          feedback_rpe: rpeMap[sessionId] || 7,
        }),
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAdapt = async (programId: number) => {
    setAdaptingId(programId);
    try {
      await apiRequest(`/api/training/programs/${programId}/adapt`, { method: 'POST' });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAdaptingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      {/* Generator Card */}
      <form onSubmit={handleGenerate} className="glass-card p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-extrabold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-500" /> AI-Personalized Weekly Training Generator
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Builds a tailored 7-day schedule using logged athlete history, goals, and real session calorie targets from your trained model.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {user?.role !== 'athlete' && (
            <div>
              <label className="label-text">Athlete</label>
              <select
                className="input-field"
                value={form.athlete_id}
                onChange={(e) => setForm({ ...form, athlete_id: e.target.value })}
              >
                <option value="">Self ({user?.full_name})</option>
                {athletes.map((a) => (
                  <option key={a.id} value={a.id}>{a.full_name}</option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className="label-text">Sport Focus</label>
            <input
              className="input-field"
              placeholder="e.g., Football, Track"
              value={form.sport}
              onChange={(e) => setForm({ ...form, sport: e.target.value })}
            />
          </div>
          <div>
            <label className="label-text">Training Goal</label>
            <select
              className="input-field"
              value={form.goal}
              onChange={(e) => setForm({ ...form, goal: e.target.value })}
            >
              {FITNESS_GOALS.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label-text">Level</label>
            <select
              className="input-field"
              value={form.experience_level}
              onChange={(e) => setForm({ ...form, experience_level: e.target.value })}
            >
              {EXPERIENCE_LEVELS.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label-text">Active Days / Wk</label>
            <input
              type="number"
              min={2}
              max={7}
              className="input-field"
              value={form.weekly_sessions}
              onChange={(e) => setForm({ ...form, weekly_sessions: Number(e.target.value) })}
            />
          </div>
        </div>

        <button type="submit" disabled={generating} className="btn-primary">
          <Calendar className="w-4 h-4" />
          {generating ? 'Generating Weekly Schedule...' : 'Generate Personalized Program'}
        </button>
      </form>

      {/* Programs List */}
      {programs.length === 0 ? (
        <div className="glass-card p-6">
          <EmptyState
            title="No Training Programs Created Yet"
            description="Generate a personalized daily and weekly training plan above to track progress and adapt workouts based on RPE feedback."
          />
        </div>
      ) : (
        <div className="space-y-6">
          {programs.map((prog) => (
            <div key={prog.id} className="glass-card p-6 space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-extrabold">{prog.title}</h3>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/15 text-cyan-500">
                      {prog.completion_pct}% Complete
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Athlete: <strong>{prog.athlete_name}</strong> • Goal: {prog.goal} •{' '}
                    {prog.weekly_target_calories
                      ? `Estimated Weekly Burn (Trained ML): ${prog.weekly_target_calories} kcal`
                      : 'Calorie targets populate when trained ML model is loaded'}
                  </p>
                  {prog.adaptation_notes && (
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1.5">
                      Adaptive Engine: {prog.adaptation_notes}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => handleAdapt(prog.id)}
                  disabled={adaptingId === prog.id}
                  className="btn-secondary text-xs"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${adaptingId === prog.id ? 'animate-spin' : ''}`} />
                  Adapt Plan from Feedback
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
                {prog.sessions.map((s: any) => (
                  <div
                    key={s.id}
                    className={`p-4 rounded-2xl border transition-all flex flex-col justify-between gap-3 ${
                      s.is_completed
                        ? 'bg-emerald-500/10 border-emerald-500/35'
                        : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-extrabold uppercase tracking-wider text-cyan-500">
                          {s.day_of_week}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            s.intensity === 'High'
                              ? 'bg-rose-500/15 text-rose-400'
                              : s.intensity === 'Recovery'
                              ? 'bg-slate-500/15 text-slate-400'
                              : 'bg-amber-500/15 text-amber-400'
                          }`}
                        >
                          {s.intensity}
                        </span>
                      </div>
                      <div className="text-sm font-bold">{s.exercise_type}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">{s.focus_area}</div>
                      <div className="flex flex-wrap gap-2 pt-1 text-[11px] font-mono text-slate-600 dark:text-slate-300">
                        <span>{s.target_duration_minutes}m</span>
                        <span>•</span>
                        <span>{s.target_heart_rate_bpm} BPM</span>
                        {s.expected_calories && (
                          <>
                            <span>•</span>
                            <span className="text-emerald-500 font-bold flex items-center gap-0.5">
                              <Flame className="w-3 h-3" /> {s.expected_calories}
                            </span>
                          </>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 pt-1">{s.instructions}</p>
                    </div>

                    <div className="pt-2 border-t border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 text-[11px]">
                        <span className="text-slate-400">RPE:</span>
                        <input
                          type="number"
                          min={1}
                          max={10}
                          className="w-12 px-1.5 py-1 rounded-lg bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 text-xs font-mono"
                          value={rpeMap[s.id] ?? s.feedback_rpe ?? 7}
                          onChange={(e) => setRpeMap({ ...rpeMap, [s.id]: Number(e.target.value) })}
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleToggleSession(s.id, s.is_completed)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                          s.is_completed
                            ? 'bg-emerald-500 text-white'
                            : 'bg-slate-200 dark:bg-slate-800 hover:bg-cyan-500 hover:text-white'
                        }`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        {s.is_completed ? 'Done' : 'Complete'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
