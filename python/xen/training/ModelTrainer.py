import yaml


class ModelTrainer:
    def __init__(self, modelName, modelPath="../models"):
        self.modelName = modelName
        self.modelPath = modelPath
        self.trainingInfo = []
        self.datasetInfo = {}
        self.modelInfo = {}
        
    def setDataset(self, dataset):
        self.dataset = dataset

    def addTrainingInfo(self, batchSize, epochs, learningRate, history):
        traininginfo = {}
        traininginfo['batchSize'] = batchSize
        traininginfo['epochs'] = epochs
        traininginfo['learningRate'] = learningRate
        traininginfo['loss'] = history['loss'][-1]
        self.trainingInfo.append(traininginfo)

    def saveModelInfo(self):
        info = {}
        info['name'] = self.modelName
        info['training'] = self.trainingInfo
        info['dataset'] = self.datasetInfo
        info['model'] = self.modelInfo
        with open(f'{self.modelPath}/{self.modelName}.yml', 'w') as outfile:
            yaml.dump(info, outfile)
    