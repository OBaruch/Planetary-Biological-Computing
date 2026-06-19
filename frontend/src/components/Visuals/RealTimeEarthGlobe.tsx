import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { DecodedAction, NeuralMetrics, PlanetState } from "../../api/types";
import { useEarthTextures } from "../../hooks/useEarthTextures";
import type { GeoPlanetEvent } from "../../types/geoEvents";
import { EarthAtmosphere } from "./EarthAtmosphere";
import { EarthClouds } from "./EarthClouds";
import { EarthSphere } from "./EarthSphere";
import { GeoEventArc } from "./GeoEventArc";
import { GeoEventMarker } from "./GeoEventMarker";
import { SpaceBackground } from "./SpaceBackground";

const GLOBE_RADIUS = 2;
const MAX_CAMERA_DISTANCE = 14;

export interface RealTimeEarthGlobeProps {
  events: GeoPlanetEvent[];
  planetState: PlanetState;
  neuralMetrics?: NeuralMetrics;
  decodedAction?: DecodedAction;
  autoRotate?: boolean;
  selectedEventId?: string | null;
  onSelectEvent?: (event: GeoPlanetEvent) => void;
}

interface GlobeProps extends RealTimeEarthGlobeProps {
  reducedMotion: boolean;
  interaction: React.RefObject<{ active: boolean; resumeAt: number }>;
}

function Globe({
  events,
  planetState,
  neuralMetrics,
  decodedAction,
  autoRotate = true,
  selectedEventId,
  onSelectEvent,
  reducedMotion,
  interaction
}: GlobeProps) {
  const earthGroup = useRef<THREE.Group>(null);
  const cloudGroup = useRef<THREE.Group>(null);
  const neuralShell = useRef<THREE.Mesh>(null);
  const textures = useEarthTextures();

  const neuralActivity = neuralMetrics?.neural_activity_level ?? 0;
  const spikeRate = neuralMetrics?.spikes_per_second ?? 0;
  const chaosSignal = neuralMetrics?.chaos_signal ?? planetState.chaos;
  const recoverySignal = neuralMetrics?.recovery_signal ?? planetState.recovery;

  useFrame((state, delta) => {
    const now = state.clock.elapsedTime;
    const paused = interaction.current.active || now < interaction.current.resumeAt;
    const spin = autoRotate && !reducedMotion && !paused ? 1 : 0;

    // Base axial spin accelerates slightly with chaos.
    const baseSpeed = 0.05 + planetState.chaos * 0.12;
    if (earthGroup.current) {
      earthGroup.current.rotation.y += delta * baseSpeed * spin;
      // Micro-glitch: tiny jitter when chaos is high.
      const glitch = !reducedMotion && chaosSignal > 0.6 ? (Math.random() - 0.5) * 0.0025 * chaosSignal : 0;
      earthGroup.current.rotation.z = glitch;
    }
    if (cloudGroup.current) {
      cloudGroup.current.rotation.y += delta * (baseSpeed * 1.35 + 0.01) * spin;
    }

    // Global neural-burst shell: brighter with spikes + recovery harmonics.
    if (neuralShell.current) {
      const mat = neuralShell.current.material as THREE.MeshBasicMaterial;
      const burst = reducedMotion ? 0 : (Math.sin(now * (1.5 + spikeRate * 0.05)) * 0.5 + 0.5);
      const target = 0.02 + neuralActivity * 0.1 * burst + recoverySignal * 0.04;
      mat.opacity += (target - mat.opacity) * Math.min(1, delta * 3);
    }
  });

  const selectableEvents = useMemo(() => events.slice(0, 100), [events]);

  return (
    <>
      <SpaceBackground reducedMotion={reducedMotion} />

      <ambientLight intensity={0.35} />
      <directionalLight position={[5, 3, 5]} intensity={2.4} color="#fff4e0" />
      <pointLight position={[-6, -2, -4]} intensity={0.7} color="#5a86ff" />

      {/* Rotating Earth system: surface + coordinate-anchored events. */}
      <group ref={earthGroup}>
        <EarthSphere
          radius={GLOBE_RADIUS}
          textures={textures}
          planetState={planetState}
          decodedAction={decodedAction}
        />
        <GeoEventArc
          events={selectableEvents}
          radius={GLOBE_RADIUS * 1.01}
          neuralActivity={neuralActivity}
          reducedMotion={reducedMotion}
        />
        {selectableEvents.map((event) => (
          <GeoEventMarker
            key={event.id}
            event={event}
            radius={GLOBE_RADIUS}
            selected={event.id === selectedEventId}
            onSelect={(e) => onSelectEvent?.(e)}
            reducedMotion={reducedMotion}
          />
        ))}
      </group>

      {/* Clouds drift slightly faster than the surface. */}
      <EarthClouds ref={cloudGroup} radius={GLOBE_RADIUS} textures={textures} />

      {/* Global neural-burst shell. */}
      <mesh ref={neuralShell} scale={GLOBE_RADIUS * 1.05}>
        <sphereGeometry args={[1, 48, 48]} />
        <meshBasicMaterial
          color="#8ef0ff"
          transparent
          opacity={0.02}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </mesh>

      <EarthAtmosphere radius={GLOBE_RADIUS} planetState={planetState} reducedMotion={reducedMotion} />

      <OrbitControls
        enablePan={false}
        enableDamping
        dampingFactor={0.08}
        rotateSpeed={0.55}
        minDistance={2.6}
        maxDistance={MAX_CAMERA_DISTANCE}
        autoRotate={false}
        onStart={() => {
          interaction.current.active = true;
        }}
        onEnd={() => {
          interaction.current.active = false;
          interaction.current.resumeAt = performance.now() / 1000 + 2.5;
        }}
      />
    </>
  );
}

export function RealTimeEarthGlobe(props: RealTimeEarthGlobeProps) {
  const interaction = useRef({ active: false, resumeAt: 0 });
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(query.matches);
    const handler = (event: MediaQueryListEvent) => setReducedMotion(event.matches);
    query.addEventListener("change", handler);
    return () => query.removeEventListener("change", handler);
  }, []);

  return (
    <Canvas
      camera={{ position: [0, 1.1, 5.4], fov: 45 }}
      dpr={[1, 2]}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={["#04070d"]} />
      <Globe {...props} reducedMotion={reducedMotion} interaction={interaction} />
    </Canvas>
  );
}
