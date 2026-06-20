import React from 'react';
import { Bell, AlertCircle, AlertOctagon, Mail, MessageSquare } from 'lucide-react';

export default function AlertCenterPanel({ alertLogs }) {
  const alerts = alertLogs.items || [];

  const getSeverityStyle = (severity) => {
    switch (String(severity).toUpperCase()) {
      case 'CRITICAL':
        return {
          bg: 'bg-cyber-red/10 border-cyber-red/40 hover:border-cyber-red text-cyber-red',
          tag: 'border-cyber-red bg-cyber-red text-white text-glow-red animate-pulse-fast',
          label: 'CRITICAL',
          icon: <AlertOctagon className="w-5 h-5 text-cyber-red animate-bounce" />
        };
      case 'HIGH':
        return {
          bg: 'bg-cyber-amber/10 border-cyber-amber/30 hover:border-cyber-amber text-cyber-amber',
          tag: 'border-cyber-amber bg-cyber-amber/20 text-cyber-amber text-glow-amber',
          label: 'HIGH ALERT',
          icon: <AlertCircle className="w-5 h-5 text-cyber-amber" />
        };
      case 'MEDIUM':
        return {
          bg: 'bg-slate-900/60 border-slate-800 hover:border-cyber-cyan/50 text-white',
          tag: 'border-cyber-cyan bg-cyber-cyan/10 text-cyber-cyan text-glow-cyan',
          label: 'MEDIUM',
          icon: <Bell className="w-5 h-5 text-cyber-cyan" />
        };
      default:
        return {
          bg: 'bg-slate-900/40 border-slate-900 hover:border-slate-800 text-cyber-muted',
          tag: 'border-slate-800 bg-slate-900 text-cyber-muted',
          label: 'LOW',
          icon: <Bell className="w-4 h-4 text-cyber-muted" />
        };
    }
  };

  return (
    <div className="cyber-panel border border-cyber-border rounded p-4 cyber-corners flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-cyber-border pb-2 mb-4 font-mono">
        <h2 className="text-sm font-bold text-cyber-cyan tracking-wider flex items-center gap-2 m-0">
          <Bell className="w-4 h-4 text-cyber-cyan animate-pulse" />
          INCIDENT_NOTIFICATION_CENTER
        </h2>
        <span className="text-[10px] text-cyber-muted uppercase">ALERTS // HISTORY</span>
      </div>

      {/* Main Alerts List */}
      <div className="flex-1 overflow-y-auto max-h-[300px] pr-1">
        {alerts.length === 0 ? (
          <div className="py-12 text-center text-cyber-muted font-mono text-xs">
            [NO_ACTIVE_INCIDENTS_REPORTED]
            <p className="text-[10px] mt-1">Status secure. Alert routing tables fully active.</p>
          </div>
        ) : (
          <div className="space-y-3 font-mono">
            {alerts.map((alert, index) => {
              const style = getSeverityStyle(alert.severity);
              const channels = alert.channels || {};
              const timestamp = alert.timestamp || alert.at || '';

              return (
                <div 
                  key={alert.alert_id || index} 
                  className={`border p-3 rounded transition-all duration-300 flex flex-col gap-2 ${style.bg}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      {style.icon}
                      <div>
                        {/* Title line */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-[9px] px-1.5 py-0.5 rounded border font-bold uppercase tracking-wider ${style.tag}`}>
                            {style.label}
                          </span>
                          <span className="text-xs font-bold text-white uppercase">
                            {String(alert.alert_type).replace(/_/g, ' ')}
                          </span>
                        </div>
                        {/* Details Message */}
                        <p className="text-xs mt-1 text-slate-300 leading-relaxed font-sans">
                          {alert.message}
                        </p>
                      </div>
                    </div>

                    <div className="text-[9px] text-cyber-muted whitespace-nowrap">
                      {timestamp ? new Date(timestamp).toLocaleTimeString('en-US', { hour12: false }) : ''}
                    </div>
                  </div>

                  {/* Dispatch Channel Badges */}
                  <div className="flex items-center gap-3 border-t border-slate-900/60 pt-2 mt-1 text-[10px]">
                    <span className="text-cyber-muted text-[9px] uppercase tracking-wider">ROUTING:</span>
                    
                    {/* Telegram channel status */}
                    {channels.telegram !== undefined && (
                      <span className={`flex items-center gap-1 px-1.5 py-0.5 rounded border ${
                        channels.telegram?.success || channels.telegram === 'sent' || channels.telegram === true
                          ? 'border-cyber-green/40 bg-cyber-green/10 text-cyber-green'
                          : 'border-cyber-red/40 bg-cyber-red/10 text-cyber-red'
                      }`}>
                        <MessageSquare className="w-3 h-3" />
                        TELEGRAM
                        <span className="text-[8px] font-bold">
                          {channels.telegram?.success || channels.telegram === 'sent' || channels.telegram === true ? '[OK]' : '[ERR]'}
                        </span>
                      </span>
                    )}

                    {/* Email channel status */}
                    {channels.email !== undefined && (
                      <span className={`flex items-center gap-1 px-1.5 py-0.5 rounded border ${
                        channels.email?.success || channels.email === 'sent' || channels.email === true
                          ? 'border-cyber-green/40 bg-cyber-green/10 text-cyber-green'
                          : 'border-cyber-red/40 bg-cyber-red/10 text-cyber-red'
                      }`}>
                        <Mail className="w-3 h-3" />
                        EMAIL
                        <span className="text-[8px] font-bold">
                          {channels.email?.success || channels.email === 'sent' || channels.email === true ? '[OK]' : '[ERR]'}
                        </span>
                      </span>
                    )}

                    {/* Console log channel fallback */}
                    {channels.console !== undefined && (
                      <span className="flex items-center gap-1 px-1.5 py-0.5 rounded border border-slate-800 bg-slate-900 text-cyber-muted">
                        CONSOLE_LOG [OK]
                      </span>
                    )}
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
