import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  icon: React.ComponentType<{ className?: string }>;
  accent?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'violet';
}

const ACCENT_MAP = {
  cyan: 'bg-cyan-500/15 text-cyan-500 border-cyan-500/20',
  emerald: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/20',
  amber: 'bg-amber-500/15 text-amber-500 border-amber-500/20',
  rose: 'bg-rose-500/15 text-rose-500 border-rose-500/20',
  violet: 'bg-violet-500/15 text-violet-500 border-violet-500/20',
};

export function StatCard({ label, value, sublabel, icon: Icon, accent = 'cyan' }: StatCardProps) {
  return (
    <div className="glass-card p-5 flex items-start justify-between gap-4 hover:border-cyan-500/40 transition-colors">
      <div className="min-w-0">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </div>
        <div className="mt-2 text-2xl lg:text-3xl font-extrabold tracking-tight font-mono">
          {value}
        </div>
        {sublabel && (
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400 truncate">{sublabel}</div>
        )}
      </div>
      <div className={`p-3 rounded-xl border shrink-0 ${ACCENT_MAP[accent]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}
