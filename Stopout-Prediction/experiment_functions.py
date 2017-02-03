'''
Run experiments
'''
import numpy as np
from classes import *
from utils import *

def initialize_model(course_taskA,course_taskB,n_A,perc_B_known,perc_B_unknown,param1,param2,seed,is_FM):
	t=LogReg_withLearnedPrior()
	if is_FM:
		print "Start FM model"
		n_B_known=perc_B_known
		n_B_unknown=perc_B_unknown
		t.flattenAndLoad_FM(course_taskA,course_taskB,param1,range(param2),n_A,n_B_known,n_B_unknown,seed)
	else:
		predict_w=param1
		range_feat_w=range(param2)
		t.flattenAndLoad_tasksAB(course_taskA,course_taskB,predict_w,range_feat_w,n_A,seed)
		n_B=np.shape(t.XtrainB)[0]
		n_B_known=int(perc_B_known*n_B)
		n_B_unknown=int(perc_B_unknown*n_B)
		t.splitTaskBData(n_B_known,n_B_unknown)
	print "Number1 of training example taskB known",np.shape(t.XtrainB_known)[0]
	t.variance_initial_prior=1
	return t

def AUC_prior(t,coef_trans): # Seems to work
	date=time.time()
	t.coef_transfer=coef_trans
	t.training_taskB_known_usingPriorTaskA()
	auc=t.AUC_taskB_unknown()
	print "Time =",time.time()-date
	return auc

def AUC_B(t,reg): # Seems to work
	date=time.time()
	t.coef_transfer=reg
	t.training_taskB_known()
	auc=t.AUC_taskB_unknown()
	print "Time =",time.time()-date
	return auc

def AUC_B_acc(t,reg): # Seems to work
	date=time.time()
	t.coef_transfer=reg
	t.training_taskB_known()
	accuracy=t.Accuracy_taskB_unknown()
	acc_naive=t.Accuracy_naive_taskB_unknown()
	print "Time =",time.time()-date
	return accuracy,acc_naive

def AUC_train(t,reg,e): # Seems to work
    date=time.time()
    t.coef_transfer=reg
    t.training_taskB_known(e)
    auc=t.AUC_train()
    print "Time =",time.time()-date
    return auc

def AUC_imp(t): # Works poorly for FM but ok for Entire
	date=time.time()
	t.training_impSampling()
	auc=t.AUC_taskB_unknown()
	print "Time =",time.time()-date
	return auc

def AUC_multi(t,l_p,l_c):
	date=time.time()
	t.training_multitask_ABknown(l_p,l_c)
	auc=t.AUC_taskB_unknown()
	print "Time =",time.time()-date
	return auc

def AUC_imp_taskBalone(t): # This doesn't seem to work : only gives AUC =0.5 because w_0=50 and w_1...w_n are close to zero 10^-6
	# INvestigate : features flatenning differences between train and test data for FM / reg param /
	date=time.time()
	t.training_impSampling_withinTaskB()
	auc=t.AUC_taskB_unknown()
	print "Time =",time.time()-date
	return auc

def AUC_naive(t,reg,e): # Works poorly for FM but ok for Entire model
	date=time.time()
	t.coef_transfer=reg
	t.training_taskA(e)
	auc=t.AUC_taskB_unknown()
	print "Time =",time.time()-date
	return auc

