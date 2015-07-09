from gevent import monkey
monkey.patch_all()

import random
from loads.case import TestCase
import os


class TestSearch(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestSearch, self).__init__(*args, **kwargs)

    def test_api(self):
        choices = (('en-US', 'US'),
                   ('fr-FR', 'FR'),
                   ('cs-CZ', 'CZ'))

        # getting a cohort
        locale, territory = random.choice(choices)
        res = self.session.get(self.server_url +
                             '/1/firefox/39/beta/%s/%s/release/default/default'
                              % (locale, territory))

        self.assertEqual(res.status_code, 200)
        self.assertTrue('settings' in res.json())
