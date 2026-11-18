import React, { useState } from 'react';
import { Activity, Brain, ShieldCheck, Video } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types';

export function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<UserRole>('coach');
  const [sport, setSport] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register({
          email,
          full_name: fullName,
          password,
          role,
          sport: sport || undefined,
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Authentication failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-50 dark:bg-[#070B14] text-slate-900 dark:text-slate-100">
      {/* Left Hero Panel */}
      <div className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-[#0B1222] via-[#0F1B33] to-[#08192B] text-white relative overflow-hidden">
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-cyan-500/15 blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-emerald-500/15 blur-3xl" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="text-xl font-extrabold tracking-tight">ApexPulse AI</div>
            <div className="text-xs uppercase tracking-widest text-cyan-400 font-semibold">
              Sports Coaching Intelligence
            </div>
          </div>
        </div>

        <div className="relative z-10 space-y-6 max-w-lg">
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight">
            Real ML Models. Real Telemetry.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
              Zero Guesswork.
            </span>
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Powered directly by your trained 300-tree ExtraTreesRegressor calorie model (91.81% R² on
            70,000 workout profiles), integrated with OpenCV movement analysis, adaptive training
            schedules, workload injury prevention, game strategy, and a data-grounded virtual coach.
          </p>

          <div className="grid grid-cols-1 gap-3 pt-2">
            {[
              {
                icon: Brain,
                title: 'Integrated Trained ML Pipeline',
                desc: 'Direct scikit-learn inference with 300-tree uncertainty bands & what-if explanations.',
              },
              {
                icon: Video,
                title: 'OpenCV Movement Breakdown',
                desc: 'Optical flow intensity profiling, contour tracking & annotated key moments.',
              },
              {
                icon: ShieldCheck,
                title: 'Role-Based Coaching Security',
                desc: 'Dedicated workflows for Admins, Coaches, Sports Analysts & Athletes.',
              },
            ].map((feat) => {
              const Icon = feat.icon;
              return (
                <div
                  key={feat.title}
                  className="flex items-start gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/10"
                >
                  <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-300 shrink-0">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{feat.title}</div>
                    <div className="text-xs text-slate-400">{feat.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="relative z-10 text-xs text-slate-400">
          Model Artifact: <span className="font-mono text-cyan-300">D:\V3\trained_models\calorie_prediction_model.pkl</span>
        </div>
      </div>

      {/* Right Auth Form */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md glass-card p-8">
          <div className="flex items-center gap-2 mb-6 lg:hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold text-lg">ApexPulse AI</span>
          </div>

          <div className="flex rounded-xl p-1 bg-slate-100 dark:bg-slate-800/80 mb-6">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError(null);
              }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all cursor-pointer ${
                mode === 'login'
                  ? 'bg-white dark:bg-slate-900 shadow-xs text-cyan-600 dark:text-cyan-400'
                  : 'text-slate-500'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setError(null);
              }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all cursor-pointer ${
                mode === 'register'
                  ? 'bg-white dark:bg-slate-900 shadow-xs text-cyan-600 dark:text-cyan-400'
                  : 'text-slate-500'
              }`}
            >
              Create Account
            </button>
          </div>

          <h1 className="text-2xl font-extrabold tracking-tight">
            {mode === 'login' ? 'Welcome back' : 'Join ApexPulse AI'}
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6">
            {mode === 'login'
              ? 'Sign in with your coaching or athlete credentials.'
              : 'Create a secure role-based account to start logging and analyzing real performance data.'}
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="label-text">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g., Alex Morgan"
                  className="input-field"
                />
              </div>
            )}

            <div>
              <label className="label-text">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@team.com"
                className="input-field"
              />
            </div>

            <div>
              <label className="label-text">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="input-field"
              />
            </div>

            {mode === 'register' && (
              <>
                <div>
                  <label className="label-text">Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as UserRole)}
                    className="input-field"
                  >
                    <option value="athlete">Athlete / Player</option>
                    <option value="coach">Coach / Trainer</option>
                    <option value="analyst">Sports Analyst</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div>
                  <label className="label-text">Primary Sport (Optional)</label>
                  <input
                    type="text"
                    value={sport}
                    onChange={(e) => setSport(e.target.value)}
                    placeholder="e.g., Football, Athletics, Swimming, Basketball"
                    className="input-field"
                  />
                </div>
              </>
            )}

            <button type="submit" disabled={submitting} className="btn-primary w-full py-3">
              {submitting
                ? 'Authenticating...'
                : mode === 'login'
                ? 'Sign In to Dashboard'
                : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
