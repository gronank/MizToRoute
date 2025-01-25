from dcs import Mission
from dataclasses import dataclass

import json 
kgToLbs = 2.20462262
mPerNm = 1852
missionWPs = ["cap"]
with open("fuel.json",'r') as fuelFile:
    fuel = json.load(fuelFile)

def calculateFullFuel(fuelData, group):
    aircraft = group.units[0]
    fuel = fuelData["internalFuel"]
    for payload in aircraft.pylons.values():
        fuel+=fuelData['tanks'].get(payload['CLSID'],0)
    return fuel
@dataclass
class FuelPoint:
    remaining:float
    consumed:float
    timeOnStation:float
    
class FuelConsumption:
    def __init__(self,group):
        craftData = fuel[group.units[0].type]
        remainingFuel = calculateFullFuel(craftData, group)
        self.points = []
        lastWp = None
        missionIndex = 0
        for i, wp in enumerate(group.points[1:]):
            consumed = 0
            if wp.name.lower() in missionWPs :
                missionIndex = i
            elif lastWp:
                consumed = lastWp.position.distance_to_point(wp.position) * craftData["lbsPerNm"] / mPerNm
            if i == 1:
                consumed += craftData["climb"]
            remainingFuel -= consumed
            self.points.append(FuelPoint(remainingFuel,consumed,-1))
            lastWp = wp
        
        missionFuel = remainingFuel - craftData["reserveFuel"] - craftData["fightFuel"]
        for i, fp in enumerate(self.points[missionIndex:]):
            fp.remaining-=missionFuel
            if i == 0:
                fp.consumed = missionFuel
                fp.timeOnStation = 60*missionFuel/craftData["lbsPerHour"] 
                self.joker = fp.remaining
                self.bingo = self.joker - craftData["fightFuel"]
            
                