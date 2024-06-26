from .Codec import Codec
from music21.stream.base import Score, Part, Measure
from xen.data.SongData import SongData, SongDataSet, elementToMidiPitches
from xen.data.Filter import SongDataFilter
from xen.data.PercussionMap import PercussionMap
from xen.utils import isInteger
from xen.data.Filter import NameFilter
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
    def __init__(self, filter:SongDataFilter, ticksPerQuarter:int=4, quartersPerMeasure:int|None=4, measuresPerSequence:int|None=1, minMeasuresPerSequence:int=0,
                 trim:bool=True, normaliseOctave:bool=True, mergeParts:bool=False, percussionMap:PercussionMap|None=None):
        self.ticksPerQuarter = ticksPerQuarter
        self.measuresPerSequence = measuresPerSequence
        self.minMeasuresPerSequence = minMeasuresPerSequence
        self.quartersPerMeasure = quartersPerMeasure
        self.filter = filter
        self.trim = trim
        self.mergeParts = mergeParts
        if(measuresPerSequence is not None and quartersPerMeasure is not None):
            self.sequenceShape = (ticksPerQuarter*quartersPerMeasure*measuresPerSequence, NUM_NOTES)
        else:
            self.sequenceShape = None
        self.encodedShape = self.sequenceShape
        self.percussionMap = percussionMap
        if(self.percussionMap is not None):
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
        for i, song in enumerate(dataset.songs):
            try:
                print(f'Encoding {i}/{len(dataset.songs)}')
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
        for sequence in sequences:
            if(sequence.shape[0] != self.sequenceShape[0]):
                print(f'ERROR: Sparse sequence shape {sequence.shape} does not match expected shape {self.sequenceShape}')
                raise Exception(f'ERROR: Sparse sequence shape {sequence.shape} does not match expected shape {self.sequenceShape}')
        song.sequences = sequences
        return sequences


    def makeSequencesFromSong(self, song: SongData) -> List[np.ndarray]:
        sequences:List[np.ndarray] = []
        ignoredSequences = 0
        if(self.filter.instrumentName is not None):
            parts = song.getPartsByInstruments(self.filter.instrumentName)
        else:
            parts = song.getParts()
        if(len(parts) == 0):
            raise Exception(f'ERROR: No parts found matching filter in {song.filePath}')
        print(f'Encoding {len(parts)} parts from {song.filePath}')
        # for part in parts:
        #     print(f'{part.partName}')
        #     for instrument in part.getInstruments():
        #         print(f'\t{instrument.instrumentName}')

        if(self.mergeParts):
            consecutiveMeasures = song.getConsecutiveMeasures(parts, self.measuresPerSequence, self.filter.timeSignature)
        else:
            consecutiveMeasures = []
            for part in parts:
                measures = song.getConsecutiveMeasures([part], self.measuresPerSequence, self.filter.timeSignature)
                consecutiveMeasures.extend(measures)

        for measures in consecutiveMeasures:
            try:
                sequence = self.makeSequenceFromConsecutiveMeasures(measures)
                sequences.append(sequence)
            except ValueError as e:
                print(f'{measures[0][0].number}: {e}')
                ignoredSequences += 1
        if(ignoredSequences > 0):
            print(f'Ignored {ignoredSequences} sequences from {song.filePath}')
        print(f'Encoded {len(sequences)} sequences from {song.filePath}')
        return sequences
    

    def makeSequenceFromConsecutiveMeasures(self, measures:List[List[Measure]]):
        if(len(measures) < self.minMeasuresPerSequence):
            raise ValueError(f'ERROR: Sequence length {len(measures)} is less than minimum {self.minMeasuresPerSequence}')
        numNotes = 0
        sequence = np.empty((0, NUM_NOTES))
        for parallelMeasures in measures:
            measureSeq, measureNotes = self.makeSequenceFromParallelMeasures(parallelMeasures)
            sequence = np.append(sequence, measureSeq, 0)
            numNotes += measureNotes
        if(numNotes < self.filter.minNotesPerSequence):
            raise ValueError(f'ERROR: Sequence has {numNotes} notes, less than minimum {self.filter.minNotesPerSequence}')
        if(len(sequence) != self.sequenceShape[0]):
            raise ValueError(f'ERROR: Sequence length {len(sequence)} does not match expected length {self.sequenceShape[0]}') 
        return sequence


    def makeSequenceFromParallelMeasures(self, measures:List[Measure]):
        sequence = np.zeros((int(measures[0].duration.quarterLength * self.ticksPerQuarter), NUM_NOTES))
        if(self.normaliseOctave):
            lowestNote = self.getLowestNote(measure)
            lowestOctave = int(lowestNote/12)
            transpose = lowestOctave * 12
        else:
            transpose = 0

        numNotes = 0
        elements = []
        for measure in measures:
            elements.extend(measure.recurse().notes)
        if(len(elements) == 0):
            print(f'Warning: measure {measures[0].number} has no notes')
        for element in elements:
            offset = element.offset * self.ticksPerQuarter
            for midinote in elementToMidiPitches(element):
                try:
                    self.addNoteToSequence(sequence, midinote, offset, transpose)
                    numNotes += 1
                except ValueError as e:
                    print(f'WARMNING: Note not added: {measures[0].number}: {e}')
        return sequence, numNotes
    

    def addNoteToSequence(self, sequence, midinote, offset, transpose=0):
        if(not isInteger(offset)):
            raise ValueError(f'ERROR: note offset is not an integer: {offset}')
        if(self.percussionMap is not None):
            group = self.percussionMap(midinote)
            if(isinstance(group, tuple)):
                # print(sequence[0][0])
                # tuple means instrument has an accent value
                sequence[int(offset)][group[0]] = 1
                sequence[int(offset)][group[0]+1] = group[1]
            elif(group is not None):
                sequence[int(offset)][group] = 1
            else:
                raise ValueError(f'ERROR: note {midinote} not in percussion map')
        else:
            midinote = midinote - transpose
            sequence[int(offset)][midinote] = 1

    
    def getLowestNote(self, measure: Measure):
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
