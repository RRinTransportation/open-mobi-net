# Multi-Modal Network Extration (MMNE)
The repository aims to provide an automated pipeline where a multimodal transport network can be generated that is entirely projected onto the same graph (OSM).

In a second phase, it will involve generating OD matrices and calibrating demand models from loop sensors.

## Usage example:

Input for operation:
store data in a `data/` folder containing a subfolder associated with the studied city (e.g., `data/lyon/`), where the raw data file is located (e.g., `data/lyon/raw_data/`), containing the necessary data for the construction of the transport network:
    - Bike network: `net_bike/shapes/` containing the files `links_processed.shp` and `nodes_processed.shp`
    - Iris Zones: `net_car/shapefiles_sym/` containing the IRIS zones shapefile
    - Public Transport: `net_pt/GTFS/` containing the GTFS folder.zip (e.g., `net_pt/gtfs/lyon_tcl_gtfs.zip`), composed of .txt files (e.g., `stops.txt`, `stop_times.txt`, `trips.txt`, `routes.txt` ...)

## Good to know:
- If Links.shp and Nodes.shp from GTFS are not already saved, pre-processing can be particularly time-consuming (~1h for Lyon on a standard laptop). After this step, they are saved in `net_pt/lines/lines.shp` and `net_pt/stops/stops.shp` to avoid having to redo the extraction each time.

## To do:
- Correct errors during map-matching of bus lines on the OSM network
- Add zoning (already partially done with IRIS or tessellation defined from aggregated IRIS zones)
- Currently, builds all defined possible modes.
  - To do: Add exceptions to handle the import of a subset of modes among [Car, Public transport, bike, walk]
- `utils/network.py` has been arbitrarily filled with assumptions that should be revised
- `arrows` from `bike` lack one direction.