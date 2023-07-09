from .AbstractModel import AbstractModel
from tensorflow.python.framework.ops import disable_eager_execution
from tensorflow.keras.layers import Input, Dense, Layer, Lambda
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers.legacy import Adam
from tensorflow.keras import backend as K
from tensorflow.keras import metrics
from tensorflow.keras.utils import custom_object_scope
import tensorflow as tf
import os


def sampling(args):
    meanLayer, logVarLayer = args
    batch = tf.shape(meanLayer)[0]
    dim = tf.shape(meanLayer)[1]
    epsilon = K.random_normal(shape=(batch, dim), mean=0.0, stddev=1.0)
    return meanLayer + K.exp(0.5 * logVarLayer) * epsilon


class VariationalAutoEncoder(AbstractModel):

    vae_suffix = 'vae'
    decoder_suffix = 'dec'
    encoder_suffix = 'enc'

    def __init__(self, path, name):
        super().__init__(path, name)
        disable_eager_execution()
            

    @classmethod
    def from_pretrained(cls, path, name):
        model = cls(path = path, name = name)
        model.load()
        return model


    @classmethod
    def from_new(cls, layerDims, path, name):
        model = cls(path = path, name = name)
        model.create(layerDims=layerDims)
        return model


    def create(self, layerDims = [2048, 512, 128, 32]):
        self.inputDim = layerDims[0]
        self.internalDims = layerDims[1:-1]
        self.latentDim = layerDims[-1]
        # encoder model
        self.encoderInputLayer = Input(self.inputDim, name='encoder_input')
        encoderInternalLayer = self.encoderInputLayer
        internalInputLayer = self.encoderInputLayer
        for i, dim in enumerate(self.internalDims):
            encoderInternalLayer = Dense(dim, activation='relu', name=f'encoder_internal_{i}')(internalInputLayer)
            internalInputLayer = encoderInternalLayer
        self.meanLayer = Dense(self.latentDim, name='encoder_mean')(encoderInternalLayer)
        self.logVarLayer = Dense(self.latentDim, name='encoder_logvar')(encoderInternalLayer)
        self.samplingLayer = Lambda(sampling, output_shape=(self.latentDim), name = 'encoder_sampling')([self.meanLayer, self.logVarLayer])
        self.encoderModel = Model(self.encoderInputLayer, [self.meanLayer, self.logVarLayer, self.samplingLayer], name='encoder')
        self.encoderModel.summary()
        # decoder model
        self.decoderInputLayer = Input(self.latentDim, name='decoder_input')
        decoderInternalLayer = self.decoderInputLayer
        internalInputLayer = self.decoderInputLayer
        for i, dim in enumerate(self.internalDims[::-1]):
            decoderInternalLayer = Dense(dim, activation='relu', name=f'decoder_internal_{i}')(internalInputLayer)
            internalInputLayer = decoderInternalLayer
        self.decoderOutputLayer = Dense(self.inputDim, activation = 'sigmoid', name='decoder_output')(decoderInternalLayer)
        self.decoderModel = Model(self.decoderInputLayer, self.decoderOutputLayer, name='decoder')
        self.decoderModel.summary()
        # autoencoder model
        self.vaeInputLayer = self.encoderInputLayer
        self.vaeOutputLayer = self.decoderModel(self.samplingLayer)
        self.vaeModel = Model(self.encoderInputLayer, self.vaeOutputLayer, name='autoencoder')
        self.vaeModel.summary()

    
    def vaeLoss(self, inputLayer, outputLayer):
        reconstructionLoss = metrics.binary_crossentropy(inputLayer, outputLayer) * self.inputDim
        klLoss = -0.5 * K.sum(1 + self.logVarLayer - K.square(self.meanLayer) - K.exp(self.logVarLayer), axis=-1)
        return K.mean(reconstructionLoss + klLoss)


    def compile(self, optimizer=Adam(learning_rate=0.01)):
        self.vaeModel.compile(optimizer=optimizer, loss=self.vaeLoss)


    def train(self, traindata, epochs, batchSize = 32):
        self.vaeModel.fit(traindata, traindata, epochs = epochs, batch_size=batchSize) 


    def encode(self, inputdata):
        return self.encoderModel.predict(inputdata)


    def decode(self, latentdata):
        return self.decoderModel.predict(latentdata)


    def predict(self, inputdata):
        return self.vaeModel.predict(inputdata)
    

    def save(self, quantize = None, metadata = None):
        vaeName = f"{self.name}_{self.vae_suffix}"
        encoderName = f"{self.name}_{self.encoder_suffix}"
        decoderName = f"{self.name}_{self.decoder_suffix}"
        self.saveModelH5(self.vaeModel, vaeName)
        self.saveModelH5(self.encoderModel, encoderName)
        self.saveModelH5(self.decoderModel, decoderName)
        self.saveModelTfLite(self.decoderModel, decoderName, quantize, metadata)


    def load(self):
        vaeName = f"{self.name}_{self.vae_suffix}"
        self.vaeModel = self.loadModel(vaeName)
        self.encoderInputLayer = self.vaeModel.get_layer('encoder_input').input
        self.meanLayer = self.vaeModel.get_layer('encoder_mean').output
        self.logVarLayer = self.vaeModel.get_layer('encoder_logvar').output
        self.samplingLayer = self.vaeModel.get_layer('encoder_sampling').output
        self.decoderModel = self.vaeModel.get_layer('decoder')
        self.encoderModel = Model(self.encoderInputLayer, [self.meanLayer, self.logVarLayer, self.samplingLayer], name='encoder')
        self.vaeOutputLayer = self.decoderModel.output
        self.vaeModel.summary()

        self.inputDim = self.encoderInputLayer.shape[1]
        self.latentDim = self.meanLayer.shape[1]
        self.internalDims = []
        for i in range(len(self.vaeModel.layers)):
            if 'encoder_internal' in self.vaeModel.layers[i].name:
                self.internalDims.append(self.vaeModel.layers[i].output_shape[1])
