from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers.legacy import Adam
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
