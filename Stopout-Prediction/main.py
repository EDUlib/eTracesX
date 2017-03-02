#utilities
import feature_dict
import getpass
import datetime
import multiprocessing as mp

#predict
import predictor as predictor

#record
import record_experiments as record

def main(dbName=None, userName=None, passwd=None, dbHost=None,
        dbPort=None,training_course=None, testing_course=None,
        earliest_date=None,latest_date_object=None,features_to_skip=None,
        pred_week=None,feat_week=None, num_weeks=None,epsilon=None,lamb=None):
    if not dbHost:
        dbHost = '127.0.0.1'
    if not dbPort:
        dbPort = 3306
    if not userName:
        userName='root'
    if not passwd:
        passwd = getpass.getpass()
    if not dbName:
        dbName = 'MOOCdb_TEST_ULB'
    if not latest_date_object:
        latest_date_object = datetime.datetime.now()
    latest_date = latest_date_object.isoformat()
    if not earliest_date:
        #in seconds:
        dateSlack = 14400 # 2 hours between currentDate and when feature extraction started
        earliest_date = (latest_date_object - datetime.timedelta(seconds=dateSlack)).isoformat()
    if not training_course:
        training_course=dbName
    if not testing_course:
        testing_course=dbName

    if not features_to_skip:
        features_to_skip = [3,4,5,14, 103,104,105, 201, 301, 302]
    features = feature_dict.featuresFromFeaturesToSkip(features_to_skip)

    if not num_weeks:
        #try with 15,16,17
        num_weeks = 15
    weeks = range(num_weeks)

    if not pred_week:
        pred_week=5
    if not feat_week:
        feat_week=3

    if not epsilon:
        epsilon=1
    if not lamb:
        lamb = 1

    #TODO: make sure defaults are correct in feature_dict
    auc_test, auc_train, weights=predictor.run_dropout_prediction(userName,
                                                        passwd, dbHost, dbPort,
                                                        training_course,
                                                        testing_course,
                                                        earliest_date,
                                                        latest_date_object,
                                                        features,
                                                        weeks,
                                                        pred_week,
                                                        feat_week,
                                                        epsilon,
                                                        lamb=lamb)
    print "done"

    feature_dict.lock.acquire()
    #save experiment and model
    print "Saving run"
    exp_id = record.record_experiment(dbName, userName, passwd, dbHost, dbPort, pred_week, feat_week,
           auc_train, testing_course, auc_test, lamb, epsilon, latest_date)

    record.record_model(dbName, userName, passwd, dbHost, dbPort, features, weights, exp_id)
    feature_dict.lock.release()
    print "done"

def initLock(l):
#    global lock
    feature_dict.lock = l

def parallelize():
    l = mp.Lock()
    ncores = mp.cpu_count()
    pool = mp.Pool(processes=ncores, initializer = initLock, initargs=(l,))
    return pool, ncores

def runSpecificLag(course_db_name, features_to_skip, lag, passwd):#course_db_name, features_to_skip, lag):
    for lead in xrange(lag+1, 14):
        main(dbName = course_db_name,
                features_to_skip = features_to_skip,
                earliest_date='2015-03-16T00:00:00',
                latest_date_object=datetime.datetime.now(),
                num_weeks = 14,
                pred_week = lead,
                feat_week = lag,
                passwd = passwd)

def runAllProblemsPerCourse(course_db_name, features_to_skip):
    pool, ncores = parallelize()
    passwd = getpass.getpass()
    funclist = []
    for lag in xrange(13):
        f = pool.apply_async(runSpecificLag, [course_db_name, features_to_skip, lag, passwd])
        funclist.append(f)
    [f.get() for f in funclist]


if __name__ == "__main__":
    runAllProblemsPerCourse('MOOCdb_TEST_ULB',
                features_to_skip = list(feature_dict.returnAllFeatureSet() - set([1,2,6,7,8,9])))                                             
#                features_to_skip = [3,4,5,14,103,104,105,201,204,205,206,207,301]) #MIT without collab
                #features_to_skip = [  4,  14,    104,105,201,204,205,206,207,   302,17]) #MIT with collab

# Features:
#    Obligatoire: 1
#    Without Collab
#        OK: 2, 6, 7, 8, 9, 10, 11, 12, 13, 15, 109, 110, 111, 112, 202, 203, 208, 209
#        KO: 16, 17, 18, 210, 302
#    With Collab
#        OK: 3, 5(L), 14, 103, 105(L), 201, 301
#        KO: 4, 104, 204, 205, 206, 207

    #run everything except 3091 2013 spring
