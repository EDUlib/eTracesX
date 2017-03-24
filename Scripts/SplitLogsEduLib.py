#!/usr/bin/python

import sys
import getopt
import re
import gzip
#import random

CoursList = [
    # Pattern, Filename
#    ('ITES\.1','ITES-A2015.txt'),

    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-102\.3([\+ ]|(%2[B0])|(%252B))A2016','ENT-102.3-A2016.txt'), # ENT-102.3 - Reussir son demarrage d'entreprise - L'approche SynOpp -  HEC Montreal        14 nov 2016    24 avr 2017    ENT-102.3    course-v1:HEC+ENT-102.3+A2016        course-v1:HEC+ENT-102.3+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101\.2([\+ ]|(%2[B0])|(%252B))H2017','DDI101.2-H2017.txt'), # DDI101.2 - L'ingenieur, source de solutions durables - Polytechnique Montreal    1 Fevrier 2017    01 avr 2017    DDI101.2    course-v1:PolyMtl+DDI101.2+H2017    course-v1:PolyMtl+DDI101.2+H2017

    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))TEKPHY1([\+ ]|(%2[B0])|(%252B))H2017','TEKPHY1-H2017.txt'), # TEKPHY1 - TEKPHY - Equilibre postural - Universite de Montreal    15 fevr 2017    31 mars 2017    TEKPHY1        course-v1:UMontreal+TEKPHY1+H2017    course-v1:UMontreal+TEKPHY1+H2017
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))IFT-Info-Theo([\+ ]|(%2[B0])|(%252B))H2016','IFT-Info-Theo-H2016.txt'), # IFT-Limites - Vers les limites ultimes de l'informatique - Universite de Montreal    26 fevr 2017    25 mai 2017    IFT-Limites    course-v1:UMontreal+IFT-Info-Theo+H2016    course-v1:UMontreal+IFT-Info-Theo+H2016
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))OAS\.2([\+ ]|(%2[B0])|(%252B))P2017','OAS.2-P2017.txt'), # OAS.2 - Outil d'aide a la scenarisation - Universite de Montreal    28 fevr 2017    15 juil 2017    OAS.2        course-v1:UMontreal+OAS.2+P2017        course-v1:UMontreal+OAS.2+P2017
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-103\.1([\+ ]|(%2[B0])|(%252B))H2017','ENT-103.1-H2017.txt'), # ENT-103.1 - Entrepreneuriat familial - HEC Montreal        13 mars 2017    30 avr 2017    ENT-103.1    course-v1:HEC+ENT-103.1+H2017        course-v1:HEC+ENT-103.1+H2017

    ('HEC([/\.]|(%2F)|(%252F))GRH-101([/\.]|(%2F)|(%252F))A2015','GRH-101-A2015.txt'), # GRH-101 - Gestion des conflits - HEC Montreal        En Tout Temps - A Votre Rythme    GRH-101        HEC/GRH-101/A2015            HEC/GRH-101/A2015
    ('HEC([/\.]|(%2F)|(%252F))GRH-101\.1([/\.]|(%2F)|(%252F))H2013','GRH-101.1-H2013.txt'), # GRH-101.1???
    ('HEC([/\.]|(%2F)|(%252F))MKT-101([/\.]|(%2F)|(%252F))H2015','MKT-101-H2015.txt'), # MKT-101 - Introduction au marketing -  HEC Montreal        En Tout Temps - A Votre Rythme    MKT-101        HEC/MKT-101/H2015            HEC/MKT-101/H2015
    ('HEC([/\.]|(%2F)|(%252F))MKT-101\.2([/\.]|(%2F)|(%252F))P2014','MKT-101.2-P2014.txt'), # MKT-101.2???
    ('HEC([/\.]|(%2F)|(%252F))MKT-101\.1([/\.]|(%2F)|(%252F))H2012','MKT-101.1-H2012.txt'), # MKT-101.1???
    
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))MAN-102\.1([\+ ]|(%2[B0])|(%252B))A2016','MAN-102.1-A2016.txt'), # MAN-102.1 - Promouvoir la sante et l'efficacite au travail - HEC Montreal        14 nov 2016    20 fevr 2017    MAN-102.1    course-v1:HEC+MAN-102.1+A2016        course-v1:HEC+MAN-102.1+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))MAN-101\.1([\+ ]|(%2[B0])|(%252B))A2016','MAN-101.1-A2016.txt'), # MAN-101.1 - Le Management - HEC Montreal        14 nov 2016    20 fevr 2017    MAN-101.1    course-v1:HEC+MAN-101.1+A2016        course-v1:HEC+MAN-101.1+A2016
        
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.3([\+ ]|(%2[B0])|(%252B))A2016','CHE101.3-A2016.txt'), # CHE101.3 - La chimie, en route vers le genie I - Polytechnique Montreal    02 nov 2016    15 janv 2017 - course-v1:PolyMtl+CHE101.3+A2016    course-v1:PolyMtl+CHE101.3+A2016
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))DDI101([\+ ]|(%2[B0])|(%252B))A2015','DDI101-A2015.txt'), # DDI101 - L'ingenieur, source de solutions durables - Polytechnique Montreal    14 Sept 2016    14 nov 2016 - course-v1:PolyMtl+DDI101+A2015        course-v1:PolyMtl+DDI101+A2015
    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))OAS\.1([\+ ]|(%2[B0])|(%252B))P2016','OAS.1-P2016.txt'), # ITES-OAS - Outil d'Aide a la Scenarisation pedagogique - Universite de Montreal    8 Aout 2016    25 oct 2016 - course-v1:UMontreal+OAS.1+P2016        course-v1:UMontreal+OAS.1+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-102\.2([\+ ]|(%2[B0])|(%252B))P2016','ENT-102.2-P2016.txt'), # ENT-102.2 - Reussir son demarrage d'entreprise - L'approche SynOpp - HEC Montreal        16 mai 2016    30 juin 2016 - course-v1:HEC+ENT-102.2+P2016        course-v1:HEC+ENT-102.2+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))d101([\+ ]|(%2[B0])|(%252B))H2016','COL-101.1-H2016.txt'), # COL-101.1 - L'evaluation participative de projets concertes - Dynamo +  HEC Montreal    16 Mai 2016    27 juin 2016 - course-v1:HEC+d101+H2016        course-v1:HEC+d101+H2016

    ('(course|block)-v1(:|(%3A)|(%253A))UMontreal([\+ ]|(%2[B0])|(%252B))PRC\.2([\+ ]|(%2[B0])|(%252B))P2016','PRC.2-P2016.txt'), # PRC.2 - Processus de raisonnement clinique - Universite de Montreal    4 Avril 2016    11 juin 2016 - course-v1:UMontreal+PRC.2+P2016        course-v1:UMontreal+PRC.2+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.2([\+ ]|(%2[B0])|(%252B))P2016','CHE101.2-P2016.txt'), # CHE101.2 - La chimie, en route vers le genie - Polytechnique Montreal    12 Avril 2016    07 juin 2016 - course-v1:PolyMtl+CHE101.2+P2016    course-v1:PolyMtl+CHE101.2+P2016
    ('(course|block)-v1(:|(%3A)|(%253A))HEC([\+ ]|(%2[B0])|(%252B))ENT-101\.2([\+ ]|(%2[B0])|(%252B))H2016','ENT-101.2-H2016.txt'), # ENT-101.2 - L'esprit entrepreneurial - HEC Montreal        28 Mars 2016    26 mai 2016 - course-v1:HEC+ENT-101.2+H2016        course-v1:HEC+ENT-101.2+H2016
    ('HEC([/\.]|(%2F)|(%252F))SC101\.2([/\.]|(%2F)|(%252F))H2015','SC101.2-H2015.txt'), # SC-101.2 - Comprendre les etats financiers - HEC Montreal        14 Dec 2015    21 mars 2016 - HEC/SC101.2/H2015            HEC/SC101.2/H2015
    ('(course|block)-v1(:|(%3A)|(%253A))PolyMtl([\+ ]|(%2[B0])|(%252B))CHE101\.1([\+ ]|(%2[B0])|(%252B))E2015','CHE101.1-E2015.txt'), # CHE101 - La chimie, en route vers le genie - Polytechnique Montreal    8 Nov 2015    12 janv 2016 - course-v1:PolyMtl+CHE101.1+E2015    course-v1:PolyMtl+CHE101.1+E2015
    ('PolyMtl([/\.]|(%2F)|(%252F))CHE101\.1([/\.]|(%2F)|(%252F))P2015','CHE101.1-P2015.txt'), # CHE101???

    ('UMontreal([/\.]|(%2F)|(%252F))PRC\.1([/\.]|(%2F)|(%252F))P2015','PRC.1-P2015.txt'), # PRC - Processus de raisonnement clinique - Universite de Montreal    5 Oct 2015    15 dec 2015 - UMontreal/PRC.1/P2015            UMontreal/PRC.1/P2015
    ('UMontreal([/\.]|(%2F)|(%252F))ITES\.1([/\.]|(%2F)|(%252F))P2015','ITES.1-P2015.txt'), # ITES - Innovations technopedagogiques en enseignement superieur - Universite de Montreal    13 Sept 2015    15 dec 2015 - UMontreal/ITES.1/P2015            UMontreal/ITES.1/P2015
    ('HEC([/\.]|(%2F)|(%252F))ENT-102\.1([/\.]|(%2F)|(%252F))P2015','ENT-102.1-P2015.txt'), # ENT-102.1 - Reussir son demarrage d'entreprise - L'approche SynOpp - HEC Montreal        25 Mai 2015    28 juil 2015 - HEC/ENT-102.1/P2015            HEC/ENT-102.1/P2015
    ]
    
