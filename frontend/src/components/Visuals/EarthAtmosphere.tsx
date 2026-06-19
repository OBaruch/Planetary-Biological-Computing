import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { PlanetState } from "../../api/types";

interface Props {
  radius: number;
  planetState: PlanetState;
  reducedMotion?: boolean;
}

const VERTEX = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vViewDir;
  void main() {
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vNormal = normalize(mat3(modelMatrix) * normal);
    vViewDir = normalize(cameraPosition - worldPos.xyz);
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

const FRAGMENT = /* glsl */ `
  uniform vec3 uColor;
  uniform float uIntensity;
  uniform float uPower;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  void main() {
    float fresnel = pow(1.0 - clamp(dot(vNormal, vViewDir), 0.0, 1.0), uPower);
    gl_FragColor = vec4(uColor, fresnel * uIntensity);
  }
`;

/** Fresnel atmosphere glow that shifts color/intensity with planet state. */
export function EarthAtmosphere({ radius, planetState, reducedMotion = false }: Props) {
  const material = useRef<THREE.ShaderMaterial>(null);
  const uniforms = useMemo(
    () => ({
      uColor: { value: new THREE.Color("#5aa9ff") },
      uIntensity: { value: 0.9 },
      uPower: { value: 3.2 }
    }),
    []
  );

  const calm = useMemo(() => new THREE.Color("#5aa9ff"), []);
  const hot = useMemo(() => new THREE.Color("#ff8a4c"), []);
  const heal = useMemo(() => new THREE.Color("#52e6c8"), []);
  const scratch = useMemo(() => new THREE.Color(), []);

  useFrame((state) => {
    if (!material.current) return;
    // Blend calm -> hot with temperature/chaos, lift toward heal with recovery.
    const warmth = Math.min(1, planetState.temperature * 0.6 + planetState.chaos * 0.5);
    scratch.copy(calm).lerp(hot, warmth).lerp(heal, planetState.recovery * 0.4);
    uniforms.uColor.value.copy(scratch);
    const flicker = reducedMotion ? 0 : Math.sin(state.clock.elapsedTime * 1.6) * 0.05 * planetState.chaos;
    uniforms.uIntensity.value = 0.55 + planetState.visual_intensity * 0.5 + planetState.recovery * 0.2 + flicker;
  });

  return (
    <mesh scale={radius * 1.16}>
      <sphereGeometry args={[1, 64, 64]} />
      <shaderMaterial
        ref={material}
        args={[
          {
            vertexShader: VERTEX,
            fragmentShader: FRAGMENT,
            uniforms,
            transparent: true,
            blending: THREE.AdditiveBlending,
            side: THREE.BackSide,
            depthWrite: false
          }
        ]}
      />
    </mesh>
  );
}
