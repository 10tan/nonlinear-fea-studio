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

    const width = mountRef.current.clientWidth || 800;
    const height = mountRef.current.clientHeight || 500;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#EEF1F4');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(1.0, 0.6, 2.8);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

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
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.75);
    dirLight1.position.set(5, 10, 7);
    scene.add(dirLight1);
    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.35);
    dirLight2.position.set(-5, -5, -5);
    scene.add(dirLight2);

    // Grid Plane
    const grid = new THREE.GridHelper(6, 30, 0x1F4E79, 0xCBD5E1);
    grid.position.set(1.0, -0.05, 0);
    scene.add(grid);

    // Select active step displacement
    const activeDisp = dispHistory.length > 0 && currentStep < dispHistory.length 
      ? dispHistory[currentStep] 
      : (displacements || []);

    if (nodes && nodes.length > 0 && elements && elements.length > 0) {
      // Calculate deformed nodal coordinates
      const currentNodes = nodes.map((node, i) => {
        if (showDeformed && activeDisp && activeDisp.length >= (i + 1) * 2) {
          const dx = (activeDisp[i * 2] || 0) * dispScale;
          const dy = (activeDisp[i * 2 + 1] || 0) * dispScale;
          return [node[0] + dx, node[1] + dy, 0];
        }
        return [node[0], node[1], 0];
      });

      // Max stress calculation for normalized heatmap
      let maxSig = 1.0;
      if (stresses && stresses.length > 0) {
        maxSig = Math.max(...stresses.map(s => Math.hypot(s[0], s[1]) + 1e-6));
        setMaxStressVal(Math.round(maxSig / 1e6));
      }

      // Non-indexed triangle buffer for 100% reliable 1:1 vertex-color alignment
      const triPositions: number[] = [];
      const triColors: number[] = [];
      const linePositions: number[] = [];

      elements.forEach((elem, eIdx) => {
        if (elem.length < 4) return;
        const n0 = elem[0], n1 = elem[1], n2 = elem[2], n3 = elem[3];
        const p0 = currentNodes[n0], p1 = currentNodes[n1], p2 = currentNodes[n2], p3 = currentNodes[n3];
        if (!p0 || !p1 || !p2 || !p3) return;

        // Determine color for element
        let r = 0.12, g = 0.3, b = 0.47;

        if (activeModule === 'topopt' && densities && densities.length > 0) {
          const row = Math.floor(eIdx / (densities[0]?.length || 1));
          const col = eIdx % (densities[0]?.length || 1);
          const rho = densities[row]?.[col] ?? 0.5;
          r = 0.95 - rho * 0.8;
          g = 0.95 - rho * 0.75;
          b = 0.95 - rho * 0.4;
        } else if (colormapMode === 'displacement' && activeDisp.length > 0) {
          const mag = Math.hypot(activeDisp[n0 * 2] || 0, activeDisp[n0 * 2 + 1] || 0) * dispScale;
          const val = Math.min(1.0, mag / 0.15);
          r = val;
          g = 0.4 * val;
          b = 1.0 - val;
        } else if (stresses && stresses[eIdx]) {
          const vm = Math.hypot(stresses[eIdx][0], stresses[eIdx][1]) / maxSig;
          r = Math.min(1.0, Math.max(0.0, 2.0 * vm - 0.5));
          g = Math.min(1.0, Math.max(0.0, 1.5 - Math.abs(2.0 * vm - 1.0)));
          b = Math.min(1.0, Math.max(0.0, 1.5 - 2.0 * vm));
        }

        // Triangles (p0, p1, p2) and (p0, p2, p3)
        const quadVertices = [p0, p1, p2, p0, p2, p3];
        quadVertices.forEach(v => {
          triPositions.push(v[0], v[1], v[2]);
          triColors.push(r, g, b);
        });

        // Wireframe edges (p0-p1, p1-p2, p2-p3, p3-p0)
        const edges = [[p0, p1], [p1, p2], [p2, p3], [p3, p0]];
        edges.forEach(([ea, eb]) => {
          linePositions.push(ea[0], ea[1], ea[2], eb[0], eb[1], eb[2]);
        });
      });

      // Create Solid Mesh
      const meshGeom = new THREE.BufferGeometry();
      meshGeom.setAttribute('position', new THREE.Float32BufferAttribute(triPositions, 3));
      meshGeom.setAttribute('color', new THREE.Float32BufferAttribute(triColors, 3));
      meshGeom.computeVertexNormals();

      const meshMat = new THREE.MeshStandardMaterial({
        vertexColors: true,
        side: THREE.DoubleSide,
        roughness: 0.35,
        metalness: 0.15
      });
      const mesh = new THREE.Mesh(meshGeom, meshMat);
      scene.add(mesh);

      // Create Wireframe Line Segments
      const lineGeom = new THREE.BufferGeometry();
      lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
      const lineMat = new THREE.LineBasicMaterial({ color: 0x1A1A1A, transparent: true, opacity: 0.35 });
      const wireframeLines = new THREE.LineSegments(lineGeom, lineMat);
      scene.add(wireframeLines);

      // Support BC cones at x=0
      nodes.forEach(pt => {
        if (pt[0] === 0) {
          const pinGeom = new THREE.ConeGeometry(0.035, 0.07, 8);
          const pinMat = new THREE.MeshStandardMaterial({ color: 0xD32F2F, roughness: 0.2 });
          const pinMesh = new THREE.Mesh(pinGeom, pinMat);
          pinMesh.position.set(pt[0] - 0.04, pt[1], 0);
          pinMesh.rotation.z = -Math.PI / 2;
          scene.add(pinMesh);
        }
      });

      // Load arrow indicator
      const maxNodeX = Math.max(...currentNodes.map(n => n[0]));
      const loadNodes = currentNodes.filter(n => n[0] === maxNodeX);
      loadNodes.forEach(pt => {
        const arrowDir = new THREE.Vector3(0, -1, 0);
        const arrowOrigin = new THREE.Vector3(pt[0], pt[1] + 0.25, 0);
        const arrowHelper = new THREE.ArrowHelper(arrowDir, arrowOrigin, 0.2, 0x1F4E79, 0.06, 0.04);
        scene.add(arrowHelper);
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
      cameraRef.current.position.set(1.0, 0.6, 2.8);
      controlsRef.current.target.set(1.0, 0.2, 0);
      controlsRef.current.update();
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
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
        backdropFilter: 'blur(4px)',
        zIndex: 5
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
        gap: '6px',
        zIndex: 5
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
          backdropFilter: 'blur(6px)',
          zIndex: 5
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
