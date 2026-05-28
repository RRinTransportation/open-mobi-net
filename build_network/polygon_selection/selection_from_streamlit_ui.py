import streamlit as st
import geopandas as gpd
import os 
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

def get_polygon_from_streamlit_ui(
    gdf=None,
    centroid=None,
    save_path="data.geojson",
    target_crs="EPSG:4326",
):
    """Extract GeoDataFrame containing the selected area based on a polygon drawn by the user"""

    # Set center coordinates for the map
    if centroid is None:
        lat = gdf.to_crs(epsg=4326).geometry.centroid.y.mean()
        lon = gdf.to_crs(epsg=4326).geometry.centroid.x.mean()
    else:
        lat, lon = centroid[0], centroid[1]

    # Create a folium map centered on the location
    m = folium.Map(location=[lat, lon], zoom_start=12)
    
    # Add drawing tools to the map
    draw = Draw(export=True)
    draw.add_to(m)
    
    # Display the map and capture user interaction
    st.write("Draw a polygon on the map to select your area:")
    map_data = st_folium(m, width=700, height=500)

    # Allow the user to customize the export path
    save_path = st.text_input("Export path", value=save_path)
    
    # Extract the drawn polygon from map data
    drawn_polygon = None
    
    if map_data and map_data.get('all_drawings') and len(map_data['all_drawings']) > 0:
        for drawing in map_data['all_drawings']:
            # Get the geometry from the drawing
            geometry = drawing.get('geometry', {})
            
            if geometry.get('type') == 'Polygon':
                coords = geometry['coordinates'][0]
                # Convert [lon, lat] to [lat, lon] for Shapely
                polygon_coords = [(lon, lat) for lon, lat in coords]
                polygon = Polygon(polygon_coords)
                
                # Create a GeoDataFrame from the polygon
                drawn_polygon = gpd.GeoDataFrame(
                    [{"geometry": polygon}],
                    crs="EPSG:4326",
                )
                if target_crs:
                    drawn_polygon = drawn_polygon.to_crs(target_crs)
                st.success("Polygon extracted successfully!")
                break
    
    if drawn_polygon is None:
        st.info("No polygon drawn yet. Draw a polygon on the map to proceed.")
    else:
        if st.button("Save polygon"):
            if save_path:
                drawn_polygon.to_file(save_path, driver="GeoJSON")
                st.success(f"Polygon saved to {save_path}")
                st.components.v1.html("<script>window.parent.close();</script>", height=0)
            else:
                st.warning("Please provide a valid export path.")
    
    return drawn_polygon




if __name__ == "__main__":
    temp_gdf_path = os.environ.get("TEMP_GDF_PATH")
    loaded_gdf = gpd.read_file(temp_gdf_path)
    get_polygon_from_streamlit_ui(gdf=loaded_gdf)