import pandas as pd
import os

from build_network.builder import NetworkBuilder
from build_network.AequilibraeBuilder import AequilibraeBuilder
from build_network.build_pt_network.GTFSImporter import GTFSImporter
from build_network.build_pt_network.GTFSNetworkBuilder import GTFSNetworkBuilder
from build_network.build_pt_network.MatMatchingPT2OSM import MapMatchingPT2OSM


class MultiModalNetwork:

    def __init__(self, 
                 folder_path,
                 traffic_folder_path,
                 file_name,
                 init_crs,
                 target_crs,
                 export_file,
                 selection_from_polygon,
                 key_column,
                 restricted_keys,
                 shp_restriction_path,
                gtfs_folder_name: str,
                gtfs_zip_name :str,
                agency_name: str,
                transit_date: str,
                 ): 
        self.folder_path = folder_path
        self.traffic_folder_path = traffic_folder_path
        self.file_name = file_name
        self.init_crs = init_crs
        self.target_crs = target_crs
        self.export_file = export_file
        self.selection_from_polygon = selection_from_polygon
        self.key_column = key_column
        self.restricted_keys = restricted_keys
        self.shp_restriction_path = shp_restriction_path
        self.gtfs_folder_name = gtfs_folder_name
        self.gtfs_zip_name = gtfs_zip_name
        self.agency_name = agency_name
        self.transit_date = transit_date


    def build(self):
        networkbuilder = self._build_working_area()
        aequilibraebuilder, networkbuilder = self._build_traffic_network(networkbuilder)
        gtfs_network_builder = self._build_pt_network(networkbuilder, aequilibraebuilder)

        return networkbuilder, aequilibraebuilder, gtfs_network_builder

    

    def _build_working_area(self,):
        networkbuilder = NetworkBuilder(
            traffic_folder_path = self.traffic_folder_path,
            file_name = self.file_name,
            init_crs = self.init_crs,
            target_crs = self.target_crs,
            export_file = self.export_file,
            selection_from_polygon = self.selection_from_polygon,
            key_column = self.key_column,
            restricted_keys = self.restricted_keys,
            shp_restriction_path = self.shp_restriction_path,
        )
        gdf = networkbuilder.run()
        return networkbuilder
    

    def _build_traffic_network(self, networkbuilder):

        aequilibraebuilder = AequilibraeBuilder(networkbuilder, project_save_path=f"{self.folder_path}/tmps_trial")
        aequilibraebuilder.extract_network_from_osm()
        aequilibraebuilder.preprocess_network()

        aequilibraebuilder.add_bike_network(       
                            folder_path = f'{self.folder_path}/net_bike/shapes',          
                            link_name = 'links_processed.shp',
                            node_name = 'nodes_processed.shp',
                            init_crs = 'EPSG:4326',
                                )
        
        return aequilibraebuilder, networkbuilder
    
    def _build_pt_network(self,
                         networkbuilder: NetworkBuilder,
                         aequilibraebuilder: AequilibraeBuilder,
                        ):
        
        """

        Args:
        networkbuilder: The NetworkBuilder instance used to build the initial road network, which will be used for map matching the GTFS data.
        aequilibraebuilder: The AequilibraeBuilder instance used to build the public transport network.
        gtfs_folder_name (str): The name of the folder where the GTFS data is located, relative to the LYON_DATA_PATH.
        gtfs_zip_name (str): The name of the GTFS zip file 
        agency_name (str): The name of the transit agency as specified in the GTFS data
        transit_date (str): The date for which to build the transit network

        """
                            
        # --- If stops and nodes have not been extracted yet, we run the GTFS importer to extract them:
        if not os.path.exists(f'{self.folder_path}/{self.gtfs_folder_name}/stops/stops.shp'):
            gtfs_importer = GTFSImporter(
                save_folder_path = f"{self.folder_path}/{self.gtfs_folder_name}/GTFS",
                gtfs_zip_name = self.gtfs_zip_name,
                agency_name = self.agency_name,
                transit_date = self.transit_date,
                study_area_polygon = networkbuilder.study_area_polygon
            )

        # Once links and nodes are extracted: 
        gtfs_network_builder = GTFSNetworkBuilder(project_save_path=f"{self.folder_path}/{self.gtfs_folder_name}")
        gtfs_network_builder.restrain_to_area_study(networkbuilder.study_area_polygon)

        mapmatching_pt_to_osm = MapMatchingPT2OSM()
        final_matches, final_pt_links =  mapmatching_pt_to_osm.match_pt_to_osm(pt_links_inside=gtfs_network_builder.pt_links_inside, 
                                                                               aequilibraebuilder=aequilibraebuilder
                                                                               )
        
        gtfs_network_builder.final_matches = final_matches
        gtfs_network_builder.final_pt_links = final_pt_links
        return gtfs_network_builder





if __name__ == "__main__":
    # Init ...
    CITY="Lyon"

    folder_path = f"data/{CITY}/raw_data"
    traffic_folder_path = f'{folder_path}/net_car/shapefiles_sym'
    file_name = 'Iris_Lyon.shp'
    init_crs = "EPSG:2154"
    target_crs = "EPSG:4326"
    export_file = "data.geojson"
    selection_from_polygon = True # True
    key_column = None # 'NOM_COM'
    restricted_keys = None # ['Lyon 6e Arrondissement']
    shp_restriction_path = None


    # Public Transport (GTFS):
    gtfs_folder_name = "net_pt"
    gtfs_zip_name = "lyon_tcl_gtfs.zip"
    agency_name = "TCL"
    transit_date = "2024-08-14"
    # ...

    multi_modal_network = MultiModalNetwork(
        folder_path = folder_path, 
        traffic_folder_path = traffic_folder_path,
        file_name = file_name,
        init_crs = init_crs,
        target_crs = target_crs,
        export_file = export_file,
        selection_from_polygon = selection_from_polygon,
        key_column = key_column,
        restricted_keys = restricted_keys,
        shp_restriction_path = shp_restriction_path,
        gtfs_folder_name = gtfs_folder_name,
        gtfs_zip_name = gtfs_zip_name,
        agency_name = agency_name,
        transit_date = transit_date
    )
    networkbuilder, aequilibraebuilder, gtfs_network_builder = multi_modal_network.build()


