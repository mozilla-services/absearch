import urlparse
import argparse
import sys
from collections import defaultdict

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from progress.counter import Counter
import redis


reqs = requests.Session()
_STOP = False
_BAR = None
_STATS = defaultdict(int)


def _display_stats():
    print('')
    print('Results')
    print('-------')
    items = _STATS.items()
    items.sort()

    for name, counter in items:
        print('- %s: %s' % (name, counter))

    print('')


def run_request(req_num, endpoint):
    if _STOP:
        return
    res = reqs.get(endpoint)
    if _BAR is not None:
        _BAR.next()
    cohort = res.json().get('cohort', 'default')
    _STATS[cohort] += 1


def _display_redis_counters(endpoint):
    endpoint = urlparse.urlparse(endpoint)
    host = endpoint.netloc.split(':')
    if len(host) == 1:
        port = '6379'
    else:
        host, port = host
    try:
        redis_server = redis.StrictRedis(host=host, port=port, db=0)
        print('Redis counters')
        print('--------------')
        for key in redis_server.smembers('absearch:keys'):
            print('%s:%s' % (key, redis_server.get(key)))
        print('')
    except redis.exceptions.ConnectionError:
        print('Could not reach redis')
        return



def main():
    parser = argparse.ArgumentParser(description='abcheck')

    parser.add_argument('-s', '--server', help='ABSearch server endpoint.',
                        type=str, default='http://localhost:8080')

    parser.add_argument('-r', '--redis', help='Redis server endpoint.',
                        type=str, default='redis://localhost:6379')

    parser.add_argument('-l', '--locale', help='Locale',
                        type=str, default='fr-FR')

    parser.add_argument('-t', '--territory', help='Territory',
                        type=str, default='FR')

    parser.add_argument('-p', '--product', help='Product',
                        type=str, default='firefox')

    parser.add_argument('--product-version', help='Product Version',
                        type=str, default='43')

    parser.add_argument('--channel', help='Channel', type=str,
                        default='release')

    parser.add_argument('--hits', help='Number of hits to perform.',
                        type=int, default=1000)

    args = parser.parse_args()

    _display_redis_counters(args.redis)

    executor = ThreadPoolExecutor(max_workers=100)
    future_to_resp = []

    global _BAR
    _BAR = Counter('Processing requests: ')

    path  = '/1/%s/%s/%s/%s/%s/default/default'

    path = path % (args.product, args.product_version, args.channel,
                   args.locale, args.territory)

    endpoint = args.server + path

    global _STOP

    # running the requests
    try:
        for req_num in range(args.hits):
            future = executor.submit(run_request, req_num, endpoint)
            future_to_resp.append(future)
    except KeyboardInterrupt:
        _STOP = True

    results = []

    def _grab_results():
        for future in as_completed(future_to_resp):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append(exc)

    try:
        _grab_results()
    except KeyboardInterrupt:
        _STOP = True
        executor.shutdown()
        _grab_results()
        print('Bye...')

    _BAR.finish()
    print('')
    _display_stats()
    _display_redis_counters(args.redis)


if __name__ == '__main__':
    main()
