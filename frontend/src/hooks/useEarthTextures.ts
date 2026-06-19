import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { createProceduralCloudTexture, createProceduralEarthTexture } from "../utils/proceduralEarth";

const BASE = "textures/earth";

export interface EarthTextures {
  dayMap: THREE.Texture;
  cloudMap: THREE.Texture;
  nightMap: THREE.Texture | null;
  normalMap: THREE.Texture | null;
  specularMap: THREE.Texture | null;
  usingProcedural: boolean;
}

function loadTexture(url: string): Promise<THREE.Texture | null> {
  return new Promise((resolve) => {
    new THREE.TextureLoader().load(
      url,
      (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.anisotropy = 4;
        resolve(texture);
      },
      undefined,
      () => resolve(null)
    );
  });
}

/**
 * Attempts to load realistic Earth textures from /public/textures/earth and
 * transparently falls back to procedurally-generated canvas textures when an
 * asset is missing. Never suspends or throws, so the build/runtime works with
 * zero assets present.
 */
export function useEarthTextures(): EarthTextures {
  const proceduralDay = useMemo(() => createProceduralEarthTexture(), []);
  const proceduralClouds = useMemo(() => createProceduralCloudTexture(), []);

  const [loaded, setLoaded] = useState<{
    day: THREE.Texture | null;
    clouds: THREE.Texture | null;
    night: THREE.Texture | null;
    normal: THREE.Texture | null;
    specular: THREE.Texture | null;
  }>({ day: null, clouds: null, night: null, normal: null, specular: null });

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      loadTexture(`${BASE}/earth_day.jpg`),
      loadTexture(`${BASE}/earth_clouds.png`),
      loadTexture(`${BASE}/earth_night.jpg`),
      loadTexture(`${BASE}/earth_normal.jpg`),
      loadTexture(`${BASE}/earth_specular.jpg`)
    ]).then(([day, clouds, night, normal, specular]) => {
      if (cancelled) return;
      setLoaded({ day, clouds, night, normal, specular });
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return useMemo<EarthTextures>(() => {
    const dayMap = loaded.day ?? proceduralDay;
    const cloudMap = loaded.clouds ?? proceduralClouds;
    return {
      dayMap,
      cloudMap,
      nightMap: loaded.night,
      normalMap: loaded.normal,
      specularMap: loaded.specular,
      usingProcedural: !loaded.day
    };
  }, [loaded, proceduralDay, proceduralClouds]);
}
