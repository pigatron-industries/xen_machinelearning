from music21 import converter, pitch, interval, instrument, note, stream, meter
from enum import Enum
from xen.utils import isInteger
import glob
import numpy as np
import fractions

from ipywidgets import IntProgress, Label
from IPython.display import display


NUM_NOTES = 128
MIN_NOTE = 0
MAX_NOTE = 127


class SongData:
    def __init__(self, score, filePath):
        self.score = score
        self.filePath = filePath
        self.sequences = None
        self.minPitch = None
        self.maxPitch = None

    @classmethod
    def fromMidiFile(cls, filePath):
        return cls(converter.parse(filePath), filePath)

    def getParts(self):
        return self.score.getElementsByClass(stream.Part)

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
            if(currentTimeSig.ratioString == match_timesig and len(notes) > 0):
                consecutiveMeasures.append(measure)
                if(len(consecutiveMeasures) == measuresPerSequence):
                    consecutiveMeasuresList.append(consecutiveMeasures)
                    consecutiveMeasures = []
            else:
                consecutiveMeasures = []
            i += 1
        return consecutiveMeasuresList

    def getOverlappingMeasures(self, part, measuresPerSequence, match_timesig):
        pass 

    
class SongDataSet:
    def __init__(self, songs = None):
        if songs is not None:
            self.songs = songs
        else:
            self.songs = []
        self.sequences = None
        self.encodedSequences = None


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
 