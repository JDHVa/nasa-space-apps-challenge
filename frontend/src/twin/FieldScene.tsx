import { useLayoutEffect, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";
import type { Strategy } from "../api/types";
import { useStore } from "../store";
import { sampleAt } from "./sample";

const HALF = 5;
const GRID = 28;
const PLANT_COUNT = GRID * GRID;
const RAIN_COUNT = 520;
const LAYERS = 4;
const LAYER_H = 0.6;

type CropLook = { height: number; width: number; color: string };

const LOOKS: Record<string, CropLook> = {
  maize: { height: 1.5, width: 0.9, color: "#3fa34d" },
  sorghum: { height: 1.25, width: 0.7, color: "#7bbf4a" },
  wheat: { height: 0.75, width: 0.5, color: "#c9b458" },
  oats: { height: 0.7, width: 0.5, color: "#a6c25a" },
  rye: { height: 0.85, width: 0.5, color: "#8fb56a" },
  beans: { height: 0.5, width: 1.1, color: "#2f9e5b" },
  soybean: { height: 0.55, width: 1.1, color: "#4cb35a" },
  alfalfa: { height: 0.5, width: 1.0, color: "#2e8f54" },
  vetch: { height: 0.4, width: 1.2, color: "#5f9a6a" },
  fallow: { height: 0.1, width: 0.5, color: "#8a7a4a" }
};
const DEFAULT_LOOK: CropLook = { height: 0.6, width: 0.8, color: "#4cb35a" };

function relief(x: number, z: number): number {
  const edge = Math.min(1, (HALF - Math.max(Math.abs(x), Math.abs(z))) / 1.4);
  return (0.22 * Math.sin(x * 0.55) * Math.cos(z * 0.42) + 0.08 * Math.sin(x * 1.3 + z * 0.7)) * Math.max(0, edge);
}

function seeded(i: number): number {
  const x = Math.sin(i * 91.345 + 7.77) * 43758.5453;
  return x - Math.floor(x);
}

function Terrain({ bareRef }: { bareRef: React.MutableRefObject<THREE.MeshStandardMaterial | null> }) {
  const geometry = useMemo(() => {
    const g = new THREE.PlaneGeometry(HALF * 2, HALF * 2, 56, 56);
    g.rotateX(-Math.PI / 2);
    const pos = g.attributes.position;
    const colors = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      pos.setY(i, relief(x, z));
      const v = 0.8 + seeded(i) * 0.14 + 0.1 * Math.sin(x * 2.1) * Math.cos(z * 1.7);
      colors[i * 3] = v;
      colors[i * 3 + 1] = v;
      colors[i * 3 + 2] = v;
    }
    g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    g.computeVertexNormals();
    return g;
  }, []);
  return (
    <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial ref={bareRef} vertexColors roughness={1} color="#6b4a2f" />
    </mesh>
  );
}

