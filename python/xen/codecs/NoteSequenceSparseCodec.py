from .Codec import Codec
from music21 import stream
from music21.stream.base import Score, Part, Measure
from xen.data.SongData import SongData, SongDataSet
from xen.utils import isInteger
from typing import Callable, List
import numpy as np


NUM_NOTES = 128

class NoteSequenceSparseCodec(Codec):
    """
    Scores are split into fixed length phrases based on a number of measures
    Each phrase is represented by a 2 dimensional array. 
    Dimension 1 = time, measured in ticks
    Dimension 2 = pitch, where each note on event will be represented by a number 1 
    timeSignature: string representing the time signature of the score, used to make sure consecutive measures are all the same time signature
    measuresPerSequence: number of measures to include in each sequence, if None then the whole score is used
    """
    def __init__(self, ticksPerQuarter:int=4, quartersPerMeasure:int|None=4, measuresPerSequence:int|None=1, timesignature:str|None='4/4', minMeasuresPerSequence:int=0,
                 trim:bool=True, normaliseOctave:bool=True, percussionMap:None|Callable[[int], int]=None):
        self.ticksPerQuarter = ticksPerQuarter
        self.measuresPerSequence = measuresPerSequence
        self.minMeasuresPerSequence = minMeasuresPerSequence
        self.quartersPerMeasure = quartersPerMeasure
        self.timesignature = timesignature
        self.trim = trim
        if(measuresPerSequence is not None and quartersPerMeasure is not None):
            self.sequenceShape = (ticksPerQuarter*quartersPerMeasure*measuresPerSequence, NUM_NOTES)
        else:
            self.sequenceShape = None
        self.encodedShape = self.sequenceShape
        self.percussionMap = percussionMap
        if(self.percussionMap is None):
            self.normaliseOctave = False
        else:
            self.normaliseOctave = normaliseOctave


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
        if(self.measuresPerSequence is not None and self.quartersPerMeasure is not None):
            self.encodedShape = (self.ticksPerQuarter * self.measuresPerSequence * self.quartersPerMeasure * (self.maxNote-self.minNote+1),)
        print(f'Lowest note: {self.minNote}, Highest note: {self.maxNote}')


    def trimSequences(self, sequences:List[np.ndarray]):
        trimmedSequences = []
        for sequence in sequences:
            sequence = np.swapaxes(sequence, 0, 1)
            sequence = sequence[self.minNote:self.maxNote+1]
            sequence = np.swapaxes(sequence, 0, 1)
            trimmedSequences.append(sequence)
        return trimmedSequences


    def encodeAll(self, dataset: SongDataSet) -> List[np.ndarray]:
        sequences:List[np.ndarray] = []
        for song in dataset.songs:
            try:
                songSequences = self.encodeSparse(song)
                sequences.extend(songSequences)
            except Exception as e:
                raise Exception(f'File: {song.filePath}')
        print(f'Sparse sequence shape: {sequences[0].shape}')
        if(self.trim):
            self.initTrimData(sequences)
            sequences = self.trimSequences(sequences)
            print(f'Trimmed sequences shape: {sequences[0].shape}')
        dataset.sequences = sequences
        print(f"Encoded {len(sequences)} sequences")
        return sequences
    

    def encodeSparse(self, song: SongData) -> List[np.ndarray]:
        """
        Split score into packets and create a sequence from each one
        data: SongData
        return array of sparse sequences
        """
        sequences = self.makeSequencesFromSong(song)
        song.sequences = sequences
        return sequences


    def makeSequencesFromSong(self, song: SongData) -> List[np.ndarray]:
        print(f'Encoding {song.filePath}')
        sequences:List[np.ndarray] = []
        ignoredSequences = 0
        parts = song.getParts()
        # if(len(parts) > 1):
        #     print(f'Warning: {song.filePath} has {len(parts)} parts')
        for part in parts:
            measuresList = song.getConsecutiveMeasures(part, self.measuresPerSequence, self.timesignature)
            for measures in measuresList:
                if(len(measures) < self.minMeasuresPerSequence):
                    ignoredSequences += 1
                    continue
                try:
                    sequence = np.empty((0, NUM_NOTES))
                    for measure in measures:
                        measureSeq = self.makeSequenceFromMeasure(measure)
                        sequence = np.append(sequence, measureSeq, 0)
                    sequences.append(sequence)
                except ValueError as e:
                    ignoredSequences += 1
            if(ignoredSequences > 0):
                print(f'Ignored {ignoredSequences} sequences from {song.filePath}')
        print(f'Encoded {len(sequences)} sequences from {song.filePath}')
        return sequences

    def makeSequenceFromMeasure(self, measure: Measure):
        sequence = np.zeros((int(measure.duration.quarterLength * self.ticksPerQuarter), NUM_NOTES))
        if(self.normaliseOctave):
            lowestNote = self.getLowestNote(measure)
            lowestOctave = int(lowestNote/12)
            transpose = lowestOctave * 12
        else:
            transpose = 0
            
        elements = measure.recurse().notes
        if(len(elements) == 0):
            print(f'Warning: measure {measure.number} has no notes')
        for element in elements:
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
