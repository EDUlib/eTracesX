'''
Classes for dropout prediction models
11/12/2014
Sebastien Boyer

Updated to get rid of reliance on csv files in favor of accessing database
directly
5/28/15
Ben Schreck
'''
import numpy as np
#import csv
import os
from preprocess_data import *
import flatten_featureset
from statistical_feat import *
from logreg_transfer import *
from multiTaskParam_learning import *
from importanceSampling import *

from sklearn import linear_model, cross_validation,svm
from sklearn.metrics import roc_curve, auc
import pylab as pl

import utils


class Course:
    def __init__(self,name, earliest_date, latest_date, features, weeks,
            threshold, db_conn):
        self.name=name
        #self.file='prediction/data/'+name+'.csv'
        #self.processed_file='prediction/data/'+name+'_processed.csv'
        #self.train_file='prediction/data/'+name+'_processed_train.csv'
        #self.test_file='prediction/data/'+name+'_processed_test.csv'
        self.X_train=[]
        self.X_test=[]
        self.Y_test=[]
        self.Y_train=[]
        self.weeks=set(weeks)
        self.max_w = max(weeks)
        self.features=np.array(features)
        self.earliest_date = earliest_date
        self.latest_date = latest_date
        self.threshold = threshold
        self.conn = db_conn

    #def processed(self):
        #if os.path.exists(self.processed_file)==False:
            #self.weeks,self.features=runPreProcessing(self.name)
        #else:
            #data = np.genfromtxt(self.processed_file,dtype='string', delimiter = ',')
            #self.features=data[0,2:]
            #self.weeks=set(data[1:,0])
            #print self.processed_file," already exist !"



    #def separate_traintest(self,threshold):
        #if os.path.exists(self.processed_file):
            #if os.path.exists(self.train_file)==False and os.path.exists(self.test_file)==False:
                #data=extractArray_fromCSV(self.processed_file,True)
                #end_train=int(threshold*np.shape(data)[0]/len(self.weeks))*len(self.weeks)

                #data_train=np.array(data[:end_train,1:])#.astype(np.float)
                #write_inCSV(data_train,-1,self.train_file)
                #data_test=np.array(data[end_train:,1:])#.astype(np.float)
                #write_inCSV(data_test,-1,self.test_file)
            #else:
                #print "Train and/or Test file already exist for course ", self.name
        #else:
            #print self.processed_file," not found"

    def flattenAndLoad_traindata(self,lead,lag):
        train_data = flatten_featureset.extract_features_from_sql(self.conn,
                                                                  self.name,
                                                                  self.earliest_date,
                                                                  self.latest_date,
                                                                  self.threshold,
                                                                  self.features,
                                                                  self.weeks,
                                                                  lead,
                                                                  lag,
                                                                  mode='Train')
        self.X_train = train_data[:,1:]
        self.Y_train = train_data[:,0]
        #if os.path.exists(self.train_file):
            #intermediate_file1 = "prediction/datasets_problems/"+self.name+"_week_"+str(lead)+"_lag_"+str(len(lag))+"_train.csv"
            #flatten_featureset.create_features(intermediate_file1, self.train_file, lead, lag)
            #train_data = extractArray_fromCSV(intermediate_file1,True)
            ##os.remove(intermediate_file1)
            #self.X_train = train_data[:,1:] #file format is [label list_of_features]
            #self.Y_train = train_data[:,0]
        #else:
            #print self.train_file,"not found !"
        #print np.shape(self.X_train),self.X_train[1]
    def flattenAndLoad_FM_traindata(self,hist_len, cur_week):
        train_data = flatten_featureset.extract_features_from_sql(self.conn,
                                                                  self.name,
                                                                  self.earliest_date,
                                                                  self.latest_date,
                                                                  self.threshold,
                                                                  self.features,
                                                                  self.weeks,
                                                                  cur_week,
                                                                  hist_len,
                                                                  mode='FM_train')
        self.X_train = train_data[:,1:]
        self.Y_train = train_data[:,0]
        #if os.path.exists(self.train_file):
            #print "start new flatten train data FM"
            #intermediate_file1 = "prediction/data/train.csv"
            #flatten_featureset.create_features_fixedMem(intermediate_file1, self.train_file,hist_len, cur_week)
            #train_data = extractArray_fromCSV(intermediate_file1,True)
            #print "shapes train_data ",np.shape(train_data)
            #os.remove(intermediate_file1)
            #self.X_train = train_data[:,1:] #file format is [label list_of_features]
            #self.Y_train = train_data[:,0]
        #else:
            #print self.train_file,"not found !"
        #print np.shape(self.X_train),self.X_train[1]

    def flattenAndLoad_testdata(self,lead,lag):
        test_data = flatten_featureset.extract_features_from_sql(self.conn,
                                                                  self.name,
                                                                  self.earliest_date,
                                                                  self.latest_date,
                                                                  self.threshold,
                                                                  self.features,
                                                                  self.weeks,
                                                                  lead,
                                                                  lag,
                                                                  mode='Test')
        self.X_train = test_data[:,1:]
        self.Y_train = test_data[:,0]
        #if os.path.exists(self.test_file):
            #intermediate_file1 = "prediction/datasets_problems/"+self.name+"_week_"+str(lead)+"_lag_"+str(len(lag))+"_test.csv"
            #flatten_featureset.create_features(intermediate_file1, self.test_file, lead, lag)
            #test_data = extractArray_fromCSV(intermediate_file1,True)
            ##os.remove(intermediate_file1)
            #self.X_test = test_data[:,1:] #file format is [label list_of_features]
            #self.Y_test = test_data[:,0]
        #else:
            #print self.test_file,"not found !"

    def flattenAndLoad_FM_testdata(self,hist_len, cur_week):
        test_data = flatten_featureset.extract_features_from_sql(self.conn,
                                                                  self.name,
                                                                  self.earliest_date,
                                                                  self.latest_date,
                                                                  self.threshold,
                                                                  self.features,
                                                                  self.weeks,
                                                                  cur_week,
                                                                  hist_len,
                                                                  mode='FM_test')
        self.X_train = test_data[:,1:]
        self.Y_train = test_data[:,0]
        #if os.path.exists(self.test_file):
            #intermediate_file1 = "prediction/data/test.csv"
            #flatten_featureset.create_features_fixedMem_test(intermediate_file1, self.test_file,hist_len, cur_week)
            #test_data = extractArray_fromCSV(intermediate_file1,True)
            #os.remove(intermediate_file1)
            #self.X_test = test_data[:,1:] #file format is [label list_of_features]
            #self.Y_test = test_data[:,0]
        #else:
            #print self.test_file,"not found !"

    #def Initialize(self,threshold):
        #self.annotate_train_test(threshold)


