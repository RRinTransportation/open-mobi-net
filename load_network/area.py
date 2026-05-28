import geopandas as gpd
import pandas as pd
def load_area(restricted_communes = ['Lyon 6e Arrondissement'],
            lyon_data_path = 'data/Lyon/raw_data',
               shp_folder_path = 'net_car/shapefiles_sym/Iris_Lyon.shp'):

    gdf = gpd.read_file(f"{lyon_data_path}/{shp_folder_path}")
    gdf.crs ="EPSG:2154"

    gdf = gdf[gdf['NOM_COM'].isin(restricted_communes)] # ['Lyon 6e Arrondissement','Lyon 3e Arrondissement']

    study_area_polygon = gpd.GeoDataFrame(columns = ['geometry'])
    study_area_polygon['geometry']= [gdf.unary_union]
    study_area_polygon.crs = "EPSG:2154"
    study_area_polygon=study_area_polygon.to_crs("EPSG:4326")

    return gdf,study_area_polygon