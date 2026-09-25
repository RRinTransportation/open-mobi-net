import pandas as pd
import geopandas as gpd
import os
import inspect
import numpy as np 
from datetime import datetime
from build_network.builder import NetworkBuilder
from build_network.AequilibraeBuilder import AequilibraeBuilder
from build_network.build_pt_network.GTFSImporter import GTFSImporter
from build_network.build_pt_network.GTFSNetworkBuilder import GTFSNetworkBuilder
from build_network.build_pt_network.MatMatchingPT2OSM import MapMatchingPT2OSM
from build_network.network_io import save_network, load_network
from load_network.iris import aggregate_iris_zones


class MultiModalNetwork:

    def __init__(self, 
                 folder_path,
                 IRIS_folder_path,
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
                plane_projection :str,
                target_n_zones: int,
                save_path: str = None
                 ): 
        self.folder_path = folder_path
        self.IRIS_folder_path = IRIS_folder_path
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
        self.plane_projection = plane_projection
        self.target_n_zones = target_n_zones
        self.save_path = save_path


    def build(self):
        networkbuilder = self._build_working_area()
        aequilibraebuilder, networkbuilder = self._build_traffic_network(networkbuilder)
        gtfs_network_builder = self._build_pt_network(networkbuilder, aequilibraebuilder)
        self._build_zones(networkbuilder)

        self.networkbuilder = networkbuilder
        self.aequilibraebuilder = aequilibraebuilder
        self.gtfs_network_builder = gtfs_network_builder

        if self.save_path is not None:
            self.save(self.save_path)

        return networkbuilder, aequilibraebuilder, gtfs_network_builder

    

    def save(self, path: str = None, overwrite: bool = False) -> str:
        """ Save the network built with build() (or loaded with load()) in a folder containing
        'network.gpkg' (one layer per GeoDataFrame) and 'metadata.json' (parameters, CRS, git commit, ...).
        If path is None, save in 'data/<City>/ready_input/networks/<YYYYMMDD_HHMM>'.
        """
        if not hasattr(self, 'networkbuilder'):
            raise RuntimeError("Nothing to save: run build() or load() first.")
        if path is None:
            path = self._default_save_path()

        networkbuilder = self.networkbuilder
        aequilibraebuilder = self.aequilibraebuilder
        gtfs_network_builder = self.gtfs_network_builder

        # Polygon drawn in the Streamlit UI, to be able to rebuild the same network:
        drawn_polygon = getattr(self, 'drawn_polygon', None)
        if drawn_polygon is None and self.selection_from_polygon and os.path.exists(self.export_file):
            drawn_polygon = gpd.read_file(self.export_file)

        layers = {
            'study_area': gpd.GeoDataFrame(geometry=[networkbuilder.study_area_polygon], crs=networkbuilder.gdf.crs),
            'drawn_polygon': drawn_polygon,
            'iris_selected': networkbuilder.gdf,
            'links': aequilibraebuilder.links,  # traffic_network is the same (preprocessed in place) GeoDataFrame
            'nodes': aequilibraebuilder.nodes,
            'bike_lanes': getattr(aequilibraebuilder, 'bike_lanes', None),
            'bike_nodes': getattr(aequilibraebuilder, 'bike_nodes', None),
            'pt_links_inside': gtfs_network_builder.pt_links_inside,
            'pt_nodes_inside': gtfs_network_builder.pt_nodes_inside,
            'pt_final_matches': gtfs_network_builder.final_matches,
            'pt_final_links': gtfs_network_builder.final_pt_links,
            'pt_bus_routes_init': getattr(gtfs_network_builder, 'pt_bus_routes_init', None),
            'zones_init': self.gdf_init_zones,
            'zones_agg': self.gdf_agg_zones,
        }
        save_network(layers, path, parameters=self._get_parameters(), overwrite=overwrite)
        print(f"Network saved in: {path}")
        return path

    def load(self, path: str):
        """ Load a network saved with save(), without Streamlit, OSM download nor GTFS import.
        Return the same objects as build(): (networkbuilder, aequilibraebuilder, gtfs_network_builder),
        and set self.gdf_init_zones and self.gdf_agg_zones.
        The parameters saved with the network replace the current ones (differences are printed).
        """
        layers, metadata = load_network(path)
        self._restore_parameters(metadata['parameters'])

        # --- Working area (NetworkBuilder.__init__ has no side effect, only run() does):
        networkbuilder = self._new_networkbuilder()
        networkbuilder.gdf = layers['iris_selected']
        networkbuilder.study_area_polygon = layers['study_area'].geometry.iloc[0]

        # --- Traffic and bike networks (AequilibraeBuilder.__init__ has no side effect):
        aequilibraebuilder = AequilibraeBuilder(networkbuilder, project_save_path=f"{self.folder_path}/tmps_trial")
        aequilibraebuilder.links = layers['links']
        aequilibraebuilder.nodes = layers['nodes']
        aequilibraebuilder.traffic_network = aequilibraebuilder.links
        aequilibraebuilder.bike_lanes = layers.get('bike_lanes')
        aequilibraebuilder.bike_nodes = layers.get('bike_nodes')

        # --- Public transport (GTFSNetworkBuilder.__init__ would read the whole GTFS cache, so it is skipped):
        gtfs_network_builder = GTFSNetworkBuilder.__new__(GTFSNetworkBuilder)
        gtfs_network_builder.project_save_path = f"{self.folder_path}/{self.gtfs_folder_name}"
        gtfs_network_builder.pt_links_inside = layers['pt_links_inside']
        gtfs_network_builder.pt_nodes_inside = layers['pt_nodes_inside']
        gtfs_network_builder.final_matches = layers['pt_final_matches']
        gtfs_network_builder.final_pt_links = layers['pt_final_links']
        gtfs_network_builder.pt_bus_routes_init = layers.get('pt_bus_routes_init')  # Absent from networks saved before PLAN-002

        # --- Zones:
        self.gdf_init_zones = layers['zones_init']
        self.gdf_agg_zones = layers['zones_agg']
        self.drawn_polygon = layers.get('drawn_polygon')

        self.networkbuilder = networkbuilder
        self.aequilibraebuilder = aequilibraebuilder
        self.gtfs_network_builder = gtfs_network_builder
        self.loaded_metadata = metadata
        return networkbuilder, aequilibraebuilder, gtfs_network_builder

    def _get_parameters(self) -> dict:
        """ Parameters of __init__ with their current values."""
        parameter_names = [p for p in inspect.signature(MultiModalNetwork.__init__).parameters if p != 'self']
        return {name: getattr(self, name) for name in parameter_names}

    def _restore_parameters(self, saved_parameters: dict):
        """ Set the parameters saved with a network, and print those which differ from the current configuration.
        'save_path' is not restored: it only tells where build() saves a network."""
        for name, saved_value in saved_parameters.items():
            if name == 'save_path':
                continue
            current_value = getattr(self, name, None)
            if current_value != saved_value:
                print(f"Parameter '{name}' taken from the saved network: {saved_value!r} (current configuration: {current_value!r})")
            setattr(self, name, saved_value)

    def _default_save_path(self) -> str:
        city_folder = os.path.dirname(os.path.normpath(self.folder_path))
        return os.path.join(city_folder, 'ready_input', 'networks', datetime.now().strftime('%Y%m%d_%H%M'))

    def _new_networkbuilder(self):
        return NetworkBuilder(
            IRIS_folder_path = self.IRIS_folder_path,
            file_name = self.file_name,
            init_crs = self.init_crs,
            target_crs = self.target_crs,
            export_file = self.export_file,
            selection_from_polygon = self.selection_from_polygon,
            key_column = self.key_column,
            restricted_keys = self.restricted_keys,
            shp_restriction_path = self.shp_restriction_path,
        )

    def _build_working_area(self,):
        networkbuilder = self._new_networkbuilder()
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
                            init_crs = 'EPSG:2154',  # Shapefiles without .prj, coordinates in Lambert-93
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
        gtfs_network_builder.pt_bus_routes_init = mapmatching_pt_to_osm.bus_routes_diagnostics  # Initial GTFS bus sub-routes + map matching outcome
        return gtfs_network_builder
    
    def _build_zones(self,networkbuilder):
        cordon_projected = gpd.GeoDataFrame({'geometry': [networkbuilder.study_area_polygon]}, 
                                            geometry='geometry', 
                                            crs= networkbuilder.target_crs
                                            ).to_crs(self.plane_projection)
        
        gdf_init_zones = networkbuilder.gdf.to_crs(self.plane_projection)


        gdf_agg_zones = aggregate_iris_zones(init_gdf = gdf_init_zones,
                                target_n = self.target_n_zones, 
                                unique_id = 'DCOMIRIS',
                                cordon = cordon_projected,
                                within = True,
                                save_path = None, # Aggregated zones are saved with the whole network (see save())
                                # columns_to_join: list = ['CONTAINS','NEIGHBORS']
                                )
        gdf_agg_zones['Zone_id'] = np.arange(len(gdf_agg_zones))
        
        self.gdf_init_zones = gdf_init_zones.to_crs(self.target_crs)
        self.gdf_agg_zones = gdf_agg_zones.to_crs(self.target_crs)






if __name__ == "__main__":
    # Init ...
    CITY="Lyon"

    folder_path = f"data/{CITY}/raw_data"
    IRIS_folder_path = f'{folder_path}/net_car/shapefiles_sym'
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
        IRIS_folder_path = IRIS_folder_path,
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


