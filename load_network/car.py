from shapely import wkt
import pandas as pd
import geopandas as gpd
import os 
import sys 

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
from utils.network import add_lanes_when_missing, add_capacity_on_car_links,add_speed_when_missing


def load_network(project_save_path = 'data/Lyon/raw_data/aequilibrae_lyon6',from_aequilibrae_save  = False):
    """
    Load the traffic network from the given project save path.
    link.csv, node.csv and use_definition.csv files are from AequilibraE export.

    outputs:
    -----
    links and nodes: correspond to the entire network, with all modes 
    c_network: GeoDataFrame with car links only
    """
    link_file = f"{project_save_path}/link.csv"
    node_file = f"{project_save_path}/node.csv"
    metadata_file = f"{project_save_path}/use_definition.csv"

    # Load links
    if from_aequilibrae_save: 
        links = pd.read_csv(link_file)
    else:
        links = pd.read_csv(link_file,index_col = 0)

    links.geometry = links.geometry.apply(wkt.loads)
    links = gpd.GeoDataFrame(links, geometry = links.geometry, crs="EPSG:4326")

    # Load nodes
    nodes = pd.read_csv(node_file)
    if from_aequilibrae_save: 
        nodes = pd.read_csv(node_file)
        nodes.geometry = nodes.apply(lambda row:  gpd.points_from_xy([row.x_coord],[row.y_coord])[0], axis=1)
    else:
        nodes = pd.read_csv(node_file,index_col = 0)
        nodes.geometry = nodes.geometry.apply(wkt.loads)
    nodes = gpd.GeoDataFrame(nodes, geometry = nodes.geometry, crs="EPSG:4326")

    # Preprocess links to add lanes and capacity : 
    links = add_lanes_when_missing(links)
    links = add_speed_when_missing(links)
    links = add_capacity_on_car_links(links)

    # Extract car network only :
    car_links = links[(links['modes'].str.contains('c'))    & 
                            ~(links['link_type'] == 'pedestrian') &
                            ~(links['link_type'] == 'footway')    & 
                            ~(links['link_type'] == 'service')
                            ]

    # Remove links without speed or capacities in both directions : 
    mask_anomalies = ((car_links.capacity_ab.isna() & car_links.capacity_ba.isna()) |
                        (car_links.lanes_ab.isna() & car_links.lanes_ba.isna()) |
                        (car_links.speed_ab.isna() & car_links.speed_ba.isna())
                    )

    car_links = car_links[~mask_anomalies]
    car_links_anomalies = car_links[mask_anomalies]

    # Load metadata
    metadata = pd.read_csv(metadata_file)

    return car_links,links,nodes,metadata,car_links_anomalies