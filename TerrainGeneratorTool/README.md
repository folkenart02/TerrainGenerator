# Terrain Generator Tool

This project generates terrain height data from real-world geographic elevation sources and turns it into a usable heightmap for downstream workflows. The original intention was an Unreal Engine archviz workflow: build a real-world terrain base from DEM data and then import it into Unreal for visualization, environment blocking, or concept presentation. The same output is also useful for any workflow that needs accurate ground height information from real-world terrain data, not only Unreal.

## What this project does

The tool takes a center latitude, center longitude, and radius, downloads a DEM from OpenTopography, and converts it into a square grayscale heightmap with supporting metadata. The metadata includes the output dimensions, sample spacing, and the elevation range used to map the height values. In other words, the script turns real geographic elevation data into a heightmap that can be imported into tools that expect a normalized terrain surface.

This is most directly useful for Unreal Engine archviz work, where a realistic terrain base can be used as a starting point for environment design, site studies, or visualizations. The process is still generic enough to serve other workflows that need real-world elevation data, such as terrain generation in other engines, GIS-driven modeling, or any project that needs a heightmap derived from actual ground samples.

## How it works

The workflow is straightforward:

1. A target area is defined in `terrain_config.json` using latitude, longitude, and radius.
2. The script requests a DEM from OpenTopography using the configured dataset and a valid API key.
3. The DEM is reprojected and resampled into a square heightmap.
4. A 16-bit PNG is written alongside metadata describing the terrain's source elevation range and sample spacing.
5. That output can then be used for downstream terrain import or further processing in a target engine or environment.

At the moment, the implementation is a Python prototype for the acquisition and conversion stages. It does not yet include a full Unreal project, a Unity terrain pipeline, or a verified engine import workflow.

## What you need to run it

To run the prototype successfully, the machine needs Python 3.11.x, the required Python libraries, network access, and a valid OpenTopography API key. The required packages are installed with:

```powershell
python -m pip install numpy rasterio requests
```

Then set the OpenTopography API key in the current shell before running the downloader:

```powershell
$env:OPENTOPOGRAPHY_API_KEY = "your-key"
```

The script also contains a machine-specific fallback key-file path that should be replaced or configured before moving the project to another machine. Do not commit API keys or other credentials into the repository.

## Configure and run

Edit `terrain_config.json` to choose the target area:

```json
{
  "dem_center_lat": 19.4326,
  "dem_center_lon": -99.1332,
  "dem_radius_km": 10.0
}
```

Then run the pipeline from the project directory:

```powershell
python TerrainGenerator.py
```

The current script writes the output into `output\`. Those paths are still hard-coded in the script, so running the project from a different machine or location may require updating them first.

## Current project stage

This is currently a Python-only prototype focused on the data acquisition and heightmap conversion pipeline. It successfully loads the configuration, downloads a DEM, processes it into a square 16-bit terrain heightmap, and writes metadata for the generated output. The checked-in `output\` folder contains an example heightmap for the configured Mexico City area.

The project is still intended primarily for Unreal Engine archviz work, but the same generated terrain data can also be useful in other scenarios that need real-world height information. Engine-specific import workflows, scale calibration, and final integration steps remain future work.

## Project structure

The project is intentionally organized as a modular script, with each part of the workflow kept in a separate module:

- `TerrainGenerator.py` loads the configuration and orchestrates the pipeline.
- `opentopography_api.py` handles DEM requests and downloads.
- `heightmap.py` handles reprojection, resampling, and heightmap/metadata generation.
- `terrain_config.json` stores the current target area.
- `output\` contains example generated terrain assets.

Keep this modular structure as the project grows. New data sources, export formats, engine integrations, or other applications should be added as separate components around the shared terrain-processing workflow, rather than combining unrelated responsibilities into one script. This makes it easier to reuse the real-world height data pipeline for future workflows while keeping existing behavior maintainable.
