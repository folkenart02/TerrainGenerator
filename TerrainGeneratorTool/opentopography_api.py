try:
    import requests
except Exception:
    requests = None

import json
import math
import os
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request


OPENTOPOGRAPHY_API_KEY_FILE = r"F:\Unreal_Python\TerrainGeneratorTool\Api key"
OPENTOPOGRAPHY_DEM_URL = "https://portal.opentopography.org/API/globaldem"


def _http_get_json(url, params=None, timeout=10):
    params = params or {}
    if requests is not None:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    query = urllib.parse.urlencode(params)
    full_url = url + ("?" + query if query else "")
    with urllib.request.urlopen(full_url, timeout=timeout) as response:
        return json.load(response)


def get_elevation(latitude, longitude, dataset="aster30m"):
    url = "https://api.opentopodata.org/v1/" + dataset
    params = {"locations": f"{latitude},{longitude}"}
    data = _http_get_json(url, params=params)
    return data["results"][0]["elevation"]


def bounds_for_radius(latitude, longitude, radius_km):
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees.")
    if radius_km <= 0:
        raise ValueError("Radius must be greater than zero.")

    latitude_delta = radius_km / 111.32
    longitude_scale = math.cos(math.radians(latitude))
    if longitude_scale < 1e-6:
        raise ValueError("A radius-based bounding box is not supported near the poles.")
    longitude_delta = radius_km / (111.32 * longitude_scale)

    south = latitude - latitude_delta
    north = latitude + latitude_delta
    west = longitude - longitude_delta
    east = longitude + longitude_delta
    if south < -90 or north > 90 or west < -180 or east > 180:
        raise ValueError("The requested radius crosses a latitude or longitude boundary.")

    return south, north, west, east


def download_dem(latitude, longitude, radius_km, output_path, dataset="COP30", api_key=None):
    api_key = api_key or os.environ.get("OPENTOPOGRAPHY_API_KEY")
    if not api_key:
        try:
            with open(OPENTOPOGRAPHY_API_KEY_FILE, encoding="utf-8-sig") as key_file:
                api_key = key_file.read().strip()
        except OSError as error:
            raise ValueError(
                "Could not read the OpenTopography key file. Set "
                "OPENTOPOGRAPHY_API_KEY_FILE to its location or set the "
                "OPENTOPOGRAPHY_API_KEY environment variable."
            ) from error
    if not api_key:
        raise ValueError("The OpenTopography API key file is empty.")

    south, north, west, east = bounds_for_radius(latitude, longitude, radius_km)
    params = {
        "demtype": dataset,
        "south": south,
        "north": north,
        "west": west,
        "east": east,
        "outputFormat": "GTiff",
        "API_Key": api_key,
    }

    output_path = os.path.abspath(os.fspath(output_path))
    output_directory = os.path.dirname(output_path)
    os.makedirs(output_directory, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=output_directory, suffix=".tif")
    os.close(temp_fd)

    try:
        if requests is not None:
            response = None
            try:
                response = requests.get(
                    OPENTOPOGRAPHY_DEM_URL,
                    params=params,
                    timeout=120,
                    stream=True,
                )
                if response.status_code >= 400:
                    response_detail = response.text[:500].replace(api_key, "[REDACTED]")
                    raise RuntimeError(
                        f"OpenTopography returned HTTP {response.status_code}: "
                        f"{response_detail or response.reason}"
                    )
                with open(temp_path, "wb") as dem_file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            dem_file.write(chunk)
            except RuntimeError:
                raise
            except Exception as error:
                detail = str(error).replace(api_key, "[REDACTED]")
                raise RuntimeError(
                    f"DEM request failed ({type(error).__name__}): {detail}"
                ) from error
            finally:
                if response is not None:
                    response.close()
        else:
            request_url = OPENTOPOGRAPHY_DEM_URL + "?" + urllib.parse.urlencode(params)
            try:
                with urllib.request.urlopen(request_url, timeout=120) as response:
                    with open(temp_path, "wb") as dem_file:
                        shutil.copyfileobj(response, dem_file)
            except urllib.error.HTTPError as error:
                response_detail = error.read(500).decode("utf-8", errors="replace")
                response_detail = response_detail.replace(api_key, "[REDACTED]")
                raise RuntimeError(
                    f"OpenTopography returned HTTP {error.code}: "
                    f"{response_detail or error.reason}"
                ) from error
            except Exception as error:
                detail = str(error).replace(api_key, "[REDACTED]")
                raise RuntimeError(
                    f"DEM request failed ({type(error).__name__}): {detail}"
                ) from error

        with open(temp_path, "rb") as dem_file:
            response_content = dem_file.read(500)
        signature = response_content[:4]
        if signature not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            response_detail = response_content.decode("utf-8", errors="replace")
            response_detail = response_detail.replace(api_key, "[REDACTED]").strip()
            raise RuntimeError(
                "OpenTopography did not return a valid GeoTIFF. "
                f"Response: {response_detail[:300]}"
            )

        os.replace(temp_path, output_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return output_path