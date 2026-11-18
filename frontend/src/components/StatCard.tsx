import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  icon: React.ComponentType<{ className?: string }>;
  accent?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'violet';
}

const ACCENT_MAP = {
  cyan: 'bg-cyan-500/20 text-cyan-400 border-cyan-400/35 shadow-[0_0_16px_-4px_rgba(34,211,238,0.65)]',
  emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-400/35 shadow-[0_0_16px_-4px_rgba(16,185,129,0.65)]',
  amber: 'bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-400/35 shadow-[0_0_16px_-4px_rgba(236,72,153,0.65)]',
  rose: 'bg-rose-500/20 text-rose-400 border-rose-400/35 shadow-[0_0_16px_-4px_rgba(244,63,94,0.65)]',
  violet: 'bg-purple-500/20 text-purple-400 border-purple-400/35 shadow-[0_0_16px_-4px_rgba(168,85,247,0.7)]',
};

export function StatCard({ label, value, sublabel, icon: Icon, accent = 'violet' }: StatCardProps) {
  return (
    <div className="glass-card p-5 flex items-start justify-between gap-4 hover:-translate-y-0.5">
      <div className="min-w-0">
        <div className="text-xs font-semibold uppercase tracking-wider text-purple-600/80 dark:text-purple-300/75">
          {label}
        </div>
        <div className="mt-2 text-2xl lg:text-3xl font-extrabold tracking-tight font-mono bg-gradient-to-r from-slate-900 to-purple-800 dark:from-white dark:via-purple-100 dark:to-cyan-200 bg-clip-text text-transparent">
          {value}
        </div>
        {sublabel && (
          <div className="mt-1 text-xs text-slate-500 dark:text-purple-200/60 truncate">{sublabel}</div>
        )}
      </div>
      <div className={`p-3 rounded-xl border shrink-0 ${ACCENT_MAP[accent]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}
