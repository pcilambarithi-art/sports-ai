import { useEffect, useState } from 'react';
import { Target } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';
import { EmptyState } from '../components/EmptyState';

export function SkillAssessmentPage() {
  const { user } = useAuth();
  const [assessments, setAssessments] = useState<any[]>([]);
  const [athletes, setAthletes] = useState<User[]>([]);
  const [selectedAthleteId, setSelectedAthleteId] = useState('');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [list, aths] = await Promise.all([
        apiRequest<any[]>('/api/skills/assessments'),
        apiRequest<User[]>('/api/users?role=athlete'),
      ]);
      setAssessments(list);
      setAthletes(aths);
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
      await apiRequest('/api/skills/assess', {
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

  const latest = assessments[0];
  const radarData = latest
    ? [
        { metric: 'Consistency', score: latest.consistency_score },
        { metric: 'Energy Output', score: latest.energy_output_score },
        { metric: 'Aerobic Eff.', score: latest.aerobic_efficiency_score },
        { metric: 'Workload Cap.', score: latest.workload_capacity_score },
        { metric: 'Recovery', score: latest.recovery_discipline_score },
      ]
    : [];

  const historyChart = [...assessments]
    .reverse()
    .map((a) => ({
      date: new Date(a.created_at).toLocaleDateString(),
      overall_score: a.overall_score,
    }));

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      <div className="glass-card p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-extrabold flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-500" /> Transparent Criteria-Based Skill Scoring
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Scores are computed directly from logged sessions, trained model outputs, and 70,000-row dataset peer percentiles (no fabricated pro benchmarks).
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
            {running ? 'Evaluating...' : 'Compute Skill Score'}
          </button>
        </div>
      </div>

      {!latest ? (
        <div className="glass-card p-6">
          <EmptyState
            title="No Skill Assessments Computed Yet"
            description="Log at least one training session or AI calorie prediction, then click Compute Skill Score to evaluate strengths and peer percentiles."
          />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase font-bold text-slate-400">Latest Overall Skill Index</div>
                  <div className="text-4xl font-extrabold font-mono text-cyan-500 mt-1">
                    {latest.overall_score} <span className="text-base text-slate-400">/ 100</span>
                  </div>
                </div>
                <div className="text-right text-xs font-mono space-y-1">
                  <div className="px-3 py-1 rounded-xl bg-emerald-500/15 text-emerald-500 font-bold">
                    Cohort Rank: #{latest.db_cohort_rank} / {latest.db_cohort_total}
                  </div>
                  <div className="text-slate-400">
                    Dataset Peer: {latest.dataset_peer_percentile ?? 'N/A'}%ile
                  </div>
                </div>
              </div>

              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <Radar
                      dataKey="score"
                      stroke="#06b6d4"
                      fill="#06b6d4"
                      fillOpacity={0.35}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="text-[11px] font-mono text-slate-400 p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                Formula: {latest.criteria_breakdown?.formula}
              </div>
            </div>

            <div className="glass-card p-6 space-y-5">
              <h3 className="text-sm font-bold">Historical Skill Progression</h3>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historyChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '10px',
                        fontSize: '12px',
                      }}
                    />
                    <Line type="monotone" dataKey="overall_score" name="Skill Score" stroke="#10b981" strokeWidth={2.5} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-1">
                  <div className="font-bold text-emerald-500 uppercase">Key Strengths</div>
                  {latest.strengths.map((s: string, i: number) => (
                    <div key={i}>• {s}</div>
                  ))}
                </div>
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25 space-y-1">
                  <div className="font-bold text-amber-500 uppercase">Focus Areas</div>
                  {latest.improvement_areas.map((s: string, i: number) => (
                    <div key={i}>• {s}</div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
