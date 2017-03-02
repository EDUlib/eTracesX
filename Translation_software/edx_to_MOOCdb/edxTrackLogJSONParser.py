'''
Created on Oct 2, 2013

:author: paepcke

Modifications:

* Jun 23, 2014: Added support for AB Experiment events
* Dec 28, 2013: Col load_info_fk in EdxTrackEvent now properly typed to varchar(40) to match LoadInfo.load_info_id's type uses REPLACE INTO, rather than INSERT INTO
* Dec 28, 2013: Fixed some epydoc comment format errors.  

* Dec 29, 2013: Caused the ALTER ENABLE KEYS section in the output .sql file
                to be commented out. When loading multiple .sql files in a row,
                these statements caused re-creation of indexes after each load,
                adding significantly to the load time. Instead, manageEdxDb.py
                handles the re-enabling. 
                In pushDBCreations() pushed a header comment into the output .sql
                file to warn about the commented-out ALTER ENABLE KEYS. The comment
                advises to uncomment if loading manually, i.e. not via
                manageEdxDb.py.
                
'''

from collections import OrderedDict
import datetime
import hashlib
import json
import os
import re
import string
from unidecode import unidecode
import uuid

from locationManager import LocationManager
from modulestoreImporter import ModulestoreImporter
from ipToCountry import IpCountryDict

EDX_HEARTBEAT_PERIOD = 360 # seconds

class EdXTrackLogJSONParser(object):
    '''
    Parser specialized for EdX track logs.
    '''
    # Class var to detect JSON strings that contain backslashes 
    # in front of chars other than \bfnrtu/. JSON allows backslashes
    # only before those. But: /b, /f, /n, /r, /t, /u, and \\ also need to
    # be escaped.
    # Pattern used in makeSafeJSON()
    #JSON_BAD_BACKSLASH_PATTERN = re.compile(r'\\([^\\bfnrtu/])')
    JSON_BAD_BACKSLASH_PATTERN = re.compile(r'\\([^/"])')

    # Regex patterns for extracting fields from bad JSON:
    searchPatternDict = {}
    searchPatternDict['username'] = re.compile(r"""
                                    username[^:]*       # The screen_name key
                                    [^"']*              # up to opening quote of the value 
                                    ["']                # opening quote of the value 
                                    ([^"']*)            # the value
                                    """, re.VERBOSE)
    searchPatternDict['host'] = re.compile(r"""
                                    host[^:]*
                                    [^"']*
                                    ["']
                                    ([^"']*)
                                    """, re.VERBOSE)
    searchPatternDict['session'] = re.compile(r"""
                                    session[^:]*
                                    [^"']*
                                    ["']
                                    ([^"']*)
                                    """, re.VERBOSE)
    searchPatternDict['event_source'] = re.compile(r"""
                                    event_source[^:]*
                                    [^"']*
                                    ["']
                                    ([^"']*)
                                    """, re.VERBOSE)
    searchPatternDict['event_type'] = re.compile(r"""
                                    event_type[^:]*
                                    [^"']*
                                    ["']
                                    ([^"']*)
                                    """, re.VERBOSE)
    searchPatternDict['time'] = re.compile(r"""
                                    time[^:]*
                                    [^"']*
                                    ["']
                                    ([^"']*)
                                    """, re.VERBOSE)
    searchPatternDict['ip'] = re.compile(r"""
                                    ip[^:]*
                                    [^"']*
                                    ["']
                                    ([^"']*)
                                    """, re.VERBOSE)
    
    searchPatternDict['event'] = re.compile(r"""
                                    [\\"']event[\\"']   # Event with possibly backslashed quotes
                                    [^:]*               # up to the colon
                                    :                   # colon that separates key and value
                                    (.*)                # all of the rest of the string.
                                    """, re.VERBOSE)
    
    
    # Picking (likely) zip codes out of a string:
    zipCodePattern = re.compile(r'[^0-9]([0-9]{5})')
    
    hexGE32Digits = re.compile(r'[a-fA-F0-9]{32,}')
    
    # Finding the word 'status' in problem_graded events:
    # Extract problem ID and 'correct' or 'incorrect' from 
    # a messy problem_graded event string. Two cases:
    #     ' aria-describedby=\\"input_i4x-Medicine-SciWrite-problem-c3266c76a7854d02b881250a49054ddb_2_1\\">\\n        incorrect\\n      </p>\\n\\n'
    # and
    #     'aria-describedby=\\"input_i4x-Medicine-HRP258-problem-068a71cb1a1a4da39da093da2778f000_3_1_choice_2\\">Status: incorrect</span>'
    # with lots of HTML and other junk around it.
    problemGradedComplexPattern = re.compile(r'aria-describedby=[\\"]*(input[^\\">]*)[\\"]*[>nStatus\\:\s"]*([iIn]{0,2}correct)')

    # isolate '-Medicine-HRP258-problem-8dd11b4339884ab78bc844ce45847141_2_1":' from:
    # ' {"success": "correct", "correct_map": {"i4x-Medicine-HRP258-problem-8dd11b4339884ab78bc844ce45847141_2_1": {"hint": "", "mode": null'
    problemXFindCourseID = re.compile(r'[^-]*([^:]*)')

    # Isolate 32-bit hash inside any string, e.g.:
    #   i4x-Medicine-HRP258-videoalpha-7cd4bf0813904612bcd583a73ade1d54
    # or:
    #   input_i4x-Medicine-HRP258-problem-98ca37dbf24849debcc29eb36811cb68_3_1_choice_3'
    findHashPattern = re.compile(r'([a-f0-9]{32})')
    
    def __init__(self):
        '''
        Constructor

        :param mainTableName: name wanted for the table into which the bulk of event data is placed
        :type mainTableName: String
        :param logfileID: an identfier of the tracking log file being processed. Used 
               to build error/warning msgs that cite a file and line number in
               their text
        :type logfileID: String
        :param progressEvery: number of input lines, a.k.a. JSON objects after which logging should report total done
        :type progressEvery: int
        :param replaceTables: determines whether the tables that constitute EdX track logs are to be deleted before inserting entries. Default: False
        :type  replaceTables: bool
        :param dbName: database name into which tables will be created (if replaceTables is True), and into which insertions will take place.
        :type dbName: String
        :param useDisplayNameCache: if True then use an existing cache for mapping
                    OpenEdx hashes to human readable display names is used. Else
                    the required information is read and parsed from a JSON file name
                    that contains the needed information from modulestore. See
                    modulestoreImporter.py for details. 
        :type useDisplayNameCache: Bool      
        '''
        
        # Prepare as much as possible outside parsing of
        # each line; Build the schema:
        
        # Fields common to every request:
        self.commonFldNames = ['agent',
                               'event_source',
                               'event_type',
                               'ip',
                               'page',
                               'session',
                               'time',
                               'username', 
                               'course_id', 
                               'course_display_name',
                               'context'
                               ]

        # A Country abbreviation lookup facility:
        self.countryChecker = LocationManager()
        
        # An ip-country lookup facility:
        self.ipCountryDict = IpCountryDict()
    
        # Lookup table from OpenEdx 32-bit hash values to
        # corresponding problem, course, or video display_names.
        # This call can cause a portion of the modulestore to be
        # pulled from S3, which may cause exceptions. Those
        # are caught and logged by the caller:
        self.hashMapper = ModulestoreImporter(os.path.join(os.path.dirname(__file__),'data/modulestore_latest.json'), 
                                              useCache=False, 
                                              parent=self)
        # Make a list of all short course names 
        # sorted by length in decreasing order. 
        # This list is used by extractCanonicalCourseName()
        # to pull the most likely course name from a nasty
        # string that has a course name embedded:
        self.courseNamesSorted = sorted(self.hashMapper.keys(), key=len, reverse=True)
                
        # Dict<IP,Datetime>: record each IP's most recent
        # activity timestamp (heartbeat or any other event).
        # Used to detect server downtimes: 
        self.downtimes = {}
                
        # Place to keep history for some rows, for which we want
        # to computer some on-the-fly aggregations:
        self.resultDict = {}

        self.currContext = None;
        
        self.currentEvent = {}        
        self.eventsQueue = []  
        
    def logWarn(self, msg):
        print msg

    def logInfo(self, msg):
        print msg
     
    def logError(self, msg):
        print msg

    def logDebug(self, msg):
        print msg
        
    def makeFileCitation(self):
        return '-1'
    
    def format_timestamp(self, jsonobject):
        time = jsonobject['time']
        if isinstance(time, dict):
            timestamp = int(time["$date"])/1000.0
            time_obj = datetime.datetime.fromtimestamp(timestamp)
            time_formatted = time_obj.strftime('%Y-%m-%dT%H:%M:%S.%f') 
            jsonobject['time'] = time_formatted
            
    def setValInRow(self, colName, value):
        if value is None:
            value = ''
        self.currentEvent[colName] = str(value)
        
    def pushEvent(self):
        if not self.currentEvent.has_key('answer'):
            self.currentEvent['answer'] = ''
        if not self.currentEvent.has_key('answer_identifier'):
            self.currentEvent['answer_identifier'] = ''
        if not self.currentEvent.has_key('correctness'):
            self.currentEvent['correctness'] = ''
            
        if not self.currentEvent.has_key('_id'):
            self.currentEvent['_id'] = ''
        if not self.currentEvent.has_key('agent'):
            self.currentEvent['agent'] = ''
        if not self.currentEvent.has_key('event_type'):
            self.currentEvent['event_type'] = ''
        if not self.currentEvent.has_key('ip'):
            self.currentEvent['ip'] = ''
        if not self.currentEvent.has_key('page'):
            self.currentEvent['page'] = ''
        if not self.currentEvent.has_key('time'):
            self.currentEvent['time'] = ''
        if not self.currentEvent.has_key('anon_screen_name'):
            self.currentEvent['anon_screen_name'] = ''
        if not self.currentEvent.has_key('resource_display_name'):
            self.currentEvent['resource_display_name'] = ''
        if not self.currentEvent.has_key('goto_dest'):
            self.currentEvent['goto_dest'] = ''
        if not self.currentEvent.has_key('problem_id'):
            self.currentEvent['problem_id'] = ''
        if not self.currentEvent.has_key('question_location'):
            self.currentEvent['question_location'] = ''
        if not self.currentEvent.has_key('attempts'):
            self.currentEvent['attempts'] = -1
        if not self.currentEvent.has_key('transcript_id'):
            self.currentEvent['transcript_id'] = ''
        if not self.currentEvent.has_key('transcript_code'):
            self.currentEvent['transcript_code'] = ''
        if not self.currentEvent.has_key('video_id'):
            self.currentEvent['video_id'] = ''
        if not self.currentEvent.has_key('video_code'):
            self.currentEvent['video_code'] = ''
        if not self.currentEvent.has_key('book_interaction_type'):
            self.currentEvent['book_interaction_type'] = ''
        if not self.currentEvent.has_key('correctMap_fk'):
            self.currentEvent['correctMap_fk'] = ''
        if not self.currentEvent.has_key('answer_fk'):
            self.currentEvent['answer_fk'] = ''
        if not self.currentEvent.has_key('sequence_id'):
            self.currentEvent['sequence_id'] = ''
        if not self.currentEvent.has_key('goto_from'):
            self.currentEvent['goto_from'] = ''
        if not self.currentEvent.has_key('success'):
            self.currentEvent['success'] = ''
            
        self.eventsQueue.insert(0, self.currentEvent)
        self.currentEvent = self.currentEvent.copy() 
        
    def processOneJSONObject(self, jsonStr):
        '''
        This method is the main dispatch for track log event_types.
        It's a long method, and should be partitioned. First, bookkeeping
        fields are filled in that are common to all events, such as the 
        user agent, and the reference into the LoadInfo table that shows
        on which date this row was loaded. Then a long 'case' statement
        calls handler methods depending on the incoming track log's event_type.  
        
        Given one line from the EdX Track log, produce one row
        of relational output. Return is an array of values, the 
        same that is passed in. On the way, the partner JSONToRelation
        object is called to ensure that JSON fields for which new columns
        have not been created yet receive a place in the row array.    
        Different types of JSON records will be passed: server heartbeats,
        dashboard accesses, account creations, user logins. Example record
        for the latter::
        
            {"username": "", 
             "host": "class.stanford.edu", 
             "event_source": "server", 
             "event_type": "/accounts/login", 
             "time": "2013-06-14T00:31:57.661338", 
             "ip": "98.230.189.66", 
             "event": "{
                        \"POST\": {}, 
                          \"GET\": {
                             \"next\": [\"/courses/Medicine/HRP258/Statistics_in_Medicine/courseware/80160e.../\"]}}", 
             "agent": "Mozilla/5.0 (Windows NT 5.1; rv:21.0) Gecko/20100101
             Firefox/21.0", 
             "page": null}

        Two more examples to show the variance in the format. Note "event" field:
        
        Second example::
        
            {"username": "jane", 
             "host": "class.stanford.edu", 
             "event_source": "server", 
             "event_type": "/courses/Education/EDUC115N/How_to_Learn_Math/modx/i4x://Education/EDUC115N/combinedopenended/c415227048464571a99c2c430843a4d6/get_results", 
             "time": "2013-07-31T06:27:06.222843+00:00", 
             "ip": "67.166.146.73", 
             "event": "{\"POST\": {
                                    \"task_number\": [\"0\"]}, 
                                    \"GET\": {}}",
             "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36", 
             "page": null
             }
                
        Third example::
        
            {"username": "miller", 
             "host": "class.stanford.edu", 
             "session": "fa715506e8eccc99fddffc6280328c8b", 
             "event_source": "browser", 
             "event_type": "hide_transcript", 
             "time": "2013-07-31T06:27:10.877992+00:00", 
             "ip": "27.7.56.215", 
             "event": "{\"id\":\"i4x-Medicine-HRP258-videoalpha-09839728fc9c48b5b580f17b5b348edd\",
                        \"code\":\"fQ3-TeuyTOY\",
                        \"currentTime\":0}", 
             "agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36", 
             "page": "https://class.stanford.edu/courses/Medicine/HRP258/Statistics_in_Medicine/courseware/495757ee7b25401599b1ef0495b068e4/6fd116e15ab9436fa70b8c22474b3c17/"
             }
                
        :param jsonStr: string of a single, self contained JSON object
        :type jsonStr: String
        :param row: partially filled array of values. Passed by reference
        :type row: List<<any>>
        :return: the filled-in row

        :rtype: [<any>]
        '''
        
        self.currentEvent = {}        
        self.eventsQueue = []
        
        # No error has occurred yet in processing this JSON str:
        self.errorOccurred = False
        try:
            # Turn top level JSON object to dict:
            try:
                record = json.loads(str(jsonStr))
            except ValueError as e:
                # Try it again after cleaning up the JSON
                # We don't do the cleanup routinely to save
                # time.
                try:
                    cleanJsonStr = self.makeJSONSafe(jsonStr)
                    record = json.loads(cleanJsonStr)
                except ValueError as e:
                    # Pull out what we can, and place in 'badly_formatted' column
                    self.rescueBadJSON(jsonStr)                
                    raise ValueError('Ill formed JSON: %s' % `e`)
    
            # Apply formatting specific to MIT logs
            self.format_timestamp(record)

            # Dispense with the fields common to all events, except event,
            # which is a nested JSON string. Results will be 
            # in self.resultDict:
            self.handleCommonFields(record)
            #print self.resultDict 
            
            # If the event was fully handled in
            # handleCommonFields(), then we're done:
            if self.finishedRow:
                return
            
            # Now handle the different types of events:
            
            try:
                eventType = record['event_type']
            except KeyError:
                # New-type event, in which the event_type is a field
                # called 'name' within the 'event' field:
                try:
                    event = record['event']
                except KeyError:
                    # No event record at all:
                    raise KeyError("No event field")
                event = self.ensureDict(event)
                if event is None:
                    raise KeyError("No properly formatted event field")
                eventType = event.get('name', None)
                if eventType is None:
                    raise KeyError("No event type field; cannot determine tye type of event.")
            
            # Check whether we had a server downtime:
            try:
                eventTimeStr = record['time']
                ip = record['ip']
                if ip == "":
                    ip = "127.0.0.1"
                # Time strings in the log may or may not have a UTF extension:
                # '2013-07-18T08:43:32.573390:+00:00' vs '2013-07-18T08:43:32.573390'
                # For now we ignore time zone. Observed log samples are
                # all universal +/- 0:
                maybeOffsetDir = eventTimeStr[-6]
                if maybeOffsetDir == '+' or maybeOffsetDir == '-': 
                    eventTimeStr = eventTimeStr[0:-6]
                eventDateTime = datetime.datetime.strptime(eventTimeStr, '%Y-%m-%dT%H:%M:%S.%f')
            except KeyError:
                raise ValueError("No event time or server IP.")
            except ValueError:
                raise ValueError("Bad event time format: '%s'" % eventTimeStr)
            
            try:
                doRecordHeartbeat = False
                recentSignOfLife = self.downtimes[ip]
                # Get a timedelta obj w/ duration of time
                # during which nothing was heard from server:
                serverQuietTime = eventDateTime - recentSignOfLife
                if serverQuietTime.seconds > EDX_HEARTBEAT_PERIOD:
                    self.setValInRow('downtime_for', str(serverQuietTime))
                    doRecordHeartbeat = True
                # New recently-heard from this IP:
                self.downtimes[ip] = eventDateTime
            except KeyError:
                # First sign of life for this IP:
                self.downtimes[ip] = eventDateTime
                # Record a time of 0 in downtime detection column:
                self.setValInRow('downtime_for', str(datetime.timedelta()))
                doRecordHeartbeat = True
                
            
            if eventType == '/heartbeat':
                # Handled heartbeat above, we don't transfer the heartbeats
                # themselves into the relational world. If a server
                # downtime was detected from the timestamp of this
                # heartbeat, then above code added a respective warning
                # into the row, else we just ignore the heartbeat
                if not doRecordHeartbeat:
                    self.currentEvent = {}
                return
            
            # If eventType is "/" then it was a ping, no more to be done:
            if eventType == '/':
                self.currentEvent = {}
                return
            elif eventType == 'page_close':
                # The page ID was already recorded in the common fields:
                return

            # For any event other than heartbeat, we need to look
            # at the event field, which is an embedded JSON *string*
            # Turn that string into a (nested) Python dict. Though
            # *sometimes* the event *is* a dict, not a string, as in
            # problem_check_fail:
            try:
                eventJSONStrOrDict = record['event']
            except KeyError:
                raise ValueError("Event of type %s has no event field" % eventType)
            
            try:
                event = json.loads(eventJSONStrOrDict)
            except TypeError:
                # Was already a dict
                event = eventJSONStrOrDict
            except Exception as e:
                # Try it again after cleaning up the JSON
                # We don't do the cleanup routinely to save
                # time.
                try:
                    cleanJSONStr = self.makeJSONSafe(eventJSONStrOrDict)
                    event = json.loads(cleanJSONStr)
                except ValueError:
                    # Last ditch: event types like goto_seq, need backslashes removed:
                    event = json.loads(re.sub(r'\\','',eventJSONStrOrDict))
                except Exception as e1:                
                    self.rescueBadJSON(str(record))
                    raise ValueError('Bad JSON; saved in col badlyFormatted: event_type %s (%s)' % (eventType, `e1`))
                    return

            if eventType == 'seq_goto' or\
               eventType == 'seq_next' or\
               eventType == 'seq_prev':
            
                self.handleSeqNav(record, event, eventType)
                return
            
            elif eventType == '/accounts/login':
                # Already recorded everything needed in common-fields
                return
            
            elif eventType == '/login_ajax':
                self.handleAjaxLogin(record, event, eventType)
                return
            
            elif eventType == 'problem_check' or\
                 eventType == 'save_problem_check':
                # Note: some problem_check cases are also handled in handleAjaxLogin()
                self.handleProblemCheck(record, event)
                return
             
            elif eventType == 'problem_reset':
                self.handleProblemReset(record, event)
                return
            
            elif eventType == 'problem_show':
                self.handleProblemShow(record, event)
                return
            
            elif eventType == 'problem_save':
                self.handleProblemSave(record, event)
                return
            
            elif eventType == 'oe_hide_question' or\
                 eventType == 'oe_hide_problem' or\
                 eventType == 'peer_grading_hide_question' or\
                 eventType == 'peer_grading_hide_problem' or\
                 eventType == 'staff_grading_hide_question' or\
                 eventType == 'staff_grading_hide_problem' or\
                 eventType == 'oe_show_question' or\
                 eventType == 'oe_show_problem' or\
                 eventType == 'peer_grading_show_question' or\
                 eventType == 'peer_grading_show_problem' or\
                 eventType == 'staff_grading_show_question' or\
                 eventType == 'staff_grading_show_problem':
                 
                self.handleQuestionProblemHidingShowing(record, event)
                return
    
            elif eventType == 'rubric_select':
                self.handleRubricSelect(record, event)
                return
            
            elif eventType == 'oe_show_full_feedback' or\
                 eventType == 'oe_show_respond_to_feedback':
                self.handleOEShowFeedback(record, event)
                return
                
            elif eventType == 'oe_feedback_response_selected':
                self.handleOEFeedbackResponseSelected(record, event)
                return
            
            elif eventType == 'show_transcript' or eventType == 'hide_transcript':
                self.handleShowHideTranscript(record, event)
                return
            
            elif eventType == 'play_video' or\
                 eventType == 'pause_video' or\
                 eventType == 'stop_video' or\
                 eventType == 'video_player_ready' or\
                 eventType == 'load_video':
                self.handleVideoPlayPause(record, event)
                return

            elif eventType == 'seek_video':
                self.handleVideoSeek(record, event)
                return
                
            elif eventType == 'speed_change_video':
                self.handleVideoSpeedChange(record, event)
                return
                
            elif eventType == 'fullscreen':
                self.handleFullscreen(record, event)
                return
                
            elif eventType == 'not_fullscreen':
                self.handleNotFullscreen(record, event)
                return
                
            elif eventType == '/dashboard':
                # Nothing additional to grab:
                return
                
            elif eventType == 'book':
                self.handleBook(record, event)
                return
    
            elif eventType == 'showanswer' or eventType == 'show_answer':
                self.handleShowAnswer(record, event)
                return
    
            elif eventType == 'problem_check_fail' or\
                 eventType == 'save_problem_check_fail':
                self.handleProblemCheckFail(record, event)
                return
            
            elif eventType == 'problem_rescore_fail':
                self.handleProblemRescoreFail(record, event)
                return
            
            elif eventType == 'problem_rescore':
                self.handleProblemRescore(record, event)
                return
            
            elif eventType == 'save_problem_fail' or\
                 eventType == 'save_problem_success' or\
                 eventType == 'reset_problem_fail':
                self.handleSaveProblemFailSuccessCheckOrReset(record, event)
                return
                # Removed the case eventType == 'save_problem_check' 
                # save_problem_check should be treated as
                # problem_check in early log versions.
                
            elif eventType == 'reset_problem':
                self.handleResetProblem(record, event)
                return
            
            # Instructor events:
            elif eventType in ['list-students',  'dump-grades',  'dump-grades-raw',  'dump-grades-csv',
                               'dump-grades-csv-raw', 'dump-answer-dist-csv', 'dump-graded-assignments-config',
                               'list-staff',  'list-instructors',  'list-beta-testers'
                               ]:
                # These events have no additional info. The event_type says it all,
                # and that's already been stuck into the table:
                return
              
            elif eventType == 'rescore-all-submissions' or eventType == 'reset-all-attempts':
                self.handleRescoreReset(record, event)
                return
                
            elif eventType == 'delete-student-module-state' or eventType == 'rescore-student-submission':
                self.handleDeleteStateRescoreSubmission(record, event)
                return
                
            elif eventType == 'reset-student-attempts':
                self.handleResetStudentAttempts(record, event)
                return
                
            elif eventType == 'get-student-progress-page':
                self.handleGetStudentProgressPage(record, event)
                return
    
            elif eventType == 'add-instructor' or eventType == 'remove-instructor':        
                self.handleAddRemoveInstructor(record, event)
                return

            elif eventType in ['list-forum-admins', 'list-forum-mods', 'list-forum-community-TAs']:
                self.handleListForumMatters(record, event)
                return
    
            elif eventType in ['remove-forum-admin', 'add-forum-admin', 'remove-forum-mod',
                               'add-forum-mod', 'remove-forum-community-TA',  'add-forum-community-TA']:
                self.handleForumManipulations(record, event)
                return
    
            elif eventType == 'psychometrics-histogram-generation':
                self.handlePsychometricsHistogramGen(record, event)
                return
            
            elif eventType == 'add-or-remove-user-group':
                self.handleAddRemoveUserGroup(record, event)
                return
            
            elif eventType == '/create_account':
                self.handleCreateAccount(record, event)
                return
            
            elif eventType == 'problem_graded':
                # Need to look at return, b/c this
                # method handles all its own pushing:
                self.handleProblemGraded(record, event)
                return

            elif eventType == 'change-email-settings':
                self.handleReceiveEmail(record, event)
                return
                
            # A/B Test Events:
            elif eventType == 'assigned_user_to_partition' or eventType == 'child_render':
                self.handleABExperimentEvent(record, event)
                return
            
            elif eventType == 'edx.course.enrollment.activated' or eventType == 'edx.course.enrollment.deactivated':
                self.handleCourseEnrollActivatedDeactivated(record, event) 
                return
            
            # Forum events:
            elif eventType == 'edx.forum.searched':
                self.handleForumEvent(record, event)
                return
            
            elif eventType in ['edx.forum.comment.created',
                               'edx.forum.response.created',
                               'edx.forum.response.voted',
                               'edx.forum.thread.created',
                               'edx.forum.thread.voted']:
                self.handleListForumInteraction(record, event)
                return 
            
            # Event type values that start with slash:
            elif eventType[0] == '/':
                self.handlePathStyledEventTypes(record, event)
                return
            
            else:
                # Filter events
                # if eventType not in ['harvardx.video_embedded_problems']:
                self.logWarn("Unknown event type '%s' in tracklog row %s" % (eventType, self.makeFileCitation()))
                return
        except Exception as e:
            # Note whether any error occurred, so that
            # the finally clause can act accordingly:
            self.errorOccurred = True
            # Re-raise same error:
            raise
        finally:
            # If above code generated anything to INSERT into SQL
            # table, do that now. If row is None, then nothing needs
            # to be inserted (e.g. heartbeats):
            if self.currentEvent is not None and len(self.currentEvent) != 0 and not self.errorOccurred:
                self.pushEvent()
            # Clean out data structures in preparation for next 
            # call to this method:
            return self.eventsQueue
                
    def handleCommonFields(self, record):
        self.currCourseDisplayName = None
        # Create a unique tuple key and event key  for this event:
        event_tuple_id = self.getUniqueID()
        self.setValInRow('_id', event_tuple_id)
        self.setValInRow('event_id', self.getUniqueID())
        self.finishedRow = False
        for fldName in self.commonFldNames:
            # Default non-existing flds to null:
            val = record.get(fldName, None)
            # Ensure there are no embedded single quotes or CR/LFs;
            # takes care of name = O'Brian 
            if isinstance(val, basestring):
                val = self.makeInsertSafe(val)
            # if the event_type starts with a '/', followed by a 
            # class ID and '/about', treat separately:
            if fldName == 'event_type' and val is not None:
                if len(val) > 0 and  val[0] == '/' and val[-6:] == '/about':
                    self.setValInRow('course_id', val[0:-6])
                    val = 'about'
                    self.finishedRow = True
                elif val.find('/password_reset_confirm') == 0:
                    val = 'password_reset_confirm'
                    self.finishedRow = True
                elif val == '/networking/':
                    val = 'networking'
                    self.finishedRow = True
            elif fldName == 'course_id':
                (fullCourseName, course_id, displayName) = self.get_course_id(record)  # @UnusedVariable
                val = course_id
                # Make course_id available for places where rows are added to the Answer table.
                # We stick the course_id there for convenience.
                self.currCourseID = course_id
                self.currCourseDisplayName = displayName
            elif fldName == 'course_display_name':
                if self.currCourseDisplayName is not None:
                    val = self.currCourseDisplayName
                else:
                    (fullCourseName, course_id, displayName) = self.get_course_id(record)  # @UnusedVariable
                    val = displayName
            elif fldName == 'username':
                # Hash the name, and store in MySQL col 'anon_screen_name':
                if val is not None:
                    val = self.hashGeneral(val)
                fldName = 'anon_screen_name'
            elif fldName == 'ip':
                ip  = val
                if ip == "":
                    ip = "127.0.0.1"
                # Col value is to be three-letter country code;
                # Get the triplet (2-letter-country-code, 3-letter-country-code, country): 
                val = self.getThreeLetterCountryCode(ip)
