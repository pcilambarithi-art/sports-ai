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
    <div className="min-h-screen grid lg:grid-cols-2 app-cosmic-bg text-slate-900 dark:text-purple-50">
      {/* Left Glossy Purple-Black Hero Panel */}
      <div className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-[#06020D] via-[#13072B] to-[#080214] text-white relative overflow-hidden border-r border-purple-500/30">
        <div className="absolute -top-24 -left-24 w-[28rem] h-[28rem] rounded-full bg-purple-600/25 blur-3xl" />
        <div className="absolute top-1/2 -right-24 w-80 h-80 rounded-full bg-fuchsia-600/20 blur-3xl" />
        <div className="absolute -bottom-20 left-1/3 w-96 h-96 rounded-full bg-cyan-500/15 blur-3xl" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-purple-500 via-fuchsia-500 to-cyan-400 flex items-center justify-center shadow-[0_0_24px_rgba(192,38,211,0.7)]">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-purple-200 to-cyan-200 bg-clip-text text-transparent">
              ApexPulse AI
            </div>
            <div className="text-xs uppercase tracking-widest text-fuchsia-300 font-semibold">
              Sports Coaching Intelligence
            </div>
          </div>
        </div>

        <div className="relative z-10 space-y-6 max-w-lg">
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight">
            Trained ML Models. Live Vision.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-fuchsia-400 to-cyan-300">
              Next-Gen Coaching.
            </span>
          </h2>
          <p className="text-purple-100/75 text-sm leading-relaxed">
            Powered by your preserved 300-tree ExtraTreesRegressor calorie model (91.81% R² on 70,000
            workouts) paired with our continuously trained Readiness Classifier, Semantic NLP Virtual
            Coach, OpenCV movement tracking, workload injury prevention, and game strategy engine.
          </p>

          <div className="grid grid-cols-1 gap-3 pt-2">
            {[
              {
                icon: Brain,
                title: 'Dual Trained AI / ML Engine',
                desc: 'Your D:\\V3 ExtraTrees model + DB-trained Strain Classifier & Semantic Coaching NLP.',
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
                  className="flex items-start gap-3 p-3.5 rounded-2xl bg-purple-950/40 backdrop-blur-md border border-purple-400/25 shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]"
                >
                  <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500/30 to-fuchsia-500/30 border border-purple-400/30 text-cyan-300 shrink-0">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{feat.title}</div>
                    <div className="text-xs text-purple-200/70">{feat.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="relative z-10 text-xs text-purple-300/70">
          Primary Model: <span className="font-mono text-cyan-300">D:\V3\trained_models\calorie_prediction_model.pkl</span>
        </div>
      </div>

      {/* Right Glossy Auth Card */}
      <div className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md glass-card p-8">
          <div className="flex items-center gap-2 mb-6 lg:hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 via-fuchsia-500 to-cyan-400 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold text-lg">ApexPulse AI</span>
          </div>

          <div className="flex rounded-xl p-1 bg-purple-100/80 dark:bg-[#120724] border border-purple-300/40 dark:border-purple-500/25 mb-6">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError(null);
              }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all cursor-pointer ${
                mode === 'login'
                  ? 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white shadow-[0_0_14px_rgba(192,38,211,0.5)]'
                  : 'text-purple-400'
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
                  ? 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white shadow-[0_0_14px_rgba(192,38,211,0.5)]'
                  : 'text-purple-400'
              }`}
            >
              Create Account
            </button>
          </div>

          <h1 className="text-2xl font-extrabold tracking-tight">
            {mode === 'login' ? 'Welcome back' : 'Join ApexPulse AI'}
          </h1>
          <p className="text-xs text-slate-500 dark:text-purple-200/70 mt-1 mb-6">
            {mode === 'login'
              ? 'Sign in with your coaching or athlete credentials.'
              : 'Create a secure role-based account to start logging and analyzing real performance data.'}
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-400 text-xs font-medium">
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
