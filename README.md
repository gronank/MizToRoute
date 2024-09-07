# MizToRoute
Tool for exporting dcs .miz files to route presets.

## Usage
* The program will read aicraft groups from a .miz file: It will use group name as the name of the preset and read name and altitude information about waypoints. The last waypoint may be a Landing waypoint.
* The program will generate the following files:
  * Route preset file named \<map name\> containing route presets
  * A kml file \<mission name\>.kml containing simple kml visualization of the routes
  * A text file \<mission name\>.txt containg the coordinates of the waypoints in plain text

## Exporting JF-17 polygons
The program will look for line and polygons named 'A' and 'B' and export these geometries in the format read by the JF-17. It creates a file customerAirSpace_\<map name\>.lua that should be placed in \<dcs install folder>/Mods/aircraft/JF-17/Doc/airspace.
