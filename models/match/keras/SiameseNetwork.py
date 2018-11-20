# -*- coding: utf-8 -*-

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


class SiameseNetwork(BasicModel):

    def initialize(self):
        self.question = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
        self.answer = Input(shape=(self.opt.max_sequence_length,), dtype='float32')
        self.neg_answer = Input(shape=(self.opt.max_sequence_length,), dtype='float32')


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
                    
        self.distance= distances[self.opt.distance_type]
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
            model = Model([self.question, self.answer], output)
            
        elif self.opt.match_type == 'pairwise':
#            rep = []
#            for doc in [self.question, self.answer, self.neg_answer]:
#                rep.append(rep_m.get_representation(doc))
            q_rep = self.dropout_probs(self.representation_model.get_representation(self.question))

            score1 = self.distance([q_rep, self.representation_model.get_representation(self.answer)])
            score2 = self.distance([q_rep, self.representation_model.get_representation(self.neg_answer)])
            basic_loss = MarginLoss(self.opt.margin)( [score1,score2])
            
            output=[score1,basic_loss,basic_loss]
            model = Model([self.question, self.answer, self.neg_answer], output)           
        else:
            raise ValueError('wrong input of matching type. Please input pairwise or pointwise.')
        return model