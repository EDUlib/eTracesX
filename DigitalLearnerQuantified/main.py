import scripts_runner as sr
import getpass
import datetime
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
    '''
    ULB: 16 mars 2015 
    
    Scripts:
        C1:    initial_preprocessing
        C2:    add_submissions_validity_column
        C3:    problems_populate_problem_week
        C4:    users_populate_user_last_submission_id
        C5:    modify_durations
        C6:    curate_submissions
        C7:    curate_observed_events
        C8:    --- populate_resource_type
        
        P1:    create_longitudinal_features
        P2:    --- populate_longitudinal_features
        P3:    create_models_table
        P4:    create_experiments_table
        P5:    create_user_longitudinal_feature_values
        P6:    users_populate_dropout_week
        
        1:     dropout
        2:     sum_observed_events_duration
        3:     * number_of_forum_posts
        4:     * number_of_wiki_edits
        5:     * average_length_of_forum_posts
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
        16:    sum_observed_events_lecture
        17:    sum_observed_events_book
        18:    sum_observed_events_wiki
        103:   * difference_feature_3
        104:   * difference_feature_4
        105:   * difference_feature_5
        109:   difference_feature_9
        110:   difference_feature_10
        111:   difference_feature_11
        112:   difference_feature_12
        201:   * number_of_forum_responses
        202:   percentile_of_average_number_of_attempts
        203:   percent_of_average_number_of_attempts
        204:   pset_grade
        205:   pset_grade_over_time
        206:   lab_grade
        207:   lab_grade_over_time
        208:   attempts_correct
        209:   percent_correct_submissions
        210:   average_predeadline_submission_time
        301:   * std_hours_working
        302:   --- time_to_react
    '''
    main(dbName            = 'MOOCdb_TEST_ULB',
         userName           = 'root',
         passwd             = '',
#         timeout           = 1800,
         #This date is year-month-day
         startDate         = '2015-03-16 00:00:00',
         numWeeks          = 15,
#        Curation of MOOCdb
         scripts_to_run = ['C1','C2','C3','C4','C5','C6','C7']
#        Preprocess for features extraction
#         scripts_to_run = ['P1','P3','P4','P5','P6']
#        Feature extraction without collab
#         scripts_to_run = [1,2,6,7,8,9,10,11,12,13,15,16,17,18,109,110,111,112,202,203,204,205,206,207,208,209,210]
#        Feature extraction collab
#         scripts_to_run = [3,4,5,14,103,104,105,201,301]

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
