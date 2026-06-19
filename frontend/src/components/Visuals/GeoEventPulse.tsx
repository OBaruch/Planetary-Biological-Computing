import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { EventVisualStyle } from "../../types/geoEvents";

// Shared ring geometry: lies in the local XY plane (tangent to the surface
// once the parent marker orients +Z along the surface normal).
const RING_GEOMETRY = new THREE.RingGeometry(0.42, 0.5, 48);

interface RingProps {
  color: string;
  speed: number;
  maxScale: number;
  phase: number;
  baseOpacity: number;
  spin?: boolean;
  reducedMotion?: boolean;
}

function PulseRing({ color, speed, maxScale, phase, baseOpacity, spin = false, reducedMotion = false }: RingProps) {
  const mesh = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshBasicMaterial>(null);

  useFrame((state) => {
    if (!mesh.current || !material.current) return;
    if (reducedMotion) {
      mesh.current.scale.setScalar(maxScale * 0.6);
      material.current.opacity = baseOpacity * 0.5;
      return;
    }
    const t = (state.clock.elapsedTime * speed + phase) % 1;
    mesh.current.scale.setScalar(0.3 + (maxScale - 0.3) * t);
    material.current.opacity = baseOpacity * (1 - t);
    if (spin) mesh.current.rotation.z = state.clock.elapsedTime * 0.7;
  });

  return (
    <mesh ref={mesh} geometry={RING_GEOMETRY}>
      <meshBasicMaterial
        ref={material}
        color={color}
        transparent
        opacity={baseOpacity}
        side={THREE.DoubleSide}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}

interface Props {
  style: EventVisualStyle;
  intensity: number;
  reducedMotion?: boolean;
}

/** Expanding surface waves whose count/cadence depend on the event style. */
export function GeoEventPulse({ style, intensity, reducedMotion = false }: Props) {
  const maxScale = 0.9 + intensity * 1.7;
  const baseOpacity = 0.28 + intensity * 0.32;
  const speed = 1 / Math.max(0.4, style.pulseSpeed);

  const rings = useMemo(() => {
    if (style.ring === "none") return [];
    if (style.ring === "concentric") {
      return [0, 0.33, 0.66].map((phase) => ({ phase, spin: false }));
    }
    if (style.ring === "spiral") {
      return [
        { phase: 0, spin: true },
        { phase: 0.5, spin: true }
      ];
    }
    return [{ phase: 0, spin: false }];
  }, [style.ring]);

  return (
    <group>
      {rings.map((ring, index) => (
        <PulseRing
          key={index}
          color={style.color}
          speed={speed}
          maxScale={maxScale}
          phase={ring.phase}
          baseOpacity={baseOpacity}
          spin={ring.spin}
          reducedMotion={reducedMotion}
        />
      ))}
    </group>
  );
}
