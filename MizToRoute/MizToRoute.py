from dcs import Mission
from pykml.factory import KML_ElementMaker as KML
import dcs.lua as lua
import sys
import math
from lxml import etree
from pathlib import Path

stylename = "waypointStyle"

def loopGroups(mission):
    for coalition in mission.coalition.values():
        for country in coalition.countries.values():
            for group in country.plane_group:
                yield group
                
def toKmlCoord(waypoint):
    p = waypoint.position.latlng()
    return f"{p.lng},{p.lat},{waypoint.alt}"

def toCoordString(waypoint):
    p = waypoint.position.latlng()
    NS = "N" if p.lng >= 0 else "S"
    EW = "E" if p.lat >= 0 else "W"
    lng = abs(p.lng)
    lat = abs(p.lat)
    (longMin,longDeg) = math.modf(p.lng)
    (latMin,latDeg) = math.modf(p.lat)
    return f"{NS}{latDeg:0.0f} {latMin*60:06.3f} {EW}{longDeg:0.0f} {longMin*60:06.3f}"

def toKmlPoint(waypoint):
    altMode="absolute" if waypoint.alt_type == "BARO" else "relativeToGround"
    
    return KML.Point(KML.coordinates(toKmlCoord(waypoint)),KML.altitudeMode(altMode))

def exportKml(doc, group):
    routeName = group.name
    linePoints = []
    wayPoints = []

    for wp in group.points[1:]:
        wayPoints.append(KML.Placemark(KML.name(wp.name),KML.styleUrl(f'#{stylename}'), toKmlPoint(wp)))
        linePoints.append(toKmlCoord(wp))

    routeLine = KML.Placemark(KML.name(routeName), KML.LineString(KML.coordinates("\n".join(linePoints))))
    wpFolder= KML.Folder(KML.name(routeName), routeLine,*wayPoints)
    doc.Document.append(wpFolder)
    
def exportWaypointCoords(flights, group):
    coordinateString = []
    for wp in group.points[1:]:
        coordText = f"{toCoordString(wp)}  {wp.name}".rstrip()
        coordinateString.append(coordText)
        
    flights[group.name] = coordinateString
    
def createKmlDoc(missionName):
    
    return KML.kml(
        KML.Document(
            KML.Name(missionName),
            KML.Style(
                KML.IconStyle(
                    KML.scale(1.2),
                    KML.Icon(
                        KML.href("http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png")
                    ),
                ),
                id=stylename,
            )
        )
    )
def writeRoute(mission, path):
    
    presets = {}
    
    missionName = Path(path).stem
    doc = createKmlDoc(path)
    flights = {}
    for group in loopGroups(mission):
        presets[group.name] = [p.dict() for p in group.points[1:]]
        exportKml(doc, group)
        exportWaypointCoords(flights, group)
        

    routeStr = lua.dumps(presets, "presets",1)

    fileName = f"{mission.terrain.name}.lua"
    with open(fileName,"w") as outFile:
        outFile.write(routeStr)
    with open(f"{missionName}.kml","wb") as out:
        out.write(etree.tostring(doc, pretty_print=True))
    with open(f"{missionName}.txt","w") as out:
        for flightName, waypoints in flights.items():
            out.write(flightName+'\n')
            out.writelines("\n".join(waypoints))
            out.write("\n")
            
def toAirspace(point):
    latlng = point.latlng()
    return {"lat":latlng.lat,"lon":latlng.lng}

def writeAirspace(mission: Mission):
    airspace = {}
    items = [item for layer in mission.drawings.layers for item in layer.objects]
    for item in items:
        if not item.name.upper() in ["A", "B"]:
            continue

        airspace[f'BKY{item.name.upper()}'] = {"closed" : False, "points":[toAirspace(point+item.position) for point in item.points]}
    if len(airspace) == 0:
        return
    airspaceStr = lua.dumps(airspace, "airspace",1)
    fileName =f'customerAirSpace_{mission.terrain.name}.lua'
    with open(fileName,"w") as outFile:
        outFile.write(airspaceStr)

if __name__ =="__main__":
    path = sys.argv[1]
    mission = Mission()
    mission.load_file(path)
    writeAirspace(mission)
    writeRoute(mission, path)
    
    