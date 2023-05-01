from tensorflow.python.framework.ops import disable_eager_execution
from tensorflow.keras.layers import Input, Dense, Lambda, Layer
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers.legacy import Adam
from tensorflow.keras import backend as K
from tensorflow.keras import metrics
import tensorflow as tf

class AutoEncoder:
    def __init__(self, inputDim, latentDim):
        self.inputShape = (inputDim)
        self.latentShape = (latentDim)
        # encoder model
        self.encoderInputLayer = Input(shape = self.inputShape)
        self.encoderOutputLayer = Dense(self.latentShape, activation = 'tanh')(self.encoderInputLayer)
        self.encoderModel = Model(self.encoderInputLayer, self.encoderOutputLayer)
        # decoder model
        self.decoderInputLayer = Input(shape = self.latentShape)
        self.decoderOutputLayer = Dense(self.inputShape, activation = 'sigmoid')(self.decoderInputLayer)
        self.decoderModel = Model(self.decoderInputLayer, self.decoderOutputLayer)
        # autoencoder model
        self.vaeInputLayer = self.encoderInputLayer
        self.vaeOutputLayer = self.decoderModel(self.encoderOutputLayer)
        self.autoencoderModel = Model(self.encoderInputLayer, self.vaeOutputs)

    def compile(self, loss = 'binary_crossentropy', optimizer=Adam(learning_rate=0.01)):
        self.autoencoderModel.compile(loss=loss, optimizer=optimizer)

    def train(self, traindata, epochs):
        self.autoencoderModel.fit(traindata, traindata, epochs = epochs)

    def encode(self, inputdata):
        return self.encoderModel.predict(inputdata)

    def decode(self, latentdata):
        return self.decoderModel.predict(latentdata)

    def predict(self, inputdata):
        return self.autoencoderModel.predict(inputdata)


class Sampling(Layer):
    def call(self, inputs):
        meanLayer, logVarLayer = inputs
        batch = tf.shape(meanLayer)[0]
        dim = tf.shape(meanLayer)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return meanLayer + tf.exp(0.5 * logVarLayer) * epsilon
    

class VariationalAutoEncoder:
    def __init__(self, inputDim, internalDim, latentDim):
        disable_eager_execution()

        self.inputShape = (inputDim,)
        self.internalShape = (internalDim,)
        self.latentShape = (latentDim,)
        # encoder model
        self.encoderInputLayer = Input(shape = self.inputShape, name='encinput')
        self.encoderInternalLayer = Dense(internalDim, activation='relu', name='encinternal')(self.encoderInputLayer)

        self.meanLayer = Dense(latentDim, name='mean')(self.encoderInternalLayer)
        self.logVarLayer = Dense(latentDim, name='logvar')(self.encoderInternalLayer)
        self.samplingLayer = Sampling()([self.meanLayer, self.logVarLayer])
        # self.samplingLayer = Lambda(self.samplingLayerFunc, output_shape=(latentDim,), name='sampling')([self.meanLayer, self.logVarLayer])
        self.encoderModel = Model(self.encoderInputLayer, [self.meanLayer, self.logVarLayer, self.samplingLayer], name='encoder')
        self.encoderModel.summary()
        # decoder model
        self.decoderInputLayer = Input(shape = self.latentShape, name='decinput')
        self.decoderInternalLayer  =  Dense(internalDim, activation='relu', name='decinternal')(self.decoderInputLayer)
        self.decoderOutputLayer = Dense(self.inputShape[0], activation = 'sigmoid')(self.decoderInternalLayer)
        self.decoderModel = Model(self.decoderInputLayer, self.decoderOutputLayer, name='decoder')
        self.decoderModel.summary()
        # autoencoder model
        self.vaeInputLayer = self.encoderInputLayer
        self.vaeOutputLayer = self.decoderModel(self.samplingLayer)
        self.vaeModel = Model(self.encoderInputLayer, self.vaeOutputLayer, name='autoencoder')
        # loss function
        # reconstructionLoss = tf.keras.losses.binary_crossentropy(self.vaeModel.inputs[0], self.vaeModel.outputs[0])
        # klLoss = -0.5 * tf.reduce_mean(1 + self.logVarLayer - tf.square(self.meanLayer) - tf.exp(self.logVarLayer))
        # vaeLoss = reconstructionLoss + klLoss * klWeight
    
    def vaeLoss(self, inputLayer, outputLayer):
        reconstructionLoss = metrics.binary_crossentropy(inputLayer, outputLayer) * self.inputShape[0]
        klLoss = -0.5 * K.sum(1 + self.logVarLayer - K.square(self.meanLayer) - K.exp(self.logVarLayer), axis=-1)
        return K.mean(reconstructionLoss + klLoss)


    def compile(self, optimizer=Adam(learning_rate=0.01)):
        self.vaeModel.compile(optimizer=optimizer, loss=self.vaeLoss)


    def train(self, traindata, batchSize, epochs):
        self.vaeModel.fit(traindata, traindata, epochs = epochs) 
        # batch_size=batchSize

    def encode(self, inputdata):
        return self.encoderModel.predict(inputdata)

    def decode(self, latentdata):
        return self.decoderModel.predict(latentdata)

    def predict(self, inputdata):
        return self.vaeModel.predict(inputdata)