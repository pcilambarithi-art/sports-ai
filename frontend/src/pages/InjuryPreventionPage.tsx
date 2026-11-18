import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';
import { EmptyState } from '../components/EmptyState';

export function InjuryPreventionPage() {
  const { user } = useAuth();
  const [assessments, setAssessments] = useState<any[]>([]);
  const [athletes, setAthletes] = useState<User[]>([]);
  const [selectedAthleteId, setSelectedAthleteId] = useState('');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [list, athList] = await Promise.all([
        apiRequest<any[]>('/api/injury/assessments'),
        apiRequest<User[]>('/api/users?role=athlete'),
      ]);
      setAssessments(list);
      setAthletes(athList);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAssess = async () => {
    setRunning(true);
    setError(null);
    try {
      await apiRequest('/api/injury/assess', {
        method: 'POST',
        body: JSON.stringify({
          athlete_id: selectedAthleteId ? Number(selectedAthleteId) : undefined,
        }),
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await apiRequest(`/api/injury/assessments/${id}/acknowledge`, { method: 'PATCH' });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Explicit Non-Medical Disclaimer */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-xs text-amber-700 dark:text-amber-300">
        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
        <div>
          <strong>Important Clinical Boundary:</strong> Injury-risk assessments use transparent sports-science
          workload heuristics (Acute:Chronic Workload Ratio, HR load spikes, RPE/fatigue z-score anomalies, sleep &amp;
          hydration recovery indicators) computed from logged sessions. They are{' '}
          <strong>not medical diagnoses</strong> and are separate from your trained calorie regression model.
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      {/* Action Controls */}
      <div className="glass-card p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-extrabold flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-500" /> Workload & Anomaly Injury-Risk Engine
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Analyzes the last 7-day acute load vs 28-day chronic workload and flags unusual performance deviations.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {user?.role !== 'athlete' && (
            <select
              className="input-field w-56"
              value={selectedAthleteId}
              onChange={(e) => setSelectedAthleteId(e.target.value)}
            >
              <option value="">Self ({user?.full_name})</option>
              {athletes.map((a) => (
                <option key={a.id} value={a.id}>{a.full_name}</option>
              ))}
            </select>
          )}
          <button onClick={handleAssess} disabled={running} className="btn-primary">
            {running ? 'Analyzing Load...' : 'Run Risk Assessment'}
          </button>
        </div>
      </div>

      {assessments.length === 0 ? (
        <div className="glass-card p-6">
          <EmptyState
            title="No Injury-Risk Assessments Yet"
            description="Log athlete workouts and click Run Risk Assessment to compute ACWR, detect load anomalies, and generate preventive protocols."
          />
        </div>
      ) : (
        <div className="space-y-4">
          {assessments.map((a) => {
            const badgeStyle =
              a.risk_level === 'High'
                ? 'bg-rose-500/15 text-rose-500 border-rose-500/30'
                : a.risk_level === 'Moderate'
                ? 'bg-amber-500/15 text-amber-500 border-amber-500/30'
                : 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30';
            return (
              <div key={a.id} className="glass-card p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className={`px-3.5 py-2 rounded-xl border font-extrabold font-mono text-lg ${badgeStyle}`}>
                      {a.risk_score}/100
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold">{a.athlete_name}</h3>
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badgeStyle}`}>
                          {a.risk_level} Risk
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono mt-0.5">
                        7d Acute: {a.acute_load_7d} AU • 28d Chronic Avg: {a.chronic_load_28d} AU • ACWR:{' '}
                        {a.acwr ?? 'N/A'}
                      </div>
                    </div>
                  </div>

                  {a.coach_alert_required && (
                    <div>
                      {a.coach_acknowledged ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-500">
                          <ShieldCheck className="w-4 h-4" /> Coach Reviewed
                        </span>
                      ) : user?.role !== 'athlete' ? (
                        <button
                          onClick={() => handleAcknowledge(a.id)}
                          className="btn-secondary text-xs border-amber-500/40 text-amber-500"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledge Coach Alert
                        </button>
                      ) : (
                        <span className="px-3 py-1 rounded-full bg-rose-500/15 text-rose-400 text-xs font-semibold">
                          Coach Review Recommended
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {a.anomalies_detected?.length > 0 && (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 space-y-1">
                    <div className="text-[11px] font-bold uppercase text-rose-400">Anomalies Detected</div>
                    {a.anomalies_detected.map((an: string, idx: number) => (
                      <div key={idx} className="text-xs text-rose-300">• {an}</div>
                    ))}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <div className="font-bold uppercase tracking-wider text-slate-400">Risk Indicators</div>
                    {a.risk_factors.map((f: string, i: number) => (
                      <div key={i}>• {f}</div>
                    ))}
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <div className="font-bold uppercase tracking-wider text-cyan-500">Training Modifications</div>
                    {a.training_modifications.map((m: string, i: number) => (
                      <div key={i}>• {m}</div>
                    ))}
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <div className="font-bold uppercase tracking-wider text-emerald-500">Preventive Exercises</div>
                    {a.preventive_exercises.map((p: string, i: number) => (
                      <div key={i}>• {p}</div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
