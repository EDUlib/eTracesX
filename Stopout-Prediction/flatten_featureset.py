'''
Created on March 17, 2013
@author: Colin Taylor

Flatten a multi data point, multi time sequenced dataset with a given lead and lag

Updated to get rid of reliance on csv files in favor of accessing database
directly
5/28/15
Ben Schreck

'''

import csv
import math
import argparse
import numpy as np
import sql_functions as sql
import utils
import sys
#from feature_dict import *
import feature_dict
import pickle as pck
import os.path

def extract_features_from_sql(conn,
                              course_name,
                              earliest_date,
                              latest_date,
                              threshold,
                              feature_ids,
                              all_weeks,
                              predict_w, #for FM_test this is cur_week
                              range_feat_w, #for FM and FM_test this is hist_len
                              mode, #modes are 'Train',Test','FM_train', 'FM_test'
                              fm_lead = 3):  # only matters for FM and FM_test


    print "Features to be extracted=%s" %(feature_ids)

    #date_of_extraction >= '%s'
    # AND
    # date_of_extraction <= '%s'
    # AND


    ###########################  EXTRACT FEATURES ##########################
    feature_dict.lock.acquire()
    if os.path.isfile("features"+course_name+".p"):  # Load saved features
        data=pck.load( open( "features"+course_name+".p", "rb" ) )
    else: # Query and load Features
        get_features = '''
        SELECT user_id,
                longitudinal_feature_week,
                longitudinal_feature_id,
                longitudinal_feature_value
        FROM
        `%s`.user_longitudinal_feature_values
        WHERE
        longitudinal_feature_id in (%s)
        AND
        longitudinal_feature_week in (%s)
        ORDER BY user_id, longitudinal_feature_week, longitudinal_feature_id, longitudinal_feature_value
        ASC
        ''' % (course_name,
               # earliest_date,
               # latest_date,
               utils.convert_list_to_str(list(feature_ids)),
               utils.convert_list_to_str(list(all_weeks)))



        cursor = conn.cursor()
        cursor.execute(get_features)
        data = np.array(cursor.fetchall())
        cursor.close()

        # Save features once for all
        pck.dump(data,open( "features"+course_name+".p", "wb" ) )
    feature_dict.lock.release()

    feature_dict.lock.acquire()
    ###########################  EXTRACT NUMBER OF STUDENTS ##########################
    if os.path.isfile("num_students_"+course_name+".p"):
        num_students=pck.load( open( "num_students_"+course_name+".p", "rb" ) )
    else:
        get_num_students = '''
        select count(*)
        FROM `%s`.users
        WHERE user_dropout_week IS NOT NULL
        ''' % (course_name)


        cursor = conn.cursor()
        cursor.execute(get_num_students)
        num_students = int(cursor.fetchone()[0])
        # Save features once for all
        pck.dump(num_students,open( "num_students_"+course_name+".p", "wb" ) )
    feature_dict.lock.release()


    num_features = len(feature_ids)


    #p == labeling week
    if mode == 'Train' or mode == 'Test':
        p = predict_w
        #elimination week is last accessible week
        #students who already dropped out in this week should be eliminated from
        #consideration
        elimination_w = max(range_feat_w)
        active_weeks = set(range_feat_w)
    else:
        hist_len = range_feat_w
        if mode == 'FM':
            p = hist_len + fm_lead - 1
        else:
            p = predict_w

        #if fm, elimination week is previous week
        elimination_w = p-1
        active_weeks = set(range(p-hist_len-fm_lead+1, p-fm_lead+1))


    #rows are students
    #columns are of format [label, feature1wk1, feature2wk1, ...featurenwkn]
    row_length = 1+(len(active_weeks)*(num_features-1))
    features = np.zeros((num_students, row_length))

    student_index = 0
    current_student = data[0][0]
    feature_row = np.zeros((1,row_length))
    current_student_viable = True
    for row in data:
        student_id, week, feat_id, value = row
        if value:
            value = float(value)
        else:
            value = featureDict[feat_id]['default']

        week = int(week)
        feat_id = int(feat_id)
        if student_id != current_student:
            if current_student_viable:
                #add feature_row to features
                features[student_index,:]=utils.replace_nulls_with_defaults(feature_ids,
                                                                                feature_row)
                pass
            #update to new student
            current_student = student_id
            feature_row = np.zeros((1,row_length))
            current_student_viable = True
            student_index += 1
            if student_index == num_students:
                break


        if current_student_viable:
            if feat_id == 1 and week == p:
                feature_row[0,0] = value
            elif feat_id == 1 and week == elimination_w and value == 0:
                current_student_viable = False
            elif feat_id != 1 and week in active_weeks:
                feature_index = (np.where(feature_ids==feat_id)[0][0])+(week*(num_features-1))
                feature_row[0,feature_index] = value


    #put this above end_train to export features to csv
    #export_features(features, feature_ids, len(active_weeks))

    end_train=int(threshold*np.shape(features)[0]/len(active_weeks))*len(active_weeks)


    if mode == 'Test' or mode == 'FM_test':
        return features[end_train:,:]
    else:
        return features[:end_train,:]