#                fldName = 'ip_country'
                
                # The event row id and IP address go into 
                # a separate, temp table, to be transferred
                # to EdxPrivate later:
                eventIpDict = OrderedDict()
                eventIpDict['event_table_id'] = event_tuple_id
                eventIpDict['event_ip'] = ip
                self.pushEventIpInfo(eventIpDict)
            elif fldName == 'context':
                # Handle here all fields of the context dict
                # that are common. Then set self.currContext
                # to the context value, i.e. the dict inside.
                # These are course_id, org_id, and user_id.
                # We leave out the user_id, b/c we don't want
                # it in the tables: they have anon_screen_name
                # instead. With self.currContextDict, all field
                # handlers can grab what they need in their context:
                
                self.currContextDict = self.ensureDict(val)

                if self.currContextDict is not None:
                    theCourseId = self.currContextDict.get('course_id', None)
                    self.setValInRow('course_display_name', theCourseId)
                    
                    # Fill in the organization:
                    theOrg = self.currContextDict.get('org_id', None)
                    self.setValInRow('organization', theOrg)

                    # When a participant who is assigned to an AB experiment
                    # triggers an event, the context field course_user_tags
                    # contains a dict with user_id, course_id, key, and value,
                    # where key is the experiment partition, and value is 
                    # the experiment group_id to which the participant is
                    # was assigned.
                    
                    abTestInfo = self.currContextDict.get('course_user_tags', None)
                    if abTestInfo is not None:
                        abTestDictInfoDict = self.ensureDict(abTestInfo)
                        if abTestDictInfoDict is not None:
                            # Use handleABExperimentEvent(), passing the
                            # abTestInfo as if it were an event. The
                            # method will then add a row to the ABExperiment
                            # table:
                            self.handleABExperimentEvent(record, abTestDictInfoDict)

                    # Make course_id available for places where rows are added to the Answer table.
                    # We stick the course_id there for convenience.
                    self.currCourseID = theCourseId
                    self.currCourseDisplayName = theCourseId
                # We took care of all fields in the context element, so go on to next common field:
                continue
                
            self.setValInRow(fldName, val)
        # Add the foreign key that points to the current row in the load info table:
