
import math
import pandas as pd
import geopandas as gpd

LANE_CAPACITY_ASSUMPTIONS = {
                                    'motorway': 2000,
                                    'motorway_link': 1900,
                                    'trunk': 1800,
                                    'trunk_link': 1700,

                                    'primary': 1500,
                                    'primary_link': 1400,

                                    'secondary': 1200,
                                    'secondary_link': 1100,

                                    'tertiary': 1000,
                                    'tertiary_link': 900,

                                    'residential': 600,

                                    'unclassified': 700,
                                    }

CAPACITY_ASSUMPTIONS_BASED_ON_SPEED = { 15.0: 300,  # 15km/h
                                        20.0: 500,  # 20km/h
                                        30.0: 700,  # 30km/h
                                        50.0: 1000,  # 50km/h
                                        70.0: 1200,  # 70km/h
                                        90.0: 1500,  # 90km/h
                                        110.0: 1800,  # 110km/h
                                        130.0: 2000,  # 130km/h
                                    }

SPEED_ASSUMPTIONS_BASED_ON_TYPE = {
                                        'motorway': 130,    
                                        'motorway_link': 110,

                                        'trunk': 110,
                                        'trunk_link': 90,

                                        'primary': 90,
                                        'primary_link': 70,

                                        'secondary': 70,
                                        'secondary_link': 50,

                                        'tertiary': 50,
                                        'tertiary_link': 30,

                                        'residential': 30,

                                        'unclassified': 30,

                                        'living_street': 20,
                                        'service': 30,
                                        # 'footway': 5,
                                        # 'pedestrian': 5,
                                    }   


def load_shp_from_2154(shp_path):
    gdf_i = gpd.read_file(shp_path)
    gdf_i.crs = "EPSG:2154"
    gdf_i = gdf_i.to_crs("EPSG:4326")
    return gdf_i

def add_lanes_when_missing(network_gdf):
    """ Sometimes the row contains lanes_ab = None & lanes_ba = 0 
    or lanes_ab = 0 & lanes_ba = None.
    In that specific case, and where speed exists, we assume the lane with count = 0 is actually equal to 1.
    And then we specify in a new columns 'added_lane' that we add a lane to that direction.
    Otherwise, we just keep the original values, and set added_lane to False.
    """
    network_gdf[['lanes_ab','lanes_ba','added_lane']] = network_gdf.apply(lambda row : add_lanes(row),axis=1)
    return network_gdf

def add_speed_when_missing(network_gdf):
    """ Sometimes the row contains speed_ab isna or speed_ba isna 
    or speed_ab = 0 & speed_ba = None.
    In that specific case, and where lanes exists, we assume the speed with count = 0 is actually equal to 50km/h.
    And then we specify in a new columns 'added_speed' that we add a speed to that direction.
    Otherwise, we just keep the original values, and set added_speed to False.
    """
    is_car_link = network_gdf['modes'].str.contains('c')
    def add_speed(row):
        link_type = row['link_type']
        if link_type in SPEED_ASSUMPTIONS_BASED_ON_TYPE.keys():
            return SPEED_ASSUMPTIONS_BASED_ON_TYPE[link_type]
        else:
            return 30.0
    for direction_ab in ['ab', 'ba']:
        # Fill only NaN values of the 0 values if lanes_{direction_ab} > 0:
        network_gdf.loc[(network_gdf[f'speed_{direction_ab}'].isna()) & (network_gdf[f'lanes_{direction_ab}'] > 0) & (is_car_link), f'speed_{direction_ab}'] = network_gdf.loc[(network_gdf[f'speed_{direction_ab}'].isna()) & (network_gdf[f'lanes_{direction_ab}'] > 0) & (is_car_link)].apply(lambda row: add_speed(row), axis=1)
        network_gdf.loc[(network_gdf[f'speed_{direction_ab}'] == 0) & (network_gdf[f'lanes_{direction_ab}'] > 0) & (is_car_link) , f'speed_{direction_ab}'] = network_gdf.loc[(network_gdf[f'speed_{direction_ab}'] == 0) & (network_gdf[f'lanes_{direction_ab}'] > 0)& (is_car_link) ].apply(lambda row: add_speed(row), axis=1)

    return network_gdf
def add_capacity_on_car_links(network_gdf):
    """
    Estimates per-lane capacity based on max speed tiers.
    """
    is_car_link = network_gdf['modes'].str.contains('c')
    for direction_ab in ['ab', 'ba']:
        network_gdf[f'capacity_{direction_ab}'] = None
        network_gdf.loc[is_car_link, f'capacity_{direction_ab}'] = network_gdf[is_car_link].apply(
            lambda row: estimate_capacity(row['link_type'],row[f'lanes_{direction_ab}'], row[f'speed_{direction_ab}']),
            axis=1
        )
    return network_gdf

def add_lanes(row):
    """ Sometimes the row contains lanes_ab = None & lanes_ba = 0 
    or lanes_ab = 0 & lanes_ba = None.
    In that specific case, and where speed exists, we assume the lane with count = 0 is actually equal to 1.
    And then we specify in a new columns 'added_lane' that we add a lane to that direction.
    Otherwise, we just keep the original values, and set added_lane to False.
    """
    if math.isnan(row['lanes_ab']) and row['lanes_ba'] == 0:
        return pd.Series([0,  1, True])
    elif row['lanes_ab'] == 0 and math.isnan(row['lanes_ba']):
        return pd.Series([1, 0, True])
    else:
        return pd.Series([row['lanes_ab'], row['lanes_ba'], False])



def estimate_capacity(link_type,lanes, max_speed):
    """
    Estimates per-lane capacity based on max speed tiers.
    """
    # if max speed is None or if is NaN values: 
    if (max_speed is None or pd.isna(max_speed) )or (lanes is None or pd.isna(lanes)):
        return None
    else:
        if lanes == 0:
            return None
        else:
            if link_type in LANE_CAPACITY_ASSUMPTIONS.keys():
                lane_capacity = LANE_CAPACITY_ASSUMPTIONS[link_type]
            else:
                lane_capacity = CAPACITY_ASSUMPTIONS_BASED_ON_SPEED[max_speed]

            return int(lanes * lane_capacity)