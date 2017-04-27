import sys
import getopt
import MySQLdb
import MySQLdb.cursors as cursors

SEQ_LEN = 97
INTERVAL_DELAY = 15 # in second
NEW_SESSION_DELAY = 3600000000 # in second
TRUNCATE_SEQ = False
SESSION_BY_VIDEO = False # Create a new session for each video viewed
KEEP_ALL = False
SEQ_SORTED = False
PRINT_PCT = False

type_dict = {'stop_video' : 'St',
             'speed_change_video' : 'Sp',
             'seek_video' : 'Se',
             'play_video' : 'Pl',
             'pause_video' : 'Pa',
             'load_video' : 'Lo'             
            }

def print_header(outputFile):
    header = 'ID'
    for i in range(1,SEQ_LEN+1):
        header += '|T' + format(i, '03')
    header += '\n'
    outputFile.write(header)
#    print 'ID|T1|T2|T3|T4|T5|T6|T7|T8|T9|T10|T11|T12|T13|T14|T15|T16|T17|T18|T19|T20|T21|T22|T23|T24|T25|T26|T27|T28|T29|T30|T31|T32|T33|T34|T35|T36|T37|T38|T39|T40|T41|T42|T43|T44|T45|T46|T47|T48|T49|T50|T51|T52|T53|T54|T55|T56|T57|T58|T59|T60|T61|T62|T63|T64|T65|T66|T67|T68|T69|T70|T71|T72|T73|T74|T75|T76|T77|T78|T79|T80|T81|T82|T83|T84|T85|T86|T87|T88|T89|T90|T91|T92|T93|T94|T95|T96|T97'

def print_header_pct():
    print 'ID|Lo|Pa|Pl|Se|Sp|St|NA'
    
def print_sequence_pct(cur_user, cur_line):
    print cur_user + '|' + format(cur_line.count('Lo')/float(SEQ_LEN), '0.4f') +\
            '|' + format(cur_line.count('Pa')/float(SEQ_LEN), '0.4f') + '|' + format(cur_line.count('Pl')/float(SEQ_LEN), '0.4f') +\
            '|' + format(cur_line.count('Se')/float(SEQ_LEN), '0.4f') + '|' + format(cur_line.count('Sp')/float(SEQ_LEN), '0.4f') +\
            '|' + format(cur_line.count('St')/float(SEQ_LEN), '0.4f') + '|' + format(cur_line.count('NA')/float(SEQ_LEN), '0.4f')

#    print cur_user + '|' + str(cur_line.count('Lo')/float(SEQ_LEN)) +\
#            '|' + str(cur_line.count('Pa')/float(SEQ_LEN)) + '|' + str(cur_line.count('Pl')/float(SEQ_LEN)) +\
#            '|' + str(cur_line.count('Se')/float(SEQ_LEN)) + '|' + str(cur_line.count('Sp')/float(SEQ_LEN)) +\
#            '|' + str(cur_line.count('St')/float(SEQ_LEN)) + '|' + str(cur_line.count('NA')/float(SEQ_LEN))

#    print cur_user + '|' + format(cur_line.count('Lo'), '03') +\
#            '|' + format(cur_line.count('Pa'), '03') + '|' + format(cur_line.count('Pl'), '03') +\
#            '|' + format(cur_line.count('Se'), '03') + '|' + format(cur_line.count('Sp'), '03') +\
#            '|' + format(cur_line.count('St'), '03') + '|' + format(cur_line.count('NA'), '03')
            
#    seq_cumul_dict = {'Lo':0, 'Pa':0, 'Pl':0, 'Se':0, 'Sp':0, 'St':0, 'NA':0}
#    for event in cur_seq:
#        seq_cumul_dict[event] += 1
#    print cur_user + '|' + str(seq_cumul_dict['Lo']/float(SEQ_LEN)) + '|' + str(seq_cumul_dict['Pa']/float(SEQ_LEN)) +\
#                '|' + str(seq_cumul_dict['Pl']/float(SEQ_LEN)) + '|' + str(seq_cumul_dict['Se']/float(SEQ_LEN)) +\
#                '|' + str(seq_cumul_dict['Sp']/float(SEQ_LEN)) + '|' + str(seq_cumul_dict['St']/float(SEQ_LEN)) +\
#                '|' + str(seq_cumul_dict['NA']/float(SEQ_LEN))

