import { forwardRef } from "react";
import * as THREE from "three";
import type { EarthTextures } from "../../hooks/useEarthTextures";

interface Props {
  radius: number;
  textures: EarthTextures;
  opacity?: number;
}

/**
 * Translucent cloud shell. The parent advances this group's rotation slightly
 * faster than the Earth so the clouds drift over the surface.
 */
export const EarthClouds = forwardRef<THREE.Group, Props>(function EarthClouds(
  { radius, textures, opacity = 0.42 },
  ref
) {
  return (
    <group ref={ref}>
      <mesh>
        <sphereGeometry args={[radius * 1.012, 64, 64]} />
        <meshStandardMaterial
          map={textures.cloudMap}
          alphaMap={textures.cloudMap}
          transparent
          opacity={opacity}
          depthWrite={false}
          roughness={1}
          metalness={0}
        />
      </mesh>
    </group>
  );
});
