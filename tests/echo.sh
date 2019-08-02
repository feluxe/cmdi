#!/bin/sh


for i in $(seq 1 5)
do
    echo "subprocess: stdout_text $i"

    if [ $i == 2 ]
    then
        >&2 echo "subprocess: stderr_text after 2"
    fi
    sleep 0.01
done
