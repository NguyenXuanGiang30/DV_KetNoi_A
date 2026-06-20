import React, { useState, useEffect } from 'react';
import HUDHeader from './components/HUDHeader';
import EnvironmentPanel from './components/EnvironmentPanel';
import AccessControlPanel from './components/AccessControlPanel';
import AlertCenterPanel from './components/AlertCenterPanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import { RefreshCw, Play, ShieldAlert, Cpu } from 'lucide-react';

export default function App() {
  const [recentEvents, setRecentEvents] = useState([]);
  const [accessLogs, setAccessLogs] = useState({ items: [], total: 0 });
  const [alertLogs, setAlertLogs] = useState({ items: [], total: 0 });
  const [metrics, setMetrics] = useState({});
  const [serviceStatus, setServiceStatus] = useState({
    ingestion: false,
    camera: false,
    access_gate: false,
    ai_vision: false,
    analytics: false,
    core: false,
    notification: false,
  });
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(2000);

  const fetchData = async () => {
    const token = 'smart-campus-dev-token-2026';
    const headers = {
      'Authorization': `Bearer ${token}`
    };

    // Health check helper
    const checkHealth = async (url) => {
      try {
        const res = await fetch(url);
        return res.status === 200;
      } catch {
        return false;
      }
    };

    // Parallel fetch health checks
    const statuses = await Promise.all([
      checkHealth('/api/v1/ingestion/health'),
      checkHealth('/api/v1/camera/health'),
      checkHealth('/api/v1/access/health'),
      checkHealth('/api/v1/vision/health'),
      checkHealth('/api/v1/analytics/health'),
      checkHealth('/api/v1/core/health'),
      checkHealth('/api/v1/notifications/health'),
    ]);

    setServiceStatus({
      ingestion: statuses[0],
      camera: statuses[1],
      access_gate: statuses[2],
      ai_vision: statuses[3],
      analytics: statuses[4],
      core: statuses[5],
      notification: statuses[6],
    });

    // Parallel fetch data endpoints
    try {
      const [eventsRes, accessRes, alertRes, metricsRes] = await Promise.all([
        fetch('/api/v1/analytics/events/recent', { headers }).then(r => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
        fetch('/api/v1/access/logs/recent', { headers }).then(r => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
        fetch('/api/v1/notifications/recent', { headers }).then(r => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
        fetch('/api/v1/analytics/metrics', { headers }).then(r => r.ok ? r.json() : {}).catch(() => ({})),
      ]);

      setRecentEvents(eventsRes.items || []);
      setAccessLogs(accessRes);
      setAlertLogs(alertRes);
      setMetrics(metricsRes);
    } catch (err) {
      console.error("Error reading backend data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const anyServiceDown = Object.values(serviceStatus).some(status => !status);

  return (
    <div className="min-h-screen bg-cyber-bg cyber-grid cyber-grid-radial relative flex flex-col text-slate-200 selection:bg-cyber-cyan selection:text-black">
      {/* HUD Header */}
      <HUDHeader stats={metrics} serviceStatus={serviceStatus} />

      {/* Main Content Layout */}
      <main className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-6 space-y-6 z-10">
        
        {/* Service Interruption Bar if any service is down */}
        {anyServiceDown && (
          <div className="bg-cyber-red/10 border border-cyber-red p-3 rounded font-mono text-xs flex items-center justify-between text-cyber-red animate-pulse">
            <span className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              WARNING: ONE OR MORE INTEGRATED BACKEND MICROSERVICES ARE OFFLINE. SECURE PROTOCOLS SUSPENDED.
            </span>
            <span className="hidden sm:inline">[PORT_DIAGNOSTICS_ACTIVE]</span>
          </div>
        )}

        {/* Dashboard Status controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-950/40 border border-slate-900 p-3 rounded font-mono text-xs">
          <div className="flex items-center gap-3">
            <RefreshCw className={`w-4 h-4 text-cyber-cyan ${loading ? 'animate-spin' : ''}`} />
            <span className="text-cyber-muted uppercase">POLLING_FREQUENCY:</span>
            <select 
              value={refreshInterval} 
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-slate-900 border border-slate-800 text-white rounded px-2 py-0.5 outline-none focus:border-cyber-cyan"
            >
              <option value={1000}>1.0s (AGGRESSIVE)</option>
              <option value={2000}>2.0s (OPTIMIZED)</option>
              <option value={5000}>5.0s (STABLE)</option>
            </select>
          </div>
          
          <div className="text-[10px] text-cyber-muted text-right">
            <span>DATA SOURCE: LOCAL_DOCKER_CONTAINERS (PORTS: 8001-8007)</span>
          </div>
        </div>

        {/* Dynamic Panels Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Environmental Telemetry (Takes 2 cols on wide, 1 col normally) */}
          <div className="lg:col-span-2 space-y-6">
            <EnvironmentPanel recentEvents={recentEvents} />
            <AnalyticsPanel metrics={metrics} />
          </div>

          {/* Right Column: Access logs & Alert Center */}
          <div className="space-y-6">
            <AccessControlPanel accessLogs={accessLogs} />
            <AlertCenterPanel alertLogs={alertLogs} />
          </div>

        </div>

        {/* Guide footer section */}
        <footer className="border-t border-slate-900 pt-6 mt-12 pb-12 font-mono text-[10px] text-cyber-muted text-center space-y-2">
          <div>SMART CAMPUS NETWORK LAYER SECURED WITH RSA-SHA256 PROTOCOLS // LOCALHOST LAYER ACTIVE</div>
          <div className="flex items-center justify-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-cyber-cyan" />
            <span>To populate this dashboard, run: <code className="bg-slate-950 border border-slate-800 text-white px-2 py-0.5 rounded">python test_all_services_lan.py</code></span>
          </div>
        </footer>

      </main>
    </div>
  );
}
