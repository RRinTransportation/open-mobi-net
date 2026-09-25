""" Round-trip tests of network saving / loading, on small synthetic GeoDataFrames (no network access needed).

Run from the root of the repository:
    python tests/test_network_io.py
(also compatible with pytest)
"""
import os
import sys
import socket
import subprocess
import tempfile
from types import SimpleNamespace

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString, Polygon

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from build_network.network_io import save_network, load_network
from build_network.MultiModalNetwork import MultiModalNetwork
from config.Lyon_multimodal import args
from utils.filtering import filter_args


# ------------------------------------------------------------------------------------------------
# Synthetic layers
# ------------------------------------------------------------------------------------------------

def make_zones():
    """ Polygons in Lambert-93, index named 'DCOMIRIS', list columns (like aggregated IRIS zones)."""
    squares = [Polygon([(x, 0), (x + 100, 0), (x + 100, 100), (x, 100)]) for x in (0, 100, 200)]
    gdf = gpd.GeoDataFrame({'NOM_IRIS': ['A', 'B', 'C'],
                            'area': [0.01, 0.01, 0.01],
                            'NEIGHBORS': [[np.int64(2)], [np.int64(1), np.int64(3)], [np.int64(2)]],
                            'CONTAINS': [[1], [2], [3, 4]],
                            'geometry': squares},
                           index=pd.Index([1, 2, 3], name='DCOMIRIS', dtype='int64'),
                           crs='EPSG:2154')
    return gdf


def make_links():
    """ Lines in WGS84 with object columns mixing numbers and None, and booleans (like the preprocessed OSM links)."""
    lines = [LineString([(4.85, 45.76), (4.86, 45.77)]), LineString([(4.86, 45.77), (4.87, 45.77)])]
    gdf = gpd.GeoDataFrame({'link_id': [1, 2],
                            'modes': ['cbw', 'w'],
                            'lanes_ab': pd.Series([1, np.nan], dtype=object),
                            'capacity_ab': pd.Series([1000, None], dtype=object),
                            'added_lane': pd.Series([True, False], dtype=object),
                            'speed_ab': [30.0, np.nan],
                            'geometry': lines},
                           crs='EPSG:4326')
    return gdf


def make_pt_links():
    """ Lines in Lambert-93 with a list column of link ids (like final_pt_links)."""
    return gpd.GeoDataFrame({'sub_route_id': [10],
                             'line_name': ['C3'],
                             'geometry': [LineString([(0, 0), (50, 50)])],
                             'path_link_id': [[np.int64(1), np.int64(2), np.int64(3)]]},
                            crs='EPSG:2154')


def make_mixed_lines():
    """ LineString and MultiLineString (with Z) in the same layer, as produced by a clip of the bike network."""
    return gpd.GeoDataFrame({'link_id': [1, 2],
                             'geometry': [LineString([(4.85, 45.76, 170.0), (4.86, 45.77, 171.0)]),
                                          MultiLineString([[(4.85, 45.76, 1.0), (4.86, 45.77, 1.0)], [(4.87, 45.78, 1.0), (4.88, 45.79, 1.0)]])]},
                            crs='EPSG:4326')


def make_points():
    return gpd.GeoDataFrame({'node_id': [1, 2], 'geometry': [Point(4.85, 45.76), Point(4.86, 45.77)]}, crs='EPSG:4326')


# ------------------------------------------------------------------------------------------------
# Comparison
# ------------------------------------------------------------------------------------------------

def _same_value(a, b):
    if isinstance(a, (list, tuple, np.ndarray)) or isinstance(b, (list, tuple, np.ndarray)):
        return list(map(int, a)) == list(map(int, b))
    if pd.isna(a) and pd.isna(b):  # None and NaN are considered equivalent
        return True
    return a == b


def assert_same_layer(original, loaded, name):
    assert len(original) == len(loaded), f"{name}: {len(original)} rows saved, {len(loaded)} loaded"
    assert list(original.columns) == list(loaded.columns), f"{name}: columns differ {list(original.columns)} / {list(loaded.columns)}"
    if len(original) == 0:
        return
    assert original.crs == loaded.crs, f"{name}: CRS differ {original.crs} / {loaded.crs}"
    assert list(original.index.names) == list(loaded.index.names), f"{name}: index names differ"
    assert list(original.index) == list(loaded.index), f"{name}: index values differ"
    geometry_name = original.geometry.name
    assert original.geometry.geom_equals_exact(loaded.geometry, tolerance=1e-9).all(), f"{name}: geometries differ"
    assert list(original.geom_type) == list(loaded.geom_type), f"{name}: geometry types differ"
    for column in original.columns:
        if column == geometry_name:
            continue
        for a, b in zip(original[column], loaded[column]):
            assert _same_value(a, b), f"{name}.{column}: {a!r} saved, {b!r} loaded"


# ------------------------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------------------------

def test_round_trip_layers():
    layers = {'zones': make_zones(),
              'links': make_links(),
              'pt_links': make_pt_links(),
              'mixed_lines': make_mixed_lines(),
              'empty_without_geometry': gpd.GeoDataFrame(),
              'empty_with_geometry': make_points().iloc[0:0],
              'absent': None}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        save_network(layers, tmp, parameters={'city': 'test'})
        loaded, metadata = load_network(tmp)

    assert 'absent' not in loaded
    assert metadata['parameters'] == {'city': 'test'}
    assert metadata['layers']['zones']['list_columns'] == ['NEIGHBORS', 'CONTAINS']
    for name in ['zones', 'links', 'pt_links', 'mixed_lines', 'empty_with_geometry']:
        assert_same_layer(layers[name], loaded[name], name)
    assert len(loaded['empty_without_geometry']) == 0
    assert loaded['empty_with_geometry'].crs == 'EPSG:4326'


