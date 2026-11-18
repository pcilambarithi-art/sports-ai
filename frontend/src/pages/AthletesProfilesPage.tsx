import React, { useEffect, useState } from 'react';
import {
  Activity,
  Download,
  PlusCircle,
  Save,
  Shield,
  TrendingUp,
  UserPlus,
  Users,
} from 'lucide-react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest, downloadCsv } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { EXERCISE_TYPES, EXPERIENCE_LEVELS, FITNESS_GOALS } from '../types';
import type { User, UserRole } from '../types';
import { EmptyState } from '../components/EmptyState';

export function AthletesProfilesPage() {
  const { user, refreshUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [records, setRecords] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [selectedAthleteId, setSelectedAthleteId] = useState<string>('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // My Profile state
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    bio: user?.bio || '',
    sport: user?.athlete_profile?.sport || user?.coach_profile?.specialization || '',
    age: user?.athlete_profile?.age ?? '',
    gender: user?.athlete_profile?.gender || 'Male',
    weight_kg: user?.athlete_profile?.weight_kg ?? '',
    height_cm: user?.athlete_profile?.height_cm ?? '',
    experience_level: user?.athlete_profile?.experience_level || 'Intermediate',
    fitness_goal: user?.athlete_profile?.fitness_goal || 'Endurance',
    preferred_exercise: user?.athlete_profile?.preferred_exercise || 'Running',
    workout_frequency_per_week: user?.athlete_profile?.workout_frequency_per_week ?? 4,
    avg_sleep_hours: user?.athlete_profile?.avg_sleep_hours ?? 7.5,
    avg_water_intake_liters: user?.athlete_profile?.avg_water_intake_liters ?? 2.5,
    team_name: user?.coach_profile?.team_name || '',
    years_experience: user?.coach_profile?.years_experience ?? '',
  });

  // Log performance session form
  const [perfForm, setPerfForm] = useState({
    exercise_type: 'Running',
    duration_minutes: 45,
    heart_rate_bpm: 152,
    speed_kmh: '',
    distance_km: '',
    calories_burned: '',
    rpe_score: 7,
    fatigue_level: 5,
    sleep_hours: 7.5,
    water_intake_liters: 2.5,
    notes: '',
    auto_predict_calories: true,
  });

  // Coach-athlete assignment form
  const [assignCoachId, setAssignCoachId] = useState('');
  const [assignAthleteId, setAssignAthleteId] = useState('');

  const loadAll = async (targetAth?: string) => {
    try {
      const athParam = targetAth ? `?athlete_id=${targetAth}` : '';
      const [uList, asgList, recList, fcData] = await Promise.all([
        apiRequest<User[]>('/api/users'),
        apiRequest<any[]>('/api/users/assignments'),
        apiRequest<any[]>(`/api/performance${athParam}`),
        apiRequest<any>(`/api/performance/forecast${athParam}`),
      ]);
      setUsers(uList);
      setAssignments(asgList);
      setRecords(recList);
      setForecast(fcData);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadAll(selectedAthleteId);
  }, [selectedAthleteId]);

  useEffect(() => {
    if (!user) return;
    setProfileForm({
      full_name: user.full_name || '',
      bio: user.bio || '',
      sport: user.athlete_profile?.sport || user.coach_profile?.specialization || '',
      age: user.athlete_profile?.age ?? '',
      gender: user.athlete_profile?.gender || 'Male',
      weight_kg: user.athlete_profile?.weight_kg ?? '',
      height_cm: user.athlete_profile?.height_cm ?? '',
      experience_level: user.athlete_profile?.experience_level || 'Intermediate',
      fitness_goal: user.athlete_profile?.fitness_goal || 'Endurance',
      preferred_exercise: user.athlete_profile?.preferred_exercise || 'Running',
      workout_frequency_per_week: user.athlete_profile?.workout_frequency_per_week ?? 4,
      avg_sleep_hours: user.athlete_profile?.avg_sleep_hours ?? 7.5,
      avg_water_intake_liters: user.athlete_profile?.avg_water_intake_liters ?? 2.5,
      team_name: user.coach_profile?.team_name || '',
      years_experience: user.coach_profile?.years_experience ?? '',
    });
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatusMsg(null);
    try {
      const payload: any = {
        full_name: profileForm.full_name,
        bio: profileForm.bio,
      };
      if (user?.role === 'athlete') {
        payload.athlete_profile = {
          sport: profileForm.sport || null,
          age: profileForm.age ? Number(profileForm.age) : null,
          gender: profileForm.gender,
          weight_kg: profileForm.weight_kg ? Number(profileForm.weight_kg) : null,
          height_cm: profileForm.height_cm ? Number(profileForm.height_cm) : null,
          experience_level: profileForm.experience_level,
          fitness_goal: profileForm.fitness_goal,
          preferred_exercise: profileForm.preferred_exercise,
          workout_frequency_per_week: Number(profileForm.workout_frequency_per_week),
          avg_sleep_hours: Number(profileForm.avg_sleep_hours),
          avg_water_intake_liters: Number(profileForm.avg_water_intake_liters),
        };
      } else if (user?.role === 'coach') {
        payload.coach_profile = {
          specialization: profileForm.sport || null,
          team_name: profileForm.team_name || null,
          years_experience: profileForm.years_experience ? Number(profileForm.years_experience) : null,
        };
      }
      await apiRequest('/api/users/me', { method: 'PUT', body: JSON.stringify(payload) });
      await refreshUser();
      await loadAll(selectedAthleteId);
      setStatusMsg('Profile updated successfully.');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleLogPerformance = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatusMsg(null);
    try {
      await apiRequest('/api/performance', {
        method: 'POST',
        body: JSON.stringify({
          athlete_id: selectedAthleteId ? Number(selectedAthleteId) : undefined,
          exercise_type: perfForm.exercise_type,
          duration_minutes: Number(perfForm.duration_minutes),
          heart_rate_bpm: Number(perfForm.heart_rate_bpm),
          speed_kmh: perfForm.speed_kmh ? Number(perfForm.speed_kmh) : null,
          distance_km: perfForm.distance_km ? Number(perfForm.distance_km) : null,
          calories_burned: perfForm.calories_burned ? Number(perfForm.calories_burned) : null,
          rpe_score: Number(perfForm.rpe_score),
          fatigue_level: Number(perfForm.fatigue_level),
          sleep_hours: Number(perfForm.sleep_hours),
          water_intake_liters: Number(perfForm.water_intake_liters),
          notes: perfForm.notes || null,
          auto_predict_calories: perfForm.auto_predict_calories,
        }),
      });
      setStatusMsg('Training performance session logged.');
      setPerfForm((p) => ({ ...p, notes: '' }));
      await loadAll(selectedAthleteId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignCoachId || !assignAthleteId) return;
    try {
      await apiRequest('/api/users/assignments', {
        method: 'POST',
        body: JSON.stringify({
          coach_id: Number(assignCoachId),
          athlete_id: Number(assignAthleteId),
        }),
      });
      setStatusMsg('Coach-Athlete assignment saved.');
      await loadAll(selectedAthleteId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAdminRoleChange = async (userId: number, role: UserRole) => {
    try {
      await apiRequest(`/api/users/${userId}/admin`, {
        method: 'PATCH',
        body: JSON.stringify({ role }),
      });
      setStatusMsg('User role updated.');
      await loadAll(selectedAthleteId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const athletes = users.filter((u) => u.role === 'athlete');
  const coaches = users.filter((u) => u.role === 'coach');

  return (
    <div className="space-y-6">
      {statusMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-500 text-xs font-semibold">
          {statusMsg}
        </div>
      )}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs font-semibold">
          {error}
        </div>
      )}

      {/* Athlete Filter Bar for Staff */}
      {user?.role !== 'athlete' && (
        <div className="glass-card p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-bold">
            <Users className="w-4 h-4 text-cyan-500" />
            Active Athlete Scope
          </div>
          <select
            className="input-field max-w-xs"
            value={selectedAthleteId}
            onChange={(e) => setSelectedAthleteId(e.target.value)}
          >
            <option value="">All Accessible Athletes / Self</option>
            {athletes.map((a) => (
              <option key={a.id} value={a.id}>
                {a.full_name} ({a.athlete_profile?.sport || 'Athlete'})
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Edit My Profile */}
        <form onSubmit={handleSaveProfile} className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <Save className="w-4 h-4 text-cyan-500" /> My Profile ({user?.role})
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-text">Full Name</label>
              <input
                className="input-field"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">{user?.role === 'coach' ? 'Specialization' : 'Sport'}</label>
              <input
                className="input-field"
                value={profileForm.sport}
                onChange={(e) => setProfileForm({ ...profileForm, sport: e.target.value })}
                placeholder="e.g., Athletics, Football"
              />
            </div>
          </div>
          <div>
            <label className="label-text">Bio</label>
            <input
              className="input-field"
              value={profileForm.bio}
              onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
              placeholder="Training background, goals, or coaching philosophy"
            />
          </div>

          {user?.role === 'athlete' && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div>
                <label className="label-text">Age</label>
                <input
                  type="number"
                  className="input-field"
                  value={profileForm.age}
                  onChange={(e) => setProfileForm({ ...profileForm, age: e.target.value })}
                />
              </div>
              <div>
                <label className="label-text">Gender</label>
                <select
                  className="input-field"
                  value={profileForm.gender}
                  onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value as any })}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
              <div>
                <label className="label-text">Weight (kg)</label>
                <input
                  type="number"
                  step="0.5"
                  className="input-field"
                  value={profileForm.weight_kg}
                  onChange={(e) => setProfileForm({ ...profileForm, weight_kg: e.target.value })}
                />
              </div>
              <div>
                <label className="label-text">Experience</label>
                <select
                  className="input-field"
                  value={profileForm.experience_level}
                  onChange={(e) => setProfileForm({ ...profileForm, experience_level: e.target.value as any })}
                >
                  {EXPERIENCE_LEVELS.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label-text">Fitness Goal</label>
                <select
                  className="input-field"
                  value={profileForm.fitness_goal}
                  onChange={(e) => setProfileForm({ ...profileForm, fitness_goal: e.target.value })}
                >
                  {FITNESS_GOALS.map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label-text">Freq (days/wk)</label>
                <input
                  type="number"
                  min={1}
                  max={7}
                  className="input-field"
                  value={profileForm.workout_frequency_per_week}
                  onChange={(e) =>
                    setProfileForm({ ...profileForm, workout_frequency_per_week: Number(e.target.value) })
                  }
                />
              </div>
            </div>
          )}

          {user?.role === 'coach' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-text">Team / Club</label>
                <input
                  className="input-field"
                  value={profileForm.team_name}
                  onChange={(e) => setProfileForm({ ...profileForm, team_name: e.target.value })}
                />
              </div>
              <div>
                <label className="label-text">Years Experience</label>
                <input
                  type="number"
                  className="input-field"
                  value={profileForm.years_experience}
                  onChange={(e) => setProfileForm({ ...profileForm, years_experience: e.target.value })}
                />
              </div>
            </div>
          )}

          <button type="submit" className="btn-primary">
            <Save className="w-4 h-4" /> Save Profile Changes
          </button>
        </form>

        {/* Log Real Performance Session */}
        <form onSubmit={handleLogPerformance} className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-emerald-500" /> Log Training Performance Session
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div>
              <label className="label-text">Exercise Type</label>
              <select
                className="input-field"
                value={perfForm.exercise_type}
                onChange={(e) => setPerfForm({ ...perfForm, exercise_type: e.target.value })}
              >
                {EXERCISE_TYPES.map((ex) => (
                  <option key={ex} value={ex}>{ex}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label-text">Duration (min)</label>
              <input
                type="number"
                required
                className="input-field"
                value={perfForm.duration_minutes}
                onChange={(e) => setPerfForm({ ...perfForm, duration_minutes: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Avg HR (BPM)</label>
              <input
                type="number"
                required
                className="input-field"
                value={perfForm.heart_rate_bpm}
                onChange={(e) => setPerfForm({ ...perfForm, heart_rate_bpm: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Speed (km/h)</label>
              <input
                type="number"
                step="0.1"
                placeholder="Optional"
                className="input-field"
                value={perfForm.speed_kmh}
                onChange={(e) => setPerfForm({ ...perfForm, speed_kmh: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">Distance (km)</label>
              <input
                type="number"
                step="0.1"
                placeholder="Optional"
                className="input-field"
                value={perfForm.distance_km}
                onChange={(e) => setPerfForm({ ...perfForm, distance_km: e.target.value })}
              />
            </div>
            <div>
              <label className="label-text">RPE (1-10)</label>
              <input
                type="number"
                min={1}
                max={10}
                className="input-field"
                value={perfForm.rpe_score}
                onChange={(e) => setPerfForm({ ...perfForm, rpe_score: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Fatigue (1-10)</label>
              <input
                type="number"
                min={1}
                max={10}
                className="input-field"
                value={perfForm.fatigue_level}
                onChange={(e) => setPerfForm({ ...perfForm, fatigue_level: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Sleep (hrs)</label>
              <input
                type="number"
                step="0.1"
                className="input-field"
                value={perfForm.sleep_hours}
                onChange={(e) => setPerfForm({ ...perfForm, sleep_hours: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label-text">Water (L)</label>
              <input
                type="number"
                step="0.1"
                className="input-field"
                value={perfForm.water_intake_liters}
                onChange={(e) => setPerfForm({ ...perfForm, water_intake_liters: Number(e.target.value) })}
              />
            </div>
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={perfForm.auto_predict_calories}
              onChange={(e) => setPerfForm({ ...perfForm, auto_predict_calories: e.target.checked })}
            />
            Auto-estimate calories burned using trained ExtraTreesRegressor model (when ready)
          </label>
          <button type="submit" className="btn-primary">
            <Activity className="w-4 h-4" /> Log Performance Record
          </button>
        </form>
      </div>

      {/* Predictive Analytics Trend & Peak Competition Window */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-500" /> Predictive Analytics & Peak Performance Window
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Linear progression forecast computed strictly from chronological logged training sessions.
            </p>
          </div>
          {forecast?.peak_window && (
            <span className="px-3 py-1.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-xs font-semibold text-emerald-500">
              Peak Window: {forecast.peak_window.recommended_start} → {forecast.peak_window.recommended_end}
            </span>
          )}
        </div>
        {forecast?.available ? (
          <>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecast.forecast_points}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
                  <XAxis dataKey="step" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '10px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="actual" name="Actual Output (kcal/min)" stroke="#06b6d4" strokeWidth={2.5} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="projected" name="Trend Forecast" stroke="#10b981" strokeDasharray="5 5" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">{forecast.peak_window?.rationale}</p>
          </>
        ) : (
          <EmptyState
            title="Insufficient History for Forecasting"
            description={forecast?.message || 'Log at least 3 training sessions to forecast performance trajectory and peak windows.'}
          />
        )}
      </div>

      {/* Training History Table */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold">Training Performance History</h3>
          <button
            onClick={() => downloadCsv('/api/performance/export', 'performance_records.csv')}
            className="btn-secondary text-xs"
            disabled={records.length === 0}
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>
        {records.length === 0 ? (
          <EmptyState
            title="No Performance Sessions Yet"
            description="Logged workouts appear here with AI-predicted calories, HR, speed, RPE, and fatigue."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase">
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Athlete</th>
                  <th className="py-2 pr-4">Exercise</th>
                  <th className="py-2 pr-4">Duration</th>
                  <th className="py-2 pr-4">HR (BPM)</th>
                  <th className="py-2 pr-4">Calories / AI Est.</th>
                  <th className="py-2">RPE / Fatigue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/70 dark:divide-slate-800/70">
                {records.map((r) => (
                  <tr key={r.id}>
                    <td className="py-2 pr-4 font-mono text-slate-400">
                      {new Date(r.session_date).toLocaleDateString()}
                    </td>
                    <td className="py-2 pr-4 font-semibold">{r.athlete_name}</td>
                    <td className="py-2 pr-4">{r.exercise_type}</td>
                    <td className="py-2 pr-4 font-mono">{r.duration_minutes} min</td>
                    <td className="py-2 pr-4 font-mono">{r.heart_rate_bpm}</td>
                    <td className="py-2 pr-4 font-mono text-cyan-500 font-bold">
                      {r.calories_burned ?? r.ai_predicted_calories ?? '—'} kcal
                    </td>
                    <td className="py-2 font-mono">
                      {r.rpe_score ?? '—'}/10 · {r.fatigue_level ?? '—'}/10
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Coach-Athlete Assignment & Admin Directory */}
      {(user?.role === 'admin' || user?.role === 'coach') && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <UserPlus className="w-4 h-4 text-cyan-500" /> Coach & Athlete Assignments
            </h3>
            <form onSubmit={handleAssign} className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <select
                className="input-field"
                value={assignCoachId}
                onChange={(e) => setAssignCoachId(e.target.value)}
                required
              >
                <option value="">Select Coach...</option>
                {coaches.map((c) => (
                  <option key={c.id} value={c.id}>{c.full_name}</option>
                ))}
              </select>
              <select
                className="input-field"
                value={assignAthleteId}
                onChange={(e) => setAssignAthleteId(e.target.value)}
                required
              >
                <option value="">Select Athlete...</option>
                {athletes.map((a) => (
                  <option key={a.id} value={a.id}>{a.full_name}</option>
                ))}
              </select>
              <button type="submit" className="btn-primary">Assign</button>
            </form>
            {assignments.length === 0 ? (
              <p className="text-xs text-slate-400">No coach-athlete pairings created yet.</p>
            ) : (
              <div className="space-y-2">
                {assignments.map((a) => (
                  <div
                    key={a.id}
                    className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs flex justify-between"
                  >
                    <span><strong>{a.coach_name}</strong> → {a.athlete_name}</span>
                    <span className="text-slate-400 font-mono">
                      {new Date(a.assigned_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {user?.role === 'admin' && (
            <div className="glass-card p-6 space-y-4">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-500" /> Admin Role Management
              </h3>
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {users.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs"
                  >
                    <div className="min-w-0">
                      <div className="font-bold truncate">{u.full_name}</div>
                      <div className="text-slate-400 truncate">{u.email}</div>
                    </div>
                    <select
                      className="input-field w-32 py-1 text-xs"
                      value={u.role}
                      onChange={(e) => handleAdminRoleChange(u.id, e.target.value as UserRole)}
                    >
                      <option value="athlete">Athlete</option>
                      <option value="coach">Coach</option>
                      <option value="analyst">Analyst</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
