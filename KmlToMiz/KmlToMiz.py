import re
from sys import argv
import urllib.request as url
from lxml import etree
from dcs import Mission
from dcs.terrain import Kola
from dcs.mapping import Point, LatLng
from dcs.drawing import Rgba
import re
from urllib.parse import urlparse
from urllib.parse import parse_qs
import json

# images = {
#     re.compile(".*(Motor|Air Assault|Marine|Nord)"): "P91000004.png",
#     re.compile("(Armor|Norrbotten)"): "P91000001.png",
#     re.compile("Headquarters"): "P91000071.png",
#     re.compile("Art"): "P91000006.png",
#     re.compile("(BTG|Swedish|Finnish|HV|MEB|Special Border)"): "P91000201.png",
#     re.compile("ADA"): "P91000011.png",
#     re.compile("Battery"): "P91000009.png",
#     re.compile("Supply"): "P91000207.png",
#     re.compile("Base"): "P91000076.png",
# }

def findPicture(name, pictureRules):
    for matcher, path in pictureRules.items():
        if(matcher.search(name)):
            return path

def isGeometry(element, geometry):
    return element.find("{http://www.opengis.net/kml/2.2}"+geometry) != None

def parseCoordinates(element, terrain):
    points = []
    coordinates = element.findtext(".//{http://www.opengis.net/kml/2.2}coordinates")
    for coordinate in coordinates.split('\n')[1:-1]:
        lng,lat = coordinate.strip().split(",")[:2]
        points.append(Point.from_latlng(LatLng(lat,lng),terrain))
    return points

def parseColor(element):
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
    
def addSymbols(layer, folderElement, color, terrain, pictureRules):
    for placemark in folderElement.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        if not isGeometry(placemark,"Point"):
            continue
        name = placemark.findtext(".//{http://www.opengis.net/kml/2.2}name")
        picturePath = findPicture(name, pictureRules)
        position = parseCoordinates(placemark, terrain)[0]
        layer.add_text_box(position, f'   {name}', color = color, fill = Rgba(0,0,0,100))
        layer.add_icon(position, picturePath,color=color)
        
def addPolygons(layerDcs, layerKml, kmlDoc, terrain):
    for placemark in layerKml.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        name = placemark.findtext(".//{http://www.opengis.net/kml/2.2}name")
        if not isGeometry(placemark,"Polygon"):
            continue
        coordinates = parseCoordinates(placemark, terrain)
        lineColor, fillColor = parseStyle(placemark, kmlDoc)
        layerDcs.add_freeform_polygon(Point(0,0,terrain), coordinates, color = Rgba(*lineColor), fill = Rgba(*fillColor))
        

def modifyLink(link):
    url = urlparse(link)
    mid = parse_qs(url.query)["mid"][0]
    base = link.split("?")[0]
    base = base.replace("/viewer","/kml")
    return f"{base}?mid={mid}&resourcekey&forcekml=1"

jsonPath = argv[1]
with open(jsonPath,"r") as jsonFile:
    rules = json.loads(jsonFile.read())

    
modifiedLink = modifyLink(rules["url"])
response = url.urlopen(modifiedLink)
if response.status != 200:
    print(f"Unexpected error: {response.reson}")

kmlDoc = etree.fromstring(response.read())

febaName = kmlDoc.xpath(".//*[text()='Forward Edge of Battle Area']")[0]
feba = febaName.getparent()

terrain = Kola()
points = parseCoordinates(feba, terrain)

mission = Mission(terrain)
layerDcs = mission.drawings.get_layer_by_name("Author")
layerDcs.add_line_freeform(Point(0,0,terrain),points)


for layerRule in rules["layers"]:
    layerName = layerRule["name"]
    layerKml = kmlDoc.xpath(f".//*[text()='{layerName}']")[0].getparent()
    color = [int(i) for i in layerRule["symbolColor"]]
    pictureRules = {re.compile(rule):value for (rule,value) in layerRule["symbolRules"]}
    addPolygons(layerDcs, layerKml, kmlDoc, terrain)
    addSymbols(layerDcs, layerKml, Rgba(*color), terrain, pictureRules)

#alpha = 230
#russianSymbols = kmlDoc.xpath(".//*[text()='Russian Ground Forces']")[0].getparent()
#addSymbols(layerDcs, russianSymbols, Rgba(255,128,128,alpha), terrain)

#natoSymbols = kmlDoc.xpath(".//*[text()='Combined Force Land Component']")[0].getparent()

missionName = kmlDoc.findtext(".//{http://www.opengis.net/kml/2.2}name")
mission.save(f"{missionName}.miz")
print(modifiedLink=="https://www.google.com/maps/d/u/0/kml?mid=11wFbORd-qUVfdvC7emmXcKaj_JG4H38&resourcekey&forcekml=1")