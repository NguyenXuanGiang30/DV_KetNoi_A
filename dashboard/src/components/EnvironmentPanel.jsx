import React from 'react';
import { Thermometer, Droplets, Wind, AlertTriangle, Cpu } from 'lucide-react';

export default function EnvironmentPanel({ recentEvents }) {
  // Extract latest state per room from the recentEvents array
  // recentEvents format: { topic, event: { device_id, temperature_c, humidity_percent, co2_ppm, smoke_ppm, battery_percent, location }, at }
  const getRoomsData = () => {
    const rooms = {};
    
    // Process from oldest to newest so latest overwrites
    [...recentEvents].reverse().forEach(evt => {
      const data = evt.event;
      if (!data || !data.location) return;
      
      const loc = data.location;
      if (!rooms[loc]) {
        rooms[loc] = {
          location: loc,
          device_id: data.device_id,
          temperature_c: data.temperature_c,
          humidity_percent: data.humidity_percent,
          co2_ppm: data.co2_ppm || 0,
          smoke_ppm: data.smoke_ppm || 0,
          battery_percent: data.battery_percent ?? 100,
          history: []
        };
      }
      
      // Update values
      rooms[loc].temperature_c = data.temperature_c;
      rooms[loc].humidity_percent = data.humidity_percent;
      rooms[loc].co2_ppm = data.co2_ppm || rooms[loc].co2_ppm;
      rooms[loc].smoke_ppm = data.smoke_ppm || rooms[loc].smoke_ppm;
      rooms[loc].battery_percent = data.battery_percent ?? rooms[loc].battery_percent;
      
      // Keep up to 10 historical values for charts
      rooms[loc].history.push(data.temperature_c);
      if (rooms[loc].history.length > 12) {
        rooms[loc].history.shift();
      }
    });
    
    return Object.values(rooms);
  };

  const rooms = getRoomsData();

  // Helper to render simple SVG sparkline path
  const renderSparkline = (history) => {
    if (!history || history.length < 2) return null;
    const width = 100;
    const height = 30;
    const min = Math.min(...history) - 1;
    const max = Math.max(...history) + 1;
    const range = max - min || 1;
    
    const points = history.map((val, idx) => {
      const x = (idx / (history.length - 1)) * width;
      const y = height - ((val - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg className="w-full h-8 overflow-visible" viewBox={`0 0 ${width} ${height}`}>
        <polyline
          fill="none"
          stroke="#00f0ff"
          strokeWidth="2"
          points={points}
          className="drop-shadow-[0_0_4px_#00f0ff]"
        />
      </svg>
    );
  };

  return (
    <div className="cyber-panel border border-cyber-border rounded p-4 cyber-corners">
      <div className="flex items-center justify-between border-b border-cyber-border pb-2 mb-4 font-mono">
        <h2 className="text-sm font-bold text-cyber-cyan tracking-wider flex items-center gap-2 m-0">
          <Thermometer className="w-4 h-4 text-cyber-cyan animate-pulse" />
          ENVIRONMENTAL_TELEMETRY
        </h2>
        <span className="text-[10px] text-cyber-muted uppercase">REAL_TIME // SENSORS</span>
      </div>

      {rooms.length === 0 ? (
        <div className="py-12 text-center text-cyber-muted font-mono text-xs">
          [WAITING_FOR_SENSOR_TELEMETRY...]
          <p className="text-[10px] mt-1">Publish room events to active topic to view metrics.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rooms.map((room) => {
            const isDanger = room.temperature_c >= 40 || room.smoke_ppm > 150;
            const isWarning = (room.temperature_c >= 35 && room.temperature_c < 40) || (room.co2_ppm > 800);

            return (
              <div 
                key={room.location} 
                className={`relative overflow-hidden bg-slate-950/80 border p-4 rounded transition-all duration-300 ${
                  isDanger 
                    ? 'border-cyber-red shadow-[0_0_12px_rgba(255,0,85,0.25)] animate-pulse' 
                    : isWarning 
                      ? 'border-cyber-amber shadow-[0_0_8px_rgba(255,183,3,0.15)]' 
                      : 'border-slate-800 hover:border-cyber-cyan/50'
                }`}
              >
                {/* Visual danger highlight */}
                {isDanger && (
                  <div className="absolute top-0 right-0 bg-cyber-red text-white text-[9px] px-2 py-0.5 font-mono flex items-center gap-1 animate-pulse">
                    <AlertTriangle className="w-2.5 h-2.5" /> CRITICAL
                  </div>
                )}
                {isWarning && !isDanger && (
                  <div className="absolute top-0 right-0 bg-cyber-amber text-black text-[9px] px-2 py-0.5 font-mono flex items-center gap-1">
                    <AlertTriangle className="w-2.5 h-2.5" /> WARNING
                  </div>
                )}

                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-mono text-sm font-bold text-white tracking-wider">{room.location}</h3>
                    <p className="text-[9px] text-cyber-muted font-mono uppercase">{room.device_id}</p>
                  </div>
                  <div className="text-right font-mono">
                    <span className={`text-[10px] ${room.battery_percent < 20 ? 'text-cyber-red font-bold animate-pulse' : 'text-cyber-green'}`}>
                      🔋 {room.battery_percent}%
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 mb-3">
                  {/* Temp */}
                  <div className="bg-slate-900/60 p-2 border border-slate-800 rounded font-mono text-center">
                    <span className="text-[10px] text-cyber-muted block">TEMP</span>
                    <span className={`text-base font-bold ${
                      room.temperature_c >= 40 ? 'text-cyber-red text-glow-red' : room.temperature_c >= 35 ? 'text-cyber-amber text-glow-amber' : 'text-cyber-cyan text-glow-cyan'
                    }`}>
                      {room.temperature_c.toFixed(1)}°C
                    </span>
                  </div>

                  {/* Humidity */}
                  <div className="bg-slate-900/60 p-2 border border-slate-800 rounded font-mono text-center">
                    <span className="text-[10px] text-cyber-muted block">HUMIDITY</span>
                    <span className="text-base font-bold text-cyber-green text-glow-green">
                      {room.humidity_percent.toFixed(0)}%
                    </span>
                  </div>

                  {/* CO2/Smoke */}
                  <div className="bg-slate-900/60 p-2 border border-slate-800 rounded font-mono text-center">
                    <span className="text-[10px] text-cyber-muted block">CO2</span>
                    <span className="text-base font-bold text-white">
                      {room.co2_ppm}
                    </span>
                  </div>
                </div>

                {/* Smoke value row if elevated */}
                {room.smoke_ppm > 0 && (
                  <div className="flex items-center justify-between text-[11px] font-mono px-2 py-1 mb-2 bg-slate-900 border border-slate-800 rounded">
                    <span className="text-cyber-muted">SMOKE LEVEL:</span>
                    <span className={room.smoke_ppm > 150 ? 'text-cyber-red font-bold' : 'text-cyber-cyan'}>
                      {room.smoke_ppm} ppm
                    </span>
                  </div>
                )}

                {/* SVG trend sparkline */}
                {room.history.length > 1 && (
                  <div className="border-t border-slate-900 pt-2 mt-2">
                    <div className="flex justify-between items-center text-[9px] text-cyber-muted font-mono mb-1">
                      <span>TEMP TREND</span>
                      <span>12 POINTS</span>
                    </div>
                    {renderSparkline(room.history)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