##########################################################################################################################################
##########################################################################################################################################

class PredictionModel:
    def __init__(self):
        self.train_course=''
        self.test_course=''
        self.lead=''
        self.lag=''
        self.X_train=''
        self.Y_train=''
        self.X_test=''
        self.Y_test=''
        self.penal=1
        self.logreg=linear_model.LogisticRegression('l2',dual=False,C=self.penal)
        self.svm=svm.SVC(C=self.penal)

    def flattenAndLoad_train(self,train_course,lead,lag):
        self.train_course=train_course
        train_course.flattenAndLoad_traindata(lead,lag)
        self.X_train=train_course.X_train
        self.Y_train=train_course.Y_train
        self.lead=lead
        self.lag=lag

    def flattenAndLoad_test(self,test_course,lead,lag):
        self.test_course=test_course
        test_course.flattenAndLoad_testdata(lead,lag)
        self.X_test=test_course.X_test
        self.Y_test=test_course.Y_test

    def normalize_features(self):
        X_train_means=sum(self.X_train)/np.shape(self.X_train)[0]
        X_train_stdev=np.amin(self.X_train,axis=0)-np.amax(self.X_train,axis=0)
        X_train_stdev[X_train_stdev==0]=1
        self.X_train=(self.X_train-X_train_means)/X_train_stdev
        self.X_test=(self.X_test-X_train_means)/X_train_stdev

    def add_VarianceFeat(self):
        num_feat=len(self.train_course.features)
        self.X_train=addVarianceAllFeat(self.X_train,self.lag,num_feat)
        self.X_test=addVarianceAllFeat(self.X_test,self.lag,num_feat)

    def add_DerivativeFeat(self):
        num_feat=len(self.train_course.features)
        self.X_train=addAllDerivative(self.X_train,self.lag,num_feat)
        self.X_test=addAllDerivative(self.X_test,self.lag,num_feat)

    def LogReg_train(self):
        self.logreg.fit(self.X_train, self.Y_train)
        predicted_probs = self.logreg.predict_proba(self.X_train)
        desired_label = 0 # want to predict if student will dropout
        fpr, tpr, thresholds = roc_curve(self.Y_train, predicted_probs[:, desired_label],  pos_label=desired_label)
        auc_train = auc(fpr, tpr)
        print "Log reg trained for course",self.train_course.name," with auc on the training set : ",auc_train
        return auc_train

    def SVM_train(self):
        self.svm.fit(self.X_train, self.Y_train)

    def SVM_accuracy(self):
        predictions=self.svm.predict(self.X_train)
        n_samples=np.shape(self.X_test)[0]
        good=0
        for i in range(0,n_samples):
            print self.Y_train[i],predictions[i]
            if self.Y_train[i]==0 and predictions[i]==-1:
                good+=1
            elif self.Y_train[i]==1 and predictions[i]==1:
                good+=1
        acc=good/float(n_samples)
        print "Accuracy on test set = ", acc
        return acc

    def LogReg_test(self):
        predicted_probs = self.logreg.predict_proba(self.X_test)
        desired_label = 0 # want to predict if student will dropout
        fpr, tpr, thresholds = roc_curve(self.Y_test, predicted_probs[:, desired_label],  pos_label=desired_label)
        auc_test = auc(fpr, tpr)
        print "Log reg tested on course",self.test_course.name," with auc on the test set : ",auc_test
        return auc_test

    def LogReg_accuracy(self):
        predictions=self.logreg.predict(self.X_test)
        n_samples=np.shape(self.X_test)[0]
        good=0
        for i in range(0,n_samples):
            print self.Y_test[i],predictions[i]
            if self.Y_test[i]==0 and predictions[i]==-1:
                good+=1
            elif self.Y_test[i]==1 and predictions[i]==1:
                good+=1
        acc=good/float(n_samples)
        print "Accuracy on test set = ", acc
        return acc

    def LogReg_general(self,train_course,test_course):
        num_week=len(train_course.weeks)
        auc=np.zeros((num_week-2,num_week-2))
        for w in range(0,num_week-2):
            for j in range(0,w-1):
                lead=w-j
                lag=j+1
                self.flattenAndLoad_train(train_course,lead,lag)
                self.flattenAndLoad_test(test_course,lead,lag)
                self.normalize_features()
                self.LogReg_train()
                auc_test=self.LogReg_test()
                auc[w-1,lag-1]=auc_test
        self.plot_auc_results(auc,'prediction/data/auc_plot')

    def plot_auc_results(self,auc,out_file):
        AUC_fontsize = 8
        med_fontsize = 12
        fontsize = 18
        n=13
        ax = pl.gca()
        pl.imshow(np.transpose(auc), interpolation='nearest',origin='lower', vmin=0, vmax=1, cmap='RdBu')
        ax.set_xlabel("The predicted week number", fontsize=fontsize)
        ax.set_ylabel("Lag", fontsize=fontsize)
        pl.title('Logistic Regression AUC ', fontsize=fontsize)

        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(range(2,n+2),fontsize=med_fontsize)
        ax.set_yticklabels(range(1,n+1),fontsize=med_fontsize)

        cb = pl.colorbar()
        for t in cb.ax.get_yticklabels():
            t.set_fontsize(med_fontsize)
        pl.show()

