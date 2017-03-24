import MySQLdb
import MySQLdb.cursors as cursors

type_dict = {'stop_video' : 'St',
             'speed_change_video' : 'Sp',
             'seek_video' : 'Se',
             'play_video' : 'Pl',
             'pause_video' : 'Pa',
             'load_video' : 'Lo'             
            }

if __name__ == "__main__":
    conn = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='MOOCdb_ULB', cursorclass=cursors.SSCursor)
    cursor = conn.cursor()
#    cursor.execute("SELECT DISTINCT(user_id) FROM observed_events")
    cursor.execute("SELECT user_id,observed_event_timestamp,observed_event_duration, observed_event_type_id " +
                    "FROM observed_events " +
                    "WHERE observed_event_type_id IN ('stop_video','speed_change_video','seek_video','play_video','pause_video','load_video') " + 
                    "ORDER BY user_id,observed_event_timestamp")
    count = 0
    cur_user = ''
    cur_line = ''
    print 'ID|T1|T2|T3|T4|T5|T6|T7|T8|T9|T10|T11|T12|T13|T14|T15|T16|T17|T18|T19|T20|T21|T22|T23|T24|T25|T26|T27|T28|T29|T30|T31|T32|T33|T34|T35|T36|T37|T38|T39|T40|T41|T42|T43|T44|T45|T46|T47|T48|T49|T50|T51|T52|T53|T54|T55|T56|T57|T58|T59|T60|T61|T62|T63|T64|T65|T66|T67|T68|T69|T70|T71|T72|T73|T74|T75|T76|T77|T78|T79|T80|T81|T82|T83|T84|T85|T86|T87|T88|T89|T90|T91|T92|T93|T94|T95|T96|T97'
    for user_id, event_ts, event_dur, event_type in cursor.fetchall():
        if cur_user == '':
            cur_user = user_id
            cur_line = user_id
        if cur_user != user_id:
            cur_user = user_id
            if count > 0:
                for i in range(count,97):
                    cur_line += '|NA'
                print cur_line
                count = 0
            cur_line = user_id
        if event_dur//15 > 0:
            nb_to_add = event_dur//15
            while nb_to_add + count >= 97:
                nb_to_add = nb_to_add - (97 - count)
                for i in range(count,97):
                    cur_line += '|' + type_dict[event_type]
                print cur_line
                cur_line = user_id
                count = 0
            for i in range(0,nb_to_add):
                cur_line += '|' + type_dict[event_type]
            count += nb_to_add
#        print user_id + str(event_ts) + str(event_dur) + event_type
    if count > 0:
        for i in range(count,97):
            cur_line += '|NA'
        print cur_line        
        
    cursor.close()
    conn.close()
#    print 'DONE!'
