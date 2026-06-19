# Earth textures

Drop realistic equirectangular Earth textures here to upgrade the
`RealTimeEarthGlobe` from its built-in procedural fallback to photographic
quality. Files are loaded at runtime and are **optional** — if any are missing,
the globe automatically uses a procedurally-generated canvas texture instead, so
the build and app always work with zero assets present.

Expected files (all optional):

```
public/textures/earth/
  earth_day.jpg       # daytime color map (required for a photographic globe)
  earth_clouds.png    # cloud layer, white on transparent alpha
  earth_night.jpg     # city lights (used as a subtle emissive map)
  earth_normal.jpg    # normal map for surface relief
  earth_specular.jpg  # ocean specular / metalness mask
```

## Recommended specs

- Equirectangular projection (2:1 aspect ratio), e.g. 2048×1024 or 4096×2048.
- `earth_day.jpg` / `earth_night.jpg`: sRGB JPG.
- `earth_clouds.png`: PNG with an alpha channel (white clouds, transparent sky).

## Where to get properly-licensed textures

Use public-domain or appropriately-licensed sources only. NASA Visible Earth
("Blue Marble" / "Black Marble") publishes high-resolution, public-domain Earth
imagery:

- https://visibleearth.nasa.gov/collection/1484/blue-marble
- https://earthobservatory.nasa.gov/features/NightLights

Do **not** commit textures with unclear or restrictive licensing.
