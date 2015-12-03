=======
abcheck
=======

**abcheck** can be used to control an absearch server is working properly.

Once you've picked a locale & territory, the script runs 100k requests
to get cohort attributions. Once it's over, it displays the cohort
distribution.

If you provide a Redis endpoint, it will also display the counters
values before and after the test, so you can verify that they are right.
It will also set back the old values in Redis.

To run the script, run **make install** then **bin/python check.py**

Example::

    $ bin/python check.py
    Redis counters
    --------------
    fr-fr:fr:default:997
    fr-fr:fr:foo:3

    Processing requests: 1000

    Results
    -------
    - default: 1000

    Redis counters
    --------------
    fr-fr:fr:default:1997
    fr-fr:fr:foo:3

Optional arguments:

* --server ABSearch server endpoint. Default: http://localhost:8080
* --redis Redis server endpoint. Default: redis://localhost:6379
* --locale locale. Default: fr-FR
* --territory territory. Default: FR
* --product product. Default: Firefox.
* --product-version product. Default: 43
* --channel channel. Default: release
* --hits Number of requests to perform. Default: 1000


This script can be used to validate a release on stage.

**If you run this script without providing a valid Redis endpoint,
counters will be changed and not set back to their initial values**
