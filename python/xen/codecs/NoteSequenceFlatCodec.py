from .NoteSequenceSparseCodec import NoteSequenceSparseCodec
from xen.data.SongData import SongData, SongDataSet
from xen.data.Filter import NameFilter
from typing import Callable, List
import numpy as np


NUM_NOTES = 128


class NoteSequenceFlatCodec(NoteSequenceSparseCodec):
    """
    Takes a SparseNoteSequence and flattens it into 1 dimension.
    Compresses the resulting array by removing all data points that are never used.
    """
    def __init__(self, ticksPerQuarter:int=4, quartersPerMeasure:int=4, measuresPerSequence:int=1, timesignature:str='4/4', 
                 instrumentFilter:NameFilter|None = None, trim:bool=True, normaliseOctave:bool=True, percussionMap:None|Callable[[int], int]=None):
        super().__init__(ticksPerQuarter, quartersPerMeasure, measuresPerSequence, timesignature, instrumentFilter = instrumentFilter, normaliseOctave=normaliseOctave, percussionMap=percussionMap)
        self.encodedShape = (ticksPerQuarter*measuresPerSequence*quartersPerMeasure*NUM_NOTES,)
        self.trim = trim
        self.maxNote = NUM_NOTES-1
        self.minNote = 0


    def encodeAll(self, dataset: SongDataSet) -> List[np.ndarray]:
        sequences = super().encodeAll(dataset)
        sequences = self.flatten(sequences)
        print(f'Flattened sequences shape: {sequences[0].shape}')
        dataset.sequences = sequences
        return sequences


    def flatten(self, sequences:List[np.ndarray]) -> List[np.ndarray]:
        flatSequences = []
        for sequence in sequences:
            flatSequences.append(sequence.flatten())
        return flatSequences


    def decode(self, sequences:List[np.ndarray]) -> List[np.ndarray]:
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
