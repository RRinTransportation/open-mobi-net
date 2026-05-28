## Input: 

- GTFS files should be placed in a .zip containing all the GTFS files in .txt format.

- If Links.shp and Nodes.shp from GTFS are not already saved, pre-processing can be particularly time-consuming (~1h for Lyon on a standard laptop)

`utils/network.py` has been arbitrary filled with assumption that should be revised 


## Identified Limits:

`arrows` from `bike` lack one direction. 