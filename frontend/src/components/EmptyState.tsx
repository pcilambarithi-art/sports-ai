import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 px-6 rounded-2xl border border-dashed border-purple-300 dark:border-purple-500/35 bg-purple-50/40 dark:bg-[#100621]/50">
      <div className="w-12 h-12 rounded-2xl bg-purple-200/60 dark:bg-purple-950/80 border border-purple-400/30 flex items-center justify-center mb-3 text-purple-600 dark:text-purple-300 shadow-[0_0_16px_-4px_rgba(168,85,247,0.5)]">
        <Inbox className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-bold text-slate-800 dark:text-purple-100">{title}</h3>
      <p className="mt-1 text-xs text-slate-500 dark:text-purple-200/65 max-w-md">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
