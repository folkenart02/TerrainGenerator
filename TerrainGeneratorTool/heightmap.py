import json
import os


def convert_dem_to_heightmap(dem_path, heightmap_path, latitude, longitude):
    try:
        import numpy as np
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.fill import fillnodata
        from rasterio.transform import from_origin
        from rasterio.warp import reproject, transform_bounds
    except ImportError as error:
        raise ImportError(
            "GeoTIFF conversion requires Rasterio. Install it with: "
            "python -m pip install rasterio"
        ) from error

    supported_sizes = (127, 253, 505, 1009, 2017, 4033, 8129)
    output_directory = os.path.dirname(os.path.abspath(os.fspath(heightmap_path)))
    os.makedirs(output_directory, exist_ok=True)

    with rasterio.open(dem_path) as source:
        if source.crs is None:
            raise ValueError("The GeoTIFF has no coordinate reference system.")

        heightmap_size = next(
            (size for size in supported_sizes if size >= max(source.width, source.height)),
            None,
        )
        if heightmap_size is None:
            raise ValueError(
                "The DEM is too large for one Landscape heightmap. Split it into tiles first."
            )

        utm_zone = max(1, min(60, int((longitude + 180) // 6) + 1))
        epsg_code = (32600 if latitude >= 0 else 32700) + utm_zone
        destination_crs = f"EPSG:{epsg_code}"
        left, bottom, right, top = transform_bounds(
            source.crs,
            destination_crs,
            *source.bounds,
            densify_pts=21,
        )
        square_span = max(right - left, top - bottom)
        center_x = (left + right) / 2
        center_y = (bottom + top) / 2
        left = center_x - square_span / 2
        top = center_y + square_span / 2
        pixel_spacing = square_span / (heightmap_size - 1)
        destination_transform = from_origin(left, top, pixel_spacing, pixel_spacing)

        source_data = source.read(1, masked=True).filled(np.nan).astype(np.float32)
        elevations = np.full(
            (heightmap_size, heightmap_size), np.nan, dtype=np.float32
        )
        reproject(
            source=source_data,
            destination=elevations,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=np.nan,
            dst_transform=destination_transform,
            dst_crs=destination_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )

        valid_cells = np.isfinite(elevations)
        if not valid_cells.any():
            raise ValueError("The DEM contains no valid elevation samples.")
        if not valid_cells.all():
            elevations = fillnodata(
                elevations,
                mask=valid_cells.astype(np.uint8),
                max_search_distance=heightmap_size,
                smoothing_iterations=0,
            )
        if not np.isfinite(elevations).all():
            raise ValueError("The DEM contains gaps too large to fill for a heightmap.")

        minimum_elevation = float(elevations.min())
        maximum_elevation = float(elevations.max())
        elevation_range = maximum_elevation - minimum_elevation
        if elevation_range <= 0:
            raise ValueError("The DEM has no elevation range to convert.")

        height_values = np.rint(
            (elevations - minimum_elevation) * (65535.0 / elevation_range)
        ).clip(0, 65535).astype(np.uint16)

    heightmap_path = os.path.abspath(os.fspath(heightmap_path))
    with rasterio.open(
        heightmap_path,
        "w",
        driver="PNG",
        width=heightmap_size,
        height=heightmap_size,
        count=1,
        dtype="uint16",
    ) as output:
        output.write(height_values, 1)

    metadata_path = os.path.splitext(heightmap_path)[0] + "_metadata.json"
    metadata = {
        "source_dem": os.path.abspath(os.fspath(dem_path)),
        "heightmap": heightmap_path,
        "width_samples": heightmap_size,
        "height_samples": heightmap_size,
        "crs": destination_crs,
        "sample_spacing_m": pixel_spacing,
        "minimum_elevation_m": minimum_elevation,
        "maximum_elevation_m": maximum_elevation,
        "encoding": "uint16: 0 is minimum_elevation_m; 65535 is maximum_elevation_m",
    }
    with open(metadata_path, "w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)

    return heightmap_path