def print_sequence(cur_user, cur_seq, outputFile):
    if len(cur_seq) > 0:
        print str(len(cur_seq)) + " : " + cur_user
    count = 0;
    cur_line = cur_user
    if SEQ_SORTED:
        cur_seq.sort()
    for event in cur_seq:
        cur_line += '|' + event
        count += 1
        if count % SEQ_LEN == 0:
            cur_line += '\n'
            outputFile.write(cur_line)
            if PRINT_PCT:
                print_sequence_pct(cur_user,cur_line)
            if TRUNCATE_SEQ:
                return
            cur_line = cur_user
            count = 0
    if count > 0:
        for i in range(count,SEQ_LEN):
            cur_line += '|NA'
        cur_line += '\n'
        outputFile.write(cur_line)
        if PRINT_PCT:
            print_sequence_pct(cur_user,cur_line)

def print_help():
    print 'test.py -d <databaseName> -o <outputFile> [-a -i <timeInterval> -l <sequenceLength> -s <sessionDelay> -S -t -v]'
    print "a: keep all events"
    print "S: sort the events"
    print "t: truncate the sequence"
    print "v: create a sequence for each video"
    print "Default values a:F i:15 l:97 s:3600000000 S:F t:F v:F"

if __name__ == "__main__":
    mooc_db = ''
    outputFileName = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:],"had:i:l:o:s:Stv",["database=","output=","keep-all","interval=","seq-length=","session-delay=","sorted","truncate","video-split"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-a", "--keep-all"):
            KEEP_ALL = True
        elif opt in ("-d", "--database"):
            mooc_db = arg
        elif opt in ("-i", "--interval"):
            INTERVAL_DELAY = int(arg)
        elif opt in ("-l", "--seq-length"):
            SEQ_LEN = int(arg)
        elif opt in ("-o", "--output"):
            outputFileName = arg
        elif opt in ("-s", "--session-delay"):
            NEW_SESSION_DELAY = int(arg)
        elif opt in ("-S", "--sorted"):
            SEQ_SORTED = True
        elif opt in ("-t", "--truncate"):
            TRUNCATE_SEQ = True
        elif opt in ("-v", "--video-split"):
            SESSION_BY_VIDEO = True
    if mooc_db == '':
        print_help()
        sys.exit(2)

    if outputFileName == '':
        outputFileName = 'SEQ_' + mooc_db + '_a' + str(KEEP_ALL)[0] + '_i' + str(INTERVAL_DELAY) +\
                        '_l' + str(SEQ_LEN) + '_s' + str(NEW_SESSION_DELAY) + '_S' + str(SEQ_SORTED)[0] +\
                        '_t' + str(TRUNCATE_SEQ)[0] + '_v' + str(SESSION_BY_VIDEO)[0] + '.txt'

    outputFile = open(outputFileName, 'w')
    
    conn = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='', db=mooc_db, cursorclass=cursors.SSCursor)
    cursor = conn.cursor()
#    cursor.execute("SELECT DISTINCT(user_id) FROM observed_events")
    cursor.execute("SELECT user_id,observed_event_timestamp,observed_event_duration, observed_event_type_id, url_id " +
                    "FROM observed_events " +
                    "WHERE observed_event_type_id IN ('stop_video','speed_change_video','seek_video','play_video','pause_video','load_video') " + 
                    "ORDER BY user_id,observed_event_timestamp")
    cur_user = ''
    cur_seq = []
    prev_ts = ''
    prev_video = -1
    print_header(outputFile)
    if PRINT_PCT:
        print_header_pct()
    for user_id, event_ts, event_dur, event_type, cur_video in cursor.fetchall():
        if cur_user == '':
            cur_user = user_id
            cur_seq = []
            prev_ts = event_ts
            prev_video = cur_video
        if cur_user != user_id:
            print_sequence(cur_user, cur_seq, outputFile)
            cur_seq = []
            cur_user = user_id
            prev_ts = event_ts
            prev_video = cur_video
        if (int((event_ts - prev_ts).total_seconds()) > NEW_SESSION_DELAY):
            print_sequence(cur_user, cur_seq, outputFile)
            cur_seq = []
            cur_user = user_id
            prev_ts = event_ts
            prev_video = cur_video
        if prev_video != cur_video and SESSION_BY_VIDEO: # TODO... 
            print_sequence(cur_user, cur_seq, outputFile)
            cur_seq = []
            cur_user = user_id
            prev_ts = event_ts
            prev_video = cur_video
        prev_ts = event_ts
        prev_video = cur_video
        nb_to_add = event_dur//INTERVAL_DELAY
        if KEEP_ALL:
            nb_to_add += 1
        for i in range(0,nb_to_add):
            cur_seq.append(type_dict[event_type])
#        print user_id + str(event_ts) + str(event_dur) + event_type
    print_sequence(cur_user,cur_seq, outputFile)
        
    cursor.close()
    conn.close()
    outputFile.close()
#    print 'DONE!'
