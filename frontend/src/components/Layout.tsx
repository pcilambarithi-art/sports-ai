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
  roles?: string[];
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
  admin: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  coach: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  analyst: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  athlete: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
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
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
          <Cpu className="w-3.5 h-3.5 animate-pulse" /> Checking AI Model...
        </span>
      );
    }
    if (modelStatus.ready) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Trained Model Ready ({modelStatus.metrics.test_r2_pct ?? '91.8'}% R²)
        </span>
      );
    }
    if (modelStatus.status === 'loading') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          Loading 2.93 GB Model ({modelStatus.loading_elapsed_seconds ?? 0}s)...
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-500 border border-rose-500/30">
        <span className="w-2 h-2 rounded-full bg-rose-500" />
        Model Offline ({modelStatus.status})
      </span>
    );
  };

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-[#070B14] text-slate-900 dark:text-slate-100">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-50 h-screen flex flex-col bg-white dark:bg-[#0B1222] border-r border-slate-200 dark:border-slate-800/90 transition-all duration-200 ${
          collapsed ? 'w-20' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800/80">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20">
              <Activity className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="leading-tight">
                <div className="font-extrabold text-sm tracking-tight">ApexPulse AI</div>
                <div className="text-[10px] font-semibold uppercase tracking-widest text-cyan-500">
                  Sports Coaching
                </div>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="hidden lg:inline-flex p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-slate-400"
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
                      ? 'bg-gradient-to-r from-cyan-500/15 to-emerald-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/25 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100 border border-transparent'
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

        <div className="p-3 border-t border-slate-200 dark:border-slate-800/80">
          {user && (
            <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} gap-2`}>
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-slate-200 dark:bg-slate-800 flex items-center justify-center font-bold text-xs text-cyan-600 dark:text-cyan-400 shrink-0">
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
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition-colors cursor-pointer"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 h-16 px-4 lg:px-8 flex items-center justify-between bg-white/85 dark:bg-[#070B14]/85 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-xl bg-slate-100 dark:bg-slate-800"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-base lg:text-lg font-bold tracking-tight">{currentItem.label}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="hidden sm:block">{renderModelPill()}</div>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800/90 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
              title="Toggle dark/light theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
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
