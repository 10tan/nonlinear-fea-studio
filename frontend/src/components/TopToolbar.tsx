import React from 'react';
import { Play, Activity, Layers, Cpu, RefreshCw, Box, ShieldCheck } from 'lucide-react';

interface TopToolbarProps {
  onSolve: (type: string) => void;
  activeModule: string;
  setActiveModule: (m: string) => void;
  isSolving: boolean;
  onReset: () => void;
}

export const TopToolbar: React.FC<TopToolbarProps> = ({
  onSolve,
  activeModule,
  setActiveModule,
  isSolving,
  onReset
}) => {
  return (
    <header style={{
      height: '52px',
      backgroundColor: 'var(--bg-card)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.02)'
    }}>
      {/* Brand & Project Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: 'var(--border-radius)',
          backgroundColor: 'var(--accent-primary)',
          color: '#FFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
          fontSize: '14px'
        }}>
          FEA
        </div>
        <div>
          <h1 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
            Nonlinear FEA Studio
          </h1>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Multiscale Computational Structural Mechanics Platform
          </p>
        </div>
      </div>

      {/* Module Selector Tabs */}
      <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-app)', padding: '3px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
        {[
          { id: 'static', label: 'Newton-Raphson', icon: Play },
          { id: 'arc_length', label: 'Arc-Length Snap', icon: Activity },
          { id: 'topopt', label: 'SIMP Topology', icon: Layers },
          { id: 'homog', label: 'FE² Homogenization', icon: Box },
          { id: 'fatigue', label: 'Rainflow Fatigue', icon: ShieldCheck }
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeModule === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveModule(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                backgroundColor: isActive ? 'var(--bg-card)' : 'transparent',
                color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                boxShadow: isActive ? '0 1px 2px rgba(0,0,0,0.05)' : 'none'
              }}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <button
          onClick={onReset}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: 'var(--border-radius)',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '13px',
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={14} />
          Reset
        </button>

        <button
          onClick={() => onSolve(activeModule)}
          disabled={isSolving}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 16px',
            borderRadius: 'var(--border-radius)',
            border: 'none',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFF',
            fontSize: '13px',
            fontWeight: 600,
            cursor: isSolving ? 'not-allowed' : 'pointer',
            opacity: isSolving ? 0.7 : 1
          }}
        >
          <Cpu size={14} />
          {isSolving ? 'Solving...' : 'Run Simulation'}
        </button>
      </div>
    </header>
  );
};
