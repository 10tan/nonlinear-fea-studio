import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

interface ThreeViewportProps {
  nodes: number[][];
  elements: number[][];
  displacements?: number[];
  stresses?: number[][];
  densities?: number[][];
  dispScale?: number;
  showDeformed?: boolean;
  colormap?: 'stress' | 'damage' | 'density';
  activeModule?: string;
}

export const ThreeViewport: React.FC<ThreeViewportProps> = ({
  nodes,
  elements,
  displacements,
  stresses,
  densities,
  dispScale = 1.0,
  showDeformed = true,
  colormap = 'stress',
  activeModule = 'static'
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#EEF1F4');
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0.5, 0.5, 2.5);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // Grid helper
    const grid = new THREE.GridHelper(4, 20, 0x1F4E79, 0xCBD5E1);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -0.01;
    scene.add(grid);

    // Render mesh geometry
    if (nodes && nodes.length > 0 && elements && elements.length > 0) {
      const geom = new THREE.BufferGeometry();
      const vertices: number[] = [];
      const colors: number[] = [];
      const indices: number[] = [];

      // Calculate deformed nodal coordinates
      const currentNodes = nodes.map((node, i) => {
        if (showDeformed && displacements && displacements.length >= (i + 1) * 2) {
          const dx = displacements[i * 2] * dispScale;
          const dy = displacements[i * 2 + 1] * dispScale;
          return [node[0] + dx, node[1] + dy, 0];
        }
        return [node[0], node[1], 0];
      });

      // Populate vertices
      currentNodes.forEach(pt => {
        vertices.push(pt[0], pt[1], pt[2]);
      });

      // Max stress for colormap normalization
      let maxStress = 1.0;
      if (stresses && stresses.length > 0) {
        maxStress = Math.max(...stresses.map(s => Math.hypot(s[0], s[1]) + 1e-6));
      }

      // Populate element triangles & colors
      elements.forEach((elem, eIdx) => {
        if (elem.length >= 4) {
          // Q4 element split into 2 triangles (0,1,2) & (0,2,3)
          indices.push(elem[0], elem[1], elem[2]);
          indices.push(elem[0], elem[2], elem[3]);
        }

        // Stress / Density color lookup
        let r = 0.12, g = 0.3, b = 0.47;  // Default #1F4E79
        if (activeModule === 'topopt' && densities && densities.length > 0) {
          // Density visualization
          const row = Math.floor(eIdx / (densities[0]?.length || 1));
          const col = eIdx % (densities[0]?.length || 1);
          const rhoVal = densities[row]?.[col] ?? 0.5;
          r = 0.95 - rhoVal * 0.8;
          g = 0.95 - rhoVal * 0.7;
          b = 0.95 - rhoVal * 0.4;
        } else if (stresses && stresses[eIdx]) {
          const vm = Math.hypot(stresses[eIdx][0], stresses[eIdx][1]) / maxStress;
          // Blue to Red jet colormap
          r = Math.min(1.0, Math.max(0.0, 2.0 * vm - 0.5));
          g = Math.min(1.0, Math.max(0.0, 1.5 - Math.abs(2.0 * vm - 1.0)));
          b = Math.min(1.0, Math.max(0.0, 1.5 - 2.0 * vm));
        }

        elem.forEach(() => {
          colors.push(r, g, b);
        });
      });

      geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      geom.setIndex(indices);
      geom.computeVertexNormals();

      const mat = new THREE.MeshStandardMaterial({
        vertexColors: true,
        side: THREE.DoubleSide,
        roughness: 0.4,
        metalness: 0.1,
        wireframe: false
      });

      const mesh = new THREE.Mesh(geom, mat);
      scene.add(mesh);

      // Wireframe overlay
      const wireMat = new THREE.MeshBasicMaterial({ color: 0x1A1A1A, wireframe: true, transparent: true, opacity: 0.25 });
      const wireMesh = new THREE.Mesh(geom, wireMat);
      scene.add(wireMesh);
    }

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize listener
    const handleResize = () => {
      if (!mountRef.current || !rendererRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      if (rendererRef.current && mountRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
      }
    };
  }, [nodes, elements, displacements, stresses, densities, dispScale, showDeformed, colormap, activeModule]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%', position: 'relative' }} />;
};
