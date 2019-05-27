#!/bin/bash

if [ $1 == "server" ]; then
    exec /usr/local/bin/absearch-server /app/config/absearch.ini
elif [ $1 == "test" ]; then
    # install dependencies (if required)

    if [ $EUID != 0 ]; then
        echo "Need to be root.  Run container with '--user root'"
        exit 1
    fi

    apt-get install -y redis-server
    pip install -r dev-requirements.txt
    nosetests --nocapture absearch
else
    echo "Unknown mode: $1"
fi