function SoilBlock({ fillRefs }: { fillRefs: React.MutableRefObject<(THREE.Mesh | null)[]> }) {
  const layerColors = ["#4a3320", "#3d2a1a", "#33231a", "#2a1d15"];
  return (
    <group position={[0, -LAYERS * LAYER_H, 0]}>
      {layerColors.map((color, i) => {
        const y = (LAYERS - 1 - i) * LAYER_H + LAYER_H / 2;
        return (
          <group key={i} position={[0, y, 0]}>
            <mesh>
              <boxGeometry args={[HALF * 2, LAYER_H - 0.02, HALF * 2]} />
              <meshStandardMaterial color={color} roughness={1} />
            </mesh>
            <mesh
              ref={(m) => {
                fillRefs.current[i * 2] = m;
              }}
              position={[0, -LAYER_H / 2, HALF + 0.012]}
            >
              <planeGeometry args={[HALF * 2, LAYER_H - 0.02]} />
              <meshStandardMaterial color="#38bdf8" emissive="#0ea5e9" emissiveIntensity={0.6} transparent opacity={0.6} />
            </mesh>
            <mesh
              ref={(m) => {
                fillRefs.current[i * 2 + 1] = m;
              }}
              position={[HALF + 0.012, -LAYER_H / 2, 0]}
              rotation={[0, Math.PI / 2, 0]}
            >
              <planeGeometry args={[HALF * 2, LAYER_H - 0.02]} />
              <meshStandardMaterial color="#38bdf8" emissive="#0ea5e9" emissiveIntensity={0.6} transparent opacity={0.6} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

type Live = {
  canopy: number;
  moisture: number;
  rain: number;
  height: number;
  width: number;
  color: THREE.Color;
  layers: number[];
};

function Dynamics({ strategy }: { strategy: Strategy }) {
  const plants = useRef<THREE.InstancedMesh>(null);
  const rain = useRef<THREE.InstancedMesh>(null);
  const soilMat = useRef<THREE.MeshStandardMaterial | null>(null);
  const fills = useRef<(THREE.Mesh | null)[]>([]);
  const sun = useRef<THREE.DirectionalLight>(null);
  const cloud = useRef<THREE.Group>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const live = useRef<Live>({
    canopy: 0,
    moisture: 0.4,
    rain: 0,
    height: 0.6,
    width: 0.8,
    color: new THREE.Color("#4cb35a"),
    layers: [0.4, 0.4, 0.4, 0.4]
  });
  const plantData = useMemo(() => {
    const list: { x: number; z: number; y: number; yaw: number; offset: number }[] = [];
    const step = (HALF * 2 - 1) / (GRID - 1);
    for (let r = 0; r < GRID; r++) {
      for (let c = 0; c < GRID; c++) {
        const i = r * GRID + c;
        const x = -HALF + 0.5 + c * step + (seeded(i) - 0.5) * 0.12;
        const z = -HALF + 0.5 + r * step + (seeded(i + 999) - 0.5) * 0.05;
        list.push({ x, z, y: relief(x, z), yaw: seeded(i + 31) * Math.PI, offset: seeded(i + 77) });
      }
    }
    return list;
  }, []);
  const rainData = useMemo(
    () =>
      Array.from({ length: RAIN_COUNT }, (_, i) => ({
        x: (seeded(i + 5) - 0.5) * (HALF * 2 + 1),
        z: (seeded(i + 500) - 0.5) * (HALF * 2 + 1),
        y: seeded(i + 900) * 8,
        v: 11 + seeded(i + 1300) * 6
      })),
    []
  );
  const tint = useMemo(() => new THREE.Color(), []);
  const bare = useMemo(() => new THREE.Color("#7a5634"), []);
  const wet = useMemo(() => new THREE.Color("#3e2a19"), []);
  const stubble = useMemo(() => new THREE.Color("#5f6b3a"), []);

  useLayoutEffect(() => {
    const mesh = plants.current;
    if (!mesh) return;
    const c = new THREE.Color();
    plantData.forEach((p, i) => {
      const v = 0.72 + p.offset * 0.28;
      c.setRGB(v, v, v);
      mesh.setColorAt(i, c);
    });
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  }, [plantData]);

  useFrame((_, rawDt) => {
    const dt = Math.min(rawDt, 0.05);
    const state = useStore.getState();
    const s = sampleAt(strategy.daily_sample, state.week);
    const look = (s.crop && LOOKS[s.crop]) || (s.crop ? DEFAULT_LOOK : null);
    const k = 1 - Math.exp(-dt * 4);
    const L = live.current;
    L.canopy += (s.canopy - L.canopy) * k;
    L.moisture += (s.moisture - L.moisture) * k;
    L.rain += (s.rain - L.rain) * k;
    if (look) {
      L.height += (look.height - L.height) * k;
      L.width += (look.width - L.width) * k;
      tint.set(look.color);
      L.color.lerp(tint, k);
    }
    for (let i = 0; i < LAYERS; i++) {
      const target = Math.max(0.03, Math.min(1, s.moisture * (1.15 - i * 0.12) + (i > 1 ? 0.08 : 0)));
      L.layers[i] += (target - L.layers[i]) * (1 - Math.exp(-dt * (2.2 - i * 0.45)));
      const front = fills.current[i * 2];
      const side = fills.current[i * 2 + 1];
      const f = L.layers[i];
      [front, side].forEach((m) => {
        if (!m) return;
        m.scale.y = Math.max(0.001, f);
        m.position.y = -LAYER_H / 2 + (LAYER_H * f) / 2 - 0.01;
      });
    }

    const mesh = plants.current;
    if (mesh) {
      const mat = mesh.material as THREE.MeshStandardMaterial;
      mat.color.copy(L.color);
      for (let i = 0; i < PLANT_COUNT; i++) {
        const p = plantData[i];
        const g = Math.max(0, Math.min(1.15, L.canopy * 1.25 - p.offset * 0.18));
        const visible = L.canopy > 0.04 ? g : 0;
        dummy.position.set(p.x, p.y, p.z);
        dummy.rotation.set(0, p.yaw, 0);
        if (visible <= 0) dummy.scale.set(0, 0, 0);
        else
          dummy.scale.set(
            0.1 + 0.18 * L.width * visible,
            Math.max(0.0001, L.height * visible),
            0.1 + 0.18 * L.width * visible
          );
        dummy.updateMatrix();
        mesh.setMatrixAt(i, dummy.matrix);
      }
      mesh.instanceMatrix.needsUpdate = true;
    }

    if (soilMat.current) {
      soilMat.current.color.copy(bare).lerp(wet, Math.min(1, L.moisture * 1.1));
      soilMat.current.color.lerp(stubble, Math.min(0.5, L.canopy * 0.6));
    }

    const rainMesh = rain.current;
    const intensity = Math.max(0, Math.min(1, L.rain / 22));
    if (rainMesh) {
      const active = Math.floor(intensity * RAIN_COUNT);
      for (let i = 0; i < RAIN_COUNT; i++) {
        const d = rainData[i];
        d.y -= d.v * dt;
        if (d.y < 0) d.y += 8;
        dummy.position.set(d.x, d.y, d.z);
        dummy.rotation.set(0, 0, 0);
        const on = i < active ? 1 : 0;
        dummy.scale.set(on, on, on);
        dummy.updateMatrix();
        rainMesh.setMatrixAt(i, dummy.matrix);
      }
      rainMesh.instanceMatrix.needsUpdate = true;
    }

    if (sun.current) sun.current.intensity = 2.3 - intensity * 1.4;
    if (cloud.current) {
      cloud.current.children.forEach((c) => {
        const m = (c as THREE.Mesh).material as THREE.MeshBasicMaterial;
        m.opacity = 0.08 + intensity * 0.5;
      });
    }
  });

  return (
    <>
      <Terrain bareRef={soilMat} />
      <SoilBlock fillRefs={fills} />
      <instancedMesh ref={plants} args={[undefined, undefined, PLANT_COUNT]} castShadow frustumCulled={false}>
        <coneGeometry args={[1, 1, 5, 1]} onUpdate={(g) => g.translate(0, 0.5, 0)} />
        <meshStandardMaterial roughness={0.8} />
      </instancedMesh>
      <instancedMesh ref={rain} args={[undefined, undefined, RAIN_COUNT]} frustumCulled={false}>
        <boxGeometry args={[0.012, 0.35, 0.012]} />
        <meshBasicMaterial color="#9bd0ff" transparent opacity={0.75} />
      </instancedMesh>
      <group ref={cloud} position={[0, 8.6, 0]}>
        {[
          [-3, 0, -1, 3.2],
          [1.5, 0.3, 1, 3.8],
          [3.5, -0.2, -2, 2.8]
        ].map(([x, y, z, r], i) => (
          <mesh key={i} position={[x, y, z]} scale={[r, r * 0.35, r * 0.8]}>
            <sphereGeometry args={[1, 16, 12]} />
            <meshBasicMaterial color="#aab6c8" transparent opacity={0.1} depthWrite={false} />
          </mesh>
        ))}
      </group>
      <directionalLight
        ref={sun}
        position={[9, 10, -5]}
        intensity={2.2}
        color="#ffe2b0"
        castShadow
        shadow-mapSize={[1024, 1024]}
        shadow-camera-left={-9}
        shadow-camera-right={9}
        shadow-camera-top={9}
        shadow-camera-bottom={-9}
      />
      <mesh position={[14, 12, -9]}>
        <sphereGeometry args={[1.1, 24, 24]} />
        <meshBasicMaterial color="#ffd27a" />
      </mesh>
    </>
  );
}

export function FieldScene({ strategy }: { strategy: Strategy }) {
  return (
    <Canvas shadows dpr={[1, 1.75]} camera={{ position: [11, 7.5, 12], fov: 38 }} gl={{ antialias: true }}>
      <color attach="background" args={["#070d1a"]} />
      <fog attach="fog" args={["#070d1a", 26, 60]} />
      <ambientLight intensity={0.55} color="#9db8ff" />
      <hemisphereLight args={["#86a8ff", "#2a1d12", 0.45]} />
      <Stars radius={70} depth={40} count={2200} factor={3} fade speed={0.6} />
      <Dynamics strategy={strategy} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -LAYERS * LAYER_H - 0.05, 0]}>
        <circleGeometry args={[30, 64]} />
        <meshStandardMaterial color="#0a1424" roughness={1} />
      </mesh>
      <gridHelper args={[60, 60, "#1c3358", "#122240"]} position={[0, -LAYERS * LAYER_H - 0.04, 0]} />
      <OrbitControls
        autoRotate
        autoRotateSpeed={0.45}
        enablePan={false}
        enableDamping
        minDistance={8}
        maxDistance={30}
        maxPolarAngle={Math.PI / 2.05}
        target={[0, -0.8, 0]}
      />
    </Canvas>
  );
}
