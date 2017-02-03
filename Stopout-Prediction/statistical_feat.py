'''
nov 2014, Seb Boyer
Computing statistical features form basic feature
Scripts used in the classes.py script tp improve prediction process
'''

import csv
import numpy as np

def addVarianceFeat(X,lag,num_feat,feat_column):
	columns=[x*num_feat+feat_column for x in range(0,lag)]
	mean_feat=np.sum(X[:,columns],axis=1)/float(lag)  #computing mean over the weeks for feature feat_column for each students

	X_var=sum(np.square(X[:,columns].T-mean_feat))/lag
	X_var=np.array([X_var]).T

	X_new=np.concatenate((X,X_var),axis=1)
	return X_new

def addVarianceAllFeat(X,lag,num_feat):
	X_new=X
	for feat in range(0,num_feat):
		X_new=addVarianceFeat(X_new,lag,num_feat,feat)
	return X_new

def addDerivative(X,lag,num_feat,feat):
	columns_feat=[x*num_feat+feat for x in range(0,lag)]
	if lag>1:
		X_derivative=X
		for i in range(0,lag-1):
			X_rate=X[:,columns_feat[i+1]]-X[:,columns_feat[i]]
			X_rate=np.array([X_rate]).T
			X_derivative=np.concatenate((X_derivative,X_rate),axis=1)
	return X_derivative

def addAllDerivative(X,lag,num_feat):
	X_new=X
	for feat in range(0,num_feat):
		X_new=addDerivative(X_new,lag,num_feat,feat)
	return X_new


X=np.array([[1,1,2,3,3,4],[2,3,3,6,7,8]])
lag=2
num_feat=3
feat_column=0
#addVarianceFeat(X,lag,num_feat,feat_column)
#print addVarianceAllFeat(X,lag,num_feat)
#print addDerivative(X,lag,num_feat,2)
#print addAllDerivative(X,lag,num_feat)