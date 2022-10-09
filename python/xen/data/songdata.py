from music21 import converter, pitch, interval, instrument, note, stream, meter
from enum import Enum
from xen.utils import isInteger
import glob
import numpy as np
import fractions

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


class Codec:
    def __init__(self):
        self.encodedShape = None
    def initEncode(self, dataset):
        pass
    def encode(self, data):
        pass
    def decode(self, data):
        pass

    
class SongDataSet:
    def __init__(self, ticksPerQuarter = 4):
        self.songs = []
        self.sequences = None
        self.ticksPerQuarter = ticksPerQuarter
        self.compressedSequences = None
        self.sequenceCompressor = None

    def loadMidiDir(self, path):
        files = glob.glob(path + "/*.mid")
        print(f'Loading {len(files)} files')
        self.loadMidiFiles(files)

    def loadMidiFiles(self, files):
        for file in files:
            song = SongData.fromMidiFile(file)
            self.songs.append(song)

    def filterTimeSig(self, match_timesig):
        filtered = []
        for songdata in self.songs:
            if songdata.hasTimeSig(match_timesig):
                filtered.append(songdata)
        self.songs = filtered

    def filterTimeSigOnly(self, match_timesig):
        filtered = []
        for songdata in self.songs:
            if songdata.hasOnlyTimeSig(match_timesig):
                filtered.append(songdata)
        self.songs = filtered

    def filterFractionalOffsets(self, ticksPerQuarter=4):
        filtered = []
        for songdata in self.songs:
            if (not songdata.hasFractionalOffsets(ticksPerQuarter)):
                filtered.append(songdata)
        self.songs = filtered

    def encodeSongs(self, codec: Codec):
        self.sequences = np.empty((0,)+codec.encodedShape)
        for song in self.songs:
            try:
                songSequences = codec.encode(song)
                song.sequences = songSequences
                self.sequences = np.append(self.sequences, songSequences, 0)
            except Exception as e:
                raise Exception(f'File: {song.filePath}')
        return self.sequences
 