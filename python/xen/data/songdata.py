from music21 import converter, pitch, interval, instrument, note, stream, meter
from music21.stream.base import Score
from enum import Enum
from xen.utils import isInteger
from typing import List
import glob
import re
import numpy as np
import fractions
import numpy as np

from ipywidgets import IntProgress, Label
from IPython.display import display


NUM_NOTES = 128
MIN_NOTE = 0
MAX_NOTE = 127


class SongData:
    def __init__(self, score:Score, filePath:str):
        self.score: Score = score
        self.filePath: str = filePath
        self.sequences: List[np.ndarray] = []
        self.minPitch = None
        self.maxPitch = None

    @classmethod
    def fromMidiFile(cls, filePath):
        score = converter.parse(filePath)
        if (isinstance(score, Score)):
            return cls(score, filePath)
        else:
            raise Exception(f'score not instance of Score: {filePath}')

    def getParts(self):
        return self.score.getElementsByClass(stream.Part)
    

    def getPartsByInstruments(self, matchInstrumentNames:List[str]):
        parts = []
        for part in self.getParts():
            instruments = part.getInstruments()
            for instrument in instruments:
                for matchInstrumentName in matchInstrumentNames:
                    if(re.search(matchInstrumentName, instrument.instrumentName) or
                       re.search(matchInstrumentName, part.partName)):
                        parts.append(part)
        return parts
    

    def getTimeSigs(self):
        return self.score.recurse().getElementsByClass(meter.TimeSignature)

    def hasTimeSig(self, match_timesig):
        for timesig in self.getTimeSigs():
            timesigString = f'{timesig.numerator}/{timesig.denominator}'
            if (timesigString == match_timesig):
                return True
        return False

    def hasOnlyTimeSig(self, match_timesig):
        for timesig in self.getTimeSigs():
            if (timesig.numerator != match_timesig[0] or timesig.denominator != match_timesig[1]):
                return False
        return True

    def hasFractionalOffsets(self, ticksPerQuarter):
        for note in self.score.recurse().notes:
            offset = note.offset * ticksPerQuarter
            if(not isInteger(offset)):
                return True
        return False

    def getConsecutiveMeasures(self, part, measuresPerSequence, match_timesig):
        consecutiveMeasuresList = []
        consecutiveMeasures = []
        measures = part.getElementsByClass(stream.Measure)
        currentTimeSig = None
        i = 0
        while i < len(measures):
            measure = measures[i]
            notes = measure.recurse().notes
            if(measure.timeSignature != None):
                currentTimeSig = measure.timeSignature
            
            if(len(notes) > 0):
                if(measuresPerSequence is not None and currentTimeSig.ratioString == match_timesig):
                    consecutiveMeasures.append(measure)
                    if(len(consecutiveMeasures) == measuresPerSequence):
                        consecutiveMeasuresList.append(consecutiveMeasures)
                        consecutiveMeasures = []
                elif(measuresPerSequence is None):
                    consecutiveMeasures.append(measure)
                else:
                    consecutiveMeasures = []

            if(len(notes) == 0):
                if(measuresPerSequence is None and len(consecutiveMeasures) > 0):
                    consecutiveMeasuresList.append(consecutiveMeasures)
                    consecutiveMeasures = []

            i += 1
            
        # if no sequence length then append everything
        if(measuresPerSequence is None and len(consecutiveMeasures) > 0):
            consecutiveMeasuresList.append(consecutiveMeasures)
        return consecutiveMeasuresList
    

    def getAllMeasures(self, part):
        return part.getElementsByClass(stream.Measure)


    def getOverlappingMeasures(self, part, measuresPerSequence, match_timesig):
        pass 


    
class SongDataSet:
    def __init__(self, songs = None):
        if songs is not None:
            self.songs = songs
        else:
            self.songs = []
        # self.sequences:np.ndarray = np.array([])
        self.sequences:List[np.ndarray] = []
        self.encodedSequences = None


    @classmethod
    def fromMidiPaths(cls, paths:List[str], recursive = False):
        dataset = cls()
        for path in paths:
            # if path is file
            if path.endswith('.mid'):
                dataset.loadMidiFiles([path])
            else:
                dataset.loadMidiDir(path, recursive)
        return dataset


    def getDataset(self):
        return self.sequences


    def loadMidiDir(self, path, recursive = False):
        if recursive:
            files = glob.glob(path + "/**/*.mid", recursive=True)
        else:
            files = glob.glob(path + "/*.mid", recursive=False)
        print(f'Loading {len(files)} files')
        self.loadMidiFiles(files)


    def loadMidiFiles(self, files):
        progress = IntProgress(min=0, max=len(files))
        label = Label()
        display(progress, label)
        for i, file in enumerate(files):
            song = SongData.fromMidiFile(file)
            self.songs.append(song)
            progress.value = i + 1
            label.value = f'{i + 1}/{len(files)}'

        print(f'Loaded {len(self.songs)} songs')


    def filterTimeSig(self, match_timesig):
        filtered = []
        for songdata in self.songs:
            if songdata.hasTimeSig(match_timesig):
                filtered.append(songdata)
        print(f'Filtered to {len(filtered)} songs')
        return SongDataSet(filtered)


    def filterTimeSigOnly(self, match_timesig):
        filtered = []
        for songdata in self.songs:
            if songdata.hasOnlyTimeSig(match_timesig):
                filtered.append(songdata)
        print(f'Filtered to {len(filtered)} songs')
        return SongDataSet(filtered)


    def filterFractionalOffsets(self, ticksPerQuarter=4):
        filtered = []
        for songdata in self.songs:
            if (not songdata.hasFractionalOffsets(ticksPerQuarter)):
                filtered.append(songdata)
        print(f'Filtered to {len(filtered)} songs')
        return SongDataSet(filtered)


    def splitByTimeSignature(self):
        timesigsdict = {}
        for song in self.songs:
            timesigs = song.score.recurse().getElementsByClass(meter.TimeSignature)
            for timesig in timesigs:
                timsiglabel = f'{timesig.numerator}/{timesig.denominator}'
                if timsiglabel not in timesigsdict:
                    timesigsdict[timsiglabel] = SongDataSet()
                timesigsdict[timsiglabel].songs.append(song)
        return timesigsdict
 