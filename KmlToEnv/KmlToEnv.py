import json
from sys import argv
import uuid
from urllib.parse import urlparse
from urllib.parse import parse_qs
from lxml import etree
import urllib.request as url

def formatUuid():
    return f"{{{str(uuid.uuid4())}}}"

def modifyLink(link):
    url = urlparse(link)
    mid = parse_qs(url.query)["mid"][0]
    base = link.split("?")[0]
    base = base.replace("/viewer","/kml")
    base = base.replace("/edit","/kml")
    return f"{base}?mid={mid}&resourcekey&forcekml=1"

def formatColor(color):
    return '#'+"".join(f"{v:02x}" for v in color[::-1])

def isGeometry(element, geometry):
    return element.find("{http://www.opengis.net/kml/2.2}"+geometry) != None
    
def parseCoordinates(element):
    points = []
    coordinates = element.findtext(".//{http://www.opengis.net/kml/2.2}coordinates")
    for coordinate in coordinates.split('\n')[1:-1]:
        lng,lat = coordinate.strip().split(",")[:2]
        points.append({
                    "latitude": lat,
                    "longitude": lng
                })
    return points

def parseColor(element):
    if element is None:
        return (0,0,0,0)
    colorHex = element.findtext("{http://www.opengis.net/kml/2.2}color")
    return (int(colorHex[6:8],16),
    int(colorHex[4:6],16),
    int(colorHex[2:4],16),
    int(colorHex[0:2],16))

def parseStyle(placemark, kmlDoc):
    styleUrl = placemark.findtext(".//{http://www.opengis.net/kml/2.2}styleUrl").lstrip("#")
    style = kmlDoc.xpath(f".//*[@id='{styleUrl}-normal']")[0]
    lineStyle = style.find("{http://www.opengis.net/kml/2.2}LineStyle")
    polyStyle = style.find("{http://www.opengis.net/kml/2.2}PolyStyle")
    return (parseColor(lineStyle),parseColor(polyStyle))

global lineCount
lineCount = 2000
def addLine(layerEnv, lineKml, kmlDoc):
    color,colorBg = parseStyle(lineKml, kmlDoc)
    name = lineKml.findtext(".//{http://www.opengis.net/kml/2.2}name")
    line = {"author": "",
            "brushStyle": 1,
            "color": formatColor(color),
            "colorBg": "#00000000",
            "id": formatUuid(),
            "lineWidth": 1,
            "name": name,
            "points": parseCoordinates(lineKml),
            "shared": False,
            "timestamp": "",
            "type": "line",
            "visible": True}
    
    layerEnv["drawings"].append(line)

def addPolygons(layerEnv, layerKml, kmlDoc):
    for polygonKml in layerKml.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        if not isGeometry(polygonKml,"Polygon"):
            continue
        color,colorBg = parseStyle(polygonKml, kmlDoc)
        name = polygonKml.findtext(".//{http://www.opengis.net/kml/2.2}name")
        polygon ={#"author": "",
            "brushStyle": 1,
            "color": formatColor(color),
            "colorBg": formatColor(colorBg),
            "id": formatUuid(),
            "lineWidth": 1,
            "name": name,
            "points": parseCoordinates(polygonKml),
            "shared": False,
            "timestamp": "",
            "type": "polygon",
            "visible": True
            }
        layerEnv["drawings"].append(polygon)

def addSymbols(layerEnv, layerKml, color):
    
    for placemark in layerKml.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        if not isGeometry(placemark,"Point"):
            continue
        name = placemark.findtext(".//{http://www.opengis.net/kml/2.2}name")
        position = parseCoordinates(placemark)[0]

        p = parseCoordinates(placemark)[0]
        symbol = {"author": "",
            "brushStyle": 1,
            "classification": {
                "classification": "hostile",
                "dimension": "ground",
                "sub_dimension": ""
            },
            "color": formatColor(color),
            "colorBg": formatColor((0,0,0,100)),
            "font": {
                "color": "#ffd5b97b",
                "font": "Lato"
            },
            "id": formatUuid(),
            "latitude": p["latitude"],
            "lineWidth": 10,
            "longitude": p["longitude"],
            "name": name,
            "shared": False,
            "text": name,
            "timestamp": "",
            "type": "symbol"}
        layerEnv["drawings"].append(symbol)

def parseKMLSite(layerEnv, rules):
    modifiedLink = modifyLink(rules["url"])
    response = url.urlopen(modifiedLink)
    if response.status != 200:
        print(f"Unexpected error: {response.reson}")
    result = response.read()
    kmlDoc = etree.fromstring(result)
    
    for layerRule in rules["layers"]:
        layerName = layerRule["name"]
        layerKml = kmlDoc.xpath(f".//*[text()='{layerName}']")[0].getparent()
        
        if layerRule.get("isLine",False):
            addLine(layerEnv, layerKml, kmlDoc)
            continue
        color = [int(i) for i in layerRule["symbolColor"]]
        if layerRule.get("readPolygons",False):
            addPolygons(layerEnv, layerKml, kmlDoc)
        addSymbols(layerEnv, layerKml, color)
        
    return kmlDoc.findtext(".//{http://www.opengis.net/kml/2.2}name")

layerEnv = {"author": "me",
            "drawings":[],
            "enable": "true",
    "id": formatUuid(),
    "name": "Default layer",
    "shared": False,
    "timestamp": "",
    "type": "layer",
    "version": "2.4.0.400",
    "visible": True}

jsonPath = argv[1]
with open(jsonPath,"r") as jsonFile:
    rules = json.loads(jsonFile.read())
missionName ="default"
for layerRule in rules:
    name = parseKMLSite(layerEnv, layerRule)
    if missionName == "default":
        missionName = name
        
with open(f"{missionName}.env","w") as outFile:
    outFile.write(json.dumps(layerEnv, indent=4))

