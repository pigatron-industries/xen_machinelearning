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

    # def makeSequences(self, ticksPerQuarter=4, measuresPerSequence=4, match_timesig='4/4'):
    #     """ 
    #     Create training sequences from consecutive measures in parts of the song.
    #     Arguments:
    #         ticksPerQuarter: number of sequences steps (ticks) per quarter note
    #         measuresPerSequence: number of measures to create each sequence from
    #         timesig: only use mesaures with given time signature
    #     """
    #     self.sequences = np.empty((0, ticksPerQuarter*measuresPerSequence*4, NUM_NOTES))
    #     minPitch = 127
    #     maxPitch = 0
    #     ignoredSequences = 0
    #     for part in self.getParts():
    #         measuresList = self.getConsecutiveMeasures(part, measuresPerSequence, match_timesig)
    #         for measures in measuresList:
    #             try:
    #                 sequence = np.empty((0, NUM_NOTES))
    #                 for measure in measures:
    #                     measureSeq, minMeasurePitch, maxMeasurePitch = self.makeSequenceFromMeasure(measure, ticksPerQuarter)
    #                     minPitch = min(minPitch, minMeasurePitch)
    #                     maxPitch = max(maxPitch, maxMeasurePitch)
    #                     sequence = np.append(sequence, measureSeq, 0)
    #                 self.sequences = np.append(self.sequences, [sequence], 0)
    #             except ValueError as e:
    #                 ignoredSequences += 1
    #     if(ignoredSequences > 0):
    #         print(f'Ignored {ignoredSequences} sequences from {self.filePath}')
    #     self.minPitch = minPitch
    #     self.maxPitch = maxPitch
    #     return self.sequences, self.minPitch, self.maxPitch
        
    # def makeSequenceFromMeasure(self, measure, ticksPerQuarter):
    #     sequence = np.zeros((int(measure.duration.quarterLength * ticksPerQuarter), NUM_NOTES))        
    #     minPitch = 127
    #     maxPitch = 0
    #     for element in measure.recurse().notes:
    #         offset = element.offset * ticksPerQuarter
    #         if(not isInteger(offset)):
    #             raise ValueError(f'ERROR: note offset is not an integer: {offset}')
    #         if element.isNote:
    #             sequence[int(offset)][element.pitch.midi] = 1
    #             minPitch = min(minPitch, element.pitch.midi)
    #             maxPitch = max(maxPitch, element.pitch.midi)
    #         if element.isChord:
    #             for note in element.notes:
    #                 sequence[int(offset)][note.pitch.midi] = 1
    #                 minPitch = min(minPitch, note.pitch.midi)
    #                 maxPitch = max(maxPitch, note.pitch.midi)
    #     return sequence, minPitch, maxPitch

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

    # def makeSequences(self, ticksPerQuarter=4, measuresPerSequence=4, match_timesig='4/4'):
    #     self.sequences = np.empty((0, ticksPerQuarter*measuresPerSequence*4, NUM_NOTES))
    #     minPitch = 127
    #     maxPitch = 0
    #     for song in self.songs:
    #         try:
    #             songSequences, minSongPitch, maxSongPitch = song.makeSequences(ticksPerQuarter, measuresPerSequence, match_timesig)
    #             minPitch = min(minPitch, minSongPitch)
    #             maxPitch = max(maxPitch, maxSongPitch)
    #             self.sequences = np.append(self.sequences, songSequences, 0)
    #         except Exception as e:
    #             raise Exception(f'File: {song.filePath}')

    #     self.minPitch = minPitch
    #     self.maxPitch = maxPitch
    #     return self.sequences, self.minPitch, self.maxPitch

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

    # def makeCompressor(self):
    #     tickSet = {}
    #     pitchSet = {}
    #     for sequence in self.sequences:
    #         for i, tick in enumerate(sequence):
    #             for j, note in enumerate(tick):
    #                 if(note > 0.5):
    #                     tickSet[i] = 1
    #                     pitchSet[j] = 1
    #     self.sequenceCompressor = SequenceCompressor((self.sequences.shape[1], self.sequences.shape[2]), [tickSet, pitchSet])
    #     return self.sequenceCompressor

    # def compressSequences(self):
    #     self.makeCompressor()
    #     self.compressedSequences = np.empty((0, self.sequenceCompressor.shapeCompressed[0] * self.sequenceCompressor.shapeCompressed[1]))
    #     for sequence in self.sequences:
    #         compressed = self.sequenceCompressor.compress(sequence)
    #         self.compressedSequences = np.append(self.compressedSequences, [compressed], 0)

 

class SequenceCompressor:
    """
    Deprecated
    Compress and flatten 2 dimensional sequence arrays by removing rows and columns that never contain any data
    """
    def __init__(self, shape, axisIndexes):
        self.shape = shape
        self.axisIndexes = axisIndexes
        self.shapeCompressed = (len(axisIndexes[0]), len(axisIndexes[1]))

    def compress(self, sequence):
        # TODO compress after flattening
        sequence = self.compressAxis(sequence, 0)
        sequence = self.compressAxis(sequence, 1)
        sequence = sequence.reshape(self.shapeCompressed[0] * self.shapeCompressed[1])
        return sequence

    def compressAxis(self, sequence, axis):
        removeSet = []
        for i in range(self.shape[axis]):
            if i not in self.axisIndexes[axis]:
                removeSet.append(i)
        return np.delete(sequence, removeSet, axis=axis)

    def decompress(self, sequence):
        sequence = sequence.reshape(self.shapeCompressed[0], self.shapeCompressed[1])
        sequence = self.decompressAxis(sequence, 0)
        sequence = self.decompressAxis(sequence, 1)
        return sequence
        
    def decompressAxis(self, sequence, axis):
        removeSet = []
        for i in range(self.shape[axis]):
            if i not in self.axisIndexes[axis]:
                removeSet.append(i)
        for removed in removeSet:
            sequence = np.insert(sequence, removed, 0, axis=axis)
        return sequence