import React from 'react';
import { Network, Database, Shield, Zap, Circle } from 'lucide-react';

interface ModelTreeProps {
  numNodes: number;
  numElements: number;
  materialName: string;
  activeModule: string;
  presetScenario: string;
  setPresetScenario: (s: string) => void;
}

export const ModelTree: React.FC<ModelTreeProps> = ({
  numNodes,
  numElements,
  materialName,
  activeModule,
  presetScenario,
  setPresetScenario
}) => {
  return (
    <aside style={{
      width: '240px',
      backgroundColor: 'var(--bg-card)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      padding: '14px',
      gap: '16px',
      overflowY: 'auto'
    }}>
      <div>
        <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
          Preset Benchmark Case
        </h3>
        <select
          value={presetScenario}
          onChange={(e) => setPresetScenario(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 10px',
            borderRadius: 'var(--border-radius)',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-app)',
            fontSize: '12px',
            color: 'var(--text-primary)',
            outline: 'none'
          }}
        >
          <option value="cantilever">Cantilever Beam (Plane Stress)</option>
          <option value="arch_snap">Shallow Arch (Snap-Through)</option>
          <option value="topopt_bridge">MBB Bridge (SIMP TopOpt)</option>
          <option value="rve_composite">Fiber RVE (FE² Homogenization)</option>
        </select>
      </div>

      <div>
        <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
          Model Hierarchy
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
            <Network size={15} color="var(--accent-primary)" />
            <span>Nodal Mesh ({numNodes} nodes)</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
            <Database size={15} color="var(--accent-primary)" />
            <span>Quad Elements ({numElements} Q4)</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
            <Shield size={15} color="var(--accent-primary)" />
            <span>Material: {materialName}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
            <Zap size={15} color="var(--accent-primary)" />
            <span>Module: {activeModule.toUpperCase()}</span>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--color-success)' }}>
          <Circle size={8} fill="var(--color-success)" />
          <span>Core Solver Ready</span>
        </div>
      </div>
    </aside>
  );
};
