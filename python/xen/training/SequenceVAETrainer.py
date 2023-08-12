from xen.data.SongData import SongData, SongDataSet
from xen.data.PercussionMap import PercussionMap
from xen.codecs.NoteSequenceFlatCodec import NoteSequenceFlatCodec
from xen.models.VariationalAutoencoder import VariationalAutoEncoder
from xen.models.AbstractModel import ModelMetadata
from xen.visualise import plotSparseNoteSequence
from .ModelTrainer import ModelTrainer

import numpy as np
import tensorflow as tf
from tensorflow.keras.optimizers.legacy import Adam
from keras.callbacks import ReduceLROnPlateau, EarlyStopping
from typing import List, Callable

from matplotlib import pyplot as plt

DECODER_TYPE_NOTE = "seqdec"
DECODER_TYPE_PERCUSSION = "perdec"


class SequenceVAEMetaData(ModelMetadata):
    def __init__(self, type:str, notesPerTick:int, ticksPerSequence:int, latentScale:int):
        self.type = type
        self.notesPerTick = notesPerTick
        self.ticksPerSequence = ticksPerSequence
        self.latentScale = latentScale
        metabytes = [notesPerTick, ticksPerSequence, latentScale]
        super().__init__(type, metabytes)

class SequenceVAENoteMetaData(SequenceVAEMetaData):
    def __init__(self, notesPerTick, ticksPerSequence, latentScale:int):
        super().__init__(DECODER_TYPE_NOTE, notesPerTick, ticksPerSequence, latentScale)

class SequenceVAEPercussionGroupedMetaData(SequenceVAEMetaData):
    def __init__(self, notesPerTick, ticksPerSequence, latentScale:int, groupSizes:List[int]):
        self.groupSizes = groupSizes
        super().__init__(DECODER_TYPE_PERCUSSION, notesPerTick, ticksPerSequence, latentScale)
        self.metabytes.extend([len(groupSizes)] + groupSizes)


class SequenceVAETrainer(ModelTrainer):
    def __init__(self, modelName, modelPath="../models"):
        super().__init__(modelName, modelPath)
        self.model:VariationalAutoEncoder|None = None
        self.dataset:SongDataSet = SongDataSet([])


    def setModel(self, model):
        self.model = model


    def loadSongDataset(self, paths:List[str], recursive:bool = False, timesig = '4/4', ticksPerQuarter = 4, quartersPerMeasure = 4, measuresPerSequence = 1, 
                        instrumentFilter:List[str]|None = None, percussionMap:PercussionMap|None = None):
        self.dataset = SongDataSet.fromMidiPaths(paths, recursive).filterTimeSig(timesig)
        self.codec = NoteSequenceFlatCodec(ticksPerQuarter, quartersPerMeasure, measuresPerSequence, timesignature=timesig, instrumentFilter=instrumentFilter, trim = True, normaliseOctave=True, percussionMap=percussionMap)
        self.codec.encodeAll(self.dataset)
        if(percussionMap is None):
            self.metadata = SequenceVAENoteMetaData(notesPerTick=self.codec.maxNote-self.codec.minNote+1, 
                                                    ticksPerSequence=ticksPerQuarter*quartersPerMeasure*measuresPerSequence, 
                                                    latentScale=3)
        else:
            self.metadata = SequenceVAEPercussionGroupedMetaData(notesPerTick=self.codec.maxNote-self.codec.minNote+1, 
                                                                 ticksPerSequence=ticksPerQuarter*quartersPerMeasure*measuresPerSequence, 
                                                                 groupSizes=percussionMap.groupSizes,
                                                                 latentScale=3)
        self.datasetInfo['paths'] = paths
        self.datasetInfo['recursive'] = recursive
        self.datasetInfo['timesig'] = timesig
        self.datasetInfo['ticksPerQuarter'] = ticksPerQuarter
        self.datasetInfo['quartersPerMeasure'] = quartersPerMeasure
        self.datasetInfo['measuresPerSequence'] = measuresPerSequence
        self.datasetInfo['instrumentFilter'] = instrumentFilter


    def createModel(self, latentDim = 3, hiddenLayers = 2, latentScale:float = 3.0):
        # calculate layer dimensions as a reduction by equal factor
        inputDim = self.dataset.getDataset()[0].shape[0]
        # inputDim = self.dataset.getDataset().shape[1]
        dimDivider = (inputDim // latentDim) ** (1./(hiddenLayers + 1))
        layerDims = [inputDim]
        for i in range(hiddenLayers):
            layerDims.append(int(layerDims[-1] / dimDivider))
        layerDims.append(latentDim)
        print(f'Layer dims: {layerDims}')
        self.model = VariationalAutoEncoder.from_new(layerDims=layerDims, name=self.modelName, path=self.modelPath, latentScale=latentScale)
        self.model.compile(optimizer=Adam(learning_rate=0.005))
        self.modelInfo['latentDim'] = latentDim
        self.modelInfo['hiddenLayers'] = hiddenLayers
        self.modelInfo['latentScale'] = latentScale
        self.metadata.latentScale = int(latentScale)


    def loadModel(self):
        self.model = VariationalAutoEncoder.from_pretrained(name=self.modelName, path=self.modelPath)


    def getTrainData(self):
        return np.array(self.dataset.getDataset())


    def train(self, batchSize = 32, epochs = 500, learningRate = 0.005, minLearningRate = 1e-6, factor=0.5, patience=100):
        if self.model is None:
            raise Exception('Model not set')
        self.model.compile(optimizer=Adam(learning_rate=learningRate))
        early_stopping = EarlyStopping(monitor='loss', patience=500, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='loss', factor=factor, patience=patience, min_lr=minLearningRate)
        history = self.model.train(self.getTrainData(), batchSize = batchSize, epochs = epochs, callbacks=[early_stopping, reduce_lr])
        # history = self.model.train(self.getTrainData(), batchSize = batchSize, epochs = epochs)
        self.addTrainingInfo(batchSize, epochs, learningRate, minLearningRate, factor, patience, history)


    def saveModel(self, quantize = None):
        if self.model is None:
            raise Exception('Model not set')
        self.model.save(quantize=quantize, metadata = self.metadata)
        self.saveModelInfo(metadata = self.metadata)


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


