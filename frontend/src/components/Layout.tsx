import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Activity,
  Award,
  Brain,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Cpu,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Moon,
  Radio,
  ShieldAlert,
  Sun,
  Swords,
  Target,
  Users,
  Video,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useModelStatus } from '../context/ModelStatusContext';

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/ai-lab', label: 'AI Model Lab', icon: Brain },
  { to: '/athletes', label: 'Athletes & Profiles', icon: Users },
  { to: '/training', label: 'Training Programs', icon: Calendar },
  { to: '/injury', label: 'Injury Prevention', icon: ShieldAlert },
  { to: '/video', label: 'Video Analysis', icon: Video },
  { to: '/telemetry', label: 'Live Telemetry', icon: Radio },
  { to: '/strategy', label: 'Game Strategy', icon: Swords },
  { to: '/skills', label: 'Skill Assessment', icon: Target },
  { to: '/gamification', label: 'Gamification', icon: Award },
  { to: '/assistant', label: 'Virtual Coach', icon: MessageSquare },
];

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500/40',
  coach: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
  analyst: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
  athlete: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
};

export function Layout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { modelStatus } = useModelStatus();
  const location = useLocation();

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const currentItem = NAV_ITEMS.find((i) => i.to === location.pathname) || NAV_ITEMS[0];

  const renderModelPill = () => {
    if (!modelStatus) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-950/60 border border-purple-500/30 text-purple-200">
          <Cpu className="w-3.5 h-3.5 animate-pulse" /> Checking AI Models...
        </span>
      );
    }
    if (modelStatus.ready) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-purple-500/20 via-fuchsia-500/20 to-cyan-500/20 text-purple-700 dark:text-cyan-300 border border-purple-400/40 shadow-[0_0_16px_-4px_rgba(168,85,247,0.6)]">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
          AI Models Ready ({modelStatus.metrics.test_r2_pct ?? '91.81'}% R²)
        </span>
      );
    }
    if (modelStatus.status === 'loading') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-300 border border-amber-400/35">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          Loading 2.93 GB Model ({modelStatus.loading_elapsed_seconds ?? 0}s)...
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/35">
        <span className="w-2 h-2 rounded-full bg-rose-500" />
        Model Offline ({modelStatus.status})
      </span>
    );
  };

  return (
    <div className="min-h-screen flex app-cosmic-bg text-slate-900 dark:text-purple-50">
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/75 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Glossy Purple-Black Sidebar with Glowing Neon Edge */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-50 h-screen flex flex-col bg-white/90 dark:bg-[#080312]/92 backdrop-blur-2xl border-r border-purple-300/60 dark:border-purple-500/30 shadow-[4px_0_32px_-12px_rgba(168,85,247,0.45)] transition-all duration-200 ${
          collapsed ? 'w-20' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-purple-200/70 dark:border-purple-500/20">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 via-fuchsia-500 to-cyan-400 flex items-center justify-center shrink-0 shadow-[0_0_18px_rgba(192,38,211,0.6)]">
              <Activity className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="leading-tight">
                <div className="font-extrabold text-sm tracking-tight bg-gradient-to-r from-purple-400 via-fuchsia-400 to-cyan-300 bg-clip-text text-transparent">
                  ApexPulse AI
                </div>
                <div className="text-[10px] font-semibold uppercase tracking-widest text-purple-500 dark:text-purple-300/80">
                  Sports Coaching
                </div>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="hidden lg:inline-flex p-1.5 rounded-lg text-purple-400 hover:text-purple-200 hover:bg-purple-500/15 cursor-pointer"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-purple-400"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-purple-600/30 via-fuchsia-600/20 to-cyan-500/15 text-purple-700 dark:text-white border border-purple-400/50 shadow-[0_0_18px_-6px_rgba(192,38,211,0.75)]'
                      : 'text-slate-600 dark:text-purple-200/70 hover:bg-purple-500/10 hover:text-purple-800 dark:hover:text-white border border-transparent'
                  }`
                }
                title={collapsed ? item.label : undefined}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        <div className="p-3 border-t border-purple-200/70 dark:border-purple-500/20">
          {user && (
            <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} gap-2`}>
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-600/40 to-fuchsia-600/40 border border-purple-400/40 flex items-center justify-center font-bold text-xs text-purple-700 dark:text-purple-100 shrink-0 shadow-[0_0_12px_rgba(168,85,247,0.4)]">
                  {user.avatar_initials}
                </div>
                {!collapsed && (
                  <div className="min-w-0">
                    <div className="text-xs font-semibold truncate">{user.full_name}</div>
                    <span
                      className={`inline-block mt-0.5 px-2 py-0.2 rounded-full text-[10px] font-semibold uppercase border ${
                        ROLE_COLORS[user.role] || ''
                      }`}
                    >
                      {user.role}
                    </span>
                  </div>
                )}
              </div>
              {!collapsed && (
                <button
                  onClick={logout}
                  className="p-2 rounded-lg text-purple-400 hover:text-rose-400 hover:bg-rose-500/15 transition-colors cursor-pointer"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 h-16 px-4 lg:px-8 flex items-center justify-between bg-white/80 dark:bg-[#070310]/80 backdrop-blur-xl border-b border-purple-200/70 dark:border-purple-500/25">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-xl bg-purple-500/15 text-purple-400"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-base lg:text-lg font-extrabold tracking-tight bg-gradient-to-r from-purple-600 via-fuchsia-500 to-cyan-500 dark:from-white dark:via-purple-200 dark:to-cyan-200 bg-clip-text text-transparent">
              {currentItem.label}
            </h1>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="hidden sm:block">{renderModelPill()}</div>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-purple-100/80 dark:bg-[#170A2C] hover:bg-purple-200 dark:hover:bg-[#231042] border border-purple-300/60 dark:border-purple-500/35 text-purple-700 dark:text-purple-200 transition-colors cursor-pointer"
              title="Toggle dark/light theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8 max-w-[1600px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
