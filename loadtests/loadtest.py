# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import random
from loads.case import TestCase
import os


LOCALES = [('en-US', 'US', u'Yahoo'),
           ('en-GB', 'GB', u'Google'),
           ('de-DE', 'DE', u'Google'),
           ('pt-BR', 'BR', u'Google'),
           ('be', 'BE', u'Yandex'),
           ('ru', 'RU', u'Yandex'),
           ('uk', 'UK', u'Yandex'),
           ('kk', 'KK', u'Yandex'),
           ('tr', 'TR', u'Yandex'),
           ('zh-TW', 'TW', u'Google'),
           ('zh-TW', 'HK', u'Google'),
           ('fr-FR', 'FR', u'Google'),
           ('zh-CN', 'CN', u'百度')]

COHORT = ['/web.xml', '/passwd', '/script>', '', '', '', '', '', '', '']


class TestSearch(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestSearch, self).__init__(*args, **kwargs)

    def test_api(self):

        # getting a cohort or asking for a crap cohort
        # everything should return the default settings
        locale, territory, expected = random.choice(LOCALES)
        cohort = random.choice(COHORT)
        path = '/1/firefox/43/release/%s/%s/default/default' + cohort
        res = self.session.get(self.server_url + path % (locale, territory))

        self.assertEqual(res.status_code, 200)
        self.assertTrue('settings' in res.json())
        self.assertTrue('cohort' not in res.json())
        self.assertEqual(res.json()['settings']['searchDefault'], expected)
