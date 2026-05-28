import sys
import os
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
import numpy as np
from datetime import datetime
import pickle 
import shapely 

def load_zones(DATA_PATH = "data/Lyon/raw_data/net_car/shapefiles_sym"):
    iris_path = f"{DATA_PATH}/Iris_lyon.shp"
    iris_gdf = gpd.read_file(iris_path)
    return iris_gdf

def compute_score(row,gdf,agg_per_IRIS_type = False):
    # Init score:
    best_score = float('inf')
    best_neighbor = None
    
    # Compute: 
    area_i = row['area']
    geom_i = row.geometry

    for iris_code in row['NEIGHBORS']:
        iris_code = np.int64(iris_code)
        row_j = gdf.loc[iris_code]
        common = geom_i.union(row_j.geometry)


        common_zone_type = True if not agg_per_IRIS_type else (row['TYP_IRIS'] == row_j['TYP_IRIS'])
            

        ## Common Perimeter: 
        # perim = common.length/1e3  # Convertir en km
        intersection = geom_i.intersection(row_j.geometry)
        common_perimeter = intersection.length / 1e3  # in Km 
        area = area_i + row_j['area']
        if common_perimeter > 1e-9 and common_zone_type:
            score = (area) / common_perimeter
        else:
            score = np.inf


        if score < best_score:
            best_score = score
            best_neighbor = iris_code

    return best_score,best_neighbor
        
def iteration_spatial_agg(gdf):
    
    ## Find index of the best score (i.e min score):
    two_best_scores = gdf['best_score'].nsmallest(2)
    assert abs(two_best_scores.iloc[0] - two_best_scores.iloc[1])<1e-3, f"two_best_scores.iloc[0] = {two_best_scores.iloc[0]} and  two_best_scores.iloc[0] = {two_best_scores.iloc[1]}"
    best_score_index = list(two_best_scores.index)
    aggregated_rows = gdf.loc[best_score_index].copy()
    # print('Best score: ')
    # display(two_best_scores)


    # ------- Merge 2 rows:  ---------------------------------------------------------------
    row1 = gdf.loc[best_score_index[0]]
    row2 = gdf.loc[best_score_index[1]]
    row = row1.copy()

    # Update Neighbors, Station & Geometry:
    row.NEIGHBORS = list((set(row1.NEIGHBORS) | set(row2.NEIGHBORS)) - set([row1.name,row2.name]))
    # row.STATION = list((set(row1.STATION) | set(row2.STATION)))
    row.geometry = row1.geometry.union(row2.geometry)
    row.CONTAINS = row.CONTAINS + row2.CONTAINS
    # row.geometry = unary_union([row_i.geometry, row_j.geometry]).convex_hull
    row['area'] = row.geometry.area /1e6


    ## Remove row2 and row1 from gdf: 
    gdf.drop(index=best_score_index[0], inplace=True)
    gdf.drop(index=best_score_index[1], inplace=True)

    ## Add row to gdf:
    gdf.loc[row.name] = row

    # print('row1.name: ', row1.name)
    # print('row2.name: ', row2.name)
    # print('All neighbords: ', row2.NEIGHBORS)

    # ------- Update Names: replace neighbor2 to the name of neighor1 in the gdf  -------------------------
    gdf_neighbords = gdf.copy()
    for neighbor in row2.NEIGHBORS:
        # If neighbor is not in row1.NEIGHBORS, add it:
        if neighbor != row1.name : 
            # print('\nneighbor: ', neighbor)
            # print("gdf.loc[neighbor, 'NEIGHBORS'] before: ", gdf.loc[neighbor, 'NEIGHBORS'])
            new_neighbors = list(set(gdf_neighbords.loc[neighbor]['NEIGHBORS'] + [row1.name]) - set([row2.name]) )
            gdf.at[neighbor, 'NEIGHBORS'] = new_neighbors
            # print("gdf.loc[neighbor, 'NEIGHBORS'] after: ", gdf.loc[neighbor]['NEIGHBORS'] )


    # -------  Compute New scores for the New aggregated row and all the concerned neighbors -------------------------
    updated_best_score,updated_best_neighbor = compute_score(row, gdf)
    gdf.loc[row.name,'best_score'] = updated_best_score
    gdf.loc[row.name,'best_neighbor'] = updated_best_neighbor

    # print('\nRow IRIS: ',row.name)
    # print('Row Neighbors: ',row.NEIGHBORS)
    # print('Best Neighbor among them: ',row['best_neighbor'])


    # Compute new best_score and best_neighbor of each neighbor :
    for neighbor in row.NEIGHBORS:
        # print('type neighbor: ',neighbor,type(neighbor))
        # print('type gdf.index[0]: ',gdf.index[0],type(gdf.index[0]))
        best_score, best_neighbor = compute_score(gdf.loc[neighbor], gdf)
        # gdf.loc[neighbor, 'best_score'] = best_score
        # gdf.loc[neighbor, 'best_neighbor'] = best_neighbor
        gdf.at[neighbor, 'best_score']= best_score
        gdf.at[neighbor, 'best_neighbor']= best_neighbor

    gdf.crs = 'EPSG:2154'
    return gdf,aggregated_rows