#        self.setValInRow('load_info_fk', self.currLoadInfoFK)

    def handleSeqNav(self, record, event, eventType):
        '''
        Video navigation. Events look like this::
        
            {"username": "BetaTester1", 
             "host": "class.stanford.edu", 
             "session": "009e5b5e1bd4ab5a800cafc48bad9e44", 
             "event_source": "browser", "
             event_type": "seq_goto", 
             "time": "2013-06-08T23:29:58.346222", 
             "ip": "24.5.14.103", 
             "event": "{\"old\":2,\"new\":1,\"id\":\"i4x://Medicine/HRP258/sequential/53b0357680d24191a60156e74e184be3\"}", 
             "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0", 
             "page": "https://class.stanford.edu/courses/Medicine/HRP258/Statistics_in_Medicine/courseware/ac6d006c4bc84fc1a9cec412734fd5ca/53b0357680d24191a60156e74e184be3/"
             }        
        
        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        :param eventType:
        :type eventType:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in sequence navigation event." %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in sequence navigation event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        oldIndex = event.get('old', 0)
        newIndex = event.get('new', 0)
        try:
            seqID    = event['id']
        except KeyError:
            self.logWarn("Track log line %s with event type %s is missing sequence id" %
                         (self.makeFileCitation(), eventType)) 
            return
        self.setValInRow('sequence_id', seqID)
        self.setValInRow('goto_from', oldIndex)
        self.setValInRow('goto_dest', newIndex)
        # Try to find a display name for this sequence id:
        self.setResourceDisplayName(seqID)
        
    def handleProblemCheck(self, record, event):
        '''
        The problem_check event comes in two flavors (assertained by observation):
        The most complex is this one::
        
          {       
            "success": "correct",
            "correct_map": {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {
                    "hint": "",
                    "mode": null,
                    "correctness": "correct",
                    "msg": "",
                    "npoints": null,
                    "queuestate": null
                },
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {
                    "hint": "",
                    "hintmode": null,
                    "correctness": "correct",
                    "msg": "",
                    "npoints": null,
                    "queuestate": null
                }
            },
            "attempts": 2,
            "answers": {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": "choice_0",
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": "choice_3"
            },
            "state": {
                "student_answers": {
                    "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": "choice_3",
                    "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": "choice_1"
                },
                "seed": 1,
                "done": true,
                "correct_map": {
                    "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {
                        "hint": "",
                        "hintmode": null,
                        "correctness": "incorrect",
                        "msg": "",
                        "npoints": null,
                        "queuestate": null
                    },
                    "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {
                        "hint": "",
                        "hintmode": null,
                        "correctness": "incorrect",
                        "msg": "",
                        "npoints": null,
                        "queuestate": null
                    }
                },
                "input_state": {
                    "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {},
                    "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {}
                }
            },
            "problem_id": "i4x://Medicine/HRP258/problem/e194bcb477104d849691d8b336b65ff6"
          }
          
        The simpler version is like this, in which the answers are styled as HTTP GET parameters::
        
          {"username": "smitch", 
           "host": "class.stanford.edu", 
           "session": "75a8c9042ba10156301728f61e487414", 
           "event_source": "browser", 
           "event_type": "problem_check", 
           "time": "2013-08-04T06:27:13.660689+00:00", 
           "ip": "66.172.116.216", 
           "event": "\"input_i4x-Medicine-HRP258-problem-7451f8fe15a642e1820767db411a4a3e_2_1=choice_2&
                       input_i4x-Medicine-HRP258-problem-7451f8fe15a642e1820767db411a4a3e_3_1=choice_2\"", 
           "agent": "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36", 
           "page": "https://class.stanford.edu/courses/Medicine/HRP258/Statistics_in_Medicine/courseware/de472d1448a74e639a41fa584c49b91e/ed52812e4f96445383bfc556d15cb902/"
           }            

        We handle the complex version here, but call problemCheckSimpleCase() 
        for the simple case.

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in problem_check event." %\
                         (self.makeFileCitation()))
            return

        if isinstance(event, basestring):
            # Simple case:
            return self.handleProblemCheckSimpleCase(event)

        # Complex case: event field should be a dict:
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in problem_check event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        # Go through all the top-level problem_check event fields first:
        self.setValInRow('success', event.get('success', '')) 
        self.setValInRow('attempts', event.get('attempts', -1))
        problem_id = event.get('problem_id', '')
        self.setValInRow('problem_id', problem_id)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problem_id)

        # correctMap field may consist of many correct maps.
        # Create an entry for each in the CorrectMap table,
        # collecting the resulting foreign keys:
        
        correctMapsDict = event.get('correct_map', None)
        if correctMapsDict is not None:
            (correctMapFKeys, correctMapTableDict) = self.pushCorrectMaps(correctMapsDict)
        else:
            correctMapFKeys = []    
        
        answersDict = event.get('answers', None)
        if answersDict is not None:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        else:
            answersFKeys = []
        
        stateDict = event.get('state', None)
        if stateDict is not None:
            stateFKeys = self.pushState(stateDict)
        else:
            stateFKeys = []

        # Now need to generate enough near-replicas of event
        # entries to cover all correctMap, answers, and state 
        # foreign key entries that were created:
        
        generatedAllRows = False
        indexToFKeys = 0
        # Generate main table rows that refer to all the
        # foreign entries we made above to Answer, CorrectMap, and State
        # We make as few rows as possible by filling in 
        # columns in all three foreign key entries, until
        # we run out of all references:
        while not generatedAllRows:
            try:
                correctMapFKey = correctMapFKeys[indexToFKeys]
            except IndexError:
                correctMapFKey = None
            try:
                answerFKey = answersFKeys[indexToFKeys]
            except IndexError:
                answerFKey = None
            try:
                stateFKey = stateFKeys[indexToFKeys]
            except IndexError:
                stateFKey = None
            
            # Have we created rows to cover all student_answers, correct_maps, and input_states?
            if correctMapFKey is None and answerFKey is None and stateFKey is None:
                generatedAllRows = True
                continue

            # Fill in one main table row.
            self.setValInRow('correctMap_fk', correctMapFKey if correctMapFKey is not None else '')
            self.setValInRow('answer_fk', answerFKey if answerFKey is not None else '')
            if answerFKey is not None:
                # For convenience: enter the Answer's problem ID 
                # in the main table's problemID field:
                problemID = answerToProblemMap[answerFKey] if answerToProblemMap[answerFKey] is not None else ''
                self.setValInRow('problem_id', problemID) 
            self.setValInRow('state_fk', stateFKey if stateFKey is not None else '')
            
            if len(self.currentEvent['correctMap_fk']) > 0:
                self.setValInRow('answer_identifier', correctMapTableDict[self.currentEvent['correctMap_fk']][1])
                self.setValInRow('correctness', correctMapTableDict[self.currentEvent['correctMap_fk']][2])
            else:
                self.setValInRow('answer_identifier', '')
                self.setValInRow('correctness', '')
                  
            if len(self.currentEvent['answer_fk']) > 0:
                self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
            else:
                self.setValInRow('answer', '')
                        
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
            indexToFKeys += 1
        # Return empty row, b/c we already pushed all necessary rows:
        self.currentEvent = {}

    def handleProblemCheckSimpleCase(self, event):
        '''
        Handle the simple case of problem_check type events. 
        Their event field has this form::
        
           "event": "\"input_i4x-Medicine-HRP258-problem-7451f8fe15a642e1820767db411a4a3e_2_1=choice_2&
                       input_i4x-Medicine-HRP258-problem-7451f8fe15a642e1820767db411a4a3e_3_1=choice_2\"", 
        The problems and proposed solutions are styled like HTTP GET request parameters.        

        :param row:
        :type row:
        :param event:
        :type event:
        '''
        # Easy case: event field is GET-styled list of problem ID/choices.
        # Separate all (&-separated) answers into strings like 'problem10=choice_2':
        problemAnswers = event.split('&')
        # Build a map problemID-->answer:
        answersDict = {}            
        for problemID_choice in problemAnswers:
            try:
                # Pull elements out from GET parameter strings like 'problemID=choice_2' 
                (problemID, answerChoice) = problemID_choice.split('=')
                answersDict[problemID] = self.makeInsertSafe(answerChoice)
            except ValueError:
                # Badly formatted GET parameter element:
                self.logWarn("Track log line %s: badly formatted problemID/answerChoice GET parameter pair: '%s'." %\
                             (self.makeFileCitation(), str(event)))
                return
        if len(answersDict) > 0:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        else:
            answersFKeys = []
        # Now need to generate enough near-replicas of event
        # entries to cover all answers, putting one Answer
        # table key into the answers foreign key column each
        # time:
        for answerFKey in answersFKeys:
            # Fill in one main table row.
            self.setValInRow('answer_fk', answerFKey)
            if answerFKey is not None:
                # For convenience: enter the Answer's problem ID 
                # in the main table's problemID field:
                problemID = answerToProblemMap[answerFKey]
                self.setValInRow('problem_id', problemID)
                # Try to look up the human readable display name
                # of the problem, and insert it into the main
                # table's resource_display_name field:
                self.setResourceDisplayName(problemID)
                self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
            else:
                self.setValInRow('answer', '')
                
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
            
        # Return empty row, b/c we already pushed all necessary rows:
        self.currentEvent = {}

    def pushCorrectMaps(self, correctMapsDict):
        '''
        Get dicts like this::
        
        {"i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {
                "hint": "",
                "hintmode": null,
                "correctness": "correct",
                "msg": "",
                "npoints": null,
                "queuestate": null
            },
            "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {
                "hint": "",
                "hintmode": null,
                "correctness": "correct",
                "msg": "",
                "npoints": null,
                "queuestate": null
            }
        }
        
        The above has two correctmaps.

        :param correctMapsDict: dict of CorrectMap dicts
        :type correctMapsDict: Dict<String, Dict<String,String>>
        :return: array of unique keys, one key for each CorrectMap row the method has added.
                 In case of the above example that would be two keys (uuids)

        :rtype: [String]
        '''
        # We'll create uuids for each new CorrectMap row
        # we create. We collect these uuids in the following
        # array, and return them to the caller. The caller
        # will then use them as foreign keys in the Event
        # table:
        correctMapUniqKeys = []
        correctMapTableDict = {}
        for answerKey in correctMapsDict.keys():
            answer_id = answerKey
            oneCorrectMapDict = correctMapsDict[answerKey]
            hint = oneCorrectMapDict.get('hint', '')
            if hint is None:
                hint = ''
            mode = oneCorrectMapDict.get('hintmode', '')
            if mode is None:
                mode = ''
            correctness = oneCorrectMapDict.get('correctness', '')
            if correctness is None:
                correctness = ''
            msg = oneCorrectMapDict.get('msg', '')
            if msg is None:
                msg = ''
            else:
                msg = self.makeInsertSafe(msg)
            npoints = oneCorrectMapDict.get('npoints', -1)
            if npoints is None:
                npoints = -1
            # queuestate:
            # Dict {key:'', time:''} where key is a secret string, and time is a string dump
            #        of a DateTime object in the format '%Y%m%d%H%M%S'. Is None when not queued
            queuestate = oneCorrectMapDict.get('queuestate', '')
            if queuestate is None:
                queuestate = ''
            if len(queuestate) > 0:
                queuestate_key  = queuestate.get('key', '')
                queuestate_time = queuestate.get('time', '')
                queuestate = queuestate_key + ":" + queuestate_time 
            
            # Unique key for the CorrectMap entry (and foreign
            # key for the Event table):
            correct_map_id = self.getUniqueID()
            correctMapUniqKeys.append(correct_map_id)
            correctMapValues = [correct_map_id,
                                answer_id,
                                correctness,
                                npoints,
                                msg,
                                hint,
                                mode,
                                queuestate]
            correctMapTableDict[correct_map_id] = correctMapValues
#            self.jsonToRelationConverter.pushToTable(self.resultTriplet(correctMapValues, 'CorrectMap', self.schemaCorrectMapTbl.keys()))
        # Return the array of RorrectMap row unique ids we just
        # created and pushed:
        return (correctMapUniqKeys, correctMapTableDict) 

    def pushAnswers(self, answersDict):
        '''
        Gets structure like this::
            "answers": {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": "choice_0",
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": "choice_3"
            }

        :param answersDict:
        :type answersDict:
        :return: array of keys created for answers in answersDict, and a dict mapping each key to the 
                 corresponding problem ID

        :rtype: ([String], Dict<String,String>
        '''
        answersKeys = []
        answerToProblemMap = {}
        answerTableDict = {}
        for problemID in answersDict.keys():
            answer = answersDict.get(problemID, None)
            # answer could be an array of Unicode strings, or
            # a single string: u'choice_1', or [u'choice_1'] or [u'choice_1', u'choice_2']
            # below: turn into latin1, comma separated single string.
            # Else Python prints the "u'" into the INSERT statement
            # and makes MySQL unhappy:
            if answer is not None:
                if isinstance(answer, list):
                    answer = self.makeInsertSafe(','.join(answer))
                else:
                    answer = self.makeInsertSafe(answer)
                answersKey = self.getUniqueID()
                answerToProblemMap[answersKey] = problemID
                answersKeys.append(answersKey)
                answerValues = [answersKey,          # answer_id fld 
                                problemID,           # problem_id fld
                                answer,
                                self.currCourseID
                                ]
                answerTableDict[answersKey] = answerValues
#                self.jsonToRelationConverter.pushToTable(self.resultTriplet(answerValues, 'Answer', self.schemaAnswerTbl.keys()))
        return (answersKeys, answerTableDict, answerToProblemMap)

    def pushState(self, stateDict):
        '''
        We get a structure like this::
        
        {   
            "student_answers": {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": "choice_3",
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": "choice_1"
            },
            "seed": 1,
            "done": true,
            "correct_map": {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {
                    "hint": "",
                    "hintmode": null,
                    "correctness": "incorrect",
                    "msg": "",
                    "npoints": null,
                    "queuestate": null
                },
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {
                    "hint": "",
                    "hintmode": null,
                    "correctness": "incorrect",
                    "msg": "",
                    "npoints": null,
                    "queuestate": null
                }
            },
            "input_state": {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {},
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {}
            }
        }        

        :param stateDict:
        :type stateDict:
        :return: array of keys into State table that were created in this method

        :rtype: [String]
        '''
        stateFKeys = []
        studentAnswersDict = stateDict.get('student_answers', None)
        if studentAnswersDict is not None:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            (studentAnswersFKeys, studentAnswersTableDict, answerToProblemMap) = self.pushAnswers(studentAnswersDict)  # @UnusedVariable
        else:
            studentAnswersFKeys = []
        seed = stateDict.get('seed', '')
        done = stateDict.get('done', '')
        # Can't use int for SQL, b/c Python writes as 'True'
        done = str(done)
        problemID = stateDict.get('problem_id', '')
        correctMapsDict = stateDict.get('correct_map', None)
        if correctMapsDict is not None:
            (correctMapFKeys, correctMapTableDict) = self.pushCorrectMaps(correctMapsDict)
        else:
            correctMapFKeys = []
        inputStatesDict = stateDict.get('input_state', None)
        if inputStatesDict is not None:
            inputStatesFKeys = self.pushInputStates(inputStatesDict)
        else:
            inputStatesFKeys = []

        # Now generate enough State rows to reference all student_answers,
        # correctMap, and input_state entries. That is, flatten the JSON
        # structure across relations State, Answer, CorrectMap, and InputState:
        generatedAllRows = False
        
        indexToFKeys = 0
        while not generatedAllRows:
            try:
                studentAnswerFKey = studentAnswersFKeys[indexToFKeys]
            except IndexError:
                studentAnswerFKey = None
            try:
                correctMapFKey = correctMapFKeys[indexToFKeys]
            except IndexError:
                correctMapFKey = None
            try:
                inputStateFKey = inputStatesFKeys[indexToFKeys]
            except IndexError:
                inputStateFKey = None
                
            # Have we created rows to cover all student_answers, correct_maps, and input_states?
            if studentAnswerFKey is None and correctMapFKey is None and inputStateFKey is None:
                generatedAllRows = True
                continue
            
            studentAnswerFKey = studentAnswerFKey if studentAnswerFKey is not None else ''
            correctMapFKey = correctMapFKey if correctMapFKey is not None else ''
            inputStateFKey = inputStateFKey if inputStateFKey is not None else ''
            # Unique ID that ties all these related rows together:
            state_id = self.getUniqueID()
            stateFKeys.append(state_id)
            stateValues = [state_id, seed, done, problemID, studentAnswerFKey, correctMapFKey, inputStateFKey]
