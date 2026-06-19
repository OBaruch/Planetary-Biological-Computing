import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { DecodedAction, PlanetState } from "../../api/types";
import type { EarthTextures } from "../../hooks/useEarthTextures";

interface Props {
  radius: number;
  textures: EarthTextures;
  planetState: PlanetState;
  decodedAction?: DecodedAction;
}

/** The textured Earth body. Rotation is owned by the parent globe group. */
export function EarthSphere({ radius, textures, planetState, decodedAction }: Props) {
  const material = useRef<THREE.MeshStandardMaterial>(null);

  const oceanColor = useMemo(() => new THREE.Color("#2bd6ff"), []);
  const recoveryColor = useMemo(() => new THREE.Color("#37e0a0"), []);
  const heatColor = useMemo(() => new THREE.Color("#ff6a3a"), []);
  const target = useMemo(() => new THREE.Color(), []);

  useFrame((_, delta) => {
    const mat = material.current;
    if (!mat) return;
    const action = decodedAction?.primary_action;
    const oceanBoost = action === "stabilize_oceans" ? 0.5 : 0;
    const coolBoost = action === "cool_planet" ? 0.25 : 0;
    const chaosBoost = action === "amplify_chaos" ? 0.3 : 0;

    // Target emissive color: recovery -> teal, heat/chaos -> orange, oceans -> blue.
    target.copy(recoveryColor).lerp(heatColor, Math.min(1, planetState.temperature * 0.6 + chaosBoost));
    if (oceanBoost > 0) target.lerp(oceanColor, oceanBoost);
    mat.emissive.lerp(target, Math.min(1, delta * 2));

    const targetIntensity =
      0.08 + planetState.recovery * 0.22 + oceanBoost * 0.25 + coolBoost * 0.1 + planetState.visual_intensity * 0.06;
    mat.emissiveIntensity += (targetIntensity - mat.emissiveIntensity) * Math.min(1, delta * 2);
  });

  return (
    <mesh>
      <sphereGeometry args={[radius, 96, 96]} />
      <meshStandardMaterial
        ref={material}
        map={textures.dayMap}
        normalMap={textures.normalMap ?? undefined}
        metalnessMap={textures.specularMap ?? undefined}
        emissiveMap={textures.nightMap ?? undefined}
        metalness={textures.specularMap ? 0.45 : 0.12}
        roughness={0.72}
        emissive={new THREE.Color("#1a7d6b")}
        emissiveIntensity={0.12}
      />
    </mesh>
  );
}
