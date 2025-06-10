import json
import xml.etree.cElementTree as ET
style = """
@page {  } 
table {
    border-collapse: collapse;
    margin:10
}
table tr {height: 26px;}
table td {font-size:14pt; border:1px solid; text-align: center}
.offRow {background-color:#eeeeee;}
.headerFinal {border-bottom-width:3;}
"""
def makeHtml(planSpec, entries):
    
    root = ET.Element("html")
    head = ET.SubElement(root, "head") 
    ET.SubElement(head, "style",{"type":"text/css"}).text = style
    body = ET.SubElement(root, "body",{"dir":"ltr"})

    table = ET.SubElement(body, "table")
    colgroup = ET.SubElement(table, "colgroup")
    for cw in planSpec["columnWidths"]:
        ET.SubElement(colgroup, "col",{"width":str(cw)})
    
    headerRows = planSpec["headerRows"]
    for i, hr in enumerate(headerRows):
        row = ET.SubElement(table, "tr")
        for hc in hr:
            attrs = {}
            if i == len(headerRows)-1:
                attrs["class"] = "headerFinal"
            if isinstance(hc, str):
                content = hc
            else:
                content = hc["name"]
                attrs["colspan"] = "3"
            ET.SubElement(row, "td", attrs).text = content
            
    if len(entries)<15:
        entries+=[{} for _ in range(15-len(entries))]
    for i,entry in enumerate(entries):
        entry['#'] = str(i + 1)
        for hr in headerRows:
            row = ET.SubElement(table, "tr")
            for hc in hr:
                attrs = {}
                if i%2 ==1:
                    attrs["class"]="offRow"
                if isinstance(hc, str):
                    column = hc
                else:
                    column = hc["name"]
                    attrs["colspan"] = "3"
                ET.SubElement(row, "td", attrs).text = entry.get(column,'')

    tree = ET.ElementTree(root)
    return tree


wpts = [{"Name":"TAKE-OFF", "Fuel (lb)": "8677","Delta (lb)":"355", "Tacan":"63X", "ETA":"1325z", "Velocity (IAS)":"340", "Position":"45 32 12N 13 53 11E", "Offset":"123@245","Distance":"138","Heading":"097", "Duration (min)":"18"}]
with open('planSpec.json') as planSpec:
    spec = json.load(planSpec)
    tree = makeHtml(spec,wpts)
    tree.write("filename.html")