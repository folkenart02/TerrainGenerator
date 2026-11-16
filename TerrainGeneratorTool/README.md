# Terrain Generator Tool

A Python prototype for creating terrain heightmaps from real-world elevation data. The original goal is to use terrain tools in Unreal Engine with a generated heightmap, followed by a working terrain-generation workflow for Unity as well.

## Project scope

The project is intended to:

1. Select an area using a center latitude/longitude and radius.
2. Download a digital elevation model (DEM) from OpenTopography.
3. Convert the DEM into a grayscale PNG heightmap and write metadata describing its elevation range and sample spacing.
4. Make the generated terrain usable in Unreal Engine or Unity (Depending on which one is being used).

The current implementation covers the Python download and conversion pipeline. It does **not** yet include an Unreal Engine project, automated Unreal Landscape import, a Unity project, or a Unity terrain importer. See [REQUIREMENTS.md](REQUIREMENTS.md) for scope, status, and acceptance criteria.

## Current status

**Stage: functional Python prototype; engine integration remains future work.**

The pipeline currently:

- Reads `dem_center_lat`, `dem_center_lon`, and `dem_radius_km` from `terrain_config.json`.
- Requests a COP30 DEM from OpenTopography and saves it as a GeoTIFF.
- Reprojects and resamples the DEM into a square, 16-bit PNG heightmap at one of the configured sample sizes.
- Writes a companion metadata JSON file with the output dimensions, projected CRS, sample spacing, elevation minimum/maximum, and pixel encoding.
- Has five passing unit tests for configuration loading, request construction, bounds calculation, conversion, and pipeline order.

The checked-in output directory contains an example for the configured Mexico City area. Its current metadata reports a 1009 × 1009 heightmap. Generated data may need to be regenerated when the configuration or pipeline changes.

## Requirements

- Python 3.11.9 is the version currently tested.
- Python packages: `numpy` and `rasterio`. `requests` is optional; the downloader has a standard-library HTTP fallback.
- Network access and a valid OpenTopography API key are needed to download a DEM. Conversion and tests can be run with an existing DEM without making a DEM request.

Install the packages in your Python environment:

```powershell
python -m pip install numpy rasterio requests
```

Set the API key in the current PowerShell session before running the downloader:

```powershell
$env:OPENTOPOGRAPHY_API_KEY = "your-key"
```

Do not commit API keys or other credentials. The downloader also contains a machine-specific fallback key-file path; that fallback should be configured or removed as part of making the project portable.

## Configure and run

Edit `terrain_config.json` to select the area:

```json
{
  "dem_center_lat": 19.4326,
  "dem_center_lon": -99.1332,
  "dem_radius_km": 10.0
}
```

Run the end-to-end pipeline from the project directory:

```powershell
python TerrainGenerator.py
```

The current script writes the DEM, heightmap, and metadata into `output\`. Its output paths are currently hard-coded in `TerrainGenerator.py`, so running it in another location may require updating those paths first.

## Generated files

- `output\mexico_terrain.tif` — downloaded source elevation model.
- `output\mexico_terrain_heightmap.png` — 16-bit grayscale height samples.
- `output\mexico_terrain_heightmap_metadata.json` — dimensions, CRS, sample spacing, elevation range, and encoding details.

The PNG maps the source elevation range linearly: pixel value `0` represents the reported minimum elevation and `65535` represents the maximum. Use the metadata when configuring vertical terrain scale in an engine; the correct engine-specific scale/import settings have not yet been implemented or verified.

## Tests

Run the current unit tests with:

```powershell
python -m unittest -v test_terrain_pipeline.py
```

The tests cover the Python data pipeline only. They do not test importing or rendering a terrain in Unreal Engine or Unity.

## Repository guide

- `TerrainGenerator.py` — pipeline entry point and configuration loading.
- `opentopography_api.py` — DEM request and download.
- `heightmap.py` — GeoTIFF reprojection, resampling, heightmap, and metadata generation.
- `terrain_config.json` — current area settings.
- `test_terrain_pipeline.py` — Python unit tests.
- `output\` — sample generated terrain data.

