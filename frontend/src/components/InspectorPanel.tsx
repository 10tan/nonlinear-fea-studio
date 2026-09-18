import React from 'react';
import { Sliders } from 'lucide-react';

interface InspectorPanelProps {
  E: number;
  setE: (v: number) => void;
  nu: number;
  setNu: (v: number) => void;
  yieldSig: number;
  setYieldSig: (v: number) => void;
  loadMag: number;
  setLoadMag: (v: number) => void;
  volfrac: number;
  setVolfrac: (v: number) => void;
  dispScale: number;
  setDispScale: (v: number) => void;
  showDeformed: boolean;
  setShowDeformed: (b: boolean) => void;
  activeModule: string;
}

export const InspectorPanel: React.FC<InspectorPanelProps> = ({
  E, setE,
  nu, setNu,
  yieldSig, setYieldSig,
  loadMag, setLoadMag,
  volfrac, setVolfrac,
  dispScale, setDispScale,
  showDeformed, setShowDeformed,
  activeModule
}) => {
  return (
    <aside style={{
      width: '280px',
      backgroundColor: 'var(--bg-card)',
      borderLeft: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      padding: '14px',
      gap: '16px',
      overflowY: 'auto'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
        <Sliders size={16} color="var(--accent-primary)" />
        <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Inspector & Settings
        </h3>
      </div>

      {/* Material Properties */}
      <div>
        <h4 style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Material Parameters
        </h4>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span>Young's Modulus E (GPa)</span>
              <span>{(E / 1e9).toFixed(1)}</span>
            </label>
            <input
              type="range"
              min="10"
              max="400"
              value={E / 1e9}
              onChange={(e) => setE(parseFloat(e.target.value) * 1e9)}
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span>Poisson Ratio ν</span>
              <span>{nu.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="0.1"
              max="0.48"
              step="0.01"
              value={nu}
              onChange={(e) => setNu(parseFloat(e.target.value))}
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>

          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span>Yield Stress σy (MPa)</span>
              <span>{(yieldSig / 1e6).toFixed(0)}</span>
            </label>
            <input
              type="range"
              min="50"
              max="1000"
              value={yieldSig / 1e6}
              onChange={(e) => setYieldSig(parseFloat(e.target.value) * 1e6)}
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>
        </div>
      </div>

      {/* Loading & TopOpt Controls */}
      <div>
        <h4 style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
          {activeModule === 'topopt' ? 'SIMP Optimization Parameters' : 'Applied Loading'}
        </h4>

        {activeModule === 'topopt' ? (
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <span>Target Volume Fraction V_max</span>
              <span>{volfrac.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="0.1"
              max="0.8"
              step="0.05"
              value={volfrac}
              onChange={(e) => setVolfrac(parseFloat(e.target.value))}
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>
        ) : (
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <span>Prescribed Load (kN)</span>
              <span>{(loadMag / 1000).toFixed(1)}</span>
            </label>
            <input
              type="range"
              min="5"
              max="500"
              value={loadMag / 1000}
              onChange={(e) => setLoadMag(parseFloat(e.target.value) * 1000)}
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>
        )}
      </div>

      {/* Viewport Visualization Controls */}
      <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
        <h4 style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Viewport Display
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: 'var(--text-primary)' }}>
            <input
              type="checkbox"
              checked={showDeformed}
              onChange={(e) => setShowDeformed(e.target.checked)}
            />
            <span>Show Deformed Mesh</span>
          </label>

          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span>Deformation Magnification</span>
              <span>{dispScale.toFixed(1)}x</span>
            </label>
            <input
              type="range"
              min="0.1"
              max="50"
              step="0.5"
              value={dispScale}
              onChange={(e) => setDispScale(parseFloat(e.target.value))}
              style={{ width: '100%', marginTop: '4px' }}
            />
          </div>
        </div>
      </div>
    </aside>
  );
};
