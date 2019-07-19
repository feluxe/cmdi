#!/bin/sh

for i in $(seq 1 25)
do
    echo "Looping ... number $i"

    if [ $i == 5 ]
    then
        >&2 echo "myerror"
    fi
    sleep 0.01
done
