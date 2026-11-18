import React, { useEffect, useRef, useState } from 'react';
import { Activity, Flame, Gauge, Heart, Radio, Send, Timer, Wifi, WifiOff } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest, buildWsUrl, getStoredToken } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { StatCard } from '../components/StatCard';
import { EmptyState } from '../components/EmptyState';

export function TelemetryPage() {
  const { user } = useAuth();
  const [status, setStatus] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const [manual, setManual] = useState({
    device_name: 'Manual Check-In',
    heart_rate_bpm: '142',
    speed_kmh: '11.4',
    distance_km: '4.2',
    duration_minutes: '22',
    calories: '240',
    muscle_load_pct: '62',
    fatigue_index: '5',
  });

  const loadTelemetry = async () => {
    try {
      const [st, hist] = await Promise.all([
        apiRequest<any>('/api/telemetry/status'),
        apiRequest<any[]>('/api/telemetry/history?limit=40'),
      ]);
      setStatus(st);
      setHistory(hist);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadTelemetry();
  }, []);

  // Connect real WebSocket stream for live incoming sensor readings
  useEffect(() => {
    if (!user) return;
    const token = getStoredToken();
    if (!token) return;

    const ws = new WebSocket(buildWsUrl(`/api/telemetry/ws/${user.id}?token=${encodeURIComponent(token)}`));
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.event === 'telemetry_update' && msg.reading) {
          setHistory((prev) => [...prev.slice(-59), msg.reading]);
          setStatus((prev: any) =>
            prev
              ? {
                  ...prev,
                  latest_reading: msg.reading,
                  hardware_connected:
                    msg.reading.source_type === 'wearable_webhook' ||
                    msg.reading.source_type === 'iot_sensor' ||
                    prev.hardware_connected,
                }
              : prev
          );
        }
      } catch {
        // ignore malformed frames
      }
    };

    const ping = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 25000);

    return () => {
      window.clearInterval(ping);
      ws.close();
    };
  }, [user]);

  const handleManualLog = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiRequest('/api/telemetry/ingest', {
        method: 'POST',
        body: JSON.stringify({
          source_type: 'manual',
          device_name: manual.device_name,
          heart_rate_bpm: manual.heart_rate_bpm ? Number(manual.heart_rate_bpm) : null,
          speed_kmh: manual.speed_kmh ? Number(manual.speed_kmh) : null,
          distance_km: manual.distance_km ? Number(manual.distance_km) : null,
          duration_minutes: manual.duration_minutes ? Number(manual.duration_minutes) : null,
          calories: manual.calories ? Number(manual.calories) : null,
          muscle_load_pct: manual.muscle_load_pct ? Number(manual.muscle_load_pct) : null,
          fatigue_index: manual.fatigue_index ? Number(manual.fatigue_index) : null,
        }),
      });
      await loadTelemetry();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const latest = status?.latest_reading;
  const chartData = history.map((h) => ({
    time: new Date(h.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    heart_rate_bpm: h.heart_rate_bpm,
    speed_kmh: h.speed_kmh,
  }));

  return (
    <div className="space-y-6">
      {/* Honest Hardware Integration Status Banner */}
      <div
        className={`p-5 rounded-2xl border flex flex-wrap items-center justify-between gap-4 ${
          status?.hardware_connected
            ? 'bg-emerald-500/10 border-emerald-500/30'
            : 'bg-amber-500/10 border-amber-500/30'
        }`}
      >
        <div className="flex items-start gap-3">
          {status?.hardware_connected ? (
            <Wifi className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
          ) : (
            <WifiOff className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          )}
          <div>
            <div className="text-sm font-extrabold">
              {status?.status_label || 'Awaiting Wearable / IoT Sensor Integration'}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">
              {status?.hardware_connected
                ? 'Receiving live external wearable/IoT telemetry readings via webhook & WebSocket push.'
                : 'No wearable sensor or IoT hardware stream is currently connected. This dashboard never fabricates simulated heart-rate data. Connect a sensor via the Webhook API below or record a real manual reading.'}
            </p>
          </div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
            wsConnected
              ? 'bg-emerald-500/15 text-emerald-500'
              : 'bg-slate-200 dark:bg-slate-800 text-slate-500'
          }`}
        >
          <Radio className="w-3.5 h-3.5" /> WebSocket: {wsConnected ? 'Subscribed' : 'Connecting...'}
        </span>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-500 text-xs">
          {error}
        </div>
      )}

      {/* Live Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="Heart Rate"
          value={latest?.heart_rate_bpm != null ? `${latest.heart_rate_bpm} BPM` : '—'}
          sublabel={latest ? latest.device_name : 'Awaiting reading'}
          icon={Heart}
          accent="rose"
        />
        <StatCard
          label="Speed"
          value={latest?.speed_kmh != null ? `${latest.speed_kmh} km/h` : '—'}
          sublabel={latest?.distance_km != null ? `Distance: ${latest.distance_km} km` : 'Awaiting reading'}
          icon={Gauge}
          accent="cyan"
        />
        <StatCard
          label="Duration"
          value={latest?.duration_minutes != null ? `${latest.duration_minutes} min` : '—'}
          sublabel="Session elapsed"
          icon={Timer}
          accent="violet"
        />
        <StatCard
          label="Calories"
          value={latest?.calories != null ? `${latest.calories} kcal` : '—'}
          sublabel="Logged energy burn"
          icon={Flame}
          accent="amber"
        />
        <StatCard
          label="Muscle / Fatigue"
          value={
            latest?.muscle_load_pct != null
              ? `${latest.muscle_load_pct}%`
              : latest?.fatigue_index != null
              ? `${latest.fatigue_index}/10`
              : '—'
          }
          sublabel={latest?.fatigue_index != null ? `Fatigue index: ${latest.fatigue_index}/10` : 'Biometric load'}
          icon={Activity}
          accent="emerald"
        />
      </div>

      {/* Live Stream Chart */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold mb-4">Real-Time Telemetry Stream</h3>
        {chartData.length === 0 ? (
          <EmptyState
            title="Awaiting Live Telemetry Readings"
            description="Once a wearable sensor posts to /api/telemetry/webhook or you log a live telemetry reading below, metrics stream here over WebSocket in real time."
          />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '10px',
                    fontSize: '12px',
                  }}
                />
                <Line type="monotone" dataKey="heart_rate_bpm" name="Heart Rate (BPM)" stroke="#f43f5e" strokeWidth={2.5} />
                <Line type="monotone" dataKey="speed_kmh" name="Speed (km/h)" stroke="#06b6d4" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Manual Real Telemetry Logger */}
        <form onSubmit={handleManualLog} className="glass-card p-6 space-y-4">
          <h3 className="text-sm font-bold">Record Live Telemetry Check-In</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="label-text">HR (BPM)</label>
              <input className="input-field" type="number" value={manual.heart_rate_bpm} onChange={(e) => setManual({ ...manual, heart_rate_bpm: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Speed (km/h)</label>
              <input className="input-field" type="number" step="0.1" value={manual.speed_kmh} onChange={(e) => setManual({ ...manual, speed_kmh: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Distance (km)</label>
              <input className="input-field" type="number" step="0.1" value={manual.distance_km} onChange={(e) => setManual({ ...manual, distance_km: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Duration (m)</label>
              <input className="input-field" type="number" value={manual.duration_minutes} onChange={(e) => setManual({ ...manual, duration_minutes: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Calories</label>
              <input className="input-field" type="number" value={manual.calories} onChange={(e) => setManual({ ...manual, calories: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Muscle Load %</label>
              <input className="input-field" type="number" value={manual.muscle_load_pct} onChange={(e) => setManual({ ...manual, muscle_load_pct: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Fatigue (0-10)</label>
              <input className="input-field" type="number" step="0.5" value={manual.fatigue_index} onChange={(e) => setManual({ ...manual, fatigue_index: e.target.value })} />
            </div>
            <div>
              <label className="label-text">Source Label</label>
              <input className="input-field" value={manual.device_name} onChange={(e) => setManual({ ...manual, device_name: e.target.value })} />
            </div>
          </div>
          <button type="submit" className="btn-primary">
            <Send className="w-4 h-4" /> Push Reading to Live Stream
          </button>
        </form>

        {/* Wearable / IoT Integration Snippet */}
        <div className="glass-card p-6 space-y-3">
          <h3 className="text-sm font-bold">Wearable &amp; IoT Sensor Webhook Integration</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Stream readings from Garmin, Polar, Apple Health bridges, or custom ESP32/BLE IoT sensors directly into
            this dashboard using your configured `SENSOR_API_KEY`:
          </p>
          <pre className="p-4 rounded-xl bg-slate-950 text-cyan-300 text-[11px] overflow-x-auto font-mono">
{`POST /api/telemetry/webhook
Header: X-Sensor-API-Key: <SENSOR_API_KEY>
Content-Type: application/json

{
  "athlete_id": ${user?.id ?? 1},
  "source_type": "wearable_webhook",
  "device_name": "Polar H10 / Garmin HRM",
  "heart_rate_bpm": 156,
  "speed_kmh": 13.8,
  "distance_km": 5.4,
  "duration_minutes": 24,
  "calories": 295,
  "muscle_load_pct": 68,
  "fatigue_index": 5.5
}`}
          </pre>
        </div>
      </div>
    </div>
  );
}
