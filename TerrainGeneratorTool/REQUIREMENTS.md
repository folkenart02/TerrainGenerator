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

## 3. Functional requirements

| ID | Requirement | Status |
|---|---|---|
| FR-01 | Read center latitude, center longitude, and radius from a JSON configuration file. | Implemented |
| FR-02 | Validate numeric settings and geographic bounds before constructing a radius-based request. | Partially implemented: values are checked for numeric type; geographic and radius constraints are checked when calculating bounds. |
| FR-03 | Download a GeoTIFF DEM from OpenTopography using a configured dataset and API key. | Implemented |
| FR-04 | Reproject DEM elevation data and resample it to a supported square heightmap size. | Implemented |
| FR-05 | Write a 16-bit grayscale PNG whose normalized values map the elevation minimum to 0 and maximum to 65535. | Implemented |
| FR-06 | Write companion metadata containing dimensions, CRS, sample spacing, elevation range, and encoding. | Implemented |
| FR-07 | Import the generated heightmap into an Unreal Engine Landscape and provide correct horizontal/vertical scale guidance. | Not implemented or engine-validated |
| FR-08 | Provide a working Unity terrain path, including heightmap import and correct terrain dimensions/elevation scaling. | Not implemented or engine-validated |
| FR-09 | Provide clear actionable errors for invalid input, missing credentials, failed downloads, and unsupported or invalid DEM data. | Implemented in the Python pipeline; engine error handling remains undefined |
| FR-10 | Make configuration and output locations usable on other machines without editing machine-specific source paths. | Not yet implemented; output and fallback key-file paths are currently machine-specific |

## 4. Non-functional requirements

- Preserve enough elevation precision for terrain import by using 16-bit height values.
- Keep metadata alongside each generated heightmap to retain its elevation range and sample spacing.
- Do not store API credentials in source control or generated documentation.
- Verify pipeline behavior with automated tests and separately verify engine import in each target engine.
- Document tested Python and engine versions as engine integrations are added.

## 5. Current implementation and project stage

**Current stage: Python pipeline prototype; Unreal/Unity integration phase has not started.**

Implemented in the repository:

- `TerrainGenerator.py` loads the JSON settings and runs download followed by conversion.
- `opentopography_api.py` calculates geographic bounds and downloads a GeoTIFF from OpenTopography's Global DEM API.
- `heightmap.py` reprojects the DEM into a local UTM CRS, fills missing samples, resamples to a supported square size, writes a 16-bit PNG, and writes metadata.
- `test_terrain_pipeline.py` tests the configuration, bounds, download request, conversion output, and pipeline sequence.
- The project is currently tested with Python 3.11.9. The current unit test suite passes five tests.
- Existing sample outputs in `output\` include a 1009 × 1009 PNG heightmap for the configured area near Mexico City.

Not implemented or verified:

- Unreal project setup and repeatable Landscape import instructions.
- Unreal Landscape component/layout choices, vertical scale calculation, and visual validation.
- Unity project setup, terrain creation/import, vertical and horizontal scale mapping, and visual validation.
- Portable configuration for output paths and the OpenTopography key-file fallback.
- A documented strategy for areas that exceed the size supported by one generated heightmap.

## 6. Engine-specific requirements

### Unreal Engine

The Unreal milestone should demonstrate that a generated heightmap can be imported with the engine's terrain tools to create a Landscape. It should document the tested Unreal version, supported heightmap dimensions, Landscape component settings, horizontal scale, and how the metadata's elevation range is used to set vertical scale. The pipeline currently writes a PNG, but a successful engine import has not been demonstrated by this repository.

### Unity

The Unity milestone should demonstrate terrain creation from generated elevation data in a Unity project. It should document the tested Unity version, any required conversion/import format, heightmap resolution constraints, terrain dimensions, and how minimum/maximum elevation and sample spacing map to Unity terrain size and height. No Unity-specific code or project is currently present.

The implementations should use consistent geographic input and elevation meaning. The exact sharing strategy (same PNG, an intermediate format, or engine-specific exports) remains to be decided and validated during the engine integration work.

## 7. Acceptance criteria

The Python pipeline milestone is accepted when:

- A valid configuration produces a GeoTIFF, a 16-bit grayscale PNG, and a metadata JSON.
- Invalid configuration, missing credentials, invalid DEM data, and unsupported output dimensions report a useful error rather than silently producing success.
- Automated tests cover configuration, download request setup, conversion properties, and pipeline order.

The Unreal milestone is accepted when:

- A documented, reproducible import workflow creates a Landscape from a generated heightmap.
- Terrain dimensions and elevation scaling can be reconstructed from configuration and metadata.
- The workflow is tested in a named Unreal Engine version and produces a visually inspected terrain.

The Unity milestone is accepted when:

- A documented, reproducible workflow creates a Unity Terrain from generated elevation data.
- Terrain dimensions and elevation scaling can be reconstructed from configuration and metadata.
- The workflow is tested in a named Unity version and produces a visually inspected terrain.

## 8. Suggested next steps

1. Make API key and output path configuration portable, then document a clean setup on a second machine.
2. Choose and test the Unreal Engine version and Landscape import settings; verify dimensions and elevation scaling using the metadata.
3. Choose and test the Unity version and a heightmap import workflow with equivalent terrain dimensions and elevation scale.
4. Add engine-level validation steps or small integration tests/examples for both workflows.
5. Decide how to handle oversized areas (reject clearly, split into tiles, or allow configurable output resolution).
