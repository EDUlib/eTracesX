#!/bin/bash -x

STR1=$1+$2+$3
zegrep -a -e "$2" all-Logs.txt.gz > tmpfile.txt
wc -l tmpfile.txt 
#zegrep -a -e "$2" all-Logs.txt.gz 
cat tmpfile.txt | egrep -a -v -e "(course|block)-v1(:|(%3A)|(%253A))$1([\+ ]|(%2[B0])|(%252B))$2([\+ ]|(%2[B0])|(%252B))$3" > $STR1.lost.txt
wc -l $STR1.lost.txt 
