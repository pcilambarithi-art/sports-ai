import React, { useEffect, useState } from 'react';
import { Award, CheckCircle2, Flame, PlusCircle, Trophy } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { EmptyState } from '../components/EmptyState';

export function GamificationPage() {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressInput, setProgressInput] = useState<Record<number, string>>({});

  const [newChallenge, setNewChallenge] = useState({
    title: '',
    description: '',
    metric_type: 'calories',
    target_value: '2000',
    reward_points: '200',
    reward_title: '',
  });

  const loadData = async () => {
    try {
      const res = await apiRequest<any>('/api/gamification/overview');
      setData(res);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateChallenge = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiRequest('/api/gamification/challenges', {
        method: 'POST',
        body: JSON.stringify({
          title: newChallenge.title,
          description: newChallenge.description,
          metric_type: newChallenge.metric_type,
          target_value: Number(newChallenge.target_value),
          reward_points: Number(newChallenge.reward_points),
          reward_title: newChallenge.reward_title || null,
        }),
      });
      setNewChallenge({
        title: '',
        description: '',
        metric_type: 'calories',
        target_value: '2000',
        reward_points: '200',
        reward_title: '',
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleJoin = async (id: number) => {
    try {
      await apiRequest(`/api/gamification/challenges/${id}/join`, { method: 'POST' });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddProgress = async (id: number) => {
    const val = Number(progressInput[id] || 0);
    if (val <= 0) return;
    try {
      await apiRequest(`/api/gamification/challenges/${id}/progress`, {
        method: 'POST',
        body: JSON.stringify({ increment_value: val }),
      });
      setProgressInput({ ...progressInput, [id]: '' });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (!data) {
    return <div className="glass-card p-6 text-xs text-slate-400">Loading gamification data...</div>;
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      {/* Player Standing Banner */}
      {data.user_summary && (
        <div className="glass-card p-6 flex flex-wrap items-center justify-between gap-4 border-l-4 border-l-emerald-500">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-emerald-500">
              Your Verified Standing
            </div>
            <h2 className="text-2xl font-extrabold mt-0.5">
              Rank #{data.user_summary.rank} — {data.user_summary.total_points} XP
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {data.user_summary.badges_count} Badges Earned • {data.user_summary.sessions_logged} Sessions Logged •{' '}
              <strong>{data.user_summary.active_days_14d} active training days</strong> in the last 14 days
            </p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-amber-500/15 text-amber-500 font-bold text-sm">
            <Flame className="w-5 h-5" /> 14-Day Consistency: {data.user_summary.active_days_14d}d
          </div>
        </div>
      )}

      {/* Achievement Badges */}
      <div className="glass-card p-6 space-y-4">
        <h3 className="text-sm font-bold flex items-center gap-2">
          <Award className="w-4 h-4 text-amber-500" /> Achievement Badges
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {data.badges.map((b: any) => (
            <div
              key={b.id}
              className={`p-4 rounded-2xl border transition-all ${
                b.earned
                  ? 'bg-gradient-to-br from-emerald-500/15 to-cyan-500/10 border-emerald-500/35'
                  : 'bg-slate-50/70 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 opacity-65'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-extrabold">{b.name}</span>
                <span className="text-[11px] font-mono font-bold text-amber-500">+{b.points} XP</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">{b.description}</p>
              <div className="mt-3 text-[10px] font-bold uppercase tracking-wider">
                {b.earned ? (
                  <span className="text-emerald-500 inline-flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Unlocked
                  </span>
                ) : (
                  <span className="text-slate-400">Locked</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Challenges + Leaderboard */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <Trophy className="w-4 h-4 text-cyan-500" /> Training Challenges &amp; Rewards
          </h3>

          {data.challenges.length === 0 ? (
            <EmptyState
              title="No Active Challenges"
              description="Coaches, analysts, or admins can create team or personal challenges below."
            />
          ) : (
            <div className="space-y-3">
              {data.challenges.map((c: any) => (
                <div
                  key={c.id}
                  className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-bold">{c.title}</div>
                      <div className="text-xs text-slate-500">{c.description}</div>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-500 text-xs font-bold shrink-0">
                      +{c.reward_points} XP
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] font-mono">
                      <span>
                        {c.current_value} / {c.target_value} {c.metric_type}
                      </span>
                      <span>{c.progress_pct}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                        style={{ width: `${c.progress_pct}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {!c.joined ? (
                      <button onClick={() => handleJoin(c.id)} className="btn-primary text-xs py-1.5">
                        Join Challenge
                      </button>
                    ) : c.is_completed ? (
                      <span className="text-xs font-bold text-emerald-500">
                        ✓ Completed {c.reward_title ? `— Reward: ${c.reward_title}` : ''}
                      </span>
                    ) : (
                      <>
                        <input
                          type="number"
                          step="0.5"
                          placeholder={`Add ${c.metric_type}`}
                          className="input-field w-40 py-1.5 text-xs"
                          value={progressInput[c.id] || ''}
                          onChange={(e) => setProgressInput({ ...progressInput, [c.id]: e.target.value })}
                        />
                        <button
                          onClick={() => handleAddProgress(c.id)}
                          className="btn-secondary text-xs py-1.5"
                        >
                          Log Progress
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {user?.role !== 'athlete' && (
            <form onSubmit={handleCreateChallenge} className="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-3">
              <div className="text-xs font-bold uppercase text-slate-400 flex items-center gap-1.5">
                <PlusCircle className="w-3.5 h-3.5" /> Create New Challenge
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input
                  required
                  className="input-field"
                  placeholder="Challenge Title"
                  value={newChallenge.title}
                  onChange={(e) => setNewChallenge({ ...newChallenge, title: e.target.value })}
                />
                <select
                  className="input-field"
                  value={newChallenge.metric_type}
                  onChange={(e) => setNewChallenge({ ...newChallenge, metric_type: e.target.value })}
                >
                  <option value="calories">Calories</option>
                  <option value="sessions">Sessions</option>
                  <option value="duration_minutes">Duration (min)</option>
                  <option value="distance_km">Distance (km)</option>
                </select>
                <input
                  required
                  type="number"
                  className="input-field"
                  placeholder="Target Value"
                  value={newChallenge.target_value}
                  onChange={(e) => setNewChallenge({ ...newChallenge, target_value: e.target.value })}
                />
                <input
                  required
                  type="number"
                  className="input-field"
                  placeholder="Reward XP"
                  value={newChallenge.reward_points}
                  onChange={(e) => setNewChallenge({ ...newChallenge, reward_points: e.target.value })}
                />
              </div>
              <input
                required
                className="input-field"
                placeholder="Challenge description"
                value={newChallenge.description}
                onChange={(e) => setNewChallenge({ ...newChallenge, description: e.target.value })}
              />
              <button type="submit" className="btn-primary text-xs">
                Publish Challenge
              </button>
            </form>
          )}
        </div>

        {/* Live Leaderboard */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold">Live Team Leaderboard</h3>
          {data.leaderboard.length === 0 ? (
            <EmptyState title="No Ranked Users Yet" description="Register athletes and log sessions to populate rankings." />
          ) : (
            <div className="space-y-2">
              {data.leaderboard.map((row: any) => (
                <div
                  key={row.user_id}
                  className={`flex items-center justify-between p-3.5 rounded-xl border text-xs ${
                    row.user_id === user?.id
                      ? 'bg-cyan-500/10 border-cyan-500/35'
                      : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-slate-200 dark:bg-slate-800 flex items-center justify-center font-extrabold font-mono">
                      #{row.rank}
                    </span>
                    <div>
                      <div className="font-bold">{row.full_name}</div>
                      <div className="text-[11px] text-slate-400">
                        {row.sessions_logged} sessions • {row.badges_count} badges • {row.active_days_14d}d/14d streak
                      </div>
                    </div>
                  </div>
                  <div className="font-mono font-extrabold text-sm text-emerald-500">
                    {row.total_points} XP
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