def test_no_silent_overwrite():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        save_network({'points': make_points()}, tmp)
        try:
            save_network({'points': make_points()}, tmp)
            raise AssertionError("Saving twice in the same folder should raise FileExistsError")
        except FileExistsError:
            pass
        save_network({'points': make_points().iloc[:1]}, tmp, overwrite=True)
        loaded, _ = load_network(tmp)
    assert len(loaded['points']) == 1


def test_multimodal_network_save_load_without_network_access():
    """ MultiModalNetwork.save() then MultiModalNetwork.load() on synthetic builders.
    Network access and subprocesses are forbidden during load()."""
    multi_modal_network = MultiModalNetwork(**filter_args(args, MultiModalNetwork))
    zones = make_zones()
    multi_modal_network.networkbuilder = SimpleNamespace(gdf=zones, study_area_polygon=zones.union_all())
    multi_modal_network.aequilibraebuilder = SimpleNamespace(links=make_links(), nodes=make_points(),
                                                             bike_lanes=make_links(), bike_nodes=make_points())
    multi_modal_network.gtfs_network_builder = SimpleNamespace(pt_links_inside=make_pt_links().drop(columns='path_link_id'),
                                                               pt_nodes_inside=make_points(),
                                                               final_matches=make_links(),
                                                               final_pt_links=make_pt_links())
    multi_modal_network.gdf_init_zones = zones.to_crs('EPSG:4326')
    multi_modal_network.gdf_agg_zones = zones.to_crs('EPSG:4326')
    multi_modal_network.drawn_polygon = gpd.GeoDataFrame(geometry=[zones.geometry.iloc[0]], crs='EPSG:2154')

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        multi_modal_network.save(tmp)

        # A new instance with a different configuration: saved parameters must be restored
        other = MultiModalNetwork(**filter_args(args, MultiModalNetwork))
        other.target_n_zones = 999

        def forbidden(*a, **k):
            raise AssertionError("load() must not access the network nor launch subprocesses")
        original_connect, original_popen = socket.socket.connect, subprocess.Popen
        socket.socket.connect, subprocess.Popen = forbidden, forbidden
        try:
            networkbuilder, aequilibraebuilder, gtfs_network_builder = other.load(tmp)
        finally:
            socket.socket.connect, subprocess.Popen = original_connect, original_popen

    assert other.target_n_zones == multi_modal_network.target_n_zones
    assert networkbuilder.study_area_polygon.equals(zones.union_all())
    assert aequilibraebuilder.traffic_network is aequilibraebuilder.links
    assert_same_layer(multi_modal_network.aequilibraebuilder.links, aequilibraebuilder.traffic_network, 'links')
    assert_same_layer(multi_modal_network.aequilibraebuilder.bike_lanes, aequilibraebuilder.bike_lanes, 'bike_lanes')
    assert_same_layer(multi_modal_network.gtfs_network_builder.final_pt_links, gtfs_network_builder.final_pt_links, 'final_pt_links')
    assert_same_layer(multi_modal_network.gdf_agg_zones, other.gdf_agg_zones, 'zones_agg')
    assert_same_layer(multi_modal_network.drawn_polygon, other.drawn_polygon, 'drawn_polygon')
    # Network saved without the map matching diagnostic (as before PLAN-002): loaded without it
    assert gtfs_network_builder.pt_bus_routes_init is None


def test_map_matching_diagnostic_round_trip():
    """ The map matching diagnostic (pt_bus_routes_init, PLAN-002) is saved and reloaded with the network."""
    multi_modal_network = MultiModalNetwork(**filter_args(args, MultiModalNetwork))
    zones = make_zones()
    diagnostic = gpd.GeoDataFrame({'sub_route_id': [0, 1], 'route_id': [10050000000, 10050000000], 'line_name': ['37', '37'],
                                   'status': ['matched', 'path_too_short_dropped'], 'n_candidates': [39.0, 6.0], 'n_links_path': [5.0, 2.0],
                                   'len_init_m': [1142.1, 103.9], 'len_matched_m': [1000.0, np.nan], 'hausdorff_m': [12.5, np.nan],
                                   'geometry': [LineString([(0, 0), (100, 0)]), LineString([(100, 0), (150, 0)])]}, crs='EPSG:2154')
    multi_modal_network.networkbuilder = SimpleNamespace(gdf=zones, study_area_polygon=zones.union_all())
    multi_modal_network.aequilibraebuilder = SimpleNamespace(links=make_links(), nodes=make_points())
    multi_modal_network.gtfs_network_builder = SimpleNamespace(pt_links_inside=make_pt_links().drop(columns='path_link_id'), pt_nodes_inside=make_points().iloc[0:0],
                                                               final_matches=make_links(), final_pt_links=make_pt_links(), pt_bus_routes_init=diagnostic)
    multi_modal_network.gdf_init_zones = multi_modal_network.gdf_agg_zones = zones.to_crs('EPSG:4326')
    multi_modal_network.drawn_polygon = None
    multi_modal_network.selection_from_polygon = False
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        multi_modal_network.save(tmp)
        other = MultiModalNetwork(**filter_args(args, MultiModalNetwork))
        _, _, gtfs_network_builder = other.load(tmp)
    assert_same_layer(diagnostic, gtfs_network_builder.pt_bus_routes_init, 'pt_bus_routes_init')


if __name__ == "__main__":
    for test in [test_round_trip_layers, test_no_silent_overwrite, test_multimodal_network_save_load_without_network_access,
                 test_map_matching_diagnostic_round_trip]:
        test()
        print(f"OK  {test.__name__}")
