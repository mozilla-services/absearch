#!/bin/bash

if [ $1 == "server" ]; then
    exec /usr/local/bin/absearch-server /app/config/absearch.ini
elif [ $1 == "tests" ]; then
    # install dependencies (if required)

    if [ $EUID != 0 ]; then
        echo "Need to be root.  Run container with '--user root'"
        exit 1
    fi

    cp -R example-data/ data/

    pip install -r dev-requirements.txt
    pytest --capture=no absearch/tests
elif [ $1 == "flake8" ]; then
    pip install flake8
    flake8 absearch
else
    echo "Unknown mode: $1"
fi
