import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { PlanetState } from "../api/types";

function mixColor(a: string, b: string, amount: number) {
  return new THREE.Color(a).lerp(new THREE.Color(b), amount);
}

function PlanetMesh({ state }: { state: PlanetState }) {
  const planet = useRef<THREE.Mesh>(null);
  const halo = useRef<THREE.Mesh>(null);
  const particles = useRef<THREE.Points>(null);
  const particleGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(360 * 3);
    for (let i = 0; i < 360; i += 1) {
      const radius = 2.35 + Math.random() * 0.9;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
    }
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geometry;
  }, []);

  useFrame((_, delta) => {
    if (planet.current) {
      planet.current.rotation.y += delta * (0.08 + state.chaos * 0.16);
      planet.current.rotation.x = Math.sin(Date.now() / 3400) * 0.04;
    }
    if (halo.current) {
      const pulse = 1 + Math.sin(Date.now() / 260) * state.visual_intensity * 0.05;
      halo.current.scale.setScalar(pulse);
    }
    if (particles.current) {
      particles.current.rotation.y -= delta * (0.025 + state.recovery * 0.04);
    }
  });

  const oceanColor = mixColor("#0b6f7d", "#e85c4a", state.temperature);
  const landColor = mixColor("#2fbf71", "#b98542", 1 - state.biosphere);
  const atmosphereColor = mixColor("#8ee6ff", "#f5b04c", state.chaos);

  return (
    <group>
      <mesh ref={planet}>
        <sphereGeometry args={[1.75, 96, 96]} />
        <meshStandardMaterial
          color={oceanColor}
          metalness={0.12}
          roughness={0.48}
          emissive={landColor}
          emissiveIntensity={0.22 + state.recovery * 0.28}
        />
      </mesh>
      <mesh rotation={[0.3, 0.55, 0.1]}>
        <sphereGeometry args={[1.765, 64, 64]} />
        <meshBasicMaterial color={landColor} wireframe transparent opacity={0.18 + state.biosphere * 0.12} />
      </mesh>
      <mesh ref={halo}>
        <sphereGeometry args={[1.96, 64, 64]} />
        <meshBasicMaterial color={atmosphereColor} transparent opacity={0.16 + state.visual_intensity * 0.18} />
      </mesh>
      <points ref={particles} geometry={particleGeometry}>
        <pointsMaterial color="#f4f1c9" size={0.016 + state.visual_intensity * 0.02} transparent opacity={0.58} />
      </points>
    </group>
  );
}

export function PlanetView({ state }: { state: PlanetState }) {
  return (
    <section className="planet-stage" aria-label="Digital Earth visualization">
      <Canvas camera={{ position: [0, 0, 5.6], fov: 42 }}>
        <color attach="background" args={["#071111"]} />
        <ambientLight intensity={0.65} />
        <directionalLight position={[3, 2, 4]} intensity={2.6} color="#f4dfae" />
        <pointLight position={[-3, -2, 2]} intensity={1.3} color="#54d6c7" />
        <PlanetMesh state={state} />
      </Canvas>
      <div className="planet-readout">
        <span>{state.planetary_mood_label}</span>
        <strong>{Math.round(state.resilience * 100)}% resilience</strong>
      </div>
    </section>
  );
}
