import scripts_runner as sr
import getpass
import datetime
import getopt
import sys
#from DigitalLearnerQuantified.feature_dict import returnAllFeatureSet

def main(dbName=None, userName=None, passwd=None, dbHost=None,
        dbPort=None, startDate=None, currentDate=None,
        scripts_to_run=None, timeout=None, numWeeks=None):
    if not dbHost:
        dbHost = '127.0.0.1'
    if not dbPort:
        dbPort = 3306
    if not dbName:
        dbName = 'XXXXX'
    print "database name: ", dbName
    if not passwd:
        passwd = getpass.getpass()
    if not userName:
        userName = 'root'
    if not startDate:
        startDate='2015-03-16 00:00:00'
    if not currentDate:
        currentDateObject = datetime.datetime.now().date()
        currentDate = currentDateObject.isoformat()
        print "currentDate: ",currentDate
    if not numWeeks:
        numWeeks = 15
    if not scripts_to_run:
        ##3,4,5,14,103,104,105,201,301 depend on collaborations table- not populated yet
        scripts_to_run = [1]
        #[4,14,104,105,201,204,205,206,207,302]
#    if not timeout:
        ##set how long you're willing to wait for a feature (in seconds)
#        timeout = 1800

    sr.runAllScripts(dbName, userName, passwd, dbHost, dbPort, startDate,
            currentDate,numWeeks, scripts_to_run, timeout)
    