def export_features(features, feature_ids, num_weeks):
    with open('exported_201_features.csv', "wb") as out_csv:#file format is [label list_of_features ]
        csv_writer = csv.writer(out_csv, delimiter= ',')
        ###### WRITE HEADER
        header = ["dropout"]
        week = -1

        for feature_num in range(1, len(features[0,:])):
            feature_id = ((feature_num-1) %(len(feature_ids)-1))+1
            if feature_id == 1:
                week += 1
                week %= num_weeks
            header += ["feature_%s week_%s" % (feature_ids[feature_id], week)]

        csv_writer.writerow(header)
        for row in features:
            csv_writer.writerow(row)

#TESTING, TODO: take out
#from run_scripts.feature_extraction import *
#import getpass
#conn = sql.openSQLConnectionP('201x_2013_spring', 'sebboyer', getpass.getpass())
#train_data = extract_features_from_sql(conn,
                                                              #'201x_2013_spring',
                                                              #'2015-05-28T00:00:00.000000',
                                                              #'2015-05-28T23:59:59.000000',
                                                               #np.array(featuresFromFeaturesToSkip([302])),
                                                               #range(15),
                                                               #5,
                                                               #[0,1,2,3],
                                                               #mode='Train')
#nonzeros = 0
#zeros = 0
#rows = len(train_data)
#cols = len(train_data[0])
#for i in range(rows):
    #for j in range(cols):
        #if train_data[i,j] != 0:
            #nonzeros += 1
        #else:
            #zeros += 1
#print "nonzeros: ", nonzeros
#print "z: ",zeros

#def create_features(out_file, in_file, predict_w, range_feat_w):  #predict_w=lead, range_feat_w=lag   range_feat_w can start at 0
	#out_csv = open(out_file, "wb") #file format is [label list_of_features ]
	## infile format is [features] (includes feature 1, no header)
	#csv_writer = csv.writer(out_csv, delimiter= ',')

	####### EXTRACT DATA
	#data=extractArray_fromCSV(in_file,False)
	#num_weeks =16
	#num_students = len(data) / num_weeks
	#num_feat_weeks=len(range_feat_w)
	#num_cols = (data.shape[1] - 1 ) * num_feat_weeks + 1 #num_feat_weeks = lag

	####### WRITE HEADER
	#header = ["dropout"]
	#for feature_num in range(2, num_cols + 1):
		#header += ["feature_%s" % (feature_num)]
	#csv_writer.writerow(header)

	#count=0
	####### POPULATE FLATTEN DATA FILE
	#for student in range(num_students):
		#stud_data = data[student * num_weeks: (student + 1) * num_weeks] # Gather data for student student
		#predict_week = predict_w #lead+lag-1
		#label = stud_data[predict_week][0] # find the label (to be predicted)
		#last_label = stud_data[max(range_feat_w), 0] #find the last accessible label
		#if last_label == 0: # Eliminate students whose last accessible label was : 0 (=dropout)
			#continue  #if the previous label is 0, don't want to include this student- prediction problem is too easy!
		#write_array = [label] # begin new line by the label to be predicted
		#for active_week in range_feat_w: #add data from accessible week to this new table
			#write_array += stud_data[active_week, 1:].tolist()
		#csv_writer.writerow(write_array) #Copy the student line in the new file


