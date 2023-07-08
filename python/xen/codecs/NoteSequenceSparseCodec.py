from .Codec import Codec
from music21 import stream
from music21.stream.base import Score, Part, Measure
from xen.data.SongData import SongData, SongDataSet
from xen.utils import isInteger
from typing import Callable
import numpy as np


NUM_NOTES = 128

class NoteSequenceSparseCodec(Codec):
    """
    Scores are split into fixed length phrases based on a number of measures
    Each phrase is represented by a 2 dimensional array. 
    Dimension 1 = time, measured in ticks
    Dimension 2 = pitch, where each note on event will be represented by a number 1 
    timeSignature: string representing the time signature of the score, used to make sure consecutive measures are all the same time signature
    """
    def __init__(self, ticksPerQuarter:int=4, quartersPerMeasure:int=4, measuresPerSequence:int=1, timesignature:str='4/4', normaliseOctave:bool=True, 
                 percussionMap:None|Callable[[int], int]=None):
        self.ticksPerQuarter = ticksPerQuarter
        self.measuresPerSequence = measuresPerSequence
        self.quartersPerMeasure = quartersPerMeasure
        self.timesignature = timesignature
        self.sequenceShape = (ticksPerQuarter*quartersPerMeasure*measuresPerSequence, NUM_NOTES)
        self.encodedShape = self.sequenceShape
        self.percussionMap = percussionMap
        if(self.percussionMap is None):
            self.normaliseOctave = False
        else:
            self.normaliseOctave = normaliseOctave

    def encodeAll(self, dataset: SongDataSet):
        sequences = np.empty((0,)+self.sequenceShape)
        for song in dataset.songs:
            try:
                self.makeSequences(song)
                sequences = np.append(sequences, song.sequences, 0)
            except Exception as e:
                raise Exception(f'File: {song.filePath}')
        dataset.sequences = sequences
        return sequences

    def makeSequences(self, song: SongData):
        """
        Split score into packets and create a sequence from each one
        data: SongData
        return array of sparse sequences
        """
        sequences = self.makeSequencesFromSong(song)
        song.sequences = sequences
        return sequences

    def makeSequencesFromSong(self, song: SongData) -> np.ndarray:
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

    def makeSequenceFromMeasure(self, measure: Measure):
        sequence = np.zeros((int(measure.duration.quarterLength * self.ticksPerQuarter), NUM_NOTES))
        if(self.normaliseOctave):
            lowestNote = self.getLowestNote(measure)
            lowestOctave = int(lowestNote/12)
            transpose = lowestOctave * 12
        else:
            transpose = 0
            
        for element in measure.recurse().notes:
            offset = element.offset * self.ticksPerQuarter
            if element.isNote:
                self.addNoteToSequence(sequence, element.pitch.midi, offset, transpose)
            if element.isChord:
                for note in element.notes:
                    self.addNoteToSequence(sequence, note.pitch.midi, offset, transpose)
        return sequence
    

    def addNoteToSequence(self, sequence, midinote, offset, transpose=0):
        if(not isInteger(offset)):
            raise ValueError(f'ERROR: note offset is not an integer: {offset}')
        if(self.percussionMap is not None):
            midinote = self.percussionMap(midinote)
        else:
            midinote = midinote - transpose
        sequence[int(offset)][midinote] = 1

    
    def getLowestNote(self, measure: stream.Measure):
        lowestNote = 128
        for element in measure.recurse().notes:
            if element.isNote:
                lowestNote = min(lowestNote, element.pitch.midi)
            if element.isChord:
                for note in element.notes:
                    lowestNote = min(lowestNote, note.pitch.midi)
        return lowestNote

    def decode(self, data):
        # TODO
        return data