# TOFIX
#            rowInfoTriplet = self.resultTriplet(stateValues, 'State', self.schemaStateTbl.keys())
#            self.jsonToRelationConverter.pushToTable(rowInfoTriplet)
            indexToFKeys += 1
            
        return stateFKeys
        
    def pushInputStates(self, inputStatesDict):
        '''
        Gets structure like this::
        
            {
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_3_1": {},
                "i4x-Medicine-HRP258-problem-e194bcb477104d849691d8b336b65ff6_2_1": {}
            }        

        :param inputStatesDict:
        :type inputStatesDict:
        :return: array of keys created for input state problems.

        :rtype: [String]
        '''
        inputStateKeys = []
        for problemID in inputStatesDict.keys():
            inputStateProbVal = inputStatesDict.get(problemID, None)
            if inputStateProbVal is not None:
                # If prob value is an empty dict (as in example above),
                # then make it an empty str, else the value will show up as
                # {} in the VALUES part of the INSERT statements, and
                # MySQL will get cranky:
                try:
                    if len(inputStateProbVal) == 0:
                        inputStateProbVal = ''
                except:
                    pass
                inputStateKey = self.getUniqueID()
                inputStateKeys.append(inputStateKey)
                inputStateValues = [inputStateKey,
                                    problemID,
                                    inputStateProbVal
                                    ]
#                self.jsonToRelationConverter.pushToTable(self.resultTriplet(inputStateValues, 'InputState', self.schemaInputStateTbl.keys()))
        return inputStateKeys
        
    def pushEventIpInfo(self, eventIpDict):
        '''
        Takes an ordered dict with two fields:
        the _id field of the current main table event
        under key event_table_id, and an IP address.
        
        :param eventCountryDict: dict with main table _id, and 3-char country code 
        :type eventCountryDict: {String : String}
        '''
#        self.jsonToRelationConverter.pushToTable(self.resultTriplet(eventIpDict.values(), 'EventIp', self.schemaEventIpTbl.keys()))
        return

    def pushABExperimentInfo(self, abExperimentDict):
        '''
        Takes an ordered dict with  fields:
           - 'event_table_id' : EdxTrackEvent _id field
           - 'event_type      : type of event that caused need for this row
           - 'group_id'       : experimental group's ID
           - 'group_name'     : experimental group's name
           - 'partition_id'   : experimental partition's id
           - 'partition_name' : experimental partition's name
           - 'child_module_id': id of module within partition that was served to a participant

        :param abExperimentDict: Ordered dict with all required ABExperiment table column values 
        :type abExperimentDict: {STRING : STRING, STRING : INT, STRING : STRING, STRING : INT, STRING : STRING, STRING : STRING} 
        '''
        str(abExperimentDict['event_type'])
#        self.jsonToRelationConverter.pushToTable(self.resultTriplet(abExperimentDict.values(), 'ABExperiment', self.schemaABExperimentTbl.keys()))
        return
        
    def pushAccountInfo(self, accountDict):
        '''
        Takes an ordered dict with the fields of
        a create_account event. Pushes the values
        (name, address, email, etc.) as a row to the
        Account table, and returns the resulting row
        primary key for inclusion in the main table's
        accountFKey field. 

        :param accountDict:
        :type accountDict:
        '''
        accountDict['account_id'] = self.getUniqueID()
#        self.jsonToRelationConverter.pushToTable(self.resultTriplet(accountDict.values(), 'Account', self.schemaAccountTbl.keys()))
        return
        
    def pushLoadInfo(self, loadDict):
        #loadDict['load_info_id'] = self.getUniqueID()
        # Make the primary-key row ID from the load file
        # basename, so that it is reproducible:
        loadDict['load_info_id'] = self.hashGeneral(loadDict['load_file'])
