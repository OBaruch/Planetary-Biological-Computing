import { useFrame } from "@react-three/fiber";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { GeoPlanetEvent } from "../../types/geoEvents";
import { eventIntensityToScale, eventTypeToVisualStyle, latLonToVector3 } from "../../utils/geo";
import { GeoEventPulse } from "./GeoEventPulse";

interface AscendingParticlesProps {
  color: string;
  count: number;
  reducedMotion?: boolean;
}

/** Small particles drifting outward along +Z (used for fire / renewable). */
function AscendingParticles({ color, count, reducedMotion = false }: AscendingParticlesProps) {
  const points = useRef<THREE.Points>(null);
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const seeds = new Float32Array(count);
    for (let i = 0; i < count; i += 1) {
      positions[i * 3] = (Math.random() - 0.5) * 0.18;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 0.18;
      positions[i * 3 + 2] = Math.random() * 0.6;
      seeds[i] = Math.random();
    }
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.userData.seeds = seeds;
    return geo;
  }, [count]);

  useFrame((_, delta) => {
    if (reducedMotion || !points.current) return;
    const attr = points.current.geometry.getAttribute("position") as THREE.BufferAttribute;
    for (let i = 0; i < count; i += 1) {
      let z = attr.getZ(i) + delta * (0.25 + (geometry.userData.seeds[i] as number) * 0.2);
      if (z > 0.7) z = 0.0;
      attr.setZ(i, z);
    }
    attr.needsUpdate = true;
  });

  return (
    <points ref={points} geometry={geometry}>
      <pointsMaterial
        color={color}
        size={0.05}
        transparent
        opacity={0.85}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

interface Props {
  event: GeoPlanetEvent;
  radius: number;
  selected: boolean;
  onSelect: (event: GeoPlanetEvent) => void;
  reducedMotion?: boolean;
}

export function GeoEventMarker({ event, radius, selected, onSelect, reducedMotion = false }: Props) {
  const [hovered, setHovered] = useState(false);
  const core = useRef<THREE.Mesh>(null);
  const halo = useRef<THREE.Mesh>(null);

  const style = useMemo(() => eventTypeToVisualStyle(event.type), [event.type]);
  const scale = eventIntensityToScale(event.intensity);

  const { position, quaternion } = useMemo(() => {
    const pos = latLonToVector3(event.latitude, event.longitude, radius);
    const normal = pos.clone().normalize();
    const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
    return { position: pos, quaternion: quat };
  }, [event.latitude, event.longitude, radius]);

  useFrame((state) => {
    const breathe = reducedMotion ? 1 : 1 + Math.sin(state.clock.elapsedTime * 2.4 + position.x) * 0.12;
    const focus = selected ? 1.7 : hovered ? 1.3 : 1;
    if (core.current) core.current.scale.setScalar(0.05 * scale * focus * breathe);
    if (halo.current) {
      halo.current.scale.setScalar(0.12 * scale * focus * breathe);
      (halo.current.material as THREE.MeshBasicMaterial).opacity = (selected ? 0.55 : 0.32) * breathe;
    }
  });

  return (
    <group position={position} quaternion={quaternion}>
      <group position={[0, 0, 0.02]}>
        {/* Glow halo */}
        <mesh ref={halo}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshBasicMaterial
            color={style.accent}
            transparent
            opacity={0.32}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
        {/* Clickable core */}
        <mesh
          ref={core}
          onPointerDown={(e) => {
            e.stopPropagation();
            onSelect(event);
          }}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHovered(true);
            document.body.style.cursor = "pointer";
          }}
          onPointerOut={() => {
            setHovered(false);
            document.body.style.cursor = "auto";
          }}
        >
          <sphereGeometry args={[1, 18, 18]} />
          <meshBasicMaterial color={style.color} toneMapped={false} />
        </mesh>
      </group>

      <GeoEventPulse style={style} intensity={event.intensity} reducedMotion={reducedMotion} />

      {style.particles ? (
        <AscendingParticles color={style.accent} count={12} reducedMotion={reducedMotion} />
      ) : null}

      {selected ? (
        <mesh position={[0, 0, 0.45]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.012, 0.012, 0.9, 8]} />
          <meshBasicMaterial color={style.accent} transparent opacity={0.7} toneMapped={false} />
        </mesh>
      ) : null}
    </group>
  );
}
