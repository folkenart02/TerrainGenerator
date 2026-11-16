import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

import numpy as np
import rasterio
from rasterio.transform import from_origin

import heightmap
import opentopography_api
import TerrainGenerator as runner


class TerrainPipelineTests(unittest.TestCase):
    def test_load_terrain_config_reads_numeric_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "terrain.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dem_center_lat": 19.4326,
                        "dem_center_lon": -99.1332,
                        "dem_radius_km": 10,
                    }
                ),
                encoding="utf-8",
            )

            settings = runner.load_terrain_config(config_path)

        self.assertEqual(settings["dem_center_lat"], 19.4326)
        self.assertEqual(settings["dem_center_lon"], -99.1332)
        self.assertEqual(settings["dem_radius_km"], 10.0)

    def test_bounds_for_radius_produces_requested_square_extent(self):
        south, north, west, east = opentopography_api.bounds_for_radius(
            19.4, -99.1, 1.0
        )

        self.assertAlmostEqual(north - south, 2.0 / 111.32)
        self.assertAlmostEqual(
            east - west,
            2.0 / (111.32 * np.cos(np.radians(19.4))),
        )

    def test_download_dem_writes_geotiff_and_builds_request(self):
        fake_response = io.BytesIO(b"II*\x00mock-geotiff")
        fake_response.__enter__ = lambda: fake_response
        fake_response.__exit__ = lambda *args: False

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "dem.tif"
            with mock.patch.object(opentopography_api, "requests", None):
                with mock.patch.object(
                    opentopography_api.urllib.request,
                    "urlopen",
                    return_value=fake_response,
                ) as urlopen:
                    result = opentopography_api.download_dem(
                        19.4,
                        -99.1,
                        1.0,
                        output_path,
                        dataset="COP30",
                        api_key="test-key",
                    )

            query = parse_qs(urlparse(urlopen.call_args.args[0]).query)
            self.assertEqual(query["demtype"], ["COP30"])
            self.assertEqual(query["API_Key"], ["test-key"])
            self.assertEqual(Path(result).read_bytes(), b"II*\x00mock-geotiff")

    def test_convert_dem_writes_16_bit_landscape_png_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            dem_path = Path(directory) / "synthetic.tif"
            heightmap_path = Path(directory) / "heightmap.png"
            elevations = np.arange(64, dtype=np.float32).reshape((8, 8))
            with rasterio.open(
                dem_path,
                "w",
                driver="GTiff",
                width=8,
                height=8,
                count=1,
                dtype="float32",
                crs="EPSG:4326",
                transform=from_origin(-99.1, 19.5, 0.001, 0.001),
            ) as dem:
                dem.write(elevations, 1)

            result = heightmap.convert_dem_to_heightmap(
                dem_path, heightmap_path, 19.4, -99.1
            )

            with rasterio.open(result) as png:
                pixels = png.read(1)
                self.assertEqual(png.driver, "PNG")
                self.assertEqual(png.dtypes, ("uint16",))
                self.assertEqual((png.width, png.height), (127, 127))
                self.assertEqual(int(pixels.min()), 0)
                self.assertEqual(int(pixels.max()), 65535)

            metadata_path = heightmap_path.with_name("heightmap_metadata.json")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertLess(
                metadata["minimum_elevation_m"], metadata["maximum_elevation_m"]
            )
            self.assertEqual(metadata["width_samples"], 127)

    def test_runner_calls_download_then_heightmap_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "terrain.json"
            config_path.write_text(
                json.dumps(
                    {
                        "dem_center_lat": 19.4,
                        "dem_center_lon": -99.1,
                        "dem_radius_km": 1.0,
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                runner.opentopography_api,
                "download_dem",
                return_value="dem.tif",
            ) as download:
                with mock.patch.object(
                    runner.heightmap,
                    "convert_dem_to_heightmap",
                    return_value="heightmap.png",
                ) as convert:
                    result = runner.run_pipeline(config_path)

        self.assertEqual(result, ("dem.tif", "heightmap.png"))
        download.assert_called_once_with(
            19.4,
            -99.1,
            1.0,
            runner.DEM_OUTPUT_PATH,
            dataset=runner.DEM_DATASET,
        )
        convert.assert_called_once_with(
            "dem.tif",
            runner.HEIGHTMAP_OUTPUT_PATH,
            19.4,
            -99.1,
        )


if __name__ == "__main__":
    unittest.main()
