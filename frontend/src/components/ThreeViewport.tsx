import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Play, Pause, RotateCcw } from 'lucide-react';

interface ThreeViewportProps {
  nodes: number[][];
  elements: number[][];
  displacements?: number[];
  stresses?: number[][];
  densities?: number[][];
  dispScale?: number;
  showDeformed?: boolean;
  activeModule?: string;
  loadHistory?: number[];
  dispHistory?: number[][];
}

export const ThreeViewport: React.FC<ThreeViewportProps> = ({
  nodes,
  elements,
  displacements,
  stresses,
  densities,
  dispScale = 10.0,
  showDeformed = true,
  activeModule = 'static',
  loadHistory = [],
  dispHistory = []
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  // Animation timeline state
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [colormapMode, setColormapMode] = useState<'stress' | 'displacement' | 'density'>('stress');
  const [maxStressVal, setMaxStressVal] = useState<number>(150);

  const totalSteps = dispHistory.length > 0 ? dispHistory.length : 1;

  // Auto-play step animation
  useEffect(() => {
    let interval: any;
    if (isPlaying && totalSteps > 1) {
      interval = setInterval(() => {
        setCurrentStep(prev => (prev + 1) % totalSteps);
      }, 150);
    }
    return () => clearInterval(interval);
  }, [isPlaying, totalSteps]);

  // Render Three.js Scene
  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#EEF1F4');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(1.0, 0.8, 3.0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Clear previous canvas
    while (mountRef.current.firstChild) {
      mountRef.current.removeChild(mountRef.current.firstChild);
    }
    mountRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(1.0, 0.2, 0);
    controlsRef.current = controls;

    // Ambient & Directional Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.7);
    dirLight1.position.set(5, 10, 7);
    scene.add(dirLight1);
    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
    dirLight2.position.set(-5, -5, -5);
    scene.add(dirLight2);

    // Grid Plane
    const grid = new THREE.GridHelper(5, 25, 0x1F4E79, 0xCBD5E1);
    grid.position.set(1.0, -0.05, 0);
    scene.add(grid);

    // Select active step displacement
    const activeDisp = dispHistory.length > 0 && currentStep < dispHistory.length 
      ? dispHistory[currentStep] 
      : (displacements || []);

    if (nodes && nodes.length > 0 && elements && elements.length > 0) {
      const geom = new THREE.BufferGeometry();
      const vertices: number[] = [];
      const colors: number[] = [];
      const indices: number[] = [];

      // Nodal positions incorporating scaled deformation
      const currentNodes = nodes.map((node, i) => {
        if (showDeformed && activeDisp && activeDisp.length >= (i + 1) * 2) {
          const dx = activeDisp[i * 2] * dispScale;
          const dy = activeDisp[i * 2 + 1] * dispScale;
          return [node[0] + dx, node[1] + dy, 0];
        }
        return [node[0], node[1], 0];
      });

      currentNodes.forEach(pt => {
        vertices.push(pt[0], pt[1], pt[2]);
      });

      // Max stress calculation for normalized heatmap
      let maxSig = 1.0;
      if (stresses && stresses.length > 0) {
        maxSig = Math.max(...stresses.map(s => Math.hypot(s[0], s[1]) + 1e-6));
        setMaxStressVal(Math.round(maxSig / 1e6));
      }

      elements.forEach((elem, eIdx) => {
        if (elem.length >= 4) {
          indices.push(elem[0], elem[1], elem[2]);
          indices.push(elem[0], elem[2], elem[3]);
        }

        let r = 0.12, g = 0.3, b = 0.47;

        if (activeModule === 'topopt' && densities && densities.length > 0) {
          const row = Math.floor(eIdx / (densities[0]?.length || 1));
          const col = eIdx % (densities[0]?.length || 1);
          const rho = densities[row]?.[col] ?? 0.5;
          r = 0.95 - rho * 0.8;
          g = 0.95 - rho * 0.75;
          b = 0.95 - rho * 0.4;
        } else if (colormapMode === 'displacement' && activeDisp.length > 0) {
          // Displacement heatmap
          const n0 = elem[0];
          const mag = Math.hypot(activeDisp[n0 * 2] || 0, activeDisp[n0 * 2 + 1] || 0) * dispScale;
          const val = Math.min(1.0, mag / 0.2);
          r = val;
          g = 0.5 * val;
          b = 1.0 - val;
        } else if (stresses && stresses[eIdx]) {
          // Von Mises stress Jet colormap
          const vm = Math.hypot(stresses[eIdx][0], stresses[eIdx][1]) / maxSig;
          r = Math.min(1.0, Math.max(0.0, 2.0 * vm - 0.5));
          g = Math.min(1.0, Math.max(0.0, 1.5 - Math.abs(2.0 * vm - 1.0)));
          b = Math.min(1.0, Math.max(0.0, 1.5 - 2.0 * vm));
        }

        elem.forEach(() => colors.push(r, g, b));
      });

      geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      geom.setIndex(indices);
      geom.computeVertexNormals();

      const mat = new THREE.MeshStandardMaterial({
        vertexColors: true,
        side: THREE.DoubleSide,
        roughness: 0.3,
        metalness: 0.1
      });

      const mesh = new THREE.Mesh(geom, mat);
      scene.add(mesh);

      // High-contrast CAD wireframe
      const wireMat = new THREE.MeshBasicMaterial({ color: 0x1A1A1A, wireframe: true, transparent: true, opacity: 0.3 });
      const wireMesh = new THREE.Mesh(geom, wireMat);
      scene.add(wireMesh);

      // Support BC visualization (Fixed pins at x=0)
      nodes.forEach((pt) => {
        if (pt[0] === 0) {
          const pinGeom = new THREE.ConeGeometry(0.04, 0.08, 6);
          const pinMat = new THREE.MeshBasicMaterial({ color: 0xD32F2F });
          const pinMesh = new THREE.Mesh(pinGeom, pinMat);
          pinMesh.position.set(pt[0] - 0.04, pt[1], 0);
          pinMesh.rotation.z = -Math.PI / 2;
          scene.add(pinMesh);
        }
      });
    }

    // Animation Render Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
    };
  }, [nodes, elements, displacements, stresses, densities, dispScale, showDeformed, activeModule, currentStep, dispHistory, colormapMode]);

  // Reset Camera View
  const resetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(1.0, 0.8, 3.0);
      controlsRef.current.target.set(1.0, 0.2, 0);
      controlsRef.current.update();
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* 3D Canvas Container */}
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating CAD Overlay Tools */}
      <div style={{
        position: 'absolute',
        top: '14px',
        left: '14px',
        display: 'flex',
        gap: '6px',
        backgroundColor: 'rgba(255,255,255,0.92)',
        padding: '4px',
        borderRadius: 'var(--border-radius)',
        border: '1px solid var(--border-color)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        backdropFilter: 'blur(4px)'
      }}>
        <button
          onClick={() => setColormapMode('stress')}
          style={{
            padding: '5px 10px',
            fontSize: '11px',
            fontWeight: 600,
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            backgroundColor: colormapMode === 'stress' ? 'var(--accent-primary)' : 'transparent',
            color: colormapMode === 'stress' ? '#FFF' : 'var(--text-secondary)'
          }}
        >
          Von Mises Stress
        </button>

        <button
          onClick={() => setColormapMode('displacement')}
          style={{
            padding: '5px 10px',
            fontSize: '11px',
            fontWeight: 600,
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            backgroundColor: colormapMode === 'displacement' ? 'var(--accent-primary)' : 'transparent',
            color: colormapMode === 'displacement' ? '#FFF' : 'var(--text-secondary)'
          }}
        >
          Displacement Field
        </button>

        <button
          onClick={resetCamera}
          title="Reset Camera View"
          style={{
            padding: '5px 8px',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            backgroundColor: 'transparent',
            color: 'var(--text-secondary)'
          }}
        >
          <RotateCcw size={14} />
        </button>
      </div>

      {/* Interactive Stress Heatmap Colorbar Legend */}
      <div style={{
        position: 'absolute',
        top: '14px',
        right: '14px',
        backgroundColor: 'rgba(255,255,255,0.92)',
        padding: '10px 12px',
        borderRadius: 'var(--border-radius)',
        border: '1px solid var(--border-color)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        fontSize: '11px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px'
      }}>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {colormapMode === 'stress' ? 'Von Mises Stress (MPa)' : colormapMode === 'displacement' ? 'Displacement Mag (mm)' : 'Density ρ'}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>0</span>
          <div style={{
            width: '120px',
            height: '12px',
            borderRadius: '2px',
            background: colormapMode === 'displacement' 
              ? 'linear-gradient(to right, #0000FF, #7F007F, #FF0000)'
              : 'linear-gradient(to right, #0000FF, #00FFFF, #00FF00, #FFFF00, #FF0000)'
          }} />
          <span>{maxStressVal}</span>
        </div>
      </div>

      {/* Interactive Step Animation Player Bar */}
      {totalSteps > 1 && (
        <div style={{
          position: 'absolute',
          bottom: '14px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(255,255,255,0.95)',
          padding: '6px 16px',
          borderRadius: '24px',
          border: '1px solid var(--border-color)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backdropFilter: 'blur(6px)'
        }}>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              border: 'none',
              backgroundColor: 'var(--accent-primary)',
              color: '#FFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} style={{ marginLeft: '2px' }} />}
          </button>

          <span style={{ fontSize: '12px', fontWeight: 600, minWidth: '75px', color: 'var(--text-primary)' }}>
            Step {currentStep + 1} / {totalSteps}
          </span>

          <input
            type="range"
            min="0"
            max={totalSteps - 1}
            value={currentStep}
            onChange={(e) => {
              setIsPlaying(false);
              setCurrentStep(parseInt(e.target.value));
            }}
            style={{ width: '180px', cursor: 'pointer' }}
          />

          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Load: {loadHistory[currentStep] ? (loadHistory[currentStep] * 100).toFixed(0) : 100}%
          </span>
        </div>
      )}
    </div>
  );
};
