import geopandas as gpd 
import math
import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString
from shapely.ops import unary_union, linemerge
import networkx as nx
from tqdm import tqdm
from load_network.pt import get_candidates_links 

    
class MapMatchingPT2OSM():
    
    """ Process map matching between GTFS bus routes and OSM road network
    
    
    Could be smart to filter candidate in advance ... 
    Especially using "_find_possible_extremities" to filter out graph extremities that are not true bus route extremities
    """
    def __init__(self):

        self.excluded_link_types = ['pedestrian','footway','path','cycleway','steps','elevator','construction','living_street']


    def match_pt_to_osm(self, pt_links_inside, aequilibraebuilder):
        possible_tc_lanes = aequilibraebuilder.links[~aequilibraebuilder.links.link_type.isin(self.excluded_link_types)].copy()

        road_links = possible_tc_lanes.to_crs(epsg=2154)
        bus_routes = pt_links_inside[pt_links_inside.mode_name == 'Bus'].to_crs(epsg=2154).drop(columns=['index_right']).copy()
        bus_routes = bus_routes.drop_duplicates(subset=['geometry','route_id','mode'])  # Several identical route and path for just a different trip_id

        bus_routes_buffered = bus_routes.copy()
        bus_routes_buffered['geometry'] = bus_routes.geometry.buffer(10)

        candidate_matches = self._get_candidates_links(road_links,bus_routes_buffered)

        # 2. Identify which links are near the true start/end of each bus route
        bus_extremities_dict = self._find_bus_route_extremities(candidate_matches, bus_routes,10)

        # 3. For each route, find the best path among the filtered candidates
        final_link_indices = [] 
        sub_route_idx_col = 'index_bus'

        assert len(set(bus_extremities_dict.keys())) == len(bus_extremities_dict.keys()), "Duplicate route IDs found in bus_extremities_dict"

        final_pt_links = gpd.GeoDataFrame()
        for sub_route_id, route_extremities in tqdm(bus_extremities_dict.items(), desc="Processing Bus Routes"):

            # Could be smart to filter candidate in advance ... Especially using "_find_possible_extremities" to filter out graph extremities that are not true bus route extremities
            route_candidates = candidate_matches[candidate_matches[sub_route_idx_col] == sub_route_id].copy()

            route_ids = route_candidates['route_id'].unique()
            line_name = route_candidates.line_name.unique()
            assert len(route_ids) == 1, "Multiple route_ids found for a single bus route segment"
            assert len(line_name) == 1, "Multiple line_name found for a single bus route segment"
            route_id = route_ids[0]
            line_name = line_name[0]

            bus_geom = bus_routes.loc[sub_route_id].geometry
            
            start_links = route_extremities['start_bus_lane']
            end_links = route_extremities['end_bus_lane']

            # Find path with dijkstra optimization:
            best_path = self._find_best_path_for_route_optimized(route_candidates, start_links, end_links, bus_geom)
            if len(best_path) > 2:
                final_route = route_candidates[route_candidates.link_id.isin(best_path)]
                merged_geom = linemerge(unary_union(final_route.geometry))

                row = {'sub_route_id': sub_route_id, 'line_name': line_name, 'route_id': route_id, 'geometry': merged_geom, 'path_link_id': best_path}
                final_pt_links = pd.concat([final_pt_links, gpd.GeoDataFrame([row], geometry='geometry', crs=route_candidates.crs)], ignore_index=True)
            final_link_indices.extend(best_path)


        final_matches = road_links[road_links['link_id'].isin(list(set(final_link_indices)))]
        return final_matches, final_pt_links

    def _get_candidates_links(self, road_links, bus_routes_buffered):
        """
        Identifies road links that intersect with buffered bus routes.
        """
        candidate_matches = gpd.sjoin(
            road_links,
            bus_routes_buffered,
            how="inner",
            predicate='intersects', # Le critère clé
            lsuffix='road',
            rsuffix='bus'
        )
        return candidate_matches

    def _find_possible_extremities(self, candidates_gdf, link_id_col = 'link_id'):
        """
        Finds all links that are potential extremities in the candidate graph.
        An extremity is a link where at least one of its nodes has a degree of 1,
        meaning it connects to only one other link in the entire candidate set.
        """
        if candidates_gdf.empty:
            return set()
        
        node_counts = pd.concat([candidates_gdf['a_node'], candidates_gdf['b_node']]).value_counts()
        degree_one_nodes = set(node_counts[node_counts == 1].index)
        
        extremity_mask = candidates_gdf['a_node'].isin(degree_one_nodes) | candidates_gdf['b_node'].isin(degree_one_nodes)
        
        return set(candidates_gdf[extremity_mask][link_id_col])

    def _find_bus_route_extremities(self, candidates_gdf, bus_routes_gdf, epsilon=3):
        """
        Identifies which candidate links fall near the start and end points of each bus route.
        It creates a buffer of 'epsilon' meters around the first and last coordinate
        of each bus route's geometry and finds all candidate links that intersect these buffers.
        """
        extremities_dict = {}
        # Use the bus index from the join as the route_id
        bus_route_id_col = 'index_bus'
        link_id_col = 'link_id' if 'link_id' in candidates_gdf.columns else candidates_gdf.index.name

        unique_bus_routes = bus_routes_gdf.loc[candidates_gdf[bus_route_id_col].unique()]

        for route_id, bus_route in unique_bus_routes.iterrows():
            start_point = Point(bus_route.geometry.coords[0])
            end_point = Point(bus_route.geometry.coords[-1])

            start_buffer = start_point.buffer(epsilon)
            end_buffer = end_point.buffer(epsilon)

            start_candidates_mask = candidates_gdf.intersects(start_buffer)
            end_candidates_mask = candidates_gdf.intersects(end_buffer)

            start_links = list(set(candidates_gdf[start_candidates_mask][link_id_col]))
            end_links = list(set(candidates_gdf[end_candidates_mask][link_id_col]))
            
            extremities_dict[route_id] = {
                'start_bus_lane': start_links,
                'end_bus_lane': end_links
            }
        return extremities_dict

    def find_best_path_for_route(self, route_candidates_gdf, start_link_ids, end_link_ids, bus_route_geom):
        """
        Finds the best path of connected links for a single bus route.
        It builds a graph of candidate links for the route, finds all possible paths
        between the identified start and end links, and selects the path whose
        combined geometry is closest to the original bus route geometry based on
        the Hausdorff distance.
        """
        if route_candidates_gdf.empty or not start_link_ids or not end_link_ids:
            return []

        link_id_col = 'link_id' if 'link_id' in route_candidates_gdf.columns else route_candidates_gdf.index.name
        
        G = nx.from_pandas_edgelist(route_candidates_gdf, 'a_node', 'b_node', [link_id_col, 'geometry'])

        start_nodes = set(
            route_candidates_gdf[route_candidates_gdf[link_id_col].isin(start_link_ids)][['a_node', 'b_node']]
            .stack().unique()
        )
        end_nodes = set(
            route_candidates_gdf[route_candidates_gdf[link_id_col].isin(end_link_ids)][['a_node', 'b_node']]
            .stack().unique()
        )

        best_path_links = []
        min_distance = float('inf')

        # Create a mapping from nodes back to link_ids for path reconstruction
        edge_map = {}
        for _, row in route_candidates_gdf.iterrows():
            edge_map[(row['a_node'], row['b_node'])] = row[link_id_col]
            edge_map[(row['b_node'], row['a_node'])] = row[link_id_col]

        link_geometries = route_candidates_gdf.set_index(link_id_col)['geometry']

        for start_node in start_nodes:
            print('from node:', start_node)
            for end_node in end_nodes:
                print('  to node:', end_node)
                if start_node == end_node or not nx.has_path(G, start_node, end_node):
                    continue
                
                for node_path in nx.all_simple_paths(G, source=start_node, target=end_node):
                    print('      try path:', node_path)
                    path_links_ids = [edge_map[(node_path[i], node_path[i+1])] for i in range(len(node_path)-1)]
                    
                    path_geometries = [link_geometries.loc[link_id] for link_id in path_links_ids]
                    merged_geom_union = unary_union(path_geometries)
                    
                    if merged_geom_union.geom_type == 'MultiLineString':
                        merged_geom = linemerge(merged_geom_union)
                    else:
                        merged_geom = merged_geom_union

                    if not merged_geom.is_empty and merged_geom.geom_type.startswith('LineString'):
                        distance = bus_route_geom.hausdorff_distance(merged_geom)
                        if distance < min_distance:
                            min_distance = distance
                            best_path_links = path_links_ids

        return best_path_links


    def calculate_edge_weight(self, road_geom, bus_geom):
        """
        Calculates a 'cost' for a single road segment against the bus route.
        A lower cost means a better match. The cost is based on the average
        distance of the road segment from the bus route.
        We add a penalty if the road segment is much longer than the part of the bus route it covers.
        """
        # Project the start and end of the road segment onto the bus route
        start_proj_dist = bus_geom.project(Point(road_geom.coords[0]))
        end_proj_dist = bus_geom.project(Point(road_geom.coords[-1]))

        # Extract the portion of the bus route corresponding to the road segment
        if start_proj_dist > end_proj_dist:
            start_proj_dist, end_proj_dist = end_proj_dist, start_proj_dist

        # If end and start point are the same: 
        if abs(end_proj_dist - start_proj_dist) < 1e-6:
            return 1e6 # Return a high cost immediately
        # Extract the relevant part of the bus route by interpolating points
        coords = [bus_geom.interpolate(dist).coords[0] for dist in np.linspace(start_proj_dist, end_proj_dist, 10) if dist <= bus_geom.length]
        if len(coords) < 2:
            return 1e6 # Return a high cost if the segment doesn't map well
            
        bus_sub_geom = LineString(coords)

        # The cost is the average distance (Hausdorff) plus a length penalty
        distance_cost = road_geom.hausdorff_distance(bus_sub_geom)
        length_penalty = abs(road_geom.length - bus_sub_geom.length)
        
        # We square the distance to heavily penalize segments that are far away
        return (distance_cost**2) + length_penalty + 1 # Add 1 to avoid zero-cost edges


    def _find_best_path_for_route_optimized(self, route_candidates_gdf, start_link_ids, end_link_ids, bus_route_geom):
        """
        Finds the best path using a weighted graph and Dijkstra's algorithm.
        Instead of finding all paths, it finds the single path with the lowest
        cumulative 'cost', where cost is determined by geometric similarity to the bus route.
        This is exponentially faster than the previous brute-force method.
        """
        if route_candidates_gdf.empty or not start_link_ids or not end_link_ids:
            return []

        link_id_col = 'link_id' if 'link_id' in route_candidates_gdf.columns else route_candidates_gdf.index.name
        
        # Pre-calculate weights for all candidate edges
        route_candidates_gdf['weight'] = route_candidates_gdf['geometry'].apply(
            lambda geom: self.calculate_edge_weight(geom, bus_route_geom)
        )

        # Build the weighted graph
        G = nx.from_pandas_edgelist(
            route_candidates_gdf, 'a_node', 'b_node', edge_attr='weight'
        )

        start_nodes = set(
            route_candidates_gdf[route_candidates_gdf[link_id_col].isin(start_link_ids)][['a_node', 'b_node']]
            .stack().unique()
        )
        end_nodes = set(
            route_candidates_gdf[route_candidates_gdf[link_id_col].isin(end_link_ids)][['a_node', 'b_node']]
            .stack().unique()
        )
        
        best_path_nodes = []
        min_path_cost = float('inf')

        # Find the single best path using Dijkstra's algorithm for each start/end pair
        for start_node in start_nodes:
            for end_node in end_nodes:
                if start_node == end_node or not nx.has_path(G, start_node, end_node):
                    continue
                
                try:
                    # Use Dijkstra's algorithm to find the path with the lowest total weight
                    cost, node_path = nx.bidirectional_dijkstra(G, start_node, end_node, weight='weight')
                    
                    if cost < min_path_cost:
                        min_path_cost = cost
                        best_path_nodes = node_path
                except nx.NetworkXNoPath:
                    continue

        if not best_path_nodes:
            return []

        # Reconstruct the best path's link IDs from the node path
        edge_map = {}
        for _, row in route_candidates_gdf.iterrows():
            edge_map[(row['a_node'], row['b_node'])] = row[link_id_col]
            edge_map[(row['b_node'], row['a_node'])] = row[link_id_col]
        
        best_path_links = [edge_map[(best_path_nodes[i], best_path_nodes[i+1])] for i in range(len(best_path_nodes)-1)]
        
        return best_path_links
