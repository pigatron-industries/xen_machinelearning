from .NoteSequenceSparseCodec import NoteSequenceSparseCodec
from xen.data.SongData import SongData, SongDataSet
import numpy as np


NUM_NOTES = 128

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


class NoteSequenceFlatCodec(NoteSequenceSparseCodec):
    """
    Takes a SparseNoteSequence and flattens it into 1 dimension.
    Compresses the resulting array by removing all data points that are never used.
    """
    def __init__(self, ticksPerQuarter:int=4, quartersPerMeasure:int=4, measuresPerSequence:int=1, timesignature:str='4/4', trim = True, compress = False):
        super().__init__(ticksPerQuarter, quartersPerMeasure, measuresPerSequence, timesignature)
        self.encodedShape = (ticksPerQuarter*measuresPerSequence*quartersPerMeasure*NUM_NOTES,)
        self.compress = compress
        self.trim = trim
        self.compressor = ArrayCompressor()
        self.maxNote = NUM_NOTES-1
        self.minNote = 0

    def initTrimData(self, sequences):
        """
        Find lowest and highest notes in all sequences
        """
        self.minNote = NUM_NOTES-1
        self.maxNote = 0
        for sequence in sequences:
            sequence = np.swapaxes(sequence, 0, 1)
            for i, note in enumerate(sequence):
                if(np.any(note)):
                    if(i < self.minNote):
                        self.minNote = i
                    if(i > self.maxNote):
                        self.maxNote = i
        self.encodedShape = (self.ticksPerQuarter * self.measuresPerSequence * self.quartersPerMeasure * (self.maxNote-self.minNote+1),)
        print(f'Lowest note: {self.minNote}, Highest note: {self.maxNote}')


    def encodeAll(self, dataset: SongDataSet):
        sequences = super().encodeAll(dataset)
        sequences = self.encodeSequences(sequences)
        dataset.sequences = sequences
        return sequences


    def encodeSequences(self, sequences):
        print(f'Sparse sequences shape: {sequences.shape}')
        if(self.trim):
            self.initTrimData(sequences)
            sequences = self.trimSequences(sequences)
            print(f'Trimmed sequences shape: {sequences.shape}')
        sequences = self.flatten(sequences)
        print(f'Flattened sequences shape: {sequences.shape}')
        if(self.compress):
            self.compressor.init(sequences)
            sequences = self.compressor.compress(sequences)
            print(f'Compressed sequences shape: {sequences.shape}')
        return sequences
    

    def encode(self, song: SongData):
        """
        Split score into packets and create a flattened sequence from each one
        data: SongData
        return array of flattened sparse sequences
        """
        sequences = super().encode(song)
        if(self.trim):
            sequences = self.trimSequences(sequences)
        sequences = self.flatten(sequences)
        if(self.compress):
            sequences = self.compressor.compress(sequences)
        song.sequences = sequences
        return sequences
    

    def trimSequences(self, sequences):
        return sequences[:, :, self.minNote:self.maxNote+1]


    def flatten(self, sequences):
        return sequences.reshape(sequences.shape[0], self.encodedShape[0])


    def decode(self, sequences):
        if(self.compress):
            sequences = self.compressor.decompress(sequences)
        sequences = self.unflatten(sequences)
        return super().decode(sequences)


    def unflatten(self, data):
        return data.reshape(data.shape[0], self.sequenceShape[0], self.maxNote-self.minNote+1)


    def untrimSequences(self, sequences):
        """
        Add back all rows that were removed by trimSequences
        """
        # Add empty rows to beginning and end of each sequence
        emptyRows = np.zeros((sequences.shape[0], sequences.shape[1], self.minNote))
        sequences = np.concatenate((emptyRows, sequences), axis = 2)
        emptyRows = np.zeros((sequences.shape[0], sequences.shape[1], NUM_NOTES - self.maxNote - 1))
        sequences = np.concatenate((sequences, emptyRows), axis = 2)
        return sequences
