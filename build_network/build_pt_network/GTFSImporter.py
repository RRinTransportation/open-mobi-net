from aequilibrae.project.database_connection import database_connection
import os
from tempfile import gettempdir
from aequilibrae import Project
from uuid import uuid4
from aequilibrae.transit import Transit
import pandas as pd 
import geopandas as gpd
from build_pt_network.SQL_query import sql_enriched_nodes_query, sql_links_query

class GTFSImporter:
    def __init__(self, 
                 save_folder_path,
                 gtfs_zip_name,
                 agency_name,
                 transit_date,
                 study_area_polygon
                 ):
        
        self.save_folder_path = save_folder_path
        self.gtfs_zip_name = gtfs_zip_name
        self.agency_name = agency_name
        self.transit_date = transit_date
        self.study_area_polygon = study_area_polygon
        self.sql_enriched_nodes_query = sql_enriched_nodes_query
        self.sql_links_query = sql_links_query

        transit = self._start()
        self._load_gtfs_route(transit)


    def _start(self):
        fldr = os.path.join(gettempdir(), uuid4().hex)
        project = Project()
        project.new(fldr)
        project.network.create_from_osm(model_area=self.study_area_polygon) # "Lyon, France" # "Nauru"
        data = Transit(project)

        dest_path = f"{self.save_folder_path}/{self.gtfs_zip_name}"
        transit = data.new_gtfs_builder(agency=self.agency_name, file_path=dest_path)
        transit.load_date(self.transit_date)
        return transit

    def _load_gtfs_route(self, transit):
        """ Loads the GTFS data into the Aequilibrae model, including map matching.
        Depending on the GTFS size, this process can be really time-consuming.
        """

        transit.set_allow_map_match(True)
        transit.map_match()
        transit.save_to_disk()

        # Now we will plot one of the route's patterns we just imported
        self.conn = database_connection("transit")


    def _SQL_extract(self):
        # --- Extract the links and nodes from the GTFS data using SQL queries ---
        self._tackle_trips()
        self._tackle_enriched_nodes()
        self._save_shapefiles()
        self._provide_information()

    def _tackle_trips(self):
        df_trips = pd.read_sql_query(self.sql_links_query, self.conn)

        # --- Convert to GeoDataFrame ---
        self.gdf_trips = gpd.GeoDataFrame(
            df_trips,
            geometry=gpd.GeoSeries.from_wkt(df_trips['geometry']),
            crs="EPSG:4326"
        )

        # Add columns with mode names (rather than mode codes)
        self.mode_mapping = {0: 'Tramway', 1: 'Métro', 3: 'Bus', 6: 'Funiculaire'}
        self.gdf_trips['mode_name'] = self.gdf_trips['mode'].map(self.mode_mapping).fillna('Autre')


    def _tackle_enriched_nodes(self):
        df_stops_enriched = pd.read_sql_query(self.sql_enriched_nodes_query, self.conn)

        # --- Convert to GeoDataFrame ---
        self.gdf_stops = gpd.GeoDataFrame(
            df_stops_enriched,
            geometry=gpd.GeoSeries.from_wkt(df_stops_enriched['geometry']),
            crs="EPSG:4326"
        )

        self.gdf_stops['mode_name'] = self.gdf_stops['modes'].astype(int).map(self.mode_mapping).fillna('Autre')

    def _save_shapefiles(self):
        # Save : 
        self.gdf_stops.to_file(f'{self.save_folder_path}/{self.gtfs_folder_name}/stops/stops.shp')
        self.gdf_trips.to_file(f'{self.save_folder_path}/{self.gtfs_folder_name}/lines/lines.shp')


    def _provide_information(self):

        print("--- Table 'stops' ---")
        schema_stops = pd.read_sql_query("PRAGMA table_info(stops);", self.conn)
        print(schema_stops)

        print("--- Table 'stop_times' ---")
        schema_stop_times = pd.read_sql_query("PRAGMA table_info(stop_times);", self.conn)
        print(schema_stop_times)

        print("--- Table 'trips_schedule' ---")
        schema_trips_schedule = pd.read_sql_query("PRAGMA table_info(trips_schedule);", self.conn)
        print(schema_trips_schedule)

        print("--- Table 'pattern_mapping' ---")
        schema_pattern_mapping = pd.read_sql_query("PRAGMA table_info(pattern_mapping);", self.conn)
        print(schema_pattern_mapping)
        print("--- Table 'route_links' ---")
        schema_route_links = pd.read_sql_query("PRAGMA table_info(route_links);", self.conn)
        print(schema_route_links)

        # Information if needed ....
        sql_query_tables = "SELECT name FROM sqlite_master WHERE type='table';"

        # Exécuter la requête et afficher le résultat
        available_tables = pd.read_sql_query(sql_query_tables, self.conn)

        print("Tables within 'transit' :")
        print(available_tables.values)

        print("--- Table 'trips' ---")
        schema_trips = pd.read_sql_query("PRAGMA table_info(trips);", self.conn)
        print(schema_trips)

        print("\n--- Table 'routes' ---")
        schema_routes = pd.read_sql_query("PRAGMA table_info(routes);", self.conn)
        print(schema_routes)

    
