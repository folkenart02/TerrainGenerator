# Project Requirements and Progress

## 1. Purpose

Build a terrain-generation workflow that turns geographic elevation data into usable terrain in a game engine. The original project scope is to use Unreal Engine's terrain tools with a generated heightmap, and also to make a working version for Unity.

The intended pipeline is:

**Area settings → DEM acquisition → heightmap preparation → engine terrain**

The Python prototype currently implements the first three steps. Engine-specific terrain creation/import is still outstanding.

## 2. Scope

### In scope

- Specify an area by center latitude, center longitude, and radius.
- Retrieve elevation data from OpenTopography.
- Convert downloaded elevation data into a square 16-bit grayscale PNG suitable as a heightmap source.
- Preserve key geographic/elevation information in metadata so engine import and terrain scaling can be configured.
- Support an Unreal Engine terrain workflow using the generated heightmap.
- Provide a working Unity terrain workflow using the same source terrain data or a documented compatible export.
- Keep the acquisition/conversion stage independent of either game engine where practical.

### Out of scope for the current prototype

- A graphical user interface or in-engine editor tool.
- Automatic material, foliage, roads, water, or biome generation.
- Runtime streaming, terrain tiling, or very large world support.
- FBX/USD export; these were considered possible future alternatives, not current requirements.
- A finished Unreal or Unity integration; neither is present in the current project.

## 3. Required environment and access

To run the prototype successfully, the machine must have:

- Python 3.11.x installed.
- The `numpy` and `rasterio` packages installed in the active Python environment.
- `requests` installed only if you want the downloader to use the optional requests-based HTTP client; otherwise the standard library fallback is used.
- Network access to the public OpenTopography API endpoints.
- An OpenTopography account with a valid API key.
- A value for `OPENTOPOGRAPHY_API_KEY` in the environment, or a valid key file location configured for the script.

Install the required Python packages:

```powershell
python -m pip install numpy rasterio requests
```

Set the API key in the current shell before running the downloader:

```powershell
$env:OPENTOPOGRAPHY_API_KEY = "your-key"
```

If you do not want to set the environment variable, the script also checks a machine-specific key-file fallback path in `opentopography_api.py`. That fallback is not portable and should be replaced with a project-relative or user-specific configuration before using the project on another machine.

To get an API key, create an account on OpenTopography and generate a personal API key from the portal. The downloaded DEM request will fail without a valid key.

## 4. Current implementation and project stage

The project is currently a Python-only terrain-generation prototype. The script loads the configured target area, requests a DEM from OpenTopography using a valid API key, converts that DEM into a square 16-bit grayscale heightmap, and writes companion metadata describing the elevation range and sample spacing. In the repository, `TerrainGenerator.py` orchestrates the pipeline, `opentopography_api.py` handles the DEM request and geographic bounds, and `heightmap.py` handles reprojection, resampling, PNG export, and metadata generation. The sample output in `output\` already contains a generated Mexico City heightmap, so the pipeline has been validated on the current configuration.

Unreal and Unity integration work is still not implemented or tested in this repository. The current prototype does not yet include a reproducible in-engine terrain import workflow, engine-specific scale settings, or a Unity project. The code still includes machine-specific output and API-key fallback paths that need to be made portable before the project can be used cleanly on another machine.

