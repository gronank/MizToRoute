from html2image import Html2Image
from xml.dom.minidom import parse, parseString
hti = Html2Image(browser="chrome", 
    custom_flags=[
        '--no-sandbox', 
        '--headless', 
        #'--disable-gpu', 
        '--disable-software-rasterizer', 
        '--disable-dev-shm-usage'
    ])
hti.size = (700, 1000)

def removeTextNodes(node):
    for child in node.firstChild.childNodes:
        if child.nodeType == node.TEXT_NODE:
            node.firstChild.removeChild(child)

def printKneeboard(replacements, baseHtml, outFile):
    kneeboardBaseXml = parse(baseHtml)
    grid = {}
    for i,row in enumerate(kneeboardBaseXml.getElementsByTagName("tr")):
        for j, cell in enumerate(row.getElementsByTagName("td")):
            grid[(i,j)] = cell
        
    for place, replacement in replacements.items():
        if not isinstance(replacement, list):
            replacement = [replacement]
        if not isinstance(replacement[0], list):
            replacement = [[r] for r in replacement]
        
        for i, rowReplacement in enumerate(replacement):
            for j, cellReplacement in enumerate(rowReplacement):
                cellPosition = (place[0]+i, place[1]+j)
                removeTextNodes(grid[cellPosition])
                textNode = kneeboardBaseXml.createTextNode(cellReplacement)
                grid[cellPosition].appendChild(textNode)
    hti.screenshot(html_str=kneeboardBaseXml.toxml(), save_as = outFile)
#l = hti.screenshot(html_file=r"C:\Users\ander\source\repos\CreateKneeboard\WP_base.xhtml", save_as=r"myImage.png")

if __name__ == "__main__":
    replacements = {(2,3):["MyFlight","F/A-18C"]}
    printKneeboard(replacements, 'WP_base.xhtml', 'WP.png')
