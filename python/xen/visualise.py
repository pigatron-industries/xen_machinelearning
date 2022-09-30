from music21 import stream, meter
from matplotlib import pyplot as plt


def plotPart(part):
    print(part.partName)
    measures = part.getElementsByClass(stream.Measure)
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
            if element.isNote:
                plt.plot([measure.offset+element.offset, measure.offset+element.offset+element.duration.quarterLength], [element.pitch.midi, element.pitch.midi], color='b', marker='.')
            if element.isChord:
                for note in element.notes:
                    plt.plot([measure.offset+element.offset, measure.offset+element.offset+element.duration.quarterLength], [note.pitch.midi, note.pitch.midi], color='b', marker='.')

    plt.xlabel('Time (qtr notes)')
    plt.ylabel('Pitch (midi)')
    plt.show()


def plotSequence(sequence):
    plt.figure(figsize=(20, 4))
    for i, tick in enumerate(sequence):
        for j, note in enumerate(tick):
            if(note > 0.5):
                plt.plot([i, i], [j, j], color='b', marker='.')

    plt.xlabel('Ticks')
    plt.ylabel('Pitch (midi)')
    plt.show()