#        self.jsonToRelationConverter.pushToTable(self.resultTriplet(loadDict.values(), 'LoadInfo', self.schemaLoadInfoTbl.keys()))
        return loadDict['load_info_id']
    
    def handleProblemReset(self, record, event):
        '''
        Gets a event string like this::
        
           "{\"POST\": {\"id\": [\"i4x://Engineering/EE222/problem/e68cfc1abc494dfba585115792a7a750@draft\"]}, \"GET\": {}}"
           
        After turning this JSON into Python::
        
           {u'POST': {u'id': [u'i4x://Engineering/EE222/problem/e68cfc1abc494dfba585115792a7a750@draft']}, u'GET': {}}
        
        Or the event could be simpler, like this::
        
           u'input_i4x-Engineering-QMSE01-problem-dce5fe9e04be4bc1932efb05a2d6db68_2_1=2'
           
        In the latter case we just put that string into the problemID field
        of the main table
        
        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event type problem_reset." %\
                         (self.makeFileCitation()))
            return
        
        # From "{\"POST\": {\"id\": [\"i4x://Engineering/EE368/problem/ab656f3cb49e4c48a6122dc724267cb6@draft\"]}, \"GET\": {}}"
        # make a dict:
        postGetDict = self.ensureDict(event)
        if postGetDict is None:
            if isinstance(event, basestring):
                self.setValInRow('problem_id', event)
                # Try to look up the human readable display name
                # of the problem, and insert it into the main
                # table's resource_display_name field:
                self.setResourceDisplayName(event)
                
                return
            else:
                self.logWarn("Track log line %s: event is not a dict in problem_reset event: '%s'" %\
                             (self.makeFileCitation(), str(event)))
                return
    
        # Get the POST field's problem id array:
        try:
            problemIDs = postGetDict['POST']['id']
        except KeyError:
            self.logWarn("Track log line %s with event type problem_reset contains event without problem ID array: '%s'" %
                         (self.makeFileCitation(), event))
        self.setValInRow('problem_id', problemIDs)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problemIDs)

    def handleProblemShow(self, record, event):
        '''
        Gets a event string like this::
        
         "{\"problem\":\"i4x://Medicine/HRP258/problem/c5cf8f02282544729aadd1f9c7ccbc87\"}"
        
        After turning this JSON into Python::
        
        {u'problem': u'i4x://Medicine/HRP258/problem/c5cf8f02282544729aadd1f9c7ccbc87'}

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event type problem_show." %\
                         (self.makeFileCitation()))
            return

        # From "{\"POST\": {\"id\": [\"i4x://Engineering/EE368/problem/ab656f3cb49e4c48a6122dc724267cb6@draft\"]}, \"GET\": {}}"
        # make a dict:
        postGetDict = self.ensureDict(event)
        if postGetDict is None:
            self.logWarn("Track log line %s: event is not a dict in problem_show event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        # Get the problem id:
        try:
            problemID = postGetDict['problem']
        except KeyError:
            self.logWarn("Track log line %s with event type problem_show contains event without problem ID: '%s'" %
                         (self.makeFileCitation(), event))
            return
        self.setValInRow('problem_id', problemID)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problemID)

    def handleProblemSave(self, record, event):
        '''
        Gets a event string like this::
        
           "\"input_i4x-Medicine-HRP258-problem-44c1ef4e92f648b08adbdcd61d64d558_2_1=13.4&
              input_i4x-Medicine-HRP258-problem-44c1ef4e92f648b08adbdcd61d64d558_3_1=2.49&
              input_i4x-Medicine-HRP258-problem-44c1ef4e92f648b08adbdcd61d64d558_4_1=13.5&
              input_i4x-Medicine-HRP258-problem-44c1ef4e92f648b08adbdcd61d64d558_5_1=3\""        
                   
        After splitting this string on '&', and then each result on '=', we add the 
        problemID/solution pairs to the Answer table:

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event type problem_save." %\
                         (self.makeFileCitation()))
            return

        if not isinstance(event, basestring):
            self.logWarn("Track log line %s: event is not a string in problem save event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        probIDSolPairs = event.split('&')
        answersDict = {}
        for probIDSolPair in probIDSolPairs: 
            (problemID, choice) = probIDSolPair.split('=')
            answersDict[problemID] = choice

        # Add answer/solutions to Answer table.
        # Receive all the Answer table keys generated for
        # the answers, and a dict mapping each key
        # to the problem ID to which that key's row
        # in the Answer refers:
        if len(answersDict) > 0:
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        else:
            answersFKeys = []

        # Now need to generate enough near-replicas of event
        # entries to cover all answer 
        # foreign key entries that were created:
        for answerFKey in answersFKeys: 
            # Fill in one main table row.
            self.setValInRow('answer_fk', answerFKey)
            if answerFKey is not None:
                # For convenience: enter the Answer's problem ID 
                # in the main table's problemID field:
                problemID = answerToProblemMap[answerFKey]
                self.setValInRow('problem_id', problemID)
                # Try to look up the human readable display name
                # of the problem, and insert it into the main
                # table's resource_display_name field:
                self.setResourceDisplayName(problemID)
                self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
                self.pushEvent()
                # The next row keeps its eventID, but needs its own
                # primary key (in _id):
                self.setValInRow('_id', self.getUniqueID())
            else:
                self.setValInRow('answer', '')                

        # Return empty row, b/c we already pushed all necessary rows:
        self.currentEvent = {}


    def handleQuestionProblemHidingShowing(self, record, event):
        '''
        Gets a event string like this::
        
        "{\"location\":\"i4x://Education/EDUC115N/combinedopenended/c8af7daea1f54436b0b25930b1631845\"}"
        
        After importing from JSON into Python::
        
        {u'location': u'i4x://Education/EDUC115N/combinedopenended/c8af7daea1f54436b0b25930b1631845'}
        
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in question hide or show." %\
                         (self.makeFileCitation()))
            return

        "{\"location\":\"i4x://Education/EDUC115N/combinedopenended/4abb8b47b03d4e3b8c8189b3487f4e8d\"}"
        # make a dict:
        locationDict = self.ensureDict(event)
        if locationDict is None:
            self.logWarn("Track log line %s: event is not a dict in problem_show/hide event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        # Get location:
        try:
            location = locationDict['location']
        except KeyError:
            self.logWarn("Track log line %s: no location field provided in problem hide or show event: '%s'" %\
             (self.makeFileCitation(), str(event)))
            return

        self.setValInRow('question_location', location)        
        
    def handleRubricSelect(self, record, event):
        '''
        Gets a event string like this::
        
        "{\"location\":\"i4x://Education/EDUC115N/combinedopenended/4abb8b47b03d4e3b8c8189b3487f4e8d\",\"selection\":\"1\",\"category\":0}"
        {u'category': 0, u'selection': u'1', u'location': u'i4x://Education/EDUC115N/combinedopenended/4abb8b47b03d4e3b8c8189b3487f4e8d'}
        
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in select_rubric." %\
                         (self.makeFileCitation()))
            return

        # From "{\"location\":\"i4x://Education/EDUC115N/combinedopenended/4abb8b47b03d4e3b8c8189b3487f4e8d\",\"selection\":\"1\",\"category\":0}"
        # make a dict:
        locationDict = self.ensureDict(event)
        if locationDict is None:
            self.logWarn("Track log line %s: event is not a dict in select_rubric event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        try:
            location = locationDict['location']
            selection = locationDict['selection']
            category = locationDict['category']
        except KeyError:
            self.logWarn("Track log line %s: missing location, selection, or category in event type select_rubric." %\
                         (self.makeFileCitation()))
            return
        self.setValInRow('question_location', location)
        self.setValInRow('rubric_selection', selection)
        self.setValInRow('rubric_category', category)

    def handleOEShowFeedback(self, record, event):
        '''
        All examples seen as of this writing had this field empty: "{}"
        '''
        # Just stringify the dict and make it the field content:
        self.setValInRow('feedback', str(event))
        
    def handleOEFeedbackResponseSelected(self, record, event):
        '''
        Gets a event string like this::
        
            "event": "{\"value\":\"5\"}"
            
        After JSON import into Python::
        
            {u'value': u'5'}
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in oe_feedback_response_selected." %\
                         (self.makeFileCitation()))
            return
        
        # From "{\"value\":\"5\"}"
        # make a dict:
        valDict = self.ensureDict(event)
        if valDict is None:
            self.logWarn("Track log line %s: event is not a dict in oe_feedback_response_selected event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        try:
            value = valDict['value']
        except KeyError:
            self.logWarn("Track log line %s: missing 'value' field in event type oe_feedback_response_selected." %\
                         (self.makeFileCitation()))
            return
        self.setValInRow('feedback_response_selected', value)

    def handleVideoPlayPause(self, record, event):
        '''
        For play_video, event looks like this::
        
            "{\"id\":\"i4x-Education-EDUC115N-videoalpha-c41e588863ff47bf803f14dec527be70\",\"code\":\"html5\",\"currentTime\":0}"
            
        For pause_video::
        
            "{\"id\":\"i4x-Education-EDUC115N-videoalpha-c5f2fd6ee9784df0a26984977658ad1d\",\"code\":\"html5\",\"currentTime\":124.017784}"
            
        For load_video::
        
            "{\"id\":\"i4x-Education-EDUC115N-videoalpha-003bc44b4fd64cb79cdfd459e93a8275\",\"code\":\"4GlF1t_5EwI\"}"
            
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in video play or pause." %\
                         (self.makeFileCitation()))
            return

        valsDict = self.ensureDict(event) 
        if valsDict is None:
            self.logWarn("Track log line %s: event is not a dict in video play/pause: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        videoID = valsDict.get('id', None)
        self.setResourceDisplayName(videoID)
        videoCode = valsDict.get('code', None)
        videoCurrentTime = str(valsDict.get('currentTime', None))
        videoSpeed = str(valsDict.get('speed', None))

        self.setValInRow('video_id', str(videoID))
        self.setValInRow('video_code', str(videoCode))
        self.setValInRow('video_current_time', str(videoCurrentTime))
        self.setValInRow('video_speed', str(videoSpeed))

    def handleVideoSeek(self, record, event):
        '''
        For play_video, event looks like this::
        
           "{\"id\":\"i4x-Medicine-HRP258-videoalpha-413d6a45b82848339ab5fd3836dfb928\",
             \"code\":\"html5\",
             \"old_time\":308.506103515625,
             \"new_time\":290,
             \"type\":\"slide_seek\"}"
                     
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in video seek." %\
                         (self.makeFileCitation()))
            return

        valsDict = self.ensureDict(event) 
        if valsDict is None:
            self.logWarn("Track log line %s: event is not a dict in video play/pause: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        videoID = valsDict.get('id', None)
        self.setResourceDisplayName(videoID)
        videoCode = valsDict.get('code', None)
        videoOldTime = str(valsDict.get('old_time', None))
        videoNewTime = str(valsDict.get('new_time', None))
        videoSeekType = valsDict.get('type', None)
            
        self.setValInRow('video_id', videoID)
        self.setValInRow('video_code', videoCode)
        self.setValInRow('video_old_time', videoOldTime)
        self.setValInRow('video_new_time', videoNewTime)
        self.setValInRow('video_seek_type', videoSeekType)

    def handleVideoSpeedChange(self, record, event):
        '''
        Events look like this::
        
           "{\"id\":\"i4x-Medicine-HRP258-videoalpha-7cd4bf0813904612bcd583a73ade1d54\",
             \"code\":\"html5\",
             \"currentTime\":1.6694719791412354,
             \"old_speed\":\"1.50\",
             \"new_speed\":\"2.0\"}"
                     
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in video speed change." %\
                         (self.makeFileCitation()))
            return

        valsDict = self.ensureDict(event) 
        if valsDict is None:
            self.logWarn("Track log line %s: event is not a dict in video speed change: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        videoID = valsDict.get('id', None)
        self.setResourceDisplayName(videoID)
        videoCode = valsDict.get('code', None)
        videoCurrentTime = str(valsDict.get('currentTime', None))
        videoOldSpeed = str(valsDict.get('old_speed', None))
        videoNewSpeed = str(valsDict.get('new_speed', None))
            
        self.setValInRow('video_id', videoID)
        self.setValInRow('video_code', videoCode)
        self.setValInRow('video_current_time', videoCurrentTime)
        self.setValInRow('video_old_speed', videoOldSpeed)
        self.setValInRow('video_new_speed', videoNewSpeed)

    def handleFullscreen(self, record, event):
        '''
        Events look like this::
        
           "{\"id\":\"i4x-Medicine-HRP258-videoalpha-4b200d3944cc47e5ae3ad142c1006075\",\"code\":\"html5\",\"currentTime\":348.4132080078125}"    

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text event type fullscreen." %\
                         (self.makeFileCitation()))
            return

        valsDict = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in fullscreen: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        videoID = valsDict.get('id', None)
        self.setResourceDisplayName(videoID)
        videoCode = valsDict.get('code', None)
        videoCurrentTime = str(valsDict.get('currentTime', None))

        self.setValInRow('video_id', videoID)
        self.setValInRow('video_code', videoCode)
        self.setValInRow('video_current_time', videoCurrentTime)
        
    def handleNotFullscreen(self, record, event):
        '''
        Events look like this::
        
           "{\"id\":\"i4x-Medicine-HRP258-videoalpha-c5cbefddbd55429b8a796a6521b9b752\",\"code\":\"html5\",\"currentTime\":661.1010131835938}"        

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text event type fullscreen." %\
                         (self.makeFileCitation()))
            return

        valsDict = self.ensureDict(event) 
        if valsDict is None:
            self.logWarn("Track log line %s: event is not a dict in not_fullscreen: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        videoID = valsDict.get('id', None)
        self.setResourceDisplayName(videoID)
        videoCode = valsDict.get('code', None)
        videoCurrentTime = str(valsDict.get('currentTime', None))

        self.setValInRow('video_id', videoID)
        self.setValInRow('video_code', videoCode)
        self.setValInRow('video_current_time', videoCurrentTime)
    
    def handleBook(self, record, event):
        '''
        No example of book available
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in book event type." %\
                         (self.makeFileCitation()))
            return
        
        # Make a dict from the string:
        valsDict = self.ensureDict(event)
        if valsDict is None:
            self.logWarn("Track log line %s: event is not a dict in book event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        bookInteractionType = valsDict.get('type', None)
        bookOld = valsDict.get('old', None)
        bookNew = valsDict.get('new', None)
        if bookInteractionType is not None:
            self.setValInRow('book_interaction_type', bookInteractionType)
        if bookOld is not None:            
            self.setValInRow('goto_from', bookOld)
        if bookNew is not None:            
            self.setValInRow('goto_dest', bookNew)
        
    def handleShowAnswer(self, record, event):
        '''
        Gets a event string like this::
        
        {"problem_id": "i4x://Medicine/HRP258/problem/28b525192c4e43daa148dc7308ff495e"}
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in showanswer." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in handle showanswer event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        try:
            problem_id = event['problem_id']
        except KeyError:
            self.logWarn("Track log line %s: showanswer event does not include a problem ID: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        self.setValInRow('problem_id', problem_id)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problem_id)

    def handleShowHideTranscript(self, record, event):
        '''
        Events look like this::
        
            "{\"id\":\"i4x-Medicine-HRP258-videoalpha-c26e4247f7724cc3bc407a7a3541ed90\",
              \"code\":\"q3cxPJGX4gc\",
              \"currentTime\":0}"
              
        Same for hide_transcript

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event info in show_transcript or hide_transcript." %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in show_transcript or hide_transcript: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        xcriptID = event.get('id', None)
        code  = event.get('code', None)
        self.setValInRow('transcript_id', xcriptID)
        self.setValInRow('transcript_code', code)        

    def handleProblemCheckFail(self, record, event):
        '''
        Gets events like this::
        
            {
              "failure": "unreset",
              "state": {
                "student_answers": {
                  "i4x-Education-EDUC115N-problem-ab38a55d2eb145ae8cec26acebaca27f_2_1": "choice_0"
                },
                "seed": 89,
                "done": true,
                "correct_map": {
                  "i4x-Education-EDUC115N-problem-ab38a55d2eb145ae8cec26acebaca27f_2_1": {
                    "hint": "",
                    "hintmode": null,
                    "correctness": "correct",
                    "msg": "",
                    "npoints": null,
                    "queuestate": null
                  }
                },
                "input_state": {
                  "i4x-Education-EDUC115N-problem-ab38a55d2eb145ae8cec26acebaca27f_2_1": {
                    
                  }
                }
              },
              "problem_id": "i4x:\/\/Education\/EDUC115N\/problem\/ab38a55d2eb145ae8cec26acebaca27f",
              "answers": {
                "i4x-Education-EDUC115N-problem-ab38a55d2eb145ae8cec26acebaca27f_2_1": "choice_0"
              }
            }        

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in problem_check event." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in handle problem_check event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        problem_id = event.get('problem_id', None)
        success    = event.get('failure', None)  # 'closed' or 'unreset'
        self.setValInRow('problem_id', problem_id)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problem_id)
        
        self.setValInRow('success', success)
        
        answersDict = event.get('answers', None)
        stateDict = event.get('state', None)
        
        if isinstance(answersDict, dict) and len(answersDict) > 0:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        else:
            answersFKeys = []
            
        if isinstance(stateDict, dict) and len(stateDict) > 0:
            stateFKeys = self.pushState(stateDict)
        else:
            stateFKeys = []
            
        generatedAllRows = False
        indexToFKeys = 0
        # Generate main table rows that refer to all the
        # foreign entries we made above to tables Answer, and State
        # We make as few rows as possible by filling in 
        # columns in all three foreign key entries, until
        # we run out of all references:
        while not generatedAllRows:
            try:
                answerFKey = answersFKeys[indexToFKeys]
            except IndexError:
                answerFKey = None
            try:
                stateFKey = stateFKeys[indexToFKeys]
            except IndexError:
                stateFKey = None
            
            # Have we created rows to cover all answers, and states?
            if answerFKey is None and stateFKey is None:
                generatedAllRows = True
                continue

            # Fill in one main table row.
            self.setValInRow('answer_fk', answerFKey if answerFKey is not None else '')
            if answerFKey is not None:
                # For convenience: enter the Answer's problem ID 
                # in the main table's problemID field:
                problemID = answerToProblemMap[answerFKey] if answerToProblemMap[answerFKey] is not None else ''
                self.setValInRow('problem_id', problemID)
                # Try to look up the human readable display name
                # of the problem, and insert it into the main
                # table's resource_display_name field:
                self.setResourceDisplayName(problemID)
                self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
            else:
                self.setValInRow('answer', '')                
                
            self.setValInRow('state_fk', stateFKey if stateFKey is not None else '')
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
            indexToFKeys += 1

    def handleProblemRescoreFail(self, record, event):
        '''
        No example available. Records reportedly include:
        state, problem_id, and failure reason

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event info in problem_rescore_fail." %\
                         (self.makeFileCitation()))
            return
        problem_id = event.get('problem_id', None)
        failure    = event.get('failure', None)  # 'closed' or 'unreset'
        self.setValInRow('problem_id', problem_id)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problem_id)
        
        self.setValInRow('failure', failure)
        
        stateDict = event.get('state', None)
        
        if isinstance(stateDict, dict) and len(stateDict) > 0:
            stateFKeys = self.pushState(stateDict)
        else:
            stateFKeys = []
        for stateFKey in stateFKeys:
            # Fill in one main table row.
            self.setValInRow('state_fk', stateFKey)
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
        self.currentEvent = {}

    def handleProblemRescore(self, record, event):
        '''
        No example available
        Fields: state, problemID, orig_score (int), orig_total(int), new_score(int),
        new_total(int), correct_map, success (string 'correct' or 'incorrect'), and
        attempts(int)

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in problem_rescore event." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in handle problem_rescore event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        problem_id = event.get('problem_id', None)
        success    = event.get('success', None)  # 'correct' or 'incorrect'
        attempts   = event.get('attempts', None)
        orig_score = event.get('orig_score', None)
        orig_total = event.get('orig_total', None)
        new_score  = event.get('new_score', None)
        new_total  = event.get('new_total', None)
        correctMapsDict = event.get('correct_map', None)
        
        # Store the top-level vals in the main table:
        self.setValInRow('problem_id', problem_id)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problem_id)
        self.setValInRow('success', success)
        self.setValInRow('attempts', attempts)
        self.setValInRow('orig_score', orig_score)
        self.setValInRow('orig_total', orig_total)
        self.setValInRow('new_score', new_score)
        self.setValInRow('new_total', new_total)
        
        # And the correctMap, which goes into a different table:
        if isinstance(correctMapsDict, dict) and len(correctMapsDict) > 0:
            (correctMapsFKeys, correctMapTableDict) = self.pushCorrectMaps(correctMapsDict)
        else:
            correctMapsFKeys = []

        # Replicate main table row if needed:            
        for correctMapFKey in correctMapsFKeys:
            # Fill in one main table row.
            self.setValInRow('correctMap_fk', correctMapFKey)
            if len(self.currentEvent['correctMap_fk']) > 0:
                self.setValInRow('answer_identifier', correctMapTableDict[self.currentEvent['correctMap_fk']][1])
                self.setValInRow('correctness', correctMapTableDict[self.currentEvent['correctMap_fk']][2])
            else:
                self.setValInRow('answer_identifier', '')
                self.setValInRow('correctness', '')
            
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
        self.currentEvent = {}
         
    def handleSaveProblemFailSuccessCheckOrReset(self, record, event):
        '''
        Do have examples. event has fields state, problem_id, failure, and answers.
        For save_problem_success or save_problem_check there is no failure field 

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in save_problem_fail, save_problem_success, or reset_problem_fail." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in handle save_problem_fail, save_problem_success, or reset_problem_fail event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        problem_id = event.get('problem_id', None)
        success    = event.get('failure', None)  # 'closed' or 'unreset'
        if success is None:
            success = event.get('success', None) # 'incorrect' or 'correct'
        self.setValInRow('problem_id', problem_id)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problem_id)
        
        self.setValInRow('success', success)
        
        answersDict = event.get('answers', None)
        stateDict = event.get('state', None)
        
        if isinstance(answersDict, dict) and len(answersDict) > 0:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        else:
            answersFKeys = []
            
        if isinstance(stateDict, dict) and len(stateDict) > 0:
            stateFKeys = self.pushState(stateDict)
        else:
            stateFKeys = []
            
        generatedAllRows = False
        indexToFKeys = 0
        # Generate main table rows that refer to all the
        # foreign entries we made above to tables Answer, and State
        # We make as few rows as possible by filling in 
        # columns in all three foreign key entries, until
        # we run out of all references:
        while not generatedAllRows:
            try:
                answerFKey = answersFKeys[indexToFKeys]
            except IndexError:
                answerFKey = None
            try:
                stateFKey = stateFKeys[indexToFKeys]
            except IndexError:
                stateFKey = None
            
            # Have we created rows to cover all answers, and states?
            if answerFKey is None and stateFKey is None:
                generatedAllRows = True
                continue

            # Fill in one main table row.
            self.setValInRow('answer_fk', answerFKey if answerFKey is not None else '')
            if answerFKey is not None:
                # For convenience: enter the Answer's problem ID 
                # in the main table's problemID field:
                problemID = answerToProblemMap[answerFKey] if answerToProblemMap[answerFKey] is not None else ''
                self.setValInRow('problem_id', problemID)
                # Try to look up the human readable display name
                # of the problem, and insert it into the main
                # table's resource_display_name field:
                self.setResourceDisplayName(problemID)
                self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
            else:
                self.setValInRow('answer', '')
                
            self.setValInRow('state_fk', stateFKey if stateFKey is not None else '')
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
            indexToFKeys += 1
        self.currentEvent = {}
        
    def handleResetProblem(self, record, event):
        '''
        Events look like this::
        
            {"old_state": 
                {"student_answers": {"i4x-HMC-MyCS-problem-d457165577d34e5aac6fbb55c8b7ad33_2_1": "choice_2"}, 
                 "seed": 811, 
                 "done": true, 
                 "correct_map": {"i4x-HMC-MyCS-problem-d457165577d34e5aac6fbb55c8b7ad33_2_1": {"hint": "", 
                                                                                               "hintmode": null, 
                                                                                               ...
                                                    }}, 
                
              "problem_id": "i4x://HMC/MyCS/problem/d457165577d34e5aac6fbb55c8b7ad33", 
              "new_state": {"student_answers": {}, "seed": 93, "done": false, "correct_map": {}, "input_state": {"i4x-HMC-MyCS-problem-d457165577d34e5aac6fbb55c8b7ad33_2_1": {}}}}   

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in reset_problem." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in handle reset_problem event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        self.setValInRow('problem_id',event.get('problem_id', '')) 
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(event.get('problem_id', ''))
        
        oldStateDict = event.get('old_state', None)
        newStateDict = event.get('new_state', None)
        
        stateFKeys = []
        if isinstance(oldStateDict, dict) and len(oldStateDict) > 0:
            stateFKeys.extend(self.pushState(oldStateDict))
        if isinstance(newStateDict, dict) and len(newStateDict) > 0:
            stateFKeys.extend(self.pushState(newStateDict))
            
        for stateFKey in stateFKeys:
            # Fill in one main table row.
            self.setValInRow('state_fk', stateFKey if stateFKey is not None else '')
            self.pushEvent()
            # The next row keeps its eventID, but needs its own
            # primary key (in _id):
            self.setValInRow('_id', self.getUniqueID())
        self.currentEvent = {}

    def handleRescoreReset(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in rescore-all-submissions or reset-all-attempts." %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in handle resource event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        courseID = event.get('course', '')
        if len(courseID) == 0:
            self.logWarn("Track log line %s: missing course ID in rescore-all-submissions or reset-all-attempts." %\
                         (self.makeFileCitation()))
        problemID = event.get('problem', '')
        if len(problemID) == 0:
            self.logWarn("Track log line %s: missing problem ID in rescore-all-submissions or reset-all-attempts." %\
                         (self.makeFileCitation()))
        
        self.setValInRow('course_id', courseID)
        self.setValInRow('problem_id', problemID)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problemID)                
                
    def handleDeleteStateRescoreSubmission(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in delete-student-module-state or rescore-student-submission." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:

            self.logWarn("Track log line %s: event is not a dict in delete-student-module-state or rescore-student-submission event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        courseID  = event.get('course', '')
        problemID = event.get('problem', '')
        studentID = event.get('student', '')
        if courseID is None:
            self.logWarn("Track log line %s: missing course ID in delete-student-module-state or rescore-student-submission." %\
                         (self.makeFileCitation()))
        if problemID is None:
            self.logWarn("Track log line %s: missing problem ID in delete-student-module-state or rescore-student-submission." %\
                         (self.makeFileCitation()))
        if studentID is None:
            self.logWarn("Track log line %s: missing student ID in delete-student-module-state or rescore-student-submission." %\
                         (self.makeFileCitation()))
        self.setValInRow('course_id', courseID)
        self.setValInRow('problem_id', problemID)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problemID)
        self.setValInRow('student_id', studentID)
        
    def handleResetStudentAttempts(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in reset-student-attempts." %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in reset-student-attempt event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        problemID = event.get('problem', '')
        studentID = event.get('student', '')
        instructorID = event.get('instructor_id', '')
        attempts = event.get('old_attempts', -1)
        if len(problemID) == 0:
            self.logWarn("Track log line %s: missing problem ID in reset-student-attempts." %\
                         (self.makeFileCitation()))
        if len(studentID) == 0:
            self.logWarn("Track log line %s: missing student ID in reset-student-attempts." %\
                         (self.makeFileCitation()))
        if len(instructorID) == 0:
            self.logWarn("Track log line %s: missing instrucotrIDin reset-student-attempts." %\
                         (self.makeFileCitation()))
        if attempts < 0:
            self.logWarn("Track log line %s: missing attempts field in reset-student-attempts." %\
                         (self.makeFileCitation()))
            
        self.setValInRow('problem_id', problemID)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problemID)
        self.setValInRow('student_id', studentID)        
        self.setValInRow('instructor_id', instructorID)
        self.setValInRow('attempts', attempts)
        
    def handleGetStudentProgressPage(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in get-student-progress-page." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in get-student-progress-page event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        studentID = event.get('student', None)
        instructorID = event.get('instructor_id', None)
        
        if studentID is None:
            self.logWarn("Track log line %s: missing student ID in get-student-progress-page." %\
                         (self.makeFileCitation()))
        if instructorID is None:
            self.logWarn("Track log line %s: missing instrucotrID in get-student-progress-page." %\
                         (self.makeFileCitation()))
            
        self.setValInRow('student_id', studentID)        
        self.setValInRow('instructor_id', instructorID)

    def handleAddRemoveInstructor(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in add-instructor or remove-instructor." %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in add-instructor or remove-instructor event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        instructorID = event.get('instructor_id', None)

        if instructorID is None:
            self.logWarn("Track log line %s: missing instrucotrID add-instructor or remove-instructor." %\
                         (self.makeFileCitation()))
        self.setValInRow('instructor_id', instructorID)
        
    def handleListForumMatters(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in list-forum-admins, list-forum-mods, or list-forum-community-TAs." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in list-forum-admins, list-forum-mods, or list-forum-community-TAs event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
    def handleForumManipulations(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in one of remove-forum-admin, add-forum-admin, " +\
                         "remove-forum-mod, add-forum-mod, remove-forum-community-TA, or add-forum-community-TA." %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in one of handle forum manipulations event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        screen_name  = event.get('username', None)

        if screen_name is None:
            self.logWarn("Track log line %s: missing screen_name in one of remove-forum-admin, add-forum-admin, " +\
                         "remove-forum-mod, add-forum-mod, remove-forum-community-TA, or add-forum-community-TA." %\
                         (self.makeFileCitation()))
            
        self.setValInRow('screen_name', self.hashGeneral(screen_name))        

    def handlePsychometricsHistogramGen(self, record, event):
        if event is None:
            self.logWarn("Track log line %s: missing event info in psychometrics-histogram-generation." %\
                         (self.makeFileCitation()))
            return
        
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in psychometrics-histogram-generation event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        problemID = event.get('problem', None)
        
        if problemID is None:
            self.logWarn("Track log line %s: missing problemID in pyschometrics-histogram-generation event." %\
                         (self.makeFileCitation()))
        self.setValInRow('problem_id', problemID)
        # Try to look up the human readable display name
        # of the problem, and insert it into the main
        # table's resource_display_name field:
        self.setResourceDisplayName(problemID)
    
    def handleAddRemoveUserGroup(self, record, event):
        '''
        This event looks like this::
        
           {"event_name": "beta-tester", 
            "user": "smith", 
            "event": "add"}
        Note that the 'user' is different from the screen_name. The latter triggered
        the event. User is the group member being talked about. For clarity,
        'user' is called 'group_user', and 'event' is called 'group_event' in the
        main table.

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event info add-or-remove-user-group" %\
                         (self.makeFileCitation()))
            return

        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in add-or-remove-user-group event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        eventName  = event.get('event_name', None)
        user  = event.get('user', None)
        event = event.get('event', None)

        if eventName is None:
            self.logWarn("Track log line %s: missing event_name in add-or-remove-user-group." %\
                         (self.makeFileCitation()))
        if user is None:
            self.logWarn("Track log line %s: missing user field in add-or-remove-user-group." %\
                         (self.makeFileCitation()))
        if event is None:
            self.logWarn("Track log line %s: missing event field in add-or-remove-user-group." %\
                         (self.makeFileCitation()))
            
        self.setValInRow('event_name', eventName)
        self.setValInRow('group_user', user)
        self.setValInRow('group_action', event)
    
    def handleCreateAccount(self, record, event):
        '''
        Get event structure like this (fictitious values)::
        
           "{\"POST\": {\"username\": [\"luisXIV\"], 
                        \"name\": [\"Roy Luigi Cannon\"], 
                        \"mailing_address\": [\"3208 Dead St\\r\\nParis, GA 30243\"], 
                        \"gender\": [\"f\"], 
                        \"year_of_birth\": [\"1986\"], 
                        \"level_of_education\": [\"p\"], 
                        \"goals\": [\"flexibility, cost, 'prestige' and course of study\"], 
                        \"honor_code\": [\"true\"], 
                        \"terms_of_service\": [\"true\"], 
                        \"course_id\": [\"Medicine/HRP258/Statistics_in_Medicine\"], 
                        \"password\": \"********\", 
                        \"enrollment_action\": [\"enroll\"], 
                        \"email\": [\"luig.cannon@yahoo.com\"]}, \"GET\": {}}"        

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event type create_account." %\
                         (self.makeFileCitation()))
            return
        
        try:
            # From {\"POST\": {\"username\": ... , \"GET\": {}}
            # get the inner dict, i.e. the value of 'POST':
            # Like this:
            # {'username': ['luisXIV'], 
            #  'mailing_address': ['3208 Dead St\r\nParis, GA 30243'], 
            #  ...
            # }
            postDict = event['POST']
        except Exception as e:
            self.logWarn("Track log line %s: event is not a dict in create_account event: '%s' (%s)" %\
                         (self.makeFileCitation(), str(event), `e`))
            return

        # Get the POST field's entries into an ordered
        # dict as expected by pushAccountInfo():
        accountDict = OrderedDict()
        accountDict['account_id'] = None # filled in by pushAccountInfo()
        userScreenName = postDict.get('username', '')
        accountDict['screen_name'] = userScreenName
        accountDict['name'] = postDict.get('name', '')
        if isinstance(userScreenName, list):
            userScreenName = userScreenName[0]
        accountDict['anon_screen_name'] = self.hashGeneral(userScreenName)
        accountDict['mailing_address'] = postDict.get('mailing_address', '')
        # Mailing addresses are enclosed in brackets, making them 
        # an array. Pull the addr string out:
        mailAddr = accountDict['mailing_address']
        if isinstance(mailAddr, list):
            mailAddr = mailAddr[0]
            accountDict = self.getZipAndCountryFromMailAddr(mailAddr, accountDict)
        else:
            accountDict['zipcode'] = ''
            accountDict['country'] = ''
            
        # Make sure that zip code is null unless address is USA:
        if accountDict['country'] != 'USA':
            accountDict['zipcode'] = ''
            
        accountDict['gender'] = postDict.get('gender', '')
        accountDict['year_of_birth'] = postDict.get('year_of_birth', -1)
        accountDict['level_of_education'] = postDict.get('level_of_education', '')
        accountDict['goals'] = postDict.get('goals', '')
        accountDict['honor_code'] = postDict.get('honor_code', -1)
        accountDict['terms_of_service'] = postDict.get('terms_of_service', -1)
        accountDict['course_id'] = postDict.get('course_id', '')
        accountDict['enrollment_action'] = postDict.get('enrollment', '')
        accountDict['email'] = postDict.get('email', '') 
        accountDict['receive_emails'] = postDict.get('receive_emails', '') 

        # Some values in create_account are arrays. Replace those
        # values' entries in accountDict with the arrays' first element:
        for fldName in accountDict.keys():
            if isinstance(accountDict[fldName], list):
                accountDict[fldName] = accountDict[fldName][0]

        # Convert some values into more convenient types
        # (that conform to the SQL types we declared in
        # self.schemaAccountTbl:
        try:
            accountDict['year_of_birth'] = int(accountDict['year_of_birth'])
        except:
            accountDict['year_of_birth'] = 0

        try:
            accountDict['terms_of_service'] = 1 if accountDict['terms_of_service'] == 'true' else 0
        except:
            pass

        try:
            accountDict['honor_code'] = 1 if accountDict['honor_code'] == 'true' else 0
        except:
            pass
        
        # Escape single quotes and CR/LFs in the various fields, so that MySQL won't throw up.
        # Also replace newlines with ", ":
        if len(accountDict['goals']) > 0:
            accountDict['goals'] = self.makeInsertSafe(accountDict['goals'])
        if len(accountDict['screen_name']) > 0:            
            accountDict['screen_name'] = self.makeInsertSafe(accountDict['screen_name'])
        if len(accountDict['name']) > 0:                        
            accountDict['name'] = self.makeInsertSafe(accountDict['name'])
        if len(accountDict['mailing_address']) > 0:                                    
            accountDict['mailing_address'] = self.makeInsertSafe(accountDict['mailing_address'])
        
        # Get the (only) Account table foreign key.
        # Returned in an array for conformance with the
        # other push<TableName>Info()
        self.pushAccountInfo(accountDict)

    def handleCourseEnrollActivatedDeactivated(self, record, event):
        '''
        Handles events edx_course_enrollment_activated, and edx_course_enrollment_deactivated.
        Checks the context field. If it contains a 'path' field, then
        its value is placed in the 'page' column.
        
        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in edx_course_enrollment_(de)activated event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        self.setValInRow('hintmode', event.get('mode', None))
        self.setValInRow('session', event.get('session', None))
        
        if self.currContext is not None:
            pathToUiButton = self.currContext.get('path', None)
            self.setValInRow('page', pathToUiButton)

    def handleCourseEnrollUpgradeOrSucceeded(self, record, event):
        '''
        Handles events edx_course_enrollment_upgrade_clicked, and 
        edx_course_enrollment_upgrade_succeeded, and edx_course_enrollment_deactivated.
        Checks the context field. If it contains a 'mode' field, then
        its value is placed in the 'mode' column.
        
        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''

        if self.currContext is not None:
            pathToUiButton = self.currContext.get('mode', None)
            self.setValInRow('hintmode', pathToUiButton)

    def handleProblemGraded(self, record, event):
        '''
        Events look like this::
        
             '[...#8217;t improve or get worse. Calculate the 95% confidence interval for the true proportion of heart disease patients who improve their fitness using this particular exercise regimen. Recall that proportions are normally distributed with a standard error of </p><p>\\\\[ \\\\sqrt{\\\\frac{p(1-p)}{n}} \\\\]</p><p>(You may use the observed proportion to calculate the standard error.)</p><span><form class=\\\"choicegroup capa_inputtype\\\" id=\\\"inputtype_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\"><div class=\\\"indicator_container\\\">\\n    </div><fieldset><label for=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_0\\\"><input type=\\\"radio\\\" name=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" id=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_0\\\" aria-describedby=\\\"answer_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" value=\\\"choice_0\\\"/> 66%\\n\\n        </label><label for=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_1\\\"><input type=\\\"radio\\\" name=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" id=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_1\\\" aria-describedby=\\\"answer_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" value=\\\"choice_1\\\"/> 66%-70%\\n\\n        </label><label for=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_2\\\" class=\\\"choicegroup_correct\\\"><input type=\\\"radio\\\" name=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" id=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_2\\\" aria-describedby=\\\"answer_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" value=\\\"choice_2\\\" checked=\\\"true\\\"/> 50%-84%\\n\\n            \\n            <span class=\\\"sr\\\" aria-describedby=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_2\\\">Status: correct</span>\\n        </label><label for=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1_choice_3\\\"><input type=\\\"radio\\\" name=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_1\\\" id=\\\"input_i4x-Medicine-HRP258-problem-fc217b7c689a40938dd55ebc44cb6f9a_4_...        
            ]'

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in save_problem_fail, save_problem_success, or reset_problem_fail." %\
                         (self.makeFileCitation()))
            return
        
        answersDict = {}
        # The following will go through the mess, and
        # pull out all pairs problemID/(in)correct. Those
        # will live in each Match obj's group(1) and group(2)
        # respectively:
        probIdCorrectIterator = EdXTrackLogJSONParser.problemGradedComplexPattern.finditer(str(event))
        if probIdCorrectIterator is None:
            # Should have found at least one probID/correctness pair:
            self.logWarn("Track log line %s: could not parse out problemID/correctness pairs from '%s'. (stuffed into badlyFormatted)" %\
                         (self.makeFileCitation(), str(event)))
            self.setValInRow('badly_formatted', str(event))
            return
        # Go through each match:
        for searchMatch in probIdCorrectIterator:
            answersDict[searchMatch.group(1)] = searchMatch.group(2)
        
        if len(answersDict) > 0:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        else:
            answersFKeys = []
        
        if len(answersFKeys) > 0:
            # Now need to generate enough near-replicas of event
            # entries to cover all answer 
            # foreign key entries that were created:
            for answerFKey in answersFKeys: 
                # Fill in one main table row.
                self.setValInRow('answer_fk', answerFKey)
                if answerFKey is not None:
                    # For convenience: enter the Answer's problem ID 
                    # in the main table's problemID field:
                    problemID = answerToProblemMap[answerFKey]
                    self.setValInRow('problem_id', problemID)
                    # Try to look up the human readable display name
                    # of the problem, and insert it into the main
                    # table's resource_display_name field:
                    self.setResourceDisplayName(problemID)
                    self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
                    self.pushEvent()
                    # The next row keeps its eventID, but needs its own
                    # primary key (in _id):
                    self.setValInRow('_id', self.getUniqueID())
                else:
                    self.setValInRow('answer', '')                    
            
        # Return empty row, b/c we already pushed all necessary rows:
        self.currentEvent = {}

    def handleReceiveEmail(self, record, event):
        '''
        Event is something like this::
        
            {"course": "Medicine/SciWrite/Fall2013", "receive_emails": "yes"}

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event type change-email-settings." %\
                         (self.makeFileCitation()))
            return
        
        accountDict = self.ensureDict(event)
        if accountDict is None:
            self.logWarn("Track log line %s: event is not a dict in change-email-settings event: '%s' (%s)" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        course_id = accountDict.get('course', None)
        receive_emails = accountDict.get('receive_emails', None)
        screen_name = record.get('username', None)

        # Get the event fields and put them in their place:
        # dict as expected by pushAccountInfo():
        accountDict = OrderedDict()
        accountDict['account_id'] = None # filled in by pushAccountInfo()
        accountDict['anon_screen_name'] = self.hashGeneral(screen_name)
        accountDict['name'] = None
        accountDict['mailing_address'] = None
        
        mailAddr = accountDict['mailing_address']
        if mailAddr is not None:
            # Mailing addresses are enclosed in brackets, making them 
            # an array. Pull the addr string out:
            if isinstance(mailAddr, list):
                mailAddr = mailAddr[0] 
            accountDict = self.getZipAndCountryFromMailAddr(mailAddr, accountDict)
        else:
            accountDict['zipcode'] = None
            accountDict['country'] = None
        accountDict['gender'] = None
        accountDict['year_of_birth'] = None
        accountDict['level_of_education'] = None
        accountDict['goals'] = None
        accountDict['honor_code'] = None
        accountDict['terms_of_service'] = None
        accountDict['course_id'] = course_id
        accountDict['enrollment_action'] = None
        accountDict['email'] = None
        accountDict['receive_emails'] = receive_emails
#************** push to account???
                
    def handleABExperimentEvent(self, record, event):
        
        if event is None:
            self.logWarn("Track log line %s: missing event text in event type assigned_user_to_partition or child_id." %\
                         (self.makeFileCitation()))
            return
        
        eventDict = self.ensureDict(event)
        if eventDict is None:
            self.logWarn("Track log line %s: event is not a dict in assigned_user_to_partition or child_id event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        if len(self.currentEvent) < 1:
            self.logWarn("Track log line %s: encountered empty partial row while processing assigned_user_to_partition or child_id: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        try:
            eventType = record['event_type']
        except KeyError:
            eventType = None
        
        # Give the ABExperiment table row we are constructing
        # the same key as the current row in EdxTrackEvent:
        currEventRowId =self.currentEvent['_id']
        abExpDict = OrderedDict()
        abExpDict['event_table_id']  = currEventRowId
        abExpDict['event_type']      = eventType
        abExpDict['group_id']        = eventDict.get('group_id', -1)
        abExpDict['group_name']      = eventDict.get('group_name', '')
        abExpDict['partition_id']    = eventDict.get('partition_id', -1)
        abExpDict['partition_name']  = eventDict.get('partition_name', '')
        abExpDict['child_module_id'] = eventDict.get('child_id', '')

        self.pushABExperimentInfo(abExpDict)

    def handlePathStyledEventTypes(self, record, event):
        '''
        Called when an event type is a long path-like string.
        Examples::
        
          /courses/OpenEdX/200/Stanford_Sandbox/modx/i4x://OpenEdX/200/combinedopenended/5fb3b40e76a14752846008eeaca05bdf/check_for_score
          /courses/Education/EDUC115N/How_to_Learn_Math/modx/i4x://Education/EDUC115N/peergrading/ef6ba7f803bb46ebaaf008cde737e3e9/is_student_calibrated",
          /courses/Education/EDUC115N/How_to_Learn_Math/courseware
          
        Most have action instructions at the end, some don't. The ones that don't 
        have no additional information. We drop those events.

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event %s." %\
                         (self.makeFileCitation(), str(event)))
            return

        # Interesting info is hidden in the event_type field of this
        # type of record: the embedded hash string corresponds to a
        # sometimes illuminating entry in the modulestore's 'metadata.display_name'
        # field. We use our ModulestoreMapper instance self.hashMapper to
        # get that information, and insert it in the resource_display_name field
        # of the edXTrackEvent table (setResourceDisplayName() does nothing if
        # given a None, so the call is safe):
        self.setResourceDisplayName(record.get('event_type', None))

        eventDict = self.ensureDict(event) 
        if eventDict is None:
            self.logWarn("Track log line %s: event is not a dict in path-styled event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        try:
            postDict = eventDict['POST']
        except KeyError:
            self.logWarn("Track log line %s: event in path-styled event is not GET styled: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
            
        # Grab the 'verb' at the end, if there is one:
        eventType = record['event_type']
        if eventType is None or not isinstance(eventType, basestring):
            return 
        pieces = eventType.split('/')
        verb   = pieces[-1]
        if verb == 'is_student_calibrated':
            self.subHandleIsStudentCalibrated(postDict)
            return 
        elif verb == 'goto_position':
            self.subHandleGotoPosition(postDict)
            return 
        elif verb == 'get_last_response':
            # No additional info to get
            return
        elif verb == 'problem':
            self.subHandleProblem(postDict)
            return 
        elif verb == 'save_answer':
            self.subHandleSaveAnswer(postDict)
            return 
        elif verb == 'check_for_score':
            # No additional info to get
            return
        elif verb == 'problem_get':
            # No additional info to get
            return
        elif verb == 'get_legend':
            # No additional info to get
            return
        elif verb == 'problem_show':
            # No additional info to get
            return
        elif verb == 'problem_check':
            self.subHandleProblemCheckInPath(postDict)
            return 
        elif verb == 'save_grade':
            self.subHandleSaveGrade(postDict)
            return
        
    def handleForumEvent(self, record, event):

        eventDict = self.ensureDict(event) 
        if eventDict is None:
            self.logWarn("Track log line %s: event is not a dict in path-styled event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        self.setValInRow('submission_id', str(event.get('query', None)))
        self.setValInRow('page', str(event.get('page', None)))
        self.setValInRow('success', str(event.get('total_results', None)))
            
    def handleListForumInteraction(self, record, event):
        eventType = record['event_type']
        if event is None:
            self.logWarn("Track log line %s: missing event info in list-forum-admins, list-forum-mods, or list-forum-community-TAs." %\
                         (self.makeFileCitation()))
            return
        event = self.ensureDict(event) 
        if event is None:
            self.logWarn("Track log line %s: event is not a dict in list-forum-admins, list-forum-mods, or list-forum-community-TAs event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        
        if eventType == 'edx.forum.thread.created':
            self.setValInRow('collaboration_type_id',1)
        elif eventType == 'edx.forum.response.created':
            self.setValInRow('collaboration_type_id',2)
        elif eventType == 'edx.forum.comment.created':
            self.setValInRow('collaboration_type_id',3)
        elif eventType in ['edx.forum.response.voted','edx.forum.thread.voted']:
            self.setValInRow('collaboration_type_id',4)
        
        self.setValInRow('collaboration_content', self.makeInsertSafe(event.get('body',None)))

                
    def subHandleIsStudentCalibrated(self, eventDict):
        '''
        Called from handlePathStyledEventTypes(). Event dict looks like this::
        
           {\"location\": [\"i4x://Education/EDUC115N/combinedopenended/0d67667941cd4e14ba29abd1542a9c5f\"]}, \"GET\": {}"        
           
        The caller is expected to have verified the legitimacy of EventDict

        :param row:
        :type row:
        :param eventDict:
        :type eventDict:
        '''

        # Get location:
        try:
            location = eventDict['location']
        except KeyError:
            self.logWarn("Track log line %s: no location field provided in is_student_calibrated event: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            return
        try:
            # The 'location' is an array of strings. Turn them into one string:
            location = '; '.join(location)
            self.setValInRow('question_location', location)
        except TypeError:
            self.logWarn("Track log line %s: location field provided in is_student_calibrated event contains a non-string: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            return

    def subHandleGotoPosition(self, eventDict):
        '''
        Called from handlePathStyledEventTypes(). Event dict looks like this::
        
           {\"position\": [\"2\"]}, \"GET\": {}}"
           
        The caller is expected to have verified the legitimacy of EventDict

        :param row:
        :type row:
        :param eventDict:
        :type eventDict:
        '''

        # Get location:
        try:
            position = eventDict['position']
        except KeyError:
            self.logWarn("Track log line %s: no position field provided in got_position event: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            return
        try:
            # The 'position' is an array of ints. Turn them into one string:
            position = '; '.join(position)
            self.setValInRow('position', position)
        except TypeError:
            self.logWarn("Track log line %s: position field provided in goto_position event contains a non-string: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            return

    def subHandleProblem(self, eventDict):
        '''
        Called from handlePathStyledEventTypes(). Event dict looks like this::
        
           {\"location\": [\"i4x://Education/EDUC115N/combinedopenended/0d67667941cd4e14ba29abd1542a9c5f\"]}, \"GET\": {}}"
           
        The caller is expected to have verified the legitimacy of EventDict

        :param row:
        :type row:
        :param eventDict:
        :type eventDict:
        '''

        # Get location:
        try:
            location = eventDict['location']
        except KeyError:
            self.logWarn("Track log line %s: no location field provided in is_student_calibrated event: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            return
        try:
            # The 'location' is an array of strings. Turn them into one string:
            location = '; '.join(location)
            self.setValInRow('question_location', location)
        except TypeError:
            self.logWarn("Track log line %s: location field provided in is_student_calibrated event contains a non-string: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            return

    def subHandleSaveAnswer(self, eventDict):
        '''
        Called from handlePathStyledEventTypes(). Event dict looks like this::
        
           {\"student_file\": [\"\"], 
            \"student_answer\": [\"Students will have to use higher level thinking to describe the...in the race. \"], 
            \"can_upload_files\": [\"false\"]}, \"GET\": {}}"
                    
        The caller is expected to have verified the legitimacy of EventDict

        :param row:
        :type row:
        :param eventDict:
        :type eventDict:
        '''

        student_file = eventDict.get('student_file', [''])
        student_answer = eventDict.get('student_answer', [''])
        can_upload_file = eventDict.get('can_upload_files', [''])

        # All three values are arrays. Turn them each into a semicolon-
        # separated string:
        try:
            student_file = '; '.join(student_file)
        except TypeError:
            self.logWarn("Track log line %s: student_file field provided in save_answer event contains a non-string: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            student_file = ''
        self.setValInRow('student_file', student_file)

        try:
            student_answer = '; '.join(student_answer)
            # Ensure escape of comma, quotes, and CR/LF:
            student_answer = self.makeInsertSafe(student_answer)
        except TypeError:
            self.logWarn("Track log line %s: student_answer field provided in save_answer event contains a non-string: '%s'" %\
             (self.makeFileCitation(), str(eventDict)))
            student_answer = ''
        self.setValInRow('long_answer', student_answer)
            
        try:
            can_upload_file = '; '.join(can_upload_file)
        except TypeError:
            #self.logWarn("Track log line %s: can_upload_file field provided in save_answer event contains a non-string: '%s'" %\
            # (self.jsonToRelationConverter.makeFileCitation(), str(eventDict)))
            can_upload_file = str(can_upload_file)
        self.setValInRow('can_upload_file', can_upload_file)

    def subHandleSaveGrade(self, postDict):
        '''
        Get something like::
        
           "{\"POST\": {\"submission_id\": [\"60611\"], 
                        \"feedback\": [\"<p>This is a summary of a paper stating the positive effects of a certain hormone on face recognition for people with disrupted face processing [1].\\n<br>\\n<br>Face recognition is essential for social interaction and most people perform it effortlessly. But a surprisingly high number of people \\u2013 one in forty \\u2013 are impaired since birth in their ability to recognize faces [2]. This condition is called 'developmental prosopagnosia'. Its cause isn\\u2"        

        :param row:
        :type row:
        :param postDict:
        :type postDict:
        '''
        if postDict is None:
            return
        submissionID = postDict.get('submission', None) 
        feedback = postDict.get('feedback', None)
        if feedback is not None:
            feedback = self.makeInsertSafe(str(feedback))
        self.setValInRow('submission_id', submissionID)
        self.setValInRow('long_answer', feedback)

    def subHandleProblemCheckInPath(self, answersDict):
        '''
        Get dict like this::
        
           {\"input_i4x-Medicine-HRP258-problem-f0b292c175f54714b41a1b05d905dbd3_2_1\": [\"choice_3\"]}, 
            \"GET\": {}}"        

        :param row:
        :type row:
        :param answersDict:
        :type answersDict:
        '''
        if answersDict is not None:
            # Receive all the Answer table keys generated for
            # the answers, and a dict mapping each key
            # to the problem ID to which that key's row
            # in the Answer refers:
            (answersFKeys, answersTableDict, answerToProblemMap) = self.pushAnswers(answersDict)
        for answerFKey in answersFKeys:
            self.setValInRow('answer_fk', answerFKey)
            if answerFKey is not None:
                # For convenience: enter the Answer's problem ID 
                # in the main table's problemID field:
                problemID = answerToProblemMap[answerFKey]
                self.setValInRow('problem_id', problemID)
                # Try to look up the human readable display name
                # of the problem, and insert it into the main
                # table's resource_display_name field:
                self.setResourceDisplayName(problemID)
                self.setValInRow('answer', answersTableDict[self.currentEvent['answer_fk']][2])
                self.pushEvent()
                # The next row keeps its eventID, but needs its own
                # primary key (in _id):
                self.setValInRow('_id', self.getUniqueID())
            else:
                self.setValInRow('answer', '')

        self.currentEvent = {}

    def handleAjaxLogin(self, record, event, eventType):
        '''
        Events look like this::
        
            "{\"POST\": {\"password\": \"********\", \"email\": [\"emil.smith@gmail.com\"], \"remember\": [\"true\"]}, \"GET\": {}}"        

        :param record:
        :type record:
        :param row:
        :type row:
        :param event:
        :type event:
        :param eventType:
        :type eventType:
        '''
        if event is None:
            self.logWarn("Track log line %s: missing event text in event %s." %\
                         (self.makeFileCitation(), str(event)))
            return

        eventDict = self.ensureDict(event) 
        if eventDict is None:
            self.logWarn("Track log line %s: event is not a dict in event: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return

        try:
            postDict = eventDict['POST']
        except KeyError:
            self.logWarn("Track log line %s: event in login_ajax is not GET styled: '%s'" %\
                         (self.makeFileCitation(), str(event)))
            return
        email = postDict.get('email', None)
        # We get remember here, but don't carry it to the relational world:
        remember = postDict.get('remember', None)  # @UnusedVariable
        if email is not None:
            # Stick email into the screen_name field. But flatten
            # the array of email addresses to a string (I've only
            # seen single-element arrays anyway):
            try:
                email = '; '.join(email)
            except TypeError:
                pass
            self.setValInRow('anon_screen_name', self.hashGeneral(email))
                    
    def handleBadJSON(self, offendingText):
        '''
        When JSON parsing fails, place the offending text into 
        longAnswer. Happens, for instance, when student answers have embedded
        quotes that confused some upstream load process.

        :param row:
        :type row:
        :param offendingText:
        :type offendingText:
        '''
        self.setValInRow('badly_formatted', self.makeInsertSafe(offendingText))
    
    def get_course_id(self, event):
        '''
        Given a 'pythonized' JSON tracking event object, find
        the course URL, and extract the course name from it.
        A number of different events occur, which do not contain
        course IDs: server heartbeats, account creation, dashboard
        accesses. Among them are logins, which look like this::
        
            {"username": "", 
             "host": "class.stanford.edu", 
             "event_source": "server", 
             "event_type": "/accounts/login", 
             "time": "2013-06-14T00:31:57.661338", 
             "ip": "98.230.189.66", 
             "event": "{
                        \"POST\": {}, 
                        \"GET\": {
                             \"next\": [\"/courses/Medicine/HRP258/Statistics_in_Medicine/courseware/80160e.../\"]}}", 
             "agent": "Mozilla/5.0 (Windows NT 5.1; rv:21.0) Gecko/20100101
             Firefox/21.0", 
             "page": null
             }
    
        But also::
        
            {"username": "RobbieH", 
             "host": "class.stanford.edu", 
            ...
            "event": {"failure": "closed", "state": {"student_answers": {"i4x-Medicine-HRP258-problem-4cd47ea861f542488a20691ac424a002_7_1": "choice_1", "i4x-Medicine-HRP258-problem-4cd47ea861f542488a20691ac424a002_2_1": "choice_3", "i4x-Medicine-HRP258-problem-4cd47ea861f542488a20691ac424a002_9_1": ["choice_0", "choice_1"], "i4x-Medicine-HRP258-problem-4cd47ea861f542488a20691ac424a002_6_1": "choice_0", "i4x-Medicine-HRP258-problem-4cd47ea861f542488a20691ac424a002_8_1": ["choice_0", "choice_1", "choice_2", "choice_3", "choice_4"], 
        
        Notice the 'event' key's value being a *string* containing JSON, rather than 
        a nested JSON object. This requires special attention. Buried inside
        that string is the 'next' tag, whose value is an array with a long (here
        partially elided) hex number. This is where the course number is
        extracted.
        
        :param event: JSON record of an edx tracking event as internalized dict
        :type event: Dict<String,Dict<<any>>
        :return: two-tuple: full name of course in which event occurred, and descriptive name.
                 None if course ID could not be obtained.

        :rtype: {(String,String) | None} 
        '''
        course_id = ''
        eventSource = event.get('event_source', None)
        if eventSource is None:
            return ('','','')
        if eventSource == 'server':
            # get course_id from event type
            eventType = event.get('event_type', None)
            if eventType is None:
                return('','','')
            if eventType == u'/accounts/login':
                try:
                    post = json.loads(str(event.get('event', None)))
                except:
                    return('','','')
                if post is not None:
                    getEntry = post.get('GET', None)
                    if getEntry is not None:
                        try:
                            fullCourseName = getEntry.get('next', [''])[0]
                        except:
                            return('','','')
                    else:
                        return('','','')
                else:
                    return('','','')
                
            elif eventType.startswith('/courses'):
                courseID = self.extractShortCourseID(eventType)
                return(courseID, courseID, self.getCourseDisplayName(eventType))
                 
            elif eventType.find('problem_') > -1:
                event = event.get('event', None)
                if event is None:
                    return('','','')
                courseID = self.extractCourseIDFromProblemXEvent(event)
                return(courseID, courseID, '')
            else:
                fullCourseName = event.get('event_type', '')
        else:
            fullCourseName = event.get('page', '')
            
        # Abvove logic makes an error for '/dashboard' events:
        # it assigns '/dashboard' to the fullCourseName. Correct
        # this:
        if fullCourseName == '/dashboard' or fullCourseName == '/heartbeat':
            fullCourseName = ""
        if len(fullCourseName) > 0:
            course_display_name = self.extractShortCourseID(fullCourseName)
        else:
            course_display_name = ''
        if len(course_id) == 0:
            course_id = fullCourseName
        return (fullCourseName, course_id, course_display_name)
        
    def getCourseDisplayName(self, fullCourseName):
        '''
        Given a 

        :param fullCourseName:
        :type fullCourseName:
        '''
        hashStr = self.extractOpenEdxHash(fullCourseName)
        if hashStr is None:
            return None
        courseShortName = self.hashMapper.getCourseShortName(hashStr)
        if courseShortName is not None:
            return self.hashMapper[courseShortName]
        else:
            return None
        
        
    def extractShortCourseID(self, fullCourseStr):
        if fullCourseStr is None:
            return ''
        courseNameFrags = fullCourseStr.split('/')
        course_id = ''
        if 'courses' in courseNameFrags:
            i = courseNameFrags.index('courses')
            course_id = "/".join(map(str, courseNameFrags[i+1:i+4]))
        return course_id        

    def extractCourseIDFromProblemXEvent(self, event):
        '''
        Given the 'event' field of an event of type problem_check, problem_check_fail, problem_save...,
        extract the course ID. Ex from save_problem_check::
        
            "event": {"success": "correct", "correct_map": {"i4x-Medicine-HRP258-problem-8dd11b4339884ab78bc844ce45847141_2_1": {"hint": "", "hintmode": null,...

        :param event:
        :type event:
        '''
        if event is None:
            return None
        # isolate '-Medicine-HRP258-problem-8dd11b4339884ab78bc844ce45847141_2_1":' from:
        # ' {"success": "correct", "correct_map": {"i4x-Medicine-HRP258-problem-8dd11b4339884ab78bc844ce45847141_2_1": {"hint": "", "hintmode": null'
        match = EdXTrackLogJSONParser.problemXFindCourseID.search(str(event))
        if match is None:
            return None
        # the match obj's groups is now: '-Medicine-HRP258-problem-8dd11b4339884ab78bc844ce45847141_2_1"'
        # Split into ['', 'Medicine', 'HRP258', 'problem', '8dd11b4339884ab78bc844ce45847141_2_1"'] 
        parts = match.groups()[0].split('-')
        try:
            return "-".join([parts[1], parts[2]])
        except IndexError:
            return None

    def ensureDict(self, event):
        '''
        If event is either a dict, or a string with a dict
        definition inside, returns a dict. Else returns None
        
        :param event:
        :type event:
        '''
        if isinstance(event, dict):
            return event
        else:
            try:
                # Maybe it's a string: make a dict from the string:
                res = eval(event)
                if isinstance(res, dict):
                    return res
                else:
                    return None
            except Exception:
                return None
        
    def ensureArray(self, event):
        '''
        If event is either a Python array, or a string with an array
        definition inside, returns the array. Else returns None
        
        :param event:
        :type event:
        '''
        if isinstance(event, list):
            return event
        else:
            try:
                # Maybe it's a string: make an array from the string:
                res = eval(event)
                if isinstance(res, list):
                    return res
                else:
                    return None
            except Exception:
                return None
            
    def makeInsertSafe(self, unsafeStr):
        '''
        Makes the given string safe for use as a value in a MySQL INSERT
        statement. Looks for embedded CR or LFs, and turns them into 
        semicolons. Escapes commas and single quotes. Backslash is
        replaced by double backslash. This is needed for unicode, like
        \0245 (invented example)

        :param unsafeStr: string that possibly contains unsafe chars
        :type unsafeStr: String
        :return: same string, with unsafe chars properly replaced or escaped

        :rtype: String
        '''
        #return unsafeStr.replace("'", "\\'").replace('\n', "; ").replace('\r', "; ").replace(',', "\\,").replace('\\', '\\\\')
        if unsafeStr is None or not isinstance(unsafeStr, basestring) or len(unsafeStr) == 0:
            return ''
        # Check for chars > 128 (illegal for standard ASCII):
        for oneChar in unsafeStr:
            if ord(oneChar) > 128:
                # unidecode() replaces unicode with approximations. 
                # I tried all sorts of escapes, and nothing worked
                # for all cases, except this:
                unsafeStr = unidecode(unicode(unsafeStr))
                break
        return unsafeStr.replace('\n', "; ").replace('\r', "; ").replace('\\', '').replace("'", r"\'")
    
    def makeJSONSafe(self, jsonStr):
        '''
        Given a JSON string, make it safe for loading via
        json.loads(). Backslashes before chars other than 
        any of \bfnrtu/ are escaped with a second backslash 

        :param jsonStr:
        :type jsonStr:
        '''
        res = EdXTrackLogJSONParser.JSON_BAD_BACKSLASH_PATTERN.sub(self.fixOneJSONBackslashProblem, jsonStr)
        return res

    
    def fixOneJSONBackslashProblem(self, matchObj):
        '''
        Called from the pattern.sub() method in makeJSONSafe for
        each match of a bad backslash in jsonStr there. Returns
        the replacement string to use by the caller for the substitution. 
        Ex. a match received from the original string "\d'Orsay" returns
        "\\d".    

        :param matchObj: a Match object resulting from a regex search/replace
                         call.
        :type matchObj: Match
        '''
        return "\\\\" + matchObj.group(1)

    def rescueBadJSON(self, badJSONStr):
        '''
        When JSON strings are not legal, we at least try to extract 
        the username, host, session, event_type, event_source, and event fields
        verbatim, i.e. without real parsing. We place those in the proper 
        fields, and leave it at that.

        :param badJSONStr:
        :type badJSONStr:
        '''
        screen_name = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['username'], badJSONStr)
        #host = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['host'], badJSONStr)
        session = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['session'], badJSONStr)
        event_source = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['event_source'], badJSONStr)        
        event_type = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['event_type'], badJSONStr)        
        time = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['time'], badJSONStr)        
        ip = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['ip'], badJSONStr)                
        event = self.tryJSONExtraction(EdXTrackLogJSONParser.searchPatternDict['event'], badJSONStr)                
        
        if isinstance(screen_name, basestring):
            self.setValInRow('anon_screen_name', self.hashGeneral(screen_name))
        else:
            self.setValInRow('anon_screen_name', '')
        #self.setValInRow(row, 'host', host)
        self.setValInRow('session', session)
        self.setValInRow('event_source', event_source)
        self.setValInRow('event_type', event_type)
        self.setValInRow('time', time)
        self.setValInRow('ip', self.getThreeLetterCountryCode(ip))
        self.setValInRow('badly_formatted', self.makeInsertSafe(event))
    
    def tryJSONExtraction(self, pattern, theStr):
        m = pattern.search(theStr)
        try:
            return None if m is None else m.group(1)
        except:
            return None
        
    def getUniqueID(self):
        '''
        Generate a universally unique key with
        all characters being legal in MySQL identifiers. 
        '''
        return str(uuid.uuid4()).replace('-','_')

    def getZipAndCountryFromMailAddr(self, mailAddr, accountDict):
        
            zipCodeMatch = EdXTrackLogJSONParser.zipCodePattern.findall(mailAddr)
            if len(zipCodeMatch) > 0:
                accountDict['zipcode'] = zipCodeMatch[-1]
            else:
                accountDict['zipcode'] = ''
                
            # See whether the address includes a country:
            # Last ditch: if we think we found a zip code, 
            # start out thinking US for the country:
            if len(accountDict['zipcode']) > 0:
                accountDict['country'] = 'USA'
            else:
                accountDict['country'] = ''
            # Our zip code might be a different number,
            # so do look for an explicit country:
            splitMailAddr = re.split(r'\W+', mailAddr)
            # Surely not the fastest, but I'm tired: pass
            # a sliding window of four,three,bi, and unigrams
            # over the mailing address to find a country
            # specification:
            for mailWordIndx in range(len(splitMailAddr)):
                try: 
                    fourgram = string.join([splitMailAddr[mailWordIndx], 
                                            splitMailAddr[mailWordIndx + 1], 
                                            splitMailAddr[mailWordIndx + 2],
                                            splitMailAddr[mailWordIndx + 3]])
                    country = self.countryChecker.isCountry(fourgram)
                    if len(country) > 0:
                        accountDict['country'] = country
                        break 
                except IndexError:
                    pass
                try: 
                    trigram = string.join([splitMailAddr[mailWordIndx], splitMailAddr[mailWordIndx + 1], splitMailAddr[mailWordIndx + 2]])
                    country = self.countryChecker.isCountry(trigram)
                    if len(country) > 0:
                        accountDict['country'] = country
                        break 
                except IndexError:
                    pass
                
                try:
                    bigram = string.join([splitMailAddr[mailWordIndx], splitMailAddr[mailWordIndx + 1]])
                    country = self.countryChecker.isCountry(bigram)
                    if len(country) > 0:
                        accountDict['country'] = country
                        break 
                except IndexError:
                    pass
                
                unigram = splitMailAddr[mailWordIndx]
                country = self.countryChecker.isCountry(unigram)
                if len(country) > 0:
                    accountDict['country'] = country
                    break 
            # Make sure that zip code is empty unless address is USA:
            if accountDict['country'] != 'USA':
                accountDict['zipcode'] = ''
                
            return accountDict

    def anonymizeUser(self,screenName,email):
        '''
        Generate a user hash, using email if available,
        else the screenName. (Sometimes either email or screenName are empty)

        :param screenName: user screen name in system
        :type screenName: string
        :param email: user email address
        :type email: string
        :return: 40 byte hash

        :rtype: string
        '''
        if len(email) > 0:
            return self.hashGeneral(email)
        else:
            return self.hashGeneral(screenName)

    def hashGeneral(self, username):
        '''
        Returns a ripemd160 40 char hash of the given name. Uses the
        corresponding class method below. 

        :param username: name to be hashed
        :type username: String
        :return: hashed equivalent. Calling this function multiple times returns the same string

        :rtype: String
        '''
        return EdXTrackLogJSONParser.makeHash(username)
        
    @classmethod
    def makeHash(cls, username):
        '''
        Returns a ripemd160 40 char hash of the given name. 

        :param username: name to be hashed
        :type username: String
        :return: hashed equivalent. Calling this function multiple times returns the same string

        :rtype: String
        '''
        #return hashlib.sha224(username).hexdigest()
        oneHash = hashlib.new('ripemd160')
        oneHash.update(username)
        return oneHash.hexdigest()
    
    def extractOpenEdxHash(self, idStr):
        '''
        Given a string, such as::
        
            i4x-Medicine-HRP258-videoalpha-7cd4bf0813904612bcd583a73ade1d54
            
        or::
        
            input_i4x-Medicine-HRP258-problem-98ca37dbf24849debcc29eb36811cb68_3_1_choice_3'
            
        extract and return the 32 bit hash portion. If none is found,
        return None. Method takes any string and finds a 32 bit hex number.
        It is up to the caller to ensure that the return is meaningful. As
        a minimal check, the method does ensure that there is at most one 
        qualifying string present; we know that this is the case with problem_id
        and other strings.

        :param idStr: problem, module, video ID and others that might contain a 32 bit OpenEdx platform hash
        :type idStr: string
        '''
        if idStr is None:
            return None
        match = EdXTrackLogJSONParser.findHashPattern.search(idStr)
        if match is not None:
            return match.group(1)
        else:
            return None

    def setResourceDisplayName(self, openEdxHash):
        '''
        Given an OpenEdx hash of problem ID, video ID, or course ID,
        set the resource_display_name in the given row. The value
        passed in may have the actual hash embedded in a larger
        string, as in::
        
            input_i4x-Medicine-HRP258-problem-7451f8fe15a642e1820767db411a4a3e_2_1
            
        We fish it out of there.            

        :param row: current row's values
        :type row: [<any>]
        :param openEdxHash: 32-bit hash string encoding a problem, video, or class, or 
                       such a 32-bit hash embedded in a larger string.
        :type openEdxHash: String
        '''
        if openEdxHash is not None and len(openEdxHash) > 0:
            # Fish out the actual 32-bit hash:
            hashNum = self.extractOpenEdxHash(openEdxHash)
            # Get display name and add to main table as resource_display_name:
            displayName = self.hashMapper.getDisplayName(hashNum)
            if displayName is not None:
                self.setValInRow('resource_display_name', self.makeInsertSafe(displayName))
        
    def extractCanonicalCourseName(self, trackLogStr):
        '''
        Given a string believed to be the best course name
        snippet from a log entry, use the modulestoreImporter's
        facilities to get a canonical name. Inputs look like::
        
            Medicine/HRP258/Statistics_in_Medicine
            /courses/Education/EDUC115N/How_to_Learn_Math/modx/i4x://Education/EDUC115N/sequential/1b3ac347ca064b3eaaddbc27d4200964/goto_position

        :param trackLogStr: string that hopefully contains a course short name
        :type trackLogStr: String
        :return: a string of the form org/courseShortName/courseTitle, or None if no course name 
                  could be found in the given string.

        :rtype: {String | None}
        '''
        # First, remove substrings that are obviously 
        # hashes that could match short course names:
        trackLogStr = self.hexGE32Digits.sub('', trackLogStr)
        
        # We go through all course short names, starting
        # with the longest, in decreasing length. We
        # select the first course short name that is
        # embedded in the given trackLogStr. Proceeding
        # by decreasing length is needed to avoid prematurely
        # choosing a course short name like 'db', which easily
        # matches a hash string.
        for shortCourseName in self.courseNamesSorted:
            if string.find(trackLogStr, shortCourseName) > -1:
                return self.hashMapper[shortCourseName]
        return None

    def getThreeLetterCountryCode(self, ipAddr):
        '''
        Given an ip address string, return the corresponding
        3-letter country code, or None if no country found.
        This method could easily be modified to return the 2-letter code, 
        or the full country name.
        
        :param ipAddr: IP address whose assigned country is to be found
        :type ipAddr: String
        :return: a three-letter country code
        :rtype: String
        '''
        
        # Get the triplet (2-letter-country-code, 3-letter-country-code, country): 
        val = self.ipCountryDict.get(ipAddr, None)
        if val is not None:
            return val[1] # get 3-letter country code
        else:
            return None
        

