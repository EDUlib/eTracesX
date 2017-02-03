'''
Created on April 16, 2014
@author: Colin Taylor

Creates cohorts datasets

Grouping row into (user_id,week) pair
'''
import numpy as np
import time
import csv
from utils import *

################## PARAMETERS #################################################################

def runPreProcessing(name):
	print "Starting preprocessing"
	#name="features_1473xspring"      #  features_1473xspring   features     test
	in_file_prefix ="prediction/data/"+name #"data/test" #"data/features"
	out_file_prefix="prediction/data/"+name+"_processed"

	file_suffix = ".csv"
	in_file = in_file_prefix + file_suffix
	out_file=out_file_prefix + file_suffix

	data = np.genfromtxt(in_file,dtype='string', delimiter = ',', skip_header = 1)#

	print "weeks = ",set(data[:,3])

	################# REFORMATING INTO A NUMPY ARRAY  ###############################################
	weeks,features,data_dict=create_perStudent_dictionnary(data)
	print "weeks =",weeks
	print "features",features
	data_format=create_formatData_fromDict(weeks,features,data_dict)

	################ WRITING IN NEW CSV FILE ###################################################
	write_inCSV(data_format,-1,out_file)
	print "End preproccessing"
	return weeks,features



