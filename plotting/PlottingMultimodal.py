from plotting.plotting_folium import plot_layers_on_folium_map,plot_zones,draw_lane
import xyzservices.providers as xyz
import folium 


class PlottingMultimodal():
    """
    Plots the multimodal network using Folium.
    We first extract the different sub-networks (car, bike, walk) from the Aequilibrae network GeoDataFrame.
    Then we define the layers and their styles.
    Finally, we plot the layers on a Folium map, and add the GTFS network as an additional layer.
    We also add a layer control to toggle the visibility of each layer.
    """
    def __init__(self, aequilibraebuilder, gtfs_network_builder, 
                 gdf_init_zones = None,
                 gdf_agg_zones = None,
                 Layers: list[str] = ["Car", "Bike", "Cycling Lanes", "Walk Only"]):
        self.network_gdf = aequilibraebuilder.traffic_network
        self.nodes_gdf = aequilibraebuilder.nodes
        self.final_pt_links = gtfs_network_builder.final_pt_links
        self.final_matches = getattr(gtfs_network_builder, 'final_matches', None)
        self.pt_bus_routes_init = getattr(gtfs_network_builder, 'pt_bus_routes_init', None)
        self.Layers = Layers
        self.gdf_init_zones = gdf_init_zones
        self.gdf_agg_zones = gdf_agg_zones
        self.own_bike_lanes = getattr(aequilibraebuilder, 'bike_lanes', None)
        self._extract_subnetworks()
        self._get_road_lane_without_direction()
        self._get_own_loaded_bike_layers()
        self._get_pt_bus_diagnostic_layers()

    def plotting(self,save=None):
        
        # --- Plotting 
        m =  plot_layers_on_folium_map(self.layers_to_plot,
                                        self.nodes_gdf,
                                        location=self.network_gdf.unary_union.centroid.coords[0][::-1],

                                        # tiles=xyz.Esri.WorldGrayCanvas.build_url(),
                                        # attr=xyz.Esri.WorldGrayCanvas.html_attribsution,

                                        tiles = "OpenStreetMap",

                                        # tiles = "Cartodb positron", 
                                        layercontrol = False
                                        )

        # Initial GTFS bus sub-routes (matched / not matched), drawn below the map matched ones:
        for layer in self.pt_bus_init_layers:
            m = draw_lane(main_map=m,
                          links_gdf=layer['gdf'],
                          layer_name=layer['name'],
                          link_color=layer['link_color'],
                          tooltip_fields=layer['tooltip'])

        m = draw_lane(main_map=m,
                links_gdf=self.final_pt_links,
                layer_name="PT bus map-matched",
                link_color="#2278f0",
                tooltip_fields=['line_name','sub_route_id','route_id'])

        if self.pt_bus_osm_links_layer:
            m = draw_lane(main_map=m,
                          links_gdf=self.pt_bus_osm_links_layer['gdf'],
                          layer_name=self.pt_bus_osm_links_layer['name'],
                          link_color=self.pt_bus_osm_links_layer['link_color'],
                          tooltip_fields=self.pt_bus_osm_links_layer['tooltip'])

        if self.road_lane_anomalies:
            m = draw_lane(main_map=m,
                          links_gdf=self.road_lane_anomalies['gdf'],
                          layer_name = self.road_lane_anomalies['name'],
                          link_color = self.road_lane_anomalies['link_color'],
                          tooltip_fields= self.road_lane_anomalies['tooltip']
            )

        # Bike network loaded from our own shapefiles (not from OSM):
        for layer in self.own_bike_layers:
            m = draw_lane(main_map=m,
                          links_gdf=layer['gdf'],
                          layer_name=layer['name'],
                          link_color=layer['link_color'],
                          tooltip_fields=layer['tooltip'])


        m = plot_zones(m, self.gdf_init_zones, self.gdf_agg_zones)

        folium.LayerControl(collapsed=False).add_to(m)

        # Save the map to an HTML file
        if save is not None:
            m.save(save)
        # display :
        return m


    def _extract_subnetworks(self):
        # --- Extract Sub-Networks
        w_network = self.network_gdf[(self.network_gdf["modes"].str.contains("w")) & (self.network_gdf['link_type'] == 'pedestrian') | (self.network_gdf['link_type'] == 'footway')   ]
        b_network = self.network_gdf[(self.network_gdf["modes"].str.contains("b"))  & ~(self.network_gdf['link_type'] == 'footway')] # & ~(self.network_gdf['link_type'] == 'pedestrian') 
        bb_network =  self.network_gdf[(self.network_gdf["modes"].str.contains("b"))  & (self.network_gdf['link_type'] == 'cycleway')] 
        c_network = self.network_gdf[(self.network_gdf['modes'].str.contains('c')) & ~(self.network_gdf['link_type'] == 'pedestrian') & ~(self.network_gdf['link_type'] == 'footway') & ~(self.network_gdf['link_type'] == 'service')]
        service_network = self.network_gdf[(self.network_gdf['modes'].str.contains('c')) & (self.network_gdf['link_type'] == 'service')]
        added_car_lanes = self.network_gdf[(self.network_gdf['added_lane'] == True) & (self.network_gdf['modes'].str.contains('c')) & ~(self.network_gdf['link_type'] == 'pedestrian') & ~(self.network_gdf['link_type'] == 'footway') ]
        original_car_lanes = self.network_gdf[(self.network_gdf['added_lane'] == False) & (self.network_gdf['modes'].str.contains('c'))& ~(self.network_gdf['link_type'] == 'pedestrian') & ~(self.network_gdf['link_type'] == 'footway') ]
        # ---

        potential_layers_to_plot = [
            {"name": "Car", "gdf": c_network, "link_color": "#8A2BE2", "node_color": "#DDA0DD"},
            {"name": "Services Lanes", "gdf": service_network, "link_color": "black", "node_color": "black"},
            {"name": "Original Car with direction", "gdf": original_car_lanes, "link_color": "#003366", "node_color": "#0077B6"},
            {"name": "Added Car lane directions", "gdf": added_car_lanes, "link_color": "#FF6B6B", "node_color": "#C44536"},
            {"name": "Bike", "gdf": b_network, "link_color": "#2ca02c", "node_color": "#98df8a"},
            {"name": "Cycling Lanes", "gdf": bb_network, "link_color": "#D93F8D", "node_color": "#E090B8"},
            {"name":  "Walk Only", "gdf": w_network, "link_color": "#ff7f0e", "node_color": "#ffbb78"},
        ]

        self.layers_to_plot = [layer for layer in potential_layers_to_plot if layer['name'] in self.Layers]

    def _get_own_loaded_bike_layers(self):
        '''Layers of the bike network loaded from our own shapefiles (aequilibraebuilder.bike_lanes),
        to be distinguished from the 'Bike' and 'Cycling Lanes' layers which come from the OSM network.'''
        self.own_bike_layers = []
        if self.own_bike_lanes is None or self.own_bike_lanes.empty:
            return
        tooltip = [c for c in ['link_id', 'anode', 'bnode', 'is_bike'] if c in self.own_bike_lanes.columns]
        self.own_bike_layers.append({"name": "own_loaded_bikes", "gdf": self.own_bike_lanes, "link_color": "#17becf", "tooltip": tooltip})
        if 'is_bike' in self.own_bike_lanes.columns:
            is_bike_lanes = self.own_bike_lanes[self.own_bike_lanes['is_bike'] == 1]
            if not is_bike_lanes.empty:
                self.own_bike_layers.append({"name": "own_loaded_bikes is_bike", "gdf": is_bike_lanes, "link_color": "#0B6E4F", "tooltip": tooltip})

    def _get_pt_bus_diagnostic_layers(self):
        '''Layers to check the bus map matching: initial GTFS sub-routes split into matched / not matched
        (outcome, lengths and Hausdorff distance in the tooltip), and the OSM links used by the map matching (final_matches).
        Networks saved before PLAN-002 have no pt_bus_routes_init: the initial GTFS layers are then skipped.'''
        self.pt_bus_init_layers = []
        if self.pt_bus_routes_init is not None and not self.pt_bus_routes_init.empty:
            init = self.pt_bus_routes_init.copy()
            for column in ['len_init_m', 'len_matched_m', 'hausdorff_m']:
                init[column] = init[column].round(1)
            tooltip = ['sub_route_id', 'line_name', 'route_id', 'status', 'n_candidates', 'n_links_path', 'len_init_m', 'len_matched_m', 'hausdorff_m']
            is_matched = init['status'] == 'matched'
            for name, gdf, color in [("PT bus GTFS init - matched", init[is_matched], "#00A86B"),
                                     ("PT bus GTFS init - not matched", init[~is_matched], "#E41A1C")]:
                if not gdf.empty:
                    self.pt_bus_init_layers.append({"name": name, "gdf": gdf, "link_color": color, "tooltip": tooltip})

        self.pt_bus_osm_links_layer = None
        if self.final_matches is not None and not self.final_matches.empty:
            tooltip = [c for c in ['link_id', 'link_type', 'name', 'modes'] if c in self.final_matches.columns]
            self.pt_bus_osm_links_layer = {"name": "PT bus OSM links used", "gdf": self.final_matches, "link_color": "#555555", "tooltip": tooltip}

    def _get_road_lane_without_direction(self):
        '''Extract road lane that have either 0 lanes or a "null" number of lane in both possible directions'''
        name2pos = {self.layers_to_plot[k]['name']:k for k in range(len(self.layers_to_plot))}
        pos_car = name2pos['Car'] if 'Car' in name2pos.keys() else None
        if pos_car is not None: 
            c_network = self.layers_to_plot[pos_car]['gdf']
            # --- Explore anomalies in the car network :
            mask_anomaly = ((c_network['lanes_ab'].isnull() | (c_network['lanes_ab'] == 0)) &
                            (c_network['lanes_ba'].isnull() | (c_network['lanes_ba'] == 0))
                        )
            self.road_lane_anomalies = {'name':'Car anomalies', 
                                        'gdf': c_network[mask_anomaly], 
                                        "link_color":  "#38025C", 
                                        "tooltip": ["lanes_ab", "lanes_ba", "capacity_ab", "capacity_ba", "speed_ab", "speed_ba", "modes", "link_type"]
            }
        else:
            self.road_lane_anomalies = None