def avAUC_seeds(course_taskA,course_taskB,n_A,n_B_known,n_B_unknown,lead,lag,seed_num,AUC_func,is_FM):
	result=list()
	for seed in range(0,seed_num):
		t=initialize_model(course_taskA,course_taskB,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		result.append(AUC_func(t))
	mean=sum(result)/seed_num
	std=np.std(result)
	return mean,std

def find_best_param(t,AUC_func):
	param=0.01
	best_auc=0.4
	best_param=-1
	while param<100:
		auc=AUC_func(t,param)
		if auc>best_auc:
			best_auc=auc
			best_param=param
		param=param*3
	return best_auc,best_param

def find_best_params(t,AUC_func):
	param1=1
	best_auc=0.4
	best_param1=-1
	best_param2=-1
	while param1<1000:
		param2=1
		while param2<1000*param1:
			auc=AUC_func(t,param1,param2)
			if auc>best_auc:
				best_auc=auc
				best_param1=param1
				best_param2=param2
			param2=param2*3
		param1=3*param1
	return best_auc,best_param1,best_param2

def EM(course_a,course_b,course_c,n_A,n_B_known,n_B_unknown,lead,lag,seed_num):
	is_FM=False
	a=course_a
	b=course_b
	c=course_c
	mean=list()
	for seed in range(1,seed_num):
		result=np.zeros((3,6))
		t=initialize_model(a,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,0]=AUC_naive(t,1)
		t=initialize_model(a,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,1]=AUC_imp(t)
		t=initialize_model(a,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,0]=AUC_naive(t,1)
		t=initialize_model(a,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,1]=AUC_imp(t)

		t=initialize_model(b,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,2]=AUC_naive(t,1)
		t=initialize_model(b,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,3]=AUC_imp(t)
		t=initialize_model(b,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,2]=AUC_naive(t,1)
		t=initialize_model(b,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,3]=AUC_imp(t)

		t=initialize_model(c,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,4]=AUC_naive(t,1)
		t=initialize_model(c,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,5]=AUC_imp(t)
		t=initialize_model(c,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,4]=AUC_naive(t,1)
		t=initialize_model(c,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,5]=AUC_imp(t)
		mean.append(result)

	mean_2=sum(mean)/seed_num
	print mean_2

	std=np.zeros((3,6))
	for i in range(0,2):
		for j in range(0,5):
			std[i,j]=np.std([mean[x][i][j] for x in range(0,seed_num)])

	print std

def FM(course_a,course_b,course_c,n_A,n_B_known,n_B_unknown,lead,lag,seed_num):
	is_FM=True
	a=course_a
	b=course_b
	c=course_c
	mean=list()
	for seed in range(0,seed_num):
		result=np.zeros((3,6))
		t=initialize_model(a,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,0]=AUC_naive(t,1)
		t=initialize_model(a,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,1]=AUC_B(t,0.27)
		t=initialize_model(a,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,0]=AUC_naive(t,1)
		t=initialize_model(a,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,1]=AUC_B(t,0.27)

		t=initialize_model(b,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,2]=AUC_naive(t,1)
		t=initialize_model(b,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,3]=AUC_B(t,0.27)
		t=initialize_model(b,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,2]=AUC_naive(t,1)
		t=initialize_model(b,c,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[2,3]=AUC_B(t,0.27)

		t=initialize_model(c,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,4]=AUC_naive(t,1)
		t=initialize_model(c,a,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[0,5]=AUC_B(t,0.27)
		t=initialize_model(c,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,4]=AUC_naive(t,1)
		t=initialize_model(c,b,n_A,n_B_known,n_B_unknown,lead,lag,seed,is_FM)
		t.normalize_features_independently()
		result[1,5]=AUC_B(t,0.27)
		mean.append(result)

	mean_2=sum(mean)/seed_num
	print mean_2

	std=np.zeros((3,6))
	for i in range(0,2):
		for j in range(0,5):
			std[i,j]=np.std([mean[x][i][j] for x in range(0,seed_num)])

	print std

#def HistoryLen_EM

def EH_lead_Naive(a,b,c):
	is_FM=False
	results_final=np.zeros((3,10))
	for hist_len in range(0,10):

		result=list()########### A HELPS B
		for i in range(0,3):
			t=initialize_model(a,a,1000,1000,1000,hist_len+1,5,i,is_FM)
			t.normalize_features(t.XtrainA)
			result.append(AUC_naive(t,1))
			m=sum(result)/float(3)
		results_final[0,hist_len]=m

		result=list()########### A HELPS C
		for i in range(0,3):
			t=initialize_model(b,b,1000,1000,1000,hist_len+1,5,i,is_FM)
			t.normalize_features(t.XtrainA)
			result.append(AUC_naive(t,1))
			m=sum(result)/float(3)
		results_final[1,hist_len]=m

		result=list()########### B HELPS C
		for i in range(0,3):
			t=initialize_model(c,c,1000,1000,1000,hist_len+1,5,i,is_FM)
			t.normalize_features(t.XtrainA)
			result.append(AUC_naive(t,1))
			m=sum(result)/float(3)
		results_final[2,hist_len]=m

	write_inCSV(results_final,range(1,11),'results/self_perf.csv')

	return results_final


def EH_lead_imp(a,b,c):
	is_FM=False
	results_final=np.zeros((3,10))
	for hist_len in range(0,10):

		result=list()########### A HELPS B
		for i in range(0,3):
			t=initialize_model(a,b,1000,1000,1000,hist_len+1,5,i,is_FM)
			t.normalize_features_independently()
			result.append(AUC_imp(t))
			m=sum(result)/float(3)
		results_final[0,hist_len]=m

		result=list()########### A HELPS C
		for i in range(0,3):
			t=initialize_model(a,c,1000,1000,1000,hist_len+1,5,i,is_FM)
			t.normalize_features_independently()
			result.append(AUC_imp(t))
			m=sum(result)/float(3)
		results_final[1,hist_len]=m

		result=list()########### B HELPS C
		for i in range(0,3):
			t=initialize_model(b,c,1000,1000,1000,hist_len+1,5,i,is_FM)
			t.normalize_features_independently()
			result.append(AUC_imp(t))
			m=sum(result)/float(3)
		results_final[2,hist_len]=m

	write_inCSV(results_final,range(1,11),'results/Imp_EH.csv')

	return results_final

def MW_lead_Naive(a,b,c):
	is_FM=True
	results_final=np.zeros((3,1))
	n_seed=6
	result=list()########### A HELPS B
	for i in range(0,n_seed):
		t=initialize_model(a,b,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_naive(t,1))
		m=sum(result)/float(n_seed)
	results_final[0,0]=m

	result=list()########### A HELPS C
	for i in range(0,n_seed):
		t=initialize_model(a,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_naive(t,1))
		m=sum(result)/float(n_seed)
	results_final[1,0]=m

	result=list()########### B HELPS C
	for i in range(0,n_seed):
		t=initialize_model(b,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_naive(t,1))
		m=sum(result)/float(n_seed)
	results_final[2,0]=m

	write_inCSV(results_final,range(1,3),'results/Naive_MW_2.csv')

	return results_final

def MW_insitu(a,b,c):
	is_FM=True
	results_final=np.zeros((3,1))
	n_seed=4
	result=list()########### A HELPS B
	for i in range(0,n_seed):
		t=initialize_model(b,a,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_B(t,1))
		m=sum(result)/float(n_seed)
	results_final[0,0]=m

	result=list()########### A HELPS C
	for i in range(0,n_seed):
		t=initialize_model(b,b,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_B(t,1))
		m=sum(result)/float(n_seed)
	results_final[1,0]=m

	result=list()########### B HELPS C
	for i in range(0,n_seed):
		t=initialize_model(b,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_B(t,1))
		m=sum(result)/float(n_seed)
	results_final[2,0]=m

	write_inCSV(results_final,range(1,3),'results/Insitu_MW_2.csv')

	return results_final



def MW_Prior(a,b,c):
	is_FM=True
	results_final=np.zeros((3,1))
	n_seed=6
	result=list()########### A HELPS B
	for i in range(0,n_seed):
		t=initialize_model(a,b,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_prior(t,1))
		m=sum(result)/float(n_seed)
	results_final[0,0]=m

	result=list()########### A HELPS C
	for i in range(0,n_seed):
		t=initialize_model(a,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_prior(t,1))
		m=sum(result)/float(n_seed)
	results_final[1,0]=m

	result=list()########### B HELPS C
	for i in range(0,n_seed):
		t=initialize_model(b,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_prior(t,1))
		m=sum(result)/float(n_seed)
	results_final[2,0]=m

	write_inCSV(results_final,range(1,3),'results/Prior_MW_2.csv')

	return results_final


def MW_Multi(a,b,c):
	is_FM=True
	results_final=np.zeros((3,1))
	n_seed=6
	result=list()########### A HELPS B
	for i in range(0,n_seed):
		t=initialize_model(a,b,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_multi(t,200,800))
		m=sum(result)/float(n_seed)
	results_final[0,0]=m

	result=list()########### A HELPS C
	for i in range(0,n_seed):
		t=initialize_model(a,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_multi(t,200,800))
		m=sum(result)/float(n_seed)
	results_final[1,0]=m

	result=list()########### B HELPS C
	for i in range(0,n_seed):
		t=initialize_model(b,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_multi(t,200,800))
		m=sum(result)/float(n_seed)
	results_final[2,0]=m

	write_inCSV(results_final,range(1,3),'results/Multi_MW_2.csv')

	return results_final

def MW_imp(a,b,c):
	is_FM=True
	results_final=np.zeros((3,1))
	n_seed=3
	result=list()########### A HELPS B
	for i in range(0,n_seed):
		t=initialize_model(a,b,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_imp(t))
		m=sum(result)/float(n_seed)
	results_final[0,0]=m

	result=list()########### A HELPS C
	for i in range(0,n_seed):
		t=initialize_model(a,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_imp(t))
		m=sum(result)/float(n_seed)
	results_final[1,0]=m

	result=list()########### B HELPS C
	for i in range(0,n_seed):
		t=initialize_model(b,c,1000,1000,1000,2,5,i,is_FM)
		t.normalize_features_independently()
		result.append(AUC_imp(t))
		m=sum(result)/float(n_seed)
	results_final[2,0]=m

	write_inCSV(results_final,range(1,3),'results/imp_MW_2.csv')

	return results_final
