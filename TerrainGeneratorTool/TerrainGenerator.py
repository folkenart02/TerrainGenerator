"This is Terrain Generator v.01 a tool designed to generate an environment object in unreal"
"There may be an update on fbx or usd, for different use cases"

import json
import os

import heightmap
import opentopography_api


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terrain_config.json")
DEM_DATASET = "COP30"
DEM_OUTPUT_PATH = r"F:\Unreal_Python\TerrainGeneratorTool\output\mexico_terrain.tif"
HEIGHTMAP_OUTPUT_PATH = r"F:\Unreal_Python\TerrainGeneratorTool\output\mexico_terrain_heightmap.png"
def load_terrain_config(config_path=CONFIG_PATH):
    try:
        with open(config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not load terrain settings from {config_path}: {error}") from error

    if not isinstance(config, dict):
        raise ValueError("Terrain settings must be a JSON object.")

    required_settings = ("dem_center_lat", "dem_center_lon", "dem_radius_km")
    for setting in required_settings:
        value = config.get(setting)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Terrain setting '{setting}' must be a number.")

    return {
        setting: float(config[setting])
        for setting in required_settings
    }


def run_pipeline(config_path=CONFIG_PATH):
    terrain_config = load_terrain_config(config_path)
    center_lat = terrain_config["dem_center_lat"]
    center_lon = terrain_config["dem_center_lon"]
    radius_km = terrain_config["dem_radius_km"]

    dem_path = opentopography_api.download_dem(
        center_lat,
        center_lon,
        radius_km,
        DEM_OUTPUT_PATH,
        dataset=DEM_DATASET,
    )
    heightmap_path = heightmap.convert_dem_to_heightmap(
        dem_path,
        HEIGHTMAP_OUTPUT_PATH,
        center_lat,
        center_lon,
    )
    return dem_path, heightmap_path


if __name__ == "__main__":
    try:
        dem_path, heightmap_path = run_pipeline()
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(f"DEM downloaded to: {dem_path}")
    print(f"Unreal heightmap saved to: {heightmap_path}")

