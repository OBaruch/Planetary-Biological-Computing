import * as THREE from "three";

/**
 * Procedural Earth textures used as an elegant fallback when no real textures
 * are present in /public/textures/earth. Everything is generated on a 2D
 * canvas once (memoize the result) so there is no per-frame cost.
 *
 * The noise is built on an integer lattice whose period wraps horizontally,
 * so the equirectangular texture tiles cleanly around the globe (no seam).
 */

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function smooth(t: number): number {
  return t * t * (3 - 2 * t);
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Tileable (in x) value-noise field generator. ``periodX`` is the lattice
 * period in cells across the full width; sampling wraps modulo it.
 */
function makeNoise(periodX: number, periodY: number, seed: number) {
  const rng = mulberry32(seed);
  const grid = new Float32Array((periodX + 1) * (periodY + 1));
  for (let y = 0; y <= periodY; y += 1) {
    for (let x = 0; x <= periodX; x += 1) {
      grid[y * (periodX + 1) + x] = rng();
    }
  }
  const at = (xi: number, yi: number) => {
    const wx = ((xi % periodX) + periodX) % periodX;
    const wy = Math.max(0, Math.min(periodY, yi));
    return grid[wy * (periodX + 1) + wx];
  };
  return (fx: number, fy: number) => {
    const x = fx * periodX;
    const y = fy * periodY;
    const x0 = Math.floor(x);
    const y0 = Math.floor(y);
    const tx = smooth(x - x0);
    const ty = smooth(y - y0);
    const v00 = at(x0, y0);
    const v10 = at(x0 + 1, y0);
    const v01 = at(x0, y0 + 1);
    const v11 = at(x0 + 1, y0 + 1);
    return lerp(lerp(v00, v10, tx), lerp(v01, v11, tx), ty);
  };
}

function fbm(noises: ((fx: number, fy: number) => number)[], fx: number, fy: number): number {
  let amp = 0.5;
  let sum = 0;
  let norm = 0;
  for (const noise of noises) {
    sum += amp * noise(fx, fy);
    norm += amp;
    amp *= 0.5;
  }
  return sum / norm;
}

export function createProceduralEarthTexture(width = 1024, height = 512): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d")!;
  const image = ctx.createImageData(width, height);
  const data = image.data;

  // Octaves with doubling period -> overall field tiles with the base period.
  const octaves = [
    makeNoise(6, 4, 1337),
    makeNoise(12, 8, 7331),
    makeNoise(24, 16, 4242),
    makeNoise(48, 32, 9182)
  ];

  const deepOcean = [8, 28, 64];
  const shallowOcean = [16, 78, 120];
  const lowland = [44, 110, 58];
  const highland = [120, 104, 60];
  const ice = [232, 240, 248];

  for (let y = 0; y < height; y += 1) {
    const fy = y / height;
    const lat = (0.5 - fy) * Math.PI; // -pi/2..pi/2
    const iceFactor = Math.max(0, (Math.abs(lat) - 1.04) / 0.5); // poles
    for (let x = 0; x < width; x += 1) {
      const fx = x / width;
      let h = fbm(octaves, fx, fy);
      // Bias toward more ocean and pull continents toward mid-latitudes.
      h = h * 1.15 - 0.18 - Math.abs(fy - 0.5) * 0.15;
      const idx = (y * width + x) * 4;
      let r: number;
      let g: number;
      let b: number;
      if (h < 0.42) {
        const t = Math.max(0, h / 0.42);
        r = lerp(deepOcean[0], shallowOcean[0], t);
        g = lerp(deepOcean[1], shallowOcean[1], t);
        b = lerp(deepOcean[2], shallowOcean[2], t);
      } else {
        const t = Math.min(1, (h - 0.42) / 0.4);
        r = lerp(lowland[0], highland[0], t);
        g = lerp(lowland[1], highland[1], t);
        b = lerp(lowland[2], highland[2], t);
      }
      if (iceFactor > 0) {
        const t = Math.min(1, iceFactor);
        r = lerp(r, ice[0], t);
        g = lerp(g, ice[1], t);
        b = lerp(b, ice[2], t);
      }
      data[idx] = r;
      data[idx + 1] = g;
      data[idx + 2] = b;
      data[idx + 3] = 255;
    }
  }

  ctx.putImageData(image, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  return texture;
}

export function createProceduralCloudTexture(width = 1024, height = 512): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d")!;
  const image = ctx.createImageData(width, height);
  const data = image.data;

  const octaves = [makeNoise(8, 5, 555), makeNoise(16, 10, 909), makeNoise(32, 20, 2024)];

  for (let y = 0; y < height; y += 1) {
    const fy = y / height;
    // Fewer clouds over the poles, banded toward temperate / tropical zones.
    const band = 0.55 + 0.45 * Math.cos((fy - 0.5) * Math.PI * 2.0);
    for (let x = 0; x < width; x += 1) {
      const fx = x / width;
      const n = fbm(octaves, fx, fy);
      const v = Math.max(0, (n * band - 0.45) / 0.55);
      const alpha = Math.min(1, v * 1.3);
      const idx = (y * width + x) * 4;
      data[idx] = 255;
      data[idx + 1] = 255;
      data[idx + 2] = 255;
      data[idx + 3] = Math.round(alpha * 215);
    }
  }

  ctx.putImageData(image, 0, 0);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  return texture;
}
