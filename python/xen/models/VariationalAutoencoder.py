from tensorflow.python.framework.ops import disable_eager_execution
from tensorflow.keras.layers import Input, Dense, Layer, Lambda
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers.legacy import Adam
from tensorflow.keras import backend as K
from tensorflow.keras import metrics
import tensorflow as tf


class Sampling(Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def call(self, inputs):
        meanLayer, logVarLayer = inputs
        batch = tf.shape(meanLayer)[0]
        dim = tf.shape(meanLayer)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return meanLayer + tf.exp(0.5 * logVarLayer) * epsilon
    

def sampling(args):
    meanLayer, logVarLayer = args
    batch = tf.shape(meanLayer)[0]
    dim = tf.shape(meanLayer)[1]
    epsilon = K.random_normal(shape=(batch, dim), mean=0.0, stddev=1.0)
    return meanLayer + K.exp(0.5 * logVarLayer) * epsilon


class VariationalAutoEncoder:
    def __init__(self, layerDims = None, filename = None):
        disable_eager_execution()
        if filename is not None:
            self.load(filename)
        else:
            self.create(layerDims)

    def create(self, layerDims = [2048, 512, 128, 32]):
        self.inputDim = layerDims[0]
        self.internalDims = layerDims[1:-1]
        self.latentDim = layerDims[-1]
        # encoder model
        self.encoderInputLayer = Input(shape = (self.inputDim,), name='encoder_input')
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
        self.decoderInputLayer = Input(shape = (self.latentDim,), name='decoder_input')
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
    
    def save(self, filename):
        self.vaeModel.save(f"{filename}")

    def load(self, filename):
        self.vaeModel = load_model(f"{filename}")
        self.encoderModel = self.vaeModel.get_layer('encoder')
        self.decoderModel = self.vaeModel.get_layer('decoder')
        self.encoderInputLayer = self.encoderModel.get_layer('encoder_input')
        self.meanLayer = self.encoderModel.get_layer('encoder_mean')
        self.logVarLayer = self.encoderModel.get_layer('encoder_logvar')
        self.samplingLayer = self.encoderModel.get_layer('encoder_sampling')
        self.decoderInputLayer = self.decoderModel.get_layer('decoder_input')
        self.vaeOutputLayer = self.decoderModel.get_layer('decoder_output')
        self.inputDim = self.encoderInputLayer.shape[0]
        self.latentDim = self.meanLayer.shape[0]
        self.internalDims = []
        for i in range(len(self.encoderModel.layers)):
            if 'encoder_internal' in self.encoderModel.layers[i].name:
                self.internalDims.append(self.encoderModel.layers[i].shape[0])



