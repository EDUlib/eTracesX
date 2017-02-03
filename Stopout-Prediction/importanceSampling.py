'''
Utilitarian functions
Dropout Classification Pipeline
'''

import csv
import numpy as np
from cvxopt import matrix, normal, spdiag, misc, lapack,solvers
from scipy.optimize import minimize,show_options
from plotBoundary import *



q = matrix([3.0,2.0])
P = matrix([ [1.0, 2.0], [3.0, 4.0] ])
G = matrix([ [1.0, 0.0], [3.0, 1.0] ])
h = matrix([0.0,2.0])
A = matrix([ [1.0, 1.0], [2.0, 1.0] ])
b = matrix([0.0,1.0])

#print solvers.qp(P, q, G, h,A,b)['x']
def KernelFunc_Gaussian(x_1,x_2,bandw):
	diff=x_1-x_2
	return np.exp(-np.dot(diff.T,diff)/bandw**2)

def GaussianKernelSubMatrix(X_s,X_t,bandw):
	n1=np.shape(X_s)[0]
	n2=np.shape(X_t)[0]
	K=np.zeros((n1,n2))
	for i in range(0,n1):
		for j in range(0,n2):
			K[i,j]=KernelFunc_Gaussian(X_s[i,:].T,X_t[j,:],bandw)
	return K

def GaussianKernelMatrix(X_s,X_t,bandw):
	K_1=GaussianKernelSubMatrix(X_s,X_s,bandw)
	K_2=GaussianKernelSubMatrix(X_t,X_t,bandw)
	K_12=GaussianKernelSubMatrix(X_s,X_t,bandw)
	K_sup=np.concatenate((K_1,K_12),axis=1)
	K_inf=np.concatenate((K_12,K_2),axis=1)
	K=np.concatenate((K_sup,K_inf),axis=0)
	return K

def KappaVector(K_st,n_s,n_t): #Each S data must be on a single LINE of K_st
	k=np.zeros((1,n_s))
	for i in range(0,n_s):
		k[0,i]=(n_s/float(n_t))*sum(K_st[i,:])
	return k.T

def findOptimalBeta(X_s,X_t,B,bandw,eps): 
	n_s=np.shape(X_s)[0]
	n_t=np.shape(X_t)[0]
	K=GaussianKernelSubMatrix(X_s,X_s,bandw)
	k=KappaVector(GaussianKernelSubMatrix(X_s,X_t,bandw),n_s,n_t)
	#print"k",k
	G=-np.identity(n_s)
	h=np.zeros((n_s,1))
	G=np.concatenate((G,np.identity(n_s)),axis=0)
	h=np.concatenate((h,B*np.ones((n_s,1))),axis=0)
	G=np.concatenate((G,np.ones((1,n_s))),axis=0)
	h=np.concatenate((h,n_s*np.array([[1+eps]])),axis=0)
	G=np.concatenate((G,-np.ones((1,n_s))),axis=0)
	h=np.concatenate((h,n_s*np.array([[eps-1]])),axis=0)
	K=matrix(K)
	k=-matrix(k) # k:= -k 
	G=matrix(G)
	h=matrix(h)
	sol=solvers.qp(K, k, G, h)#Solve the QP min 1/2 xKx +p.T x s.t. Gx=<h
	return np.array(sol['x'])

def Loss_logreg_BetaPonderation(X_s,Y_s,theta,beta,lamb): # X, Y and theta must be np.array
    theta=np.array([theta]).T
    theta_0=theta[0]
    p=np.dot(X_s,theta[1:,:])+theta_0
    q=-np.multiply(Y_s,p)
    cost=np.multiply(beta,np.log(1+np.exp(q)))
    reg=lamb*np.dot(theta[1:,:].T,theta[1:,:])
    #print "iteration",sum(cost)+reg 
    return sum(cost)+reg

def computeWeights_impSampling(X_s,X_t,Y_s,B,eps,bandw,lamb):
    beta=findOptimalBeta(X_s,X_t,B,bandw,eps)
    print "Finding optimal beta coef to match matrices of size",np.shape(X_s)," and ",np.shape(X_t)," found ."
    Theta_0=np.zeros((np.shape(X_s)[1]+1,1))
    func=lambda theta: Loss_logreg_BetaPonderation(X_s,Y_s,theta,beta,lamb)
    sol=minimize(func,Theta_0,tol=0.1)
    Theta_opt=np.array([sol.x]).T
    #print "weights opt",Theta_opt
    return Theta_opt

def predict(x,theta):
	x=np.array([x])
	#print x, theta[1:,:]
	if theta[0]+np.dot(x,theta[1:,:])>0:
		return 1
	else:
		return -1



X_s=np.array([ [1.0, 2.0], [3.0, 4.0] , [2.5, 6.0],[1.1, 1.9], [3.1, 4.1] ])
Y_s=np.array([[1],[-1],[1],[1],[-1]])
X_t=np.array([ [1.1, 2.1], [3.3, 4.2] ])

bandw=5
n_s=2
n_t=2
B=2
eps=0.01
lamb=1
#theta_opt=computeWeights_impSampling(X_s,X_t,Y_s,B,eps,bandw,lamb)
#scoreFn=lambda x: predict(x,theta_opt)
#values=[-1,1]
#plotDecisionBoundary(X_s, Y_s, scoreFn, values, title = "")
#pl.show()






