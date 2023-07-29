from xen.data.SongData import SongData, SongDataSet
from xen.codecs.NoteSequenceFlatCodec import NoteSequenceFlatCodec
from xen.models.VariationalAutoencoder import VariationalAutoEncoder
from xen.models.AbstractModel import ModelMetadata
from xen.visualise import plotSparseNoteSequence

import numpy as np
import tensorflow as tf
from tensorflow.keras.optimizers.legacy import Adam
from typing import List, Callable

from matplotlib import pyplot as plt

DECODER_TYPE_SEQ = "seqdec"
DECODER_TYPE_PERC = "perdec"


class SequenceVAEMetaData(ModelMetadata):
    def __init__(self, notesPerTick, ticksPerSequence, type = "seqdec"):
        self.notesPerTick = notesPerTick
        self.ticksPerSequence = ticksPerSequence
        super().__init__(type, [notesPerTick, ticksPerSequence])


class SequenceVAETrainer:
    def __init__(self, modelName, modelPath="../models"):
        self.model:VariationalAutoEncoder|None = None
        self.dataset:SongDataSet = SongDataSet()
        self.modelPath = modelPath
        self.modelName = modelName


    def setModel(self, model):
        self.model = model


    def setDataset(self, dataset):
        self.dataset = dataset


    def loadSongDataset(self, paths:List[str], recursive:bool = False, timesig = '4/4', ticksPerQuarter = 4, quartersPerMeasure = 4, measuresPerSequence = 1, 
                        percussionMap:None|Callable[[int], int] = None):
        self.dataset = SongDataSet.fromMidiPaths(paths, recursive).filterTimeSig(timesig)
        self.codec = NoteSequenceFlatCodec(ticksPerQuarter, quartersPerMeasure, measuresPerSequence, timesig, trim = True, normaliseOctave=True, percussionMap=percussionMap)
        self.codec.encodeAll(self.dataset)
        type = DECODER_TYPE_SEQ if percussionMap is None else DECODER_TYPE_PERC
        self.metadata = SequenceVAEMetaData(self.codec.maxNote-self.codec.minNote+1, ticksPerQuarter*quartersPerMeasure*measuresPerSequence, type=type)


    def createModel(self, latentDim = 3, hiddenLayers = 2):
        # calculate layer dimensions as a reduction by equal factor
        inputDim = self.dataset.getDataset()[0].shape[0]
        # inputDim = self.dataset.getDataset().shape[1]
        dimDivider = (inputDim // latentDim) ** (1./(hiddenLayers + 1))
        layerDims = [inputDim]
        for i in range(hiddenLayers):
            layerDims.append(int(layerDims[-1] / dimDivider))
        layerDims.append(latentDim)
        print(f'Layer dims: {layerDims}')
        self.model = VariationalAutoEncoder.from_new(layerDims=layerDims, name=self.modelName, path=self.modelPath)
        self.model.compile(optimizer=Adam(learning_rate=0.005))


    def loadModel(self):
        self.model = VariationalAutoEncoder.from_pretrained(name=self.modelName, path=self.modelPath)


    def getTrainData(self):
        return np.array(self.dataset.getDataset())


    def train(self, batchSize = 32, epochs = 500, learning_rate = 0.005):
        if self.model is None:
            raise Exception('Model not set')
        self.model.compile(optimizer=Adam(learning_rate=learning_rate))
        self.model.train(self.getTrainData(), batchSize = batchSize, epochs = epochs)


    def saveModel(self, quantize = None):
        if self.model is None:
            raise Exception('Model not set')
        self.model.save(quantize=quantize, metadata = self.metadata)


    def calcRecall(self):
        if self.model is None:
            raise Exception('Model not set')
        output = self.model.predict(self.getTrainData())
        matches = self._countMatches(self.dataset.getDataset(), output)
        print(f'{matches/len(self.dataset.getDataset())*100}% recall')


    def _countMatches(self, indata, outdata):
        matches = 0
        for i in range(0, len(indata)):
            insequence = indata[i]
            outsequence = outdata[i]
            match = True
            for j in range(len(insequence)):
                if ((insequence[j] >= 0.5 and outsequence[j] < 0.5) or (insequence[j] < 0.5 and outsequence[j] >= 0.5)):
                    match = False
                    # print(i)
            if (match):
                matches = matches + 1
        return matches
    

    def plotLatentSpace(self, dimensions = 3):
        """ Plots a point for each sequence in the dataset in the latent space """
        if self.model is None:
            raise Exception('Model not set')
        latentdata = self.model.encode(self.getTrainData())
        sampling = np.array(latentdata[0])
        print(sampling[:,0])

        if(dimensions == 1):
            plt.figure(figsize=(20, 4))
            plt.scatter(sampling[:,0], [0]*len(sampling), color='b', marker='.')
            plt.show()
        else:
            # TODO loop through dimensions
            plt.figure(figsize=(20, 4))
            plt.scatter(sampling[:,0], sampling[:,1], color='b', marker='.')
            plt.show()

            plt.figure(figsize=(20, 4))
            plt.scatter(sampling[:,1], sampling[:,2], color='b', marker='.')
            plt.show()

            plt.figure(figsize=(20, 4))
            plt.scatter(sampling[:,2], sampling[:,0], color='b', marker='.')
            plt.show()


    def plotInputOutputSequence(self, index, threshold = 0.5):
        if self.model is None:
            raise Exception('Model not set')
        insequence = self.getTrainData()[index:index+1]
        outsequence = self.model.predict(insequence)

        print(insequence.shape)
        print(self.codec.decode([insequence])[0].shape)

        plotSparseNoteSequence(self.codec.decode([insequence])[0], threshold = threshold)
        plotSparseNoteSequence(self.codec.decode([outsequence])[0], threshold = threshold)
        latent = self.model.encode([insequence])[0]
        print(latent)


    def plotOutputValueDistribution(self):
        if self.model is None:
            raise Exception('Model not set')
        output = self.model.predict(self.getTrainData())
        plt.hist(output.flatten(), bins=100)
        plt.ylim(0, 5000)
        plt.show()
