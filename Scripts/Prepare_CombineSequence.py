import sys
import getopt
import MySQLdb
import MySQLdb.cursors as cursors

SEQ_TIME_LEN = 300
SEQ_CLIC_LEN = 100
INTERVAL_DELAY = 5 # in second
DROP_TRUNCATE_SEQ = False
KEEP_ALL = False
SEQ_COUNT = 0

type_dict = {'stop_video' : 'St',
             'speed_change_video' : 'Sp',
             'seek_video' : 'Se',
             'play_video' : 'Pl',
             'pause_video' : 'Pa',
             'load_video' : 'Lo'             
            }

type_val_dict = {'St' : '5',
                 'Sp' : '4',
                 'Se' : '3',
                 'Pl' : '2',
                 'Pa' : '1',
                 'Lo' : '0'             
                 }

user_vid_count_dict = {}

def print_header(outputFile):
    # SID|UID|VID|VIS|TS|C001...CXXX|D001...DXXX|T001...TYYY
    header = 'SID|UID|VID|VIS|TS'
    for i in range(1,SEQ_CLIC_LEN+1):
        header += '|C' + format(i, '03')
    for i in range(1,SEQ_CLIC_LEN+1):
        header += '|D' + format(i, '03')
    for i in range(1,SEQ_TIME_LEN+1):
        header += '|T' + format(i, '03')
    header += '\n'
    outputFile.write(header)

def print_sequence(cur_user, cur_vid, time_stamp, cur_clic_seq, cur_dur_seq, cur_time_seq, outputFile):
    global SEQ_COUNT
    if len(cur_clic_seq) <= 0:
        return
    SEQ_COUNT += 1
    print str(len(cur_clic_seq)) + " : " + str(len(cur_time_seq)) + " : S" + format(SEQ_COUNT,'06') + " : " + cur_user
    if (len(cur_clic_seq) > SEQ_CLIC_LEN or len(cur_time_seq) > SEQ_TIME_LEN) and DROP_TRUNCATE_SEQ:
        return
#    if cur_clic_seq.count('Lo') == len(cur_clic_seq):  # len(cur_clic_seq) == 1 and cur_clic_seq[0] == 'Lo':
#        return
    cur_line = 'S' + format(SEQ_COUNT,'06') + '|' + cur_user + '|' + str(cur_vid) + '|' + format(user_vid_count_dict[cur_user + str(cur_vid)], '03') + '|' + str(time_stamp)
    count = len(cur_clic_seq);
    if count > SEQ_CLIC_LEN:
        count = SEQ_CLIC_LEN
    for i in range(0, count):
#        cur_line += '|' + cur_clic_seq[i]
        cur_line += '|' + type_val_dict[cur_clic_seq[i]]
    for i in range(count,SEQ_CLIC_LEN):    
        cur_line += '|NA'
    count = len(cur_dur_seq);
    if count > SEQ_CLIC_LEN:
        count = SEQ_CLIC_LEN
    for i in range(0, count):
        cur_line += '|' + format(cur_dur_seq[i], '04')
    for i in range(count,SEQ_CLIC_LEN):    
        cur_line += '|NA'
    count = len(cur_time_seq);
    if count > SEQ_TIME_LEN:
        count = SEQ_TIME_LEN
    for i in range(0, count):
#        cur_line += '|' + cur_time_seq[i]
        cur_line += '|' + type_val_dict[cur_time_seq[i]]
    for i in range(count,SEQ_TIME_LEN):    
        cur_line += '|NA'
    cur_line += '\n'
    outputFile.write(cur_line)

def print_help():
    print 'test.py -d <databaseName> -o <outputFile> [-a -D -i <timeInterval> -C <ClicSeqLength> -T <TimeSeqLength>]'
    print "a: keep all events in time sequence"
    print "D: drop/omit truncated sequence"
    print "Default values a:F D:F i:5 C:100 T:300"

if __name__ == "__main__":
    mooc_db = ''
    outputFileName = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:],"haC:d:Di:o:T:",["database=","output=","keep-all","interval=","clic-seq-length=","time-seq-length=","drop-truncated"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-a", "--keep-all"):
            KEEP_ALL = True
        elif opt in ("-C", "--clic-seq-length"):
            SEQ_CLIC_LEN = int(arg)
        elif opt in ("-d", "--database"):
            mooc_db = arg
        elif opt in ("-D", "--drop-truncated"):
            DROP_TRUNCATE_SEQ = True
        elif opt in ("-i", "--interval"):
            INTERVAL_DELAY = int(arg)
        elif opt in ("-o", "--output"):
            outputFileName = arg
        elif opt in ("-T", "--time-seq-length"):
            SEQ_TIME_LEN = int(arg)
    if mooc_db == '':
        print_help()
        sys.exit(2)

    if outputFileName == '':
        outputFileName = 'SEQ_' + mooc_db + '_a' + str(KEEP_ALL)[0] + '_i' + str(INTERVAL_DELAY) +\
                         '_C' + str(SEQ_CLIC_LEN) + '_T' + str(SEQ_TIME_LEN) + '_D' + str(DROP_TRUNCATE_SEQ)[0] + '.txt'
        
    outputFile = open(outputFileName, 'w')
    
    conn = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='', db=mooc_db, cursorclass=cursors.SSCursor)
    cursor = conn.cursor()
#    cursor.execute("SELECT DISTINCT(user_id) FROM observed_events")
    cursor.execute("SELECT user_id,observed_event_timestamp,observed_event_duration, observed_event_type_id, url_id " +
                    "FROM observed_events " +
                    "WHERE observed_event_type_id IN ('stop_video','speed_change_video','seek_video','play_video','pause_video','load_video') " + 
                    "ORDER BY user_id,observed_event_timestamp")
    cur_user = ''
    cur_clic_seq = []
    cur_dur_seq = []
    cur_time_seq = []
    prev_ts = ''
    prev_video = -1
    print_header(outputFile)
    for user_id, event_ts, event_dur, event_type, cur_video in cursor.fetchall():
        if cur_user == '' or cur_user != user_id or prev_video != cur_video:
            print_sequence(cur_user, prev_video, prev_ts, cur_clic_seq, cur_dur_seq, cur_time_seq, outputFile)
            cur_user = user_id
            cur_clic_seq = []
            cur_dur_seq = []
            cur_time_seq = []
            prev_ts = event_ts
            prev_video = cur_video
            if not user_vid_count_dict.has_key(cur_user + str(cur_video)):
                user_vid_count_dict[cur_user + str(cur_video)] = 0
            user_vid_count_dict[cur_user + str(cur_video)] += 1
        nb_to_add = event_dur//INTERVAL_DELAY
        if KEEP_ALL:
            nb_to_add += 1
        for i in range(0,nb_to_add):
            cur_time_seq.append(type_dict[event_type])
        cur_clic_seq.append(type_dict[event_type])
        cur_dur_seq.append(event_dur)
#        print user_id + str(event_ts) + str(event_dur) + event_type
    print_sequence(cur_user, prev_video, prev_ts, cur_clic_seq, cur_dur_seq, cur_time_seq, outputFile)
        
    cursor.close()
    conn.close()
    outputFile.close()
#    print 'DONE!'
