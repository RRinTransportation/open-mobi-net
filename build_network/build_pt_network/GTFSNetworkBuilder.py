import geopandas as gpd

class GTFSNetworkBuilder():
    def __init__(self,
                 project_save_path,
                 ):
        self.project_save_path = project_save_path
        self._load_network()

    def _load_network(self):
        self.pt_links = gpd.read_file(f"{self.project_save_path}/lines/lines.shp")
        self.pt_nodes = gpd.read_file(f"{self.project_save_path}/stops/stops.shp")
        self.unique_routes = self.pt_links.drop_duplicates(subset=['route_id'])

    def restrain_to_area_study(self,study_area_polygon):

        gdf_right = gpd.GeoDataFrame(geometry=[study_area_polygon.exterior], crs=self.pt_links.crs)

        self.pt_links_intersecting = gpd.sjoin(self.pt_links, gdf_right, how='inner', predicate='intersects')
        self.pt_nodes_inside = gpd.sjoin(self.pt_nodes, gdf_right, how='inner', predicate='intersects')

        # --- Keep only part of routes which are inside the polygon:
        pt_links_inside = self.pt_links_intersecting.copy()
        pt_links_inside['geometry'] = pt_links_inside.apply(lambda row: row.geometry.intersection(study_area_polygon), axis=1)

        # explode MultiLineString into LineString
        pt_links_inside = pt_links_inside.explode(index_parts=False).reset_index(drop=True)

        # Clean  GeoDataFrame from empty geometry :
        pt_links_inside = pt_links_inside[~pt_links_inside.is_empty]
        self.pt_links_inside = pt_links_inside[pt_links_inside.geometry.type.isin(['LineString', 'MultiLineString'])]
        # ---
