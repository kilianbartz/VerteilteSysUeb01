#!/bin/bash


# Loop to start the instances
for i in $(seq $1)
do
    python3 client.py "client$i" "localhost" $2 $3 > /dev/null 2>&1 &
done
echo "Started $1 clients"
