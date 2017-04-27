#!/usr/bin/python

import sys
import getopt
import gzip
import hashlib
import re

def findRealName(nameDict, name):
    for real, anon in nameDict.iteritems():
        if anon == name:
            return real
    print 'Anonymous name ' + name + ' can\'t be converted to real name'
    return name
    
def main(argv):
    inputfile = '/Users/leducni/Documents/workspace/ITES_analysis1/SEQ_TYPE.TXT'
    logfile = '/Users/leducni/Documents/DATA/ITES.1-P2015/logs.txt.gz'
    outputfile = 'TEST.TXT'
    try:
        opts, args = getopt.getopt(argv,"hi:l:o:",["ifile=","ofile=","logfile="])
    except getopt.GetoptError:
        print 'test.py -i <inputfile> -l <logfile> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputfile> -l <logfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-l", "--logfile"):
            logfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
#    print 'Input file is :', inputfile
#    print 'Log file is :', logfile    
#    print 'Output file is :', outputfile
    if inputfile == '' or outputfile == '':
        print 'test.py -i <inputfile> -l <logfile> -o <outputfile>'
        sys.exit()
    nameDict = dict()
    if logfile != '':
        lfile = ''
        pUser =re.compile('"username": "([\w.@&\-]*)"')
        if logfile.endswith('.gz'):
            lfile = gzip.open(logfile, 'rb')        
        else:
            lfile = open(logfile, "r")
        for line in lfile:
            mUser = pUser.findall(line)
            if len(mUser) == 1 and not nameDict.has_key(mUser[0]):
                oneHash = hashlib.new('ripemd160')
                oneHash.update(mUser[0])
                nameDict[mUser[0]] = oneHash.hexdigest()
                print 's/' + nameDict[mUser[0]] + '/' + mUser[0] + '/'
        lfile.close()
    f = open(inputfile, "r")
    copy = open(outputfile, "w")
    cur_user = ''
    cur_line = ''
    for line in f:
        if '"sequence.ID"' in line:
#            print 'Ignoring line : ' + line
            continue
        lines = line.split('|')
        if cur_user == '':
            cur_user = lines[1]
            cur_line = findRealName(nameDict, lines[1][1:-1])
        if cur_user != lines[1]:
            cur_line += '\n'
            copy.write(cur_line)
            cur_user = lines[1]
            cur_line = findRealName(nameDict, lines[1][1:-1])
        cur_line += ':' + lines[2]
    cur_line += '\n'
    copy.write(cur_line)
    f.close()
    copy.close()

if __name__ == "__main__":
    main(sys.argv[1:])