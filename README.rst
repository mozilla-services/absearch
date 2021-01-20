absearch
========


The AB Search service provides 2 commands:

- **absearch-server**: runs the service
- **absearch-check**: validates the config using the schema


Overview
========

.. image:: https://github.com/mozilla-services/searchab/blob/master/docs/absearch.jpg?raw=true


* config.json contains the search settings per locale and territory, and also cohorts for a/b testing
* Editors change the config JSON file in Github
* Firefox calls the service to get the search settings, providing a locale & territory


Metrics
=======


The following metrics are produced by the app in statsd:

+------------------------------+---------+------------------------------------------+
|   Name                       | Type    | Description                              |
+==============================+=========+==========================================+
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

