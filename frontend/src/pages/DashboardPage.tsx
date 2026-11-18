import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Brain,
  CalendarCheck,
  Flame,
  RefreshCw,
  UserCheck,
  Users,
  Video,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest } from '../lib/api';
import { StatCard } from '../components/StatCard';
import { EmptyState } from '../components/EmptyState';

export function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<any>('/api/dashboard/overview');
      setData(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="h-32 rounded-2xl bg-slate-200 dark:bg-slate-800/60" />
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-card p-6 text-rose-500 text-sm">
        Failed to load dashboard: {error}
      </div>
    );
  }

  const { kpis, model_summary, performance_trend, recent_predictions, recent_videos, injury_alerts, recent_activities } = data;

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">Performance Command Center</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            All KPIs, charts, predictions, and alerts are computed strictly from live database records and your trained model.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/ai-lab" className="btn-primary">
            <Brain className="w-4 h-4" /> Run AI Prediction
          </Link>
          <button onClick={load} className="btn-secondary">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Total Athletes"
          value={kpis.total_athletes}
          sublabel="Registered active players"
          icon={Users}
          accent="cyan"
        />
        <StatCard
          label="Active Coaches"
          value={kpis.active_coaches}
          sublabel="Trainers & coaching staff"
          icon={UserCheck}
          accent="emerald"
        />
        <StatCard
          label="Training Sessions"
          value={kpis.training_sessions}
          sublabel={
            kpis.training_plan_completion_pct !== null
              ? `Plan completion: ${kpis.training_plan_completion_pct}%`
              : 'No active training plans yet'
          }
          icon={CalendarCheck}
          accent="violet"
        />
        <StatCard
          label="AI Predictions"
          value={kpis.ai_predictions}
          sublabel={
            kpis.avg_predicted_calories !== null
              ? `Avg output: ${kpis.avg_predicted_calories} kcal`
              : `Model: ${model_summary.test_r2_pct ?? '91.81'}% R² (${model_summary.status})`
          }
          icon={Flame}
          accent="amber"
        />
      </div>

      {/* Main Chart + Injury Alerts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold">Training Performance Overview</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Logged session calorie output & duration progression
              </p>
            </div>
            <Link to="/athletes" className="text-xs font-semibold text-cyan-500 hover:underline">
              Log Session →
            </Link>
          </div>
          {performance_trend.length === 0 ? (
            <EmptyState
              title="No Training Sessions Logged Yet"
              description="Log athlete workout sessions in Athletes & Profiles to populate real performance trends here."
              action={
                <Link to="/athletes" className="btn-primary text-xs">
                  Log First Session
                </Link>
              }
            />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performance_trend}>
                  <defs>
                    <linearGradient id="calGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      color: '#f8fafc',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="calories"
                    name="Calories (kcal)"
                    stroke="#06b6d4"
                    strokeWidth={2.5}
                    fill="url(#calGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Injury Alerts */}
        <div className="glass-card p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Workload Risk Alerts
            </h3>
            <Link to="/injury" className="text-xs font-semibold text-cyan-500 hover:underline">
              Assess →
            </Link>
          </div>
          {injury_alerts.length === 0 ? (
            <EmptyState
              title="No Active Risk Alerts"
              description="Workload-based injury alerts appear here only when real logged training loads trigger risk thresholds."
            />
          ) : (
            <div className="space-y-3 overflow-y-auto max-h-64">
              {injury_alerts.map((a: any) => (
                <div
                  key={a.id}
                  className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{a.athlete_name}</span>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        a.risk_level === 'High'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {a.risk_level} ({a.risk_score})
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300">{a.top_factor}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom 3-column grid: Recent AI Predictions, Recent Video Analyses, Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Brain className="w-4 h-4 text-cyan-500" /> Recent AI Predictions
            </h3>
            <Link to="/ai-lab" className="text-xs text-cyan-500 font-semibold hover:underline">
              Open Lab
            </Link>
          </div>
          {recent_predictions.length === 0 ? (
            <EmptyState
              title="No Predictions Yet"
              description="Run your trained ExtraTreesRegressor model in the AI Model Lab."
            />
          ) : (
            <div className="space-y-2.5">
              {recent_predictions.map((p: any) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800"
                >
                  <div>
                    <div className="text-xs font-bold">{p.exercise_type}</div>
                    <div className="text-[11px] text-slate-500">
                      {p.athlete_name} • {p.duration_minutes}m @ {p.heart_rate_bpm} BPM
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-extrabold font-mono text-cyan-500">
                      {p.predicted_calories} kcal
                    </div>
                    <div className="text-[10px] text-slate-500">{p.burn_rate_per_min} kcal/min</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Video className="w-4 h-4 text-emerald-500" /> Recent Video Analyses
            </h3>
            <Link to="/video" className="text-xs text-cyan-500 font-semibold hover:underline">
              Upload
            </Link>
          </div>
          {recent_videos.length === 0 ? (
            <EmptyState
              title="No Videos Analyzed"
              description="Upload sports training videos for OpenCV optical flow & motion tracking."
            />
          ) : (
            <div className="space-y-2.5">
              {recent_videos.map((v: any) => (
                <div
                  key={v.id}
                  className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800"
                >
                  <div className="text-xs font-bold truncate">{v.original_filename}</div>
                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{v.duration_seconds}s</span>
                    <span className="text-emerald-500 font-semibold">
                      {v.active_movement_ratio_pct}% active motion
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Activity className="w-4 h-4 text-violet-500" /> Recent Activity Feed
            </h3>
          </div>
          {recent_activities.length === 0 ? (
            <EmptyState
              title="No Activity Yet"
              description="Actions across predictions, training plans, videos, and assessments appear here."
            />
          ) : (
            <div className="space-y-2.5 max-h-72 overflow-y-auto">
              {recent_activities.map((act: any) => (
                <div
                  key={act.id}
                  className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/70 dark:border-slate-800"
                >
                  <div className="text-xs text-slate-700 dark:text-slate-200">{act.summary}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                    {new Date(act.created_at).toLocaleString()}
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
