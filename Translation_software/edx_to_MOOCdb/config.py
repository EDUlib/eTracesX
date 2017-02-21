# Configuration file
import re

## Input file
EDX_TRACK_EVENT_LOG = '/Users/leducni/Documents/DATA/TEST-BUGGY/logs-test-ITES.txt'
## Output files
DEST_DIR = '/Users/leducni/Documents/DATA/TEST-BUGGY/MOOCDB/'

## Input source
## Can be either 'csv', 'sql' or 'json'
INPUT_SOURCE = 'json'
QUOTECHAR = "'" 
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
# MIT courses : %Y-%m-%dT%H:%M:%S.%f
# Stanford Courses : %Y-%m-%d %H:%M:%S

### Hierarchy pretty prints
RESOURCE_HIERARCHY = DEST_DIR + 'resource_hierarchy.org'
PROBLEM_HIERARCHY = DEST_DIR + 'problem_hierarchy.org' 

### Log file
VERBOSE = True
LOG_FILE = DEST_DIR + 'log.org'

## Specific formatting variables
# DOMAIN = 'https://www.edx.org'
DOMAIN = 'https://www.edx.org'

## Course URL parsing
IS_URL = re.compile('^(/|http)')
DOUBLE_SLASH = '(?<!:)//.*$'
PARAMETERS = '((undefined)?\?.*$)'
ANCHOR = '(#|\+|;|\$|\[).*$'
MODULE = '((answer|solution)[^/]*$)'
MISSING_TRAILING_SLASH = '(?<!/)$'
GET_DOMAIN = re.compile('(?P<domain>^.+://[^/]+)')
COURSEWARE = re.compile('courseware/(?P<unit>[^/]+)?/?(?P<subunit>[^/]+)?/?(?P<seq>\d{1,2})?')
BOOK = re.compile('book/(?P<booknum>\d{1,2})/(?P<page>\d{1,4})?')

## Obsolete
## CSV input files
CSV_SOURCE_DIR = '/Users/leducni/Documents/DATA/TEST-ITES/DB/'
CSV_PREFIX = 'logs-test-ULB.txt.2017-01-30T16_11_36.197853_20240.sql'

EDX_TRACK_EVENT = ''.join([CSV_SOURCE_DIR, CSV_PREFIX, '_EdxTrackEventTable.csv'])
CORRECT_MAP = ''.join([CSV_SOURCE_DIR, CSV_PREFIX, '_CorrectMapTable.csv'])
ANSWER = ''.join([CSV_SOURCE_DIR, CSV_PREFIX, '_AnswerTable.csv'])



