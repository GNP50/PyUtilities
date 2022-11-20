import math
import random
import re

import numpy as np
from sklearn.model_selection import train_test_split
import cv2
import copy
import os
import tqdm


from threading import Thread
import multiprocessing as mp

def pipeExternalConcStep(instance,i,j):
    instance.startPipelineForInput(i,j)

def pipeExternalConcStepAutoEncoder(instance,i,j,k):
    instance.startPipelineForInput(i,j,k)

def rotateExternalConcStep(instance,i):
    instance.rotate(i)

def splitExternalConcStep(instance,i,j):
    instance.split(i,j)

def pruneExternalConcStep(instance,i):
    instance.rotate(i)


def doParalllel(myFunction,inputs,instance):

        process = []

        for i in inputs:
            i.insert(0, instance)
            i = tuple(i)
            new_t = Thread(target=myFunction, args=i)
            process.append(new_t)
            new_t.start()

        for p in process:
            p.join()




class PreprocessingStage():
    def __init__(self,X):
        self.data = X
        self.Y = None
        self.isMultiOutput = False

    def perform(self):
        pass
class ScalingStage(PreprocessingStage):
    def __init__(self,X,sizes):
        self.sizes = sizes
        PreprocessingStage.__init__(self,X)

    def perform(self,toPerform=True):
        if toPerform:
            self.Y = cv2.resize(self.X,self.sizes)
        else:
            self.Y = self.X

class NormalizeStage(ScalingStage):
    def __init__(self,sizes,X=None):
        ScalingStage.__init__(self,X,sizes)

    def perform(self):
        #self.Y = cv2.fastNlMeansDenoisingColored(self.X, None, 20, 20, 7, 21)
        self.Y = self.X

        self.X,self.Y = self.Y,None
        ScalingStage.perform(self)


class SplitStage(ScalingStage):
    def __init__(self,sizes,splits,X=None):
        ScalingStage.__init__(self,X,sizes)
        self.Y = []
        self.splits = splits
        self.isMultiOutput = True

    def perform(self):

        self.imgheight = self.X.shape[0]
        self.imgwidth = self.X.shape[1]

        self.M = self.imgheight // self.splits
        self.N = self.imgwidth // self.splits

        self.Y.append(self.X)

        inputs = []
        for y in range(0, self.imgheight, self.M):
            for x in range(0, self.imgwidth, self.N):
                inputs.append([x,y])


        myFunction = splitExternalConcStep
        doParalllel(myFunction,inputs,self)

    def split(self,x,y):
        tiles = self.X[y:y + self.M, x:x + self.N]
        self.Y.append(tiles)






class RotationStage(ScalingStage):
    def __init__(self,sizes,angleStep=10,X=None):
        ScalingStage.__init__(self,X,sizes)
        self.angleStep = angleStep
        self.Y = []
        self.isMultiOutput = True

    def perform(self):
        (self.h, self.w) = self.X.shape[:2]
        (self.cX, self.cY) = (self.w // 2, self.h // 2)

        self.Y.append(self.X)

        inputs = [ [i] for i in range(0,self.angleStep)]
        myFunction = rotateExternalConcStep

        doParalllel(myFunction,inputs,self)


    def rotate(self,i):
        angle = 360 / self.angleStep * i
        M = cv2.getRotationMatrix2D((self.cX, self.cY), angle, 1.0)
        rotated = cv2.warpAffine(self.X, M, (self.w, self.h))

        self.Y.append(rotated)
