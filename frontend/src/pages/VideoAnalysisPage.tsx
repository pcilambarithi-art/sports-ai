import React, { useEffect, useState } from 'react';
import { Flame, Info, Upload, Video } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest } from '../lib/api';
import { useModelStatus } from '../context/ModelStatusContext';
import { EXERCISE_TYPES } from '../types';
import { EmptyState } from '../components/EmptyState';

export function VideoAnalysisPage() {
  const { modelStatus } = useModelStatus();
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [file, setFile] = useState<File | null>(null);
  const [sport, setSport] = useState('Athletics');
  const [exerciseType, setExerciseType] = useState('Running');
  const [heartRate, setHeartRate] = useState('150');
  const [sessionMin, setSessionMin] = useState('30');
  const [linkMlModel, setLinkMlModel] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalyses = async () => {
    try {
      const list = await apiRequest<any[]>('/api/video/analyses');
      setAnalyses(list);
      if (list.length > 0 && !selected) {
        setSelected(list[0]);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadAnalyses();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('sport', sport);
      fd.append('exercise_type', exerciseType);
      fd.append('run_calorie_model', String(linkMlModel));
      if (linkMlModel) {
        fd.append('heart_rate_bpm', heartRate);
        fd.append('session_duration_minutes', sessionMin);
      }
      const res = await apiRequest<any>('/api/video/analyze', {
        method: 'POST',
        body: fd,
      });
      setSelected(res);
      setFile(null);
      await loadAnalyses();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="glass-card p-6 space-y-4">
        <div>
          <h2 className="text-base font-extrabold flex items-center gap-2">
            <Video className="w-5 h-5 text-cyan-500" /> OpenCV Sports Video Breakdown &amp; Movement Tracking
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Upload `.mp4`, `.avi`, `.mov`, `.mkv`, or `.webm` footage for real OpenCV Farneback optical flow,
            foreground contour tracking, centroid movement trajectories, and annotated peak-moment keyframes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="label-text">Video File (Max 150 MB)</label>
            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.webm"
              required
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="input-field py-2 text-xs"
            />
          </div>
          <div>
            <label className="label-text">Sport</label>
            <input
              className="input-field"
              value={sport}
              onChange={(e) => setSport(e.target.value)}
            />
          </div>
          <div>
            <label className="label-text">Exercise Category</label>
            <select
              className="input-field"
              value={exerciseType}
              onChange={(e) => setExerciseType(e.target.value)}
            >
              {EXERCISE_TYPES.map((ex) => (
                <option key={ex} value={ex}>{ex}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3">
          <label className="flex items-center gap-2 text-xs font-medium">
            <input
              type="checkbox"
              checked={linkMlModel}
              onChange={(e) => setLinkMlModel(e.target.checked)}
              disabled={!modelStatus?.ready}
            />
            Also invoke trained ExtraTreesRegressor calorie model for this session (requires HR &amp; session duration)
          </label>
          {linkMlModel && (
            <div className="grid grid-cols-2 gap-3 max-w-md">
              <div>
                <label className="label-text">Avg Heart Rate (BPM)</label>
                <input
                  type="number"
                  className="input-field"
                  value={heartRate}
                  onChange={(e) => setHeartRate(e.target.value)}
                />
              </div>
              <div>
                <label className="label-text">Full Session Duration (min)</label>
                <input
                  type="number"
                  className="input-field"
                  value={sessionMin}
                  onChange={(e) => setSessionMin(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        <button type="submit" disabled={!file || uploading} className="btn-primary">
          <Upload className="w-4 h-4" />
          {uploading ? 'Processing Video via OpenCV...' : 'Upload & Analyze Video'}
        </button>
      </form>

      {/* Analysis Display */}
      {!selected ? (
        <div className="glass-card p-6">
          <EmptyState
            title="No Video Analyses Yet"
            description="Upload a training or match clip above to extract real optical flow profiles, tracking trails, and annotated keyframes."
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* History sidebar */}
          <div className="xl:col-span-3 glass-card p-4 space-y-2 max-h-[650px] overflow-y-auto">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
              Analyzed Clips ({analyses.length})
            </div>
            {analyses.map((a) => (
              <button
                key={a.id}
                onClick={() => setSelected(a)}
                className={`w-full text-left p-3 rounded-xl border text-xs transition-all cursor-pointer ${
                  selected.id === a.id
                    ? 'bg-cyan-500/15 border-cyan-500/40'
                    : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800'
                }`}
              >
                <div className="font-bold truncate">{a.original_filename}</div>
                <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
                  {a.duration_seconds}s • {a.resolution} • {a.active_movement_ratio_pct}% active
                </div>
              </button>
            ))}
          </div>

          {/* Detail View */}
          <div className="xl:col-span-9 space-y-6">
            <div className="glass-card p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-base font-extrabold">{selected.original_filename}</h3>
                  <p className="text-xs text-slate-400 font-mono">
                    {selected.resolution} @ {selected.fps} FPS • {selected.frame_count} frames •{' '}
                    {selected.duration_seconds}s
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-mono">
                  <span className="px-3 py-1 rounded-xl bg-cyan-500/15 text-cyan-500 font-bold">
                    Mean Motion: {selected.mean_motion_intensity}
                  </span>
                  <span className="px-3 py-1 rounded-xl bg-emerald-500/15 text-emerald-500 font-bold">
                    Peak: {selected.peak_motion_intensity}
                  </span>
                  <span className="px-3 py-1 rounded-xl bg-violet-500/15 text-violet-400 font-bold">
                    Active: {selected.active_movement_ratio_pct}%
                  </span>
                </div>
              </div>

              {selected.linked_prediction && (
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2 text-xs text-emerald-500">
                  <Flame className="w-4 h-4 shrink-0" />
                  <span>
                    Linked Trained Calorie Model Estimate:{' '}
                    <strong>{selected.linked_prediction.predicted_calories} kcal</strong> (
                    {selected.linked_prediction.burn_rate_per_min} kcal/min for{' '}
                    {selected.linked_prediction.exercise_type})
                  </span>
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs font-bold mb-2">OpenCV Motion Intensity Timeline</div>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={selected.motion_timeline}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                        <XAxis dataKey="timestamp_sec" tick={{ fontSize: 10 }} stroke="#94a3b8" unit="s" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0f172a',
                            borderColor: '#334155',
                            borderRadius: '10px',
                            fontSize: '12px',
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="motion_intensity"
                          name="Motion Energy"
                          stroke="#06b6d4"
                          fill="#06b6d4"
                          fillOpacity={0.25}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs font-bold mb-2">Tracked Subject Centroid Spatial Map</div>
                  {selected.trajectory_points?.length > 0 ? (
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                          <XAxis type="number" dataKey="x_norm" domain={[0, 1]} name="X" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                          <YAxis type="number" dataKey="y_norm" domain={[0, 1]} reversed name="Y" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                          <Scatter data={selected.trajectory_points} fill="#10b981" />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 py-12 text-center">
                      No distinct moving foreground trajectory isolated in clip.
                    </p>
                  )}
                </div>
              </div>

              {/* Annotated Keyframes */}
              {selected.key_moments?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                    Annotated Peak-Activity Key Moments (OpenCV Bounding Box &amp; Trail)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {selected.key_moments.map((km: any) => (
                      <div
                        key={km.rank}
                        className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950"
                      >
                        <img
                          src={km.image_url}
                          alt={`Keyframe at ${km.timestamp_sec}s`}
                          className="w-full h-36 object-cover"
                        />
                        <div className="p-2.5 text-[11px] text-slate-200 flex justify-between">
                          <span className="font-bold text-cyan-400">{km.label}</span>
                          <span className="font-mono">{km.timestamp_sec}s</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback & Disclosure */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Movement Feedback
                </h4>
                <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                  {selected.feedback_items?.map((fb: string, i: number) => (
                    <li key={i}>• {fb}</li>
                  ))}
                </ul>
              </div>

              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800 text-[11px] text-slate-500 flex items-start gap-2">
                <Info className="w-4 h-4 text-cyan-500 shrink-0 mt-0.5" />
                <span>{selected.analysis_disclaimer}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
