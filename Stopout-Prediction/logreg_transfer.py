'''
Utilitarian functions
Dropout Classification Pipeline
'''

import csv
import sys
import numpy as np
from scipy.optimize import minimize
from sklearn import metrics
from sklearn.metrics import accuracy_score
import mpmath as mp

def compute_weight(X,Y,u,s,coef_transfer,e):
    print "Computing weights"
    b=generate_b(np.shape(X)[1]+1,e)
    func=lambda W: logReg_ObjectiveFunction(X,Y,W,u,s,coef_transfer,b)
    w=np.zeros((np.shape(X)[1]+1,1))
    sol=minimize(func,w)
    return sol.x

def generate_b(d,e):
    res=np.random.randn(d)
    norm=np.random.gamma(d,2/float(e))
    s=sum(res)
    res=res*(norm/s)
    return np.array([res]).T

def logReg_ObjectiveFunction(X,Y,W,u,s,coef_transfer,b):
    w=np.array([W[1:]]).T
    w_0=W[0]
    A=np.dot(X,w)+float(w_0)
    B=-np.multiply(Y,A)
    with mp.workdps(30):
        NLL=sum(log_one_plus_exp(B))+coef_transfer*0.5*GPriorWeightRegTerm(W,u,s)#+(1/float(np.shape(Y)[0]))*np.dot(b.T,np.array([W]).T)[0,0]
    return NLL

def log_one_plus_exp(B):
    #overflow protection
    #very slow, in future figure out a way to do this better with np matrices
    n,m = np.shape(B)
    output = np.zeros((n,m))
    low_val = np.log(1)
    for i,x in enumerate(B):
        if x < -37:
            output[i] = low_val
        elif x > 37:
            output[i] = x
        else:
            output[i] = np.log(1+np.exp(x))
    return output


def GPriorWeightRegTerm(w,u,s):
	result=0
	for i in range(0,np.shape(u)[0]):
		result+=((w[i]-u[i])/s[i])**2
	return result

def estimatePrior(W):#W contains the list of w's computed for several task (row = weights of one task)
	K=np.shape(W)[0] #number of tasks
	u=(1/float(K))*np.sum(W,axis=0)
	W_norm=W-u
	s=np.sqrt((1/float(K-1))*np.sum(np.multiply(W_norm,W_norm),axis=0))
	return u,s  #### WRONG ANSWER ======> TO MODIFY

def separateAndComputeWeight(X,Y,u,s,n_tasks,coef_transfer):
	n_sample=np.shape(X)[0]
	n_sampleTask=int(n_sample/n_tasks)
	W=np.zeros((n_tasks,1+np.shape(X)[1]))
	for i in range(0,n_tasks):
		X_task=X[i*n_sampleTask:(i+1)*n_sampleTask,:]
		Y_task=Y[i*n_sampleTask:(i+1)*n_sampleTask,:]
		W[i,:]=compute_weight(X_task,Y_task,u,s,coef_transfer)
	return W

def computeWeight_fromPreviousTask(X_taskA,Y_taskA,X_taskB,Y_taskB,s_prior_fact,n_tasks,coef_transfer): # Compute weights for X_tasksB using assumed similarity with taskA
	n_feat=np.shape(X_taskA)[1]
	u=np.zeros((n_feat+1,1))
	s=s_prior_fact*np.ones((n_feat+1,1))
	W=separateAndComputeWeight(X_taskA,Y_taskA,u,s,n_tasks,coef_transfer)
	u,s=estimatePrior(W)
	sol=compute_weight(X_taskB,Y_taskB,u,s,coef_transfer)
	return sol

def computeAUC(w,X_test,Y_test):
	w_1=w[1:]
	w_0=w[0]
	pred=sigmoid(np.dot(X_test,w_1)+w_0)
	fpr, tpr, thresholds = metrics.roc_curve(Y_test, pred, pos_label=1)
	return metrics.auc(fpr, tpr)

def computeBestAccuracy(w,X_test,Y_test):
	w_1=w[1:]
	w_0=w[0]
	pred=sigmoid(np.dot(X_test,w_1)+w_0)
	fpr, tpr, thresholds = metrics.roc_curve(Y_test, pred, pos_label=1)

	P=len(Y_test[Y_test==1])
	N=np.shape(Y_test)[0]-P
	print "P=",P,"N=",N
	def acc(P,N,TPR,FPR):
		return (TPR*P+N*(1-FPR))/float(P+N)

	accuracies=[acc(P,N,tpr[i],fpr[i]) for i in range(len(fpr))]
	# print "thresholds[np.argmax(accuracies)]",thresholds[np.argmax(accuracies)]
	return max(accuracies)

def compute_Apriori_Accuracy(Y_train,Y_test):
	print "np.shape(Y_test)",np.shape(Y_test)
	if sum(Y_train)>0.5*np.shape(Y_train)[0]:
		res=len(Y_test[Y_test==1])/float(np.shape(Y_test)[0])
	else:
		res=1-len(Y_test[Y_test==1])/float(np.shape(Y_test)[0])
	return res

def compute_reverseAUC(w,X_test,Y_test):
	w_1=w[1:]
	w_0=w[0]
	pred=1-sigmoid(np.dot(X_test,w_1)+w_0)
	fpr, tpr, thresholds = metrics.roc_curve(Y_test, pred, pos_label=1)
	return metrics.auc(fpr, tpr)

def computeAccuracy(w,X_test,Y_test):
	w_1=w[1:]
	w_0=w[0]
	pred= np.dot(X_test,w_1)+w_0#-np.ones((1,np.shape(X_test)[0])).T#np.dot(X_test,w_1)+w_0#
	print "prediction : ",pred
	print "Number of positive prediction (dp=0)",sum([1 for x in pred if x >0])
	result=[1 for x in np.multiply(pred,Y_test) if x>0]
	acc=sum(result)/float(np.shape(X_test)[0])
	return acc

def sigmoid(x):
	return 1/(1+np.exp(-x))


def computeWeights_multiTask(X_A,X_B,Y_A,Y_B,l_particular,l_common):
	print "Computing weights for multi task"
	func=lambda W: Logreg_multitasks_objFunc(X_A,X_B,Y_A,Y_B,W,l_particular,l_common)
	w=np.zeros((3*(np.shape(X_A)[1]+1),1))
	sol=minimize(func,w)
	return sol.x






# X_taskA=np.array([[1,2,2],[0,1,3],[3,3,0],[0,1,0]])
# Y_taskA=np.array([[1],[-1],[1],[-1]])
# X_taskB=np.array([[1,2,5],[0,1,3]])
# Y_taskB=np.array([[1],[-1]])
# W=np.zeros((np.shape(X_taskB)[1]+1,1))
# W=np.array([[0],[4],[0],[-1]])
# # u=np.zeros((np.shape(X_taskB)[1],1))
# # s=10*np.ones((np.shape(X_taskB)[1],1))


# print computeAccuracy(W,X_taskB,Y_taskB)
