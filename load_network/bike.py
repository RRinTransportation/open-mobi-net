import pandas as pd
import geopandas as gpd
from utils.network import load_shp_from_2154


def load_network_from_osm(all_modes_links):
    """
    Get the bike network from already loaded all modes network from OSM import
    all_modes_links: GeoDataFrame with all modes of transport
    """

    # Keep only links with mode 'bike' and which are not footway: 
    bike_gdf = all_modes_links[(all_modes_links["modes"].str.contains("b"))  & 
                                ~(all_modes_links['link_type'] == 'footway')
                                ].copy() # & ~(network_gdf['link_type'] == 'pedestrian') 
    bike_gdf['is_bike'] = (bike_gdf['link_type'] == 'cycleway')
    bike_gdf['bicycle_lanes_ab'] = ((bike_gdf.cycleway_left.isin(['lane','track','shared_lane','share_busway','separate']) & 
                                    bike_gdf['lanes_ab'] > 0)) | \
                                      (bike_gdf.cycleway_right.isin(['lane','track','shared_lane','share_busway','separate']) &
                                        bike_gdf['lanes_ba'] > 0)
    bike_gdf['bicycle_lanes_ba'] = ((bike_gdf.cycleway_left.isin(['lane','track','shared_lane','share_busway','separate']) & 
                                    bike_gdf['lanes_ba'] > 0)) | \
                                      (bike_gdf.cycleway_right.isin(['lane','track','shared_lane','share_busway','separate']) &
                                        bike_gdf['lanes_ab'] > 0)

    # Remove links like ring road 
    bike_gdf = bike_gdf[(bike_gdf.speed_ba <= 50) & (bike_gdf.speed_ab <= 50)].copy()
    return bike_gdf

def load_network_from_preprocessed(Polygon_area_study,lyon_data_path = 'data/Lyon/raw_data'):
    """
    Load the bike network from preprocessed shapefiles.
    """
    shp_path = f'{lyon_data_path}/net_bike/shapes/links_processed.shp'
    shp_nodes_path = f'{lyon_data_path}/net_bike/shapes/nodes_processed.shp'
    bike_lanes = load_shp_from_2154(shp_path).clip(Polygon_area_study.iloc[0,0])
    bike_nodes = load_shp_from_2154(shp_nodes_path).clip(Polygon_area_study.iloc[0,0])

    return bike_lanes,bike_nodes