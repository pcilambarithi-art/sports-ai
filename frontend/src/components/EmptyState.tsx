import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 px-6 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700/80 bg-slate-50/50 dark:bg-slate-900/30">
      <div className="w-12 h-12 rounded-2xl bg-slate-200/70 dark:bg-slate-800 flex items-center justify-center mb-3 text-slate-500 dark:text-slate-400">
        <Inbox className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">{title}</h3>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-md">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
