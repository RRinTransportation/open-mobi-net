import argparse

CITY="Lyon"

parser = argparse.ArgumentParser(description='Build a multimodal network for a specified city.')

# Init 
parser.add_argument('--city', type=str, default=f"{CITY}", help='Name of the city to build the network for')
parser.add_argument('--folder_path', type=str, default=f"data/{CITY}/raw_data", help='Path to the folder containing raw data')

# Path to the traffic network shapefiles:
parser.add_argument('--IRIS_folder_path', type=str, default=f"data/{CITY}/raw_data/net_car/shapefiles_sym", help='Path to the folder containing IRIS zones shapefiles')
parser.add_argument('--file_name', type=str, default='Iris_Lyon.shp', help='Name of the shapefile containing the area of study')
parser.add_argument('--export_file', type=str, default="data.geojson", help='Path to the output file where the processed network will be saved')

# CRS of the traffic network shapefile:
parser.add_argument('--init_crs', type=str, default="EPSG:2154", help='Initial CRS of the shapefile')
parser.add_argument('--target_crs', type=str, default="EPSG:4326", help='Target CRS to which the shapefile will be reprojected')


# Selection of the area of study:
parser.add_argument('--selection_from_polygon', type=bool, default=True, help='Whether to select the area of study from a polygon')
parser.add_argument('--key_column', type=str, default=None, help='Name of the column to use for selecting the area of study')
parser.add_argument('--restricted_keys', type=list, default=None, help='List of values in the key_column to restrict the area of study to')
parser.add_argument('--shp_restriction_path', type=str, default=None, help='Path to a shapefile that can be used to restrict the area of study')

# Public transport (GTFS) parameters: 
parser.add_argument('--gtfs_folder_name', type=str, default='net_pt', help='Name of the folder where GTFS data is stored')
parser.add_argument('--gtfs_zip_name', type=str, default='lyon_tcl_gtfs.zip', help='Name of the GTFS zip file')
parser.add_argument('--agency_name', type=str, default='TCL', help='Name of the transit agency in the GTFS data')
parser.add_argument('--transit_date', type=str, default='2024-08-14', help='Date for which to load the transit data from the GTFS file (format: YYYY-MM-DD)') 

args = parser.parse_args(args=[])
# args = parser.parse_args()


