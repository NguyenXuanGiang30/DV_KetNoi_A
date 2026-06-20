import React from 'react';
import { Shield, ShieldAlert, ShieldCheck, UserCheck, Eye, Key } from 'lucide-react';

export default function AccessControlPanel({ accessLogs }) {
  const logs = accessLogs.items || [];

  return (
    <div className="cyber-panel border border-cyber-border rounded p-4 cyber-corners flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-cyber-border pb-2 mb-4 font-mono">
        <h2 className="text-sm font-bold text-cyber-cyan tracking-wider flex items-center gap-2 m-0">
          <Shield className="w-4 h-4 text-cyber-cyan animate-pulse" />
          SECURE_GATE_CONTROLLER
        </h2>
        <span className="text-[10px] text-cyber-muted uppercase">LIVE // MONITOR</span>
      </div>

      {/* Laser Scanning Simulator Visual HUD */}
      <div className="relative w-full h-32 bg-slate-950/80 border border-slate-900 rounded overflow-hidden mb-4 flex items-center justify-center font-mono">
        <div className="absolute left-0 w-full h-[2px] bg-cyber-cyan shadow-[0_0_12px_#00f0ff] animate-laser" />
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#00f0ff_1px,transparent_1px)] [background-size:16px_16px]" />
        
        <div className="text-center z-10 p-4">
          <div className="text-xs text-cyber-cyan text-glow-cyan animate-pulse tracking-widest font-bold mb-1">
            GATE SCANNER READY
          </div>
          <div className="text-[9px] text-cyber-muted">
            LOCATIONS: MAIN_GATE_A, LAB_GATE_B, LIBRARY_GATE_C
          </div>
          <div className="mt-2 text-[10px] text-cyber-green flex items-center justify-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5 animate-bounce" />
            <span>AI FACE RECOGNITION SYSTEM ONLINE</span>
          </div>
        </div>
      </div>

      {/* Logs Table / List */}
      <div className="flex-1 overflow-y-auto max-h-[300px] pr-1">
        {logs.length === 0 ? (
          <div className="py-12 text-center text-cyber-muted font-mono text-xs">
            [NO_ACCESS_LOGS_AVAILABLE]
            <p className="text-[10px] mt-1">Logs will appear automatically upon card swipes.</p>
          </div>
        ) : (
          <div className="space-y-3 font-mono">
            {logs.map((log, index) => {
              const granted = log.action === 'grant' || log.action === 'GRANTED' || String(log.decision).toUpperCase() === 'GRANT' || String(log.decision).toUpperCase() === 'GRANTED' || log.status === 'granted';
              
              // Handle multiple schemas gracefully
              const name = log.student_name || log.name || log.student_id || 'UNKNOWN';
              const cardUid = log.card_uid || log.uid || 'N/A';
              const gateId = log.gate_id || log.gate || 'GATE_01';
              const timeString = log.timestamp || log.at || '';
              const faceMatched = log.face_matched ?? log.ai_face_matched ?? false;

              return (
                <div 
                  key={log.id || index} 
                  className={`border p-3 rounded bg-slate-950/60 flex items-center justify-between gap-4 transition-all duration-300 ${
                    granted 
                      ? 'border-slate-800 hover:border-cyber-green/50' 
                      : 'border-cyber-red/40 hover:border-cyber-red bg-cyber-red/5'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {/* User Icon Badge */}
                    <div className={`p-2 border rounded ${
                      granted 
                        ? 'bg-cyber-green/10 border-cyber-green/30 text-cyber-green' 
                        : 'bg-cyber-red/10 border-cyber-red/30 text-cyber-red'
                    }`}>
                      {granted ? <ShieldCheck className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5 animate-pulse" />}
                    </div>

                    <div>
                      {/* Name & Title */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{name}</span>
                        {faceMatched && (
                          <span className="text-[8px] bg-cyber-cyan/10 border border-cyber-cyan text-cyber-cyan px-1 rounded flex items-center gap-0.5">
                            <Eye className="w-2.5 h-2.5" /> FACE_OK
                          </span>
                        )}
                      </div>

                      {/* Card details & location */}
                      <div className="text-[10px] text-cyber-muted mt-0.5 flex flex-wrap gap-x-2">
                        <span className="flex items-center gap-0.5"><Key className="w-2.5 h-2.5" /> {cardUid}</span>
                        <span>•</span>
                        <span>{gateId.toUpperCase()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Indicator */}
                  <div className="text-right">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded border ${
                      granted 
                        ? 'border-cyber-green bg-cyber-green/10 text-cyber-green text-glow-green' 
                        : 'border-cyber-red bg-cyber-red/10 text-cyber-red text-glow-red animate-pulse'
                    }`}>
                      {granted ? 'GRANTED' : 'DENIED'}
                    </span>
                    <div className="text-[9px] text-cyber-muted mt-1">
                      {timeString ? new Date(timeString).toLocaleTimeString('en-US', { hour12: false }) : ''}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
