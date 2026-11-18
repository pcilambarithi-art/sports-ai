export type UserRole = 'admin' | 'coach' | 'analyst' | 'athlete';

export interface AthleteProfile {
  sport?: string | null;
  position?: string | null;
  age?: number | null;
  gender?: 'Male' | 'Female' | null;
  weight_kg?: number | null;
  height_cm?: number | null;
  experience_level?: 'Beginner' | 'Intermediate' | 'Advanced' | null;
  fitness_goal?: string | null;
  preferred_exercise?: string | null;
  workout_frequency_per_week?: number | null;
  avg_sleep_hours?: number | null;
  avg_water_intake_liters?: number | null;
  resting_heart_rate?: number | null;
}

export interface CoachProfile {
  specialization?: string | null;
  certifications?: string | null;
  years_experience?: number | null;
  team_name?: string | null;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  avatar_initials: string;
  bio?: string | null;
  created_at: string;
  athlete_profile?: AthleteProfile | null;
  coach_profile?: CoachProfile | null;
}

export interface ModelStatus {
  status: 'idle' | 'loading' | 'ready' | 'error';
  ready: boolean;
  error?: string | null;
  load_time_seconds?: number | null;
  loading_elapsed_seconds?: number | null;
  model_path: string;
  model_file_exists: boolean;
  model_size_gb?: number | null;
  algorithm: string;
  n_estimators: number;
  target: string;
  metrics: {
    test_r2?: number | null;
    test_r2_pct?: number | null;
    test_mae?: number | null;
    test_rmse?: number | null;
    cv_mean_r2?: number | null;
    cv_std?: number | null;
  };
  global_feature_importances: {
    feature: string;
    label: string;
    importance: number;
    importance_pct: number;
  }[];
  limitations: string[];
}

export const EXERCISE_TYPES = [
  'Cycling',
  'HIIT',
  'Rowing',
  'Running',
  'Swimming',
  'Walking',
  'Weight Training',
  'Yoga',
] as const;

export const FITNESS_GOALS = [
  'Endurance',
  'Flexibility',
  'General Fitness',
  'Muscle Gain',
  'Weight Loss',
] as const;

export const EXPERIENCE_LEVELS = ['Beginner', 'Intermediate', 'Advanced'] as const;
