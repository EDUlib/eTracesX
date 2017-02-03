#!/usr/bin/python

import sys
import getopt
import datetime
import json

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

    nameDict = dict()

    f = open(inputfile, "r")
    for line in f:
        try:
            record = json.loads(str(line))
        except ValueError as e:
            continue
        if record['username'] == '':
            continue
        eventTimeStr = record['time']
        maybeOffsetDir = eventTimeStr[-6]
        if maybeOffsetDir == '+' or maybeOffsetDir == '-': 
            eventTimeStr = eventTimeStr[0:-6]
        eventDate = datetime.datetime.strptime(eventTimeStr[0:10], '%Y-%m-%d')
        #.dateT%H:%M:%S.%f').date
        if not nameDict.has_key(record['username']):
            nameDict[record['username']]=(record['username'],eventDate,0)
        lastEventDate = eventDate
        if nameDict[record['username']][1]>eventDate:
            lastEventDate = nameDict[record['username']][1]
        nameDict[record['username']] = (nameDict[record['username']][0],lastEventDate,nameDict[record['username']][2]+1)
    f.close()
    dateDict = dict()
    for aTuple in nameDict.values():
        if not dateDict.has_key(aTuple[1]):
            dateDict[aTuple[1]] = []
        dateDict[aTuple[1]].append(aTuple)
    filterNameSet = set()
    for tupleList in dateDict.values():
        tupleList.sort(key=lambda tup: tup[2])
        if len(tupleList) < 3:
            for aTuple in tupleList:
                filterNameSet.add(aTuple[0])
        else:
            filterNameSet.add(tupleList[0][0])
            filterNameSet.add(tupleList[len(tupleList)-1][0])
            filterNameSet.add(tupleList[(len(tupleList)-1)/2][0])
    print filterNameSet
    print str(len(filterNameSet)) + " : " + str(len(dateDict)) + " : " + str(len(nameDict))
    f = open(inputfile, "r")
    copy = open(outputfile, "w")
    for line in f:
        try:
            record = json.loads(str(line))
        except ValueError as e:
            copy.write(line)
            continue
        if record['username'] == '' or record['username'] in filterNameSet:
            copy.write(line)
    copy.close()
    f.close()

if __name__ == "__main__":
    main(sys.argv[1:])