if __name__ == "__main__":
    databaseFromDict = None
    database = None
    startdate = None
    enddate = None
    numweeks = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hd:s:n:e:D:",["startdate=","database=","numweeks=","enddate=","databasedict"])
    except getopt.GetoptError:
        print 'main.py -d <database> -s <start date:YYYY-MM-DD> (-e <end date:YYYY-MM-DD>|-n <num weeks>)'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'main.py -d <database> -s <start date:YYYY-MM-DD> (-e <end date:YYYY-MM-DD>|-n <num weeks>)'
            sys.exit()
        elif opt in ("-D", "--databasedict"):
            databaseFromDict = arg
        elif opt in ("-d", "--database"):
            database = arg
        elif opt in ("-s", "--startdate"):
            startdate = arg
        elif opt in ("-e", "--enddate"):
            enddate = arg
        elif opt in ("-n", "--numweeks"):
            numweeks = int(arg)
    
    databaseDict = {
        'ENT-102.3-A2016': {'database':'MOOCdb_ENT_102_3_A2016', 'startdate':'2016-11-14','enddate':'2017-06-19','numweeks':None},
        'IFT-Info-Theo-H2016': {'database':'MOOCdb_IFT_Info_Theo_H2016', 'startdate':'2017-02-26','enddate':'2017-05-28','numweeks':None},

        'OAS.2-P2017': {'database':'MOOCdb_OAS_2_P2017', 'startdate':'2017-02-28','enddate':'2017-07-15','numweeks':None},
        'ENT-103.1-H2017': {'database':'MOOCdb_ENT_103_1_H2017', 'startdate':'2017-03-13','enddate':'2017-06-30','numweeks':None},
        'PRC.3-P2017': {'database':'MOOCdb_PRC_3_P2017', 'startdate':'2017-04-01','enddate':'2017-05-13','numweeks':None}, 
        'TEKPHY2-P2017': {'database':'MOOCdb_TEKPHY2_P2017', 'startdate':'2017-04-05','enddate':'2017-06-18','numweeks':None}, 
        'BRAMS.2-P2017': {'database':'MOOCdb_BRAMS_2_P2017', 'startdate':'2017-04-18','enddate':'2017-06-30','numweeks':None}, 

        'CHE102-P2017': {'database':'MOOCdb_CHE102_P2017', 'startdate':'2017-04-19','enddate':'2017-06-14','numweeks':None}, 
        'SC-102.1-A2015': {'database':'MOOCdb_SC_102_1_A2015', 'startdate':'2017-04-30','enddate':'2017-07-02','numweeks':None}, 
        'CRP.1-A2016': {'database':'MOOCdb_CRP_1_A2016', 'startdate':'2017-05-01','enddate':'2017-06-12','numweeks':None},
#        'GRH-101-A2015': {'database':'MOOCdb_GRH_101_A2015', 'startdate':'2015-11-16','enddate':'','numweeks':None}, # En Tout Temps - A Votre Rythme
#        'GRH-101.1-H2013': {'database':'MOOCdb_GRH_101_1_H2013', 'startdate':'','enddate':'','numweeks':None}, # GRH-101.1???
#        'MKT-101-H2015': {'database':'MOOCdb_MKT_101_H2015', 'startdate':'2015-04-29','enddate':'','numweeks':None}, # En Tout Temps - A Votre Rythme
#        'MKT-101.2-P2014': {'database':'MOOCdb_MKT_101_2_P2014', 'startdate':'','enddate':'','numweeks':None}, # MKT-101.2???
#        'MKT-101.1-H2012': {'database':'MOOCdb_MKT_101_1_H2012', 'startdate':'','enddate':'','numweeks':None}, # MKT-101.1???


        'TEKPHY1-H2017': {'database':'MOOCdb_TEKPHY1_H2017', 'startdate':'2017-02-15','enddate':'2017-04-30','numweeks':None},
        'DDI101.2-H2017': {'database':'MOOCdb_DDI101_2_H2017', 'startdate':'2017-02-01','enddate':'2017-04-01','numweeks':None},

        'MAN-102.1-A2016': {'database':'MOOCdb_MAN_102_1_A2016', 'startdate':'2016-11-14','enddate':'2017-02-20','numweeks':None},
        'MAN-101.1-A2016': {'database':'MOOCdb_MAN_101_1_A2016', 'startdate':'2016-11-14','enddate':'2017-02-20','numweeks':None},
        'CHE101.3-A2016': {'database':'MOOCdb_CHE101_3_A2016', 'startdate':'2016-11-02','enddate':'2017-01-15','numweeks':None},
        'DDI101-A2015': {'database':'MOOCdb_DDI101_A2015', 'startdate':'2016-09-14','enddate':'2016-11-14','numweeks':None},
        'OAS.1-P2016': {'database':'MOOCdb_OAS_1_P2016', 'startdate':'2016-08-08','enddate':'2016-10-25','numweeks':None},

        'ENT-102.2-P2016': {'database':'MOOCdb_ENT_102_2_P2016', 'startdate':'2016-05-16','enddate':'2016-06-30','numweeks':None},
        'COL-101.1-H2016': {'database':'MOOCdb_COL_101_1_H2016', 'startdate':'2016-04-12','enddate':'2016-06-27','numweeks':None},
        'PRC.2-P2016': {'database':'MOOCdb_PRC_2_P2016', 'startdate':'2016-04-04','enddate':'2016-06-11','numweeks':None},
        'CHE101.2-P2016': {'database':'MOOCdb_CHE101_2_P2016', 'startdate':'2016-04-05','enddate':'2016-06-07','numweeks':None},
        'ENT-101.2-H2016': {'database':'MOOCdb_ENT_101_2_H2016', 'startdate':'2016-03-21','enddate':'2016-05-26','numweeks':None},

        'SC101.2-H2015': {'database':'MOOCdb_SC101_2_H2015', 'startdate':'2015-12-14','enddate':'2016-03-21','numweeks':None},
        'CHE101.1-E2015': {'database':'MOOCdb_CHE101_1_E2015', 'startdate':'2015-11-01','enddate':'2016-01-12','numweeks':None},
#        'CHE101.1-P2015': {'database':'MOOCdb_CHE101_1_P2015', 'startdate':'','enddate':'','numweeks':None}, # CHE101???
        'ITES.1-P2015': {'database':'MOOCdb_ITES_1_P2015', 'startdate':'2015-09-13','enddate':'2015-12-15','numweeks':None},
        'PRC.1-P2015': {'database':'MOOCdb_PRC_1_P2015', 'startdate':'2015-10-05','enddate':'2015-12-15','numweeks':None},
        'ENT-102.1-P2015': {'database':'MOOCdb_ENT_102_1_P2015', 'startdate':'2015-05-18','enddate':'2015-07-28','numweeks':None},

        'ITES': {'database':'MOOCdb_ITES', 'startdate':'2015-09-13','enddate':'2015-12-15','numweeks':None},
        'ULB': {'database':'MOOCdb_ULB', 'startdate':'2015-03-16','enddate':None,'numweeks':'15'},
        'TEST-ITES': {'database':'MOOCdb_TEST_ITES', 'startdate':'2015-09-13','enddate':'2015-12-15','numweeks':None},
        'TEST-ULB': {'database':'MOOCdb_TEST_ULB', 'startdate':'2015-03-16','enddate':None,'numweeks':'15'},
        }
    
    if databaseFromDict != None:
        if database != None or startdate != None or enddate != None or numweeks != None or databaseFromDict not in databaseDict.keys():
            print 'Argument ERROR!' 
            print 'main.py -d <database> -s <start date:YYYY-MM-DD> (-e <end date:YYYY-MM-DD>|-n <num weeks>)'
            sys.exit()
        database = databaseDict[databaseFromDict]['database']
        startdate = databaseDict[databaseFromDict]['startdate']
        enddate = databaseDict[databaseFromDict]['enddate']
        numweeks = databaseDict[databaseFromDict]['numweeks']

    if (enddate == None and numweeks == None) or (enddate != None and numweeks != None):
        print 'Argument ERROR!' 
        print 'main.py -d <database> -s <start date:YYYY-MM-DD> (-e <end date:YYYY-MM-DD>|-n <num weeks>)'    
        sys.exit()
    if numweeks == None:
        numweeks = (datetime.datetime.strptime(enddate,'%Y-%m-%d') - datetime.datetime.strptime(startdate,'%Y-%m-%d')).days/7+1
    if numweeks == None or database == None or startdate == None:
        print 'Argument ERROR!' 
        print 'main.py -d <database> -s <start date:YYYY-MM-DD> (-e <end date:YYYY-MM-DD>|-n <num weeks>)'    
        sys.exit()
        
    startdate = str(datetime.datetime.strptime(startdate,'%Y-%m-%d'))
    
    print 'Database Dictionary entry is : ',databaseFromDict
    print 'Database is : ',database
    print 'Start date is : ', startdate
    print 'End date is : ', enddate
    print 'Number of weeks is : ',numweeks

    '''
    ULB: 16 mars 2015 
    ITES: 13 septembre 2015 - 14 semaines
    
    Scripts:
        C1:    initial_preprocessing
        C2:    add_submissions_validity_column
        C3:    problems_populate_problem_week
        C4:    users_populate_user_last_submission_id
        C5:    OBSOLETE: modify_durations
        C6:    curate_submissions
        C7:    curate_observed_events
        C8:    populate_resource_type
        
        P1:    create_longitudinal_features
        P2:    populate_longitudinal_features
        P3:    create_models_table
        P4:    create_experiments_table
        P5:    create_user_longitudinal_feature_values
        P6:    users_populate_dropout_week
        
        1:     dropout
        2:     sum_observed_events_duration
        3:     * number_of_forum_posts
        4:     --- * number_of_wiki_edits
        5:     -L- * average_length_of_forum_posts
        6:     distinct_attempts
        7:     number_of_attempts
        8:     distinct_problems_correct
        9:     average_number_of_attempts
        10:    sum_observed_events_duration_per_correct_problem
        11:    number_problem_attempted_per_correct_problem
        12:    average_time_to_solve_problem
        13:    observed_event_timestamp_variance
        14:    * number_of_collaborations
        15:    max_duration_resources
        16:    --- sum_observed_events_lecture
        17:    --- sum_observed_events_book
        18:    --- sum_observed_events_wiki
        103:   * difference_feature_3
        104:   --- * difference_feature_4
        105:   -L- * difference_feature_5
        109:   difference_feature_9
        110:   difference_feature_10
        111:   difference_feature_11
        112:   difference_feature_12
        201:   * number_of_forum_responses
        202:   percentile_of_average_number_of_attempts
        203:   percent_of_average_number_of_attempts
        204:   --- pset_grade
        205:   --- pset_grade_over_time
        206:   --- lab_grade
        207:   --- lab_grade_over_time
        208:   attempts_correct
        209:   percent_correct_submissions
        210:   --- average_predeadline_submission_time
        301:   * std_hours_working
        302:   --- time_to_react
    '''
    main(dbName            = database,
         userName           = 'root',
         passwd             = '',
#         timeout           = 1800,
         #This date is year-month-day
         startDate         = startdate,
         numWeeks          = numweeks,
         scripts_to_run = [
#        Curation of MOOCdb
             'C1','C2','C3','C4','C6','C7','C8',
#        Preprocess for features extraction
             'P1','P2','P3','P4','P5','P6',
#        Feature extraction without collab
             1,2,6,7,8,9,10,11,12,13,15,16,17,18,109,110,111,112,202,203,204,205,206,207,208,209,210,302,
#        Feature extraction collab
             3,4,5,14,103,104,105,201,301,
             ]

#        List of all scripts ... see description above and in the dictionary
#         scripts_to_run = ['C1','C2','C3','C4','C5','C6','C7','C8']
#         scripts_to_run = ['P1','P2','P3','P4','P5','P6']
#         scripts_to_run = [1,2,6,7,8,9,10,11,12,13,15,16,17,18,109,110,111,112,202,203,204,205,206,207,208,209,210,302]
#         scripts_to_run = [3,4,5,14,103,104,105,201,301]
          
#         features_to_skip =  list(returnAllFeatureSet() - set([13]))
         #orginally we skipped 17, but i'm not sure why. The book resource seems to be populated
         #features_to_skip  = [4,14,104,105,201,204,205,206,207,302] # with collaborations
         #features_to_skip =  [3,4,5,14,17,103,104,105,201,204,205,206,207,301,302] # without collaborations
         #features_to_skip=[1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,103,104,105,109,110,111,112,201,204,205,206,207,208,210,301,302]
         #features_to_skip =  list(set([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,103,104,105,109,110,111,112,201,202,203,204,205,206,207,208,209,210,301,302])-set([13,202,203,208,209,210,301]))
        )
    print "ALL DONE!!!"
