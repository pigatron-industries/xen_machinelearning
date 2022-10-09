from music21 import stream
from xen.data.songdata import SongData, SongDataSet, Codec
from xen.utils import isInteger
import numpy as np

NUM_NOTES = 128

class SparseNoteSequenceCodec(Codec):
    """
    Scores are split into fixed length phrases based on a number of measures
    Each phrase is represented by a 2 dimensional array. 
    Dimension 1 = time, measured in ticks
    Dimension 2 = pitch, where each note on event will be represented by a number 1 
    """
    def __init__(self, ticksPerQuarter:int=4, measuresPerSequence:int=1, timesignature:str='4/4'):
        self.ticksPerQuarter = ticksPerQuarter
        self.measuresPerSequence = measuresPerSequence
        self.timesignature = timesignature
        self.sequenceShape = (ticksPerQuarter*measuresPerSequence*4, NUM_NOTES)
        self.encodedShape = self.sequenceShape

    def initEncode(self, dataset: SongDataSet):
        sequences = np.empty((0,)+self.encodedShape)
        for song in dataset.songs:
            try:
                self.encode(song)
                sequences = np.append(sequences, song.sequences, 0)
            except Exception as e:
                raise Exception(f'File: {song.filePath}')
        dataset.sequences = sequences
        return sequences

    def encode(self, song: SongData):
        """
        Split score into packets and create a sequence from each one
        data: SongData
        return array of sparse sequences
        """
        sequences = self.makeSequencesFromSong(song)
        song.sequences = sequences
        return sequences

    def makeSequencesFromSong(self, song: SongData):
        sequences = np.empty((0,)+self.sequenceShape)
        ignoredSequences = 0
        for part in song.getParts():
            measuresList = song.getConsecutiveMeasures(part, self.measuresPerSequence, self.timesignature)
            for measures in measuresList:
                try:
                    sequence = np.empty((0, NUM_NOTES))
                    for measure in measures:
                        measureSeq = self.makeSequenceFromMeasure(measure)
                        sequence = np.append(sequence, measureSeq, 0)
                    sequences = np.append(sequences, [sequence], 0)
                except ValueError as e:
                    ignoredSequences += 1
        if(ignoredSequences > 0):
            print(f'Ignored {ignoredSequences} sequences from {song.filePath}')
        return sequences

    def makeSequenceFromMeasure(self, measure: stream.Measure):
        sequence = np.zeros((int(measure.duration.quarterLength * self.ticksPerQuarter), NUM_NOTES)) 
        for element in measure.recurse().notes:
            offset = element.offset * self.ticksPerQuarter
            if(not isInteger(offset)):
                raise ValueError(f'ERROR: note offset is not an integer: {offset}')
            if element.isNote:
                sequence[int(offset)][element.pitch.midi] = 1
            if element.isChord:
                for note in element.notes:
                    sequence[int(offset)][note.pitch.midi] = 1
        return sequence

    def decode(self, data):
        # TODO
        return data


class ArrayCompressor():
    """
    Compress an array by removing unused data points
    """
    def __init__(self):
        self.removeIndexes = []

    def init(self, dataset):
        self.removeIndexes = []
        maxes = np.amax(dataset, axis = 0)
        for i, max in enumerate(maxes):
            if (max == 0):
                self.removeIndexes.append(i)
    
    def compress(self, dataset):
        return np.delete(dataset, self.removeIndexes, axis = 1)

    def decompress(self, dataset):
        for removedIndex in self.removeIndexes:
            dataset = np.insert(dataset, removedIndex, 0, axis = 1)
        return dataset


class FlatNoteSequenceCodec(SparseNoteSequenceCodec):
    """
    Takes a SparseNoteSequence and flattens it into 1 dimension.
    Compresses the resulting array by removing all data points that are never used.
    """
    def __init__(self, ticksPerQuarter:int=4, measuresPerSequence:int=1, timesignature:str='4/4'):
        super().__init__(ticksPerQuarter, measuresPerSequence, timesignature)
        self.encodedShape = (ticksPerQuarter*measuresPerSequence*4*NUM_NOTES,)
        self.compressor = ArrayCompressor()

    def initEncode(self, dataset: SongDataSet):
        sequences = np.empty((0,)+self.encodedShape)
        for song in dataset.songs:
            try:
                self.encode(song, compress = False)
                sequences = np.append(sequences, song.sequences, 0)
            except Exception as e:
                raise Exception(f'File: {song.filePath}')
        self.compressor.init(sequences)
        sequences = self.compressor.compress(sequences)
        dataset.sequences = sequences
        return sequences

    def encode(self, song: SongData, compress: bool = True):
        """
        Split score into packets and create a flattened sequence from each one
        data: SongData
        return array of flattened sparse sequences
        """
        sequences = super().encode(song)
        sequences = self.flatten(sequences)
        if(compress):
            sequences = self.compressor.compress(sequences)
        song.sequences = sequences
        return sequences

    def flatten(self, sequences):
        return sequences.reshape(sequences.shape[0], self.encodedShape[0])

    def decode(self, sequences):
        sequences = self.compressor.decompress(sequences)
        sequences = self.unflatten(sequences)
        return super().decode(sequences)

    def unflatten(self, data):
        return data.reshape(data.shape[0], self.sequenceShape[0], self.sequenceShape[1])


class ChordifiedSequenceCodec(SparseNoteSequenceCodec):
    """Identify each unique set of notes as a chord and one-hot encode each chord """
    def __init__(self, ticksPerQuarter:int = 4, measuresPerSequence:int = 1, timesignature:str = '4/4'):
        self.ticksPerQuarter = ticksPerQuarter
        self.measuresPerSequence = measuresPerSequence
        self.timesignature = timesignature
        self.chordList = []

    def initEncode(self, dataset: SongDataSet):
        pass

    def encode(self, song: SongData):
        pass

    def decode(self, sequences):
        pass