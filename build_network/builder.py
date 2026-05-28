import pandas as pd
import numpy as np
import geopandas as gpd 
import matplotlib.pyplot as plt
import math 
import os 
import subprocess
import sys
import time


from uuid import uuid4
from tempfile import gettempdir
from aequilibrae import Project


def load_init_area(folder_path = 'data/Lyon/raw_data/net_car/shapefiles_sym',
                   file_name = 'Iris_Lyon.shp',
                   crs = "EPSG:2154",
                   target_crs = None):
    gdf = gpd.read_file(f"{folder_path}/{file_name}")
    if crs is None:
        raise ValueError("You should specify the CRS of the input shapefile")
    gdf.crs = crs
    if target_crs is not None:
        gdf = gdf.to_crs(target_crs)
    return gdf

def restrict_area_from_filtering(gdf,
                  key_column = 'NOM_COM',
                  restricted_keys = ['Lyon 6e Arrondissement']):
    return gdf[gdf[key_column].isin(restricted_keys)]


def convert_gdf_to_study_area_polygon(gdf,init_crs = "EPSG:2154", target_crs = "EPSG:4326"):
    study_area_polygon = gpd.GeoDataFrame(columns = ['geometry'])
    study_area_polygon['geometry']= [gdf.union_all()]
    study_area_polygon.crs = init_crs
    study_area_polygon=study_area_polygon.to_crs(target_crs)
    return study_area_polygon

def spatial_mask(gdf, study_area_polygon):
    """ Restrict the GeoDataFrame to the area defined by the study_area_polygon"""
    gdf_filtered = gdf[gdf.intersects(study_area_polygon.union_all())]
    return gdf_filtered

class NetworkBuilder:
    def __init__(self, 
                 IRIS_folder_path = 'data/Lyon/raw_data/net_car/shapefiles_sym',
                 file_name = 'Iris_Lyon.shp',
                 init_crs = "EPSG:2154",
                 target_crs = "EPSG:4326",
                 export_file = "data.geojson",
                 shp_restriction_path = None,
                 selection_from_polygon = True,
                 key_column = None,
                 restricted_keys = None):
        
        self.IRIS_folder_path = IRIS_folder_path
        self.file_name = file_name
        self.init_crs = init_crs
        self.target_crs = target_crs
        self.export_file = export_file
        self.selection_from_polygon = selection_from_polygon
        self.key_column = key_column
        self.restricted_keys = restricted_keys
        self.shp_restriction_path = shp_restriction_path

    def run(self):
        """ Main method to run the network building process. Restrict the area based on the 3 methods and return the resulting GeoDataFrame"""
        self.gdf = load_init_area(self.IRIS_folder_path, self.file_name, self.init_crs)
        if self.selection_from_polygon:
            self._select_from_polygon(self.gdf) 

        if self.key_column is not None and self.restricted_keys is not None:
            self._restrict_from_filtering(self.gdf)
            if self.gdf.empty:
                raise ValueError("The resulting GeoDataFrame is empty after filtering. Please check the key_column and restricted_keys values.")

        if self.shp_restriction_path is not None:
            self._restrict_to_study_area()
            if self.gdf.empty:
                raise ValueError(f"The resulting GeoDataFrame is empty after restriction from shapefile. Please check the shp_restriction_path value extracted from {self.shp_restriction_path}")


        self.study_area_polygon = self.gdf.union_all()

        return self.gdf
    
    def _select_from_polygon(self, gdf):
        """ Restrict the GeoDataFrame to the area defined by a polygon drawn by the user in a Streamlit UI"""
        # If restriction from a polygon selection based on streamlit drawing tools:
        temp_gdf_path = f"temp_{self.export_file}"
        if os.path.exists(self.export_file):
            os.remove(self.export_file)

        gdf.to_crs(self.target_crs).to_file(temp_gdf_path, driver="GeoJSON")
        env = os.environ.copy()
        env["TEMP_GDF_PATH"] = temp_gdf_path

        # Wait for the user to draw a polygon in the Streamlit UI and save it to a temporary file
        script_path = os.path.join("build_network", "polygon_selection", "selection_from_streamlit_ui.py")
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", script_path, "--server.headless", "false"
        ], env=env)
        
        # if the process terminate cause the user close the streamlit window, we want to stop waiting for the file and terminate the process
        if process.poll() is not None:
            process.terminate()
            raise Exception("Streamlit process terminated. Please run the network builder again and draw a polygon to select the area.")
        
        while not os.path.exists(self.export_file):
            time.sleep(1)
        process.terminate()
        # ...

        if os.path.exists(temp_gdf_path):
            os.remove(temp_gdf_path)

        study_area_polygon = gpd.read_file(self.export_file)
        gdf_target_crs = gdf.to_crs(self.target_crs)
        self.gdf = spatial_mask(gdf_target_crs, study_area_polygon)

    def _restrict_to_study_area(self):
        """ Restrict the GeoDataFrame to the area defined by a shapefile containing the study area polygon"""
        gdf_area = gpd.read_file(self.shp_restriction_path)
        study_area_polygon = convert_gdf_to_study_area_polygon(gdf_area, 
                                                    init_crs = self.init_crs, 
                                                    target_crs = self.target_crs)
        self.gdf = spatial_mask(self.gdf, study_area_polygon)

    def _restrict_from_filtering(self, gdf):
        """ Restrict the GeoDataFrame to the area defined by filtering based on a column and a list of restricted keys"""
        self.gdf = restrict_area_from_filtering(gdf, self.key_column, self.restricted_keys)






if __name__ == "__main__":
    # Init ...
    IRIS_folder_path = 'data/Lyon/raw_data/net_car/shapefiles_sym'
    file_name = 'Iris_Lyon.shp'
    init_crs = "EPSG:2154"
    target_crs = "EPSG:4326"
    export_file = "data.geojson"
    selection_from_polygon = True
    key_column = 'NOM_COM'
    restricted_keys = ['Lyon 6e Arrondissement']
    shp_restriction_path = None
    # ...

    gdf = NetworkBuilder(
        IRIS_folder_path = IRIS_folder_path,
        file_name = file_name,
        init_crs = init_crs,
        target_crs = target_crs,
        export_file = export_file,
        selection_from_polygon = selection_from_polygon,
        key_column = key_column,
        restricted_keys = restricted_keys,
        shp_restriction_path = shp_restriction_path,
    ).run()

    
