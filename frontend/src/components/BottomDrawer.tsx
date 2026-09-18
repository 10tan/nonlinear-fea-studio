import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Terminal, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface BottomDrawerProps {
  loadHistory?: number[];
  dispHistory?: number[][];
  complianceHistory?: number[];
  fatigueTime?: number[];
  fatigueBeta?: number[];
  fatiguePf?: number[];
  activeModule: string;
  solverLogs: string[];
}

export const BottomDrawer: React.FC<BottomDrawerProps> = ({
  loadHistory = [],
  dispHistory = [],
  complianceHistory = [],
  fatigueTime = [],
  fatigueBeta = [],
  fatiguePf = [],
  activeModule,
  solverLogs
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState<'chart' | 'logs'>('chart');

  // Format Equilibrium Path data (P vs max_u)
  const eqData = loadHistory.map((load, idx) => {
    const uArr = dispHistory[idx] || [];
    const maxU = uArr.length > 0 ? Math.max(...uArr.map(Math.abs)) : 0;
    return { load: load * 100, disp: (maxU * 1000).toFixed(2) };
  });

  // Format SIMP TopOpt compliance data
  const compData = complianceHistory.map((comp, idx) => ({
    iter: idx + 1,
    compliance: comp.toFixed(2)
  }));

  // Format Fatigue data
  const fatigueData = fatigueTime.map((t, idx) => ({
    year: t.toFixed(1),
    beta: fatigueBeta[idx]?.toFixed(2) ?? 4.0,
    pf: (fatiguePf[idx] ? fatiguePf[idx] * 100 : 0).toFixed(2)
  }));

  return (
    <div style={{
      borderTop: '1px solid var(--border-color)',
      backgroundColor: 'var(--bg-card)',
      transition: 'height 0.25s ease-in-out',
      height: isExpanded ? '220px' : '36px',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 10
    }}>
      {/* Drawer Header Toggle */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          height: '36px',
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: isExpanded ? '1px solid var(--border-color)' : 'none',
          cursor: 'pointer',
          backgroundColor: 'var(--bg-app)',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={(e) => { e.stopPropagation(); setActiveTab('chart'); }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              border: 'none',
              backgroundColor: 'transparent',
              fontSize: '12px',
              fontWeight: 600,
              color: activeTab === 'chart' ? 'var(--accent-primary)' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            <TrendingUp size={14} />
            {activeModule === 'topopt' ? 'SIMP Compliance Curve' : activeModule === 'fatigue' ? 'Fatigue Reliability Trajectory' : 'Equilibrium Path (P-u)'}
          </button>

          <button
            onClick={(e) => { e.stopPropagation(); setActiveTab('logs'); }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              border: 'none',
              backgroundColor: 'transparent',
              fontSize: '12px',
              fontWeight: 600,
              color: activeTab === 'logs' ? 'var(--accent-primary)' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            <Terminal size={14} />
            Solver Log Stream ({solverLogs.length})
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
          {isExpanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </div>
      </div>

      {/* Drawer Content */}
      {isExpanded && (
        <div style={{ flex: 1, padding: '12px 16px', overflow: 'hidden' }}>
          {activeTab === 'chart' ? (
            <div style={{ width: '100%', height: '100%' }}>
              {activeModule === 'topopt' ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={compData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E3E7EC" />
                    <XAxis dataKey="iter" label={{ value: 'Iteration', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis label={{ value: 'Compliance c(ρ)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="compliance" stroke="#1F4E79" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : activeModule === 'fatigue' ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={fatigueData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E3E7EC" />
                    <XAxis dataKey="year" label={{ value: 'Service Years', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis label={{ value: 'Reliability Index β(t)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="beta" stroke="#2E7D32" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={eqData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E3E7EC" />
                    <XAxis dataKey="disp" label={{ value: 'Max Displacement u (mm)', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis label={{ value: 'Load Factor λ (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="load" stroke="#1F4E79" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          ) : (
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              backgroundColor: 'var(--bg-app)',
              padding: '10px',
              borderRadius: 'var(--border-radius)',
              height: '100%',
              overflowY: 'auto',
              color: 'var(--text-primary)',
              lineHeight: 1.6
            }}>
              {solverLogs.length === 0 ? (
                <span style={{ color: 'var(--text-muted)' }}>Ready for solver execution logs...</span>
              ) : (
                solverLogs.map((log, i) => <div key={i}>{log}</div>)
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
