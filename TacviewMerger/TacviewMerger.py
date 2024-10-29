import zipfile
import sys
import io
import os
from datetime import datetime
from datetime import timedelta

class FrameRecord:
    def __init__(self):
        self.timestamp = None
        self.entries = []
        
    def toString(self, referenceTime):
       delta = self.timestamp - referenceTime
       return '#'+str(delta.total_seconds())+"\n"+"".join(self.entries)
        
class TacviewRecord:
    def __init__(self):
        self.header = []
        self.referenceTime = None
        self.timeframes = []
        
timeFormat = "%Y-%m-%dT%H:%M:%S.%fZ\n"
def loadTacview(filePath):
    with zipfile.ZipFile(filePath) as tacviewZip:
        tacviewInfo = tacviewZip.filelist[0]
        with io.TextIOWrapper(tacviewZip.open(tacviewInfo), encoding="utf-8") as tacviewData:
            record = TacviewRecord()
            for line in tacviewData:
                if line.startswith("#"):
                    frame = FrameRecord()
                    delta = timedelta(seconds = float(line.lstrip("#")))
                    
                    frame.timestamp = record.referenceTime + delta
                    record.timeframes.append(frame)
                elif not record.timeframes:
                    record.header.append(line)
                    if line.startswith("0,RecordingTime="):
                        record.referenceTime = datetime.strptime(line.split('=')[1],timeFormat)
                else:
                    record.timeframes[-1].entries.append(line)
            return record

for a in sys.argv[1:]:
    print(a)
records = [loadTacview(tacviewPath) for tacviewPath in sys.argv[1:]]
records.sort(key=lambda r: r.referenceTime)

mergeRecord = records[0]
latestTimestamp = mergeRecord.timeframes[-1].timestamp
for mergedRecords in records[1:]:
    mergeRecord.timeframes.extend(f for f in mergedRecords.timeframes if f.timestamp>latestTimestamp)
    latestTimestamp = mergedRecords.timeframes[-1].timestamp

with zipfile.ZipFile("merged.zip.acmi",mode = "w", compression=zipfile.ZIP_DEFLATED) as out:
    acmi = "".join(mergeRecord.header)+"".join(frame.toString(mergeRecord.referenceTime) for frame in mergeRecord.timeframes)
    out.writestr("merged.txt.acmi", acmi)
