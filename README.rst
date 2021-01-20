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

