absearch
========


The AB Search service provides 5 commands:

- **absearch-server**: runs the service
- **absearch-upload**: uploads the config located in data in S3
- **absearch-check**: validates the config using the schema


Overview
========

.. image:: https://github.com/mozilla-services/searchab/blob/master/docs/absearch.jpg?raw=true


* config.json contains the search settings per locale and territory, and also cohorts for a/b testing
* Editors change the config JSON file in Github
* After some sanity check, a script uploads that file in S3
* Firefox calls the service to get the search settings, providing a locale & territory
* The app grabs them from S3 (with a local memory copy udpated every hour) and distribute users among cohorts


Metrics
=======


The following metrics are produced by the app in statsd:

+------------------------------+---------+------------------------------------------+
|   Name                       | Type    | Description                              |
+==============================+=========+==========================================+
| absearch.s3.set_file         | timer   | file uploaded in S3                      |
+------------------------------+---------+------------------------------------------+
| absearch.s3.get_file         | timer   | file downloaded from S3                  |
+------------------------------+---------+------------------------------------------+
| absearch.add_user_to_cohort  | timer   | on every GET w/ a new cohort set         |
+------------------------------+---------+------------------------------------------+
| absearch.enrolled            | counter | on every cohort enrollment               |
+------------------------------+---------+------------------------------------------+
| absearch.discarded           | counter | on every cohort discard (**)             |
+------------------------------+---------+------------------------------------------+
| absearch.refreshed           | counter | on every call to get cohort settings     |
+------------------------------+---------+------------------------------------------+
| absearch.get_cohort_settings | timer   | on every GET to get back cohort settings |
+------------------------------+---------+------------------------------------------+


(*) unknown cohorts will increment this counter as well

