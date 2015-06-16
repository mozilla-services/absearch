absearch
========


The AB Search service provides 5 commands:

- **absearch-server**: runs the service
- **absearch-upload**: uploads the config located in data in S3
- **absearch-check**: validates the config using the schema
- **absearch-redis-dump**: dumps the Redis counters
- **absearch-redis-load**: loads the counters into Redis


Overview
========

.. image:: https://github.com/mozilla-services/absearch/blob/master/docs/absearch.jpg?raw=true


* config.json contains the search settings per locale and territory, and also cohorts for a/b testing
* Editors change the config JSON file in Github
* After some sanity check, a script uploads that file in S3
* Firefox calls the service to get the search settings, providing a locale & territory
* The app grabs them from S3 (with a local memory copy udpated every hour) and distribute users among cohorts
* The app uses Redis to keep track of cohort counters, that are used for the distribution


How to import/export in Redis
=============================

Use **absearch-redis-dump** to export in a file, the script takes the config file
as an argument::

    $ absearch-redis-dump absearch.ini > redis-dump

The produced file contains all the counters extracted from Redis.
To reinject them into Redis, use **absearch-redis-load**. It takes the config
file and the data file as params::

    $ absearch-redis-load absearch.ini redis-dump
    Loading 'redis-dump' into Redis
    Done

