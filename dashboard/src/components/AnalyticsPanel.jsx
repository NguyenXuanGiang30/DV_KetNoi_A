import React from 'react';
import { BarChart, Zap, Clock, ShieldAlert, Thermometer, BatteryCharging } from 'lucide-react';

export default function AnalyticsPanel({ metrics }) {
  const data = metrics || {};
  const avgTemp = data.avg_temperature_by_room || {};
  const avgHumid = data.avg_humidity_by_room || {};
  const lowBatteryDevices = data.low_battery_devices || [];

  const tempRooms = Object.keys(avgTemp);
  const maxTemp = tempRooms.length > 0 ? Math.max(...Object.values(avgTemp)) : 40;

  // Calculate access success percentage
  const totalSwipes = (data.total_access_in || 0) + (data.denied_access_count || 0);
  const successRate = totalSwipes > 0 ? ((data.total_access_in || 0) / totalSwipes * 100).toFixed(0) : '0';

  return (
    <div className="cyber-panel border border-cyber-border rounded p-4 cyber-corners flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-cyber-border pb-2 mb-4 font-mono">
        <h2 className="text-sm font-bold text-cyber-cyan tracking-wider flex items-center gap-2 m-0">
          <BarChart className="w-4 h-4 text-cyber-cyan animate-pulse" />
          ANALYTICS_COMMAND_CENTER
        </h2>
        <span className="text-[10px] text-cyber-muted uppercase">SYS_METRICS // CORE</span>
      </div>

      {/* Grid of Key Numerical Analytics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4 font-mono">
        {/* Total Events */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded text-center">
          <span className="text-[9px] text-cyber-muted block uppercase">PEAK_TRAFFIC_HOUR</span>
          <span className="text-sm font-bold text-cyber-cyan text-glow-cyan flex items-center justify-center gap-1 mt-1">
            <Clock className="w-3.5 h-3.5" />
            {data.peak_access_hour || 'N/A'}
          </span>
        </div>

        {/* Danger events */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded text-center">
          <span className="text-[9px] text-cyber-muted block uppercase">CRITICAL_EVENTS</span>
          <span className={`text-base font-bold flex items-center justify-center gap-1 mt-1 ${
            (data.danger_event_count || 0) > 0 ? 'text-cyber-red text-glow-red animate-pulse' : 'text-cyber-muted'
          }`}>
            <Zap className="w-3.5 h-3.5" />
            {data.danger_event_count || 0}
          </span>
        </div>

        {/* Total Access Success Rate */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded text-center">
          <span className="text-[9px] text-cyber-muted block uppercase">GATE_SUCCESS_RATE</span>
          <span className="text-base font-bold text-cyber-green text-glow-green block mt-1">
            {successRate}%
          </span>
          <span className="text-[8px] text-cyber-muted">({data.total_access_in || 0} of {totalSwipes} swipes)</span>
        </div>

        {/* Access Denied Counts */}
        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded text-center">
          <span className="text-[9px] text-cyber-muted block uppercase">GATE_DENIALS</span>
          <span className={`text-base font-bold block mt-1 ${
            (data.denied_access_count || 0) > 0 ? 'text-cyber-red text-glow-red' : 'text-cyber-muted'
          }`}>
            {data.denied_access_count || 0}
          </span>
          <span className="text-[8px] text-cyber-muted">Unauthorized requests</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1">
        {/* SVG Temp Comparisons */}
        <div className="bg-slate-950/60 border border-slate-900 p-3 rounded font-mono">
          <div className="flex items-center gap-1 text-[10px] text-cyber-cyan mb-3">
            <Thermometer className="w-3.5 h-3.5" />
            <span>AVG ROOM TEMPERATURES (°C)</span>
          </div>

          {tempRooms.length === 0 ? (
            <div className="py-6 text-center text-xs text-cyber-muted">[WAITING_FOR_METRIC_RECORDS]</div>
          ) : (
            <div className="space-y-3">
              {tempRooms.map((room) => {
                const temp = avgTemp[room] || 0;
                const widthPercent = maxTemp > 0 ? (temp / maxTemp) * 100 : 0;
                
                return (
                  <div key={room} className="text-xs">
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="text-white font-bold">{room}</span>
                      <span className="text-cyber-cyan">{temp.toFixed(1)}°C</span>
                    </div>
                    {/* Glowing Bar */}
                    <div className="w-full bg-slate-900 h-2 border border-slate-800 rounded overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-cyber-cyan to-cyber-blue h-full shadow-[0_0_6px_#00f0ff] transition-all duration-500"
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Battery Health Warnings */}
        <div className="bg-slate-950/60 border border-slate-900 p-3 rounded font-mono flex flex-col">
          <div className="flex items-center gap-1 text-[10px] text-cyber-amber mb-3">
            <BatteryCharging className="w-3.5 h-3.5" />
            <span>BATTERY REPLACEMENT LOGS</span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[140px] space-y-2">
            {lowBatteryDevices.length === 0 ? (
              <div className="py-8 text-center text-[10px] text-cyber-green">
                🟢 ALL DEVICE POWER CELLS SATISFACTORY
              </div>
            ) : (
              lowBatteryDevices.map((dev) => (
                <div 
                  key={dev.device_id} 
                  className="flex items-center justify-between p-2 border border-cyber-red/20 bg-cyber-red/5 rounded text-xs"
                >
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-3.5 h-3.5 text-cyber-red animate-pulse" />
                    <div>
                      <span className="font-bold text-white">{dev.location}</span>
                      <span className="text-[8px] text-cyber-muted block uppercase">{dev.device_id}</span>
                    </div>
                  </div>
                  <span className="text-cyber-red font-bold animate-pulse text-glow-red">
                    {dev.battery_percent}% PIN
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
