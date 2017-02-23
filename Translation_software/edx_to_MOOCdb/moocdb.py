import os
import csv


class MOOCdb(object):
    """Provides an interface to store data into a MOOCdb instance. 
    The serialization may be MySQL or CSV"""

    #Important : primary key should be the first specified for each table
    TABLES = {'observed_events':['observed_event_id',           # observed_event_id char(36) NOT NULL PRIMARY KEY,
#                                 'observed_event_type_id',      # --  observed_event_type_id int(11) NOT NULL,
                                 'user_id',                     #   user_id char(40) NOT NULL,
                                 'url_id',                      #   url_id int(11) NOT NULL,
                                 'observed_event_timestamp',    #   observed_event_timestamp datetime NOT NULL,
#                                 'observed_event_data'          # --  observed_event_data longtext NOT NULL,
                                 'observed_event_duration',     #   observed_event_duration int(11) DEFAULT NULL,
                                 'observed_event_ip',           #   observed_event_ip char(3) DEFAULT NULL,
                                 'observed_event_os',           #   observed_event_os int(11) DEFAULT NULL,
                                 'observed_event_agent',        #   observed_event_agent int(11) DEFAULT NULL,
                                 'observed_event_type'],        #   observed_event_type_id varchar(255) NOT NULL,

              'resources':['resource_id',                       #   resource_id int(11) NOT NULL PRIMARY KEY,
                           'resource_name',                     #   resource_name varchar(555) NULL,
                           'resource_uri',                      #   resource_uri varchar(555) NULL,
                           'resource_type_id',                  #   resource_type_id int(2) NOT NULL,
                           'resource_parent_id',                #   resource_parent_id int(11) DEFAULT NULL,
                           'resource_child_number',             #   resource_child_number int(11) DEFAULT NULL,
                           'resource_relevant_week',            #   resource_relevant_week int(11) DEFAULT NULL,
                           'resource_release_timestamp'],       #   resource_release_date date DEFAULT NULL,

              'resources_urls':['resources_urls_id',            #   resources_urls_id int(11) NOT NULL PRIMARY KEY,
                                'resource_id',                  #   resource_id int(11) NOT NULL,
                                'url_id'],                      #   url_id int(11) NOT NULL,

              'urls':['url_id',                                 #   url_id int(11) NOT NULL PRIMARY KEY,
                      'url'],                                   #   url varchar(255) DEFAULT NULL

              'resource_types':['resource_type_id',             #   resource_type_id int(11) NOT NULL PRIMARY KEY,
                                'resource_type_content',        #   resource_type_content varchar(40) NOT NULL,
                                'resource_type_medium'],        #   resource_type_medium varchar(40) NOT NULL

              'problems':['problem_id',                         #   problem_id int(11) NOT NULL PRIMARY KEY,
                          'problem_name',                       #   problem_name varchar(127) NOT NULL,
                          'problem_parent_id',                  #   problem_parent_id int(11) DEFAULT NULL,
                          'problem_child_number',               #   problem_child_number int(11) DEFAULT NULL,
                          'problem_type_id',                    #   problem_type_id int(11) NOT NULL,
                          'problem_release_timestamp',          #   problem_release_timestamp datetime DEFAULT NULL,
                          'problem_soft_deadline',              #   problem_soft_deadline datetime DEFAULT NULL,
                          'problem_hard_deadline',              #   problem_hard_deadline datetime DEFAULT NULL,
                          'problem_max_submission',             #   problem_max_submission int(11) DEFAULT NULL,
                          'problem_max_duration',               #   problem_max_duration int(11) DEFAULT NULL,
                          'problem_weight',                     #   problem_weight int(11) DEFAULT NULL,
                          'resource_id'],                       #   resource_id int(11) DEFAULT NULL,

              'submissions':['submission_id',                   #   submission_id char(36) NOT NULL PRIMARY KEY,
                             'user_id',                         #   user_id char(40) NOT NULL,
                             'problem_id',                      #   problem_id int(11) NOT NULL,
                             'submission_timestamp',            #   submission_timestamp datetime NOT NULL,
                             'submission_attempt_number',       #   submission_attempt_number int(11) NOT NULL,
                             'submission_answer',               #   submission_answer text NOT NULL,
                             'submission_is_submitted',         #   submission_is_submitted int(1) NOT NULL,
                             'submission_ip',                   #   submission_ip char(3) DEFAULT NULL,
                             'submission_os',                   #   submission_os int(11) DEFAULT NULL,
                             'submission_agent'],               #   submission_agent int(11) DEFAULT NULL,

              'assessments':['assessment_id',                   #   assessment_id char(36) NOT NULL PRIMARY KEY,
                             'submission_id',                   #   submission_id char(36) NOT NULL,
                             'assessment_feedback',             #   assessment_feedback text,
                             'assessment_grade',                #   assessment_grade double DEFAULT NULL,
#                             'assessment_max_grade',            # --  assessment_max_grade double DEFAULT NULL,
                             'assessment_grade_with_penalty',   #   assessment_grade_with_penalty double DEFAULT NULL,
                             'assessment_grader_id',            #   assessment_grader_id varchar(63) NOT NULL,
                             'assessment_timestamp'],           #   assessment_timestamp datetime DEFAULT NULL,

              'problem_types':['problem_type_id',               #   problem_type_id int(10) NOT NULL PRIMARY KEY,
                               'problem_type_name'],            #   problem_type_name varchar(255) NOT NULL

              'collaborations':['collaboration_id',             #   collaboration_id int(11) NOT NULL PRIMARY KEY,
                                'user_id',                      #   user_id int(11) NOT NULL,
                                'collaboration_type_id',        #   collaboration_type_id int(11) NOT NULL,
                                'collaboration_content',        #   collaboration_content text NULL,
                                'collaboration_timestamp',      #   collaboration_timestamp datetime NOT NULL,
                                'collaboration_parent_id',      #   collaboration_parent_id int(11) DEFAULT NULL,
                                'collaboration_child_number',   #   collaboration_child_number int(11) DEFAULT NULL,
                                'collaborations_ip',            #   collaborations_ip int(11) DEFAULT NULL,
                                'collaborations_os',            #   collaborations_os int(11) DEFAULT NULL,
                                'collaborations_agent',         #   collaborations_agent int(11) DEFAULT NULL,
                                'resource_id'],                 #   resource_id int(11) DEFAULT NULL,

              'collaboration_types':['collaboration_type_id',   #   collaboration_type_id int(11) NOT NULL PRIMARY KEY,
                                     'collaboration_type_name'],#   collaboration_type_name varchar(45) NOT NULL

              'surveys':['survey_id',                           #   survey_id int(11) NOT NULL PRIMARY KEY,
                         'survey_start_timestamp',              #   survey_start_timestamp datetime DEFAULT NULL,
                         'survey_end_timestamp'],               #   survey_end_timestamp datetime DEFAULT NULL

              'answers':['answer_id',                           #   answer_id int(11) NOT NULL PRIMARY KEY,
                         'answer_content'],                     #   answer_content text

              'questions':['question_id',                       #   question_id int(11) NOT NULL PRIMARY KEY,
                           'question_content',                  #   question_content text,
                           'question_type',                     #   question_type int(11) DEFAULT NULL,
                           'question_reference',                #   question_reference int(11) DEFAULT NULL,
                           'survey_id'],                        #   survey_id int(11) DEFAULT NULL,

              'feedbacks':['feedback_id',                       #   feedback_id int(11) NOT NULL PRIMARY KEY,
                           'user_id',                           #   user_id int(11) NOT NULL,
                           'answer_id',                         #   answer_id int(11) NOT NULL,
                           'question_id',                       #   question_id int(11) NOT NULL,
                           'feedback_timestamp'],               #   feedback_timestamp datetime DEFAULT NULL,

              'os':['os_id',                                    #   os_id int(11) NOT NULL PRIMARY KEY,
                    'os_name'],                                 #   os_name varchar(255) DEFAULT NULL

              'agent':['agent_id',                              #   agent_id int(11) NOT NULL PRIMARY KEY,
                       'agent_name']  }                         #   agent_name varchar(255) DEFAULT NULL

    def __init__(self,MOOCDB_DIR=''):
        self.create_csv_writers(MOOCDB_DIR)

    def close(self):
        for table in self.TABLES:
            reader = getattr(self,table)
            reader.close()

    def create_csv_writers(self,MOOCDB_DIR):
        for table in self.TABLES:
            setattr(self,table,CSVWriter(MOOCDB_DIR + table + '.csv', self.TABLES[table]))
        

class CSVWriter(object):
    
    def __init__(self,output_file,fields,delim=','):

        try:
            self.output = open(output_file,'w')
            self.writer = csv.DictWriter(self.output, delimiter=delim, fieldnames=fields, quotechar='"', escapechar='\\',lineterminator='\n')
        
        except IOError:
            #print '[' + self.__class__.__name__ + '] Could not open file ' + output_file
            return

    def store(self,l):
        self.writer.writerow(l)
        
    def close(self):
        self.output.close()
        


