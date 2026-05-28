import pandas as pd
import numpy as np
import geopandas as gpd 
import matplotlib.pyplot as plt
import math 
import os 

from uuid import uuid4
from tempfile import gettempdir
from aequilibrae import Project

from utils.network import add_lanes_when_missing,add_capacity_on_car_links
from build_network.builder import NetworkBuilder,load_init_area

class AequilibraeBuilder(NetworkBuilder):
    def __init__(self, 
                 networkbuilder,
                 project_save_path = 'data/Lyon/raw_data/tmps_trial'
                 ):
        super().__init__()

        # Create a temporary folder for the sample project
        self.project_save_path = project_save_path
        self.networkbuilder = networkbuilder
        self.study_area_polygon = networkbuilder.study_area_polygon

    def extract_network_from_osm(self):
        fldr = os.path.join(gettempdir(), uuid4().hex)
        project = Project()
        project.new(fldr)
        ## Si ça ne fonctionne pas, afficher l'erreur et ajouter une information : 
        try:
            project.network.create_from_osm(model_area=self.networkbuilder.study_area_polygon) # "Lyon, France" # "Nauru"
        except Exception as e:
            print(f"An error occurred: {e}")
            print("If connected to any VPN, you should disconnect from it.")
        
        self._export_network(project)
        self._save_project(project)

    def _export_network(self, project):
        self.links = project.network.links.data
        self.nodes = project.network.nodes.data
        
    def _save_project(self, project):
        """ Save Aequilibrae Project (save csv but not I'm not able to load Aequilibrae project from it"""
        if self.project_save_path is not None:
            if not os.path.exists(self.project_save_path):
                os.mkdir(self.project_save_path)

            project.network.export_to_gmns(path=self.project_save_path)
            self.links.to_csv(f'{self.project_save_path}/link.csv')
            self.nodes.to_csv(f'{self.project_save_path}/node.csv')

    def preprocess_network(self):
        """ Restrict the GeoDataFrame to the area defined by the study_area_polygon"""

        # --- Add lanes when it's missing and capacity to the network
        traffic_network = add_lanes_when_missing(self.links)
        traffic_network = add_capacity_on_car_links(self.links)

        self.traffic_network = traffic_network


    
    def add_bike_network(self,       
                         folder_path = 'data/Lyon/raw_data/net_bike/shapes',          
                         link_name = 'links_processed.shp',
                         node_name = 'nodes_processed.shp',
                         init_crs = None,
                        ):
        self.bike_lanes = load_init_area(folder_path, 
                                         link_name, 
                                         crs = init_crs, 
                                         target_crs = self.target_crs
                                         ).clip(self.study_area_polygon)
        self.bike_nodes = load_init_area(folder_path, 
                                         node_name, 
                                         crs = init_crs, 
                                         target_crs = self.target_crs
                                         ).clip(self.study_area_polygon)
        