#def create_features_fixedMem(out_file, in_file, hist_len, cur_week):
	#out_csv = open(out_file, "wb") #file format is [label list_of_features ]
	## infile format is [features] (includes feature 1, no header)
	#csv_writer = csv.writer(out_csv, delimiter= ',')

	##data = np.genfromtxt(in_file, delimiter = ',', skip_header = 0)
	#data=extractArray_fromCSV(in_file,False)
	#num_weeks = 16
	#num_students = len(data) / num_weeks
	#num_cols = (data.shape[1] - 1 ) * hist_len + 1

	#header = ["dropout"]
	#for feature_num in range(2, num_cols + 1):
		#header += ["feature_%s" % (feature_num)]
	#csv_writer.writerow(header)


	## Normal version download train data using prediction_week<cur_week and the hist_len previous week
	## print "Uploading training data with p_week=",range(hist_len,cur_week)
	## for student in range(num_students):
	## 	stud_data = data[student * num_weeks: (student + 1) * num_weeks]
	## 	for p in range(hist_len,cur_week):
	## 		predict_week =p # p = lead 1     p+1= lead

	## 		label = stud_data[predict_week][0]
	## 		last_label = stud_data[predict_week -1, 0]# -1 for lead 2
	## 		if last_label == 0:
	## 			continue  #if the previous label is 0, don't want to include this student- prediction problem is too easy!
	## 		write_array = [label]
	## 		for active_week in range(predict_week-hist_len,predict_week): #add data from each lag week  -1 = for lead 2
	## 			write_array += stud_data[active_week, 1:].tolist()
	## 		csv_writer.writerow(write_array)

	## Specific version to predict with lead fixed
	#lead=3
	#print "Uploading training data with p_week=",range(hist_len+lead-1,hist_len+lead)
	#for student in range(num_students):
		#stud_data = data[student * num_weeks: (student + 1) * num_weeks]
		#for p in range(hist_len+lead-1,hist_len+lead):
			#predict_week =p
			#label = stud_data[predict_week][0]
			#last_label = stud_data[predict_week -1, 0]# -1 for lead 2
			#if last_label == 0:
				#continue  #if the previous label is 0, don't want to include this student- prediction problem is too easy!
			#write_array = [label]
			#for active_week in range(predict_week-hist_len-lead+1,predict_week-lead+1): #add data from each lag week  -1 = for lead 2
				#write_array += stud_data[active_week, 1:].tolist()
			#csv_writer.writerow(write_array)


#def create_features_fixedMem_test(out_file, in_file, hist_len, cur_week):
	#out_csv = open(out_file, "wb") #file format is [label list_of_features ]
	## infile format is [features] (includes feature 1, no header)
	#csv_writer = csv.writer(out_csv, delimiter= ',')

	##data = np.genfromtxt(in_file, delimiter = ',', skip_header = 0)
	#data=extractArray_fromCSV(in_file,False)
	#num_weeks = 16
	#num_students = len(data) / num_weeks
	#num_cols = (data.shape[1] - 1 ) * hist_len + 1

	#header = ["dropout"]
	#for feature_num in range(2, num_cols + 1):
		#header += ["feature_%s" % (feature_num)]
	#csv_writer.writerow(header)

	## Normal version download train data using prediction_week<cur_week and the hist_len previous week
	## print "Uploading test data with p_week=",cur_week
	## for student in range(num_students):
	## 	stud_data = data[student * num_weeks: (student + 1) * num_weeks]
	## 	predict_week =cur_week # +1 = for lead 2
	## 	label = stud_data[predict_week][0]
	## 	last_label = stud_data[predict_week-1, 0] # -1 for lead 2
	## 	if last_label == 0:
	## 		continue  #if the previous label is 0, don't want to include this student- prediction problem is too easy!
	## 	write_array = [label]
	## 	for active_week in range(predict_week-hist_len,predict_week): #add data from each lag    -1 for lead 2
	## 		write_array += stud_data[active_week, 1:].tolist()
	## 	csv_writer.writerow(write_array)

	## Specific version to predict with lead fixed
	#print "Uploading test data with p_week=",cur_week
	#lead=3
	#for student in range(num_students):
		#stud_data = data[student * num_weeks: (student + 1) * num_weeks]
		#predict_week =cur_week # +1 = for lead 2
		#label = stud_data[predict_week][0]
		#last_label = stud_data[predict_week-1, 0] # -1 for lead 2
		#if last_label == 0:
			#continue  #if the previous label is 0, don't want to include this student- prediction problem is too easy!
		#write_array = [label]
		#for active_week in range(predict_week-hist_len-lead+1,predict_week-lead+1): #add data from each lag    -1 for lead 2
			#write_array += stud_data[active_week, 1:].tolist()
		#csv_writer.writerow(write_array)

#if __name__ == "__main__":
	#parser = argparse.ArgumentParser(description='Create feature csv with given lead and lag.')
	#parser.add_argument('--in_file',type=str, default="prediction/data/features_forum_and_wiki_train.csv") #  # input csv. No header, no week number.
	#parser.add_argument('--out_file',type=str, default="tmp.csv") # output csv
	#parser.add_argument('--lead',type=int, default=14)  # number of weeks ahead to predict
	#parser.add_argument('--lag',type=int, default=1)  # number of weeks of features to use
	#args = parser.parse_args()

	#create_features(args.out_file, args.in_file, args.lead, args.lag)
