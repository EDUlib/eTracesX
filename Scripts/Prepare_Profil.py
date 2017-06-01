import sys
import getopt
import MySQLdb
import MySQLdb.cursors as cursors

INTERVAL_DELAY = 15 # in second
NEW_SESSION_DELAY = 3600000000 # in second
SESSION_BY_VIDEO = False # Create a new session for each video viewed

type_dict = {'load_video' : 0,
             'pause_video' : 0,
             'play_video' : 0,
             'seek_back_video' : 0,
             'seek_forward_video' : 0,
             'seek_video' : 0,
             'speed_change_video' : 0,
             'stop_video' : 0,             
            }

def print_header(outputFile):
    outputFile.write('ID|Lo|Pa|Pl|Sb|Sf|Se|Sp|St\n')
    
def print_profile(cur_user, outputfile):
    if (type_dict['load_video'] == 0 and
        type_dict['pause_video'] == 0 and
        type_dict['play_video'] == 0 and
        type_dict['seek_back_video'] == 0 and
        type_dict['seek_forward_video'] == 0 and
        type_dict['seek_video'] == 0 and
        type_dict['speed_change_video'] == 0 and
        type_dict['stop_video'] == 0):
        return
    cur_line = cur_user + '|' +\
            str(type_dict['load_video']) + '|' +\
            str(type_dict['pause_video']) + '|' +\
            str(type_dict['play_video']) + '|' +\
            str(type_dict['seek_back_video']) + '|' +\
            str(type_dict['seek_forward_video']) + '|' +\
            str(type_dict['seek_video']) + '|' +\
            str(type_dict['speed_change_video']) + '|' +\
            str(type_dict['stop_video']) + '\n'            
    outputfile.write(cur_line)
    type_dict['load_video'] = 0
    type_dict['pause_video'] = 0
    type_dict['play_video'] = 0
    type_dict['seek_back_video'] = 0
    type_dict['seek_forward_video'] = 0
    type_dict['seek_video'] = 0
    type_dict['speed_change_video'] = 0
    type_dict['stop_video'] = 0
    
def print_help():
    print 'test.py -d <databaseName> -o <outputFile> [-i <timeInterval> -s <sessionDelay> -v]'
    print "v: create a sequence for each video"
    print "Default values i:15 s:3600000000 v:F"

if __name__ == "__main__":
    mooc_db = ''
    outputFileName = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hd:i:o:s:v",["database=","output=","interval=","session-delay=","video-split"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-d", "--database"):
            mooc_db = arg
        elif opt in ("-i", "--interval"):
            INTERVAL_DELAY = int(arg)
        elif opt in ("-o", "--output"):
            outputFileName = arg
        elif opt in ("-s", "--session-delay"):
            NEW_SESSION_DELAY = int(arg)
        elif opt in ("-v", "--video-split"):
            SESSION_BY_VIDEO = True
    if mooc_db == '':
        print_help()
        sys.exit(2)

    if outputFileName == '':
        outputFileName = 'PROF_' + mooc_db + '_i' + str(INTERVAL_DELAY) + '_s' + str(NEW_SESSION_DELAY) +\
                        '_v' + str(SESSION_BY_VIDEO)[0] + '.txt'

    outputFile = open(outputFileName, 'w')
    
    conn = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='', db=mooc_db, cursorclass=cursors.SSCursor)
    cursor = conn.cursor()
#    cursor.execute("SELECT DISTINCT(user_id) FROM observed_events")
    cursor.execute("SELECT user_id,observed_event_timestamp,observed_event_duration, observed_event_type_id, url_id " +
                    "FROM observed_events " +
                    "WHERE observed_event_type_id IN ('stop_video','speed_change_video','seek_video','seek_forward_video','seek_back_video','play_video','pause_video','load_video') " + 
                    "ORDER BY user_id,observed_event_timestamp")
    cur_user = ''
    cur_seq = []
    prev_ts = ''
    prev_video = -1
    print_header(outputFile)
    for user_id, event_ts, event_dur, event_type, cur_video in cursor.fetchall():
        if cur_user == '':
            cur_user = user_id
            cur_seq = []
            prev_ts = event_ts
            prev_video = cur_video
        if cur_user != user_id:
            print_profile(cur_user, outputFile)
            cur_seq = []
            cur_user = user_id
            prev_ts = event_ts
            prev_video = cur_video
        if (int((event_ts - prev_ts).total_seconds()) > NEW_SESSION_DELAY):
            print_profile(cur_user, outputFile)
            cur_seq = []
            cur_user = user_id
            prev_ts = event_ts
            prev_video = cur_video
        if prev_video != cur_video and SESSION_BY_VIDEO: # TODO... 
            print_profile(cur_user, outputFile)
            cur_seq = []
            cur_user = user_id
            prev_ts = event_ts
            prev_video = cur_video
        prev_ts = event_ts
        prev_video = cur_video
        nb_to_add = event_dur//INTERVAL_DELAY
        type_dict[event_type] += nb_to_add
    print_profile(cur_user, outputFile)
        
    cursor.close()
    conn.close()
    outputFile.close()
#    print 'DONE!'
