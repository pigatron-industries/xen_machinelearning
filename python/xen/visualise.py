from music21.stream.base import Measure
from matplotlib import pyplot as plt

from xen.data.SongData import elementToMidiPitches


def plotPart(part):
    print(part.partName)
    measures = part.getElementsByClass(Measure)
    plotMeasures(measures)


def plotMeasures(measures):
    hasnotes = False
    for measure in measures:
        if (len(measure.recurse().notes) > 0):
            hasnotes = True
    if (not hasnotes):
        return

    plt.figure(figsize=(20, 4))
    for measure in measures:

        if (measure.timeSignature is None):
            plt.axvline(x = measure.offset, color = 'grey')
        else:
            plt.axvline(x = measure.offset, color = 'green', label='timesig')
            plt.text(x = measure.offset, y=45, s=f'{measure.timeSignature.numerator}/{measure.timeSignature.denominator}')

        for element in measure.recurse().notes:
            midipitches = elementToMidiPitches(element)
            for midipitch in midipitches:
                plt.plot([measure.offset+element.offset, measure.offset+element.offset+element.duration.quarterLength], [midipitch, midipitch], color='b', marker='.')

    plt.xlabel('Time (qtr notes)')
    plt.ylabel('Pitch (midi)')
    plt.show()


def plotSparseNoteSequence(sequence, threshold=0.5):
    plt.figure(figsize=(20, 4))
    for i, tick in enumerate(sequence):
        for j, note in enumerate(tick):
            if(note > threshold):
                plt.plot([i, i], [j, j], color='b', marker='.')

    plt.xlabel('Ticks')
    plt.ylabel('Pitch (midi)')
    plt.show()