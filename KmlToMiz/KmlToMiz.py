import re
import urllib.request as url
from lxml import etree
from dcs import Mission
from dcs.terrain import Kola
from dcs.mapping import Point, LatLng
from dcs.drawing import Rgba
import re

images = {
    re.compile(".*(Motor|Air Assault|Marine|Nord)"): "P91000004.png",
    re.compile("(Armor|Norrbotten)"): "P91000001.png",
    re.compile("Headquarters"): "P91000071.png",
    re.compile("Art"): "P91000006.png",
    re.compile("(BTG|Swedish|Finnish|HV|MEB)"): "P91000201.png",
    re.compile("ADA"): "P91000011.png",
    re.compile("Battery"): "P91000009.png",
    re.compile("Supply"): "P91000207.png",
    re.compile("Base"): "P91000076.png",
}

def findPicture(name):
    for matcher, path in images.items():
        if(matcher.search(name)):
            return path
    raise Exception(f"Could not find symbol for: {name}")

def parseCoordinates(element, terrain):
    points = []
    coordinates = element.findtext(".//{http://www.opengis.net/kml/2.2}coordinates")
    for coordinate in coordinates.split('\n')[1:-1]:
        lng,lat = coordinate.strip().split(",")[:2]
        points.append(Point.from_latlng(LatLng(lat,lng),terrain))
    return points

def addSymbols(layer, folderElement, color, terrain):
    for placemark in folderElement.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        name = placemark.findtext(".//{http://www.opengis.net/kml/2.2}name")
        picturePath = findPicture(name)
        position = parseCoordinates(placemark, terrain)[0]
        layer.add_text_box(position, f'   {name}', color = color, fill = Rgba(0,0,0,100))
        layer.add_icon(position, picturePath,color=color)
        
        


rawLink = "https://www.google.com/maps/d/u/0/viewer?mid=11wFbORd-qUVfdvC7emmXcKaj_JG4H38&femb=1&ll=67.954923925582%2C26.953305015127313&z=6"
def modifyLink(link):
    base = link.split('&')[0]
    base = base.replace("/viewer?","/kml?")
    return base + "&resourcekey&forcekml=1"


    
modifiedLink = modifyLink(rawLink)
response = url.urlopen(modifiedLink)
if response.status != 200:
    print(f"Unexpected error: {response.reson}")

kmlDoc = etree.fromstring(response.read())

febaName = kmlDoc.xpath(".//*[text()='Forward Edge of Battle Area']")[0]
feba = febaName.getparent()

terrain = Kola()
points = parseCoordinates(feba, terrain)

mission = Mission(terrain)
layer = mission.drawings.get_layer_by_name("Author")
layer.add_line_freeform(Point(0,0,terrain),points)

alpha = 230
russianSymbols = kmlDoc.xpath(".//*[text()='Russian Ground Forces']")[0].getparent()
addSymbols(layer, russianSymbols, Rgba(255,128,128,alpha), terrain)

natoSymbols = kmlDoc.xpath(".//*[text()='Combined Force Land Component']")[0].getparent()
addSymbols(layer, natoSymbols, Rgba(128,224,255,alpha), terrain)
missionName = kmlDoc.findtext(".//{http://www.opengis.net/kml/2.2}name")
mission.save(f"{missionName}.miz")
print(modifiedLink=="https://www.google.com/maps/d/u/0/kml?mid=11wFbORd-qUVfdvC7emmXcKaj_JG4H38&resourcekey&forcekml=1")