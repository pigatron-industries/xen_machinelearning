from .NoteSequenceSparseCodec import NoteSequenceSparseCodec
from xen.data.SongData import SongData, SongDataSet
import numpy as np


class ChordifiedSequenceCodec(NoteSequenceSparseCodec):
    """
    Identify each unique set of notes as a chord and one-hot encode each chord
    """
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