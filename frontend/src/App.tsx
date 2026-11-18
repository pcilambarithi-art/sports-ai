import { Suspense, lazy } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ModelStatusProvider } from './context/ModelStatusContext';
import { Layout } from './components/Layout';
import { AuthPage } from './pages/AuthPage';

const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const AiPredictionLabPage = lazy(() =>
  import('./pages/AiPredictionLabPage').then((m) => ({ default: m.AiPredictionLabPage }))
);
const AthletesProfilesPage = lazy(() =>
  import('./pages/AthletesProfilesPage').then((m) => ({ default: m.AthletesProfilesPage }))
);
const TrainingProgramsPage = lazy(() =>
  import('./pages/TrainingProgramsPage').then((m) => ({ default: m.TrainingProgramsPage }))
);
const InjuryPreventionPage = lazy(() =>
  import('./pages/InjuryPreventionPage').then((m) => ({ default: m.InjuryPreventionPage }))
);
const VideoAnalysisPage = lazy(() =>
  import('./pages/VideoAnalysisPage').then((m) => ({ default: m.VideoAnalysisPage }))
);
const TelemetryPage = lazy(() => import('./pages/TelemetryPage').then((m) => ({ default: m.TelemetryPage })));
const GameStrategyPage = lazy(() =>
  import('./pages/GameStrategyPage').then((m) => ({ default: m.GameStrategyPage }))
);
const SkillAssessmentPage = lazy(() =>
  import('./pages/SkillAssessmentPage').then((m) => ({ default: m.SkillAssessmentPage }))
);
const GamificationPage = lazy(() =>
  import('./pages/GamificationPage').then((m) => ({ default: m.GamificationPage }))
);
const VirtualCoachPage = lazy(() =>
  import('./pages/VirtualCoachPage').then((m) => ({ default: m.VirtualCoachPage }))
);

function RouteFallback() {
  return (
    <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
      Loading coaching module...
    </div>
  );
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#070B14] text-slate-400 text-sm">
        Initializing ApexPulse AI...
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/ai-lab" element={<AiPredictionLabPage />} />
          <Route path="/athletes" element={<AthletesProfilesPage />} />
          <Route path="/training" element={<TrainingProgramsPage />} />
          <Route path="/injury" element={<InjuryPreventionPage />} />
          <Route path="/video" element={<VideoAnalysisPage />} />
          <Route path="/telemetry" element={<TelemetryPage />} />
          <Route path="/strategy" element={<GameStrategyPage />} />
          <Route path="/skills" element={<SkillAssessmentPage />} />
          <Route path="/gamification" element={<GamificationPage />} />
          <Route path="/assistant" element={<VirtualCoachPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ModelStatusProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </ModelStatusProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
