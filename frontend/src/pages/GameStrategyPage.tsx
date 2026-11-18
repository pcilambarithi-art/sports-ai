import React, { useEffect, useState } from 'react';
import { Info, PlusCircle, Swords, Trash2 } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';
import { EmptyState } from '../components/EmptyState';

export function GameStrategyPage() {
  const { user } = useAuth();
  const [opponents, setOpponents] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [athletes, setAthletes] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [oppForm, setOppForm] = useState({
    name: '',
    sport: 'Football',
    team_or_club: '',
    avg_speed_kmh: '',
    endurance_minutes: '',
    win_rate_pct: '',
    offensive_rating: '',
    defensive_rating: '',
    tempo_style: '',
    observed_strengths: '',
    observed_weaknesses: '',
  });

  const [stratForm, setStratForm] = useState({
    opponent_id: '',
    athlete_id: '',
    tempo_adjustment_pct: 5,
    defensive_focus_pct: 55,
  });

  const loadData = async () => {
    try {
      const [opps, pls, aths] = await Promise.all([
        apiRequest<any[]>('/api/strategy/opponents'),
        apiRequest<any[]>('/api/strategy/plans'),
        apiRequest<User[]>('/api/users?role=athlete'),
      ]);
      setOpponents(opps);
      setPlans(pls);
      setAthletes(aths);
      if (opps.length > 0 && !stratForm.opponent_id) {
        setStratForm((s) => ({ ...s, opponent_id: String(opps[0].id) }));
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddOpponent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await apiRequest<any>('/api/strategy/opponents', {
        method: 'POST',
        body: JSON.stringify({
          name: oppForm.name,
          sport: oppForm.sport,
          team_or_club: oppForm.team_or_club || null,
          avg_speed_kmh: oppForm.avg_speed_kmh ? Number(oppForm.avg_speed_kmh) : null,
          endurance_minutes: oppForm.endurance_minutes ? Number(oppForm.endurance_minutes) : null,
          win_rate_pct: oppForm.win_rate_pct ? Number(oppForm.win_rate_pct) : null,
          offensive_rating: oppForm.offensive_rating ? Number(oppForm.offensive_rating) : null,
          defensive_rating: oppForm.defensive_rating ? Number(oppForm.defensive_rating) : null,
          tempo_style: oppForm.tempo_style || null,
          observed_strengths: oppForm.observed_strengths || null,
          observed_weaknesses: oppForm.observed_weaknesses || null,
        }),
      });
      setOppForm({
        name: '',
        sport: oppForm.sport,
        team_or_club: '',
        avg_speed_kmh: '',
        endurance_minutes: '',
        win_rate_pct: '',
        offensive_rating: '',
        defensive_rating: '',
        tempo_style: '',
        observed_strengths: '',
        observed_weaknesses: '',
      });
      setStratForm((s) => ({ ...s, opponent_id: String(res.id) }));
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteOpponent = async (id: number) => {
    try {
      await apiRequest(`/api/strategy/opponents/${id}`, { method: 'DELETE' });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleGenerateStrategy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stratForm.opponent_id) return;
    setError(null);
    try {
      await apiRequest('/api/strategy/generate', {
        method: 'POST',
        body: JSON.stringify({
          opponent_id: Number(stratForm.opponent_id),
          athlete_id: stratForm.athlete_id ? Number(stratForm.athlete_id) : undefined,
          tempo_adjustment_pct: Number(stratForm.tempo_adjustment_pct),
          defensive_focus_pct: Number(stratForm.defensive_focus_pct),
        }),
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Add Opponent Form */}
        <form onSubmit={handleAddOpponent} className="glass-card p-6 space-y-4">
          <div>
            <h3 className="text-sm font-bold flex items-center gap-2">
              <PlusCircle className="w-4 h-4 text-cyan-500" /> Add Verified Opponent Profile
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Leave unknown metrics blank — the system will explicitly flag unavailable data rather than fabricating stats.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-text">Opponent Name *</label>
              <input
                required
                className="input-field"
                value={oppForm.name}
                onChange={(e) => setOppForm({ ...oppForm, name: e.target.value })}
                placeholder="e.g., Falcons United"
              />
            </div>
            <div>
              <label className="label-text">Sport *</label>
              <input
                required
                className="input-field"
                value={oppForm.sport}
                onChange={(e) => setOppForm({ ...oppForm, sport: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">Avg Speed (km/h)</label>
              <input
                type="number"
                step="0.1"
                placeholder="Optional"
                className="input-field"
                value={oppForm.avg_speed_kmh}
                onChange={(e) => setOppForm({ ...oppForm, avg_speed_kmh: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">Endurance (min)</label>
              <input
                type="number"
                placeholder="Optional"
                className="input-field"
                value={oppForm.endurance_minutes}
                onChange={(e) => setOppForm({ ...oppForm, endurance_minutes: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">Offensive Rating (0-100)</label>
              <input
                type="number"
                min={0}
                max={100}
                placeholder="Optional"
                className="input-field"
                value={oppForm.offensive_rating}
                onChange={(e) => setOppForm({ ...oppForm, offensive_rating: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">Defensive Rating (0-100)</label>
              <input
                type="number"
                min={0}
                max={100}
                placeholder="Optional"
                className="input-field"
                value={oppForm.defensive_rating}
                onChange={(e) => setOppForm({ ...oppForm, defensive_rating: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="label-text">Observed Strengths</label>
              <input
                className="input-field"
                placeholder="e.g., High press in first 20 min"
                value={oppForm.observed_strengths}
                onChange={(e) => setOppForm({ ...oppForm, observed_strengths: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">Observed Weaknesses</label>
              <input
                className="input-field"
                placeholder="e.g., Vulnerable on wide transitions"
                value={oppForm.observed_weaknesses}
                onChange={(e) => setOppForm({ ...oppForm, observed_weaknesses: e.target.value })}
              />
            </div>
          </div>
          <button type="submit" className="btn-primary">
            Save Opponent Scouting Record
          </button>
        </form>

        {/* Strategy & Scenario Generator */}
        <form onSubmit={handleGenerateStrategy} className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <Swords className="w-4 h-4 text-emerald-500" /> Tactical Counter-Strategy &amp; Scenario Simulator
          </h3>
          {opponents.length === 0 ? (
            <EmptyState
              title="No Opponents Entered Yet"
              description="Add an opponent profile on the left to generate counter-strategies and simulate tactical game scenarios."
            />
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="label-text">Target Opponent</label>
                  <select
                    className="input-field"
                    value={stratForm.opponent_id}
                    onChange={(e) => setStratForm({ ...stratForm, opponent_id: e.target.value })}
                  >
                    {opponents.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.name} ({o.sport})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label-text">Compare Against Athlete</label>
                  <select
                    className="input-field"
                    value={stratForm.athlete_id}
                    onChange={(e) => setStratForm({ ...stratForm, athlete_id: e.target.value })}
                  >
                    <option value="">Team-Wide Logged Average</option>
                    {athletes.map((a) => (
                      <option key={a.id} value={a.id}>{a.full_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-3 pt-1">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold">Tempo Shift Simulation</span>
                    <span className="font-mono text-cyan-500">{stratForm.tempo_adjustment_pct}%</span>
                  </div>
                  <input
                    type="range"
                    min={-25}
                    max={25}
                    value={stratForm.tempo_adjustment_pct}
                    onChange={(e) => setStratForm({ ...stratForm, tempo_adjustment_pct: Number(e.target.value) })}
                    className="w-full accent-cyan-500"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold">Defensive Balance Focus</span>
                    <span className="font-mono text-emerald-500">{stratForm.defensive_focus_pct}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={90}
                    value={stratForm.defensive_focus_pct}
                    onChange={(e) => setStratForm({ ...stratForm, defensive_focus_pct: Number(e.target.value) })}
                    className="w-full accent-emerald-500"
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary w-full">
                Generate Tactical Plan &amp; Run Scenarios
              </button>

              {/* Stored opponents list */}
              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
                <div className="text-[11px] font-bold uppercase text-slate-400">Stored Opponents</div>
                <div className="space-y-1.5 max-h-36 overflow-y-auto">
                  {opponents.map((o) => (
                    <div
                      key={o.id}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 text-xs"
                    >
                      <div>
                        <strong>{o.name}</strong> ({o.sport}) — Speed:{' '}
                        {o.avg_speed_kmh ?? 'N/A'} | Off/Def: {o.offensive_rating ?? 'N/A'}/
                        {o.defensive_rating ?? 'N/A'}
                      </div>
                      {user?.role !== 'athlete' && (
                        <button
                          type="button"
                          onClick={() => handleDeleteOpponent(o.id)}
                          className="text-slate-400 hover:text-rose-500 p-1 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </form>
      </div>

      {/* Generated Game Strategies */}
      {plans.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold">Generated Tactical Game Plans</h3>
          {plans.map((plan) => (
            <div key={plan.id} className="glass-card p-6 space-y-4">
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <h4 className="text-base font-extrabold">{plan.title}</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{plan.tactical_summary}</p>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  {new Date(plan.created_at).toLocaleString()}
                </span>
              </div>

              {plan.data_availability_notes?.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-xs text-amber-600 dark:text-amber-300 flex items-start gap-2">
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <strong>Data Availability Notes:</strong> {plan.data_availability_notes.join(' ')}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
                  <div className="font-bold uppercase tracking-wider text-cyan-500">
                    Recommended Counter-Strategies
                  </div>
                  {plan.counter_strategies.map((c: string, i: number) => (
                    <div key={i}>• {c}</div>
                  ))}
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-emerald-500">
                    Game Scenario Simulations
                  </div>
                  {plan.scenario_simulations.map((sc: any, i: number) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="font-bold">{sc.scenario_name}</div>
                        <div className="text-slate-500">{sc.tactical_note}</div>
                      </div>
                      <div className="text-right shrink-0 font-mono">
                        <div className="text-sm font-extrabold text-cyan-500">
                          {sc.projected_control_index}
                        </div>
                        <div className="text-[10px] text-slate-400">Fatigue: {sc.fatigue_cost}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
