import { Line } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type { Line2, LineMaterial } from "three-stdlib";
import * as THREE from "three";
import type { GeoPlanetEvent } from "../../types/geoEvents";
import { buildArcCurve, latLonToVector3 } from "../../utils/geo";

interface ArcProps {
  start: THREE.Vector3;
  end: THREE.Vector3;
  color: string;
  flowSpeed: number;
  opacity: number;
  reducedMotion?: boolean;
}

function Arc({ start, end, color, flowSpeed, opacity, reducedMotion = false }: ArcProps) {
  const ref = useRef<Line2>(null);
  const points = useMemo(() => buildArcCurve(start, end, 0.8).getPoints(48), [start, end]);

  useFrame((state) => {
    if (reducedMotion || !ref.current) return;
    const material = ref.current.material as LineMaterial;
    material.dashOffset = -state.clock.elapsedTime * flowSpeed;
  });

  return (
    <Line
      ref={ref}
      points={points}
      color={color}
      lineWidth={1.4}
      transparent
      opacity={opacity}
      dashed
      dashScale={6}
      dashSize={0.35}
      gapSize={0.18}
      depthWrite={false}
    />
  );
}

interface Props {
  events: GeoPlanetEvent[];
  radius: number;
  neuralActivity: number;
  reducedMotion?: boolean;
}

/**
 * Hub-and-spoke arcs connecting the strongest event to other active regions.
 * Brightness and flow speed scale with simulated neural activity.
 */
export function GeoEventArc({ events, radius, neuralActivity, reducedMotion = false }: Props) {
  const arcs = useMemo(() => {
    const strong = [...events].sort((a, b) => b.intensity - a.intensity).slice(0, 6);
    if (strong.length < 2) return [];
    const hub = strong[0];
    const hubPos = latLonToVector3(hub.latitude, hub.longitude, radius);
    return strong.slice(1).map((event) => ({
      id: `${hub.id}-${event.id}`,
      start: hubPos,
      end: latLonToVector3(event.latitude, event.longitude, radius)
    }));
  }, [events, radius]);

  const opacity = 0.18 + neuralActivity * 0.4;
  const flowSpeed = 0.6 + neuralActivity * 2.2;

  return (
    <group>
      {arcs.map((arc) => (
        <Arc
          key={arc.id}
          start={arc.start}
          end={arc.end}
          color="#8ef0ff"
          flowSpeed={flowSpeed}
          opacity={opacity}
          reducedMotion={reducedMotion}
        />
      ))}
    </group>
  );
}
