 #!/usr/bin/python
# -*- coding: utf-8 -*-

import urlparse
import argparse
import sys
from collections import defaultdict

import requests


reqs = requests.Session()

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


def main():
    parser = argparse.ArgumentParser(description='abcheck')

    parser.add_argument('-s', '--server', help='ABSearch server endpoint.',
                        type=str, default='https://search.stage.mozaws.net')

    parser.add_argument('-p', '--product', help='Product',
                        type=str, default='firefox')

    parser.add_argument('--product-version', help='Product Version',
                        type=str, default='43')

    parser.add_argument('--channel', help='Channel', type=str,
                        default='release')

    args = parser.parse_args()


    # version, product, product version, channel, local, territory, dist, dist
    # version
    path  = '/1/%s/%s/%s/%s/%s/default/default'


    for locale, territory, required in LOCALES:
        print('Checking %s %s. Expecting: %s' % (locale, territory, required))

        endpoint = path % (args.product, args.product_version, args.channel,
                           locale, territory)

        endpoint = args.server + endpoint

        result = reqs.get(endpoint).json()
        print(result)
        res = result['settings']['searchDefault']
        if res != required:
            raise Exception('Expected %r for %r, got %r' % (required, res,
                endpont))



if __name__ == '__main__':
    main()
