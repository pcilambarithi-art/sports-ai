import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiRequest } from '../lib/api';
import type { ModelStatus } from '../types';

interface ModelStatusContextValue {
  modelStatus: ModelStatus | null;
  refreshModelStatus: () => Promise<void>;
}

const ModelStatusContext = createContext<ModelStatusContextValue | null>(null);

export function ModelStatusProvider({ children }: { children: React.ReactNode }) {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);

  const refreshModelStatus = async () => {
    try {
      const data = await apiRequest<ModelStatus>('/api/ml/status');
      setModelStatus(data);
    } catch {
      // Backend might still be starting
    }
  };

  useEffect(() => {
    refreshModelStatus();
  }, []);

  useEffect(() => {
    if (modelStatus?.status === 'ready' || modelStatus?.status === 'error') {
      return;
    }
    const timer = window.setInterval(refreshModelStatus, 5000);
    return () => window.clearInterval(timer);
  }, [modelStatus?.status]);

  return (
    <ModelStatusContext.Provider value={{ modelStatus, refreshModelStatus }}>
      {children}
    </ModelStatusContext.Provider>
  );
}

export function useModelStatus() {
  const ctx = useContext(ModelStatusContext);
  if (!ctx) throw new Error('useModelStatus must be used inside ModelStatusProvider');
  return ctx;
}