def main(argv):
    workingDir = ''    
    inputFile = ''
    zipped = False

    try:
        opts, args = getopt.getopt(argv,"hi:w:z",["ifile=","wdir=","zip"])
    except getopt.GetoptError:
        print 'test.py -i <inputFileName> -w <workingDir> -z'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputFileName> -w <workingDir> -z'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputFile = arg
        elif opt in ("-w", "--wdir"):
            workingDir = arg
        elif opt in ("-z", "--zip"):
            zipped = True

#    inputFile = 'test.txt'
#    workingDir = 'test'
     
    if inputFile == '' or workingDir == '':
        sys.exit()
    
    if workingDir[-1] != '/':
        workingDir += '/'
    inputFilePath = workingDir + inputFile
    print 'Input file is :', inputFilePath
    print 'Output directory is :', workingDir
    print "Zipped file :", zipped
    
    infile = ''
    restfile = ''
    if zipped:
        infile = gzip.open(inputFilePath + '.gz', 'rb')
        restfile = gzip.open(inputFilePath + '.leftover.txt.gz', 'wb')
        for i in xrange(0,len(CoursList)):
            CoursList[i] = (re.compile(CoursList[i][0]), gzip.open(workingDir + CoursList[i][1]+ '.gz', 'wb'))
    else:
        infile = open(inputFilePath, "r")
        restfile = open(inputFilePath + '.leftover.txt', 'w')
        for i in xrange(0,len(CoursList)):
            CoursList[i] = (re.compile(CoursList[i][0]), open(workingDir + CoursList[i][1], "w"))

    for line in infile:
        added = False
        for pattern, outfile in CoursList:
            if pattern.search(line):
                outfile.write(line)
                if added == True:
                    print 'Line already added in another course :' + line
                added = True
        if added == False:
            restfile.write(line)
            
    infile.close()
    restfile.close()
    for pattern, outfile in CoursList:
        outfile.close()
        
    '''
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
    '''

if __name__ == "__main__":
    main(sys.argv[1:])


