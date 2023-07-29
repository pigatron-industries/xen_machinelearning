from .NoteSequenceSparseCodec import NoteSequenceSparseCodec
from xen.data.SongData import SongData, SongDataSet
from typing import Callable, List
import numpy as np


NUM_NOTES = 128

# class ArrayCompressor():
#     """
#     Compress an array by removing unused data points
#     """
#     def __init__(self):
#         self.removeIndexes = []

#     def init(self, dataset):
#         self.removeIndexes = []
#         maxes = np.amax(dataset, axis = 0)
#         for i, max in enumerate(maxes):
#             if (max == 0):
#                 self.removeIndexes.append(i)
    
#     def compress(self, dataset) -> List[np.ndarray]:
#         return np.delete(dataset, self.removeIndexes, axis = 1)

#     def decompress(self, dataset):
#         for removedIndex in self.removeIndexes:
#             dataset = np.insert(dataset, removedIndex, 0, axis = 1)
#         return dataset


class NoteSequenceFlatCodec(NoteSequenceSparseCodec):
    """
    Takes a SparseNoteSequence and flattens it into 1 dimension.
    Compresses the resulting array by removing all data points that are never used.
    """
    def __init__(self, ticksPerQuarter:int=4, quartersPerMeasure:int=4, measuresPerSequence:int=1, timesignature:str='4/4', 
                 trim:bool=True, normaliseOctave:bool=True, percussionMap:None|Callable[[int], int]=None):
        super().__init__(ticksPerQuarter, quartersPerMeasure, measuresPerSequence, timesignature, normaliseOctave=normaliseOctave, percussionMap=percussionMap)
        self.encodedShape = (ticksPerQuarter*measuresPerSequence*quartersPerMeasure*NUM_NOTES,)
        # self.compress = compress
        self.trim = trim
        # self.compressor = ArrayCompressor()
        self.maxNote = NUM_NOTES-1
        self.minNote = 0


    def encodeAll(self, dataset: SongDataSet) -> List[np.ndarray]:
        sequences = super().encodeAll(dataset)
        sequences = self.flatten(sequences)
        print(f'Flattened sequences shape: {sequences[0].shape}')
        dataset.sequences = sequences
        return sequences


    # def encodeSequences(self, sequences:List[np.ndarray]):
    #     sequences = self.flatten(sequences)
    #     print(f'Flattened sequences shape: {sequences[0].shape}')
    #     # if(self.compress):
    #     #     self.compressor.init(sequences)
    #     #     sequences = self.compressor.compress(sequences)
    #     #     print(f'Compressed sequences shape: {sequences.shape}')
    #     return sequences
    

    # def encode(self, song: SongData):
    #     """
    #     Split score into packets and create a flattened sequence from each one
    #     data: SongData
    #     return array of flattened sparse sequences
    #     """
    #     sequences = super().encode(song)
    #     if(self.trim):
    #         sequences = self.trimSequences(sequences)
    #     sequences = self.flatten(sequences)
    #     # if(self.compress):
    #     #     sequences = self.compressor.compress(sequences)
    #     song.sequences = sequences
    #     print('flat encode')
    #     return sequences


    def flatten(self, sequences:List[np.ndarray]) -> List[np.ndarray]:
        flatSequences = []
        for sequence in sequences:
            flatSequences.append(sequence.flatten())
        return flatSequences


    def decode(self, sequences:List[np.ndarray]) -> List[np.ndarray]:
        # if(self.compress):
        #     sequences = self.compressor.decompress(sequences)
        sequences = self.unflatten(sequences)
        return super().decode(sequences)


    def unflatten(self, flatSequences:List[np.ndarray]) -> List[np.ndarray]:
        sequences = []
        numNotes = (self.maxNote-self.minNote+1)
        for flatSequence in flatSequences:
            shape = (flatSequence.shape[1]//numNotes, numNotes)
            sequences.append(flatSequence.reshape(shape))
        return sequences


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
