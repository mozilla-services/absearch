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

XXX


Options to run

XXX


This script can be used to validate a release on stage.

**If you run this script without providing the Redis endpoint,
counters will be changed and not set back to their initial values**
