import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Brain,
  CheckCircle2,
  Cpu,
  Download,
  FileSpreadsheet,
  Info,
  Sparkles,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest, downloadCsv } from '../lib/api';
import { useModelStatus } from '../context/ModelStatusContext';
import { useAuth } from '../context/AuthContext';
import { EXERCISE_TYPES, EXPERIENCE_LEVELS, FITNESS_GOALS } from '../types';
import type { User } from '../types';
import { EmptyState } from '../components/EmptyState';

export function AiPredictionLabPage() {
  const { user } = useAuth();
  const { modelStatus, refreshModelStatus } = useModelStatus();

  const [athletes, setAthletes] = useState<User[]>([]);
  const [selectedAthleteId, setSelectedAthleteId] = useState<string>('');
  const [form, setForm] = useState({
    Age: 28,
    Gender: 'Male',
    Weight_KG: 75,
    Exercise_Type: 'Running',
    Duration_Minutes: 45,
    Heart_Rate_BPM: 155,
    Workout_Frequency_Per_Week: 4,
    Sleep_Hours: 7.5,
    Water_Intake_Liters: 2.5,
    Fitness_Goal: 'Endurance',
    Experience_Level: 'Intermediate',
  });

  const [predicting, setPredicting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [benchmarks, setBenchmarks] = useState<any>(null);

  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState<any>(null);

  const loadData = async () => {
    try {
      const [hist, bench, usersList] = await Promise.all([
        apiRequest<any[]>('/api/ml/predictions?limit=30'),
        apiRequest<any>('/api/ml/benchmarks'),
        apiRequest<User[]>('/api/users?role=athlete'),
      ]);
      setHistory(hist);
      setBenchmarks(bench);
      setAthletes(usersList);
    } catch {
      // handled gracefully
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Pre-fill from selected athlete's profile when chosen
  const handleSelectAthlete = (idStr: string) => {
    setSelectedAthleteId(idStr);
    const ath = athletes.find((a) => String(a.id) === idStr);
    if (ath?.athlete_profile) {
      const ap = ath.athlete_profile;
      setForm((prev) => ({
        ...prev,
        Age: ap.age || prev.Age,
        Gender: ap.gender || prev.Gender,
        Weight_KG: ap.weight_kg || prev.Weight_KG,
        Exercise_Type: ap.preferred_exercise || prev.Exercise_Type,
        Workout_Frequency_Per_Week: ap.workout_frequency_per_week || prev.Workout_Frequency_Per_Week,
        Sleep_Hours: ap.avg_sleep_hours || prev.Sleep_Hours,
        Water_Intake_Liters: ap.avg_water_intake_liters || prev.Water_Intake_Liters,
        Fitness_Goal: ap.fitness_goal || prev.Fitness_Goal,
        Experience_Level: ap.experience_level || prev.Experience_Level,
      }));
    }
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setPredicting(true);
    setError(null);
    try {
      const payload = {
        ...form,
        athlete_id: selectedAthleteId ? Number(selectedAthleteId) : undefined,
        include_what_if: true,
      };
      const res = await apiRequest<any>('/api/ml/predict', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setResult(res);
      await loadData();
    } catch (err: any) {
      setError(err.message);
      refreshModelStatus();
    } finally {
      setPredicting(false);
    }
  };

  const handleBatchUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!batchFile) return;
    setBatchLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', batchFile);
      const res = await apiRequest<any>('/api/ml/predict-batch', {
        method: 'POST',
        body: fd,
      });
      setBatchResult(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBatchLoading(false);
    }
  };

  const exerciseChartData = benchmarks?.by_exercise
    ? Object.entries(benchmarks.by_exercise).map(([name, st]: [string, any]) => ({
        exercise: name,
        mean_calories: st.mean_calories,
        mean_burn_rate: st.mean_burn_rate,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Model Verification Banner */}
      <div className="glass-card p-5 border-l-4 border-l-cyan-500 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-500" />
            <h2 className="text-base font-extrabold">
              Integrated Trained Model: {modelStatus?.algorithm || 'Extra Trees Regressor'} ({modelStatus?.n_estimators || 300} Trees)
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            Source: {modelStatus?.model_path || 'D:\\V3\\trained_models\\calorie_prediction_model.pkl'} (
            {modelStatus?.model_size_gb ?? 2.93} GB)
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs font-mono">
          <span className="px-3 py-1.5 rounded-xl bg-emerald-500/15 text-emerald-500 font-bold">
            Test R²: {modelStatus?.metrics?.test_r2_pct ?? '91.81'}%
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-cyan-500/15 text-cyan-500 font-bold">
            MAE: {modelStatus?.metrics?.test_mae ?? '61.36'} kcal
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-violet-500/15 text-violet-400 font-bold">
            5-Fold CV R²: {modelStatus?.metrics?.cv_mean_r2 ?? '0.9171'}
          </span>
        </div>
      </div>

      {!modelStatus?.ready && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-xs text-amber-600 dark:text-amber-300">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div>
            <strong>Model Status: {modelStatus?.status || 'loading'}.</strong> Your 2.93 GB trained model loads
            in the background (~90s on cold start) so the API boots immediately. Predictions unlock automatically once ready.
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left: Inference Form */}
        <form onSubmit={handlePredict} className="xl:col-span-5 glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-500" /> Live Calorie Burn Prediction
            </h3>
            <span className="text-[11px] text-slate-400">11 Trained Features</span>
          </div>

          {user?.role !== 'athlete' && athletes.length > 0 && (
            <div>
              <label className="label-text">Link to Athlete (Optional)</label>
              <select
                value={selectedAthleteId}
                onChange={(e) => handleSelectAthlete(e.target.value)}
                className="input-field"
              >
                <option value="">Current User ({user?.full_name})</option>
                {athletes.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.full_name} ({a.athlete_profile?.sport || 'Athlete'})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-text">Exercise Type</label>
              <select
                className="input-field"
                value={form.Exercise_Type}
                onChange={(e) => setForm({ ...form, Exercise_Type: e.target.value })}
              >
                {EXERCISE_TYPES.map((ex) => (
                  <option key={ex} value={ex}>{ex}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label-text">Gender</label>
              <select
                className="input-field"
                value={form.Gender}
                onChange={(e) => setForm({ ...form, Gender: e.target.value })}
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>

            <div>
              <label className="label-text">Duration (min)</label>
              <input
                type="number"
                step="1"
                min="2"
                max="300"
                required
                className="input-field"
                value={form.Duration_Minutes}
                onChange={(e) => setForm({ ...form, Duration_Minutes: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Heart Rate (BPM)</label>
              <input
                type="number"
                step="1"
                min="40"
                max="230"
                required
                className="input-field"
                value={form.Heart_Rate_BPM}
                onChange={(e) => setForm({ ...form, Heart_Rate_BPM: Number(e.target.value) })}
              />
            </div>

            <div>
              <label className="label-text">Age (yrs)</label>
              <input
                type="number"
                min="10"
                max="100"
                required
                className="input-field"
                value={form.Age}
                onChange={(e) => setForm({ ...form, Age: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Weight (kg)</label>
              <input
                type="number"
                step="0.5"
                min="26"
                max="250"
                required
                className="input-field"
                value={form.Weight_KG}
                onChange={(e) => setForm({ ...form, Weight_KG: Number(e.target.value) })}
              />
            </div>

            <div>
              <label className="label-text">Frequency (days/wk)</label>
              <input
                type="number"
                min="1"
                max="7"
                required
                className="input-field"
                value={form.Workout_Frequency_Per_Week}
                onChange={(e) => setForm({ ...form, Workout_Frequency_Per_Week: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Sleep (hours)</label>
              <input
                type="number"
                step="0.1"
                min="2"
                max="16"
                required
                className="input-field"
                value={form.Sleep_Hours}
                onChange={(e) => setForm({ ...form, Sleep_Hours: Number(e.target.value) })}
              />
            </div>

            <div>
              <label className="label-text">Water Intake (L)</label>
              <input
                type="number"
                step="0.1"
                min="0.2"
                max="10"
                required
                className="input-field"
                value={form.Water_Intake_Liters}
                onChange={(e) => setForm({ ...form, Water_Intake_Liters: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Experience Level</label>
              <select
                className="input-field"
                value={form.Experience_Level}
                onChange={(e) => setForm({ ...form, Experience_Level: e.target.value })}
              >
                {EXPERIENCE_LEVELS.map((lvl) => (
                  <option key={lvl} value={lvl}>{lvl}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="label-text">Fitness Goal</label>
            <select
              className="input-field"
              value={form.Fitness_Goal}
              onChange={(e) => setForm({ ...form, Fitness_Goal: e.target.value })}
            >
              {FITNESS_GOALS.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={predicting || !modelStatus?.ready}
            className="btn-primary w-full py-3"
          >
            <Brain className="w-4 h-4" />
            {predicting ? 'Running 300-Tree Inference...' : 'Predict Calories Burned'}
          </button>
        </form>

        {/* Right: Real Prediction Output & Explainability */}
        <div className="xl:col-span-7 space-y-6">
          {result ? (
            <div className="glass-card p-6 space-y-5 border border-cyan-500/30">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-cyan-500">
                    Actual Trained Model Output
                  </span>
                  <div className="text-4xl font-extrabold font-mono mt-1">
                    {result.predicted_calories}{' '}
                    <span className="text-lg font-semibold text-slate-400">kcal</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900">
                    <div className="text-[10px] uppercase text-slate-400">Burn Rate</div>
                    <div className="text-sm font-bold font-mono text-emerald-500">
                      {result.burn_rate_per_min} /m
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900">
                    <div className="text-[10px] uppercase text-slate-400">80% Tree Band</div>
                    <div className="text-sm font-bold font-mono">
                      {result.confidence_low}–{result.confidence_high}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900">
                    <div className="text-[10px] uppercase text-slate-400">Dataset Rank</div>
                    <div className="text-sm font-bold font-mono text-cyan-500">
                      {result.dataset_percentile ?? 'N/A'}%ile
                    </div>
                  </div>
                </div>
              </div>

              {result.newly_unlocked_badges?.length > 0 && (
                <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Unlocked badge(s): <strong>{result.newly_unlocked_badges.join(', ')}</strong>
                </div>
              )}

              {/* Explanation points */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Prediction Explanation
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                  {result.explanation?.summary_points?.map((pt: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-1.5 shrink-0" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Real What-If Counterfactual Scenarios */}
              {result.explanation?.what_if_scenarios?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Live What-If Sensitivity (Re-run Through Trained Model)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {result.explanation.what_if_scenarios.map((sc: any) => (
                      <div
                        key={sc.scenario}
                        className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800 flex items-center justify-between"
                      >
                        <span className="text-xs font-medium">{sc.scenario}</span>
                        <div className="text-right font-mono">
                          <div className="text-xs font-bold">{sc.predicted_calories} kcal</div>
                          <div
                            className={`text-[10px] font-bold ${
                              sc.delta_calories >= 0 ? 'text-emerald-500' : 'text-amber-500'
                            }`}
                          >
                            {sc.delta_calories >= 0 ? '+' : ''}
                            {sc.delta_calories} kcal
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.explanation?.range_warnings?.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-500 space-y-1">
                  {result.explanation.range_warnings.map((w: string, idx: number) => (
                    <div key={idx}>⚠ {w}</div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card p-6">
              <EmptyState
                title="Ready for Real Model Inference"
                description="Enter workout and athlete biometrics on the left and click Predict Calories Burned to execute your trained 300-tree ExtraTreesRegressor pipeline."
              />
            </div>
          )}

          {/* Dataset Benchmarks & Feature Importances */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                70,000-Row Dataset Avg Calories by Exercise
              </h3>
              {exerciseChartData.length > 0 ? (
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={exerciseChartData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                      <XAxis type="number" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                      <YAxis dataKey="exercise" type="category" width={92} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          borderColor: '#334155',
                          borderRadius: '10px',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="mean_calories" name="Avg kcal" fill="#06b6d4" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-xs text-slate-400">Dataset benchmarks unavailable.</p>
              )}
            </div>

            <div className="glass-card p-5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                Model Scope & Limitations
              </h3>
              <ul className="space-y-2 text-xs text-slate-500 dark:text-slate-400">
                {(modelStatus?.limitations || []).map((lim, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Info className="w-3.5 h-3.5 text-cyan-500 mt-0.5 shrink-0" />
                    <span>{lim}</span>
                  </li>
                ))}
              </ul>
              {modelStatus?.global_feature_importances && modelStatus.global_feature_importances.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800">
                  <div className="text-[11px] font-bold uppercase text-slate-400 mb-2">
                    Top Global Feature Importances
                  </div>
                  <div className="space-y-1.5">
                    {modelStatus.global_feature_importances.slice(0, 5).map((fi) => (
                      <div key={fi.feature} className="flex items-center gap-2 text-xs">
                        <span className="w-32 truncate text-slate-500 dark:text-slate-300">{fi.label}</span>
                        <div className="flex-1 h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                            style={{ width: `${Math.min(100, fi.importance_pct * 2)}%` }}
                          />
                        </div>
                        <span className="font-mono text-[11px] w-12 text-right">{fi.importance_pct}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Batch Prediction Upload */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-emerald-500" /> Batch CSV / Excel Prediction
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Upload a CSV or Excel file with workout columns to run bulk predictions through your trained pipeline.
            </p>
          </div>
          <form onSubmit={handleBatchUpload} className="flex flex-wrap items-center gap-2">
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => setBatchFile(e.target.files?.[0] || null)}
              className="text-xs file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-200 dark:file:bg-slate-800 file:text-slate-700 dark:file:text-slate-200 cursor-pointer"
            />
            <button
              type="submit"
              disabled={!batchFile || batchLoading || !modelStatus?.ready}
              className="btn-secondary"
            >
              {batchLoading ? 'Scoring...' : 'Run Batch Inference'}
            </button>
          </form>
        </div>

        {batchResult && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-xs space-y-2">
            <div className="font-bold text-emerald-500">
              Scored {batchResult.row_count} rows — Mean: {batchResult.mean_predicted_calories} kcal (Min:{' '}
              {batchResult.min_predicted_calories} / Max: {batchResult.max_predicted_calories} kcal)
            </div>
          </div>
        )}
      </div>

      {/* Prediction History Table */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold">Stored AI Prediction History</h3>
          <button
            onClick={() => downloadCsv('/api/ml/predictions/export', 'ai_predictions_export.csv')}
            className="btn-secondary text-xs"
            disabled={history.length === 0}
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>

        {history.length === 0 ? (
          <EmptyState
            title="No Stored Predictions"
            description="Every prediction executed via your trained model is automatically persisted here."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase">
                  <th className="py-2.5 pr-4">Date</th>
                  <th className="py-2.5 pr-4">Athlete</th>
                  <th className="py-2.5 pr-4">Exercise</th>
                  <th className="py-2.5 pr-4">Duration / HR</th>
                  <th className="py-2.5 pr-4">Predicted kcal</th>
                  <th className="py-2.5 pr-4">80% Interval</th>
                  <th className="py-2.5">Percentile</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/70 dark:divide-slate-800/70">
                {history.map((p) => (
                  <tr key={p.id}>
                    <td className="py-2.5 pr-4 font-mono text-slate-400">
                      {new Date(p.created_at).toLocaleString()}
                    </td>
                    <td className="py-2.5 pr-4 font-semibold">{p.athlete_name || 'User'}</td>
                    <td className="py-2.5 pr-4">{p.inputs.Exercise_Type}</td>
                    <td className="py-2.5 pr-4 font-mono">
                      {p.inputs.Duration_Minutes}m @ {p.inputs.Heart_Rate_BPM} BPM
                    </td>
                    <td className="py-2.5 pr-4 font-mono font-bold text-cyan-500">
                      {p.predicted_calories} kcal
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-slate-400">
                      {p.confidence_low} – {p.confidence_high}
                    </td>
                    <td className="py-2.5 font-mono">{p.dataset_percentile ?? '—'}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
