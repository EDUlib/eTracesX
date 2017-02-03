'''
Utilitarian functions
Dropout Classification Pipeline
'''

import csv
import numpy as np
from scipy.optimize import minimize,show_options
from sklearn import metrics

def Loss_logreg(X,Y,theta): # X, Y and theta must be np.array
	theta_0=theta[0]
	p=np.dot(X,theta[1:,:])#+theta_0
	q=-np.multiply(Y,p)
	return sum(np.log(1+np.exp(q)))

def SeparateTheta(Theta):
	n=np.shape(Theta)[0]
	return Theta[:n/3,:],Theta[n/3:2*n/3,:],Theta[2*n/3:,:]

def concatenate(w_A,w_B,w_C):
	return np.concatenate((np.concatenate((w_A,w_B),axis=0),w_C),axis=0)

def ObjFunc_multiTask(X_A,X_B,Y_A,Y_B,Theta,l_common,l_separate):
	Theta=np.array([Theta]).T
	Theta_opt=Theta
	v_A,v_B,w_common=SeparateTheta(Theta)
	w_A=v_A+w_common
	w_B=v_B+w_common
	NLL=Loss_logreg(X_A,Y_A,w_A)+Loss_logreg(X_B,Y_B,w_B)+l_common*np.dot(w_common.T,w_common)+l_separate*(np.dot(v_A.T,v_A)+np.dot(v_B.T,v_B))
	print "iteration :",NLL
	return NLL

def computeMultiTaskWeights(X_A,X_B,Y_A,Y_B,l_common,l_separate):
	n=np.shape(X_A)[1]
	Theta_0=np.zeros((3*(n+1),1))
	func=lambda Theta: ObjFunc_multiTask(X_A,X_B,Y_A,Y_B,Theta,l_common,l_separate)
	sol=minimize(func,Theta_0,method='CG',tol=1)
	Theta_opt=np.array([sol.x]).T
	return SeparateTheta(Theta_opt)

#X_A=np.array([[1,2],[3,4]])
#Y_A=np.array([[1],[-1]])
#X_B=np.array([[1,2],[3,4]])
#Y_B=np.array([[1],[-1]])
#theta=np.array([[1],[0],[1],[1],[0],[1],[1],[0],[1]])
#l_common=1
#l_separate=1
#print computeMultiTaskWeights(X_A,X_B,Y_A,Y_B,l_common,l_separate)