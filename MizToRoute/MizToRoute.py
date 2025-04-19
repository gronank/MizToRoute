from dcs import Mission
from pykml.factory import KML_ElementMaker as KML
import dcs.lua as lua
import sys
import math
import os,shutil
from lxml import etree
from pathlib import Path
from CreateKneeboard import printKneeboard
from FuelCalculation import CreateFuelConsumption

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

def degMinSec(deg):
    deg = abs(deg)
    (minutes, deg) = math.modf(deg)
    minutes*=60
    (sec, minutes) = math.modf(minutes)
    sec*=60
    return [deg, minutes, sec]
    
def toJeffCoordString(waypoint):
    p = waypoint.position.latlng()
    NS = "N" if p.lng >= 0 else "S"
    EW = "E" if p.lat >= 0 else "W"
    
    (latDeg,latMin, latSec) = degMinSec(p.lat)
    (longDeg,longMin, longSec) = degMinSec(p.lng)

    return f"{NS}{latDeg:02.0f} {latMin:02.0f} {latSec:04.1f} {EW}{longDeg:03.0f} {longMin:02.0f} {longSec:04.1f}"

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

def writeRoute(mission, path, outFolder):
    presets = {}
    missionName = Path(path).stem
    doc = createKmlDoc(path)
    flights = {}
    for group in loopGroups(mission):
        presets[group.name] = [p.dict() for p in group.points[1:]]
        exportKml(doc, group)
        exportWaypointCoords(flights, group)
        
    routeStr = lua.dumps(presets, "presets",1)

    fileName = f"{outFolder}/{mission.terrain.name}.lua"
    with open(fileName,"w") as outFile:
        outFile.write(routeStr)
    with open(f"{outFolder}/{missionName}.kml","wb") as out:
        out.write(etree.tostring(doc, pretty_print=True))
    with open(f"{outFolder}/{missionName}.txt","w") as out:
        for flightName, waypoints in flights.items():
            out.write(flightName+'\n')
            out.writelines("\n".join(waypoints))
            out.write("\n")
            
def toAirspace(point):
    latlng = point.latlng()
    return {"lat":latlng.lat,"lon":latlng.lng}

def writeAirspace(mission: Mission, outFolder):
    airspace = {}
    items = [item for layer in mission.drawings.layers for item in layer.objects]
    for item in items:
        if not item.name.upper() in ["A", "B"]:
            continue

        airspace[f'BKY{item.name.upper()}'] = {"closed" : False, "points":[toAirspace(point+item.position) for point in item.points]}
    if len(airspace) == 0:
        return
    airspaceStr = lua.dumps(airspace, "airspace",1)
    fileName =f'{outFolder}/customerAirSpace_{mission.terrain.name}.lua'
    with open(fileName,"w") as outFile:
        outFile.write(airspaceStr)

def writeKneeboard(mission, outFolder):
    for group in loopGroups(mission):
        replacements = {}
        fuel = CreateFuelConsumption(group)
        if not fuel:
            continue
        replacements[(2,3)] = [group.name, group.units[0].type]
        waypoints = []
        for i, wp in enumerate(group.points[1:]):
            fp = fuel.points[i]
            wpData = [str(i+1), wp.name, toJeffCoordString(wp), str(round(fp.remaining)) ]
            if fp.timeOnStation > 0:
                wpData.append(str(round(fp.timeOnStation)))
            waypoints.append(wpData)
            
        replacements[(5,1)] = waypoints
        replacements[(2,5)] = [str(int(round(fuel.bingo,-2))), str(int(round(fuel.joker,-2)))]
        printKneeboard(replacements, 'WP_base.xhtml', f'{group.name}.png', outFolder)

if __name__ =="__main__":
    path = sys.argv[1]
    outFolder = Path(path).stem
    if os.path.exists(outFolder) and os.path.isdir(outFolder):
        shutil.rmtree(outFolder)
    os.mkdir(outFolder)
    
    mission = Mission()
    mission.load_file(path)
    writeKneeboard(mission,outFolder)
    writeAirspace(mission,outFolder)
    writeRoute(mission, path,outFolder)
    
    
    