def get_dic_contained_index(gdf_init,gdf_agg,save_path = None):
    gdf_agg['CONTAINS'] = gdf_agg['CONTAINS'].apply(lambda x : list(map(int,x.split(','))))
    gdf_agg['Idx_in_init'] = gdf_agg['CONTAINS'].apply(lambda L_iris_id : get_index_from_iris_ids(L_iris_id,gdf_init))

    dictionnary_aggregated_iris = {}
    for idx,row in gdf_agg.iterrows():
        dictionnary_aggregated_iris[idx] = row['Idx_in_init']
    if save_path is not None:
        target_n = len(gdf_agg)
        save_path = f"{save_path}/dic_lyon_iris_agg{target_n}.pkl"
        pickle.dump(dictionnary_aggregated_iris,open(save_path,"wb"))
    return dictionnary_aggregated_iris


def get_index_from_iris_ids(L_iris_id,iris_gdf):
    gdf_i = iris_gdf.copy()
    return list(gdf_i[gdf_i.CODE_IRIS.isin(L_iris_id)].index)


def preprocess_iris_shp(init_gdf,unique_id = 'DCOMIRIS'):
    
    gdf = init_gdf.copy()
    if not hasattr(gdf, 'crs'):
        raise ValueError("gdf should have a CRS. Please set a CRS different different from Geodetic System (i.e. not EPSG:4326)")
    if gdf.crs == 'EPSG:4326':
        raise ValueError("gdf should have a CRS different from Geodetic System (i.e. not EPSG:4326)")

    gdf[unique_id] = gdf[unique_id].apply(lambda x: np.int64(x))

    gdf['area'] = gdf.geometry.area/ 1e6  # Convertir en km²
    if 'NEIGHBORS' not in gdf.columns:
        gdf['NEIGHBORS'] = gdf.apply(lambda row: gdf[gdf.geometry.touches(row.geometry)][unique_id].tolist(), axis=1)
    if 'CONTAINS' not in gdf.columns:
        gdf['CONTAINS'] = gdf[unique_id].apply(lambda x:  [x])
    gdf.set_index(unique_id, inplace=True)
    return gdf 

def clip_gdf_with_polygon(gdf,cordon,within):
    """
    Clip a GeoDataFrame with a polygon, keeping only the geometries that are within or intersecting the polygon.
    Update the neighbors accordingly.
    """
    # Keep only the geometries that are contained within the polygon
    if type(cordon) == gpd.GeoDataFrame and len(cordon) == 1:
        cordon = cordon.geometry.iloc[0]
    if within : 
        mask = gdf.geometry.within(cordon)
    # Or intersecting:
    else:
        mask = gdf.geometry.intersects(cordon)

    gdf = gdf[mask]

    # Update neighbors:
    gdf['NEIGHBORS'] = gdf.apply(lambda row: list(set(gdf[gdf.geometry.touches(row.geometry)].index) & set(gdf.index)), axis=1)
    return gdf


def aggregate_iris_zones(init_gdf: gpd.GeoDataFrame, 
                        target_n: int, 
                        save_path:str = None,
                        unique_id: str = 'DCOMIRIS',
                        cordon: shapely.geometry.polygon.Polygon = None,
                        within: bool = True,
                        # columns_to_join: list = ['CONTAINS','NEIGHBORS']
                        ) -> gpd.GeoDataFrame:
    """
    Agrège les zones IRIS d'un GeoDataFrame jusqu'à atteindre au plus target_n zones.
    L'agrégation minimise le critère (s_i + s_j) / P_ij entre zones adjacentes.
    Où P_ij est la longueur de la portion de perimètre commune entre deux zones.

    Paramètres:
        gdf: GeoDataFrame avec colonnes 'INSEE_COM', 'IRIS', 'CODE_IRIS', 'NEIGHBORS', 'STATION', 'geometry', etc.
        target_n: nombre cible de zones après agrégation.

    Retour:
        GeoDataFrame agrégé.
    """
    gdf = preprocess_iris_shp(init_gdf,unique_id)

    # Restrict to cordon if provided:
    if cordon is not None: 
        gdf = clip_gdf_with_polygon(gdf,cordon,within)
    # ....
        
    # Init best_score and best_neighbor for each zone:
    gdf[['best_score','best_neighbor']] = pd.DataFrame(gdf.apply(
            lambda row: compute_score(row,gdf),axis=1).tolist(),
            columns=['best_score','best_neighbor'],index=gdf.index
            )
    # ...


    # While objectif not reached, aggregate the 2 best zones:
    while len(gdf) > target_n:
        gdf,_ = iteration_spatial_agg(gdf)
    # ...

    # Save gdf: 
    if save_path is not None: 
        dir_path = f"{save_path}/lyon_iris_agg{target_n}"
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        gdf.to_file(f"{dir_path}/lyon.shp")
    # ...
    return gdf
