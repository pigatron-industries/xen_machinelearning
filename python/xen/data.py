from music21 import converter, pitch, interval, instrument, note, stream, meter
from enum import Enum 
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
            if (timesig.numerator == match_timesig[0] or timesig.denominator == match_timesig[1]):
                return True
        return False

    def hasOnlyTimeSig(self, match_timesig):
        for timesig in self.getTimeSigs():
            if (timesig.numerator != match_timesig[0] or timesig.denominator != match_timesig[1]):
                return False
        return True

    def makeSequences(self, ticksPerQuarter=4, measuresPerSequence=4, match_timesig='4/4'):
        """ 
        Create training sequences from consecutive measures in parts of the song.
        Arguments:
            ticksPerQuarter: number of sequences steps (ticks) per quarter note
            measuresPerSequence: number of measures to create each sequence from
            timesig: only use mesaures with given time signature
        """
        self.sequences = np.empty((0, ticksPerQuarter*measuresPerSequence*4, NUM_NOTES))
        minPitch = 127
        maxPitch = 0
        for part in self.getParts():
            measuresList = self.getConsecutiveMeasures(part, measuresPerSequence, match_timesig)
            for measures in measuresList:
                sequence = np.empty((0, NUM_NOTES))
                for measure in measures:
                    measureSeq, minMeasurePitch, maxMeasurePitch = self.makeSequenceFromMeasure(measure, ticksPerQuarter)
                    minPitch = min(minPitch, minMeasurePitch)
                    maxPitch = max(maxPitch, maxMeasurePitch)
                    sequence = np.append(sequence, measureSeq, 0)
                self.sequences = np.append(self.sequences, [sequence], 0)
        self.minPitch = minPitch
        self.maxPitch = maxPitch
        return self.sequences, self.minPitch, self.maxPitch
        
    def makeSequenceFromMeasure(self, measure, ticksPerQuarter):
        sequence = np.zeros((int(measure.duration.quarterLength * ticksPerQuarter), NUM_NOTES))        
        minPitch = 127
        maxPitch = 0
        for element in measure.recurse().notes:
            offset = element.offset * ticksPerQuarter
            if element.isNote:
                if(not offset.is_integer()):
                    raise ValueError(f'ERROR: note offset is not an integer: {offset}')
                sequence[int(offset)][element.pitch.midi] = 1
                minPitch = min(minPitch, element.pitch.midi)
                maxPitch = max(maxPitch, element.pitch.midi)
            if element.isChord:
                for note in element.notes:
                    if(not offset.is_integer()):
                        raise ValueError(f'ERROR: note offset is not an integer: {offset}')
                    sequence[int(offset)][note.pitch.midi] = 1
                    minPitch = min(minPitch, note.pitch.midi)
                    maxPitch = max(maxPitch, note.pitch.midi)
        return sequence, minPitch, maxPitch

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

    
class SequenceDataSet:
    def __init__(self, ticksPerQuarter = 4):
        self.songs = []
        self.sequences = None
        self.ticksPerQuarter = ticksPerQuarter

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

    def makeSequences(self, ticksPerQuarter=4, measuresPerSequence=4, match_timesig='4/4'):
        self.sequences = np.empty((0, ticksPerQuarter*measuresPerSequence*4, NUM_NOTES))
        minPitch = 127
        maxPitch = 0
        for song in self.songs:
            try:
                songSequences, minSongPitch, maxSongPitch = song.makeSequences(ticksPerQuarter, measuresPerSequence, match_timesig)
                minPitch = min(minPitch, minSongPitch)
                maxPitch = max(maxPitch, maxSongPitch)
                self.sequences = np.append(self.sequences, songSequences, 0)
            except Exception as e:
                raise Exception(f'File: {song.filePath}')

        self.minPitch = minPitch
        self.maxPitch = maxPitch
        return self.sequences, self.minPitch, self.maxPitch


# def filterFractionalOffsets(scores):
#     filtered = []
#     for score in scores:
#         include = True
#         notes = score.recurse().notes
#         for note in notes:
#             if (isinstance(note.offset, fractions.Fraction)):
#                 include = False
#         if (include):
#             filtered.append(score)
#     return filtered