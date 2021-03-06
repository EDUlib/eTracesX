# Author : Quentin Agren <quentin.agren@gmail.com>

import sys
import os 
import extractor
import config as cfg
import getopt

from events import *
from resources import *
from collaboration import *
from eventformatter import *
from eventmanager import *
from helperclasses import *
from submissions import *
from util import * 
from moocdb import MOOCdb


def main():
    ROOT_DIR = os.getcwd()
    MOOCDB_DIR = cfg.DEST_DIR
    CONFIG_DIR = ROOT_DIR + '/config/'
    
    # Log file, best viewed with emacs org-mode
    LOG = cfg.LOG_FILE
    sys.stdout = open(LOG, 'w+')
    
    # File to pretty print resource hierarchy
    HIERARCHY = cfg.RESOURCE_HIERARCHY
    PB_HIERARCHY = cfg.PROBLEM_HIERARCHY
    
    # MOOCdb storage interface
# TODO Apply branching to allow different options
    moocdb = MOOCdb(MOOCDB_DIR)

# Instanciating the piping architecture
    event_formatter = EventFormatter(moocdb, CONFIG_DIR)
    resource_manager = ResourceManager(moocdb, HIERARCHY_ROOT='https://', CONFIG_PATH = CONFIG_DIR)
    event_manager = EventManager(moocdb)
    submission_manager = SubmissionManager(moocdb)
    collaboration_manager = CollaborationManager(moocdb) 
    curation_helper = CurationHelper(MOOCDB_DIR)
    
    print '**Processing events**' 
    
    i = 0
    for raw_event in extractor.get_events():
        i = i+1
        print '* Processing event #' + raw_event['_id'] + ' @ ' + str(raw_event['page'])
#    print '** Applying filter'

        # Apply event filter
        if event_formatter.pass_filter(raw_event) == False:
            print 'Event filtered out'
            continue
            
        # Format raw event and instanciate corresponding Event subclass
        event = event_formatter.polish(raw_event)
        # print '- Instanciated event :: ' + event['event_type'] + '->' + event.__class__.__name__
    
        # Inserts resource into the hierarchy
        #    print '** Inserting resource'
        resource_id = resource_manager.create_resource(event)
        event.set_data_attr('resource_id', resource_id)

        # Store submission, assessment and problem
        submission_manager.update_submission_tables(event)
        collaboration_manager.update_collaboration_table(event)

        # Record curation hints
        curation_helper.record_curation_hints(event)

        # Store observed event
        event_manager.store_event(event)

    print '**Processed %s events**' % str(i)
    print '** Writing CSV output to : ' + MOOCDB_DIR

    event_formatter.serialize()
    event_manager.serialize()
    resource_manager.serialize(pretty_print_to=HIERARCHY)
    submission_manager.serialize(pretty_print_to=PB_HIERARCHY)
    collaboration_manager.serialize(pretty_print_to=PB_HIERARCHY)    
    curation_helper.serialize()

    print '* Writing resource hierarchy to : ' + HIERARCHY
    print '* Writing problem hierarchy to : ' + PB_HIERARCHY
# Close all opened files
    moocdb.close()


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print 'main.py -i <inputfile> -o <outputdir>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'main.py -i <inputfile> -o <outputdir>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            cfg.EDX_TRACK_EVENT_LOG = arg
        elif opt in ("-o", "--ofile"):
            cfg.DEST_DIR = arg
            cfg.RESOURCE_HIERARCHY = cfg.DEST_DIR + 'resource_hierarchy.org'
            cfg.PROBLEM_HIERARCHY = cfg.DEST_DIR + 'problem_hierarchy.org' 
            cfg.LOG_FILE = cfg.DEST_DIR + 'log.org'

#    print 'Input file is :', cfg.EDX_TRACK_EVENT_LOG
#    print 'Output file is :', cfg.DEST_DIR
    if cfg.EDX_TRACK_EVENT_LOG == '' or cfg.DEST_DIR == '':
        sys.exit()
        
    main()

