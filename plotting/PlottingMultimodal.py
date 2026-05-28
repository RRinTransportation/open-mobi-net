from plotting.plotting_folium import plot_layers_on_folium_map
from plotting.plotting_folium import draw_lane
import folium 


class PlottingMultimodal():
    """
    Plots the multimodal network using Folium.
    We first extract the different sub-networks (car, bike, walk) from the Aequilibrae network GeoDataFrame.
    Then we define the layers and their styles.
    Finally, we plot the layers on a Folium map, and add the GTFS network as an additional layer.
    We also add a layer control to toggle the visibility of each layer.
    """
    def __init__(self, aequilibraebuilder, gtfs_network_builder, Layers: list[str] = ["Car", "Bike", "Cycling Lanes", "Walk Only"]):
        self.network_gdf = aequilibraebuilder.traffic_network
        self.nodes_gdf = aequilibraebuilder.nodes
        self.final_pt_links = gtfs_network_builder.final_pt_links
        self.Layers = Layers
        self._extract_subnetworks()

    def plotting(self,save=None):
        
        # --- Plotting 
        m =  plot_layers_on_folium_map(self.layers_to_plot,
                                        self.nodes_gdf,
                                        location=self.network_gdf.unary_union.centroid.coords[0][::-1],
                                        tiles = "Cartodb positron", 
                                        layercontrol = False
                                        )

        m = draw_lane(main_map=m,
                links_gdf=self.final_pt_links,
                layer_name="PT",
                link_color="#2278f0",
                tooltip_fields=['line_name','sub_route_id','route_id'])

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