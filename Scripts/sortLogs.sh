#!/bin/bash

for file in *.txt.gz; do
    dir=${file%%.txt.gz}
    mkdir -p "$dir/MOOCDB"
    mv "$file" "$dir"
    mv "$dir/$file" "$dir/logs.txt.gz"
    db=${dir//[.-]/_}
    sed s/XXXXX/$db/g /Users/leducni/Documents/workspace/eTracesX/Scripts/create_MOOCdb.sql > $dir/MOOCDB/create_MOOCdb.sql 
done
