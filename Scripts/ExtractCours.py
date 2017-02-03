#!/usr/bin/python

import sys
import getopt
import re
import random

def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print 'test.py -i <inputfile> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    print 'Input file is :', inputfile
    print 'Output file is :', outputfile
    if inputfile == '' or outputfile == '':
        sys.exit()
    pUser =re.compile('"username": "([\w.@&\-]*)"')
    pCours =re.compile('ITES\.1')
    nameDict = dict()
    f = open(inputfile, "r")
    copy = open(outputfile, "w")
    for line in f:
        mCours = pCours.search(line)
        if mCours:
            mUser = pUser.findall(line)
            newLine = ''
            if len(mUser) == 1:
                if mUser[0] != '':
                    if not nameDict.has_key(mUser[0]):
                        newName = ''.join(random.SystemRandom().choice('0123456789ABCDEF') for _ in range(16))
                        i = 0;
                        while (newName in nameDict.values()) and i < 1000:
                            newName = ''.join(random.SystemRandom().choice('0123456789ABCDEF') for _ in range(16))
                            i = i+1;
                        if i == 1000:
                            print "Can't find a name :", mUser[0]
                            sys.exit()
                        nameDict[mUser[0]] = newName; 
#                        print 'Username is :', mUser[0], ' ---  newName :', nameDict[mUser[0]]
                    newLine = re.sub('"username": "'+ mUser[0] + '"', '"username": "' + nameDict[mUser[0]] + '"', line)
#                    newLine = re.sub('"username": "'+ mUser[0] + '"', '"username": "' + mUser[0] + '"', line)
#                    newLine = line
                else:
                    newLine = line
            else:
                print line
                sys.exit()
            if newLine != '':
                copy.write(newLine)
    f.close()
    copy.close()

if __name__ == "__main__":
    main(sys.argv[1:])


