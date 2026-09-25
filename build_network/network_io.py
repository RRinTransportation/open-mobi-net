import os
import json
import subprocess
from datetime import datetime
from importlib import metadata as importlib_metadata

import numpy as np
import pandas as pd
import geopandas as gpd


FORMAT_VERSION = 1
GPKG_NAME = "network.gpkg"
METADATA_NAME = "metadata.json"
INDEX_PREFIX = "__index__"

# Known defects of the building pipeline that affect the content of a saved network.
# Keep this list up to date when they are fixed, so that old saved networks can be identified and rebuilt.
KNOWN_UNFIXED_ISSUES = [
    "OBS-03: public transport links/stops are clipped with the study area boundary (exterior) instead of its surface",
    "OBS-04: missing car speeds are not filled before capacity estimation",
]


def save_network(layers: dict, path: str, parameters: dict = None, overwrite: bool = False) -> str:
    """ Save a dictionary of GeoDataFrames {layer_name: gdf} as a GeoPackage (one layer per GeoDataFrame)
    and write a metadata.json file (format version, date, git commit, parameters, CRS and schema of each layer).

    List columns (e.g. 'NEIGHBORS', 'CONTAINS', 'path_link_id') are stored as JSON strings and restored by load_network.
    Empty layers are not written in the GeoPackage but described in the metadata, and recreated empty by load_network.
    """
    gpkg_path = os.path.join(path, GPKG_NAME)
    if os.path.exists(gpkg_path):
        if not overwrite:
            raise FileExistsError(f"A network is already saved in {path}. Use overwrite=True or choose another path.")
        os.remove(gpkg_path)
    os.makedirs(path, exist_ok=True)

    layers_metadata = {}
    for name, gdf in layers.items():
        if gdf is None:
            continue
        gdf_to_save, layer_metadata = _prepare_layer(gdf)
        if not layer_metadata['empty']:
            # promote_to_multi=False: keep LineString and MultiLineString as they are when a layer mixes both (e.g. after clip)
            gdf_to_save.to_file(gpkg_path, layer=name, driver="GPKG", promote_to_multi=False)
        layers_metadata[name] = layer_metadata

    network_metadata = {
        'format_version': FORMAT_VERSION,
        'created': datetime.now().isoformat(timespec='seconds'),
        'git': _get_git_state(),
        'library_versions': _get_library_versions(),
        'known_unfixed_issues': KNOWN_UNFIXED_ISSUES,
        'parameters': parameters if parameters is not None else {},
        'layers': layers_metadata,
    }
    with open(os.path.join(path, METADATA_NAME), 'w', encoding='utf-8') as f:
        json.dump(network_metadata, f, indent=2, ensure_ascii=False, default=_to_builtin)

    return path


def load_network(path: str):
    """ Load a network saved with save_network. Return ({layer_name: gdf}, metadata)."""
    with open(os.path.join(path, METADATA_NAME), encoding='utf-8') as f:
        network_metadata = json.load(f)
    if network_metadata['format_version'] > FORMAT_VERSION:
        raise ValueError(f"Network saved with format version {network_metadata['format_version']}, "
                         f"but this code only reads up to version {FORMAT_VERSION}.")

    gpkg_path = os.path.join(path, GPKG_NAME)
    layers = {}
    for name, layer_metadata in network_metadata['layers'].items():
        if layer_metadata['empty']:
            layers[name] = _empty_layer(layer_metadata)
        else:
            layers[name] = _restore_layer(gpd.read_file(gpkg_path, layer=name), layer_metadata)
    return layers, network_metadata


# ------------------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------------------

def _geometry_name(gdf):
    """ Name of the active geometry column, or None (e.g. for an empty gpd.GeoDataFrame())."""
    try:
        return gdf.geometry.name
    except AttributeError:
        return None