##########################################################################################################################################
##########################################################################################################################################

class LogReg_withLearnedPrior:
    def __init__(self):
        self.course_taskA=''
        self.course_taskB=''
        self.XtrainA=''
        self.YtrainA=''
        self.XtrainB=''
        self.YtrainB=''
        self.XtrainB_known=''
        self.YtrainB_known=''
        self.XtrainB_unknown=''
        self.YtrainB_unknown=''
        self.variance_initial_prior=10
        self.coef_transfer=1
        self.n_tasks=10
        self.lead=''
        self.lag=''
        self.weight=''
        self.C=1
        self.band=1
        self.eps=1

    def flattenAndLoad_tasksAB(self,course_taskA,course_taskB,lead,lag,perc_A,seed):


        ##########SOURCE DATA
        self.course_taskA=course_taskA
        course_taskA.flattenAndLoad_traindata(lead,lag)

        #Shuffling Data A :
        course_taskA.X_train,course_taskA.Y_train=shuffle_unison(course_taskA.X_train,course_taskA.Y_train,seed)

        print "Dimension of X_train total",np.shape(course_taskA.X_train)

        max_sampleA=int(perc_A*np.shape(course_taskA.X_train)[0])

        self.XtrainA=course_taskA.X_train[:max_sampleA,:]
        self.YtrainA=np.array([course_taskA.Y_train]).T[:max_sampleA,:]
        self.YtrainA[self.YtrainA==1]=-1
        self.YtrainA[self.YtrainA==0]=1

        ##########TARGET DATA
        self.course_taskB=course_taskB
        course_taskB.flattenAndLoad_traindata(lead,lag)

        #Shuffling Data A :
        course_taskB.X_train,course_taskB.Y_train=shuffle_unison(course_taskB.X_train,course_taskB.Y_train,seed)


        self.XtrainB=course_taskB.X_train
        self.YtrainB=np.array([course_taskB.Y_train]).T
        self.YtrainB[self.YtrainB==1]=-1
        self.YtrainB[self.YtrainB==0]=1

        self.lead=lead
        self.lag=lag

    def flattenAndLoad_FM(self,course_taskA,course_taskB,lead,lag,perc_A,perc_B_known,perc_B_unknown,seed): #lead=history_length lag=current_week
        hist_len=lead
        cur_week=lag

        ##########SOURCE DATA
        self.course_taskA=course_taskA
        course_taskA.flattenAndLoad_FM_traindata(hist_len,cur_week+1)
        #Shuffling Data A :
        course_taskA.X_train,course_taskA.Y_train=shuffle_unison(course_taskA.X_train,course_taskA.Y_train,seed)

        n_A=int(perc_A*np.shape(course_taskA.Y_train)[0])
        self.XtrainA=course_taskA.X_train[:n_A,:]
        self.YtrainA=np.array([course_taskA.Y_train]).T[:n_A,:]
        self.YtrainA[self.YtrainA==1]=-1
        self.YtrainA[self.YtrainA==0]=1


        ######### TARGET KNOWN DATA
        self.course_taskB=course_taskB
        course_taskB.flattenAndLoad_FM_traindata(hist_len,cur_week)
        #Shuffling Data B :
        course_taskB.X_train,course_taskB.Y_train=shuffle_unison(course_taskB.X_train,course_taskB.Y_train,seed)

        n_B_known=int(perc_B_known*np.shape(course_taskB.Y_train)[0])
        self.XtrainB_known=course_taskB.X_train[:n_B_known,:]
        self.YtrainB_known=np.array([course_taskB.Y_train]).T[:n_B_known,:]
        self.YtrainB_known[self.YtrainB==1]=-1
        self.YtrainB_known[self.YtrainB==0]=1


        ######### TARGET UNKNOWN DATA
        self.course_taskB=course_taskB
        course_taskB.flattenAndLoad_FM_testdata(hist_len,cur_week)
        #Shuffling Data B :
        course_taskB.X_train,course_taskB.Y_train=shuffle_unison(course_taskB.X_train,course_taskB.Y_train,seed)

        n_B_unknown=int(perc_B_unknown*np.shape(course_taskB.Y_train)[0])
        self.XtrainB_unknown=course_taskB.X_train[:n_B_unknown,:]
        self.YtrainB_unknown=np.array([course_taskB.Y_train]).T[:n_B_unknown,:]
        self.YtrainB_unknown[self.YtrainB==1]=-1
        self.YtrainB_unknown[self.YtrainB==0]=1

        self.lead=lead
        self.lag=lag

    def normalize_features(self,X_ref):
        X_train_means=sum(X_ref)/np.shape(X_ref)[0]
        X_train_stdev=np.amax(X_ref,axis=0)-np.amin(X_ref,axis=0)
        X_train_stdev[X_train_stdev==0]=1
        self.XtrainA=(self.XtrainA-X_train_means)/X_train_stdev
        self.XtrainB_known=(self.XtrainB_known-X_train_means)/X_train_stdev
        self.XtrainB_unknown=(self.XtrainB_unknown-X_train_means)/X_train_stdev

    def normalize_features_independently(self):
        n_feat=1#np.shape(self.XtrainA)[1]
        X_trainA_means=sum(self.XtrainA)/np.shape(self.XtrainA)[0]
        X_trainA_stdev=n_feat*(np.amax(self.XtrainA,axis=0)-np.amin(self.XtrainA,axis=0))
        X_trainA_stdev[X_trainA_stdev==0]=1
        self.XtrainA=(self.XtrainA-X_trainA_means)/X_trainA_stdev

        X_trainB_means=sum(self.XtrainB_known)/np.shape(self.XtrainB_known)[0]
        X_trainB_stdev=n_feat*(np.amax(self.XtrainB_known,axis=0)-np.amin(self.XtrainB_known,axis=0))
        X_trainB_stdev[X_trainB_stdev==0]=1
        self.XtrainB_known=(self.XtrainB_known-X_trainB_means)/X_trainB_stdev

        X_trainB_means=sum(self.XtrainB_unknown)/np.shape(self.XtrainB_unknown)[0]
        X_trainB_stdev=n_feat*(np.amax(self.XtrainB_unknown,axis=0)-np.amin(self.XtrainB_unknown,axis=0))
        X_trainB_stdev[X_trainB_stdev==0]=1
        self.XtrainB_unknown=(self.XtrainB_unknown-X_trainB_means)/X_trainB_stdev

    def splitTaskBData(self,n_B_known,n_B_unknown):
        self.XtrainB_known=self.XtrainB[:n_B_known,:]
        self.YtrainB_known=self.YtrainB[:n_B_known,:]
        self.XtrainB_unknown=self.XtrainB[n_B_known:n_B_known+n_B_unknown,:]
        self.YtrainB_unknown=self.YtrainB[n_B_known:n_B_known+n_B_unknown,:]

    def training_taskB_known_usingPriorTaskA(self):
        print "training with taskB_known using a gaussian prior based on taskA"
        self.weight=computeWeight_fromPreviousTask(self.XtrainA,self.YtrainA,self.XtrainB_known,self.YtrainB_known,self.variance_initial_prior,self.n_tasks,self.coef_transfer)
        self.weight=np.array([self.weight]).T

    def training_taskB_known(self,e):
        print "training with taskB_known only"
        n_feat=np.shape(self.XtrainB_known)[1]
        u=np.zeros((n_feat+1,1))
        s=self.variance_initial_prior*np.ones((n_feat+1,1))
        self.weight=compute_weight(self.XtrainB_known,self.YtrainB_known,u,s,self.coef_transfer,e)
        self.weight=np.array([self.weight]).T

    def training_taskA(self,e):
        print "training with taskA only"
        n_feat=np.shape(self.XtrainA)[1]
        u=np.zeros((n_feat+1,1))
        s=self.variance_initial_prior*np.ones((n_feat+1,1))
        self.weight=compute_weight(self.XtrainA,self.YtrainA,u,s,self.coef_transfer,e)
        if sum(self.weight) == 0:
            print "training task a weight == 0"
        self.weight=np.array([self.weight]).T

    def training_flat_taskBtaskA(self,e):
        print "training with taskB_known and taskA concatenate "
        n_feat=np.shape(self.XtrainB_known)[1]
        X_train=np.concatenate((self.XtrainB_known,self.XtrainA),axis=0)
        Y_train=np.concatenate((self.YtrainB_known,self.YtrainA),axis=0)
        u=np.zeros((n_feat+1,1))
        s=self.variance_initial_prior*np.ones((n_feat+1,1))
        self.weight=compute_weight(X_train,Y_train,u,s,self.coef_transfer,e)
        self.weight=np.array([self.weight]).T

    def training_multitask_ABknown(self,l_particular,l_common):
        print "training multi class model with taskA and taskB_known"
        self.weight=computeMultiTaskWeights(self.XtrainA,self.XtrainB_known,self.YtrainA,self.YtrainB_known,l_common,l_particular)[2]

    def training_impSampling(self):
        print "training importanceSampling model with taskA and taskB_known"
        eps=0.5
        bandw=1
        B=1.1
        lamb=1
        self.weight=computeWeights_impSampling(self.XtrainA,self.XtrainB_unknown,self.YtrainA,B,eps,bandw,lamb)

    def training_impSampling_withinTaskB(self):
        print "training importanceSampling model by matching taskB known and TaskBunknown"
        eps=0.5
        bandw=1
        B=5
        lamb=1
        self.weight=computeWeights_impSampling(self.XtrainB_known,self.XtrainB_unknown,self.YtrainB_known,B,eps,bandw,lamb)
        #

    def training_logReg_onTaskB(self):
        logreg=linear_model.LogisticRegression(C=self.C)
        logreg.fit(self.XtrainB_unknown, self.YtrainB_unknown)
        #print "inter",logreg.intercept_,np.shape(np.array([logreg.intercept_]))
        #print "inter",np.array(logreg.intercept_),np.shape(np.array(logreg.intercept_))
        self.weight=np.concatenate((np.array([logreg.intercept_]),np.array(logreg.coef_).T),axis=0)
        #print "weights",self.weight,np.shape(self.weight)

    def Accuracy_taskB_unknown(self):#Testing weight on the unknown taskB data
        print "Testing weight on the unknown taskB data"
        print "shapes", np.shape(self.weight), np.shape(self.XtrainB_unknown), np.shape(self.YtrainB_unknown)
        acc=computeBestAccuracy(self.weight,self.XtrainB_unknown,self.YtrainB_unknown)
        print "Accuracy on the unknown taskB data set is ", acc
        return acc

    def Accuracy_naive_taskB_unknown(self):#Testing weight on the unknown taskB data
        acc=compute_Apriori_Accuracy(self.YtrainB_known,self.YtrainB_unknown)
        print "Naive accuracy on the unknown taskB data set is ", acc
        return acc

    def AUC_taskB_unknown(self):
        auc=computeAUC(self.weight,self.XtrainB_unknown,self.YtrainB_unknown)
        print "AUC on the unknown taskB data set is",auc
        return auc

    def AUC_reverse_taskB_unknown(self):
        auc=compute_reverseAUC(self.weight,self.XtrainB_unknown,self.YtrainB_unknown)
        print "AUC reverse on the unknown taskB data set is",auc
        return auc

    def AUC_taskB_known(self):
        auc=computeAUC(self.weight,self.XtrainB_known,self.YtrainB_known)
        print "AUC on the known taskB data set is",auc
        return auc
    def AUC_train(self):
        auc=computeAUC(self.weight,self.XtrainA,self.YtrainA)
        print "AUC on the train data set is",auc
        return auc



#A=np.array([[1],[2],[1]])
#listA=np.array(np.where((A==1)))
#print A[listA[:,1]]

#C=np.concatenate((ext_A,ext_B),axis=0)
#D=np.random.permutation(C)

