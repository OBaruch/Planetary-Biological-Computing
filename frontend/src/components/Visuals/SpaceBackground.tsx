import { Stars } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";

interface Props {
  reducedMotion?: boolean;
}

/** Deep-space backdrop: a slowly drifting star field with a faint nebula tint. */
export function SpaceBackground({ reducedMotion = false }: Props) {
  const group = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (reducedMotion || !group.current) return;
    group.current.rotation.y += delta * 0.005;
    group.current.rotation.x += delta * 0.002;
  });

  return (
    <group ref={group}>
      <Stars radius={120} depth={70} count={4200} factor={4} saturation={0} fade speed={reducedMotion ? 0 : 0.4} />
      {/* Faint nebula glow far behind the planet for depth. */}
      <mesh position={[14, 8, -60]}>
        <sphereGeometry args={[26, 24, 24]} />
        <meshBasicMaterial color="#1b2a5e" transparent opacity={0.07} />
      </mesh>
      <mesh position={[-20, -12, -70]}>
        <sphereGeometry args={[30, 24, 24]} />
        <meshBasicMaterial color="#3a1c5e" transparent opacity={0.05} />
      </mesh>
    </group>
  );
}
