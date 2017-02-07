import time
from sql_functions import *
#list of features:
from scripts_dict import *

def extractFeature(dbName, userName, passwd, host, port, startDate, currentDate, numWeeks,
                    featureID, timeout):
    begin = time.time()
    if featureID not in scriptsDict:
        print "unsupported feature"
        return False
    feature = scriptsDict[featureID]
    dirName = feature['dirname']
    isSQL = (feature['extension'] == '.sql')
    print "extracting feature %s: %s" % (featureID, feature["name"])
    if isSQL:
        conn = openSQLConnectionP(dbName, userName, passwd, host, port)
        featureFile = dirName+'/'+feature['filename']+feature['extension']
        this_file = os.path.dirname(os.path.realpath(__file__))
        featureFile = this_file+'/'+featureFile
        toBeReplaced = ['moocdb', 'START_DATE_PLACEHOLDER',
                'CURRENT_DATE_PLACEHOLDER', 'NUM_WEEKS_PLACEHOLDER']
        toReplace = [dbName, startDate, currentDate, str(numWeeks)]
        success = runSQLFile(conn, featureFile, dbName, toBeReplaced,
                toReplace, timeout)
        closeSQLConnection(conn)
    else:
        conn = openSQLConnectionP(dbName, userName, passwd, host, port)
        conn2 = openSQLConnectionP(dbName, userName, passwd, host, port)
        featureFile = dirName+'/'+feature['filename']
        success = runPythonFile(conn, conn2, dirName, feature['filename'],
                dbName, startDate, currentDate, numWeeks, timeout)
        closeSQLConnection(conn)
        closeSQLConnection(conn2)
    end = time.time()
    print "Elapsed time = ", end-begin
    if not success:
        print "feature ", feature['name'], "failed"
        return False
    else:
        return True

def runAllScripts(dbName, userName, passwd, host, port, startDate,
                        currentDate,numWeeks, scripts_to_run, timeout):
    pass
    for script in scripts_to_run:
        success = extractFeature(dbName, userName, passwd, host, port, startDate,
                                currentDate, numWeeks, script, timeout)
        if not success:
            cont = ""
            while not (cont == "y" or cont == "n"):
                cont = raw_input("Continue with rest of feature extraction? (y/n)")
            if cont == "n":
                break


