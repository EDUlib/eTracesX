'''
Main function of tranfer learning METHODS
date : 05/07/2015
author : Sebastien Boyer

Function:
- run_dropout_prediction(trainingCourse,testingCourse,pred_week,feat_week,epsilon,lamb=1)

'''

##########################################################################################
###############################        Importation      ##################################
##########################################################################################

from classes import *
from experiment_functions import *

import sql_functions as sql



##########################################################################################
###############################  Parameters requirements #################################
##########################################################################################

##############################  Course names from those contain in the data folder
# trainingCourse : name of course to train the model on
# testingCourse  : name of course to test the model on
##############################  Problem specification
# pred_week : the week's id to predict on (should be contained in the week's id of both courses)
# feat_week : list of week's ids to predict from (should be contained in the week's id of both courses)
# epsilon  : the privacy parameter (between 0 (maximum protection) and 0.5 (no protection))
# lamb : the ridge regularization parameter (optional)





##########################################################################################
###############################        Main function     #################################
##########################################################################################

def run_dropout_prediction(userName,
                           passwd, host, port,
                           trainingCourse,
                           testingCourse,
                           earliest_date,
                           latest_date,
                           features,
                           weeks,
                           pred_week,
                           feat_week,
                           epsilon,
                           lamb=1):
    conn = sql.openSQLConnectionP(trainingCourse, userName, passwd, host, port)

    ############## Download course data and split into train and test sets  ######################
    training_course_threshold = 0.6
    a=Course(trainingCourse, earliest_date, latest_date, features, weeks,
            training_course_threshold, conn)

    testing_course_threshold = 0.6
    b=Course(testingCourse,  earliest_date, latest_date, features, weeks,
            testing_course_threshold, conn)

    ############## Set parameters #################################################################
    n_A=2000 # Number of samples from source domain (course)
    n_B_known=0.6 # Percentage of sample used from target domain available
    n_B_unknown=0.4  # Percentage of sample used from target domain available
    is_FM=False
    seed=1 # set up the randomization seed

    ############# Initialize model #################################################################
    model=initialize_model(a,b,n_A,n_B_known,n_B_unknown,pred_week,feat_week,seed,is_FM)
    model.normalize_features_independently()



    ############# Test model performance ###########################################################
    auc_test=AUC_naive(model,lamb,epsilon)
    auc_train = AUC_train(model,lamb, epsilon)

    conn.close()
    return (auc_test,auc_train,model.weight)



##########################################################################################
###############################        Example     ######################################
##########################################################################################

#training_course="201x_2013_spring"
#testing_course="201x_2013_spring"
#pred_week=5
#feat_week=3
#epsilon=1

##earliest_date is the earliest time the features were extracted
#earliest_date =
##latest_date is the latest time the features were extracted
#latest_date =

#features = [1,2,3,4,5,6,7,8,9,10,201]
#weeks = range(16)
#run_dropout_prediction(username, passwd,training_course,testing_course,earliest_date,latest_date, features, weeks, pred_week,feat_week,epsilon,lamb=1)
