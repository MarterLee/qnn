# -*- coding: utf-8 -*-
from models.BasicModel import BasicModel
from keras.layers import Embedding, GlobalMaxPooling1D,Dense, Masking, Flatten,Dropout, Activation,concatenate,Reshape, Permute,Lambda, Subtract
from keras.models import Model, Input, model_from_json, load_model, Sequential
from keras.constraints import unit_norm
from layers.keras.complexnn import *
import math
import numpy as np

from keras import regularizers
import keras.backend as K
from distutils.util import strtobool


class SiameseNetwork(BasicModel):

    def initialize(self):
        self.question = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
        self.answer = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
        self.neg_answer = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
        
        if self.opt.bert_enabled:
            self.mask = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
            self.question = [self.question,self.mask]
            self.mask = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
            self.answer = [self.answer,self.mask]
            self.mask = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
            self.neg_answer = [self.neg_answer,self.mask]

#        self.distance = Lambda(l2_distance)
#        self.distance = Lambda(cosine_similarity)
#        self.triplet_loss = Lambda(triplet_hinge_loss)
        distances= [getScore("AESD.AESD",mean="geometric",delta =0.5,c=1,dropout_keep_prob =self.opt.dropout_rate_probs),
                    getScore("AESD.AESD",mean="geometric",delta =1,c=1,dropout_keep_prob =self.opt.dropout_rate_probs),
                    getScore("AESD.AESD",mean="geometric",delta =1.5,c=1,dropout_keep_prob =self.opt.dropout_rate_probs),
                    getScore("AESD.AESD",mean="arithmetic",delta =0.5,c=1,dropout_keep_prob =self.opt.dropout_rate_probs),
                    getScore("AESD.AESD",mean="arithmetic",delta =1,c=1,dropout_keep_prob =self.opt.dropout_rate_probs),
                    getScore("AESD.AESD",mean="arithmetic",delta =1.5,c=1,dropout_keep_prob =self.opt.dropout_rate_probs),
                    getScore("cosine.Cosinse",dropout_keep_prob =self.opt.dropout_rate_probs)
                    ]
                    
        self.distance = distances[self.opt.distance_type]
        if self.opt.onehot:
            self.distance = getScore("multiple_loss.Multiple_loss",dropout_keep_prob =self.opt.dropout_rate_probs)
        
#        self.dense = Dense(self.opt.nb_classes, activation=self.opt.activation, kernel_regularizer= regularizers.l2(self.opt.dense_l2))
        
        self.representation_model = None
                
    def __init__(self,opt):
        super(SiameseNetwork, self).__init__(opt)

    def build(self):
        
        if self.opt.match_type == 'pointwise':
            rep = []
            for doc in [self.question, self.answer]:
                rep.append(self.representation_model.get_representation(doc))
            output = self.distance(rep)
#            output =  Cosinse(dropout_keep_prob=self.opt.dropout_rate_probs)(rep) 
            if self.opt.bert_enabled:
                model = Model([self.question[0],self.question[1],self.answer[0],self.answer[1]], output)
            else:
                model = Model([self.question,self.answer], output)
            
        elif self.opt.match_type == 'pairwise':
#            rep = []
#            for doc in [self.question, self.answer, self.neg_answer]:
#                rep.append(rep_m.get_representation(doc))
            q_rep = self.representation_model.get_representation(self.question)

            score1 = self.distance([q_rep, self.representation_model.get_representation(self.answer)])
            score2 = self.distance([q_rep, self.representation_model.get_representation(self.neg_answer)])
            basic_loss = MarginLoss(self.opt.margin)( [score1,score2])
            
            output=[score1,basic_loss,basic_loss]
            if self.opt.bert_enabled:
                model = Model([self.question[0],self.question[1], self.answer[0],self.answer[1], self.neg_answer[0],self.neg_answer[1]], output)           
            else:
                model = Model([self.question, self.answer, self.neg_answer], output)       
        else:
            raise ValueError('wrong input of matching type. Please input pairwise or pointwise.')
        return model