def _prepare_layer(gdf):
    """ Convert a GeoDataFrame into something writable in a GeoPackage, and describe how to restore it."""
    geometry_name = _geometry_name(gdf)
    layer_metadata = {
        'crs': gdf.crs.to_string() if geometry_name is not None and gdf.crs is not None else None,
        'n_rows': len(gdf),
        'geometry_column': geometry_name,
        'columns': [str(c) for c in gdf.columns],  # Full column order, geometry included
        'index_names': list(gdf.index.names),
        'list_columns': [],
        'empty': len(gdf) == 0 or geometry_name is None,
    }
    if layer_metadata['empty']:
        return gdf, layer_metadata

    # --- Keep the index as columns, to restore it identically:
    index_columns = [f"{INDEX_PREFIX}{k}" for k in range(gdf.index.nlevels)]
    gdf = gdf.copy()
    gdf.index = gdf.index.set_names(index_columns)
    gdf = gdf.reset_index()

    for column in gdf.columns:
        if column == geometry_name or gdf[column].dtype != object:
            continue
        values = gdf[column].dropna()
        # List columns -> JSON strings:
        if values.map(lambda x: isinstance(x, (list, tuple, set, np.ndarray))).any():
            gdf[column] = gdf[column].map(lambda x: json.dumps(_to_builtin(x)) if isinstance(x, (list, tuple, set, np.ndarray)) else None)
            if not column.startswith(INDEX_PREFIX):
                layer_metadata['list_columns'].append(column)
        # Object columns mixing numbers and None (e.g. 'capacity_ab') -> numeric:
        elif len(values) > 0 and values.map(lambda x: isinstance(x, (int, float, np.number)) and not isinstance(x, (bool, np.bool_))).all():
            gdf[column] = pd.to_numeric(gdf[column])
        # Object columns of booleans (e.g. 'added_lane') -> bool, or float if some values are missing:
        elif len(values) > 0 and values.map(lambda x: isinstance(x, (bool, np.bool_))).all():
            gdf[column] = gdf[column].astype(bool) if len(values) == len(gdf) else gdf[column].astype(float)

    return gdf, layer_metadata


def _restore_layer(gdf, layer_metadata):
    """ Inverse of _prepare_layer."""
    for column in layer_metadata['list_columns']:
        gdf[column] = gdf[column].map(lambda x: json.loads(x) if isinstance(x, str) else None)

    index_columns = [c for c in gdf.columns if c.startswith(INDEX_PREFIX)]
    if index_columns:
        gdf = gdf.set_index(index_columns)
        gdf.index = gdf.index.set_names(layer_metadata['index_names'])

    geometry_name = layer_metadata['geometry_column']
    if geometry_name is not None and gdf.geometry.name != geometry_name:
        gdf = gdf.rename_geometry(geometry_name)
    return gdf[layer_metadata['columns']]


def _empty_layer(layer_metadata):
    geometry_name = layer_metadata['geometry_column']
    if geometry_name is None:
        return gpd.GeoDataFrame(columns=layer_metadata['columns'])
    return gpd.GeoDataFrame(columns=layer_metadata['columns'],
                            geometry=geometry_name,
                            crs=layer_metadata['crs'])


def _to_builtin(x):
    """ Convert numpy objects (and containers of them) to JSON-serializable python objects."""
    if isinstance(x, (list, tuple, set, np.ndarray)):
        return [_to_builtin(v) for v in x]
    if isinstance(x, dict):
        return {k: _to_builtin(v) for k, v in x.items()}
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def _get_git_state():
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True, check=True).stdout.strip() != ""
        return {'commit': commit, 'uncommitted_changes': dirty}
    except (OSError, subprocess.CalledProcessError):
        return {'commit': None, 'uncommitted_changes': None}


def _get_library_versions():
    versions = {}
    for library in ['geopandas', 'pandas', 'shapely', 'pyogrio', 'aequilibrae']:
        try:
            versions[library] = importlib_metadata.version(library)
        except importlib_metadata.PackageNotFoundError:
            versions[library] = None
    return versions
