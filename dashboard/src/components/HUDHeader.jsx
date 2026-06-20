import React, { useState, useEffect } from 'react';
import { Cpu, Wifi, Shield, Bell, Database, Activity } from 'lucide-react';

export default function HUDHeader({ stats, serviceStatus }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <header className="relative w-full border-b border-cyber-border bg-slate-950/60 p-4 backdrop-blur-md z-20">
      {/* Laser Sweep Scanline Line on header */}
      <div className="absolute bottom-0 left-0 w-full h-[1px] bg-cyber-cyan animate-pulse shadow-[0_0_8px_#00f0ff]" />

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left Side: System title with futuristic glyphs */}
        <div className="flex items-center gap-3">
          <div className="relative p-2 bg-cyber-cyan/10 border border-cyber-cyan/30 rounded-md">
            <Cpu className="w-6 h-6 text-cyber-cyan animate-pulse" />
            <div className="absolute top-0 right-0 w-2 h-2 bg-cyber-green rounded-full shadow-[0_0_6px_#00ff66]" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold tracking-widest text-white text-glow-cyan font-mono m-0 flex items-center gap-2">
              SMART_CAMPUS <span className="text-xs px-2 py-0.5 border border-cyber-cyan bg-cyber-cyan/10 text-cyber-cyan rounded">v2.1.0</span>
            </h1>
            <p className="text-[10px] text-cyber-muted font-mono tracking-widest uppercase">
              Core Monitoring & Security Intelligence HUD
            </p>
          </div>
        </div>

        {/* Middle: Live Service Health Monitor */}
        <div className="flex flex-wrap items-center gap-4 bg-slate-900/60 border border-slate-800 p-2 rounded px-4 font-mono text-[11px] text-cyber-muted">
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5" />
            <span>INGESTION:</span>
            <span className={`w-2.5 h-2.5 rounded-full ${serviceStatus.ingestion ? 'bg-cyber-green shadow-[0_0_6px_#00ff66]' : 'bg-cyber-red animate-pulse shadow-[0_0_6px_#ff0055]'}`} />
          </div>
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" />
            <span>VISION:</span>
            <span className={`w-2.5 h-2.5 rounded-full ${serviceStatus.ai_vision ? 'bg-cyber-green shadow-[0_0_6px_#00ff66]' : 'bg-cyber-red animate-pulse shadow-[0_0_6px_#ff0055]'}`} />
          </div>
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            <span>GATE:</span>
            <span className={`w-2.5 h-2.5 rounded-full ${serviceStatus.access_gate ? 'bg-cyber-green shadow-[0_0_6px_#00ff66]' : 'bg-cyber-red animate-pulse shadow-[0_0_6px_#ff0055]'}`} />
          </div>
          <div className="flex items-center gap-1.5">
            <Wifi className="w-3.5 h-3.5" />
            <span>ANALYTICS:</span>
            <span className={`w-2.5 h-2.5 rounded-full ${serviceStatus.analytics ? 'bg-cyber-green shadow-[0_0_6px_#00ff66]' : 'bg-cyber-red animate-pulse shadow-[0_0_6px_#ff0055]'}`} />
          </div>
          <div className="flex items-center gap-1.5">
            <Bell className="w-3.5 h-3.5" />
            <span>NOTIF:</span>
            <span className={`w-2.5 h-2.5 rounded-full ${serviceStatus.notification ? 'bg-cyber-green shadow-[0_0_6px_#00ff66]' : 'bg-cyber-red animate-pulse shadow-[0_0_6px_#ff0055]'}`} />
          </div>
        </div>

        {/* Right Side: Live Clock & Date */}
        <div className="flex items-center gap-4 text-right">
          <div className="hidden lg:block font-mono text-[10px] text-cyber-muted tracking-wider">
            <div>UTC / SECURE LAYER ACTIVE</div>
            <div className="text-cyber-green">SYS_OK // ONLINE</div>
          </div>
          <div className="border-l border-cyber-border pl-4 font-mono">
            <div className="text-xl font-bold text-cyber-cyan text-glow-cyan tracking-widest">{formatTime(time)}</div>
            <div className="text-[10px] text-cyber-muted uppercase tracking-wider">{formatDate(time)}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
