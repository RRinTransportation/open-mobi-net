import folium
from folium.features import GeoJsonTooltip
import pandas as pd
import geopandas as gpd 
import math 
import numpy as np 


def draw_lane(main_map,links_gdf,layer_name,link_color,tooltip_fields):
    
    layer_group_lane = folium.FeatureGroup(name=f"{layer_name} Lanes", show=False)
   
    tooltip = GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=[f"{field}:" for field in tooltip_fields],
        labels=True,
        localize=True,
        sticky=False,
        style="""
            background-color: #F0EFEF;
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """
    )
    folium.GeoJson(
        links_gdf,
        style_function=lambda x, color=link_color: {'color': color, 'weight': 3, 'opacity': 0.8},
        tooltip=tooltip,
    ).add_to(layer_group_lane)
    layer_group_lane.add_to(main_map)

    return main_map

def add_network_layer(main_map, links_gdf, all_nodes_gdf, layer_name, link_color, node_color):
    """
    Adds a layer of links, nodes, and directional arrows to a Folium map.
    """
    if links_gdf.empty:
        print(f"Layer '{layer_name}' is empty, skipping.")
        return

    # --- Tackle Links ---
    tooltip_fields = ['link_id', 'a_node', 'b_node', 'lanes_ab', 'lanes_ba','speed_ab', 'speed_ba', 'capacity_ab', 'capacity_ba','modes','link_type']
    main_map = draw_lane(main_map,links_gdf,layer_name,link_color,tooltip_fields) 
  

    # --- Tackle Nodes ---
    layer_group_nodes = folium.FeatureGroup(name=f"{layer_name} Nodes", show=False)
    node_ids = pd.unique(links_gdf[['a_node', 'b_node']].values.ravel('K'))
    associated_nodes = all_nodes_gdf[all_nodes_gdf['node_id'].isin(node_ids)]
    for _, node in associated_nodes.iterrows():
        folium.CircleMarker(
            location=[node.geometry.y, node.geometry.x],
            radius=4,
            color=node_color,
            fill=True,
            fill_color=node_color,
            fill_opacity=1.0,
            tooltip=f"Node ID: {node['node_id']}"
        ).add_to(layer_group_nodes)
    layer_group_nodes.add_to(main_map)
    

    # MODIFIED ARROWHEAD SECTION ================================================
    # --- Tackle Arrows ---
    layer_group_arrows = folium.FeatureGroup(name=f"{layer_name} Arrows", show=False)

    # Define arrow geometry (in coordinate degrees - works well for local maps)
    arrow_length_deg = 0.0002  # Length from tip to base
    arrow_width_deg = 0.0001  # Full width of the arrow base

    for _, link in links_gdf.iterrows():
        line = link['geometry']
        if not isinstance(line, object) or line.is_empty:
            continue

        # 1. Position the tip of the arrow
        p = 0.25
        tip_point = line.interpolate(p, normalized=True)

        # 2. Get the line's angle to orient the arrow
        p1 = line.interpolate(p-1e-3, normalized=True)
        p2 = line.interpolate(p+1e-3, normalized=True)
        angle_rad = math.atan2(p2.y - p1.y, p2.x - p1.x)

        # 3. Calculate the 3 vertices of the isosceles triangle
        # Vertex 1: The tip
        v1 = (tip_point.y, tip_point.x)

        # Find the center of the base by moving backward from the tip
        base_center_x = tip_point.x - arrow_length_deg * math.cos(angle_rad)
        base_center_y = tip_point.y - arrow_length_deg * math.sin(angle_rad)

        # Find the two base corners by moving perpendicularly from the base center
        perp_angle_rad = angle_rad + math.pi / 2
        half_width = arrow_width_deg / 2
        
        # Vertex 2: Right base corner
        v2_x = base_center_x + half_width * math.cos(perp_angle_rad)
        v2_y = base_center_y + half_width * math.sin(perp_angle_rad)
        v2 = (v2_y, v2_x)
        
        # Vertex 3: Left base corner
        v3_x = base_center_x - half_width * math.cos(perp_angle_rad)
        v3_y = base_center_y - half_width * math.sin(perp_angle_rad)
        v3 = (v3_y, v3_x)

        # 4. Draw the filled triangle using PolyLine
        folium.PolyLine(
            locations=[v1, v2, v3, v1], # Close the loop by repeating the first point
            color=link_color,
            weight=0, # No border
            fill=True,
            fill_color=link_color,
            fill_opacity=0.8
        ).add_to(layer_group_arrows)
        
    layer_group_arrows.add_to(main_map)
    # END OF MODIFIED SECTION ===================================================


    return main_map



def plot_layers_on_folium_map(layers_to_plot,
                              nodes_gdf,
                              location=[45.764, 4.8357],
                              tiles=None,
                              layercontrol=True,
                              ):
    assert np.sum([len(n['gdf']) == 0 for n in layers_to_plot]) == 0, "Some layers have no data to plot. Please check the filters applied."

    # Initialize the map, centered on Lyon
    if tiles is None:
        m = folium.Map(location=location, zoom_start=13)
    else:
        m = folium.Map(location=location, zoom_start=13,tiles=tiles)


    # Add each layer to the map using the function
    for layer in layers_to_plot:
        m = add_network_layer(
            main_map=m,
            links_gdf=layer["gdf"],
            all_nodes_gdf=nodes_gdf,
            layer_name=layer["name"],
            link_color=layer["link_color"],
            node_color=layer["node_color"]
        )


    # Add the LayerControl panel to the map
    if layercontrol:
        folium.LayerControl(collapsed=False).add_to(m)

    return m